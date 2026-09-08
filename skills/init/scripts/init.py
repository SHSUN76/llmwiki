# -*- coding: utf-8 -*-
"""LLMwiki 폴더 구축: 템플릿 복사(멱등) → llmwiki.json → git init·첫 커밋 → GitHub private 저장소·교수 초대 → Obsidian vault 등록.
GitHub 단계 실패는 요약에 남기고 종료 코드를 올리지 않는다."""
from __future__ import annotations
import argparse, json, os, secrets, shutil, subprocess, sys, time
from datetime import date, datetime, timezone, timedelta
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

PLUGIN_ROOT = Path(__file__).resolve().parents[3]
TEMPLATE_DIR = PLUGIN_ROOT / "templates" / "student"

def _run(cmd: list[str], cwd: Path | None = None, timeout: int = 180) -> tuple[int, str]:
    try:
        p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout)
        return p.returncode, (p.stdout + p.stderr).strip()
    except FileNotFoundError:
        return 127, f"{cmd[0]} not found"
    except subprocess.TimeoutExpired:
        return 124, "timeout"

def copy_templates(root: Path, student_id: str, today: str) -> tuple[list[str], list[str]]:
    created, skipped = [], []
    for src in sorted(TEMPLATE_DIR.rglob("*")):
        rel = src.relative_to(TEMPLATE_DIR)
        dst = root / rel
        if src.is_dir():
            dst.mkdir(parents=True, exist_ok=True); continue
        if dst.exists():
            skipped.append(str(rel).replace("\\", "/")); continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        if src.suffix in (".md", ".json") or src.name in (".gitignore", ".gitkeep"):
            text = src.read_text(encoding="utf-8")
            if rel.name == "index.md":
                text = text.replace("{{date}}", today)
            if rel.name == "llmwiki.json":
                cfg = json.loads(text); cfg["owner"]["student_id"] = student_id
                text = json.dumps(cfg, ensure_ascii=False, indent=2) + "\n"
            dst.write_text(text, encoding="utf-8", newline="\n")
        else:
            shutil.copy2(src, dst)
        created.append(str(rel).replace("\\", "/"))
    return created, skipped

def git_init(root: Path, student_id: str) -> dict:
    out = {"initialized": False, "first_commit": False, "detail": ""}
    if not (root / ".git").exists():
        rc, msg = _run(["git", "init", "-b", "main"], root)
        if rc != 0:
            out["detail"] = msg; return out
    out["initialized"] = True
    _run(["git", "config", "core.autocrlf", "false"], root)
    rc, _ = _run(["git", "rev-parse", "HEAD"], root)
    if rc != 0:
        _run(["git", "add", "-A"], root)
        rc, msg = _run(["git", "-c", "user.name=LLMwiki", "-c", "user.email=llmwiki@local", "commit", "-m", f"init: LLMwiki for {student_id}"], root)
        out["first_commit"] = rc == 0; out["detail"] = msg[-300:]
    else:
        out["first_commit"] = True
    return out

def github_setup(root: Path, repo: str, professor: str) -> dict:
    out = {"status": "", "repo": "", "pushed": False, "collaborator": ""}
    rc, _ = _run(["gh", "--version"])
    if rc != 0:
        out["status"] = "skipped: gh not found"; return out
    rc, _ = _run(["gh", "auth", "status"])
    if rc != 0:
        print("GitHub 로그인이 필요합니다. 브라우저가 열리면 코드를 입력하세요...", flush=True)
        # 로그인은 대화형으로 돌린다(capture 금지): 8자리 코드와 "Enter 를 누르세요" 안내가 학생 화면에 보여야 한다.
        try:
            rc = subprocess.run(["gh", "auth", "login", "--web", "--git-protocol", "https", "-h", "github.com"], timeout=600).returncode
        except subprocess.TimeoutExpired:
            rc = 124
        except FileNotFoundError:
            rc = 127
        if rc != 0:
            out["status"] = "skipped: not logged in"; out["detail"] = f"gh auth login rc={rc}"; return out
    rc, login = _run(["gh", "api", "user", "-q", ".login"])
    if rc != 0:
        out["status"] = "skipped: cannot read user"; return out
    full = f"{login}/{repo}"
    rc, _ = _run(["gh", "repo", "view", full])
    if rc != 0:
        rc, msg = _run(["gh", "repo", "create", repo, "--private", "--source", str(root), "--remote", "origin", "--push"], root, timeout=300)
        if rc != 0:
            out["status"] = "failed: repo create"; out["detail"] = msg[-300:]; return out
        out["pushed"] = True
    else:
        rc, _ = _run(["git", "remote", "get-url", "origin"], root)
        if rc != 0:
            _run(["git", "remote", "add", "origin", f"https://github.com/{full}.git"], root)
        rc, _ = _run(["git", "push", "-u", "origin", "main"], root, timeout=300)
        out["pushed"] = rc == 0
    out["repo"] = full
    rc, msg = _run(["gh", "api", "-X", "PUT", f"repos/{full}/collaborators/{professor}", "-f", "permission=push"])
    out["collaborator"] = "invited" if rc == 0 else f"failed: {msg[-120:]}"
    out["status"] = "ok" if out["pushed"] else "partial"
    return out

