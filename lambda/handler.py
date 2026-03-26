import json
import os
import tempfile
from parse_kif import parse_kif
from openai import OpenAI

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

        structured_input = json.dumps(parsed, ensure_ascii=False)

        client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
        response = client.responses.create(
            model=os.environ.get("MODEL", "gpt-5.4-nano"),
            instructions=SYSTEM_PROMPT,
            input=structured_input,
            temperature=0.3,
        )

        raw = response.output_text.strip()
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1].rsplit("```", 1)[0].strip()

        analysis = json.loads(raw)

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
        return {
            "statusCode": 500,
            "headers": headers,
            "body": json.dumps({"error": str(e)}),
        }
