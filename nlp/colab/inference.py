"""Colab CUDA에서 Qwen3.5-9B를 4비트로 로드하고 학생 입력을 의미 주석한다."""

import gc
import importlib.metadata
import time

from contract import chat_messages, parse_annotation


def load_model(model_id: str, revision: str) -> tuple:
    import torch
    from transformers import AutoTokenizer, BitsAndBytesConfig, Qwen3_5ForConditionalGeneration

    if not torch.cuda.is_available():
        raise RuntimeError("GPU runtime required; CPU fallback is intentionally disabled")
    # Fixed dtype allows the same run to resume after Colab assigns a different GPU.
    dtype = torch.float16
    quantization = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_use_double_quant=True,
        bnb_4bit_compute_dtype=dtype,
    )
    tokenizer = AutoTokenizer.from_pretrained(model_id, revision=revision, trust_remote_code=False)
    model = Qwen3_5ForConditionalGeneration.from_pretrained(
        model_id,
        revision=revision,
        quantization_config=quantization,
        device_map={"": 0},
        dtype=dtype,
        attn_implementation="sdpa",
        trust_remote_code=False,
    ).eval()
    versions = {
        p: importlib.metadata.version(p)
        for p in ("torch", "transformers", "accelerate", "bitsandbytes", "huggingface-hub")
    }
    metadata = {
        "model_id": model_id,
        "revision": revision,
        "dtype": str(dtype),
        "quantization": "bitsandbytes NF4 double-quant",
        "versions": versions,
        "gpu": torch.cuda.get_device_name(0),
        "vram_gib": torch.cuda.get_device_properties(0).total_memory / 2**30,
    }
    return model, tokenizer, metadata


class Annotator:
    def __init__(self, model, tokenizer, max_input_tokens: int = 6000, max_new_tokens: int = 768):
        self.model = model
        self.tokenizer = tokenizer
        self.max_input_tokens = max_input_tokens
        self.max_new_tokens = max_new_tokens

    def __call__(self, source: dict) -> dict:
        import torch

        started = time.monotonic()
        if not source.get("input_verified", True):
            return {"status": "input_unverified", "error": "History structure did not validate"}
        messages = chat_messages(source)
        inputs = self.tokenizer.apply_chat_template(
            messages,
            add_generation_prompt=True,
            tokenize=True,
            return_dict=True,
            return_tensors="pt",
            enable_thinking=False,
        )
        length = inputs["input_ids"].shape[-1]
        if length > self.max_input_tokens:
            return {
                "status": "context_overflow",
                "input_tokens": length,
                "error": "Full input exceeds configured budget; no silent truncation",
            }
        failures = []
        for attempt in range(2):
            text = ""
            try:
                torch.cuda.reset_peak_memory_stats()
                device_inputs = inputs.to("cuda:0")
                with torch.inference_mode():
                    output = self.model.generate(
                        **device_inputs,
                        max_new_tokens=self.max_new_tokens,
                        do_sample=False,
                        use_cache=True,
                        pad_token_id=self.tokenizer.eos_token_id,
                    )
                generated = output[0, length:]
                text = self.tokenizer.decode(generated, skip_special_tokens=True)
                eos = self.model.generation_config.eos_token_id
                eos = [eos] if isinstance(eos, int) else (eos or [])
                if len(generated) >= self.max_new_tokens and int(generated[-1]) not in eos:
                    raise ValueError("Generation reached output limit")
                result = parse_annotation(text, source)
                return {
                    **result,
                    "status": "ok",
                    "input_tokens": length,
                    "output_tokens": len(generated),
                    "attempts": attempt + 1,
                    "seconds": time.monotonic() - started,
                    "peak_vram_gib": torch.cuda.max_memory_allocated() / 2**30,
                    "raw_response": text,
                    "validation_failures": failures,
                }
            except torch.OutOfMemoryError:
                gc.collect()
                torch.cuda.empty_cache()
                return {
                    "status": "oom",
                    "input_tokens": length,
                    "error": "CUDA OOM; input was NOT truncated",
                    "seconds": time.monotonic() - started,
                }
            except (ValueError, TypeError, KeyError, AttributeError) as exc:
                failures.append(str(exc))
                if attempt == 0:
                    repair = messages + [
                        {"role": "assistant", "content": text},
                        {
                            "role": "user",
                            "content": (
                                "Your annotation failed validation: "
                                + str(exc)
                                + ". Correct the annotation JSON only; use exact student evidence."
                            ),
                        },
                    ]
                    inputs = self.tokenizer.apply_chat_template(
                        repair,
                        add_generation_prompt=True,
                        tokenize=True,
                        return_dict=True,
                        return_tensors="pt",
                        enable_thinking=False,
                    )
                    length = inputs["input_ids"].shape[-1]
                    if length > self.max_input_tokens:
                        break
        return {"status": "invalid_output", "error": "; ".join(failures), "seconds": time.monotonic() - started}
