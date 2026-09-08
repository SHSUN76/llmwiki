---
name: init
description: 학생 PC에 LLMwiki 폴더를 만든다. 템플릿 복사·설정 기입·git 초기화·GitHub private 저장소 생성·교수 collaborator 초대·Obsidian 보관소 등록을 스크립트 한 번으로 실행하고 결과를 표로 보고한다. 수업 첫 주 설치, "LLMwiki 만들어줘", "위키 초기화해줘", "GitHub 연결이 안 됐다"는 재시도에 쓴다. 사용법 - /llmwiki:init [--root 경로] [--student-id 학번]
---

# LLMwiki 초기화

인자: `$ARGUMENTS`

이 스킬은 판단하지 않는다. 인자를 모아 `init.py`에 넘기고, 결과를 사람이 읽을 표로 옮기고, 실패한 단계의 재시도 방법을 알려 주는 것이 전부다. 폴더·git·GitHub·Obsidian 처리는 전부 스크립트가 한다.

`init`은 위키를 **만드는** 스킬이므로 `wikiconf.py`를 먼저 부르지 않는다. 설정 파일은 이 스킬이 실행된 결과로 생긴다.

## 1. 인자 확보

두 값이 필요하다. `$ARGUMENTS`에 없으면 하나씩 묻는다.

| 인자 | 물을 말 | 기본값 |
|---|---|---|
| `--root` | LLMwiki 폴더를 어디에 만들까요? | 사용자 홈 아래 `LLMwiki` |
| `--student-id` | 학번을 알려 주세요. | 없음. 반드시 받는다 |

학번은 GitHub 저장소 이름(`llmwiki-<학번>`)에 쓰이므로 공백과 한글이 없어야 한다. 어긋나면 한 번 다시 묻는다.

폴더가 이미 있어도 그대로 진행한다. `init.py`는 멱등이라 기존 파일을 덮어쓰지 않는다.

## 2. 실행

```
python "${CLAUDE_PLUGIN_ROOT}/skills/init/scripts/init.py" --root "<경로>" --student-id "<학번>" --json
```

GitHub 로그인이 필요하면 스크립트가 브라우저 로그인을 띄운다. 이때는 사용자가 브라우저에서 코드를 입력할 때까지 기다린다(최대 10분).

선택 인자는 사용자가 명시적으로 요청할 때만 붙인다.

| 인자 | 언제 |
|---|---|
| `--no-github` | GitHub 연결을 나중에 하겠다고 할 때 |
| `--no-obsidian` | Obsidian 보관소 등록을 원치 않을 때 |
| `--professor-github <계정>` | 담당 교수 계정이 기본값과 다를 때 |
| `--repo-name <이름>` | 저장소 이름을 학번과 다르게 할 때 |

GitHub 단계가 실패해도 스크립트는 종료 코드를 올리지 않는다. 로컬 폴더와 git까지는 완성된 것이다.

## 3. 결과 보고

출력 JSON을 표로 옮긴다.

| 단계 | 결과 |
|---|---|
| 폴더 | `<root>` — 생성 `len(created)`개, 유지 `len(skipped)`개 |
| git | `git.initialized` / 첫 커밋 `git.first_commit` |
| GitHub | `github.status`, 저장소 `github.repo`, push `github.pushed`, 교수 초대 `github.collaborator` |
| Obsidian | `obsidian.registered` (`obsidian.detail`) |

`next_steps`의 각 줄을 그대로 덧붙인다.

## 4. GitHub 실패 시 재시도 안내

`github.status`가 `ok`가 **아니면** 원인별로 안내한다. 상태 문자열은 스크립트가 낸 값을 그대로 쓴다.

| `github.status` | 안내 |
|---|---|
| `skipped: gh not found` | GitHub CLI가 없습니다. setup 스크립트를 다시 돌리거나 GitHub CLI를 설치한 뒤 `/llmwiki:init`을 다시 실행하세요. |
| `skipped: not logged in` | 터미널에서 `gh auth login`으로 로그인한 뒤 `/llmwiki:init`을 다시 실행하세요. |
| `skipped: cannot read user` | `gh auth status`로 로그인 상태를 확인한 뒤 `/llmwiki:init`을 다시 실행하세요. |
| `failed: repo create` | `github.detail`을 그대로 보여 주고, 같은 이름의 저장소가 이미 있는지 확인한 뒤 `/llmwiki:init`을 다시 실행하도록 안내한다. |
| `partial` | 저장소는 만들어졌지만 push가 되지 않았습니다. 폴더에서 `git push -u origin main`을 실행하세요. |
| `skipped: --no-github` | 나중에 연결하려면 `gh auth login` 후 `/llmwiki:init`을 다시 실행하세요. |

재실행은 안전하다. 이미 있는 파일은 유지되고 이미 만들어진 저장소는 다시 만들지 않는다.

`github.collaborator`가 `invited`가 아니면 교수에게 초대가 가지 않은 것이므로, 다시 실행하거나 수업 시간에 알리라고 안내한다.

## 5. 마무리

세 줄로 끝낸다.

1. `Obsidian을 열어 LLMwiki 보관소를 확인하세요.`
2. `터미널에서 이 폴더로 이동한 뒤 /llmwiki:daily 로 첫 기록을 남겨 보세요.`
3. 만들어진 폴더의 `CLAUDE.md`에 수업 규칙 다섯 줄이 있으니 읽어 보라고 알린다.

## 출력 계약 (hard constraints)

- [ ] 폴더·git·GitHub·Obsidian 처리는 전부 `init.py`가 했고 직접 파일을 만들지 않았다
- [ ] 학번을 받지 않은 채 실행하지 않았다
- [ ] 보고한 상태 값은 스크립트 출력 그대로다 (추측하지 않았다)
- [ ] GitHub 실패는 감추지 않고 원인과 재시도 방법을 알렸다
- [ ] 기존 파일을 덮어쓰지 않았다
