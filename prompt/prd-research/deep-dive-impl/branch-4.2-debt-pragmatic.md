## BRANCH 4.2: 실용적 부채 관리 전략

### 1. 부채 레지스터 시스템

```yaml
# TECHNICAL_DEBT_REGISTER.yaml
# 이 파일은 수동 + 자동으로 관리됨
# 자동: scripts/sync_debt_register.py가 DEBT 주석과 동기화

metadata:
  last_updated: "2024-01-15"
  total_items: 12
  p1_count: 0    # P1이 0이어야 커밋 가능
  p2_count: 4
  p3_count: 8

items:
  - id: "DEBT-001"
    title: "Claude API 에러 핸들링 미비"
    priority: 2              # 1=긴급, 2=이번달, 3=나중에
    category: "resilience"   # resilience|security|testing|architecture|performance
    
    # 부채 비용 측정
    impact:
      probability: "high"    # 이 부채가 문제를 일으킬 확률
      blast_radius: "medium" # 문제 발생 시 영향 범위
      fix_effort: "2h"       # 수정에 필요한 시간
      daily_interest: "0.5h" # 이 부채로 매일 낭비되는 시간 (느린 디버깅 등)
    
    location:
      file: "src/planning/generator.py"
      line: 47
    
    description: |
      API rate limit, timeout 에러를 단순 raise로 처리.
      사용자에게 의미없는 에러 메시지 노출.
    
    acceptance_criteria: |
      - RateLimitError → 자동 재시도 (exponential backoff)
      - TimeoutError → 사용자에게 명확한 메시지
      - APIError → 에러 코드별 처리
    
    created_date: "2024-01-10"
    target_date: "2024-02-10"
    owner: "sj"

  - id: "DEBT-002"
    title: "YAML 플랜 파일에 스키마 버전 없음"
    priority: 3
    category: "architecture"
    impact:
      probability: "medium"
      blast_radius: "high"    # 나중에 스키마 변경 시 모든 기존 플랜 깨짐
      fix_effort: "3h"
      daily_interest: "0h"    # 지금 당장은 문제없음
    location:
      file: "src/core/models.py"
      line: 15
    description: |
      WorkflowPlan 모델에 schema_version 필드 없음.
      스키마 변경 시 하위 호환성 없음.
    acceptance_criteria: |
      - schema_version 필드 추가
      - 버전별 마이그레이션 로직
    created_date: "2024-01-10"
    target_date: "2024-03-01"
    owner: "sj"
```

```python
# scripts/sync_debt_register.py
"""
DEBT 주석 ↔ DEBT_REGISTER.yaml 동기화
코드의 DEBT 주석이 레지스터의 단일 진실 소스

실행: python scripts/sync_debt_register.py --check  (CI용, 불일치 시 실패)
     python scripts/sync_debt_register.py --sync   (동기화)
"""
import argparse
import sys
from pathlib import Path

import yaml

from debt_tracker import scan_debt, DebtItem


def sync_register(
    register_path: Path,
    src_dir: Path,
    check_only: bool = False,
) -> int:
    """
    Returns: 0 (OK), 1 (불일치 or P1 존재)
    """
    code_debts = scan_debt(src_dir)
    register = yaml.safe_load(register_path.read_text(encoding="utf-8"))
    
    registered_ids = {item["id"] for item in register["items"]}
    
    # 코드에서 @debt-id:DEBT-XXX 태그로 레지스터 항목 연결
    linked_ids: set[str] = set()
    for debt in code_debts:
        if debt.description.startswith("@"):
            linked_ids.add(debt.description.split()[0][1:])
    
    orphaned = registered_ids - linked_ids
    unregistered = [d for d in code_debts if not any(
        d.description.startswith(f"@{rid}") for rid in registered_ids
    )]
    
    issues = []
    if orphaned:
        issues.append(f"레지스터에만 있고 코드에 없는 부채: {orphaned}")
    if unregistered:
        issues.append(f"코드에만 있고 레지스터에 없는 부채: {len(unregistered)}개")
    
    p1_items = [d for d in code_debts if d.priority == 1]
    if p1_items:
        issues.append(f"P1 부채 {len(p1_items)}개 발견 - 즉시 해소 필요!")
    
    if issues:
        for issue in issues:
            print(f"  ⚠️  {issue}")
        return 1
    
    if not check_only:
        # 레지스터 통계 업데이트
        register["metadata"]["total_items"] = len(register["items"])
        register["metadata"]["p1_count"] = sum(
            1 for i in register["items"] if i["priority"] == 1
        )
        register_path.write_text(
            yaml.dump(register, allow_unicode=True, sort_keys=False),
            encoding="utf-8",
        )
        print("Debt register synced.")
    
    return 0
```

