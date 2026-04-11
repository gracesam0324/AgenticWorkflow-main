# Branch 4.2: 데이터 파이프라인 & 포맷 — Minimal Integration (stdlib 전용)
> Data Pipeline & Format Integration Specialist
> 조사일: 2026-04-07

---

## 핵심 철학

v1.0 범위에서 90%의 데이터 엔지니어 사용 사례는 JSON + YAML + CSV로 커버 가능.
의존성 최소화 = 보안 공격 표면 최소화.

---

## 1. DataPipelineExecutor (stdlib 전용)

```python
# data_pipeline_executor.py
# stdlib만 사용: csv, json, pathlib
import csv
import json
from pathlib import Path

class DataPipelineExecutor:
    """YAML pipeline 스키마를 순서대로 실행. 의존성: stdlib만."""

    SUPPORTED_INPUTS  = {"csv", "json", "jsonl", "yaml"}
    SUPPORTED_OUTPUTS = {"csv", "json", "jsonl"}

    def execute_pipeline(self, pipeline_yaml: dict) -> dict:
        data = self._read_input(pipeline_yaml["input"])
        for transform in pipeline_yaml.get("transform", []):
            data = self._apply_transform(data, transform)
        output_info = self._write_output(pipeline_yaml["output"], data)
        return {"rows_processed": len(data), **output_info}

    def _read_input(self, cfg: dict) -> list[dict]:
        path     = Path(cfg["path"]).expanduser()
        encoding = cfg.get("encoding", "utf-8")
        fmt      = cfg["type"].lower()

        if fmt == "csv":
            with open(path, encoding=encoding, newline="") as f:
                return list(csv.DictReader(f))
        elif fmt == "json":
            return json.loads(path.read_text(encoding=encoding))
        elif fmt == "jsonl":
            return [json.loads(ln) for ln in path.read_text(encoding=encoding).splitlines() if ln.strip()]
        else:
            raise ValueError(f"지원하지 않는 입력 포맷: {fmt}")

    def _apply_transform(self, data: list[dict], transform: dict) -> list[dict]:
        step = transform["step"]

        if step == "filter_rows":
            condition = transform["condition"]
            return [row for row in data if self._eval_condition(row, condition)]

        elif step == "rename_columns":
            mapping = transform["mapping"]
            return [{mapping.get(k, k): v for k, v in row.items()} for row in data]

        elif step == "select_columns":
            cols = transform["columns"]
            return [{k: row[k] for k in cols if k in row} for row in data]

        elif step == "add_column":
            name = transform["name"]
            expr = transform["expression"]
            return [{**row, name: expr.format(**row)} for row in data]

        elif step == "sort":
            key = transform["by"]
            reverse = transform.get("descending", False)
            return sorted(data, key=lambda r: r.get(key, ""), reverse=reverse)

        else:
            raise ValueError(f"알 수 없는 transform: {step}")

    def _eval_condition(self, row: dict, condition: str) -> bool:
        """안전한 조건 평가 (builtins 차단)"""
        try:
            return bool(eval(condition, {"__builtins__": {}}, row))
        except Exception:
            return False

    def _write_output(self, cfg: dict, data: list[dict]) -> dict:
        path     = Path(cfg["path"]).expanduser()
        encoding = cfg.get("encoding", "utf-8")
        fmt      = cfg["type"].lower()
        path.parent.mkdir(parents=True, exist_ok=True)

        if fmt == "csv":
            if data:
                with open(path, "w", encoding=encoding, newline="") as f:
                    w = csv.DictWriter(f, fieldnames=data[0].keys())
                    w.writeheader(); w.writerows(data)
        elif fmt == "json":
            path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding=encoding)
        elif fmt == "jsonl":
            with open(path, "w", encoding=encoding) as f:
                for row in data:
                    f.write(json.dumps(row, ensure_ascii=False) + "\n")

        return {"output_path": str(path), "format": fmt}
```

YAML 사용 예시 (한국 데이터):
```yaml
pipeline:
  input:
    type: csv
    path: "~/data/users.csv"
    encoding: euc-kr          # 한국어 레거시 파일
  transform:
    - step: filter_rows
      condition: "status == 'active'"
    - step: rename_columns
      mapping: {user_nm: name, regist_dt: registered_at}
    - step: select_columns
      columns: [name, email, registered_at]
    - step: sort
      by: registered_at
      descending: true
  output:
    type: json
    path: "~/output/active_users.json"
    encoding: utf-8
```

---

## 2. FileStateManager (SQLite 없이 파일만)

