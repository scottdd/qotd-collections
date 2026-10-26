# Quote of the Day Collections (`qotd-collections`)

Curated quote collections maintained in **two synchronized formats**:

1. **Structured JSON (`structured/*.json`)** — Rich metadata for CMS plugins (`e107` `qotd_menu` v2.6+), web apps, and APIs, including quote text, attribution, attribution info/book/role, topic tags, and source URL.
2. **Classic Fortune Cookie (`fortune/*.fortune` + `.dat` & `fortune/*.txt`)** — Standard `%`-delimited text files compatible with BSD/Linux `fortune` (`strfile`), CLI scripts (`motd`), and the classic e107 `qotd_menu` plugin.

---

## Included Collections

| Collection | Structured JSON | Fortune File (`%` delimited) | Quotes | Description |
|---|---|---|---|---|
| **Default (General Wisdom & Humor)** | [`structured/default.json`](structured/default.json) | [`fortune/default.fortune`](fortune/default.fortune) | 176 | Clean, family-friendly, secular wisdom, science, programming/technology, literature, and humor quotes suitable out-of-the-box for any website |
| **Personal QOTD** | [`structured/personal-qotd.json`](structured/personal-qotd.json) | [`fortune/personal-qotd.fortune`](fortune/personal-qotd.fortune) | 233 | Scott's personal quote collection spanning wisdom, humor, science, history, technology, government, and Christian faith/theology |
| **Spiceworks IT Wisdom** | [`structured/spiceworks-wisdom.json`](structured/spiceworks-wisdom.json) | [`fortune/spiceworks-wisdom.fortune`](fortune/spiceworks-wisdom.fortune) | 116 | Classic IT pro, sysadmin, helpdesk, networking, and troubleshooting quotes from the Spiceworks community |

A legacy single-file [`legacy/quote.txt`](legacy/quote.txt) (seeded from `default`) is also maintained for drop-in compatibility with older `qotd_menu` installations.

---

## Structured JSON Schema

Each file in `structured/*.json` is a UTF-8 JSON array of quote objects:

```json
[
  {
    "id": "default-004",
    "quote": "The most exciting phrase to hear in science, the one that heralds new discoveries, is not \"Eureka!\" (I found it!) but \"That's funny...\"",
    "attribution": "Isaac Asimov",
    "attribution_info": "",
    "tags": [
      "science"
    ],
    "source_url": ""
  }
]
```

---

## Sync & Conversion Tool (`scripts/sync_collections.py`)

 The repository includes a zero-dependency Python 3 utility that converts between structured JSON and fortune cookie formats, compiles `.dat` binary indices when `strfile` (`fortune-mod`) is installed, and validates all collections for schema errors or duplicates.

### Commands

```bash
# Regenerate fortune/*.fortune, fortune/*.txt, and legacy/quote.txt from structured/*.json
python3 scripts/sync_collections.py build-fortunes

# Import a % delimited fortune file into structured/<collection>.json
python3 scripts/sync_collections.py import-fortune path/to/file.fortune --collection my-quotes --default-tag wisdom

# Validate all collections
python3 scripts/sync_collections.py validate
```

### Using with Linux `fortune`

```bash
fortune /path/to/qotd-collections/fortune/default.fortune
fortune /path/to/qotd-collections/fortune/personal-qotd.fortune
fortune /path/to/qotd-collections/fortune/spiceworks-wisdom.fortune
```

---

*Imagined by human, built with AI.*
