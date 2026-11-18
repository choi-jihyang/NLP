# ruff: noqa: F821
from runner import read_inputs, run

# 표본 원문·근거·처리속도를 확인한 뒤 아래 값만 True로 바꾸세요.
RUN_FULL = False
MAX_NEW_ROWS = None  # 전체 대상. 시험 처리량 제한은 정수 입력. 재실행 시 저장된 ID는 건너뜁니다.
if RUN_FULL:
    valid_pilot = sum(r["status"] == "ok" for r in pilot_journal.records.values())
    if valid_pilot != len(pilot_selection):
        raise RuntimeError("표본 중 오류가 있습니다. 원인을 확인한 뒤 전체 처리를 시작하세요.")
    full_journal = run(
        read_inputs(WORK / "inputs.jsonl.gz"),
        annotator,
        run_root / "full",
        run_config,
        limit=MAX_NEW_ROWS,
    )
else:
    print("표본을 확인한 뒤 RUN_FULL=True로 바꾸면 전체 라벨링을 진행합니다.")
