# PRD Research Archive

이 폴더는 `PRD.md` 방향을 잡기 위한 **사전 리서치 산출물**(agentic workflow 탐색 결과)을 누적 저장하기 위한 공간입니다.

## 현재 포함된 내용
- `prompt/prd_teammate_executable.md`에서 정의한 Phase 1 분기별 Teammate 결론(시장/사용자/기술/비즈니스)
- 각 Branch에서 산출된 “Must-have / Risks / Validate in next 2 weeks / KPI” 류의 구조화된 메모

## 저장된 항목 요약
- Market Researcher: Optimistic (완료), Cautious (완료)
- User Experience Researcher: Edge Case (완료), Mainstream (완료)
- Tech Architect: Monolithic (완료), Microservices (Aborted / 내용 미완)
- Business Strategist: Aggressive (완료), Sustainable (완료)

## 다음 단계
- 추가 심층조사(미완된 Tech Microservices 포함)를 수행한 뒤
- `prompt/prd-research/`의 모든 결과를 종합하여 `PRD.md`의 최종 방향(구조/범위/Green-Yellow-Red 등)을 확정합니다.

## PRD Research Archive (local-first, non-SaaS)

This folder archives teammate research outputs used to set the direction for a future `PRD.md`.

### Scope constraints (non-negotiable)
- **Local-first**: the system runs on the user's local computer.
- **Non-SaaS**: no hosted backend assumed for core functionality.
- **Pre-PRD phase**: these are research inputs; they are **not** the PRD itself.

### Contents
- `index.md`: current inventory + gaps.
- `user-edge-case.md`: edge-case persona research (offline/air-gapped).
- `user-mainstream.md`: mainstream persona research (pragmatic builder, ops-minded team dev).
- `tech-monolithic-mvp.md`: monolithic/fast-ship architecture direction for local runner.
- `tech-componentized-architecture.md`: componentized (multi-process) architecture direction for long-term.
- `business-aggressive.md`: aggressive GTM & monetization for local-first distribution.
- `business-sustainable.md`: sustainable GTM & monetization for local-first distribution.