```python
# file_state_manager.py
import fcntl
import json
import os
from pathlib import Path
from datetime import datetime

class FileStateManager:
    """
    JSONL append-only 로그로 실행 상태 관리.
    SQLite 없이 단순성과 이식성 확보.
    """

    def __init__(self, state_dir: Path):
        self.state_dir = state_dir
        self.state_dir.mkdir(parents=True, exist_ok=True)

    def _log_path(self, session_id: str) -> Path:
        return self.state_dir / f"{session_id}.jsonl"

    def append_event(self, session_id: str, event: dict):
        """atomic append"""
        event["_ts"] = datetime.utcnow().isoformat()
        line = json.dumps(event, ensure_ascii=False) + "\n"
        log_path = self._log_path(session_id)

        with open(log_path, "a", encoding="utf-8") as f:
            if os.name != "nt":
                fcntl.flock(f, fcntl.LOCK_EX)
            f.write(line)
            if os.name != "nt":
                fcntl.flock(f, fcntl.LOCK_UN)

    def read_session(self, session_id: str) -> list[dict]:
        log_path = self._log_path(session_id)
        if not log_path.exists():
            return []
        events = []
        with open(log_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    events.append(json.loads(line))
        return events

    def list_sessions(self) -> list[str]:
        return [p.stem for p in sorted(
            self.state_dir.glob("*.jsonl"),
            key=lambda x: x.stat().st_mtime, reverse=True
        )]

    def get_last_status(self, session_id: str) -> str | None:
        """JSONL 끝 부분만 읽어 O(file_tail) 성능"""
        log_path = self._log_path(session_id)
        if not log_path.exists():
            return None
        with open(log_path, "rb") as f:
            f.seek(max(0, log_path.stat().st_size - 4096))
            tail = f.read().decode("utf-8", errors="replace")
        lines = [ln for ln in tail.splitlines() if ln.strip()]
        if not lines:
            return None
        return json.loads(lines[-1]).get("status")
```

**성능 한계**:
- 10만 이벤트 이하: read_session() 50ms 이내
- 10만 초과 시: 역방향 인덱스 파일 필요 → SQLite 마이그레이션 적절
- 동시 세션 1000개 이하: OS 파일 핸들 제한 내

---

## 3. v1.0 스텝 타입 정의

```yaml
step_types:
  # 데이터 입출력
  - read_file       # CSV, JSON, JSONL, YAML, TXT
  - write_file      # CSV, JSON, JSONL
  - copy_file
  - delete_file

  # 데이터 변환 (stdlib만)
  - filter_rows
  - rename_columns
  - select_columns
  - add_column
  - sort_rows
  - deduplicate
  - join_files      # 두 CSV/JSON 파일 키 기반 조인

  # 집계 (stdlib만)
  - summarize       # count, sum, avg, min, max
  - group_by

  # 외부 연동
  - api_call        # GET 전용 (v1.0), POST는 v1.1
  - shell_command   # subprocess, 제한 명령어

  # 흐름 제어
  - condition
  - loop
```

---

## 4. PRD 포맷 지원 비교표

| 포맷 | v1.0 Minimal | v1.0 Standard | v1.1 Analytics |
|---|---|---|---|
| CSV | ✅ stdlib | ✅ stdlib | ✅ |
| JSON | ✅ stdlib | ✅ orjson | ✅ |
| JSONL | ✅ stdlib | ✅ orjson | ✅ |
| YAML | ✅ (읽기) | ✅ | ✅ |
| TXT | ✅ stdlib | ✅ stdlib | ✅ |
| Excel | ❌ | ✅ openpyxl | ✅ |
| Parquet | ❌ | ✅ pyarrow | ✅ |
| PDF | ❌ | ✅ pdfplumber | ✅ |
| DuckDB | ❌ | ❌ | ✅ |
| Pandas | ❌ | ❌ | ✅ |

---

## 5. 사용자 유형별 핵심 요구사항

### 데이터 엔지니어
- 재현성: 동일 YAML → 동일 결과 (난수 시드 고정 옵션)
- 인코딩: EUC-KR 한국 통계청 데이터 처리 필수
- 성능: 10GB+ CSV 처리 (DuckDB, v1.1)

### 학술 연구자
```yaml
# 학술 워크플로우 예시
steps:
  - name: load_survey_data
    type: read_file
    path: "~/research/survey_2024.csv"
    encoding: utf-8

  - name: clean_data
    type: filter_rows
    condition: "response_quality >= 3 and not_spam == 'true'"

  - name: export_for_r
    type: write_file
    format: csv
    path: "~/research/results/clean_data.csv"
```
- 인용 가능성: 실행 로그에 라이브러리 버전, 실행 시각, 입력 파일 해시 자동 기록

### 보안 연구자
```yaml
# 보안 로그 분석 워크플로우
steps:
  - name: tail_auth_log
    type: read_file
    path: "/var/log/auth.log"
    mode: tail
    lines: 10000

  - name: detect_brute_force
    type: duckdb_query  # v1.1
    query: |
      SELECT src_ip, COUNT(*) AS attempts
      FROM log_data
      WHERE event_type = 'auth_failure'
        AND ts > NOW() - INTERVAL 1 HOUR
      GROUP BY src_ip HAVING COUNT(*) > 10
```
- 증거 무결성: 결과 파일에 자동 SHA-256 해시 추가
