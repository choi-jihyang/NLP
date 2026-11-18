"""Batched, text-only Qwen3.5 FP8 inference for a Colab L4."""

import importlib.metadata
import os
import time

from contract import chat_messages, parse_annotation


def load_model(model_id: str, revision: str, long_context: bool = False) -> tuple:
    # Cell 1 has already initialized CUDA in the notebook process.
    os.environ["VLLM_WORKER_MULTIPROC_METHOD"] = "spawn"
    import torch
    from vllm import LLM

    if not torch.cuda.is_available():
        raise RuntimeError("GPU runtime required")
    settings = dict(
        dtype="bfloat16",
        max_model_len=7168,
        max_num_seqs=8,
        max_num_batched_tokens=8192,
        gpu_memory_utilization=0.85,
        language_model_only=True,
        enforce_eager=True,
        seed=0,
    )
    if long_context:
        settings.update(max_model_len=32768, max_num_seqs=1)
    model = LLM(model=model_id, revision=revision, tokenizer_revision=revision, trust_remote_code=False, **settings)
    metadata = {
        "model_id": model_id,
        "revision": revision,
        "engine": "vllm",
        "quantization": "checkpoint FP8 dynamic",
        "engine_settings": settings,
        "versions": {p: importlib.metadata.version(p) for p in ("torch", "vllm", "transformers", "huggingface-hub")},
        "gpu": torch.cuda.get_device_name(0),
        "vram_gib": torch.cuda.get_device_properties(0).total_memory / 2**30,
    }
    return model, model.get_tokenizer(), metadata


class Annotator:
    batch_size = 8

    def __init__(self, model, tokenizer, max_input_tokens=6000, max_new_tokens=768):
        self.model, self.tokenizer = model, tokenizer
        self.max_input_tokens, self.max_new_tokens = max_input_tokens, max_new_tokens

    def __call__(self, source):
        return self.annotate_batch([source])[0]

    def annotate_batch(self, sources):
        from vllm import SamplingParams

        started = time.monotonic()
        results = [None] * len(sources)
        messages = [chat_messages(source) for source in sources]
        failures = [[] for _ in sources]
        active = list(range(len(sources)))
        for attempt in range(2):
            prompts, indices = [], []
            for i in active:
                if not sources[i].get("input_verified", True):
                    results[i] = {"status": "input_unverified", "error": "History structure did not validate"}
                    continue
                tokens = self.tokenizer.apply_chat_template(
                    messages[i], add_generation_prompt=True, tokenize=True, return_dict=False, enable_thinking=False
                )
                if not isinstance(tokens, list) or not tokens or any(type(t) is not int or t < 0 for t in tokens):
                    raise TypeError("Chat template must return a nonempty list of nonnegative integer token IDs")
                if len(tokens) > self.max_input_tokens:
                    results[i] = {
                        "status": "context_overflow",
                        "input_tokens": len(tokens),
                        "error": "Full input exceeds budget; no silent truncation",
                    }
                    continue
                prompts.append({"prompt_token_ids": tokens})
                indices.append(i)
            if not prompts:
                break
            # Engine failures abort the run; completed journal checkpoints remain resumable.
            outputs = self.model.generate(
                prompts, SamplingParams(temperature=0, max_tokens=self.max_new_tokens, seed=0), use_tqdm=False
            )
            if len(outputs) != len(indices):
                raise RuntimeError("vLLM returned an unexpected batch size")
            active = []
            for i, request, prompt in zip(indices, outputs, prompts, strict=False):
                completion = request.outputs[0]
                text = completion.text
                try:
                    if completion.finish_reason != "stop":
                        raise ValueError("Generation did not finish normally: " + str(completion.finish_reason))
                    parsed = parse_annotation(text, sources[i])
                    results[i] = {
                        **parsed,
                        "status": "ok",
                        "input_tokens": len(prompt["prompt_token_ids"]),
                        "output_tokens": len(completion.token_ids),
                        "attempts": attempt + 1,
                        "raw_response": text,
                        "validation_failures": list(failures[i]),
                    }
                except (ValueError, TypeError, KeyError, AttributeError) as exc:
                    failures[i].append(str(exc))
                    if attempt == 0:
                        messages[i] += [
                            {"role": "assistant", "content": text},
                            {
                                "role": "user",
                                "content": "Your annotation failed validation: "
                                + str(exc)
                                + ". Correct the annotation JSON only; use exact student evidence.",
                            },
                        ]
                        active.append(i)
                    else:
                        results[i] = {"status": "invalid_output", "error": "; ".join(failures[i])}
        elapsed = time.monotonic() - started
        for result in results:
            if result is None:
                raise RuntimeError("Missing batch result")
            result["batch_seconds"] = elapsed
            result["batch_size"] = len(sources)
        return results
