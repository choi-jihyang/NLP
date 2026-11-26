"""Build a Colab notebook for validation-gated mmBERT checkpoint ensembling."""

import ast
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "notebooks/thinkguard_mmbert_checkpoint_ensemble.ipynb"


def cell(kind, source):
    if kind == "code":
        ast.parse(source)
    result = {
        "cell_type": kind,
        "metadata": {},
        "id": hashlib.sha256(source.encode()).hexdigest()[:12],
        "source": source.splitlines(keepends=True),
    }
    if kind == "code":
        result.update(execution_count=None, outputs=[])
    return result


def main():
    sources = {
        str(path.relative_to(ROOT / "nlp")).replace("\\", "/"): path.read_text(encoding="utf-8")
        for path in sorted((ROOT / "nlp/mmtrain").glob("*.py"))
    }
    intro = """# mmBERT 체크포인트 앙상블 추가 실험

기존 `studychat_mmbert_hierarchical_v1`의 세 체크포인트를 같은 비율로 평균합니다. 데이터셋 수정과 재학습은 하지 않습니다.
**A100/H100 권장, T4는 느릴 수 있습니다.** 고용량 RAM 런타임에서 순서대로 실행하세요.
각 체크포인트는 한 번씩 순차적으로 로드하며 추론 배치를 1/1로 고정해 T4 메모리 사용량을 줄입니다.
T4에서 8,192토큰 단일 구간도 OOM이면 A100/H100이 필요합니다. OOM 이후에는 런타임을 다시 시작하세요.

검증셋에서만 판단 기준값을 선택합니다. 기존 단일 모델의 검증 점수보다 앙상블 점수가 높을 때만 마지막 테스트 셀을 실행합니다.
기존 테스트 결과는 선택에 사용하지 않습니다. 점수는 Qwen 자동 검증 라벨과의 일치이며 사람 정답 성능은 아닙니다.
GPU에서 이 노트북의 전체 실행은 아직 검증하지 못했습니다.
"""
    setup = """import gc
import hashlib
import importlib.metadata
import json
import sys
from pathlib import Path
from google.colab import drive

drive.mount('/content/drive')
RUN_DIR = Path('/content/drive/MyDrive/ThinkGuard_NLP/studychat_mmbert_hierarchical_v1')
CONFIG_PATH = RUN_DIR / 'config.json'
if not CONFIG_PATH.is_file():
    raise FileNotFoundError(CONFIG_PATH)
config = json.loads(CONFIG_PATH.read_text(encoding='utf-8'))
if Path(config['run_dir']).resolve() != RUN_DIR.resolve():
    raise ValueError('config.json의 run_dir가 기존 실험 폴더와 다릅니다')
# 추론 배치만 줄입니다. 모델 가중치, 토큰 캐시, 실험 identity는 그대로입니다.
config['window_batch'] = 1
config['record_batch'] = 1
for package, version in config['versions'].items():
    actual = importlib.metadata.version(package)
    if actual != version:
        raise RuntimeError(f'{package} 버전 불일치: 현재 {actual}, 기존 {version}. 다음 설치 셀 실행 후 런타임을 다시 시작하세요.')
CODE = Path('/content/thinkguard_mmbert_ensemble_code')
CODE.mkdir(exist_ok=True)
SOURCES = """ + repr(sources) + """
for relative, source in SOURCES.items():
    path = CODE / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(source, encoding='utf-8')
if str(CODE) not in sys.path:
    sys.path.insert(0, str(CODE))
from mmtrain.data import load_cache, sha
from mmtrain.checkpoint import load
from mmtrain.metrics import choose_thresholds, evaluate
from mmtrain.runtime import initialize, predict
import numpy as np
import torch
if not torch.cuda.is_available():
    raise RuntimeError('GPU 런타임이 필요합니다')
print('GPU:', torch.cuda.get_device_name(0), '추론 window/record batch: 1/1')

CHECKPOINTS = ['best_step_541.pt', 'best_step_1082.pt', 'best_step_1623.pt']
for name in CHECKPOINTS:
    if not (RUN_DIR / name).is_file():
        raise FileNotFoundError(RUN_DIR / name)
cache = load_cache(config)  # 원본 해시·토큰 캐시 identity 확인
records, splits = cache['records'], cache['splits']
baseline = json.loads((RUN_DIR / 'best_valid_report.json').read_text(encoding='utf-8'))
if baseline['optimizer_step'] != 1623:
    raise ValueError('기존 best가 step 1623이 아닙니다. 체크포인트 목록을 재검토하세요.')
print('valid/test rows:', len(splits['valid']), len(splits['test']))
print('기존 valid 점수:', baseline['mean_label_macro_f1'])
"""
    install = """# setup 셀에서 버전 불일치가 발생했을 때만 실행하세요.
import json, subprocess, sys
from pathlib import Path
run_dir = Path('/content/drive/MyDrive/ThinkGuard_NLP/studychat_mmbert_hierarchical_v1')
versions = json.loads((run_dir / 'environment_versions.json').read_text(encoding='utf-8'))
requirements = [f'{name}=={version}' for name, version in versions.items()]
subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-q', *requirements])
print('설치 완료. Colab 런타임을 다시 시작한 뒤 setup 셀부터 실행하세요.')
"""
    valid = """def checkpoint_predictions(name, ids):
    state = load(RUN_DIR / name, config['identity'])
    model = optimizer = None
    try:
        model, optimizer = initialize(config)
        model.load_state_dict(state['model'])
        del state
        target, probabilities, seconds = predict(model, records, ids, config['record_batch'])
        return target, probabilities, seconds
    finally:
        if model is not None:
            del model
        if optimizer is not None:
            del optimizer
        gc.collect()
        torch.cuda.empty_cache()

valid_target = None
valid_probabilities = []
valid_seconds = {}
for name in CHECKPOINTS:
    target, probabilities, seconds = checkpoint_predictions(name, splits['valid'])
    if valid_target is None:
        valid_target = target
    elif not np.array_equal(valid_target, target):
        raise ValueError('검증셋 라벨·순서가 체크포인트 사이에 다릅니다')
    valid_probabilities.append(probabilities)
    valid_seconds[name] = seconds
    print(name, 'valid seconds:', round(seconds, 1))

# 기존 단일 모델 결과가 그대로 재현되는지 확인합니다.
single_state = load(RUN_DIR / CHECKPOINTS[-1], config['identity'])
single_valid = evaluate(valid_target, valid_probabilities[-1], single_state['thresholds'])
if abs(single_valid['mean_label_macro_f1'] - baseline['mean_label_macro_f1']) > 1e-9:
    raise ValueError('기존 단일 모델 valid 점수가 재현되지 않습니다')
del single_state

ensemble_valid_prob = np.mean(np.stack(valid_probabilities), axis=0)
ensemble_thresholds = choose_thresholds(valid_target, ensemble_valid_prob)
ensemble_valid = evaluate(valid_target, ensemble_valid_prob, ensemble_thresholds)
IMPROVED = ensemble_valid['mean_label_macro_f1'] > single_valid['mean_label_macro_f1'] + 1e-12
print('기존 단일 모델:', json.dumps(single_valid, ensure_ascii=False, indent=2))
print('3개 평균 앙상블:', json.dumps(ensemble_valid, ensure_ascii=False, indent=2))
print('valid 향상:', IMPROVED)

OUT_DIR = RUN_DIR / 'checkpoint_ensemble_v1'
OUT_DIR.mkdir(exist_ok=True)
validation_result = {
    'checkpoints': CHECKPOINTS,
    'checkpoint_sha256': {name: sha(RUN_DIR / name) for name in CHECKPOINTS},
    'identity': config['identity'],
    'selection_rule': 'equal probability mean of all three checkpoints; validation threshold grid 0.1..0.9 step 0.05; test only if valid score strictly improves',
    'single_valid': single_valid,
    'ensemble_valid': ensemble_valid,
    'improved': IMPROVED,
    'valid_seconds': valid_seconds,
}
(OUT_DIR / 'validation_report.json').write_text(json.dumps(validation_result, ensure_ascii=False, indent=2), encoding='utf-8')
print('저장:', OUT_DIR / 'validation_report.json')
"""
    test = """if not IMPROVED:
    print('검증셋에서 향상되지 않아 테스트 평가를 건너뜁니다.')
else:
    current = json.loads((OUT_DIR / 'validation_report.json').read_text(encoding='utf-8'))
    if current['identity'] != config['identity'] or current['checkpoint_sha256'] != {name: sha(RUN_DIR / name) for name in CHECKPOINTS}:
        raise ValueError('검증 이후 체크포인트 또는 설정이 바뀌었습니다')
    report_path = OUT_DIR / 'test_report.json'
    if report_path.exists():
        print('기존 앙상블 테스트 보고서 재사용:', report_path.read_text(encoding='utf-8'))
    else:
        test_target = None
        test_probabilities = []
        test_seconds = {}
        for name in CHECKPOINTS:
            target, probabilities, seconds = checkpoint_predictions(name, splits['test'])
            if test_target is None:
                test_target = target
            elif not np.array_equal(test_target, target):
                raise ValueError('테스트셋 라벨·순서가 체크포인트 사이에 다릅니다')
            test_probabilities.append(probabilities)
            test_seconds[name] = seconds
            print(name, 'test seconds:', round(seconds, 1))
        test_prob = np.mean(np.stack(test_probabilities), axis=0)
        ensemble_test = evaluate(test_target, test_prob, ensemble_thresholds)
        original_test = json.loads((RUN_DIR / 'test_report.json').read_text(encoding='utf-8'))
        ensemble_test.update(
            identity=config['identity'],
            checkpoint_sha256=current['checkpoint_sha256'],
            validation_report='validation_report.json',
            original_single_test_mean_macro_f1=original_test['mean_label_macro_f1'],
            delta_vs_single_test=ensemble_test['mean_label_macro_f1'] - original_test['mean_label_macro_f1'],
            test_seconds=test_seconds,
        )
        report_path.write_text(json.dumps(ensemble_test, ensure_ascii=False, indent=2), encoding='utf-8')
        print(json.dumps(ensemble_test, ensure_ascii=False, indent=2))
"""
    parts = [
        ("markdown", intro),
        ("markdown", "## 1. 기존 실행 결과 연결\n버전 오류가 나면 2번 셀로 설치하고 런타임을 다시 시작하세요."),
        ("code", setup),
        ("markdown", "## 2. 필요할 때만 환경 설치"),
        ("code", install),
        ("markdown", "## 3. 검증셋 비교\n세 체크포인트를 순서대로 추론합니다. 검증 점수가 기존보다 엄격히 높아야 테스트가 열립니다."),
        ("code", valid),
        ("markdown", "## 4. 조건부 최종 테스트\n3번 셀의 결과를 확인한 뒤 실행하세요. 원래 단일 모델 테스트와 같은 고정 테스트셋을 사용합니다."),
        ("code", test),
    ]
    notebook = {
        "cells": [cell(*part) for part in parts],
        "nbformat": 4,
        "nbformat_minor": 5,
        "metadata": {
            "accelerator": "GPU",
            "colab": {"provenance": []},
            "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
            "language_info": {"name": "python"},
        },
    }
    TARGET.write_text(json.dumps(notebook, ensure_ascii=False, indent=1), encoding="utf-8")
    print(TARGET)


if __name__ == "__main__":
    main()
