# starikov.co — Source code from starikov dot co.

Three small, dependency‑light tools that scratch common itches:

| Script                | One‑liner purpose                                           |
|-----------------------|-------------------------------------------------------------|
| **link_checker.py**   | Crawl a site, print a directory‑tree of pages, and flag bad internal links.  |
| **opml_to_markdown.py** | Turn an OPML file of RSS feeds into a share‑ready Markdown "starter pack". |
| **wordleconomics.py** | Rank Wordle opening guesses with aggregate, positional, and hybrid heuristics; optionally plot stats. |


## Quick install

```bash
git clone https://github.com/yourname/handy-scripts.git
cd handy-scripts
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
````


## Usage cheatsheet

```bash
# 1. Check for broken links inside a site (hard cap 1 000 pages)
python link_checker.py https://starikov.co --max-pages 1000

# 2. Convert an RSS OPML export to Markdown
python opml_to_markdown.py my_feeds.opml "My Favourite Feeds"

# 3. Print the top 50 hybrid‑scored Wordle openers and pop up the charts
python wordleconomics.py --words /usr/share/dict/words --top 50 --blend 0.08
```


## link_checker: Scan Any Site For 404s

`link_checker.py` is a tiny command‑line spider that crawls an entire website, reports every broken internal link (404/4xx/5xx), shows which page points to it, **and** prints a directory‑style tree of all pages visited.

### Features

* Breadth‑first crawl restricted to the same domain
* Detects and lists broken targets with their referring pages
* Pretty directory tree of every page it reached
* Progress bar with live page counter (`tqdm`)
* Safe page cap (`--max-pages`, default 10,000) & 10 s time‑outs

### Usage

```bash
python link_checker.py https://starikov.co
```

Common flags:

| Flag            | Default | Description                  |
| --------------- | ------- | ---------------------------- |
| `--max-pages N` | `10000` | Safety cap on pages to crawl |
| `--help`        | ―       | Full CLI help                |

### Example

```
Pages crawled: 1473 └── page=https://example.com/blog
=== Directory tree of visited pages ===
└── /
    ├── about
    ├── blog
    │   ├── index.html
    │   └── 2025
    │       └── launch-announcement
    └── contact

=== Broken links/pages ===
🔗 https://example.com/missing (404)
   └── linked from: https://example.com/blog/index.html
```


## opml_to_markdown: Convert OPML to a Share‑Ready RSS Starter Pack

Turn a sprawling OPML file into a neatly organised Markdown page—ready to
publish, paste into a blog post, or drop into a GitHub repo.

> *Why?*  Because handing friends an OPML file is helpful, but showing them a
> browsable, hyper‑linked "starter pack" is delightful.

### Features

* **One‑shot conversion** – pipe the script's stdout straight into a file or
  clipboard.
* **Keeps folders intact** – retains your OPML outline hierarchy as
  Markdown `###` headings.
* **Link‑rich output** – each feed entry shows both the homepage and its RSS
  endpoint.
* **Unicode‑safe** – emoji, non‑ASCII titles, and RTL text all pass through
  untouched.
* **Zero third‑party dependencies** – pure standard‑library Python 3.

### Usage

```bash
python opml_to_markdown.py INPUT.opml > starter_pack.md
```


## opml_to_markdown: Convert OPML to a Share‑Ready RSS Starter Pack

Turn a sprawling OPML file into a neatly organised Markdown page—ready to
publish, paste into a blog post, or drop into a GitHub repo.

> *Why?*  Because handing friends an OPML file is helpful, but showing them a
> browsable, hyper‑linked "starter pack" is delightful.


### Features

* **One‑shot conversion** – pipe the script's stdout straight into a file or
  clipboard.
* **Keeps folders intact** – retains your OPML outline hierarchy as
  Markdown `###` headings.
* **Link‑rich output** – each feed entry shows both the homepage and its RSS
  endpoint.
* **Unicode‑safe** – emoji, non‑ASCII titles, and RTL text all pass through
  untouched.
* **Zero third‑party dependencies** – pure standard‑library Python 3.

### Usage

