from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from utils.file_manager import resolve_output_path


def record_demo_output(
    input_audio_path: str,
    transcription: str,
    intent: str,
    action: str,
    result: str,
    metadata: dict[str, Any] | None = None,
) -> dict[str, str]:
    """Save demo run output files for video demonstration.

    Creates two files under output/generated/demo/:
    - JSON artifact (machine-readable)
    - TXT artifact (human-readable)

    Returns paths to both files.
    """
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    demo_dir = resolve_output_path("generated/demo")
    demo_dir.mkdir(parents=True, exist_ok=True)

    payload = {
        "timestamp_utc": timestamp,
        "input_audio_path": input_audio_path,
        "transcription": transcription,
        "intent": intent,
        "action": action,
        "result": result,
        "metadata": metadata or {},
    }

    json_path = Path(demo_dir) / f"demo_output_{timestamp}.json"
    txt_path = Path(demo_dir) / f"demo_output_{timestamp}.txt"

    with open(json_path, "w", encoding="utf-8") as fp:
        json.dump(payload, fp, ensure_ascii=False, indent=2)

    text_report = (
        f"Timestamp (UTC): {payload['timestamp_utc']}\n"
        f"Input Audio: {payload['input_audio_path']}\n"
        f"Transcription: {payload['transcription']}\n"
        f"Intent: {payload['intent']}\n"
        f"Action: {payload['action']}\n"
        f"Result:\n{payload['result']}\n"
    )
    with open(txt_path, "w", encoding="utf-8") as fp:
        fp.write(text_report)

    return {
        "json_path": str(json_path),
        "txt_path": str(txt_path),
    }
