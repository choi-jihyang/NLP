# ruff: noqa: F821
from journal import Journal, atomic_json

if (run_root / "full/run_config.json").exists():
    saved = Journal(run_root / "full", run_config)
    summary = saved.summary()
    summary["expected"] = manifest["total"]
    summary["remaining_unprocessed"] = manifest["total"] - summary["processed"]
    summary["all_rows_semantically_processed"] = (
        summary["remaining_unprocessed"] == 0 and summary["statuses"].get("ok", 0) == manifest["total"]
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print("전체 결과:", saved.export())
    exceptional = [r for r in saved.records.values() if r["status"] != "ok"]
    uncertain = [r for r in saved.records.values() if r.get("labels", {}).get("uncertain")]
    atomic_json(run_root / "full/errors.json", exceptional)
    atomic_json(run_root / "full/uncertain.json", uncertain)
    atomic_json(run_root / "full/coverage.json", summary)
    print("오류와 보류 결과도 Drive에 따로 저장했습니다.")
else:
    print("전체 실행은 아직 시작되지 않았습니다. 표본 결과는 pilot 폴더에 있습니다.")
