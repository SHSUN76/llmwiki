---
name: literature
description: 문헌노트(교수 배포 강의록·교재 장 요약·논문 노트) 한 개를 읽어 "하이라이트 + 나의 메모" 세트마다 영구노트 승격을 시도한다. 채점은 LLM이, 게이트와 루만 번호는 스크립트가 판정하며 원본 문헌노트는 보존한다. "강의록 승격해줘", "이 문헌노트 정리해줘", "책 노트에서 영구노트 뽑아줘", 주2 정리기가 만든 강의록 노트를 처리할 때 쓴다. 사용법 - /llmwiki:literature <문헌노트 경로> [--dry-run]
---

# 문헌노트 → 영구노트 승격

인자: `$ARGUMENTS`

절차는 `promote`와 같고, 입력이 문헌노트 한 개이며 채점 단위가 "하이라이트 + 나의 메모" 세트라는 점만 다르다. 승격 여부의 최종 문지기는 여기서도 스크립트다.

## 0. 준비 (반드시 먼저)

1. 설정을 읽는다. 인자는 없다.

```
python "${CLAUDE_PLUGIN_ROOT}/skills/_shared/scripts/wikiconf.py"
```

`{"error": ...}`(종료 코드 2)면 "LLMwiki 폴더 안에서 실행하세요"를 안내하고 멈춘다. 아래의 `<root>`·`paths.*`·`gate.*`는 전부 이 JSON에서 읽는다.

2. Read 도구로 `${CLAUDE_PLUGIN_ROOT}/skills/_shared/references/rubric.md`, `citation-rules.md`, `gate-rules.md`를 읽는다. 채점은 rubric의 **문헌노트 표**와 문헌 특화 가산·감점 규칙을 쓴다.

3. 콜드 스타트 판정. Glob 도구로 `<root>/<paths.permanent>/**/*.md`(하위 폴더 포함)를 세되, `paths.index`가 들어 있는 하위 폴더 아래의 파일과 `_`로 시작하는 파일은 제외한다(`report.py`의 영구노트 계산 방식과 같다). 이 수가 `gate.cold_start_notes`보다 작으면 콜드 스타트 모드이며 4단계 게이트에 `--cold-start`를 붙인다.

## 1. 입력 확인

`$ARGUMENTS`의 문헌노트 경로를 Read한다. 경로가 없으면 `paths.literature` 아래에서 frontmatter `processed: false`인 문헌노트 목록을 보여 주고 하나를 고르게 한다.

frontmatter에서 `title`·`source`·`date`를 읽는다. `source-type`을 정한다.

| 출처 | `source-type` |
|---|---|
| 교수 배포 강의록·수업 자료 | `lecture` |
| 교재·단행본의 장 | `book` |
| 논문 | `paper` |

frontmatter만으로 판단이 안 되면 사용자에게 한 번 묻는다.

## 2. Extractor — 세트 단위

문헌노트를 `>` 인용(하이라이트)과 바로 뒤의 `**나의 메모**:` 로 이루어진 **세트**로 쪼갠다. 한 세트가 하나의 채점 단위다.

- 메모가 있는 하이라이트를 먼저 처리한다.
- 메모 없는 단독 하이라이트는 5기준 사전 추정 평균이 3.0 이상인 세트만 후보로 올린다(3.0 미만은 표에 `후보 제외`로 표시하고 이유 한 줄). 후보로 올리더라도 통찰 점수를 낮게 준다.
- 한 세트에 주장이 둘이면 둘로 나눈다. Feynman 검사에 걸리면 **한 번만** 되묻는다.

## 3. Analyzer

세트마다 rubric의 문헌노트 5기준으로 1~5점을 매기고 표로 보여 준다.

| # | 하이라이트 | 나의 메모 | 독립성 | 원자성 | 연결성 | 영속성 | 통찰 | 평균 | 판정 |

문헌 특화 규칙: 메모 없는 단독 하이라이트는 통찰 감점, 하이라이트에 자기 메모가 붙어 있으면 통찰 가산, 저자의 주장을 자신의 경험·기존 지식과 연결했으면 연결성 가산.

평균이 `gate.pass_avg` 이상이면 PASS 후보, 2.0~2.9는 HOLD, 2.0 미만은 DROP 후보다.

3.0~3.4 경계 구간은 보완 제안 1회 후 재채점. 재채점 평균 ≥ 3.5면 후보로 올리고, 미만이면 HOLD(교수 프로필은 `routing`이 있으면 PARA 라우팅)로 확정한다. 재채점은 한 번만.

## 4. Converter → Gate → Linker → 확인

`promote`의 4~7단계를 그대로 따른다. 문헌노트에서만 다른 점은 초안 frontmatter다.

- `source-type`: 1단계에서 정한 `lecture` | `book` | `paper`
- `literature-note`: `[[<원본 문헌노트 제목>]]`
- `author`: 문헌노트에 저자 정보가 있으면 채우고, 없으면 비운다. 지어내지 않는다
- `tags`: 주제 태그 최대 3개 + `seed`
- `luhmann: ""`, `connections`는 Linker 단계에서 채운다

초안은 `<root>/<paths.meta>/drafts/<제목>.md`에 저장한 뒤 게이트를 돌린다.

