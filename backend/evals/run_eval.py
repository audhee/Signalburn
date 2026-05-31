import argparse
import json
import mimetypes
import statistics
import sys
import time
from pathlib import Path

import requests
from requests.exceptions import ConnectionError as RequestsConnectionError


ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = ROOT.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.services.ai.language_service import detect_language  # noqa: E402


ENDPOINT_CASE_TYPES = {
    "guided_query",
    "text_query",
    "multimodal_text_query",
    "transcribe_only",
    "process_voice",
    "supported_media_types",
    "chat_history_get",
    "chat_history_delete",
}


def load_cases(dataset_path: Path) -> list[dict]:
    with dataset_path.open("r", encoding="utf-8-sig") as f:
        return json.load(f)


def resolve_path(path_value: str) -> Path:
    candidate = Path(path_value)
    if candidate.is_absolute():
        return candidate
    return (PROJECT_ROOT / candidate).resolve()


def compare_fields(actual: dict, expected: dict, allowed_keys: list[str]) -> list[str]:
    failures = []
    for key in allowed_keys:
        if key not in expected:
            continue
        if actual.get(key) != expected[key]:
            failures.append(f"{key}: expected={expected[key]!r}, actual={actual.get(key)!r}")
    return failures


def validate_expectations(actual: dict, expected: dict) -> list[str]:
    failures = compare_fields(
        actual,
        expected,
        [
            "success",
            "mode",
            "question",
            "detected_language",
            "response",
            "language",
            "language_code",
            "severity",
            "media_type",
            "transcription",
            "status",
            "session_id",
            "input_type",
        ],
    )

    for key in expected.get("non_empty_fields", []):
        value = actual.get(key)
        if not isinstance(value, str) or not value.strip():
            failures.append(f"{key}: expected non-empty string, actual={value!r}")

    for key, allowed_values in expected.get("allowed_values", {}).items():
        if actual.get(key) not in allowed_values:
            failures.append(f"{key}: expected one of {allowed_values!r}, actual={actual.get(key)!r}")

    for key, needle in expected.get("contains", {}).items():
        value = actual.get(key, "")
        if needle.lower() not in str(value).lower():
            failures.append(f"{key}: expected to contain {needle!r}, actual={value!r}")

    for key, forbidden in expected.get("must_not_contain", {}).items():
        value = str(actual.get(key, "")).lower()
        if str(forbidden).lower() in value:
            failures.append(f"{key}: should not contain {forbidden!r}, actual={actual.get(key)!r}")

    for key, options in expected.get("must_contain_any", {}).items():
        value = str(actual.get(key, "")).lower()
        if not any(str(option).lower() in value for option in options):
            failures.append(f"{key}: expected to contain one of {options!r}, actual={actual.get(key)!r}")

    for key, required_items in expected.get("list_contains", {}).items():
        value = actual.get(key)
        if not isinstance(value, list):
            failures.append(f"{key}: expected list, actual={type(value).__name__}")
            continue
        for item in required_items:
            if item not in value:
                failures.append(f"{key}: expected to include {item!r}, actual={value!r}")

    for key, min_value in expected.get("min_value", {}).items():
        value = actual.get(key)
        if not isinstance(value, (int, float)) or value < min_value:
            failures.append(f"{key}: expected >= {min_value}, actual={value!r}")

    return failures


def run_json_post(case: dict, base_url: str, endpoint: str, timeout: int = 45) -> tuple[bool, str]:
    try:
        response = requests.post(f"{base_url}{endpoint}", json=case["input"], timeout=timeout)
    except RequestsConnectionError:
        return False, f"could not connect to backend at {base_url}. Start FastAPI before running endpoint evals."

    expected = case["expect"]
    if response.status_code != expected.get("status_code", 200):
        return False, f"status_code: expected={expected.get('status_code')}, actual={response.status_code}"

    data = response.json()
    failures = validate_expectations(data, expected)
    if failures:
        return False, "; ".join(failures)
    return True, "passed"


def run_language_service(case: dict) -> tuple[bool, str]:
    result = detect_language(case["input"]["text"])
    expected = case["expect"]
    failures = compare_fields(result, expected, ["language_code", "is_emergency"])
    if failures:
        return False, "; ".join(failures)
    return True, "passed"


