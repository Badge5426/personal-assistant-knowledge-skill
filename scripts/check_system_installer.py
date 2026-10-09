#!/usr/bin/env python3
"""Optional offline smoke test of a user's existing, trusted skill-installer."""
from __future__ import annotations
import argparse
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import shutil
import sys
import tempfile
from unittest.mock import patch


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--installer", required=True, help="existing trusted official installer script")
    args = parser.parse_args()
    path = Path(args.installer)
    if not path.is_file():
        raise SystemExit("specified installer is missing")
    sys.path.insert(0, str(path.parent))
    spec = importlib.util.spec_from_file_location("trusted_official_installer", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    repo = Path(__file__).resolve().parents[1]
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp).resolve()
        fixture = base / "fixture"
        shutil.copytree(repo / "skills", fixture / "skills",
                        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        dest = base / "project/.agents/skills"
        args = ["--repo", "example-owner/context-fixture", "--ref", "reviewed-fixture",
                "--path", "skills/maintain-personal-context", "--dest", str(dest),
                "--method", "download"]
        def owned_fixture(source, method, scratch):
            assert source.owner == "example-owner" and source.ref == "reviewed-fixture"
            assert method == "download"
            return str(fixture)
        log = io.StringIO()
        with patch.object(module, "_prepare_repo", side_effect=owned_fixture):
            with contextlib.redirect_stdout(log), contextlib.redirect_stderr(log):
                first, second = module.main(args), module.main(args)
        installed = dest / "maintain-personal-context"
        assert first == 0 and second != 0, "install/overwrite checks failed"
        for source in (fixture / "skills/maintain-personal-context").rglob("*"):
            if source.is_file():
                assert source.read_bytes() == (installed / source.relative_to(
                    fixture / "skills/maintain-personal-context")).read_bytes()
    print(json.dumps({"status": "passed", "checks": ["repo/path/ref/dest argument handling",
                      "owned local fixture copied", "existing destination rejected"],
                      "network": "replaced by owned fixture; remote install not tested"}))


if __name__ == "__main__":
    main()
