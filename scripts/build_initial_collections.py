#!/usr/bin/env python3
"""
Builds and syncs the dual-format Quote of the Day collections:
  - structured/personal-qotd.json
  - structured/spiceworks-wisdom.json
  - fortune/personal-qotd.fortune (plain-text standard fortune format)
  - fortune/personal-qotd.txt (HTML-enhanced fortune format for Nextcloud / web)
  - fortune/spiceworks-wisdom.fortune (Spiceworks collector fortune format)
  - fortune/spiceworks-wisdom.txt (HTML-enhanced fortune format)
  - legacy/quote.txt (UTF-8 single-line format for legacy e107 qotd_menu compatibility)
"""
import json
import os
import re
import html

REPO_ROOT = "/home/scott/Projects/qotd-collections"
NEXTCLOUD_PERSONAL = "/home/scott/Nextcloud/Documents/Personal/qotd-fortune.txt"
E107_QUOTE_TXT = "/home/scott/Projects/dowlen-e107/site/e107_plugins/qotd_menu/quote.txt"
NEXTCLOUD_SPICEWORKS = "/home/scott/Nextcloud/Documents/Personal/qotd stuff/fortunes-spiceworks-wisdom"


def infer_personal_tags(quote: str, attribution: str, info: str) -> list:
    text = f"{quote} {attribution} {info}".lower()
    tags = []
    # Faith / Theology / Scripture
    faith_authors = {
        "jesus of nazareth", "c.s. lewis", "c. s. lewis", "r.a. torrey",
        "ted s. rendall", "b.b. warfield", "john tillotson", "john owen",
        "h.a. ironside", "richard owen roberts", "napoleon bonaparte",
        "a.w. tozer", "g.k. chesterton", "gk chesterton", "dennis f. kinlaw",
        "dietrich bonhoeffer", "augustine", "saint augustine of hippo",
        "charles spurgeon", "walter strickland", "jonathan edwards",
        "thomas watson", "john newton", "saint aelred of rievaulx",
        "reinhold niebuhr"
    }
    if any(a in attribution.lower() for a in faith_authors) or any(
        w in text for w in ["god", "christ", "jesus", "holy spirit", "revival", "scripture", "bible", "sin", "grace", "soul", "prayer", "church", "eternity", "heaven", "cross"]
    ):
        if any(w in text for w in ["john 5:", "john 14:", "psalm"]):
            tags.append("scripture")
        tags.append("faith")
        if any(w in text for w in ["revival", "grace", "sin", "holy spirit", "theology", "cross", "salvation", "savior"]):
            tags.append("theology")

    # Tech / Programming / Science
    if any(w in text for w in [
        "computer", "eniac", "technology", "backup", "data analysis",
        "while(!asleep)", "ff0000", "all my base", "programming",
        "science", "statistics", "statistician", "facebook", "nasa", "helium"
    ]):
        if any(w in text for w in ["computer", "eniac", "backup", "while(!asleep)", "ff0000", "programming", "technology", "facebook"]):
            tags.append("technology")
        if any(w in text for w in ["science", "statistics", "statistician", "helium", "dunning-kruger"]):
            tags.append("science")

    # History / Politics / Liberty / Government
    if any(w in text for w in [
        "government", "democracy", "politics", "politician", "revolution",
        "tyrant", "tyrants", "liberties", "freedom", "free society", "congress",
        "laws", "state", "washington", "federalist", "america", "war", "peace"
    ]) or any(a in attribution.lower() for a in [
        "john kennedy", "winston churchill", "alexander hamilton", "ronald reagan",
        "thomas jefferson", "thomas paine", "patrick henry", "ayn rand",
        "adlai stevenson", "p. j. o'rourke", "tacitus", "john adams",
        "margaret thatcher", "henry kissinger", "general george patton"
    ]):
        if any(w in text for w in ["freedom", "liberties", "free society", "right to be wrong", "bondage"]):
            tags.append("liberty")
        if any(w in text for w in ["government", "democracy", "politics", "politician", "congress", "washington", "tyrant", "state", "laws"]):
            tags.append("government")
        elif "history" in text or "war" in text:
            tags.append("history")

    # Humor / Wit
    if any(w in text for w in [
        "immature", "afraid of dying", "where would you put it", "moray",
        "manure", "fruit flies like a banana", "golf", "ring the bell and run away",
        "comedy", "took his shoes", "spud", "wacko", "helium", "sheep++",
        "all my base", "add to cart", "anemic", "rainy sunday", "15 minutes",
        "arguing with a woman", "over the hill", "law firm", "live, laugh, love"
    ]) or any(a in attribution.lower() for a in [
        "woody allen", "steven wright", "groucho marx", "mark twain",
        "dave barry", "oscar wilde", "will rogers", "bob hope", "craig ferguson",
        "fabulous furry freak brothers", "firesign theatre", "scott adams"
    ]):
        tags.append("humor")

    # Philosophy / Wisdom / Character / Education
    if any(w in text for w in [
        "character", "wise", "wisdom", "truth", "honest", "integrity",
        "philosophy", "education", "knowledge", "learning", "humility",
        "friendship", "optimism", "goals", "habit", "simplify", "time"
    ]) or not tags:
        tags.append("wisdom")

    # Deduplicate preserving order, max 3 tags
    seen = []
    for t in tags:
        if t not in seen:
            seen.append(t)
    return seen[:3]


