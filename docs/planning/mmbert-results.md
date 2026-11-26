# mmBERT 평가 결과와 추가 실험

상태: **초안**. 기존 단일 모델의 최종 테스트는 완료됐고 체크포인트 앙상블은 Colab 실행 결과를 기다린다.

## 기존 단일 모델

[Drive 테스트 보고서](https://drive.google.com/file/d/1i4fFFL8igoL2Xqj-xIMwo0lWI6tx7PMm/view) 기준, 중복 제거 후 테스트 1,075건.
검증셋에서 선택된 모델은 3 epoch, optimizer step 1,623이며 검증 평균 Macro-F1은 0.7752다.

| 라벨 | 테스트 Macro-F1 | 양성 정밀도 | 양성 재현율 |
|---|---:|---:|---:|
| 완성 답안 요청 | 0.8064 | 0.6769 | 0.7538 |
| 자기 시도 근거 | 0.7623 | 0.7372 | 0.6102 |

두 라벨 평균 Macro-F1은 **0.7844**, 두 라벨 정확 일치는 **0.7051**이다.
이 값은 Qwen 자동 검증 라벨에 대한 일치율이며 사람 정답이나 실제 한국어 서비스 성능이 아니다.

## 추가 실험: 체크포인트 3개 평균

- 기존 `best_step_541.pt`, `best_step_1082.pt`, `best_step_1623.pt`를 같은 비율로 평균한다. 데이터와 가중치는 수정하지 않는다.
- 기존 검증셋에서만 판단 임계값을 선택한다. 기존 단일 모델의 검증 평균 Macro-F1 **0.7752**를 엄격히 넘을 때만 테스트를 실행한다.
- 결과는 기존 Drive 실행 폴더의 `checkpoint_ensemble_v1/`에 별도로 저장한다. 기존 모델과 결과는 덮어쓰지 않는다.
- [Colab 노트북](../../notebooks/thinkguard_mmbert_checkpoint_ensemble.ipynb)은 T4 메모리를 고려해 구간·레코드 추론 배치를 각각 1로 사용한다. 8,192토큰 단일 구간도 OOM이면 A100/H100에서 실행한다.

학습·평가 구현은 `nlp/mmtrain/`, 학습 노트북은 `notebooks/thinkguard_mmbert_hierarchical_finetuning.ipynb`에 있다.