---

### 2. 전략적으로 허용하는 부채 목록

#### Month 1에 허용되는 부채 10가지

```python
# ── 허용 부채 1: 에러 메시지 간소화 ──────────────────────────────
# DEBT[P3]: @DEBT-011 에러 메시지 한국어/영어 혼용, i18n 미적용
raise ValueError("YAML parsing failed")  # 영어 OK at Month 1

# ── 허용 부채 2: 설정 파일 단순 구조 ──────────────────────────────
# DEBT[P3]: @DEBT-012 설정 계층화 미비 (user/system/project 구분 없음)
config = yaml.safe_load(Path("config.yaml").read_text())

# ── 허용 부채 3: 로깅 최소화 ──────────────────────────────────────
# DEBT[P3]: @DEBT-013 구조적 로깅 미적용 (JSON 로그 없음)
print(f"Executing step: {step.name}")  # print OK at Month 1

# ── 허용 부채 4: CLI UX 미완성 ────────────────────────────────────
# DEBT[P3]: @DEBT-014 진행 상태 표시 없음 (spinner, progress bar)
# 기능 동작은 하지만 UX 미완성 → Month 4에 개선

# ── 허용 부채 5: 성능 최적화 미적용 ──────────────────────────────
# DEBT[P3]: @DEBT-015 플랜 파싱 캐싱 없음
# 매번 파싱 → Month 4에 캐싱 추가

# ── 허용 부채 6: 문서화 미비 ──────────────────────────────────────
# DEBT[P3]: @DEBT-016 docstring 없는 내부 메서드
def _build_retry_config(self) -> RetryConfig:
    return RetryConfig(max_attempts=3)  # docstring 없어도 OK

# ── 허용 부채 7: 테스트 커버리지 부족 ────────────────────────────
# DEBT[P2]: @DEBT-017 CLI 레이어 테스트 없음
# 핵심 로직(planning, execution) 테스트는 필수
# CLI 레이어는 Month 2에 추가

# ── 허용 부채 8: 단일 실행 모드만 지원 ───────────────────────────
# DEBT[P3]: @DEBT-018 병렬 실행 미지원 (순차 실행만)
for step in plan.steps:
    executor.execute(step)  # 병렬화는 나중에

# ── 허용 부채 9: 설정 검증 최소화 ────────────────────────────────
# DEBT[P2]: @DEBT-019 config.yaml 스키마 검증 없음
# Pydantic 모델 있지만 config는 raw dict로 처리 중

# ── 허용 부채 10: 플러그인 아키텍처 미비 ─────────────────────────
# DEBT[P3]: @DEBT-020 도구 등록이 하드코딩됨
AVAILABLE_TOOLS = ["file_copy", "shell_exec", "git_commit"]
# → Month 5에 플러그인 시스템으로 교체
```

#### Month 3에 반드시 해소해야 할 부채 5가지

