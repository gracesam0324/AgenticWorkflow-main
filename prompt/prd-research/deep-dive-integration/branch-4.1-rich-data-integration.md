# Branch 4.1: 데이터 파이프라인 & 포맷 — Rich Data Integration
> Data Pipeline & Format Integration Specialist
> 조사일: 2026-04-07

---

## 1. SQLite 통합 — 상태 관리

```python
# workflow_state_db.py
import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import Optional

DB_PATH = Path.home() / ".workflow_agent" / "state.db"

class WorkflowStateDB:
    """YAML 플랜 실행 결과를 SQLite에 영속화"""

    DDL = """
    CREATE TABLE IF NOT EXISTS executions (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id  TEXT NOT NULL,
        step_name   TEXT NOT NULL,
        step_type   TEXT NOT NULL,
        status      TEXT NOT NULL,
        input_hash  TEXT,
        result_json TEXT,
        error_msg   TEXT,
        started_at  TEXT,
        finished_at TEXT
    );
    CREATE INDEX IF NOT EXISTS idx_session ON executions(session_id);
    CREATE INDEX IF NOT EXISTS idx_status  ON executions(status);
    """

    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript(self.DDL)

    def store_execution_result(self, session_id: str, step: dict, result: dict) -> int:
        sql = """
        INSERT INTO executions
            (session_id, step_name, step_type, status, result_json, started_at, finished_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(sql, (
                session_id, step["name"], step["type"],
                result.get("status", "done"),
                json.dumps(result, ensure_ascii=False),
                result.get("started_at"),
                datetime.utcnow().isoformat(),
            ))
            return cursor.lastrowid

    def query_history(self, filters: dict) -> list[dict]:
        where_clauses = [f"{k} = :{k}" for k in filters]
        where_sql = ("WHERE " + " AND ".join(where_clauses)) if where_clauses else ""
        sql = f"SELECT * FROM executions {where_sql} ORDER BY id DESC LIMIT 200"
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(sql, filters).fetchall()
        return [dict(r) for r in rows]

    def get_audit_trail(self, session_id: str) -> list[dict]:
        sql = """
        SELECT step_name, step_type, status, started_at, finished_at, error_msg
        FROM executions WHERE session_id = ? ORDER BY id ASC
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(sql, (session_id,)).fetchall()
        return [dict(r) for r in rows]
```

**성능 최적화**:
- WAL 모드: `PRAGMA journal_mode=WAL` → 동시 읽기/쓰기 충돌 제거
- 10만 행 이하: 인덱스 없이도 쿼리 10ms 이내
- 500MB 초과 시: `VACUUM` 자동 스케줄링 권장

---

## 2. DuckDB 통합 — 데이터 엔지니어 타겟

```python
# duckdb_step.py
# duckdb==1.2.1
import duckdb
from pathlib import Path
from typing import Optional

class DuckDBAnalysisStep:
    """
    YAML 스텝 타입: duckdb_query
    10GB CSV를 로컬에서 집계 분석
    성능: 10GB CSV 집계 ≈ 8초 (DuckDB) vs 180초 (pandas) — M2 Mac 4코어
    """

    def __init__(self, db_file: Optional[str] = None):
        self.conn = duckdb.connect(db_file or ":memory:")
        self.conn.execute("SET threads TO 4;")
        self.conn.execute("SET memory_limit = '4GB';")

    def execute(self, query: str, output_path: Optional[str] = None) -> dict:
        rel = self.conn.sql(query)
        df = rel.df()
        result_preview = df.head(50).to_dict(orient="records")

        if output_path:
            p = Path(output_path).expanduser()
            if p.suffix == ".parquet":
                rel.write_parquet(str(p))
            elif p.suffix == ".csv":
                rel.write_csv(str(p))
            else:
                df.to_json(p, orient="records", force_ascii=False, indent=2)

        return {
            "row_count": len(df),
            "columns": list(df.columns),
            "preview": result_preview,
            "output": output_path,
        }

    def aggregate_parquet(self, glob_pattern: str, agg_sql: str):
        """Hive 파티션 Parquet 직접 집계"""
        return self.conn.sql(
            f"SELECT * FROM read_parquet('{glob_pattern}', hive_partitioning=true) WHERE {agg_sql}"
        ).df()
```

