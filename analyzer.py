"""Fungsi analisis teks yang dipakai baseline dan program hybrid."""

from collections import Counter
import re


def analyze_text(text: str) -> dict:
    """Menghitung vokal, kata, angka, simbol, dan frekuensi semua kata."""
    words = re.findall(r"[A-Za-z]+", text.lower())
    numbers = re.findall(r"\d+", text)
    symbol_count = sum(1 for char in text if not char.isalnum() and not char.isspace())
    vowel_count = sum(1 for char in text.lower() if char in "aiueo")
    return {
        "vowels": vowel_count,
        "words": len(words),
        "numbers": len(numbers),
        "symbols": symbol_count,
        "word_counts": Counter(words),
    }


def empty_totals() -> tuple[dict, Counter]:
    """Membuat agregat hitungan awal dan Counter kata kosong."""
    return ({"vowels": 0, "words": 0, "numbers": 0, "symbols": 0}, Counter())


def merge_result(totals: dict, counts: Counter, result: dict) -> None:
    """Menggabungkan hitungan satu file ke agregat bersama."""
    for key in totals:
        totals[key] += result[key]
    counts.update(result["word_counts"])


def finalize_totals(totals: dict, counts: Counter, top_n: int = 10) -> dict:
    """Mengembalikan agregat akhir dengan urutan kata yang deterministik."""
    finalized = dict(totals)
    finalized["top_words"] = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))[:top_n]
    return finalized
