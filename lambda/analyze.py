import sys
import os
import json
from openai import OpenAI

SYSTEM_PROMPT = """あなたは将棋の棋譜解析アシスタントです。
入力として、構造化された棋譜データ（JSON）が与えられます。
各手には評価値（cp=数値評価, mate=詰み）、候補手、読み筋、actual_is_best（実際の手が最善だったか）が含まれます。

目的は、人間向けに「局面のポイント」を抽出し、JSONで返すことです。

重要ルール:
- 必ずJSONのみを返してください。説明文や前置きは不要です。
- eval.type == "cp" なら数値評価（プラス=先手有利、マイナス=後手有利）
- eval.type == "mate" なら詰み（正=先手勝ち、負=後手勝ち）
- コメントの根拠は、入力中の評価値・候補手・読み筋・actual_is_bestに限定してください。
- 盤面を完全再現できない場合は、駒の利きや具体的な戦術を断定しすぎず、評価値の推移と候補手との差を主根拠にしてください。
- 評価値の推移全体を見て、形勢が大きく動いた手を swing_points として最大5件抽出してください。
- コメントは簡潔かつ実戦的に書いてください。
- 実際の手がAIの最善手と異なる場合（actual_is_best=false）、best_lineを参照し、short_commentに「AIの推奨は〇〇で、以降△△▲□□…と進む手順があった」のように最善手順の進行を含めてください。
- 不明なことは断定せず、控えめな表現を使ってください。

出力JSONのスキーマ:
{
  "swing_points": [
    {
      "move": number,
      "player": "sente or gote",
      "move_text": "string",
      "eval_after": "eval object",
      "tag": "string (例: 先手優勢確立, 形勢逆転, 詰み発生, 疑問手)",
      "short_comment": "string"
    }
  ],
  "summary": {
    "opening_to_middle": "string",
    "middle_to_endgame": "string",
    "final_phase": "string"
  }
}"""


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