```bash
python opml_to_markdown.py INPUT.opml > starter_pack.md
python opml_to_markdown.py INPUT.opml "Custom Title" > custom.md
```

| Pos | Argument                    | Description                                 |
| --- | --------------------------- | ------------------------------------------- |
| 1   | `INPUT.opml`                | An OPML file exported from your RSS reader. |
| 2   | `Custom Title` *(optional)* | Overrides the default document heading.     |


### Example

<details>
<summary>Click to expand sample output</summary>

```markdown
# Your First RSS Starter Pack

_Import the accompanying **OPML** into any reader (NetNewsWire, Reeder,
Feedly, etc.) to pull everything at once._

### Apple🍎
- **[Android Developers](https://android-developers.blogspot.com/)** — <sub>[RSS](https://feeds.feedburner.com/blogspot/hsDu)</sub>
- **[Apple&nbsp;| Developer](http://developer.apple.com/news/)** — <sub>[RSS](https://developer.apple.com/news/rss/news.rss)</sub>
- **[Apple&nbsp;| Press Releases](https://www.apple.com/newsroom)** — <sub>[RSS](https://www.apple.com/newsroom/rss-feed.rss)</sub>
⋮ _(_200‑plus lines snipped for brevity_)_

> _Generated automatically from the original OPML file._
```

</details>


## wordleconomics: Quant‑geek tools for Wordle openings

"**When in doubt, CRANE it out**" may sound clever, but data is better.
**wordleconomics** crunches a full English word list and ranks every five‑letter
candidate using three complementary heuristics:

| Heuristic   | What it measures                                                      | Good for…                         |
|-------------|-----------------------------------------------------------------------|-----------------------------------|
| **Aggregate** | How often each letter appears in *any* position across the list.     | Coverage of high‑value letters.   |
| **Positional** | How often each letter appears in each *slot* (index 0‑4).            | Hitting common patterns like "S‑‑E". |
| **Hybrid**   | A weighted blend of aggregate and positional (tunable via `--blend`). | Balancing broad coverage and placement. |

### Features

* **Zero dependencies beyond NumPy + Matplotlib.**
  Works everywhere Python 3 runs.
* **Configurable blend factor** – explore the continuum from *ADIEU* to *SOARE*.
* **Pretty leaderboards** – sorted by score, ties broken alphabetically.
* **Colourful charts** – optional bar‑plot of aggregate counts and heat‑map of
  positional frequencies.
* **Type‑hinted, Google‑style source** – ideal for hacking or porting.


### CLI reference

| Flag           | Default     | Description                                                 |
| -------------- | ----------- | ----------------------------------------------------------- |
| `--words PATH` | `words.txt` | Path to a newline‑separated word list.                      |
| `--top N`      | `100`       | How many rows to print for each leaderboard.                |
| `--blend α`    | `0.05`      | Positional weight in the hybrid formula (0 = agg, 1 = pos). |


### Example

<details>
<summary>Click to expand sample output</summary>
```bash
$ python wordleconomics.py \
      --words /usr/share/dict/words \
      --top   10 \
      --blend 0.05
Loaded 9981 words from /usr/share/dict/words

Aggregate Ranking (top 10):
  aries 1.78910
  arise 1.78910
  raise 1.78910
  serai 1.78910
  ariel 1.77978
  erian 1.77818
  irena 1.77818
  reina 1.77818
  arite 1.77327
  artie 1.77327

Positional Ranking (top 10):
  saite 0.57910
  barie 0.57599
  sairy 0.57349
  saily 0.57159
  tarie 0.57129
  sadie 0.57068
  maney 0.56768
  corey 0.56577
  solay 0.56367
  marie 0.55646

Hybrid Ranking (blend=0.05) (top 10):
  raise 0.99261
  serai 0.99234
  tarie 0.99092
  arise 0.98729
  aries 0.98674
  ariel 0.98236
  artie 0.97967
  reina 0.97917
  arite 0.97909
  arose 0.97730
```

*(Full 100‑row tables omitted for brevity – set `--top 100` to see them.)*
</details>