def clean_outer_quotes(s: str) -> str:
    s = s.strip()
    # Replace Windows-1252 / smart quotes with clean standard or typographic quotes
    # Check if wrapped in matching quotes with no internal quotes of the same kind
    if len(s) >= 2:
        if (s.startswith('"') and s.endswith('"') and s[1:-1].count('"') == 0):
            s = s[1:-1].strip()
        elif (s.startswith('“') and s.endswith('”') and '“' not in s[1:-1] and '”' not in s[1:-1]):
            s = s[1:-1].strip()
        elif (s.startswith('“') and s.endswith('"') and '“' not in s[1:-1] and '"' not in s[1:-1]):
            s = s[1:-1].strip()
    # Also fix trailing stray quote when opening quote was missing (e.g. Burke quote)
    if s.endswith('"') and s.count('"') == 1:
        s = s[:-1].strip()
    return s


def parse_attribution_line(line: str):
    """
    Parses a line starting with — into (attribution, attribution_info, source_url).
    """
    s = line.strip()
    s = re.sub(r'^(?:—|--|-)\s*(?:&nbsp;|\s)*', '', s).strip()

    # Extract URL if present
    url = ""
    m_url = re.search(r'(https?://[^\s)\]]+)', s)
    if m_url:
        url = m_url.group(1).rstrip('.,;)')

    # Check if there is <b>...</b>
    m_bold = re.match(r'^<b>(.*?)</b>(.*)$', s, flags=re.DOTALL)
    if m_bold:
        author_raw = m_bold.group(1).strip()
        rest = m_bold.group(2).strip()
    else:
        author_raw = s
        rest = ""

    # Clean URL from author_raw or rest
    if url:
        author_raw = author_raw.replace(url, '').strip()
        rest = rest.replace(url, '').strip()
        rest = re.sub(r'\(\s*from article:\s*\)', '', rest).strip()
        rest = re.sub(r'\(\s*\)', '', rest).strip()

    info = ""
    author = author_raw

    # Clean up rest
    if rest:
        rest = re.sub(r'^[,;\-–—]+\s*', '', rest).strip()
        # Strip outer parens or brackets if they wrap the entire rest
        if (rest.startswith('(') and rest.endswith(')')) or (rest.startswith('[') and rest.endswith(']')):
            rest = rest[1:-1].strip()
        info = rest

    # Sometimes author_raw itself contains ", Book Title" or " (Work)" inside <b>...</b>
    if not info:
        # Special known splits inside <b>...</b>
        if author.startswith("Francis Bacon,"):
            author, info = "Francis Bacon", author[len("Francis Bacon,"):].strip()
        elif author.startswith("Bertrand Russell,"):
            author, info = "Bertrand Russell", author[len("Bertrand Russell,"):].strip()
        elif author.startswith("Kierkegaard,"):
            author, info = "Søren Kierkegaard", author[len("Kierkegaard,"):].strip()
        elif author.startswith("Artimus Ward,"):
            author, info = "Artemus Ward", author[len("Artimus Ward,"):].strip()
        elif author.startswith("Popular Mechanics,"):
            author, info = "Popular Mechanics", author[len("Popular Mechanics,"):].strip()
        elif author.startswith("Fred Rogers,"):
            author, info = "Fred Rogers", author[len("Fred Rogers,"):].strip()
        elif author.startswith("R.A. Torrey,"):
            author, info = "R.A. Torrey", author[len("R.A. Torrey,"):].strip()
        elif author.startswith("C.S. Lewis,"):
            author, info = "C.S. Lewis", author[len("C.S. Lewis,"):].strip()
        elif author.startswith("Lionel Shriver,"):
            author, info = "Lionel Shriver", author[len("Lionel Shriver,"):].strip()
        elif author == "Bob Hope to U.S. troops in Vietnam":
            author, info = "Bob Hope", "to U.S. troops in Vietnam"
        elif author.startswith("Author unknown,"):
            author, info = "Unknown", author[len("Author unknown,"):].strip()
        elif author == "(from a programming forum)":
            author, info = "Unknown", "from a programming forum"
        else:
            m_paren = re.match(r'^([^()]+?)\s*\(([^()]+)\)$', author)
            if m_paren:
                author = m_paren.group(1).strip()
                info = m_paren.group(2).strip()

    # Normalize C. S. Lewis / GK Chesterton
    if author == "C. S. Lewis":
        author = "C.S. Lewis"
    elif author == "GK Chesterton":
        author = "G.K. Chesterton"
    elif author == '"Saint" Augustine of Hippo':
        author = "Saint Augustine of Hippo"

    return author.strip(), info.strip(), url.strip()


