#!/usr/bin/env python3
"""
sync_collections.py — Dual-format Quote of the Day collection utility.

Usage:
  python3 scripts/sync_collections.py validate
  python3 scripts/sync_collections.py build-fortunes
  python3 scripts/sync_collections.py import-fortune --collection personal-qotd --file /path/to/file.fortune
  python3 scripts/sync_collections.py import-spiceworks --file /path/to/fortunes-spiceworks-wisdom
"""
import argparse
import html
import json
import os
import re
import subprocess
import shutil
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STRUCTURED_DIR = os.path.join(REPO_ROOT, "structured")
FORTUNE_DIR = os.path.join(REPO_ROOT, "fortune")
LEGACY_DIR = os.path.join(REPO_ROOT, "legacy")


def norm_key(text: str) -> str:
    s = re.sub(r"<[^>]+>", " ", text)
    s = html.unescape(s)
    return re.sub(r"[^a-z0-9]+", "", s.lower())[:80]


def load_collection(name: str) -> list:
    path = os.path.join(STRUCTURED_DIR, f"{name}.json")
    if not os.path.isfile(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_collection(name: str, items: list):
    os.makedirs(STRUCTURED_DIR, exist_ok=True)
    path = os.path.join(STRUCTURED_DIR, f"{name}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(items, f, indent=2, ensure_ascii=False)
        f.write("\n")


def render_fortunes(name: str, items: list):
    os.makedirs(FORTUNE_DIR, exist_ok=True)
    fortune_path = os.path.join(FORTUNE_DIR, f"{name}.fortune")
    txt_path = os.path.join(FORTUNE_DIR, f"{name}.txt")

    if name == "spiceworks-wisdom":
        with open(fortune_path, "w", encoding="utf-8") as f:
            f.write("// Spiceworks wisdom - Fortune file\n%\n")
            for item in items:
                attr_part = item.get("attribution", "")
                info = item.get("attribution_info", "")
                if info and info.startswith("Spiceworks Community ("):
                    extra = info[len("Spiceworks Community ("):-1]
                    attr_part = f"{attr_part} ({extra})"
                elif info == "programming forum, attribution TBD":
                    attr_part = "(programming forum, attribution TBD)"
                line1 = f"{item['quote']} - {attr_part}" if attr_part else item["quote"]
                f.write(line1 + "\n")
                if item.get("source_url"):
                    f.write(item["source_url"] + "\n")
                f.write("%\n")
    else:
        with open(fortune_path, "w", encoding="utf-8") as f:
            for item in items:
                q = re.sub(r"</?i>", "", item["quote"])
                f.write(q + "\n")
                if item.get("attribution") and item.get("attribution_info") != "Multi-quote riff":
                    attr_str = f"    — {item['attribution']}"
                    if item.get("attribution_info"):
                        attr_str += f", {item['attribution_info']}"
                    if item.get("source_url"):
                        attr_str += f" ({item['source_url']})"
                    f.write(attr_str + "\n")
                f.write("%\n")

    # HTML-enhanced fortune format (*.txt)
    with open(txt_path, "w", encoding="utf-8") as f:
        for item in items:
            q_html = item["quote"].replace("\n", "<br/>\n")
            if item.get("attribution") and item.get("attribution_info") != "Multi-quote riff":
                f.write(q_html + "<br/>\n")
                attr_html = f"—&nbsp;<b>{item['attribution']}</b>"
                if item.get("attribution_info"):
                    attr_html += f", {item['attribution_info']}"
                if item.get("source_url"):
                    attr_html += f" ({item['source_url']})"
                f.write(attr_html + "\n%\n")
            else:
                f.write(q_html + "\n%\n")

    # Also update legacy/quote.txt for personal-qotd
    if name == "personal-qotd":
        os.makedirs(LEGACY_DIR, exist_ok=True)
        with open(os.path.join(LEGACY_DIR, "quote.txt"), "w", encoding="utf-8") as f:
            for item in items:
                q_line = item["quote"].replace("\n", "<br />")
                if item.get("attribution") and item.get("attribution_info") != "Multi-quote riff":
                    attr_str = item["attribution"]
                    if item.get("attribution_info"):
                        attr_str += f", {item['attribution_info']}"
                    f.write(f"{q_line} - <b>{attr_str}</b>\n")
                else:
                    f.write(f"{q_line}\n")

    # Build .dat index if strfile is installed
    strfile_bin = shutil.which("strfile")
    if strfile_bin:
        subprocess.run([strfile_bin, "-s", fortune_path, fortune_path + ".dat"], check=False)


def cmd_validate():
    ok = True
    for fn in sorted(os.listdir(STRUCTURED_DIR)):
        if not fn.endswith(".json"):
            continue
        name = fn[:-5]
        path = os.path.join(STRUCTURED_DIR, fn)
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        required = {"id", "quote", "attribution", "attribution_info", "tags", "source_url"}
        for idx, item in enumerate(data, 1):
            missing = required - set(item.keys())
            if missing:
                print(f"[FAIL] {fn} item #{idx} missing keys: {missing}")
                ok = False
            if not item.get("quote", "").strip():
                print(f"[FAIL] {fn} item #{idx} has empty quote")
                ok = False
        f_path = os.path.join(FORTUNE_DIR, f"{name}.fortune")
        t_path = os.path.join(FORTUNE_DIR, f"{name}.txt")
        print(f"[OK] {name}: {len(data)} structured quotes | fortune={os.path.isfile(f_path)} | txt={os.path.isfile(t_path)}")
    return 0 if ok else 1


def cmd_build_fortunes():
    for fn in sorted(os.listdir(STRUCTURED_DIR)):
        if not fn.endswith(".json"):
            continue
        name = fn[:-5]
        items = load_collection(name)
        render_fortunes(name, items)
        print(f"Generated fortune/{name}.fortune and fortune/{name}.txt ({len(items)} quotes)")
    return 0


def main():
    parser = argparse.ArgumentParser(description="Manage dual-format Quote of the Day collections")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("validate", help="Validate structured JSON and fortune files")
    sub.add_parser("build-fortunes", help="Regenerate fortune/*.fortune, fortune/*.txt, and legacy/quote.txt from structured/*.json")
    args = parser.parse_args()
    if args.cmd == "validate":
        sys.exit(cmd_validate())
    elif args.cmd == "build-fortunes":
        sys.exit(cmd_build_fortunes())


if __name__ == "__main__":
    main()
