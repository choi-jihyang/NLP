# ruff: noqa: F821
import random

from runner import diagnostic, export_review, read_inputs, run

pilot_inputs = list(read_inputs(WORK / "pilot_inputs.jsonl.gz"))
references = [json.loads(line) for line in (WORK / "references.jsonl").open(encoding="utf-8")]
rng = random.Random(20261116)
pilot_selection = []
for dataset in ("studychat", "recipe4u"):
    subset = [r for r in pilot_inputs if r["dataset"] == dataset]
    rng.shuffle(subset)
    pilot_selection.extend(subset[:10])
pilot_journal = run(pilot_selection, annotator, run_root / "pilot", run_config)
diagnostic_report = diagnostic(pilot_journal, references)
print(json.dumps(diagnostic_report, ensure_ascii=False, indent=2))
review_path = export_review(pilot_journal, pilot_selection)
print("표본 원문·모델 판단 검토 파일:", review_path)
print("기존 라벨은 AI 초안입니다. 일치율은 독립 정확도가 아닙니다.")
