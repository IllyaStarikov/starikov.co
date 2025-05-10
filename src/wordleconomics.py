"""
wordleconomics

Rank opening guesses using aggregate, positional, or blended heuristics.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path
from typing import Callable, Dict, Iterable, List, Mapping, Sequence, Tuple

import matplotlib.pyplot as plt
import numpy as np

# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------

WORD_LIST_PATH: Path = Path("/Users/starikov/Downloads/words.txt")
WORD_LENGTH: int = 5
TOP_N: int = 100
HYBRID_BLEND: float = 0.05  # 0 = aggregate only, 1 = positional only

ScoreFn = Callable[[str], float]


# -----------------------------------------------------------------------------
# I/O
# -----------------------------------------------------------------------------


def load_words(path: Path = WORD_LIST_PATH, length: int = WORD_LENGTH) -> List[str]:
  """
  Load and return sorted unique words of the requested length.
  Filters non-alphabetic entries and normalizes to lowercase.
  """
  words = {
    word.strip().lower()
    for word in path.read_text().splitlines()
    if word.strip().isalpha() and len(word.strip()) == length
  }
  return sorted(words)


# -----------------------------------------------------------------------------
# Aggregate statistics
# -----------------------------------------------------------------------------


def letter_frequencies(words: Iterable[str]) -> Counter[str]:
  """
  Count in how many words each letter appears (unique per word).
  """
  counter: Counter[str] = Counter()
  for word in words:
    counter.update(set(word))
  return counter


def letter_probability_scores(freqs: Mapping[str, int], total: int) -> Dict[str, float]:
  """
  Compute P(letter) = fraction of words containing the letter.
  Range: 0–1.
  """
  if total <= 0:
    raise ValueError("Total word count must be positive")
  return {ch: count / total for ch, count in freqs.items()}


def score_by_letters(word: str, letter_scores: Mapping[str, float]) -> float:
  """
  Sum the scores of each unique letter in the word.
  """
  return sum(letter_scores[ch] for ch in set(word))


# -----------------------------------------------------------------------------
# Positional statistics
# -----------------------------------------------------------------------------


def positional_frequencies(
  words: Iterable[str], length: int = WORD_LENGTH
) -> Dict[str, List[int]]:
  """
  Count how often each letter appears in each index (0-based).
  """
  counts: Dict[str, List[int]] = defaultdict(lambda: [0] * length)
  for word in words:
    for idx, ch in enumerate(word):
      counts[ch][idx] += 1
  return counts


def positional_probability_scores(
  freqs: Mapping[str, Sequence[int]], total: int
) -> Dict[str, List[float]]:
  """
  Normalize positional counts to probabilities (0–1).
  """
  if total <= 0:
    raise ValueError("Total word count must be positive")
  return {ch: [cnt / total for cnt in pos_list] for ch, pos_list in freqs.items()}


def score_by_position(word: str, pos_scores: Mapping[str, Sequence[float]]) -> float:
  """
  Sum P(letter | position) for each letter in the word.
  Returns 0 if there are duplicate letters.
  """
  if len(set(word)) < len(word):
    return 0.0
  return sum(pos_scores[ch][idx] for idx, ch in enumerate(word))


# -----------------------------------------------------------------------------
# Hybrid scorer
# -----------------------------------------------------------------------------


def make_hybrid_scorer(
  agg_scores: Mapping[str, float],
  pos_scores: Mapping[str, Sequence[float]],
  words: Iterable[str],
  blend: float = HYBRID_BLEND,
) -> ScoreFn:
  """
  Return a function that blends aggregate and positional scores:
      blended = (1 - blend) * (agg / agg_max) + blend * (pos / pos_max)
  """
  if not 0.0 <= blend <= 1.0:
    raise ValueError("Blend factor must be between 0 and 1")

  # Precompute normalizers
  agg_max = max(score_by_letters(w, agg_scores) for w in words) or 1.0
  pos_max = max(score_by_position(w, pos_scores) for w in words) or 1.0

  def scorer(word: str) -> float:
    agg_norm = score_by_letters(word, agg_scores) / agg_max
    pos_norm = score_by_position(word, pos_scores) / pos_max
    return (1 - blend) * agg_norm + blend * pos_norm

  return scorer


# -----------------------------------------------------------------------------
# Ranking
# -----------------------------------------------------------------------------


def rank_words(words: Iterable[str], scoring_fn: ScoreFn) -> List[Tuple[str, float]]:
  """
  Return a list of (word, score), sorted by descending score then alphabetically.
  """
  scored = ((w, scoring_fn(w)) for w in words)
  return sorted(scored, key=lambda x: (-x[1], x[0]))


def print_leaderboard(
  title: str, ranking: List[Tuple[str, float]], top_n: int = TOP_N
) -> None:
  """
  Print the top N words and their scores.
  """
  print(f"\n{title} (top {top_n}):")
  for word, score in ranking[:top_n]:
    print(f"  {word:<5} {score:6.5f}")


# -----------------------------------------------------------------------------
# Plotting helpers
# -----------------------------------------------------------------------------


def plot_aggregate_counts(freqs: Counter[str]) -> None:
  """
  Bar chart of how many words contain each letter.
  """
  letters, counts = zip(*sorted(freqs.items(), key=lambda x: x[1], reverse=True))
  plt.figure(figsize=(20, 8))
  plt.bar(letters, counts)
  plt.title("Aggregate Letter Frequency")
  plt.xlabel("Letter")
  plt.ylabel("Number of Words")
  plt.tight_layout()
  plt.show()


def plot_positional_heatmap(pos_counts: Mapping[str, Sequence[int]]) -> None:
  """
  Heatmap of positional letter counts (26 rows × WORD_LENGTH columns).
  """
  alphabet = [chr(ord("a") + i) for i in range(26)]
  data = np.vstack([pos_counts.get(letter, [0] * WORD_LENGTH) for letter in alphabet])

  plt.figure(figsize=(16, 12))
  im = plt.imshow(data, aspect="auto", cmap="viridis")
  plt.colorbar(im, label="Count")
  plt.xticks(range(WORD_LENGTH), [f"Pos {i}" for i in range(WORD_LENGTH)])
  plt.yticks(range(26), alphabet)
  plt.title("Positional Letter Counts")
  plt.xlabel("Index (0-based)")
  plt.ylabel("Letter")
  plt.tight_layout()
  plt.show()


# -----------------------------------------------------------------------------
# Main entry point
# -----------------------------------------------------------------------------


def main() -> None:
  words = load_words()
  total = len(words)
  print(f"Loaded {total} words from {WORD_LIST_PATH!s}")

  # Aggregate ranking
  agg_freqs = letter_frequencies(words)
  agg_scores = letter_probability_scores(agg_freqs, total)
  agg_ranking = rank_words(words, lambda w: score_by_letters(w, agg_scores))
  print_leaderboard("Aggregate Ranking", agg_ranking)

  # Positional ranking
  pos_freqs = positional_frequencies(words)
  pos_scores = positional_probability_scores(pos_freqs, total)
  pos_ranking = rank_words(words, lambda w: score_by_position(w, pos_scores))
  print_leaderboard("Positional Ranking", pos_ranking)

  # Hybrid ranking
  hybrid = make_hybrid_scorer(agg_scores, pos_scores, words, HYBRID_BLEND)
  hybrid_ranking = rank_words(words, hybrid)
  print_leaderboard(f"Hybrid Ranking (blend={HYBRID_BLEND:.2f})", hybrid_ranking)

  # Optional: visualize distributions
  plot_aggregate_counts(agg_freqs)
  plot_positional_heatmap(pos_freqs)


if __name__ == "__main__":
  main()
