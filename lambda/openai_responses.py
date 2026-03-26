import json
import os
import urllib.error
import urllib.request

API_URL = os.environ.get("OPENAI_API_URL", "https://api.openai.com/v1/responses")


def analyze_kifu(parsed: dict, system_prompt: str, *, model: str, api_key: str) -> dict:
    input_json = json.dumps(parsed, ensure_ascii=False)
    payload = {
        "model": model,
        "instructions": system_prompt,
        "input": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": (
                            "Analyze the following shogi game data and return JSON only.\n"
                            "Input JSON:\n"
                            f"{input_json}"
                        ),
                    }
                ],
            }
        ],
        "temperature": 0.3,
        "max_output_tokens": 1200,
        "text": {
            "format": {
                "type": "json_object",
            }
        },
    }

    request = urllib.request.Request(
        API_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=55) as response:
            body = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(_extract_error_message(detail, exc.code)) from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"OpenAI API request failed: {exc.reason}") from exc

    response_json = json.loads(body)
    error = response_json.get("error")
    if error:
        raise RuntimeError(f"OpenAI API error: {error.get('message', 'unknown error')}")

    status = response_json.get("status")
    if status not in (None, "completed"):
        detail = response_json.get("incomplete_details") or {}
        reason = detail.get("reason") or "unknown"
        raise RuntimeError(f"OpenAI response did not complete: {status} ({reason})")

    raw_output = _extract_output_text(response_json)
    return _normalize_analysis(json.loads(raw_output))


def _extract_error_message(detail: str, status_code: int) -> str:
    try:
        payload = json.loads(detail)
    except json.JSONDecodeError:
        return f"OpenAI API error {status_code}: {detail}"

    error = payload.get("error") or {}
    message = error.get("message")
    if message:
        return f"OpenAI API error {status_code}: {message}"
    return f"OpenAI API error {status_code}"


def _extract_output_text(response_json: dict) -> str:
    output_text = response_json.get("output_text")
    if isinstance(output_text, str) and output_text.strip():
        return output_text.strip()

    parts = []
    for item in response_json.get("output", []):
        if item.get("type") != "message":
            continue
        for content in item.get("content", []):
            if content.get("type") != "output_text":
                continue
            text = content.get("text")
            if isinstance(text, str) and text:
                parts.append(text)

    if parts:
        return "".join(parts).strip()

    raise RuntimeError("OpenAI response did not include text output")


def _normalize_analysis(analysis: dict) -> dict:
    swing_points = []
    for item in analysis.get("swing_points", []):
        if not isinstance(item, dict):
            continue
        move = _normalize_int(item.get("move"))
        if move is None:
            continue
        swing_points.append({
            "move": move,
            "player": _normalize_player(item.get("player")),
            "move_text": _normalize_string(item.get("move_text")),
            "eval_after": _normalize_eval(item.get("eval_after")),
            "tag": _normalize_string(item.get("tag")),
            "short_comment": _normalize_string(item.get("short_comment")),
        })
        if len(swing_points) >= 5:
            break

    summary = analysis.get("summary")
    if not isinstance(summary, dict):
        summary = {}

    return {
        "swing_points": swing_points,
        "summary": {
            "opening_to_middle": _normalize_string(summary.get("opening_to_middle")),
            "middle_to_endgame": _normalize_string(summary.get("middle_to_endgame")),
            "final_phase": _normalize_string(summary.get("final_phase")),
        },
    }


def _normalize_eval(value):
    if not isinstance(value, dict):
        return None

    eval_type = value.get("type")
    eval_value = value.get("value")
    if eval_type == "cp":
        normalized = _normalize_int(eval_value)
        if normalized is None:
            return None
        return {"type": "cp", "value": normalized}
    if eval_type == "mate":
        normalized = _normalize_int(eval_value)
        if normalized is None:
            return None
        return {"type": "mate", "value": normalized}
    if eval_type == "raw":
        return {"type": "raw", "value": _normalize_string(eval_value)}
    return None


def _normalize_player(value):
    if value in ("sente", "gote"):
        return value
    return ""


def _normalize_string(value):
    if value is None:
        return ""
    return str(value)


def _normalize_int(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return None