```python
# ── 해소 부채 1: API 키 환경변수 검증 ────────────────────────────
# ❌ Month 1 코드 (해소 전)
api_key = os.environ.get("ANTHROPIC_API_KEY", "")  # 빈 문자열 통과

# ✅ Month 3 코드 (해소 후)
from pydantic import SecretStr
from pydantic_settings import BaseSettings

class AppSettings(BaseSettings):
    anthropic_api_key: SecretStr  # 없으면 시작 시 즉시 실패
    max_plan_steps: int = 20
    execution_timeout: int = 300
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )

# ── 해소 부채 2: 실행 결과 영속성 ────────────────────────────────
# ❌ Month 1: 실행 결과가 메모리에만 존재
result = executor.run(plan)
# → 프로세스 종료 시 소실

# ✅ Month 3: 실행 이력 Git에 커밋
class ExecutionRepository:
    def save_execution(
        self, 
        plan: WorkflowPlan, 
        result: ExecutionResult,
    ) -> str:  # commit SHA 반환
        run_dir = self._runs_dir / result.run_id
        run_dir.mkdir()
        (run_dir / "plan.yaml").write_text(plan.model_dump_yaml())
        (run_dir / "result.yaml").write_text(result.model_dump_yaml())
        
        repo = git.Repo(self._repo_path)
        repo.index.add([str(run_dir)])
        commit = repo.index.commit(
            f"run: {plan.name} [{result.status}] at {result.started_at}"
        )
        return commit.hexsha

# ── 해소 부채 3: 롤백 메커니즘 ───────────────────────────────────
# ❌ Month 1: 실패 시 방치
try:
    executor.execute(step)
except StepExecutionError:
    raise  # 이미 한 작업은 그대로

# ✅ Month 3: 롤백 지원
class RollbackManager:
    """
    실행한 각 단계의 역작업 저장
    실패 시 역순으로 롤백
    """
    _undo_stack: list[Callable[[], None]] = field(default_factory=list)
    
    def register_undo(self, undo_fn: Callable[[], None]) -> None:
        self._undo_stack.append(undo_fn)
    
    def rollback_all(self) -> None:
        for undo_fn in reversed(self._undo_stack):
            try:
                undo_fn()
            except Exception as e:
                logger.error("Rollback step failed: %s", e)

# ── 해소 부채 4: 프롬프트 버전 잠금 ──────────────────────────────
# ❌ Month 1: "current" 포인터만 사용
# → 프롬프트 업데이트 시 이전 실행과 결과 달라짐

# ✅ Month 3: 실행 기록에 프롬프트 버전 포함
@dataclass
class ExecutionContext:
    prompt_versions: dict[str, str]  # {"plan_generation": "v1", ...}
    model_version: str               # "claude-3-5-sonnet-20241022"
    
    # 동일한 context로 재실행 시 동일한 결과 보장

# ── 해소 부채 5: 구조적 로깅 ─────────────────────────────────────
# ❌ Month 1: print 문
print(f"Step {step.name} completed")

# ✅ Month 3: 구조적 로깅
import structlog

logger = structlog.get_logger()
logger.info(
    "step_completed",
    step_name=step.name,
    duration_ms=elapsed_ms,
    tool=step.tool,
    run_id=context.run_id,
)
```

#### v1.0 출시 전 절대 남기면 안 되는 부채 3가지

```python
# ══ 절대 불가 부채 1: 경로 순회 검증 없음 ══════════════════════
# 이 제품은 로컬 파일시스템을 직접 조작
# 경로 순회 공격 → 시스템 파일 삭제/유출 가능

# ❌ 절대 불가
def read_file(path: str) -> str:
    return Path(path).read_text()  # ../../../etc/passwd 가능

# ✅ 필수 구현
class SafeFileSystem:
    def __init__(self, allowed_root: Path) -> None:
        self._root = allowed_root.resolve()
    
    def safe_path(self, user_path: str) -> Path:
        """경로 순회 공격 방지"""
        resolved = (self._root / user_path).resolve()
        if not resolved.is_relative_to(self._root):
            raise PermissionError(
                f"Path {user_path!r} escapes allowed root {self._root}"
            )
        return resolved

# ══ 절대 불가 부채 2: shell=True subprocess ════════════════════
# ❌ 절대 불가: 셸 인젝션 가능
import subprocess
subprocess.run(step.parameters["command"], shell=True)  # 인젝션 위험

# ✅ 필수 구현: 인수 리스트로 분리
subprocess.run(
    shlex.split(step.parameters["command"]),  # 토큰화
    shell=False,                               # 셸 없이 직접 실행
    capture_output=True,
    timeout=step.timeout_seconds,
    cwd=str(safe_working_dir),
)

# ══ 절대 불가 부채 3: 무한 실행 가능 ══════════════════════════
# ❌ 절대 불가: 타임아웃 없는 LLM 호출
response = client.messages.create(
    model="claude-3-5-sonnet-20241022",
    messages=[{"role": "user", "content": prompt}]
)  # 무한 대기 가능

# ✅ 필수 구현
import signal
from contextlib import contextmanager

@contextmanager
def timeout_guard(seconds: int, operation: str):
    def _handler(signum, frame):
        raise TimeoutError(f"{operation} exceeded {seconds}s timeout")
    
    signal.signal(signal.SIGALRM, _handler)
    signal.alarm(seconds)
    try:
        yield
    finally:
        signal.alarm(0)  # 타이머 해제

with timeout_guard(30, "LLM plan generation"):
    response = client.messages.create(...)
```

---

### 3. 부채 비용 측정 방법

