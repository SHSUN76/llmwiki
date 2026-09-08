# LLMwiki 규칙 (학생용)

이 폴더는 「화학공학을 위한 AI」 수업의 개인 지식 위키(LLMwiki)입니다. 제텔카스텐 규칙으로 운영합니다.

1. 노트는 `/llmwiki:*` 스킬로만 만듭니다. `daily`(오늘 기록) → `capture`(한 줄 생각) → `promote`(승격) → `literature`(강의록·교재) → `status`(보고서).
2. 원문을 그대로 옮긴 자리는 따옴표와 `[[원본 노트]]` 링크로 표시하고, 나머지는 반드시 자기 말로 씁니다. 복사해 둔 것은 이해한 것이 아닙니다.
3. 영구노트의 루만 번호(예 `1A1a`)와 `slipbox/index.md`는 스크립트가 관리합니다. 손으로 번호를 만들거나 index를 고치지 않습니다.
4. 매 실습 마지막 15분: `/llmwiki:daily` → `/llmwiki:promote --only 오늘` → `git add -A && git commit -m "wiki: <날짜>" && git push`.
5. `_meta/promotion-log.jsonl`과 `_reports/`는 채점 자료입니다. 지우거나 고치지 않습니다.

폴더: `0.Daily_Notes` 일일 기록 · `1.Fleeting_Notes` 임시노트 · `2.Literature_Notes` 문헌노트(강의록은 `Lectures/`) · `3.Permanent_Notes` 영구노트 · `4.Project` 도구 출력.
