#!/usr/bin/env python3
"""link_checker.py

Crawls a website, reports broken internal links, and prints a directory‑style
tree of all pages visited.

Typical usage example:

    $ python link_checker.py https://example.com --max-pages 1000
"""

from __future__ import annotations

import argparse
import collections
import sys
from collections import deque
from typing import Deque, Dict, Iterable, Iterator, Set
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from tqdm import tqdm

HEADERS: dict[str, str] = {
  "User-Agent": ("LinkChecker/1.2 (+https://github.com/yourname/linkchecker)")
}

# Explicit list of HTTP status codes to treat as “broken”.
_BROKEN_STATUS_CODES: set[int] = {400, 401, 403, 404, 410, 429, 500, 502, 503, 504}

_TIMEOUT: int = 10


def _normalize(url: str) -> str:
  """Returns *url* without a trailing slash (except at the root)."""
  if url in ("http://", "https://"):
    return url
  return url.rstrip("/") or "/"


def _is_internal(url: str, base_netloc: str) -> bool:
  """True iff *url* is hosted on *base_netloc* (or is relative)."""
  parsed = urlparse(url)
  return parsed.netloc in ("", base_netloc)


def _extract_links(html: str, base_url: str) -> Iterator[str]:
  """Yields absolute URLs discovered in *html*."""
  soup = BeautifulSoup(html, "html.parser")
  for tag in soup.find_all("a", href=True):
    href = tag["href"]
    if href.startswith(("#", "mailto:", "javascript:", "tel:")):
      continue
    yield urljoin(base_url, href.split("#", 1)[0])


def _is_broken(status_code: int) -> bool:
  """Returns True if *status_code* should be considered a broken link."""
  return status_code in _BROKEN_STATUS_CODES or status_code >= 400


def _crawl(
  start_url: str, max_pages: int = 10_000
) -> tuple[Dict[str, Set[str]], Set[str]]:
  """Recursively crawls a site starting from *start_url*."""
  to_visit: Deque[str] = deque([_normalize(start_url)])
  visited: Set[str] = set()
  broken: Dict[str, Set[str]] = collections.defaultdict(set)
  base_netloc = urlparse(start_url).netloc

  with tqdm(total=max_pages, desc="Pages crawled") as progress:
    while to_visit and len(visited) < max_pages:
      current = to_visit.popleft()
      if current in visited:
        continue

      visited.add(current)
      progress.set_postfix(page=current)
      progress.update()

      try:
        response = requests.get(current, headers=HEADERS, timeout=_TIMEOUT)
      except requests.RequestException as exc:
        broken[f"{current} (NETWORK ERROR: {exc})"].add("(fetch failed)")
        continue

      if _is_broken(response.status_code):
        broken[f"{current} ({response.status_code})"].add("(direct visit)")
        continue

      for link in _extract_links(response.text, current):
        if not _is_internal(link, base_netloc):
          continue

        link = _normalize(link)
        if link not in visited:
          to_visit.append(link)

        # Validate with a quick HEAD request.
        try:
          head_resp = requests.head(
            link, headers=HEADERS, timeout=_TIMEOUT, allow_redirects=True
          )
          status = head_resp.status_code
        except requests.RequestException:
          status = 0

        if status == 0 or _is_broken(status):
          err = "NETWORK ERROR" if status == 0 else status
          broken[f"{link} ({err})"].add(current)

  return broken, visited


def _build_tree(urls: Set[str], base_url: str) -> dict[str, dict]:
  """Converts a set of *urls* into a nested directory‑style mapping."""
  root: dict[str, dict] = {}
  base = urlparse(base_url)
  base_prefix = f"{base.scheme}://{base.netloc}"

  for url in urls:
    path = url[len(base_prefix) :] if url.startswith(base_prefix) else url
    parts = path.strip("/").split("/") if path.strip("/") else [""]

    node = root
    for part in parts:
      node = node.setdefault(part, {})

  return root


def _print_tree(node: dict[str, dict], prefix: str = "") -> None:
  """Pretty‑prints *node* (produced by `_build_tree`) to stdout."""
  entries = sorted(node.keys())
  for idx, name in enumerate(entries):
    connector = "└── " if idx == len(entries) - 1 else "├── "
    print(prefix + connector + ("/" if name == "" else name))
    extension = "    " if idx == len(entries) - 1 else "│   "
    _print_tree(node[name], prefix + extension)


def _parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
  """Parses command‑line arguments."""
  parser = argparse.ArgumentParser(
    description=("Crawl a website, list broken links, and output a directory tree.")
  )
  parser.add_argument("url", help="Starting URL (e.g. https://example.com)")
  parser.add_argument(
    "--max-pages",
    type=int,
    default=10_000,
    help="Maximum pages to visit (default 10 000).",
  )
  return parser.parse_args(argv)


def main(argv: Iterable[str] | None = None) -> None:
  """Program entry point."""
  args = _parse_args(argv)

  broken, visited = _crawl(args.url, args.max_pages)

  print("\n=== Directory tree of visited pages ===")
  _print_tree(_build_tree(visited, args.url))

  if broken:
    print("\n=== Broken links/pages ===")
    for target, sources in broken.items():
      print(f"🔗 {target}")
      for src in sorted(sources):
        print(f"   └── linked from: {src}")
  else:
    print("\nNo broken pages found.")


if __name__ == "__main__":
  main(sys.argv[1:])
