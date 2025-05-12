#!/usr/bin/env python3
"""opml_to_markdown.py

Converts an OPML file of RSS feeds into a “starter‑pack” Markdown document.

Typical usage example:

    $ python opml_to_markdown.py starter_feed.opml > starter_feed.md
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path
from typing import DefaultDict, Iterable, List, Tuple

# --------------------------------------------------------------------------- #
# Constants
# --------------------------------------------------------------------------- #
_DEFAULT_TITLE: str = "Your First RSS Starter Pack"


# --------------------------------------------------------------------------- #
# Private helpers
# --------------------------------------------------------------------------- #
def _collect_feeds(
  node: ET.Element,
  path: List[str],
  basket: DefaultDict[str, List[Tuple[str, str | None, str]]],
) -> None:
  """Recursively walks <outline> nodes, grouping feeds by category.

  Args:
      node: Current XML element to inspect.
      path: Folder stack representing the current outline path.
      basket: Mapping category → list of (title, homepage, rss_url).
  """
  if node.tag.lower() != "outline":
    return

  title = node.attrib.get("title") or node.attrib.get("text") or "Untitled"
  xml_url = node.attrib.get("xmlUrl")  # Present only on feed leaves.
  html_url = node.attrib.get("htmlUrl") or xml_url

  if xml_url:  # Leaf node – a single feed.
    category = path[-1] if path else "Misc"
    basket[category].append(
      (title.strip(), html_url.strip() if html_url else None, xml_url.strip())
    )
  else:  # Folder node – descend recursively.
    new_path = path + ([title.strip()] if title.strip() else [])
    for child in node:
      _collect_feeds(child, new_path, basket)


def _opml_to_markdown(opml_file: Path, doc_title: str | None = None) -> str:
  """Returns a Markdown string representing the OPML contents.

  Args:
      opml_file: Path to the source OPML file.
      doc_title: Optional override for the Markdown document title.

  Returns:
      Rendered Markdown text.

  Raises:
      ValueError: If the OPML is missing a <body> element.
      ET.ParseError: If the OPML XML cannot be parsed.
  """
  root = ET.parse(opml_file).getroot()
  body = root.find("body")
  if body is None:
    raise ValueError("OPML appears to be missing a <body> element.")

  feeds: DefaultDict[str, List[Tuple[str, str | None, str]]] = defaultdict(list)
  for outline in body.findall("outline"):
    _collect_feeds(outline, [], feeds)

  title = doc_title or _DEFAULT_TITLE
  lines: List[str] = [
    f"# {title}",
    "",
    (
      "_Import the accompanying **OPML** into any reader (NetNewsWire, "
      "Reeder, Feedly, etc.) to pull everything at once._"
    ),
    "",
  ]

  for category in sorted(feeds):
    lines.append(f"### {category}")
    for name, homepage, rss in sorted(feeds[category], key=lambda t: t[0].lower()):
      homepage_md = f"[{name}]({homepage})" if homepage else name
      lines.append(f"- **{homepage_md}** — <sub>[RSS]({rss})</sub>")
    lines.append("")  # Blank line between categories.

  lines.append("> _Generated automatically from the original OPML file._")
  return "\n".join(lines)


# --------------------------------------------------------------------------- #
# CLI handling
# --------------------------------------------------------------------------- #
def _parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
  """Parses command‑line arguments."""
  parser = argparse.ArgumentParser(
    description="Convert an OPML file of RSS feeds to Markdown."
  )
  parser.add_argument("opml_file", type=Path, help="Input OPML file.")
  parser.add_argument(
    "title",
    nargs="?",
    default=None,
    help="Optional override for the Markdown document title.",
  )
  return parser.parse_args(argv)


def main(argv: Iterable[str] | None = None) -> None:
  """Program entry point."""
  args = _parse_args(argv)
  markdown = _opml_to_markdown(args.opml_file, args.title)
  print(markdown)


if __name__ == "__main__":  # pragma: no cover
  main(sys.argv[1:])
