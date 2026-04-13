import argparse
import csv
import time
from pathlib import Path

import librosa
from jiwer import wer
from transformers import pipeline


MODELS = ["openai/whisper-small", "openai/whisper-base"]


def load_manifest(manifest_path: str) -> list[dict]:
    rows = []
    with open(manifest_path, "r", encoding="utf-8") as fp:
        reader = csv.DictReader(fp)
        for row in reader:
            audio_path = (row.get("audio_path") or "").strip()
            reference = (row.get("reference") or "").strip()
            if audio_path and reference:
                rows.append({"audio_path": audio_path, "reference": reference})
    return rows


def transcribe(asr, audio_path: str) -> tuple[str, float]:
    audio, _ = librosa.load(audio_path, sr=16000, mono=True)
    start = time.perf_counter()
    result = asr({"sampling_rate": 16000, "raw": audio}, batch_size=8)
    elapsed = time.perf_counter() - start
    text = result.get("text", "") if isinstance(result, dict) else str(result)
    return " ".join(text.split()), elapsed


def evaluate_model(model_id: str, samples: list[dict]) -> dict:
    asr = pipeline(
        "automatic-speech-recognition",
        model=model_id,
        chunk_length_s=30,
        stride_length_s=5,
    )

    total_time = 0.0
    total_wer = 0.0

    for sample in samples:
        hyp, elapsed = transcribe(asr, sample["audio_path"])
        total_time += elapsed
        total_wer += wer(sample["reference"], hyp)

    avg_time = total_time / max(1, len(samples))
    avg_wer = total_wer / max(1, len(samples))
    accuracy = max(0.0, 1.0 - avg_wer)

    return {
        "model": model_id,
        "samples": len(samples),
        "avg_speed_seconds": round(avg_time, 4),
        "avg_wer": round(avg_wer, 4),
        "accuracy": round(accuracy, 4),
    }


def save_results(results: list[dict], output_csv: str) -> str:
    out = Path(output_csv)
    out.parent.mkdir(parents=True, exist_ok=True)

    with open(out, "w", newline="", encoding="utf-8") as fp:
        writer = csv.DictWriter(
            fp,
            fieldnames=["model", "samples", "avg_speed_seconds", "avg_wer", "accuracy"],
        )
        writer.writeheader()
        writer.writerows(results)

    return str(out)


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare whisper-small vs whisper-base on speed and accuracy.")
    parser.add_argument("--manifest", required=True, help="CSV with columns: audio_path,reference")
    parser.add_argument("--output", default="output/generated/model_comparison.csv")
    args = parser.parse_args()

    samples = load_manifest(args.manifest)
    if not samples:
        raise ValueError("Manifest has no valid rows. Expected columns: audio_path,reference")

    results = [evaluate_model(model_id, samples) for model_id in MODELS]
    output_path = save_results(results, args.output)

    print("Model comparison complete:")
    for row in results:
        print(row)
    print(f"Saved CSV: {output_path}")


if __name__ == "__main__":
    main()