```python
# scripts/debt_cost_calculator.py
"""
기술 부채 실제 비용 계산
공식: 총비용 = 수정비용 + (일일이자 × 잔여일수)
"""
from dataclasses import dataclass
from datetime import date
from pathlib import Path
import yaml


@dataclass
class DebtCostAnalysis:
    debt_id: str
    title: str
    
    # 비용 요소 (시간 단위: 분)
    fix_cost_minutes: int       # 지금 고치면 드는 시간
    daily_interest_minutes: int # 이 부채로 매일 낭비되는 시간
    days_remaining: int         # 목표 해소일까지 남은 일수
    
    @property
    def total_cost_if_fixed_now(self) -> int:
        return self.fix_cost_minutes
    
    @property
    def total_cost_if_fixed_at_deadline(self) -> int:
        """미루면 드는 총 비용"""
        return self.fix_cost_minutes + (
            self.daily_interest_minutes * self.days_remaining
        )
    
    @property
    def should_fix_now(self) -> bool:
        """
        리팩토링 판단 기준:
        미루는 비용 > 지금 고치는 비용 이면 즉시 수정
        """
        return (
            self.total_cost_if_fixed_at_deadline > 
            self.fix_cost_minutes * 1.5  # 50% 초과 시 즉시 수정
        )
    
    @property
    def annual_interest_rate(self) -> float:
        """연간 이자율 (금융 부채 비유)"""
        if self.fix_cost_minutes == 0:
            return 0.0
        return (self.daily_interest_minutes * 365) / self.fix_cost_minutes * 100


def analyze_register(register_path: Path) -> list[DebtCostAnalysis]:
    register = yaml.safe_load(register_path.read_text(encoding="utf-8"))
    analyses = []
    
    for item in register["items"]:
        impact = item.get("impact", {})
        target = date.fromisoformat(item.get("target_date", "2024-12-31"))
        days_left = (target - date.today()).days
        
        # "2h" → 120분 변환
        fix_effort = impact.get("fix_effort", "0h")
        fix_minutes = _parse_duration(fix_effort)
        
        daily_interest = _estimate_daily_interest(
            probability=impact.get("probability", "low"),
            blast_radius=impact.get("blast_radius", "low"),
        )
        
        analyses.append(DebtCostAnalysis(
            debt_id=item["id"],
            title=item["title"],
            fix_cost_minutes=fix_minutes,
            daily_interest_minutes=daily_interest,
            days_remaining=max(0, days_left),
        ))
    
    return sorted(analyses, key=lambda x: x.annual_interest_rate, reverse=True)


def _parse_duration(duration: str) -> int:
    """'2h' → 120, '30m' → 30"""
    if duration.endswith("h"):
        return int(duration[:-1]) * 60
    if duration.endswith("m"):
        return int(duration[:-1])
    return 0


def _estimate_daily_interest(probability: str, blast_radius: str) -> int:
    """확률 × 영향 = 일일 이자 (분)"""
    prob_map = {"low": 0.1, "medium": 0.3, "high": 0.7}
    radius_map = {"low": 15, "medium": 60, "high": 240}  # 분 단위
    
    return int(prob_map.get(probability, 0.1) * radius_map.get(blast_radius, 15))


if __name__ == "__main__":
    analyses = analyze_register(Path("TECHNICAL_DEBT_REGISTER.yaml"))
    
    print("\n=== DEBT COST ANALYSIS ===")
    print(f"{'ID':<12} {'Annual Rate':>12} {'Fix Now':>10} {'Fix Later':>10} {'Decision'}")
    print("-" * 60)
    
    for a in analyses:
        decision = "🔴 FIX NOW" if a.should_fix_now else "🟡 schedule"
        print(
            f"{a.debt_id:<12} {a.annual_interest_rate:>11.0f}% "
            f"{a.fix_cost_minutes:>9}m {a.total_cost_if_fixed_at_deadline:>9}m "
            f" {decision}"
        )
```

---

### 4. AI 특화 부채 관리

#### 프롬프트 버전 관리 + 모델 버전 고정

