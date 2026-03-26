import json
import os
import tempfile
import traceback
from openai_responses import analyze_kifu
from parse_kif import parse_kif

SYSTEM_PROMPT = open(os.path.join(os.path.dirname(__file__), "prompt.txt")).read()


def handler(event, context):
    headers = {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Headers": "Content-Type",
        "Access-Control-Allow-Methods": "OPTIONS,POST",
    }

    if event.get("httpMethod") == "OPTIONS":
        return {"statusCode": 200, "headers": headers, "body": "{}"}

    try:
        body = event.get("body", "")
        if event.get("isBase64Encoded"):
            import base64
            body = base64.b64decode(body).decode("utf-8")

        payload = json.loads(body)
        kif_text = payload.get("kif", "")
        if not kif_text:
            return {"statusCode": 400, "headers": headers, "body": json.dumps({"error": "kif is required"})}

        # Write to temp file for parse_kif (expects file path)
        with tempfile.NamedTemporaryFile(mode="w", suffix=".kif", encoding="cp932", delete=False) as f:
            f.write(kif_text)
            tmp_path = f.name

        parsed = parse_kif(tmp_path)
        os.unlink(tmp_path)

        analysis = analyze_kifu(
            parsed,
            SYSTEM_PROMPT,
            model=os.environ.get("MODEL", "gpt-5.4-nano"),
            api_key=os.environ["OPENAI_API_KEY"],
        )

        result = {
            "parsed": parsed,
            "analysis": analysis,
        }

        return {
            "statusCode": 200,
            "headers": headers,
            "body": json.dumps(result, ensure_ascii=False),
        }

    except Exception as e:
        print(f"handler error: {e}")
        traceback.print_exc()
        return {
            "statusCode": 500,
            "headers": headers,
            "body": json.dumps({"error": str(e)}),
        }
