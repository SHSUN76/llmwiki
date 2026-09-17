# llmwiki

제텔카스텐 규칙으로 임시노트·문헌노트를 영구노트로 승격하는 Claude Code 플러그인.

판단은 LLM이 하고 결정은 스크립트가 한다. 5기준 채점과 연결 후보 고르기는 모델의 몫이지만, 승격 게이트(중복률·링크 수·주제 태그)와 루만 번호 계산·index 삽입은 파이썬 표준 라이브러리 스크립트가 맡는다. **게이트가 HOLD를 내면 점수와 무관하게 승격되지 않는다.**

영남대학교 「화학공학을 위한 AI」 수업에서 학생 40명의 개인 위키를 운영하려고 만들었다. 수업 밖에서도 `llmwiki.json` 하나만 바꾸면 쓸 수 있다.

## 설치

```
claude plugin marketplace add SHSUN76/sehosun
claude plugin install llmwiki@sehosun
```

Claude Code를 다시 시작하면 `/llmwiki:` 로 여섯 개 스킬이 잡힌다. 파이썬 3.10 이상이 필요하고 외부 패키지는 쓰지 않는다.

첫 위키는 이렇게 만든다.

```
/llmwiki:init --root ~/LLMwiki --student-id 20261234
```

`init`은 GitHub 원격을 `https://` 주소로 고정한다. 교내망에서 22번 포트(SSH)가 막혀 있어도 push가 되게 하려는 장치다.

## 스킬

| 스킬 | 하는 일 | 사용법 |
|---|---|---|
| `init` | 폴더·템플릿·git·GitHub private 저장소·Obsidian 보관소 등록 | `/llmwiki:init [--root 경로] [--student-id 학번]` |
| `daily` | 오늘의 일일노트를 만들고 세 칸을 하나씩 물어 학생 문장 그대로 채움 | `/llmwiki:daily` |
| `capture` | 스친 한 줄 생각을 임시노트 한 장으로 즉시 저장 | `/llmwiki:capture <한 줄 생각>` |
| `promote` | 임시노트를 5기준으로 채점하고 게이트를 통과한 것만 영구노트로 승격 | `/llmwiki:promote [경로\|--only 오늘\|--all] [--dry-run]` |
| `literature` | 문헌노트의 "하이라이트 + 나의 메모" 세트마다 승격 시도. 원본은 보존 | `/llmwiki:literature <문헌노트 경로> [--dry-run]` |
| `status` | 마일스톤 보고서 생성, 고아 노트·성장 태그 승급 후보 제시 | `/llmwiki:status [--milestone w05\|w10\|w15]` |

`literature`는 모드가 둘이다. 문헌노트 경로를 주면 승격이고, `--from`을 주면 6.Resources에 넣은 교재와 내 노트로 문헌노트를 새로 만든다.

```
/llmwiki:literature --from 6.Resources/화공열역학_3장.pdf --notes 1.Fleeting_Notes/20260918-1430-엔트로피.md --source "화공열역학 3주차"
```

생성 모드에서 하이라이트는 교재 원문을 글자 그대로 인용하고 위치(`(슬라이드 12)`·`(p. 5)`)를 붙이며, `**나의 메모**:`는 LLM이 쓰지 않는다 — 내 노트에 같은 주제 문장이 있으면 그대로 옮기고 없으면 빈칸으로 둔다. `.pdf`는 Read 도구로 읽고 `.pptx`는 `skills/_shared/scripts/doc_text.py`가 슬라이드별 텍스트를 뽑는다(표준 라이브러리만 쓴다).

스킬 본문에는 폴더 이름이 없다. 모든 경로는 위키 루트의 `llmwiki.json`에서 읽으므로 폴더 구조를 바꾸려면 설정만 고치면 된다.

### 매주 15분 의식

```
/llmwiki:daily
/llmwiki:promote --only 오늘
/llmwiki:status
git add -A && git commit -m "wiki: 2026-09-09" && git push
```

## 위키 구조

`init`이 만드는 학생 위키다. 폴더 이름은 `llmwiki.json`의 `paths.*`가 정한다.