```python
# src/config/model_config.py
"""
모델 버전 고정: 하드코딩이 아닌 설정 파일로 관리
절대 소스코드에 모델 버전 문자열 직접 쓰지 않음
"""
from pydantic import BaseModel, field_validator


class ModelConfig(BaseModel):
    """모델 버전 중앙 관리"""
    
    # 각 작업별 모델 버전 명시적 지정
    plan_generation: str = "claude-3-5-sonnet-20241022"
    plan_validation: str = "claude-3-haiku-20240307"  # 검증은 빠른 모델
    error_diagnosis: str = "claude-3-5-sonnet-20241022"
    
    # 모델 별칭 → 구체 버전 매핑
    # "latest" 같은 별칭 절대 사용 금지
    aliases: dict[str, str] = {
        "fast": "claude-3-haiku-20240307",
        "smart": "claude-3-5-sonnet-20241022",
    }
    
    @field_validator("plan_generation", "plan_validation", mode="before")
    @classmethod
    def validate_model_version(cls, v: str) -> str:
        """날짜 포함 구체 버전만 허용 (별칭 금지)"""
        if not any(char.isdigit() for char in v):
            raise ValueError(
                f"Model version must include date: {v!r}\n"
                f"Use specific version like 'claude-3-5-sonnet-20241022'"
            )
        return v


# models.yaml - 버전 설정 분리
# model_versions:
#   plan_generation: "claude-3-5-sonnet-20241022"
#   # 변경 시 여기만 수정, git blame으로 언제 바뀌었는지 추적 가능
```

#### 골든 테스트 시스템

```python
# tests/golden/test_golden_outputs.py
"""
골든 테스트: LLM 출력 변화 감지
모델 업그레이드 시 출력이 바뀌면 즉시 감지
"""
import os
import pytest
from pathlib import Path

GOLDEN_DIR = Path(__file__).parent / "golden_fixtures"


@pytest.mark.llm  # 실제 LLM 호출 - CI에서 선택적 실행
class TestGoldenOutputs:
    """
    골든 테스트 전략:
    1. 대표 입력 5개 선정
    2. 실제 LLM 출력을 골든 파일로 저장
    3. 모델 변경 시 골든 파일 업데이트 검토
    """
    
    GOLDEN_INPUTS = [
        "simple_file_copy",
        "git_commit_workflow", 
        "data_pipeline_etl",
        "security_scan",
        "multi_step_refactor",
    ]
    
    @pytest.mark.parametrize("input_name", GOLDEN_INPUTS)
    def test_plan_structure_matches_golden(
        self,
        input_name: str,
        real_plan_generator: PlanGenerator,  # 실제 LLM 호출
        assert_matches_golden,
    ) -> None:
        """
        완전한 텍스트 일치가 아닌 구조적 일치 검증
        → LLM의 자연어 변동성 허용, 구조는 고정
        """
        user_input = (
            GOLDEN_DIR / "inputs" / f"{input_name}.txt"
        ).read_text().strip()
        
        plan = real_plan_generator.generate(
            user_input=user_input,
            context=standard_test_context(),
        )
        
        # 구조적 골든 비교 (텍스트가 아닌 스키마 수준)
        structural_repr = {
            "step_count": len(plan.steps),
            "tools_used": sorted({s.tool for s in plan.steps}),
            "has_rollback": any(
                s.on_failure == StepFailurePolicy.ROLLBACK 
                for s in plan.steps
            ),
            "requires_confirmation": plan.requires_confirmation,
        }
        
        assert_matches_golden(
            str(structural_repr), 
            f"plan_structure_{input_name}",
        )
```

---

### 5. 부채 상환 루틴

```markdown
## 주간 15분 부채 체크 (매주 금요일)

### 체크리스트
- [ ] `python scripts/debt_tracker.py` 실행 → P1 부채 없음 확인
- [ ] 이번 주 추가된 DEBT 주석 검토
- [ ] 만료된 부채 (target_date 초과) 처리 결정
- [ ] 빠른 수정 가능한 P3 부채 1개 처리 ("보이 스카우트 룰")

소요 시간: 15분
```

```python
# scripts/weekly_debt_check.sh
#!/bin/bash
# 매주 금요일 자동 실행 (cron: 0 17 * * 5)

echo "=== Weekly Debt Check ==="
echo "Date: $(date)"

# 1. P1 부채 확인 (있으면 경고)
python scripts/debt_tracker.py
DEBT_EXIT=$?

# 2. 만료된 부채 확인
python scripts/check_overdue_debts.py

# 3. 부채 트렌드 (이번 주 추가/해소)
git diff HEAD~7 -- TECHNICAL_DEBT_REGISTER.yaml | \
  grep "^[+-]  - id:" | \
  sed 's/^+/ADDED: /;s/^-/REMOVED: /'

echo "=== End of Debt Check ==="
exit $DEBT_EXIT
```

