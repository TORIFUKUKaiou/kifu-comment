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


def extract_first_move(best_line: str) -> str:
    return best_line.split(" ", 1)[0].strip()


def strip_player_prefix(move_text: str) -> str:
    if move_text[:1] in ("▲", "△", "☗", "☖"):
        return move_text[1:]
    return move_text


def eval_loss_for_player(player: str, best_eval: dict, actual_eval: dict):
    best_cp = eval_as_cp(best_eval)
    actual_cp = eval_as_cp(actual_eval)
    if player == "gote":
        best_cp = -best_cp
        actual_cp = -actual_cp
    return best_cp - actual_cp


def parse_kif(path: str) -> dict:
    with open(path, "r", encoding="cp932") as f:
        lines = f.readlines()

    header = {}
    moves = []
    pending_analyses = []

    for raw_line in lines:
        line = raw_line.rstrip("\r\n")

        m = re.match(r"^(.+?)：(.+)$", line)
        if m and not line.startswith("**") and not line.startswith(" "):
            header[m.group(1)] = m.group(2)
            continue

        m = re.match(r"^\s+(\d+)\s+(.+?)\s+\(", line)
        if m:
            move_num = int(m.group(1))
            move_text = m.group(2).strip()
            player = "sente" if move_num % 2 == 1 else "gote"
            moves.append({
                "move": move_num,
                "player": player,
                "move_text": move_text,
                "analyses": pending_analyses,
            })
            pending_analyses = []
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

            pending_analyses.append({
                "candidate": candidate,
                "is_best": match_mark == "○",
                "match_mark": match_mark,
                "eval": ev,
                "best_line": best_line,
                "move_text": strip_player_prefix(extract_first_move(best_line)),
            })
            continue

    # Build structured output
    result = []
    prev_cp = None
    for mv in moves:
        if not mv["analyses"]:
            continue

        best = next((a for a in mv["analyses"] if a["candidate"] == 1), mv["analyses"][0])
        actual = next((a for a in mv["analyses"] if a["move_text"] == mv["move_text"]), None)
        quality_mark = next((a["match_mark"] for a in mv["analyses"] if a["match_mark"]), "")
        actual_is_best = actual is not None and actual["candidate"] == 1
        eval_after = actual["eval"] if actual else best["eval"]
        cp = eval_as_cp(eval_after)
        eval_loss = eval_loss_for_player(mv["player"], best["eval"], actual["eval"]) if actual else None

        entry = {
            "move": mv["move"],
            "player": mv["player"],
            "move_text": mv["move_text"],
            "eval_after": eval_after,
            "eval_source": "actual" if actual else "best",
            "actual_eval": actual["eval"] if actual else None,
            "best_eval": best["eval"],
            "eval_loss": eval_loss,
            "quality_mark": quality_mark,
            "best_move_text": best["move_text"],
            "best_line": best["best_line"],
            "actual_is_best": actual_is_best,
            "actual_move_in_candidates": actual is not None,
            "actual_candidate_rank": actual["candidate"] if actual else None,
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
