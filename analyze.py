import sys
import os
import json
from openai import OpenAI

SYSTEM_PROMPT = open(os.path.join(os.path.dirname(__file__), "lambda", "prompt.txt")).read()


def main():
    if len(sys.argv) < 2:
        print("Usage: python analyze.py <file.kif>", file=sys.stderr)
        sys.exit(1)

    kif_path = sys.argv[1]

    from parse_kif import parse_kif

    parsed = parse_kif(kif_path)
    structured_input = json.dumps(parsed, ensure_ascii=False)

    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

    response = client.responses.create(
        model="gpt-5.4-nano",
        instructions=SYSTEM_PROMPT,
        input=structured_input,
        temperature=0.3,
    )

    raw = response.output_text.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1].rsplit("```", 1)[0].strip()

    result = json.loads(raw)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