```
LLMwiki/
├── llmwiki.json               # 설정 (경로·게이트 임계값·프로필)
├── CLAUDE.md                  # 수업 규칙 5줄
├── README.md                  # 폴더 설명 + 15분 의식 + 도구 계약
├── 0.Daily_Notes/             # 하루 한 장
├── 1.Fleeting_Notes/          # 스친 한 줄 생각
├── 2.Literature_Notes/
│   └── Lectures/              # 교수 배포 강의록이 들어가는 자리
├── 3.Permanent_Notes/
│   └── slipbox/index.md       # 루만 번호 트리 (스크립트가 관리)
├── 4.Project/                 # PARA Projects: 마감 있는 과제·발표 + 수업 도구의 출력
├── 5.Areas/                   # PARA Areas: 끝나지 않는 책임
├── 6.Resources/               # PARA Resources: 관심 자료
├── 7.Archives/                # PARA Archives: 끝난 것 보관 (0~3은 처리 단계, 4~7은 PARA 상자)
├── _meta/promotion-log.jsonl  # 승격 판정 기록
└── _reports/                  # 마일스톤 보고서 md·json
```

영구노트 frontmatter: `type`, `source-type`, `title`, `author`, `literature-note`, `date`, `tags`, `luhmann`, `connections.{internal,cross}`. 새 노트에는 `seed` 태그가 붙는다.

## 게이트 규칙

승격에는 세 조건이 모두 필요하다. 판정은 `skills/promote/scripts/gate.py`가 한다.

| 조건 | 기준 | 미달 사유 |
|---|---|---|
| 내 언어로 재작성 | 인용 밖 본문의 8-gram 중복률 ≤ `gate.max_overlap` (기본 0.20) | `자기 말로 재작성 안 됨` |
| 주제 태그 | 성장 태그(`seed`/`growing`/`evergreen`)를 뺀 태그 ≥ 1 | `태그 없음` |
| 관련 노트 링크 | 원본을 뺀 서로 다른 `[[링크]]` ≥ `gate.min_links` (기본 2) | `연결 부족` |

- 중복률은 초안에서 frontmatter, 연결 섹션, `"…"([[원본]])` 형태의 인용 구간을 지운 뒤 잰다. 따옴표와 링크로 정직하게 표시한 인용은 걸리지 않고, 표시 없이 옮긴 문장만 잡힌다.
- **콜드 스타트**: 영구노트가 `gate.cold_start_notes`(기본 5)개 미만이면 링크 기준이 1로 내려가고 원본을 향한 링크도 인정된다. 첫 수업에서 영구노트 0개로 끝나지 않게 하려는 장치다.
- 판정은 PASS / HOLD / DROP 세 갈래다. HOLD는 원본에 `status: hold`와 `review_at`(+14일)을 적고 파일을 옮기지 않으며, 기한이 지나면 다음 스캔에 다시 올라온다. DROP은 반드시 사용자 확인을 받고 `_meta/dropped.md`에 사유만 남긴다. **파일은 어떤 경우에도 지우지 않는다.**
- 5기준(독립성·원자성·연결성·영속성·통찰) 평균은 LLM이 매기지만 게이트를 이기지 못한다. 자세한 규칙은 `skills/_shared/references/`의 `rubric.md`·`gate-rules.md`·`citation-rules.md`에 있다.

## 도구 계약

수업에서 학생이 만드는 도구는 위키의 정해진 자리에만 읽고 쓴다. 경로와 형식이 계약이므로 바꾸지 않는다.

**강의록 정리기 (주2)** — 강의록을 받아 문헌노트 한 장을 쓴다.

- 쓰는 곳: `2.Literature_Notes/Lectures/YYYY-MM-DD_<주제>.md`
- 형식: 하이라이트마다 원문을 `>` 인용으로 옮기고 바로 아래에 `**나의 메모**:` 로 자기 말 해석을 붙인다. `2.Literature_Notes/_template.md`와 같은 모양이며, 이 형식이라야 `/llmwiki:literature`가 세트로 읽는다.

**플래시카드 웹앱 (주3)** — 영구노트에서 문제를 만들고 푼 결과를 기록한다.