def parse_personal_collection():
    with open(NEXTCLOUD_PERSONAL, 'r', encoding='utf-8') as f:
        raw = f.read()

    blocks = [b.strip() for b in re.split(r'(?m)^%\s*$', raw) if b.strip()]
    items = []
    seq = 0

    for block in blocks:
        # Skip empty template entry
        if '"Template"' in block and '<b></b>' in block:
            continue

        lines = [l.strip() for l in block.splitlines() if l.strip()]
        attr_indices = [i for i, l in enumerate(lines) if l.startswith('—')]

        if len(attr_indices) > 1:
            # Multi-part conversational / riff quote (e.g. Steven Wright, Firesign Theatre, Descartes)
            parts = []
            authors = []
            for l in lines:
                l_clean = re.sub(r'<br\s*/?>', '', l).strip()
                if not l_clean:
                    continue
                if l_clean.startswith('—'):
                    a, inf, _ = parse_attribution_line(l_clean)
                    if a and a not in authors:
                        authors.append(a)
                    parts.append(f"— {a}" + (f" ({inf})" if inf else ""))
                else:
                    parts.append(html.unescape(l_clean))
            quote_text = "\n".join(parts)
            attribution = " / ".join(authors[:3])
            info = "Multi-quote riff"
            url = ""
        elif len(attr_indices) == 1 and attr_indices[0] == len(lines) - 1:
            attr_line = lines[-1]
            quote_lines = lines[:-1]
            quote_raw = "\n".join(quote_lines)
            quote_raw = re.sub(r'<br\s*/?>\s*', '\n', quote_raw)
            # collapse 3+ newlines to 2
            quote_raw = re.sub(r'\n{3,}', '\n\n', quote_raw).strip()
            quote_raw = html.unescape(quote_raw)
            quote_text = clean_outer_quotes(quote_raw)
            attribution, info, url = parse_attribution_line(attr_line)
        else:
            quote_raw = "\n".join(lines)
            quote_raw = re.sub(r'<br\s*/?>\s*', '\n', quote_raw)
            quote_raw = re.sub(r'\n{3,}', '\n\n', quote_raw).strip()
            quote_raw = html.unescape(quote_raw)
            quote_text = clean_outer_quotes(quote_raw)
            attribution = ""
            info = ""
            url = ""

        seq += 1
        tags = infer_personal_tags(quote_text, attribution, info)
        items.append({
            "id": f"personal-{seq:03d}",
            "quote": quote_text,
            "attribution": attribution,
            "attribution_info": info,
            "tags": tags,
            "source_url": url
        })

    return items


