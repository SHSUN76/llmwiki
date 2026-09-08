# -*- coding: utf-8 -*-
import json, os, subprocess
from pathlib import Path
from init import run_init

def test_init_creates_structure_and_git(tmp_path):
    root = tmp_path / "LLMwiki"
    r = run_init(root=root, student_id="22012345", github=False, register_obsidian=False)
    assert (root / "llmwiki.json").exists() and (root / "3.Permanent_Notes/slipbox/index.md").exists()
    cfg = json.loads((root / "llmwiki.json").read_text(encoding="utf-8"))
    assert cfg["owner"]["student_id"] == "22012345"
    assert "{{date}}" not in (root / "3.Permanent_Notes/slipbox/index.md").read_text(encoding="utf-8")
    assert r["git"]["initialized"] is True and r["git"]["first_commit"] is True
    assert r["github"]["status"] == "skipped: --no-github"
    log = subprocess.run(["git", "log", "--oneline"], cwd=root, capture_output=True, text=True).stdout
    assert "init: LLMwiki for 22012345" in log

def test_init_is_idempotent(tmp_path):
    root = tmp_path / "LLMwiki"
    run_init(root=root, student_id="1", github=False, register_obsidian=False)
    (root / "CLAUDE.md").write_text("내가 고친 규칙", encoding="utf-8")
    r = run_init(root=root, student_id="1", github=False, register_obsidian=False)
    assert (root / "CLAUDE.md").read_text(encoding="utf-8") == "내가 고친 규칙"
    assert "CLAUDE.md" in r["skipped"]

def test_obsidian_registration_writes_vault_entry(tmp_path, monkeypatch):
    appdata = tmp_path / "AppData"; monkeypatch.setenv("APPDATA", str(appdata))
    root = tmp_path / "LLMwiki"
    r = run_init(root=root, student_id="1", github=False, register_obsidian=True)
    data = json.loads((appdata / "obsidian" / "obsidian.json").read_text(encoding="utf-8"))
    assert any(v["path"] == str(root) for v in data["vaults"].values())
    assert r["obsidian"]["registered"] is True
