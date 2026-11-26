# mmBERT 계층형 대화 분류 학습

상태: **구현됨**. 전체 학습과 기존 단일 모델 테스트를 완료했다. [평가 결과](../planning/mmbert-results.md).

목적: 자동 검증 라벨로 완성 답안 요청·동일 과제 자기 시도 존재를 예측하는 연구용 분류기.
라벨 단위는 현재 학생 발화 한 건(이전 대화 포함)이며 전체 chat당 하나가 아니다.
서비스 API/정책/DB 변경 없음. Qwen 파인튜닝이나 CaMVo 재라벨링이 아니다.
입력은 현재 학생 발화와 과거 대화만이며 기존 라벨·검증 설명·미래 발화는 특징에서 제외한다.

## 수용 기준·불변식

- 원본 SHA와 ID로 final/{train,valid,test}_ok.csv를 연결. 기본 8706/1176/1081건.
- 원본 CSV와 원문은 변경하지 않음. 실험 전 입력 해시·학생·대화 중복 검증.
- 정확히 같은 원문이 split 사이 중복되면 test > valid > train 우선순위로 하위 split에서 제외.
  split 내 같은 원문은 첫 ID 유지. 라벨과 관계없는 사전 규칙이며 제외 ID/사유를 별도 저장한다.
- 모든 대상의 모든 과거/현재 텍스트 토큰을 처리. tail/head 자르기·MAX_CHUNKS·검색 누락 없음.
- 인코더 한 번의 입력은 <=8192. 기본 구간 8192, overlap256, attention 기반 bag classifier.
- 구간 간 중복 토큰은 pooling ownership에서 한 번만 계산. 특수/역할 토큰은 학생 근거 pooling 제외.
- 현재 발화도 긴 경우 여러 구간에 분산하고 전체를 query 표현에 반영한다. 현재 문장 anchor 절단 없음.
- I4: 역할은 원문 메타데이터에서 얻으며, 자기 시도 head의 pooling 대상은 학생 토큰에 한정한다.
  contextual token은 주변 AI 내용을 볼 수 있으므로 의미적으로 I4가 보장되는 증거 추출기는 아니다.
- 현재 query에 조건화한 context attention과 student attention으로 두 logit을 만든다.
  같은 과제인지 판단하는 능력은 학습 대상이며 attention 자체를 근거 인증으로 쓰지 않는다.
- 구간별 대화 라벨 복제나 단순 OR/max vote 없음. 한 대화 한 BCE loss로 길이 가중 왜곡 방지.
- 전체307M encoder+새 attention/head full fine-tuning. LoRA 아님. AdamW, BF16 autocast,
  window microbatch2, outer activation checkpoint로 긴 기록도 window 단위 재계산.
- GPU 부하가 크면 window batch/구간 길이를 낮추며 데이터를 조용히 생략하지 않는다.
- checkpoint에는 model/optimizer/scheduler/RNG/다음 epoch·대화 위치/입력·코드·모델 identity 저장.
  Drive latest 원자적 교체, best 별도 유지. optimizer step 이후에만 저장해 누적 gradient 유실 방지.
- train만 학습/클래스 가중치 산출. valid만 체크포인트/두 threshold 선택. test는 최종 별도 셀.
- 각 이진 라벨에서 class0/1 F1 평균, 그 두 라벨 macro-F1 평균을 선택 지표로 정의한다.
- 정확도는 자동 검증 AI 라벨에 대한 예측 일치이며 실제 의도 정답률의 증명 아님.

## 노트북

Drive의 기존 qwen verification ZIP과 final CSV를 사용. 추가 재라벨링·임베딩·vLLM 필요 없음.
설치/버전고정 → 원문/CSV snapshot → tokenizer+model SHA 고정 → 토큰화·누출/길이 보고서
→ train 소량 smoke → 명시적 전체 학습 → valid best → 별도 최종 test → Drive 저장.
구간 분할은 본문 한도를 늘리는 것이 아니라 인코더 호출 수를 늘리는 설계다.
원문 보존과 모든 토큰 간 전역 self-attention은 다르며 chunk 경계 정보 손실 가능성을 보고한다.
한계8192 자체를 늘리기 위한 무학습 position/RoPE 변경은 하지 않는다.

## 검증

숫자/역할 mask/overlap 소유권, 끝부분 토큰 포함, 8192 경계, 긴 현재 발화, 다수 구간,
CSV/null/ID/hash/학생 분할, exact duplicate, 개별 구간에 라벨 복제 없음,
미니 encoder로 backward 및 체크포인트 재개 동등성, valid threshold/test 격리.
전체 notebook AST/nbformat과 단위 테스트를 검사했다. GPU 학습·테스트 결과는 평가 문서에 기록했다.
별도 컨텍스트 리뷰와 Colab 앙상블 실험 검증은 남아 있다.

## 근거

- mmBERT: https://proceedings.mlr.press/v306/marone26a.html
- https://huggingface.co/jhu-clsp/mmBERT-base
- Hierarchical Attention Networks, NAACL2016: https://aclanthology.org/N16-1174/
  계층형 pooling 원리를 대화와 mmBERT에 응용하며 해당 논문 전체 재현은 아니다.