def run_multimodal_text_query(case: dict, base_url: str) -> tuple[bool, str]:
    media_path = resolve_path(case["input"]["media_path"])
    if not media_path.exists():
        return False, f"media file not found: {media_path}"

    mime_type = mimetypes.guess_type(media_path.name)[0] or "application/octet-stream"
    data = {
        "text": case["input"].get("text", ""),
        "session_id": case["input"].get("session_id", ""),
    }

    try:
        with media_path.open("rb") as media_file:
            response = requests.post(
                f"{base_url}/api/v1/ai/multimodal-text-query",
                data=data,
                files={"media": (media_path.name, media_file, mime_type)},
                timeout=90,
            )
    except RequestsConnectionError:
        return False, f"could not connect to backend at {base_url}. Start FastAPI before running endpoint evals."

    expected = case["expect"]
    if response.status_code != expected.get("status_code", 200):
        return False, f"status_code: expected={expected.get('status_code')}, actual={response.status_code}"

    response_data = response.json()
    failures = validate_expectations(response_data, expected)
    if failures:
        return False, "; ".join(failures)
    return True, "passed"


def run_multipart_audio(case: dict, base_url: str, endpoint: str, timeout: int = 90) -> tuple[bool, str]:
    audio_path = resolve_path(case["input"]["audio_path"])
    if not audio_path.exists():
        return False, f"audio file not found: {audio_path}"

    mime_type = mimetypes.guess_type(audio_path.name)[0] or "audio/mpeg"
    data = {
        "session_id": case["input"].get("session_id", "eval-audio"),
        "language_code": case["input"].get("language_code", ""),
    }

    try:
        with audio_path.open("rb") as audio_file:
            response = requests.post(
                f"{base_url}{endpoint}",
                data=data,
                files={"audio": (audio_path.name, audio_file, mime_type)},
                timeout=timeout,
            )
    except RequestsConnectionError:
        return False, f"could not connect to backend at {base_url}. Start FastAPI before running endpoint evals."

    expected = case["expect"]
    if response.status_code != expected.get("status_code", 200):
        return False, f"status_code: expected={expected.get('status_code')}, actual={response.status_code}"

    response_data = response.json()
    failures = validate_expectations(response_data, expected)
    if failures:
        return False, "; ".join(failures)
    return True, "passed"


def run_supported_media_types(case: dict, base_url: str) -> tuple[bool, str]:
    try:
        response = requests.get(f"{base_url}/api/v1/ai/supported-media-types", timeout=30)
    except RequestsConnectionError:
        return False, f"could not connect to backend at {base_url}. Start FastAPI before running endpoint evals."

    expected = case["expect"]
    if response.status_code != expected.get("status_code", 200):
        return False, f"status_code: expected={expected.get('status_code')}, actual={response.status_code}"

    data = response.json()
    failures = []
    for key in expected.get("required_keys", []):
        if key not in data:
            failures.append(f"missing key: {key}")

    for key, min_len in expected.get("min_list_lengths", {}).items():
        value = data.get(key)
        if not isinstance(value, list) or len(value) < min_len:
            failures.append(f"{key}: expected list length >= {min_len}, actual={value!r}")

    for key, required_items in expected.get("list_contains", {}).items():
        value = data.get(key)
        if not isinstance(value, list):
            failures.append(f"{key}: expected list, actual={type(value).__name__}")
            continue
        for item in required_items:
            if item not in value:
                failures.append(f"{key}: expected to include {item!r}, actual={value!r}")

    if failures:
        return False, "; ".join(failures)
    return True, "passed"


def run_chat_history_get(case: dict, base_url: str) -> tuple[bool, str]:
    session_id = case["input"]["session_id"]
    try:
        response = requests.get(f"{base_url}/api/v1/ai/chat-history/{session_id}", timeout=30)
    except RequestsConnectionError:
        return False, f"could not connect to backend at {base_url}. Start FastAPI before running endpoint evals."

    expected = case["expect"]
    if response.status_code != expected.get("status_code", 200):
        return False, f"status_code: expected={expected.get('status_code')}, actual={response.status_code}"

    data = response.json()
    failures = []
    if data.get("session_id") != session_id:
        failures.append(f"session_id mismatch: expected={session_id!r}, actual={data.get('session_id')!r}")

    messages = data.get("messages")
    if not isinstance(messages, list):
        failures.append(f"messages should be list, actual={type(messages).__name__}")
    else:
        min_messages = expected.get("min_messages")
        if min_messages is not None and len(messages) < min_messages:
            failures.append(f"messages count: expected >= {min_messages}, actual={len(messages)}")

    if failures:
        return False, "; ".join(failures)
    return True, "passed"