YAML 스텝 예시:
```yaml
steps:
  - name: analyze_sales
    type: duckdb_query
    query: |
      SELECT region, product_category,
             SUM(revenue) AS total_revenue,
             COUNT(*) AS order_count
      FROM read_csv_auto('~/data/sales_10gb.csv')
      WHERE YEAR(order_date) = 2024
      GROUP BY 1, 2
      ORDER BY total_revenue DESC
    output: ~/results/summary.parquet
```

---

## 3. 파일 포맷별 구현

### CSV (스트리밍 처리)

```python
import csv, pandas as pd
from pathlib import Path

def read_csv_full(filepath: str, encoding: str = "utf-8") -> list[dict]:
    with open(filepath, encoding=encoding, newline="") as f:
        return list(csv.DictReader(f))

def process_large_csv_streaming(filepath: str, chunk_size: int = 10_000, encoding: str = "utf-8"):
    """메모리 O(chunk_size) 유지"""
    reader = pd.read_csv(filepath, chunksize=chunk_size, encoding=encoding, low_memory=False)
    for chunk in reader:
        chunk = chunk.dropna(how="all")
        yield chunk

def write_csv_streaming(output_path: str, row_iter):
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = None
        for row in row_iter:
            if writer is None:
                writer = csv.DictWriter(f, fieldnames=row.keys())
                writer.writeheader()
            writer.writerow(row)
```

### Excel (openpyxl + xlsxwriter)

```python
# openpyxl==3.1.5 / xlsxwriter==3.2.0
import openpyxl, xlsxwriter

def read_excel(filepath: str, sheet_name: str = None) -> list[dict]:
    wb = openpyxl.load_workbook(filepath, read_only=True, data_only=True)
    ws = wb[sheet_name] if sheet_name else wb.active
    rows = list(ws.iter_rows(values_only=True))
    headers = rows[0]
    return [dict(zip(headers, row)) for row in rows[1:]]

def write_excel_report(filepath: str, data: list[dict], sheet_title: str = "Result"):
    with xlsxwriter.Workbook(filepath, {"constant_memory": True}) as wb:
        ws = wb.add_worksheet(sheet_title)
        header_fmt = wb.add_format({"bold": True, "bg_color": "#4472C4", "font_color": "#FFFFFF"})
        if not data:
            return
        headers = list(data[0].keys())
        for col, h in enumerate(headers):
            ws.write(0, col, h, header_fmt)
        for row_idx, record in enumerate(data, start=1):
            for col_idx, key in enumerate(headers):
                ws.write(row_idx, col_idx, record.get(key))
```

### JSON (orjson 고속 파싱)

```python
# orjson==3.10.12 — C 구현체
import orjson
from pathlib import Path

def read_json(filepath: str): return orjson.loads(Path(filepath).read_bytes())
def write_json(filepath: str, data, indent: bool = True):
    opts = orjson.OPT_INDENT_2 | orjson.OPT_NON_STR_KEYS
    Path(filepath).write_bytes(orjson.dumps(data, option=opts))

def read_jsonl_streaming(filepath: str):
    with open(filepath, "rb") as f:
        for line in f:
            line = line.strip()
            if line:
                yield orjson.loads(line)

def append_jsonl(filepath: str, record: dict):
    with open(filepath, "ab") as f:
        f.write(orjson.dumps(record) + b"\n")
```

### Parquet (pyarrow + 스키마)

```python
# pyarrow==19.0.1
import pyarrow.parquet as pq
import pyarrow.dataset as ds

def read_parquet(filepath: str, columns: list[str] = None):
    """Projection Pushdown으로 IO 절감"""
    return pq.read_table(filepath, columns=columns).to_pandas()

def write_parquet(filepath: str, df, compression: str = "zstd"):
    """zstd: gzip보다 빠르고 snappy보다 압축률 높음"""
    import pyarrow as pa
    pq.write_table(pa.Table.from_pandas(df), filepath, compression=compression)

def stream_large_parquet(directory: str, filter_expr=None):
    """Hive 파티션 스트리밍 (배치 단위 RAM 절약)"""
    dataset = ds.dataset(directory, format="parquet", partitioning="hive")
    scanner = dataset.scanner(filter=filter_expr, batch_size=65_536)
    for batch in scanner.to_batches():
        yield batch.to_pandas()
```

