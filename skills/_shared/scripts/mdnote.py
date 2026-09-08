# -*- coding: utf-8 -*-
"""frontmatter(제한된 YAML 부분집합)와 [[위키링크]] 파서. 외부 의존성 없음.
지원: 스칼라, 인라인 리스트 [a, b], 중첩 키 아래 블록 리스트(- 항목). 그 외 형식은 문자열로 보존."""
from __future__ import annotations
import re

_FM = re.compile(r"\A---\r?\n(.*?)\r?\n---\r?\n?", re.S)
_LINK = re.compile(r"\[\[([^\]\|#]+)(?:[#\|][^\]]*)?\]\]")

def _scalar(v: str):
    v = v.strip()
    if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
        return v[1:-1]
    if v.startswith("[") and v.endswith("]"):
        inner = v[1:-1].strip()
        return [] if not inner else [_scalar(x) for x in inner.split(",")]
    if v in ("true", "false"):
        return v == "true"
    return v

def parse_frontmatter(text: str) -> tuple[dict, str]:
    m = _FM.match(text)
    if not m:
        return {}, text
    fm: dict = {}
    stack: list[tuple[int, dict]] = [(-1, fm)]
    cur_list_owner: dict | None = None
    cur_list_key = None
    for raw in m.group(1).splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        line = raw.strip()
        while len(stack) > 1 and indent <= stack[-1][0]:
            stack.pop()
        parent = stack[-1][1]
        if line.startswith("- "):
            if cur_list_key is None or cur_list_owner is None:
                continue
            existing = cur_list_owner.get(cur_list_key)
            if not isinstance(existing, list):
                # 값이 비어 dict 로 열렸던 키였다면 그 자리표시자를 리스트로 되돌린다
                if len(stack) > 1 and stack[-1][1] is existing:
                    stack.pop()
                cur_list_owner[cur_list_key] = []
            cur_list_owner[cur_list_key].append(_scalar(line[2:]))
            continue
        if ":" not in line:
            continue
        key, _, val = line.partition(":")
        key = key.strip()
        if val.strip() == "":
            # 값이 비었다: 중첩 dict 이거나 블록 리스트다. 우선 dict 로 열어 두고,
            # 다음 줄이 '- ' 항목이면 그때 리스트로 바꾼다.
            child: dict = {}
            parent[key] = child
            stack.append((indent, child))
            cur_list_owner = parent
            cur_list_key = key
            continue
        parent[key] = _scalar(val)
        cur_list_owner = None
        cur_list_key = None
    _fix_empty_dicts(fm)
    return fm, text[m.end():]

def _fix_empty_dicts(d: dict):
    for k, v in list(d.items()):
        if isinstance(v, dict):
            if not v:
                d[k] = ""
            else:
                _fix_empty_dicts(v)

def wikilinks(text: str) -> list[str]:
    out, seen = [], set()
    for t in _LINK.findall(text):
        t = t.strip()
        if t and t not in seen:
            seen.add(t); out.append(t)
    return out

def dump_frontmatter(fm: dict) -> str:
    lines = ["---"]
    def emit(d: dict, ind: int):
        for k, v in d.items():
            pad = " " * ind
            if isinstance(v, dict):
                lines.append(f"{pad}{k}:"); emit(v, ind + 2)
            elif isinstance(v, list):
                if all(isinstance(x, str) and "[[" not in x for x in v) and ind == 0:
                    lines.append(f"{pad}{k}: [" + ", ".join(v) + "]")
                else:
                    lines.append(f"{pad}{k}:")
                    for x in v:
                        lines.append(f"{pad}  - \"{x}\"")
            elif isinstance(v, bool):
                lines.append(f"{pad}{k}: {'true' if v else 'false'}")
            elif k == "luhmann":
                lines.append(f"{pad}{k}: \"{v}\"")
            else:
                lines.append(f"{pad}{k}: {v}")
    emit(fm, 0)
    lines.append("---")
    return "\n".join(lines) + "\n"
