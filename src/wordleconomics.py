#!/usr/bin/env python3
"""wordleconomics.py

Ranks five‑letter Wordle opening guesses using three heuristics:

* Aggregate   – probability that each letter appears in a word.
* Positional  – probability that each letter appears in each position.
* Hybrid      – weighted blend of aggregate and positional scores.

Typical usage example:

    $ python wordleconomics.py \
        --words ~/Downloads/words.txt --top 50 --blend 0.1
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Callable, Dict, Iterable, List, Mapping, Sequence, Tuple

import matplotlib.pyplot as plt
import numpy as np

# --------------------------------------------------------------------------- #
# Constants and type aliases
# --------------------------------------------------------------------------- #
DEFAULT_WORD_LIST: Path = Path("/usr/share/dict/words")
WORD_LENGTH: int = 5
DEFAULT_TOP_N: int = 100
DEFAULT_BLEND: float = 0.05  # 0 → aggregate only, 1 → positional only

ScoreFn = Callable[[str], float]


# --------------------------------------------------------------------------- #
# I/O helpers
# --------------------------------------------------------------------------- #
def _load_words(path: Path, length: int = WORD_LENGTH) -> List[str]:
  """Loads and returns sorted, unique words of the requested length.

  Args:
      path: File containing one candidate word per line.
      length: Required word length (default: 5).

  Returns:
      A lexicographically sorted list of candidate words.

  Raises:
      FileNotFoundError: If *path* does not exist.
  """
  words: set[str] = {
    w.strip().lower()
    for w in path.read_text().splitlines()
    if w.strip().isalpha() and len(w.strip()) == length
  }
  return sorted(words)


# --------------------------------------------------------------------------- #
# Aggregate statistics
# --------------------------------------------------------------------------- #
def _letter_frequencies(words: Iterable[str]) -> Counter[str]:
  """Counts how many words contain each letter (letter counted once per word)."""
  counter: Counter[str] = Counter()
  for word in words:
    counter.update(set(word))
  return counter


def _letter_probability_scores(
  freqs: Mapping[str, int], total: int
) -> Dict[str, float]:
  """Computes P(letter) for each letter.

  Args:
      freqs: Mapping letter → word‑count.
      total: Total number of words.

  Returns:
      Mapping letter → probability in range 0–1.

  Raises:
      ValueError: If *total* is not positive.
  """
  if total <= 0:
    raise ValueError("Total word count must be positive.")
  return {ch: count / total for ch, count in freqs.items()}


def _score_by_letters(word: str, letter_scores: Mapping[str, float]) -> float:
  """Sum of unique‑letter scores for *word*."""
  return sum(letter_scores[ch] for ch in set(word))


# --------------------------------------------------------------------------- #
# Positional statistics
# --------------------------------------------------------------------------- #
def _positional_frequencies(
  words: Iterable[str], length: int = WORD_LENGTH
) -> Dict[str, List[int]]:
  """Counts how often each letter appears in each index (0‑based)."""
  counts: Dict[str, List[int]] = defaultdict(lambda: [0] * length)
  for word in words:
    for idx, ch in enumerate(word):
      counts[ch][idx] += 1
  return counts


def _positional_probability_scores(
  freqs: Mapping[str, Sequence[int]], total: int
) -> Dict[str, List[float]]:
  """Normalizes positional counts to probabilities (0–1)."""
  if total <= 0:
    raise ValueError("Total word count must be positive.")
  return {ch: [cnt / total for cnt in positions] for ch, positions in freqs.items()}


def _score_by_position(word: str, pos_scores: Mapping[str, Sequence[float]]) -> float:
  """Sum P(letter | position) for each letter in *word*.

  Duplicate letters receive 0 to penalize repeats.
  """
  if len(set(word)) < len(word):
    return 0.0
  return sum(pos_scores[ch][idx] for idx, ch in enumerate(word))


# --------------------------------------------------------------------------- #
# Hybrid scorer
# --------------------------------------------------------------------------- #
def _make_hybrid_scorer(
  agg_scores: Mapping[str, float],
  pos_scores: Mapping[str, Sequence[float]],
  words: Iterable[str],
  blend: float = DEFAULT_BLEND,
) -> ScoreFn:
  """Returns a function combining aggregate and positional heuristics.

  blended_score = (1‑blend) * (agg / agg_max) + blend * (pos / pos_max)

  Args:
      agg_scores: Aggregate letter probabilities.
      pos_scores: Positional letter probabilities.
      words: Iterable of candidate words (for normalization).
      blend: Weight of positional score [0, 1].

  Returns:
      A callable that maps a word to its blended score.

  Raises:
      ValueError: If *blend* is outside the range [0, 1].
  """
  if not 0.0 <= blend <= 1.0:
    raise ValueError("Blend factor must be between 0 and 1.")

  agg_max = max(_score_by_letters(w, agg_scores) for w in words) or 1.0
  pos_max = max(_score_by_position(w, pos_scores) for w in words) or 1.0

  def scorer(word: str) -> float:  # Nested for lexical closure.
    agg_norm = _score_by_letters(word, agg_scores) / agg_max
    pos_norm = _score_by_position(word, pos_scores) / pos_max
    return (1 - blend) * agg_norm + blend * pos_norm

  return scorer


# --------------------------------------------------------------------------- #
# Ranking helpers
# --------------------------------------------------------------------------- #
def _rank_words(words: Iterable[str], scoring_fn: ScoreFn) -> List[Tuple[str, float]]:
  """Returns (word, score) pairs sorted by descending score then alphabetically."""
  scored = ((w, scoring_fn(w)) for w in words)
  return sorted(scored, key=lambda x: (-x[1], x[0]))


def _print_leaderboard(
  title: str, ranking: List[Tuple[str, float]], top_n: int = DEFAULT_TOP_N
) -> None:
  """Pretty‑prints the top *top_n* words."""
  print(f"\n{title} (top {top_n}):")
  for word, score in ranking[:top_n]:
    print(f"  {word:<5} {score:6.5f}")


# --------------------------------------------------------------------------- #
# Plotting helpers
# --------------------------------------------------------------------------- #
def _plot_aggregate_counts(freqs: Counter[str]) -> None:
  """Displays a bar chart of aggregate letter frequencies."""
  letters, counts = zip(*sorted(freqs.items(), key=lambda x: x[1], reverse=True))
  plt.figure(figsize=(20, 8))
  plt.bar(letters, counts)
  plt.title("Aggregate Letter Frequency")
  plt.xlabel("Letter")
  plt.ylabel("Words containing letter")
  plt.tight_layout()
  plt.show()


def _plot_positional_heatmap(pos_counts: Mapping[str, Sequence[int]]) -> None:
  """Displays a heat‑map of positional letter counts."""
  alphabet = [chr(ord("a") + i) for i in range(26)]
  data = np.vstack([pos_counts.get(letter, [0] * WORD_LENGTH) for letter in alphabet])

  plt.figure(figsize=(16, 12))
  im = plt.imshow(data, aspect="auto", cmap="viridis")
  plt.colorbar(im, label="Count")
  plt.xticks(range(WORD_LENGTH), [f"Pos {i}" for i in range(WORD_LENGTH)])
  plt.yticks(range(26), alphabet)
  plt.title("Positional Letter Counts")
  plt.xlabel("Index")
  plt.ylabel("Letter")
  plt.tight_layout()
  plt.show()


# --------------------------------------------------------------------------- #
# CLI handling
# --------------------------------------------------------------------------- #
def _parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
  """Parses command‑line arguments."""
  parser = argparse.ArgumentParser(
    description="Rank Wordle opening guesses with various heuristics."
  )
  parser.add_argument(
    "--words",
    type=Path,
    default=DEFAULT_WORD_LIST,
    help=f"Path to word list (default: {DEFAULT_WORD_LIST})",
  )
  parser.add_argument(
    "--top",
    type=int,
    default=DEFAULT_TOP_N,
    help=f"Leaderboard size (default: {DEFAULT_TOP_N})",
  )
  parser.add_argument(
    "--blend",
    type=float,
    default=DEFAULT_BLEND,
    help=(
      "Blend factor for hybrid scorer "
      f"(0=aggregate, 1=positional; default {DEFAULT_BLEND})"
    ),
  )
  return parser.parse_args(argv)


# --------------------------------------------------------------------------- #
# Main entry point
# --------------------------------------------------------------------------- #
def main(argv: Iterable[str] | None = None) -> None:
  """Program entry point."""
  args = _parse_args(argv)

  words = _load_words(args.words)
  total = len(words)
  print(f"Loaded {total} words from {args.words}")

  # Aggregate ranking
  agg_freqs = _letter_frequencies(words)
  agg_scores = _letter_probability_scores(agg_freqs, total)
  agg_ranking = _rank_words(words, lambda w: _score_by_letters(w, agg_scores))
  _print_leaderboard("Aggregate Ranking", agg_ranking, args.top)

  # Positional ranking
  pos_freqs = _positional_frequencies(words)
  pos_scores = _positional_probability_scores(pos_freqs, total)
  pos_ranking = _rank_words(words, lambda w: _score_by_position(w, pos_scores))
  _print_leaderboard("Positional Ranking", pos_ranking, args.top)

  # Hybrid ranking
  hybrid_scorer = _make_hybrid_scorer(agg_scores, pos_scores, words, args.blend)
  hybrid_ranking = _rank_words(words, hybrid_scorer)
  _print_leaderboard(
    f"Hybrid Ranking (blend={args.blend:.2f})", hybrid_ranking, args.top
  )

  # Optional visualisations
  _plot_aggregate_counts(agg_freqs)
  _plot_positional_heatmap(pos_freqs)


if __name__ == "__main__":  # pragma: no cover
  main(sys.argv[1:])