def infer_spiceworks_tags(quote: str, url: str) -> list:
    text = f"{quote} {url}".lower()
    tags = ["spiceworks"]
    if "haiku" in text:
        tags.append("haiku")
    if any(w in text for w in ["ipv4", "ipv6", "udp", "tcp", "dns", "dhcp", "dora", "arp", "ping", "osi-model", "subnet", "fiber", "firewall", "iptables", "baud"]):
        tags.append("networking")
    if any(w in text for w in ["security", "secured", "password", "post-it", "breached", "usb", "sanitize", "sql", "bobby tables"]):
        tags.append("security")
    if any(w in text for w in ["ai-", "-ai", " ai ", "copilot", "magic 8 ball"]):
        tags.append("ai")
    if any(w in text for w in ["backup", "restore"]):
        tags.append("backups")
    if any(w in text for w in ["printer", "pc load letter", "toner", "fax", "copier"]):
        tags.append("printers")
    if any(w in text for w in ["career", "internship", "director", "boss", "salary", "on-call", "burnout", "budget", "certifications", "title"]):
        tags.append("career")
    if any(w in text for w in ["user", "helpdesk", "help desk", "ticket", "customer", "reboot", "reinstall"]):
        tags.append("sysadmin")
    if len(tags) == 1:
        tags.append("it-humor")
    return tags[:3]


def parse_spiceworks_collection():
    with open(NEXTCLOUD_SPICEWORKS, 'r', encoding='utf-8') as f:
        raw = f.read()

    blocks = [b.strip() for b in re.split(r'(?m)^%\s*$', raw) if b.strip()]
    items = []
    seq = 0

    for block in blocks:
        if block.startswith('//'):
            continue
        lines = [l.strip() for l in block.splitlines() if l.strip()]
        url = ""
        if len(lines) >= 2 and lines[-1].startswith('http'):
            url = lines[-1].strip()
            body = " ".join(lines[:-1]).strip()
        else:
            body = " ".join(lines).strip()

        # Check inline (https://...) at the end
        m_inline_url = re.search(r'\((https?://[^\s)]+)\)\s*$', body)
        if m_inline_url and not url:
            url = m_inline_url.group(1)
            body = body[:m_inline_url.start()].strip()

        # Split quote and author on last " - "
        attribution = ""
        info = "Spiceworks Community"
        quote_text = body
        if " - " in body:
            q_part, a_part = body.rsplit(" - ", 1)
            quote_text = q_part.strip()
            a_part = a_part.strip()
            if a_part == "(programming forum, attribution TBD)":
                attribution = "Unknown"
                info = "programming forum, attribution TBD"
            else:
                m_paren = re.match(r'^([^()]+?)\s*\(([^()]+)\)$', a_part)
                if m_paren:
                    attribution = m_paren.group(1).strip()
                    info = f"Spiceworks Community ({m_paren.group(2).strip()})"
                else:
                    attribution = a_part

        quote_text = clean_outer_quotes(quote_text)
        seq += 1
        tags = infer_spiceworks_tags(quote_text, url)
        items.append({
            "id": f"spiceworks-{seq:03d}",
            "quote": quote_text,
            "attribution": attribution,
            "attribution_info": info,
            "tags": tags,
            "source_url": url
        })

    return items