```
python "${CLAUDE_PLUGIN_ROOT}/skills/promote/scripts/gate.py" check --draft "<root>/<paths.meta>/drafts/<제목>.md" --source "<문헌노트 경로>" --links-min <gate.min_links> --overlap-max <gate.max_overlap> --ngram <gate.ngram>
```

콜드 스타트 모드이면 `--cold-start`를 붙인다. 출력의 `tags`는 개수가 아니라 주제 태그 목록이다. `HOLD`면 `reasons`를 보여 주고 **한 번만** 고쳐 재판정한다.

원문 표현을 옮긴 자리는 따옴표와 `([[<원본 문헌노트 제목>]])`로 표시한다. 표시 없이 옮긴 문장은 중복률에 잡혀 `자기 말로 재작성 안 됨`으로 HOLD된다.

번호는 반드시 스크립트에서 받는다.

```
python "${CLAUDE_PLUGIN_ROOT}/skills/_shared/scripts/linker.py" parse --index "<root>/<paths.index>"
python "${CLAUDE_PLUGIN_ROOT}/skills/_shared/scripts/linker.py" next --index "<root>/<paths.index>" --parent <부모번호> --relation sequential|branch
```

index가 비어 있으면(`total`이 0) 카테고리 제목을 제안하고 사용자 확인 후 `new-category --index "<root>/<paths.index>" --title "<제목>" --description "<설명>"`을 실행해 `{"section": "1A"}`를 받고, 이어서 `next --section 1A --relation sequential`로 첫 번호를 받는다. `linker.py`는 인자 오류를 포함한 모든 오류를 `{"error": ...}` + 종료 코드 1로 내므로, 오류가 나면 번호를 지어내지 말고 멈춘다.

배치·연결·번호를 표로 보여 주고 승인을 받는다. `--dry-run`이면 여기서 끝낸다.

## 5. 기록 (순서 고정, 세트 하나씩)

1. 초안을 `<root>/<paths.permanent>/<제목>.md`로 저장한다.

2. index에 한 줄 삽입한다.

```
python "${CLAUDE_PLUGIN_ROOT}/skills/_shared/scripts/linker.py" insert --index "<root>/<paths.index>" --number <번호> --title "<제목>" --relation sequential|branch --parent <부모번호>
```

출력의 `inserted`는 들여쓰기를 지운 표시용 문자열이므로 파일에 다시 쓰지 않는다.

3. **원본 문헌노트는 보존한다.** Edit 도구로 두 줄만 고친다. frontmatter의 `processed: false`를 `processed: true`로 바꾸고, 해당 하이라이트 세트 바로 아래(또는 문헌노트 맨 끝)에 `- 승격: [[<제목>]] (<번호>)` 한 줄을 덧붙인다. 하이라이트 원문과 학생의 메모는 지우거나 고치지 않는다.

4. 로그를 남긴다.

```
python "${CLAUDE_PLUGIN_ROOT}/skills/promote/scripts/gate.py" log --log "<root>/<paths.meta>/promotion-log.jsonl" --source "<문헌노트 경로>" --title "<제목>" --verdict PASS --scores "<5기준 JSON>" --gate "<게이트 출력 JSON>" --luhmann <번호> --model "<쓰고 있는 모델 이름>" --profile <profile>
```

모델 이름을 확실히 알 수 없으면 `--model ""`로 둔다(추측해 적지 않는다).

## 6. HOLD · DROP

`promote`의 9단계와 같다. HOLD는 원본 문헌노트 frontmatter에 `status: hold`와 `review_at: <오늘+14일>`을 적고 `--verdict HOLD --luhmann ""`로 로그를 남긴다. 학생 프로필은 파일을 옮기지 않고, 교수 프로필은 설정에 `routing` 키가 있을 때만 PARA 위치로 옮긴다. DROP은 사용자 확인 후 `<root>/<paths.meta>/dropped.md`에 사유를 적고 파일은 남긴다.

## 배치 결과 요약 (표준)

| # | 하이라이트 | 아이디어 | 평균 | 게이트 | 판정 | 번호 |

게이트를 돌리지 않은 줄은 `—`로 둔다. 마지막 줄에 다음을 붙인다.

`PASS n / HOLD n / DROP n. commit·push 하세요.`

## 출력 계약 (hard constraints)

- [ ] 원본 문헌노트의 하이라이트와 학생 메모를 고치지 않았다 (`processed`와 승격 링크 한 줄만 추가)
- [ ] 번호는 항상 `linker.py`가 낸 값만 쓴다
- [ ] 게이트가 HOLD인 상태로 영구노트를 저장하지 않는다
- [ ] index와 원본은 줄 단위로만 고친다
- [ ] 원문을 옮긴 자리는 따옴표와 `[[원본]]`으로 표시했고 나머지는 자기 말이다
- [ ] `literature-note`와 `source-type`을 채웠고 없는 저자·출처를 만들지 않았다
- [ ] 근거 없는 주장은 `(근거 없음)`으로 표시하고 없는 출처를 만들지 않는다
- [ ] 모든 PASS·HOLD·DROP 판정이 promotion-log에 남았다
- [ ] 폴더 이름은 설정의 `paths.*`에서 읽었고 손으로 적지 않았다
