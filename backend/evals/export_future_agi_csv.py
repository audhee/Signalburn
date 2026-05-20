import argparse
import csv
import json
from pathlib import Path


def flatten(value):
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)
    if value is None:
        return ""
    return str(value)


def main() -> int:
    parser = argparse.ArgumentParser(description="Export eval cases to Future AGI-friendly CSV")
    parser.add_argument("--input", default=str(Path(__file__).with_name("golden_cases.json")), help="Input eval JSON")
    parser.add_argument(
        "--output",
        default=str(Path(__file__).resolve().parents[1] / "future_agi_eval_dataset.csv"),
        help="Output CSV path"
    )
    args = parser.parse_args()

    in_path = Path(args.input)
    out_path = Path(args.output)

    with in_path.open("r", encoding="utf-8-sig") as f:
        cases = json.load(f)

    columns = [
        "id",
        "type",
        "input_text",
        "input_context",
        "input_language",
        "input_media_path",
        "input_audio_path",
        "expect_status_code",
        "expect_language_code",
        "expect_detected_language",
        "expect_mode",
        "expect_question",
        "expect_media_type",
        "expect_severity",
        "expect_non_empty_fields",
        "expect_allowed_values",
    ]

    with out_path.open("w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=columns)
        writer.writeheader()

        for case in cases:
            input_data = case.get("input", {})
            expect = case.get("expect", {})
            row = {
                "id": case.get("id", ""),
                "type": case.get("type", ""),
                "input_text": input_data.get("text", ""),
                "input_context": input_data.get("context", ""),
                "input_language": input_data.get("language", ""),
                "input_media_path": input_data.get("media_path", ""),
                "input_audio_path": input_data.get("audio_path", ""),
                "expect_status_code": flatten(expect.get("status_code")),
                "expect_language_code": flatten(expect.get("language_code")),
                "expect_detected_language": flatten(expect.get("detected_language")),
                "expect_mode": flatten(expect.get("mode")),
                "expect_question": flatten(expect.get("question")),
                "expect_media_type": flatten(expect.get("media_type")),
                "expect_severity": flatten(expect.get("severity")),
                "expect_non_empty_fields": flatten(expect.get("non_empty_fields")),
                "expect_allowed_values": flatten(expect.get("allowed_values")),
            }
            writer.writerow(row)

    print(f"Exported {len(cases)} cases to {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
