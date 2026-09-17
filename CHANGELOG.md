# Changelog

이 파일은 [Keep a Changelog](https://keepachangelog.com/ko/1.1.0/) 형식을 따른다.

## [0.2.1] - 2026-09-18

### Fixed

- `init`이 GitHub 원격을 `https://` 주소로 고정한다. 교내망에서 22번 포트(SSH)가 막혀 `git@github.com:` 원격의 push가 통째로 실패하던 문제를 막는다.
