"""参加者ごとのまとめを作る（何度実行してもよい。ログ本体は読むだけで変更しない）

    python make_summary.py

出力（logs/summary/、git には入らない）:
  participants.csv   1人1行の一覧（Excel でそのまま開ける UTF-8 BOM 付き）
  sheets/<ID>.png    その人の全バージョンを並べた画像（★ = 最終画像）
"""
import csv
import os
import re
from datetime import datetime

from PIL import Image, ImageDraw, ImageFont

BASE = os.path.dirname(os.path.abspath(__file__))
LOGS = os.path.join(BASE, "logs")
OUT = os.path.join(LOGS, "summary")
NOTES = os.path.join(LOGS, "分析时注意.txt")


def read(name):
    path = os.path.join(LOGS, name)
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def ts(value):
    return datetime.fromisoformat(value)


def notes_by_id():
    """分析时注意.txt の「101  …」で始まる段落（続きの行も含む）を ID ごとに拾う"""
    if not os.path.exists(NOTES):
        return {}
    result, current = {}, None
    with open(NOTES, encoding="utf-8") as f:
        for line in f:
            m = re.match(r"^(\d{3})\s{2}(.*)", line)
            if m:
                current = m.group(1)
                result[current] = m.group(2).strip()
            elif current and line.startswith("     "):
                result[current] += " " + line.strip()
            else:
                current = None
    return result


def font(size):
    for name in ("msyh.ttc", "meiryo.ttc", "YuGothM.ttc", "arial.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def contact_sheet(pid, gens, final, path):
    images = []
    for r in gens:
        file = os.path.join(BASE, r["image_file"].replace("\\", os.sep))
        if os.path.exists(file):
            images.append((int(r["version"]), Image.open(file).convert("RGB")))
    if not images:
        return
    w, cols = 260, min(5, len(images))
    tiles = []
    label_font = font(18)
    for version, im in images:
        tile = im.resize((w, int(im.height * w / im.width)))
        draw = ImageDraw.Draw(tile)
        text = f"v{version}" + (" ★" if version == final else "")
        draw.rectangle([0, 0, 70 if version == final else 44, 26], fill="#ffffff")
        draw.text((6, 3), text, fill="#c0392b" if version == final else "#222222", font=label_font)
        if version == final:
            draw.rectangle([0, 0, tile.width - 1, tile.height - 1], outline="#c0392b", width=4)
        tiles.append(tile)
    h = max(t.height for t in tiles)
    rows = (len(tiles) + cols - 1) // cols
    sheet = Image.new("RGB", (w * cols, h * rows + 34), "#ffffff")
    ImageDraw.Draw(sheet).text((8, 6), f"ID {pid}", fill="#222222", font=font(20))
    for i, t in enumerate(tiles):
        sheet.paste(t, ((i % cols) * w, 34 + (i // cols) * h))
    sheet.save(path)


def main():
    events, gens, surveys = read("event_log.csv"), read("generation_log.csv"), read("survey_log.csv")
    notes = notes_by_id()
    survey_by_id = {}
    for r in surveys:
        survey_by_id[r["participant_id"]] = r  # 同じ ID が複数あれば最後の回答

    ids = []
    for r in events:
        if r["event"] == "start" and r["participant_id"] not in ids:
            ids.append(r["participant_id"])
    # 1xx は番号順、それ以外（未整理の ID）は後ろに参加順で
    ids.sort(key=lambda p: (0, int(p)) if re.fullmatch(r"1\d\d", p) else (1, 0))

    os.makedirs(os.path.join(OUT, "sheets"), exist_ok=True)
    rows = []
    for pid in ids:
        ev = [r for r in events if r["participant_id"] == pid]
        g = sorted((r for r in gens if r["participant_id"] == pid), key=lambda r: int(r["version"]))
        sv = survey_by_id.get(pid)
        get = lambda name: next((r["detail"] for r in ev if r["event"] == name), "")
        start = min(ts(r["timestamp"]) for r in ev if r["event"] == "start")
        finish = [ts(r["timestamp"]) for r in ev if r["event"] == "finish"]
        by_version = {r["version"]: r for r in g}

        real, same = 0, 0
        for r in g:
            if r["action"] in ("rewrite", "edit"):
                base = by_version.get(r["base_version"])
                if base and base["prompt"].strip() == r["prompt"].strip():
                    same += 1
                else:
                    real += 1

        # 最終画像：アンケートの番号 → ボタンの最後の選択 の順に採用
        choices = [r for r in ev if r["event"] == "final_choice"]
        final, source = "", ""
        if sv and sv.get("final_version"):
            final, source = sv["final_version"], "survey"
        if choices:
            last = choices[-1]
            if not final:
                final = last["version"]
            source = "manual" if last["detail"].startswith("manual") else (source or "button")
        final_int = int(final) if str(final).isdigit() else 0
        final_prompt = by_version.get(str(final_int), {}).get("prompt", "") if final_int else ""

        numbered = bool(re.fullmatch(r"1\d\d", pid))
        status = "complete" if (sv and numbered) else ("no_survey" if not sv else "not_numbered")

        rows.append({
            "id": pid,
            "status": status,
            "start": start.isoformat(timespec="minutes"),
            # 途中で言語を切り替えた人もいるので、最後に選んだ言語
            "ui_language": next((r["detail"] for r in reversed(ev) if r["event"] == "ui_language"), ""),
            "q1_experience": get("pre_experience"),
            "q2_pre_clarity": get("pre_clarity"),
            "versions": len(g),
            "real_edits": real,
            "same_text_regenerations": same,
            "first_image_sec": int((ts(g[0]["timestamp"]) - start).total_seconds()) if g else "",
            "finish_sec": int((finish[0] - start).total_seconds()) if finish else "",
            "time_up": "yes" if any(r["event"] == "time_up" for r in ev) else "",
            "finished": "yes" if finish else "",
            "final_version": final,
            "final_source": source,
            "q3_clearer": sv["clearer"] if sv else "",
            "q4_satisfaction": sv["satisfaction"] if sv else "",
            "q5_focus": sv["focus"] if sv else "",
            "q6_difficulty": sv["difficulty"] if sv else "",
            "q7_reason": sv["reason"] if sv else "",
            "q8_comment": sv["comment"] if sv else "",
            "first_prompt": g[0]["prompt"] if g else "",
            "final_prompt": final_prompt,
            "note": notes.get(pid, ""),
        })
        contact_sheet(pid, g, final_int, os.path.join(OUT, "sheets", f"{pid}.png"))

    with open(os.path.join(OUT, "participants.csv"), "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    counts = {}
    for r in rows:
        counts[r["status"]] = counts.get(r["status"], 0) + 1
    print(f"{len(rows)} participants -> {OUT}")
    for k, v in counts.items():
        print(f"  {k}: {v}  ({', '.join(r['id'] for r in rows if r['status'] == k)})")


if __name__ == "__main__":
    main()
