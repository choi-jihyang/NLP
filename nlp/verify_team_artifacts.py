"""Verify generated team ZIP/notebooks without a GPU."""

import ast
import gzip
import hashlib
import json
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
package = ROOT / "data/raw/colab_team_last3000"
long_context = "--long-context" in sys.argv
suffix = "_long32k" if long_context else ""
package = package.with_name(package.name + suffix)
with zipfile.ZipFile(package / f"thinkguard_team_last3000{suffix}.zip") as archive:
    assert archive.testzip() is None
    manifest = json.loads(archive.read("manifest.json"))
    assignment = json.loads(archive.read("assignment.json"))
    for name, expected in manifest["files"].items():
        assert hashlib.sha256(archive.read(name)).hexdigest() == expected, name
        if name.endswith(".py"):
            ast.parse(archive.read(name).decode("utf-8"), filename=name)
    rows = [json.loads(line) for line in gzip.decompress(archive.read("inputs.jsonl.gz")).decode().splitlines()]
    assert len(rows) == 3000
    assert [r["dataset"] + ":" + r["source_id"] for r in rows] == assignment["team_keys"]
for name in (f"thinkguard_team_last3000{suffix}.ipynb", "thinkguard_owner_split_and_merge.ipynb"):
    notebook = json.loads((ROOT / "notebooks" / name).read_text(encoding="utf-8"))
    for cell in notebook["cells"]:
        if cell["cell_type"] == "code":
            ast.parse("".join(cell["source"]))
    if name.startswith("thinkguard_team_last3000"):
        upload = "".join(notebook["cells"][4]["source"])
        assert f"thinkguard_team_last3000{suffix}.zip" in upload
        assert 'manifest["references"]' not in upload
        assert "owner_run_config.json" in upload
        load = "".join(notebook["cells"][8]["source"])
        assert 'owner_config["model"]["revision"]' in load
        assert "assert_compatible(owner_config, run_config)" in load
        if long_context:
            assert "long_context=True" in load
            assert "max_input_tokens=32000" in load
            assert "annotator.batch_size = 1" in load
            assert 'run_config["inference_profile"] = "team_long32k_v1"' in load
print("Generated ZIP CRC/hashes, 3,000 IDs, module/notebook syntax and settings wiring: OK")