```python
# 보이 스카우트 룰 구현 예시
# "코드를 찾았을 때보다 더 깨끗하게 두고 떠나라"

# 다른 기능 작업 중 발견한 개선점
# ❌ 그냥 지나침
# ✅ 작은 개선 즉시 적용

# 원칙: 발견한 코드와 관련된 경우, 30분 이내 수정 가능한 경우만
# 그 이상은 DEBT 주석으로 등록하고 레지스터에 추가

def process_plan(self, plan_data: dict) -> WorkflowPlan:
    # 보이 스카우트 개선 전: magic number
    if len(plan_data.get("steps", [])) > 50:  
        raise ValueError("Too many steps")
    
    # 보이 스카우트 개선 후: 상수로 명명
    MAX_STEPS = 50  # 한 플랜의 최대 단계 수
    if len(plan_data.get("steps", [])) > MAX_STEPS:
        raise ValueError(f"Plan exceeds maximum {MAX_STEPS} steps")
```

---

## 결론: 1인 6개월 MVP를 위한 현실적 권고

### Branch 4.1 vs 4.2 비교

| 기준 | Branch 4.1 (최소화) | Branch 4.2 (실용 관리) | 1인 MVP 적합도 |
|------|---------------------|------------------------|----------------|
| 초기 투자 | 높음 (2주 설정) | 낮음 (3일 설정) | 4.2 우위 |
| 장기 속도 | 빠름 | 보통 | 4.1 우위 |
| 인지 부하 | 높음 | 낮음 | 4.2 우위 |
| 보안 수준 | 높음 | 높음 (선택적) | 동등 |
| 팀 확장성 | 우수 | 보통 | 4.1 우위 |

**권고: Branch 4.1의 핵심 + Branch 4.2의 실용성 결합**

```
Week 1-2: Branch 4.1의 인프라 구축 (pyproject.toml, pre-commit, 아키텍처)
Week 3+:  Branch 4.2의 전략적 부채 허용으로 개발 속도 확보
Month 3:  Branch 4.2의 부채 레지스터로 체계적 상환
```

---

### PRD.md에 명시해야 할 부채 관리 원칙

```markdown
## 기술 부채 관리 원칙

### 허용 원칙
1. 모든 의도적 부채는 DEBT 주석 + 레지스터 등록 필수
2. P1 부채(보안/데이터 손실 관련)는 당일 해소
3. P2 부채는 30일 내 해소
4. 월 첫째 주는 부채 상환 스프린트

### 아키텍처 불변 규칙
- core/ 모듈은 외부 의존성 없음 (순수 Python + Pydantic)
- 계층 간 의존성 방향 단방향 유지
- Protocol로 인터페이스 분리 (테스트 가능성 보장)

### 품질 게이트 (CI 통과 필수)
- mypy strict 통과
- ruff 오류 없음
- bandit medium 이상 없음
- 테스트 커버리지 70% 이상
- P1 DEBT 주석 없음
```

---

### 절대 허용하면 안 되는 부채 (이 제품 특화)

이 제품은 **로컬 파일시스템을 직접 조작**하고 **LLM이 생성한 명령을 자동 실행**하는 특성상, 아래 부채는 MVP에서도 절대 허용 불가입니다.

```
╔══════════════════════════════════════════════════════════════╗
║          절대 허용 불가 부채 (Non-Negotiable)                ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  1. 경로 순회 검증 없음                                      ║
║     이유: LLM이 ../../../etc/passwd 생성 가능               ║
║     영향: 시스템 전체 파일 노출/삭제                         ║
║                                                              ║
║  2. shell=True subprocess                                    ║
║     이유: 프롬프트 인젝션 → 셸 인젝션 연계 공격              ║
║     영향: 임의 명령 실행                                     ║
║                                                              ║
║  3. LLM 출력 무검증 실행                                     ║
║     이유: 환각으로 잘못된 파일 삭제/덮어쓰기                  ║
║     영향: 데이터 영구 손실                                   ║
║                                                              ║
║  4. 실행 타임아웃 없음                                       ║
║     이유: 무한 루프 플랜 생성 가능                            ║
║     영향: 리소스 고갈, 강제 종료 불가                         ║
║                                                              ║
║  5. API 키 소스코드 하드코딩                                 ║
║     이유: git push 시 즉시 유출                              ║
║     영향: 금전적 손실, 계정 탈취                             ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
```

이 5가지는 기능 출시 전 코드 리뷰 체크리스트에 명시하고, pre-commit hooks와 bandit 설정으로 자동 감지하는 것을 강력히 권장합니다. 나머지 부채는 "전략적 자산"으로 관리할 수 있지만, 이 5가지는 단 하나의 인시던트로도 사용자의 시스템 전체를 위험에 빠뜨릴 수 있기 때문입니다.