def run_chat_history_delete(case: dict, base_url: str) -> tuple[bool, str]:
    session_id = case["input"]["session_id"]
    try:
        response = requests.delete(f"{base_url}/api/v1/ai/chat-history/{session_id}", timeout=30)
    except RequestsConnectionError:
        return False, f"could not connect to backend at {base_url}. Start FastAPI before running endpoint evals."

    expected = case["expect"]
    if response.status_code != expected.get("status_code", 200):
        return False, f"status_code: expected={expected.get('status_code')}, actual={response.status_code}"

    data = response.json()
    failures = validate_expectations(data, expected)
    if failures:
        return False, "; ".join(failures)
    return True, "passed"


def run_case(case: dict, base_url: str) -> tuple[bool, str]:
    case_type = case["type"]

    if case_type == "guided_query":
        return run_json_post(case, base_url, "/api/v1/ai/guided-query", timeout=45)
    if case_type == "text_query":
        return run_json_post(case, base_url, "/api/v1/ai/text-query", timeout=60)
    if case_type == "language_service":
        return run_language_service(case)
    if case_type == "multimodal_text_query":
        return run_multimodal_text_query(case, base_url)
    if case_type == "transcribe_only":
        return run_multipart_audio(case, base_url, "/api/v1/ai/transcribe-only", timeout=90)
    if case_type == "process_voice":
        return run_multipart_audio(case, base_url, "/api/v1/ai/process-voice", timeout=120)
    if case_type == "supported_media_types":
        return run_supported_media_types(case, base_url)
    if case_type == "chat_history_get":
        return run_chat_history_get(case, base_url)
    if case_type == "chat_history_delete":
        return run_chat_history_delete(case, base_url)

    return False, f"unsupported case type: {case_type}"


def compare_with_baseline(current_report: dict, baseline_path: Path) -> dict:
    if not baseline_path.exists():
        return {"baseline_found": False}

    with baseline_path.open("r", encoding="utf-8-sig") as f:
        baseline = json.load(f)

    current_failed = {c["id"] for c in current_report["cases"] if not c["passed"]}
    baseline_failed = {c["id"] for c in baseline.get("cases", []) if not c.get("passed", False)}

    return {
        "baseline_found": True,
        "previous_score": baseline.get("summary", {}).get("score_percent"),
        "current_score": current_report["summary"].get("score_percent"),
        "new_failures": sorted(list(current_failed - baseline_failed)),
        "fixed_failures": sorted(list(baseline_failed - current_failed)),
    }


def build_report(case_results: list[dict], suite: str, dataset_path: Path, base_url: str) -> dict:
    total_weight = sum(item["weight"] for item in case_results) or 1.0
    passed_weight = sum(item["weight"] for item in case_results if item["passed"])

    endpoint_latencies = [item["latency_ms"] for item in case_results if item["is_endpoint_case"]]

    by_type = {}
    for item in case_results:
        bucket = by_type.setdefault(item["type"], {"count": 0, "passed": 0, "failed": 0, "latencies": []})
        bucket["count"] += 1
        if item["passed"]:
            bucket["passed"] += 1
        else:
            bucket["failed"] += 1
        if item["latency_ms"] is not None:
            bucket["latencies"].append(item["latency_ms"])

    for _, bucket in by_type.items():
        lat = bucket.pop("latencies")
        bucket["avg_latency_ms"] = round(statistics.mean(lat), 2) if lat else None
        bucket["pass_rate_percent"] = round((bucket["passed"] / bucket["count"]) * 100, 2) if bucket["count"] else 0.0

    report = {
        "meta": {
            "suite": suite,
            "dataset": str(dataset_path),
            "base_url": base_url,
            "generated_at_epoch": int(time.time()),
        },
        "summary": {
            "total_cases": len(case_results),
            "passed": sum(1 for c in case_results if c["passed"]),
            "failed": sum(1 for c in case_results if not c["passed"]),
            "score_percent": round((passed_weight / total_weight) * 100, 2),
            "weighted_passed": round(passed_weight, 2),
            "weighted_total": round(total_weight, 2),
            "endpoint_avg_latency_ms": round(statistics.mean(endpoint_latencies), 2) if endpoint_latencies else None,
            "endpoint_p95_latency_ms": round(sorted(endpoint_latencies)[int(0.95 * (len(endpoint_latencies) - 1))], 2) if endpoint_latencies else None,
        },
        "reliability": {
            "by_type": by_type,
        },
        "cases": case_results,
    }
    return report


