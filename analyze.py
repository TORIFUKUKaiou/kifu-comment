import sys
import os
import json

LAMBDA_DIR = os.path.join(os.path.dirname(__file__), "lambda")
if LAMBDA_DIR not in sys.path:
    sys.path.insert(0, LAMBDA_DIR)

from openai_responses import analyze_kifu

SYSTEM_PROMPT = open(os.path.join(os.path.dirname(__file__), "lambda", "prompt.txt")).read()


def main():
    if len(sys.argv) < 2:
        print("Usage: python analyze.py <file.kif>", file=sys.stderr)
        sys.exit(1)

    kif_path = sys.argv[1]

    from parse_kif import parse_kif

    parsed = parse_kif(kif_path)
    result = analyze_kifu(
        parsed,
        SYSTEM_PROMPT,
        model=os.environ.get("MODEL", "gpt-5.4-nano"),
        api_key=os.environ["OPENAI_API_KEY"],
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
