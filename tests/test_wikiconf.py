# -*- coding: utf-8 -*-
import json, os
from pathlib import Path
import pytest
from wikiconf import find_root, load, WikiConfigError

def make_wiki(tmp: Path, **over):
    cfg = json.loads((Path(__file__).parents[1] / "templates/student/llmwiki.json").read_text(encoding="utf-8"))
    cfg.update(over)
    (tmp / "llmwiki.json").write_text(json.dumps(cfg, ensure_ascii=False), encoding="utf-8")
    return tmp

def test_find_root_walks_up(tmp_path):
    make_wiki(tmp_path)
    deep = tmp_path / "3.Permanent_Notes" / "slipbox"; deep.mkdir(parents=True)
    assert find_root(deep) == tmp_path

def test_missing_config_raises(tmp_path):
    with pytest.raises(WikiConfigError):
        load(tmp_path)

def test_paths_are_resolved_absolute(tmp_path):
    make_wiki(tmp_path)
    c = load(tmp_path)
    assert c.path("index") == tmp_path / "3.Permanent_Notes" / "slipbox" / "index.md"
    assert c.gate["min_links"] == 2 and c.profile == "student"

def test_professor_template_has_types():
    cfg = json.loads((Path(__file__).parents[1] / "templates/professor/llmwiki.json").read_text(encoding="utf-8"))
    assert cfg["profile"] == "professor"
    assert set(cfg["fleeting_types"]) >= {"Standard", "Daily", "Weekly", "Monthly", "Limitless"}