def select_cases(cases: list[dict], suite: str, only: str) -> list[dict]:
    filtered = cases
    if only:
        filtered = [c for c in filtered if c["type"] == only]

    if suite == "all":
        return filtered

    allowed = {"smoke": {"smoke"}, "core": {"smoke", "core"}, "full": {"smoke", "core", "full"}}[suite]
    result = []
    for case in filtered:
        case_suite = case.get("suite", "core")
        if case_suite in allowed:
            result.append(case)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Arohan AI eval cases.")
    parser.add_argument("--base-url", default="http://localhost:8000", help="Base URL of the running FastAPI backend")
    parser.add_argument("--dataset", default=str(Path(__file__).with_name("golden_cases.json")), help="Path to eval dataset JSON file")
    parser.add_argument("--only", default="", help="Run only one case type")
    parser.add_argument("--suite", default="core", choices=["smoke", "core", "full", "all"], help="Eval suite tier")
    parser.add_argument("--report-out", default=str(Path(__file__).resolve().parents[1] / "last_eval_report.json"), help="Path to save run report JSON")
    parser.add_argument("--baseline-report", default="", help="Previous report path for regression comparison")
    parser.add_argument("--fail-threshold", type=float, default=0.0, help="Fail if score_percent goes below this value")
    args = parser.parse_args()

    dataset_path = Path(args.dataset)
    cases = load_cases(dataset_path)
    cases = select_cases(cases, args.suite, args.only)

    print("Arohan Eval Runner")
    print(f"Dataset: {dataset_path}")
    print(f"Base URL: {args.base_url}")
    print(f"Suite: {args.suite}")
    print("")

    if any(case["type"] in ENDPOINT_CASE_TYPES for case in cases):
        try:
            requests.get(args.base_url, timeout=5)
        except RequestsConnectionError:
            print("Backend check")
            print(f"  Could not reach {args.base_url}")
            print("  Start FastAPI backend for endpoint evals.")
            print("")

    case_results = []
    for case in cases:
        start = time.perf_counter()
        ok, detail = run_case(case, args.base_url)
        latency_ms = round((time.perf_counter() - start) * 1000, 2)

        status = "PASS" if ok else "FAIL"
        print(f"[{status}] {case['id']} ({case['type']})")
        print(f"  {detail}")

        case_results.append(
            {
                "id": case["id"],
                "type": case["type"],
                "suite": case.get("suite", "core"),
                "critical": bool(case.get("critical", False)),
                "weight": float(case.get("weight", 1.0)),
                "passed": ok,
                "detail": detail,
                "latency_ms": latency_ms,
                "is_endpoint_case": case["type"] in ENDPOINT_CASE_TYPES,
            }
        )

    report = build_report(case_results, args.suite, dataset_path, args.base_url)

    baseline_diff = None
    if args.baseline_report:
        baseline_diff = compare_with_baseline(report, Path(args.baseline_report))

    report["baseline"] = baseline_diff

    report_path = Path(args.report_out)
    with report_path.open("w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    summary = report["summary"]
    print("")
    print("Summary")
    print(f"  Passed: {summary['passed']}")
    print(f"  Failed: {summary['failed']}")
    print(f"  Total:  {summary['total_cases']}")
    print(f"  Score:  {summary['score_percent']}%")
    print(f"  Avg endpoint latency: {summary['endpoint_avg_latency_ms']} ms")
    print(f"  Report: {report_path}")

    if baseline_diff and baseline_diff.get("baseline_found"):
        print("")
        print("Baseline comparison")
        print(f"  Previous score: {baseline_diff.get('previous_score')}")
        print(f"  Current score:  {baseline_diff.get('current_score')}")
        print(f"  New failures:   {baseline_diff.get('new_failures')}")
        print(f"  Fixed failures: {baseline_diff.get('fixed_failures')}")

    if summary["score_percent"] < args.fail_threshold:
        return 1

    if any(item["critical"] and not item["passed"] for item in case_results):
        return 1

    return 0 if summary["failed"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())

