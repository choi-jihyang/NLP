"""Standalone full-history hierarchical mmBERT Colab notebook; source code only."""

import ast
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMPLATES = ROOT/'nlp/mmtrain/templates'


def cell(kind, text):
    if kind=='code':
        ast.parse(text)
    value = {'cell_type':kind,'metadata':{},'id':hashlib.sha256(text.encode()).hexdigest()[:12],
             'source':text.splitlines(keepends=True)}
    if kind=='code':
        value.update(execution_count=None,outputs=[])
    return value


def main():
    sources = {str(p.relative_to(ROOT/'nlp')).replace('\\','/'):p.read_text(encoding='utf-8')
               for p in sorted((ROOT/'nlp/mmtrain').glob('*.py'))}
    bootstrap = '''import sys
from pathlib import Path
CODE = Path('/content/thinkguard_mmbert_training_code')
CODE.mkdir(exist_ok=True)
SOURCES = ''' + repr(sources) + '''
for relative,text in SOURCES.items():
    path = CODE/relative
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(text,encoding='utf-8')
if str(CODE) not in sys.path:
    sys.path.insert(0,str(CODE))
for name in list(sys.modules):
    if name=='mmtrain' or name.startswith('mmtrain.'):
        del sys.modules[name]
print('계층형 mmBERT 코드 준비 완료')
'''
    intro = '''# mmBERT-base 전체 대화 파인튜닝 — 긴 입력은 구간별 인코딩 후 통합

**새 A100/H100 GPU Colab 런타임**에서 실행하세요. 고용량 RAM 권장.
이 노트북은 연구용 구현이며 실제 A100/H100 학습을 개발 환경에서 실행하지 못했습니다.
Qwen 라벨 생성·CoVe 검증·CaMVo 투표를 다시 실행하지 않습니다. vLLM이나 임베딩 준비도 필요 없습니다.

## 데이터와 목표

Drive/ThinkGuard_NLP/studychat_qwen_blind_verify_v1/final/{train,valid,test}_ok.csv를 사용합니다.
앞서 정리한 splits_v2_qwen_verified와 동일한 원본 파일입니다. 기본 8,706/1,176/1,081건.
이전에 업로드한 thinkguard_qwen_verification_bundle.zip에서 원문만 읽습니다. 새 ZIP은 필요 없습니다.
ID와 원문 SHA로 연결하고, 과거 모델 라벨·검증 설명은 모델 입력에서 제외합니다.
학습 목표: requests_complete_answer / has_self_attempt_evidence 두 개. learning_context는 입력으로 주지 않습니다.
한 샘플은 현재 학생 발화 한 건과 그 시점 이전 대화입니다. 전체 chat당 라벨 하나를 붙이는 것이 아닙니다.
원본 파일을 덮어쓰지 않고 새 실험 폴더에 입력 스냅샷·결과를 저장합니다.

## 8,192토큰 초과 처리

- 원문 전체를 역할/발화 번호로 표시하고, 최대 8,192토큰 구간으로 나눕니다. 구간은 256토큰 겹칩니다.
- 같은 mmBERT를 모든 구간에 적용합니다. MAX_CHUNKS·앞/뒤 자르기·검색에 따른 생략이 없습니다.
- 현재 발화 자체가 길어도 모두 처리합니다. query는 현재 학생 토큰 전체에서 만듭니다.
- 구간 순서·현재 발화 위치·학생 토큰 비율을 활용해 현재 query에 조건화한 attention으로 합칩니다.
- 자기 시도 경로는 학생 토큰을 pooling합니다. AI 토큰은 문맥으로는 읽습니다.
- 구간마다 라벨을 복제하지 않습니다. **현재 학생 발화 샘플당 하나의 두 라벨 BCE 손실**을 계산합니다.
- overlap 토큰은 문맥으로 중복 읽지만 pooling 소유권은 한 번만 줍니다.

이는 8,192 위치 한도를 늘린 모델이 아닙니다. 전체 토큰을 보는 계층형 근사이며,
모든 토큰 사이의 전역 self-attention과 같지 않습니다. 경계를 가로지르는 추론이 약해질 수 있습니다.
학생 토큰 표현에도 주변 AI 문맥이 섞입니다. 역할 pooling·attention은 의미적 근거 인증이 아닙니다.
같은 과제인지, 학생이 실제 시도했는지는 여전히 학습·평가 대상입니다.

## 학습·메모리·재개

307M 인코더와 새 분류기를 **전체 파인튜닝**합니다. LoRA가 아닙니다.
BF16 autocast, 구간 microbatch, activation checkpoint로 메모리를 줄입니다.
학습의 batch는 추론 동시 요청과 다릅니다. OOM이면 먼저 WINDOW_BATCH/RECORD_BATCH를 낮추세요.
이 두 값과 SAVE_STEPS는 같은 RUN_NAME에서 변경 가능합니다. 숫자 연산/RNG 경로는 달라질 수 있습니다.
CHUNK_LENGTH·학습률·라벨·모델·epoch 변경은 새 RUN_NAME을 사용합니다.
전체 optimizer 체크포인트는 수 GB입니다. latest와 최대 3개 best 가중치 및 토큰 캐시용 Drive 공간이 필요합니다.
SAVE_STEPS=100과 epoch 종료에 원자적으로 저장하며 마지막 미저장 step은 중단 후 다시 계산합니다.
동일 환경·설정에서 optimizer/RNG/다음 대화 위치를 복원합니다. GPU가 바뀌면 비트 단위 동일성을 보장하지 않습니다.

## 평가 규칙

train만 학습·클래스 가중치 계산에 사용합니다. valid만 checkpoint와 두 threshold 선택에 사용합니다.
선택 지표는 각 이진 라벨의 class0/1 Macro-F1을 구한 뒤 두 라벨을 평균한 값입니다.
test는 마지막 별도 셀에서만 예측합니다. 높은 점수는 자동 검증 Qwen 라벨과의 일치이며 실제 정답률 증명이 아닙니다.
분할 간 정확히 같은 원문 중복은 test>valid>train 우선순위로 제외하고 ID/사유를 기록합니다.
분할 내 같은 원문도 첫 ID만 유지하므로 실제 학습 건수는 위 CSV 건수보다 줄 수 있습니다.

근거: [mmBERT 논문](https://proceedings.mlr.press/v306/marone26a.html),
[공식 모델](https://huggingface.co/jhu-clsp/mmBERT-base),
[계층형 Attention 원리, NAACL 2016](https://aclanthology.org/N16-1174/).
본 구조는 이 원리를 대화에 응용한 것으로 해당 논문의 완전 재현은 아닙니다.
'''
    sections = [('markdown',intro)]
    for heading,filename in [('1. Drive·기존 CSV/원문 스냅샷','setup.py.txt'),
                              ('2. 학습 전용 환경 설치·버전 고정','install.py.txt')]:
        sections += [('markdown','## '+heading),('code',(TEMPLATES/filename).read_text(encoding='utf-8'))]
    sections += [('markdown','## 3. 내장 코드 준비'),('code',bootstrap),
                 ('markdown','## 4. 모델·길이·학습 설정 고정'),
                 ('code',(TEMPLATES/'config.py.txt').read_text(encoding='utf-8')),
                 ('markdown','## 5. 원문 연결·전체 토큰화·길이/중복/분포 검사\n'
                  '토큰화는 한 번만 수행하고 Drive에 저장합니다. 누락 없이 전체 구간을 처리합니다.'),
                 ('code',"job('mmtrain.prepare')\n"),
                 ('markdown','## 6. GPU smoke — 짧은 대화와 가장 긴 train 대화\n'
                  '인코더 gradient와 메모리를 확인합니다. 이 가중치는 전체 학습에 사용하지 않습니다.\n'
                  'OOM이면 4번의 WINDOW_BATCH=1, RECORD_BATCH=1로 낮추고 4번부터 재실행하세요. '
                  '토큰 캐시는 재사용됩니다.'),
                 ('code',"job('mmtrain.train','--smoke')\n"),
                 ('markdown','## 7. 전체 학습·validation 선택·중단 후 재개\n'
                  '같은 셀을 다시 실행하면 마지막 optimizer 체크포인트에서 재개합니다.'),
                 ('code',"RUN_TRAIN = False\nif RUN_TRAIN:\n    job('mmtrain.train')\nelse:\n"
                  "    print('smoke 결과 확인 후 RUN_TRAIN=True로 변경하세요.')\n"),
                 ('markdown','## 8. 마지막 test 평가 — 설정·best 고정 후 한 번만\n'
                  '이 결과로 학습률·길이·모델을 다시 선택하지 마세요. 재실행 시 완료된 동일 보고서를 재사용합니다.'),
                 ('code',"RUN_TEST = False\nif RUN_TEST:\n    job('mmtrain.evaluate')\nelse:\n"
                  "    print('전체 학습 완료 후 RUN_TEST=True로 변경하세요.')\n")]
    sections += [('markdown','''## Drive 결과

ThinkGuard_NLP/studychat_mmbert_hierarchical_v1/
- token_cache_manifest.json: 길이·8192 초과·구간 수·중복 제외·양성 분포. 원문을 버린 건수와 구분하세요.
- tokenized.pt: 원문에서 만든 모든 구간과 라벨. 모델 입력에는 라벨이 포함되지 않습니다.
- smoke_report.json: longest train 처리 여부, 메모리, 샘플 처리 시간. 전체 시간 예측값은 아닙니다.
- latest.pt: 학습 재개용 model/optimizer/scheduler/RNG/위치. 직접 삭제하지 마세요.
- best_step_*.pt: validation으로 선택된 모델 가중치·threshold. latest가 가리키는 committed best 사용.
- best_valid_report.json / training_log.jsonl: validation 선택 기록.
- test_report.json / test_predictions.jsonl: 라벨별 F1·오탐률·정확 일치·속도·train 다수 클래스 기준선.
- config.json / model_pin.json / environment_versions.json: 재현 설정과 모델 commit SHA.

런타임이 사라지면 같은 노트북 1~5번을 복구한 뒤 7번을 실행하세요. 토큰 캐시와 optimizer를 재사용합니다.
학습 완료 후 마지막 평가만 필요하면 1~4번 복구 후 8번만 실행해도 됩니다.
checkpoint 내부에는 Python pickle이 포함되므로 이 노트북이 생성한 파일만 사용하세요.
''')]
    notebook = {'cells':[cell(*part) for part in sections],'nbformat':4,'nbformat_minor':5,
                'metadata':{'accelerator':'GPU','colab':{'provenance':[]},
                  'kernelspec':{'display_name':'Python 3','language':'python','name':'python3'},
                  'language_info':{'name':'python'}}}
    target = ROOT/'notebooks/thinkguard_mmbert_hierarchical_finetuning.ipynb'
    target.write_text(json.dumps(notebook,ensure_ascii=False,indent=1),encoding='utf-8')
    print(target)


if __name__=='__main__':
    main()