def write_outputs(personal_items, spiceworks_items):
    # 1. Structured JSON files
    with open(os.path.join(REPO_ROOT, "structured/personal-qotd.json"), "w", encoding="utf-8") as f:
        json.dump(personal_items, f, indent=2, ensure_ascii=False)
        f.write("\n")

    with open(os.path.join(REPO_ROOT, "structured/spiceworks-wisdom.json"), "w", encoding="utf-8") as f:
        json.dump(spiceworks_items, f, indent=2, ensure_ascii=False)
        f.write("\n")

    # 2. Standard plain-text fortune files (fortune/*.fortune)
    with open(os.path.join(REPO_ROOT, "fortune/personal-qotd.fortune"), "w", encoding="utf-8") as f:
        for item in personal_items:
            q = re.sub(r'</?i>', '', item["quote"])
            f.write(q + "\n")
            if item["attribution"] and item["attribution_info"] != "Multi-quote riff":
                attr_str = f"    — {item['attribution']}"
                if item["attribution_info"]:
                    attr_str += f", {item['attribution_info']}"
                if item["source_url"]:
                    attr_str += f" ({item['source_url']})"
                f.write(attr_str + "\n")
            f.write("%\n")

    with open(os.path.join(REPO_ROOT, "fortune/spiceworks-wisdom.fortune"), "w", encoding="utf-8") as f:
        f.write("// Spiceworks wisdom - Fortune file\n%\n")
        for item in spiceworks_items:
            attr_part = item["attribution"]
            if item["attribution_info"] and item["attribution_info"].startswith("Spiceworks Community ("):
                extra = item["attribution_info"][len("Spiceworks Community ("):-1]
                attr_part = f"{attr_part} ({extra})"
            elif item["attribution_info"] == "programming forum, attribution TBD":
                attr_part = "(programming forum, attribution TBD)"
            line1 = f"{item['quote']} - {attr_part}" if attr_part else item["quote"]
            f.write(line1 + "\n")
            if item["source_url"]:
                f.write(item["source_url"] + "\n")
            f.write("%\n")

    # 3. HTML-enhanced fortune files (fortune/*.txt) matching Nextcloud qotd-fortune.txt
    with open(os.path.join(REPO_ROOT, "fortune/personal-qotd.txt"), "w", encoding="utf-8") as f:
        for item in personal_items:
            q_html = item["quote"].replace("\n", "<br/>\n")
            if item["attribution"] and item["attribution_info"] != "Multi-quote riff":
                f.write(q_html + "<br/>\n")
                attr_html = f"—&nbsp;<b>{item['attribution']}</b>"
                if item["attribution_info"]:
                    attr_html += f", {item['attribution_info']}"
                if item["source_url"]:
                    attr_html += f" ({item['source_url']})"
                f.write(attr_html + "\n%\n")
            else:
                f.write(q_html + "\n%\n")

    with open(os.path.join(REPO_ROOT, "fortune/spiceworks-wisdom.txt"), "w", encoding="utf-8") as f:
        for item in spiceworks_items:
            q_html = item["quote"].replace("\n", "<br/>\n")
            f.write(q_html + "<br/>\n")
            attr_html = f"—&nbsp;<b>{item['attribution'] or 'Anonymous'}</b>"
            if item["attribution_info"]:
                attr_html += f", {item['attribution_info']}"
            if item["source_url"]:
                attr_html += f" (<a href=\"{item['source_url']}\" target=\"_blank\" rel=\"noopener\">source</a>)"
            f.write(attr_html + "\n%\n")

    # 4. Legacy single-line quote.txt (clean UTF-8)
    with open(os.path.join(REPO_ROOT, "legacy/quote.txt"), "w", encoding="utf-8") as f:
        for item in personal_items:
            q_line = item["quote"].replace("\n", "<br />")
            if item["attribution"] and item["attribution_info"] != "Multi-quote riff":
                attr_str = item["attribution"]
                if item["attribution_info"]:
                    attr_str += f", {item['attribution_info']}"
                f.write(f"{q_line} - <b>{attr_str}</b>\n")
            else:
                f.write(f"{q_line}\n")


if __name__ == "__main__":
    p_items = parse_personal_collection()
    s_items = parse_spiceworks_collection()
    write_outputs(p_items, s_items)
    print(f"Built personal-qotd: {len(p_items)} quotes")
    print(f"Built spiceworks-wisdom: {len(s_items)} quotes")
