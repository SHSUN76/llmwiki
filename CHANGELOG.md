# Changelog

이 파일은 [Keep a Changelog](https://keepachangelog.com/ko/1.1.0/) 형식을 따른다.

## [0.2.1] - 2026-09-18

### Added

- `/llmwiki:literature --from <교재 파일>` 생성 모드. 수업 교재(pptx·pdf·md)와 내 노트로 문헌노트를 새로 만든다. 하이라이트는 교재 원문 그대로 인용하고 `**나의 메모**:`는 학생 문장이거나 빈칸이다. pptx 텍스트 추출은 새 `skills/_shared/scripts/doc_text.py`(표준 라이브러리)가 맡는다.

### Fixed

- `init`이 GitHub 원격을 `https://` 주소로 고정한다. 교내망에서 22번 포트(SSH)가 막혀 `git@github.com:` 원격의 push가 통째로 실패하던 문제를 막는다.
