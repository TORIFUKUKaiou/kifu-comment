"""Parse .kif files with engine analysis into structured JSON."""

import re
import sys
import json


def parse_eval(eval_raw: str):
    eval_raw = eval_raw.strip()
    if re.match(r"^-?\d+$", eval_raw):
        return {"type": "cp", "value": int(eval_raw)}
    m = re.match(r"^(-?)詰\s*(\d+)$", eval_raw)
    if m:
        sign = -1 if m.group(1) == "-" else 1
        return {"type": "mate", "value": sign * int(m.group(2))}
    return {"type": "raw", "value": eval_raw}


def eval_as_cp(ev):
    """Return a comparable integer. Mate is treated as ±99999."""
    if ev["type"] == "cp":
        return ev["value"]
    if ev["type"] == "mate":
        return 99999 if ev["value"] > 0 else -99999
    return 0


def parse_kif(path: str) -> dict:
    with open(path, "r", encoding="cp932") as f:
        lines = f.readlines()

    header = {}
    moves = []
    current_move = None
    analyses = []

    for raw_line in lines:
        line = raw_line.rstrip("\r\n")

        m = re.match(r"^(.+?)：(.+)$", line)
        if m and not line.startswith("**") and not line.startswith(" "):
            header[m.group(1)] = m.group(2)
            continue

        m = re.match(r"^\s+(\d+)\s+(.+?)\s+\(", line)
        if m:
            if current_move is not None:
                current_move["analyses"] = analyses
                moves.append(current_move)
            move_num = int(m.group(1))
            move_text = m.group(2).strip()
            player = "sente" if move_num % 2 == 1 else "gote"
            current_move = {
                "move": move_num,
                "player": player,
                "move_text": move_text,
            }
            analyses = []
            continue

        m = re.match(
            r"^\*\*解析\s+\d+\s*(○|△|×)?\s*候補(\d+)\s+時間\s+\S+\s+深さ\s+\S+\s+ノード数\s+\d+\s+評価値\s+(.+?)\s+読み筋\s+(.+)$",
            line,
        )
        if m:
            match_mark = m.group(1) or ""
            candidate = int(m.group(2))
            ev = parse_eval(m.group(3))
            best_line = m.group(4).strip()

            analyses.append({
                "candidate": candidate,
                "is_best": match_mark == "○",
                "match_mark": match_mark,
                "eval": ev,
                "best_line": best_line,
            })
            continue

    if current_move is not None:
        current_move["analyses"] = analyses
        moves.append(current_move)

    # Build structured output
    result = []
    prev_cp = None
    for mv in moves:
        if not mv["analyses"]:
            continue

        best = next((a for a in mv["analyses"] if a["candidate"] == 1), mv["analyses"][0])
        actual = next((a for a in mv["analyses"] if a["match_mark"]), None)
        actual_is_best = actual["is_best"] if actual else False
        eval_after = actual["eval"] if actual else best["eval"]
        cp = eval_as_cp(eval_after)

        entry = {
            "move": mv["move"],
            "player": mv["player"],
            "move_text": mv["move_text"],
            "eval_after": eval_after,
            "eval_source": "actual" if actual else "best",
            "actual_eval": actual["eval"] if actual else None,
            "best_eval": best["eval"],
            "best_line": best["best_line"],
            "actual_is_best": actual_is_best,
            "actual_move_in_candidates": actual is not None,
            "candidates": len(mv["analyses"]),
        }

        if prev_cp is not None:
            entry["eval_diff"] = cp - prev_cp
        prev_cp = cp
        result.append(entry)

    return {
        "header": header,
        "total_moves": len(moves),
        "moves": result,
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python parse_kif.py <file.kif>", file=sys.stderr)
        sys.exit(1)
    data = parse_kif(sys.argv[1])
    print(json.dumps(data, ensure_ascii=False, indent=2))
