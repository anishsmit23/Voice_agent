import argparse
import json

from app.dependencies import get_llm_service
from pipeline.intent.intent_classifier import IntentClassifier
from pipeline.routing.router import Router
from pipeline.stt.wishper import transcribe_audio
from services.tool_service import ToolService


def run_agent(audio_path: str) -> dict:
    transcript, stt_duration = transcribe_audio(audio_path)

    if not transcript:
        return {
            "transcription": "",
            "intent": "",
            "action": "error",
            "result": "Audio error",
            "stt_duration_s": round(stt_duration, 4),
        }

    try:
        classifier = IntentClassifier()
        intent_payload = classifier.classify(transcript)
        intent_list = [item.get("intent", "chat") for item in intent_payload] if isinstance(intent_payload, list) else ["chat"]
    except Exception:
        return {
            "transcription": transcript,
            "intent": "",
            "action": "error",
            "result": "Intent error",
            "stt_duration_s": round(stt_duration, 4),
        }

    try:
        tool_service = ToolService(get_llm_service())
        router = Router(tool_service)
        action_payload = router.route(intent_payload, transcript)
    except Exception:
        return {
            "transcription": transcript,
            "intent": ", ".join(intent_list),
            "action": "error",
            "result": "Tool error",
            "stt_duration_s": round(stt_duration, 4),
        }

    return {
        "transcription": transcript,
        "intent": ", ".join(intent_list),
        "action": action_payload.get("action", "chat"),
        "result": action_payload.get("result", ""),
        "stt_duration_s": round(stt_duration, 4),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Voice Agent from CLI using an audio file path.")
    parser.add_argument("audio_path", help="Path to input audio file (.wav or .mp3)")
    parser.add_argument("--json", action="store_true", help="Print output as formatted JSON")
    args = parser.parse_args()

    output = run_agent(args.audio_path)

    if args.json:
        print(json.dumps(output, indent=2, ensure_ascii=False))
        return

    print("Transcription:", output.get("transcription", ""))
    print("Intent:", output.get("intent", ""))
    print("Action:", output.get("action", ""))
    print("Result:", output.get("result", ""))
    print("STT Duration (s):", output.get("stt_duration_s", 0.0))


if __name__ == "__main__":
    main()
