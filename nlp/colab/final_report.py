"""Write aggregate coverage, private result files and an auditable archive."""

import csv
import json
import zipfile
from collections import Counter

from contract import LABELS
from final_validation import sha
from journal import record_key


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def export_results(
    OUT,
    all_rows,
    failures,
    lineage,
    conflicts,
    quarantine,
    owner_expected,
    team_expected,
    unexpected,
    by_key,
    verified_rows,
    chosen_sources,
    source_info,
    configurations,
    full_inputs,
):
    successful = [r for r in all_rows if r["status"] == "ok"]
    decided = [r for r in successful if all(r["labels"][k] is not None for k in LABELS)]
    for filename, rows in (
        ("studychat_all_16851.jsonl", all_rows),
        ("studychat_ok.jsonl", successful),
        ("studychat_failures.jsonl", failures),
        ("studychat_ok_all_labels_decided.jsonl", decided),
    ):
        with (OUT / filename).open("w", encoding="utf-8") as stream:
            for row in rows:
                stream.write(json.dumps(row, ensure_ascii=False) + "\n")
    with (OUT / "studychat_labels.csv").open("w", encoding="utf-8-sig", newline="") as stream:
        fields = ["dataset", "source_id", "student_id", "conversation_id", *LABELS, "uncertain", "status"]
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for row in all_rows:
            flat = {k: row.get(k) for k in fields}
            for key in (*LABELS, "uncertain"):
                value = row.get("labels", {}).get(key)
                flat[key] = "null" if value is None else str(value).lower()
            writer.writerow(flat)
    statuses = dict(Counter(r["status"] for r in all_rows))
    missing = [record_key(r) for r in all_rows if r["status"] == "missing_result"]
    report = {
        "dataset": "studychat",
        "expected": 16851,
        "integrated_unique_ids": len(all_rows),
        "owner_expected": 15764,
        "team_expected": 1087,
        "statuses": statuses,
        "ok_all_three_labels_decided": len(decided),
        "ok_with_nullable_labels": len(successful) - len(decided),
        "missing_ids": missing,
        "unexpected_ids": unexpected,
        "duplicate_final_ids": [],
        "cross_attempt_repeated_ids": sum(len(v) > 1 for v in by_key.values()),
        "validated_candidate_records": verified_rows,
        "quarantined_ok_claims": len(quarantine),
        "disagreeing_valid_attempt_ids": len(conflicts),
        "selected_sources": dict(chosen_sources),
        "all_ids_accounted_for": len(all_rows) == 16851 and not missing and not unexpected,
        "all_rows_ok": len(successful) == 16851,
        "human_reviewed": False,
        "gold_eligible": False,
        "configuration_verification": (
            "Known config signatures checked where available; raw-response contract and original-source "
            "identity checked for every ok. Team and original owner complete run configs were not supplied."
        ),
        "selection_policy": (
            "Preserve original valid success, then first valid success in source priority order; "
            "retain failure if never successful. Conflicting valid labels are flagged, not called human gold."
        ),
    }
    write_json(OUT / "integration_report.json", report)
    write_json(
        OUT / "sources_and_configs.json",
        {"sources": source_info, "known_configurations": configurations, "full_input_sha256": sha(full_inputs)},
    )
    write_json(OUT / "label_conflicts.json", conflicts)
    write_json(OUT / "quarantined_ok_claims.json", quarantine)
    with (OUT / "lineage.jsonl").open("w", encoding="utf-8") as stream:
        for entry in lineage:
            stream.write(json.dumps(entry, ensure_ascii=False) + "\n")
    manifest = {
        path.name: {"bytes": path.stat().st_size, "sha256": sha(path)}
        for path in OUT.iterdir()
        if path.is_file() and path.name not in {"SHA256.json", "studychat_final_bundle.zip", "README.md"}
    }
    readme = f"""# StudyChat 통합 결과 — 2026-11-18

- 원본 StudyChat 16,851개 ID = 내 담당 15,764 + 팀원 1,087. RECIPE4U 제외.
- 전체 상태: {json.dumps(statuses, ensure_ascii=False)}
- 누락 {len(missing)} / 최종 중복 0 / 예상 외 ID 0.
- ok 중 3개 라벨 모두 결정: {len(decided)} / nullable 라벨 포함: {len(successful) - len(decided)}.
- 여러 검증 통과 시도 사이 라벨 불일치: {len(conflicts)}개 ID. label_conflicts.json에서 검토.

## 파일

- studychat_ok.jsonl: status=ok 결과만. 라벨 값 true/false/null을 그대로 보존.
- studychat_all_16851.jsonl: 실패를 포함한 원본 순서 전체 결과. 누락 없이 관리할 때 사용.
- studychat_failures.jsonl: 추론 미완료/검증 실패. 학습 라벨로 사용하지 않음.
- studychat_ok_all_labels_decided.jsonl: ok이면서 세 라벨 모두 null이 아닌 부분집합.
- studychat_labels.csv: ID와 세 라벨, 상태를 확인하는 UTF-8 BOM CSV.
- integration_report.json: 커버리지/성공/실패/검증 통계.
- lineage.jsonl 및 sources_and_configs.json: 행별 선택 출처와 원본 파일 해시/실행 설정.
- label_conflicts.json: 성공 시도끼리 판단이 달랐던 ID와 판단값.
- quarantined_ok_claims.json: ok 주장 중 독립 검증에 실패한 시도.
- SHA256.json: 배포 산출물 해시.

## 검증과 선택

모든 후보를 원본 source_id, 입력 SHA, 원본 SHA, 학생/대화 ID, 담당 범위와 대조했다.
ok는 raw_response를 원본 대화에 대해 다시 파싱하여 인용 위치·학생 역할·필수 필드·라벨 일관성을 검사했다.
기존 검증 통과 성공을 우선 보존하고, 실패 ID는 이전 재처리 → 배치 비교 2/4/8 → 최적화 본 실행의 첫 성공으로 복구했다.
중복 시도는 최종 ID 중복과 구분한다. 성공끼리 값이 다르면 선택 정책에 따라 한 건을 유지하고 불일치를 별도 기록했다.
원본과 팀원 일부 실행의 전체 설정 파일은 제공되지 않아 모든 모델 환경을 완전히 재현했다고 주장하지 않는다.
ok는 형식·근거 검증 통과이며, 의미 정확성이나 사람 정답을 보증하지 않는다.
human_reviewed=false, gold_eligible=false를 유지한다.
원래 입력 텍스트는 프로젝트의 data/raw/colab_bundle/inputs.jsonl.gz와 dataset/source_id로 연결할 수 있다.
"""
    (OUT / "README.md").write_text(readme, encoding="utf-8")
    manifest["README.md"] = {"bytes": (OUT / "README.md").stat().st_size, "sha256": sha(OUT / "README.md")}
    write_json(OUT / "SHA256.json", manifest)
    with zipfile.ZipFile(OUT / "studychat_final_bundle.zip", "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(OUT.iterdir()):
            if path.is_file() and path.suffix != ".zip":
                archive.write(path, path.name)
    print(json.dumps(report, ensure_ascii=True, indent=2))