- 읽는 곳: `3.Permanent_Notes/*.md` (읽기 전용. 고치지 않는다)
- 쓰는 곳: `4.Project/flashcards/results.jsonl` (한 줄에 한 판, 덧붙이기만)

## 채점 아티팩트

두 산출물이 채점 근거다. 둘 다 스크립트가 쓰고 사람이 고치지 않는다.

**`_meta/promotion-log.jsonl`** — 승격을 시도할 때마다 한 줄이 붙는다.

```json
{"ts":"2026-09-09T15:20:11+09:00","source":"...","title":"...","scores":{"독립성":4,"원자성":5,"연결성":4,"영속성":4,"통찰":4},"avg":4.2,"gate":{"verdict":"PASS","reasons":[],"overlap":0.08,"links":2,"links_required":2,"tags":["회의"],"cold_start":false},"verdict":"PASS","luhmann":"1A3","model":"...","profile":"student"}
```

`ts`는 KST ISO 시각이다. HOLD와 DROP도 남는다. HOLD는 감점 사유가 아니고, 시도하지 않은 것이 감점이다.

**`_reports/milestone_YYMMDD[_wNN].{md,json}`** — `/llmwiki:status`가 만드는 집계다. 폴더별 노트 수, 임시노트 처리 비율, 성장 태그 분포, 노트당 평균 링크 수, 고아 노트 목록, 주차별 승격 건수, HOLD 사유 상위 3개, 마지막 commit 시각이 들어 있다. `.md`는 사람이 읽고 `.json`은 교수 집계 스크립트가 읽는다.

## 교수 프로필

교수 vault처럼 PARA 폴더와 여러 임시노트 타입을 쓰는 곳에서는 학생 설정 대신 교수 프로필을 쓴다.

1. `templates/professor/llmwiki.json`을 vault 루트에 `llmwiki.json`으로 복사한다.
2. `paths.*`를 그 vault의 실제 폴더 이름으로 맞춘다.
3. `owner.github`와 `professor_github`를 자기 계정으로 바꾼다.

학생 프로필과 다른 점은 셋이다.

- `fleeting_types`에 `Daily`·`Weekly`·`Monthly`·`Limitless`가 더 있다. `promote`가 이 폴더들을 함께 훑는다. `fleeting_types`의 각 폴더와 그 **하위 폴더 전체**(Glob `<폴더>/**/*.md`)에서 모으며, `_`로 시작하는 파일(`_template.md` 등)은 제외한다.
- `routing` 키(`project`·`area`·`resource`·`archive`)가 있다. 5기준 평균 2.0~2.9인 노트를 PARA 위치로 옮긴다. 이 키가 없으면 파일을 옮기지 않고 HOLD 표시만 남긴다.
- `profile`이 `professor`다.

기존 vault에 처음 적용할 때는 `--dry-run`으로 판정만 확인한 뒤 실행하기를 권한다.

## 함께 쓰면 좋은 것

- [kepano/obsidian-skills](https://github.com/kepano/obsidian-skills) (MIT) — Obsidian 문법(callout·properties·Dataview 등)을 다룰 때 함께 설치하면 좋다. 이 플러그인은 코드를 포함하지 않고 안내만 한다.

## 개발

```
python -m pytest -q
```

`pytest.ini`가 스크립트 폴더를 `pythonpath`에 넣으므로 설치 없이 돈다. 표준 라이브러리만 쓰고, 파일은 UTF-8(BOM 없음)·LF로 쓴다.

실제 vault의 index로 왕복 손실이 없는지 확인하려면 환경변수를 주고 돌린다.

```
LLMWIKI_REAL_INDEX=<index.md 경로> python -m pytest tests/test_linker.py -q
```

플러그인 자체 검증은 `claude plugin validate .`이다.

## 라이선스

MIT. 차용 문안의 출처는 [NOTICE.md](NOTICE.md)에 적었다 — 승격 3조건과 PASS/HOLD/DROP 판정 문안은 p-changki/devtrail(MIT), Feynman 검사·출력 계약·QA 체크리스트 형식은 mikonos/zettelkasten-agent-skills(MIT)에서 가져왔다.
