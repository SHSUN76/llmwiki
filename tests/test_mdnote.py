# -*- coding: utf-8 -*-
from mdnote import parse_frontmatter, wikilinks, dump_frontmatter

NOTE = '''---
type: permanent
title: 글쓰기는 사고의 매체
tags: [글쓰기, 사고]
luhmann: "1B1"
connections:
  internal:
    - "[[상향식 글쓰기와 창발적 구조]]"
  cross:
    - "[[지식의 연금술은 정보를 연결하고 변환하여 지혜를 만드는 것이다]]"
---
본문 [[니클라스 루만의 제텔카스텐 시스템]] 과 [[글쓰기는 실천적 기술이다|별칭]] 그리고 [[상향식 글쓰기와 창발적 구조]].
'''

def test_parse_scalars_and_inline_list():
    fm, body = parse_frontmatter(NOTE)
    assert fm["type"] == "permanent"
    assert fm["tags"] == ["글쓰기", "사고"]
    assert fm["luhmann"] == "1B1"
    assert body.startswith("본문")

def test_parse_nested_block_lists():
    fm, _ = parse_frontmatter(NOTE)
    assert fm["connections"]["internal"] == ["[[상향식 글쓰기와 창발적 구조]]"]
    assert len(fm["connections"]["cross"]) == 1

def test_wikilinks_distinct_targets_without_alias():
    _, body = parse_frontmatter(NOTE)
    assert wikilinks(body) == ["니클라스 루만의 제텔카스텐 시스템", "글쓰기는 실천적 기술이다", "상향식 글쓰기와 창발적 구조"]

def test_no_frontmatter():
    fm, body = parse_frontmatter("그냥 본문")
    assert fm == {} and body == "그냥 본문"

def test_dump_roundtrip_simple():
    fm, body = parse_frontmatter(NOTE)
    text = dump_frontmatter(fm) + body
    fm2, _ = parse_frontmatter(text)
    assert fm2 == fm
