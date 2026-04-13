from __future__ import annotations

import csv
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from utils.file_manager import resolve_output_path


@dataclass
class BenchmarkRecord:
    timestamp: str
    request_id: str
    stt_time_s: float = 0.0
    llm_time_s: float = 0.0
    tool_time_s: float = 0.0
    total_time_s: float = 0.0
    metadata: str = ""


@dataclass
class BenchmarkSession:
    request_id: str
    started_at: float = field(default_factory=time.perf_counter)
    stt_time_s: float = 0.0
    llm_time_s: float = 0.0
    tool_time_s: float = 0.0

    def set_stage_time(self, stage: str, elapsed_seconds: float) -> None:
        value = max(0.0, float(elapsed_seconds))
        if stage == "stt":
            self.stt_time_s = value
        elif stage == "llm":
            self.llm_time_s = value
        elif stage == "tool":
            self.tool_time_s = value
        else:
            raise ValueError("Unsupported benchmark stage. Use: stt, llm, tool")

    def to_record(self, metadata: str = "") -> BenchmarkRecord:
        total = self.stt_time_s + self.llm_time_s + self.tool_time_s
        return BenchmarkRecord(
            timestamp=datetime.utcnow().isoformat(timespec="seconds") + "Z",
            request_id=self.request_id,
            stt_time_s=round(self.stt_time_s, 6),
            llm_time_s=round(self.llm_time_s, 6),
            tool_time_s=round(self.tool_time_s, 6),
            total_time_s=round(total, 6),
            metadata=metadata,
        )


class BenchmarkLogger:
    def __init__(self, csv_relative_path: str = "generated/benchmarks.csv") -> None:
        self.csv_path = resolve_output_path(csv_relative_path)
        self.csv_path.parent.mkdir(parents=True, exist_ok=True)

    def save(self, record: BenchmarkRecord) -> str:
        file_exists = self.csv_path.exists()
        with open(self.csv_path, "a", newline="", encoding="utf-8") as fp:
            writer = csv.DictWriter(
                fp,
                fieldnames=[
                    "timestamp",
                    "request_id",
                    "stt_time_s",
                    "llm_time_s",
                    "tool_time_s",
                    "total_time_s",
                    "metadata",
                ],
            )
            if not file_exists:
                writer.writeheader()
            writer.writerow(record.__dict__)
        return str(self.csv_path)


def measure_execution(func, *args: Any, **kwargs: Any) -> tuple[Any, float]:
    start = time.perf_counter()
    result = func(*args, **kwargs)
    elapsed = time.perf_counter() - start
    return result, elapsed