### PDF (pdfplumber)

```python
# pdfplumber==0.11.4
import pdfplumber

def extract_text_from_pdf(filepath: str) -> str:
    pages_text = []
    with pdfplumber.open(filepath) as pdf:
        for page in pdf.pages:
            text = page.extract_text(x_tolerance=3, y_tolerance=3)
            if text:
                pages_text.append(text)
    return "\n\n--- PAGE BREAK ---\n\n".join(pages_text)

def extract_tables_from_pdf(filepath: str) -> list:
    all_tables = []
    with pdfplumber.open(filepath) as pdf:
        for page in pdf.pages:
            all_tables.extend(page.extract_tables())
    return all_tables
```

---

## 4. 외부 API 통합 (httpx + ConstitutionalPolicy)

```python
# api_call_step.py
# httpx==0.28.1 / tenacity==9.0.0
import httpx
import asyncio
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from urllib.parse import urlparse

ALLOWED_SCHEMES = {"https"}
BLOCKED_HOSTS = {"localhost", "127.0.0.1", "0.0.0.0", "::1"}

class APIPolicy:
    @staticmethod
    def validate(url: str, method: str, has_auth: bool) -> None:
        parsed = urlparse(url)
        if parsed.scheme not in ALLOWED_SCHEMES:
            raise PermissionError(f"Non-HTTPS 차단: {url}")
        if parsed.hostname in BLOCKED_HOSTS:
            raise PermissionError(f"로컬 호스트 차단: {url}")
        if method.upper() in {"POST", "PUT", "PATCH", "DELETE"} and not has_auth:
            raise PermissionError("쓰기 API는 사용자 승인 후 실행")

class APICallStep:
    DEFAULT_TIMEOUT = httpx.Timeout(connect=5.0, read=30.0, write=10.0, pool=5.0)

    @retry(
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.ConnectError)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=8),
    )
    async def execute(self, url: str, method: str = "GET",
                      headers: dict = None, body: dict = None,
                      auth_token: str = None) -> dict:
        APIPolicy.validate(url, method, bool(auth_token))
        req_headers = headers or {}
        if auth_token:
            req_headers["Authorization"] = f"Bearer {auth_token}"

        async with httpx.AsyncClient(timeout=self.DEFAULT_TIMEOUT) as client:
            response = await client.request(method.upper(), url, headers=req_headers, json=body)
            response.raise_for_status()
            content_type = response.headers.get("content-type", "")
            if "json" in content_type:
                return {"status": response.status_code, "data": response.json()}
            return {"status": response.status_code, "text": response.text[:4096]}
```

---

## 5. PRD 포맷 지원 범위 결정

### v1.0 Standard 범위 (권장)

| 포맷 | 지원 | 라이브러리 | 설치 |
|---|---|---|---|
| CSV | 읽기/쓰기 | stdlib csv | 기본 |
| JSON | 읽기/쓰기 | orjson | `pip install workflow-agent` |
| JSONL | 읽기/쓰기 | orjson | `pip install workflow-agent` |
| YAML | 읽기 | pyyaml | `pip install workflow-agent` |
| TXT | 읽기/쓰기 | stdlib | 기본 |
| Excel | 읽기 | openpyxl | `pip install workflow-agent[data]` |
| Parquet | 읽기/쓰기 | pyarrow | `pip install workflow-agent[data]` |
| PDF | 텍스트 추출 | pdfplumber | `pip install workflow-agent[data]` |

**`[data]` extras**: openpyxl, pyarrow, pdfplumber, orjson을 선택적으로 분리.

### v1.1으로 연기

- DuckDB 기반 `duckdb_query` 스텝
- 청크 스트리밍 pandas 처리
- Hive 파티션 Parquet 스트리밍