def obsidian_config_path() -> tuple[Path | None, str]:
    """OS별 Obsidian vault 목록 파일 위치. (경로, 실패 사유) 를 돌려준다."""
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "obsidian" / "obsidian.json", ""
    if sys.platform.startswith("win"):
        appdata = os.environ.get("APPDATA")
        if not appdata:
            return None, "APPDATA 없음"
        return Path(appdata) / "obsidian" / "obsidian.json", ""
    return Path.home() / ".config" / "obsidian" / "obsidian.json", ""

def register_obsidian_vault(root: Path) -> dict:
    cfg, why = obsidian_config_path()
    if cfg is None:
        return {"registered": False, "detail": why}
    try:
        data = json.loads(cfg.read_text(encoding="utf-8")) if cfg.exists() else {}
        vaults = data.setdefault("vaults", {})
        if any(Path(v.get("path", "")) == root for v in vaults.values()):
            return {"registered": True, "detail": "이미 등록됨"}
        vaults[secrets.token_hex(8)] = {"path": str(root), "ts": int(time.time() * 1000), "open": True}
        cfg.parent.mkdir(parents=True, exist_ok=True)
        cfg.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8", newline="\n")
        return {"registered": True, "detail": "추가됨"}
    except Exception as e:  # noqa: BLE001
        return {"registered": False, "detail": str(e)[:200]}

def run_init(root: Path, student_id: str, github: bool = True, professor: str = "SHSUN76", repo: str | None = None, register_obsidian: bool = True) -> dict:
    root = Path(root).resolve(); root.mkdir(parents=True, exist_ok=True)
    today = datetime.now(timezone(timedelta(hours=9))).date().isoformat()  # KST
    created, skipped = copy_templates(root, student_id, today)
    summary = {"root": str(root), "created": created, "skipped": skipped, "git": git_init(root, student_id)}
    summary["github"] = github_setup(root, repo or f"llmwiki-{student_id}", professor) if github else {"status": "skipped: --no-github"}
    summary["obsidian"] = register_obsidian_vault(root) if register_obsidian else {"registered": False, "detail": "skipped"}
    steps = []
    if summary["github"].get("status") != "ok":
        steps.append("GitHub 연결이 안 됐습니다. 수업 시간에 `gh auth login` 후 `/llmwiki:init` 을 다시 실행하세요.")
    steps.append("Obsidian 을 열어 LLMwiki 보관소를 확인하세요.")
    summary["next_steps"] = steps
    return summary

def main(argv=None):
    ap = argparse.ArgumentParser(description="LLMwiki 초기화")
    ap.add_argument("--root", required=True); ap.add_argument("--student-id", required=True)
    ap.add_argument("--professor-github", default="SHSUN76"); ap.add_argument("--repo-name")
    ap.add_argument("--no-github", action="store_true"); ap.add_argument("--no-obsidian", action="store_true")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    s = run_init(Path(a.root), a.student_id, github=not a.no_github, professor=a.professor_github, repo=a.repo_name, register_obsidian=not a.no_obsidian)
    if a.json:
        print(json.dumps(s, ensure_ascii=False, indent=2))
    else:
        print(f"LLMwiki: {s['root']}  생성 {len(s['created'])}개, 유지 {len(s['skipped'])}개")
        print(f"git: {s['git']}"); print(f"GitHub: {s['github']}"); print(f"Obsidian: {s['obsidian']}")
        for n in s["next_steps"]: print(" -", n)
    return 0

if __name__ == "__main__":
    sys.exit(main())
