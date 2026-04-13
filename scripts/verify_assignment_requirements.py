from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.dependencies import get_llm_service
from pipeline.intent.intent_classifier import IntentClassifier
from pipeline.routing.router import Router
from services.tool_service import ToolService


def _run_request(text: str) -> dict:
    intents = IntentClassifier().classify(text)
    result = Router(ToolService(get_llm_service())).route(intents, text)
    return {
        "text": text,
        "intents": intents,
        "action": result.get("action", ""),
        "result": result.get("result", ""),
    }


def _exists(path: str) -> bool:
    return Path(path).exists()


def main() -> None:
    checks = []

    create_case = _run_request("Create a file named hello.txt")
    checks.append((
        "File Creation",
        "create_file" in create_case["action"],
        _exists("output/generated/hello.txt"),
        create_case,
    ))

    code_case = _run_request("Write Python code to add two numbers into add.py")
    checks.append((
        "Code Writing",
        "write_code" in code_case["action"],
        _exists("output/generated/add.py"),
        code_case,
    ))

    summarize_case = _run_request(
        "Summarize this text: Python is a high-level language used for automation, data science, and web development."
    )
    checks.append((
        "Summarization",
        "summarize" in summarize_case["action"],
        "Summary generated" in summarize_case["result"],
        summarize_case,
    ))

    lines = ["# Assignment Requirement Verification", ""]
    lines.append("| Test | Action Match | Evidence Check | Status |")
    lines.append("|---|---|---|---|")

    for name, action_ok, evidence_ok, case in checks:
        status = "PASS" if (action_ok and evidence_ok) else "FAIL"
        lines.append(
            f"| {name} | {'yes' if action_ok else 'no'} | {'yes' if evidence_ok else 'no'} | {status} |"
        )
        lines.append("")
        lines.append(f"## {name} Details")
        lines.append(f"Request: {case['text']}")
        lines.append(f"Action: {case['action']}")
        lines.append("Result:")
        lines.append("```")
        lines.append(case["result"])
        lines.append("```")
        lines.append("")

    lines.append("## Audio Input Proof")
    lines.append(
        "Run the UI and capture one microphone input + one uploaded audio file interaction screenshot/video to complete this requirement."
    )

    out = Path("output/generated/requirement_verification.md")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"Verification report written to: {out.as_posix()}")


if __name__ == "__main__":
    main()
