# Quote of the Day Collections (`qotd-collections`)

Curated Quote of the Day (`QotD`) collections stored in **dual formats** — both **structured JSON** (with rich attribution, context, topical tags, and source URLs) and classic **`%`-delimited fortune-cookie files** (compatible with BSD/Linux `fortune`, Nextcloud notes, and `@H-QotD Collector`).

---

## Collections

| Collection | Structured JSON | Standard Fortune (`%`) | HTML Fortune (`%`) | Quotes | Description |
| :--- | :--- | :--- | :--- | :---: | :--- |
| **`personal-qotd`** | [`structured/personal-qotd.json`](structured/personal-qotd.json) | [`fortune/personal-qotd.fortune`](fortune/personal-qotd.fortune) | [`fortune/personal-qotd.txt`](fortune/personal-qotd.txt) | **168** | Personal collection of quotes on wisdom, faith & theology, history, liberty, science, technology, and humor (combining Nextcloud `qotd-fortune.txt` and `dowlen.net` `quote.txt`). |
| **`spiceworks-wisdom`** | [`structured/spiceworks-wisdom.json`](structured/spiceworks-wisdom.json) | [`fortune/spiceworks-wisdom.fortune`](fortune/spiceworks-wisdom.fortune) | [`fortune/spiceworks-wisdom.txt`](fortune/spiceworks-wisdom.txt) | **116** | Sysadmin, networking, security, helpdesk, and IT humor quotes curated from the Spiceworks Community (`@H-QotD Collector`). |

A legacy single-line-per-quote file is also maintained at [`legacy/quote.txt`](legacy/quote.txt) (clean UTF-8) for backward compatibility with older e107 `qotd_menu` installations.

---

## Structured JSON Schema (`structured/*.json`)

Each collection in `structured/<collection>.json` is a UTF-8 JSON array of quote objects:

```json
{
  "id": "personal-027",
  "quote": "There is an evil tendency underlying all our technology - the tendency to do what is reasonable even when it isn't any good.",
  "attribution": "Robert Pirsig",
  "attribution_info": "Zen and the Art of Motorcycle Maintenance",
  "tags": [
    "technology",
    "wisdom"
  ],
  "source_url": ""
}
```

### Fields
- **`id`** (`string`): Stable collection-prefixed identifier (`personal-001`, `spiceworks-001`, etc.).
- **`quote`** (`string`): Clean UTF-8 quote text (without outer redundant wrapping quotation marks).
- **`attribution`** (`string`): Speaker, author, or community handle.
- **`attribution_info`** (`string`): Book, sermon, article, date, or community context.
- **`tags`** (`string[]`): Topical tags for filtering and themed tag pills on the frontend.
- **`source_url`** (`string`): Optional canonical URL to the source post, article, or podcast.

---

## Sync & Validation Utility (`scripts/sync_collections.py`)

 Regenerate all fortune-cookie files (`fortune/*.fortune`, `fortune/*.txt`, and `legacy/quote.txt`) from `structured/*.json` and validate all schemas:

```bash
python3 scripts/sync_collections.py build-fortunes
python3 scripts/sync_collections.py validate
```

---

## Integration with e107 `qotd_menu` (`v2.6.0`)

The upgraded **Quote of the Day (`qotd_menu` v2.6.0)** plugin on `dowlen.net` supports:
1. **Direct GitHub & Local Sync:** One-click import from `https://raw.githubusercontent.com/scottdd/qotd-collections/main/structured/<collection>.json` (or bundled `quotes/` files) into the `e107_qotd` database table.
2. **Dual Data Source:** Serve quotes from either the MySQL table (`e107_qotd`) or directly from the structured JSON / fortune files.
3. **Pinned Quote Date Ranges & Rotation Mode:** Pin any quote to a specific `Start Date` → `End Date` window, and choose between deterministic **Daily Quote of the Day** or **Random on Every Page Load** rotation.
4. **Theme-Following Frontend:** Semantic `<figure>` / `<blockquote>` / `<figcaption>` rendering with theme-inheriting tag pills and an AJAX **"↻ Another Quote"** button.
