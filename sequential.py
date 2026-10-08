"""Baseline sekuensial dengan fungsi analisis yang sama."""

from pathlib import Path

from analyzer import analyze_text, empty_totals, finalize_totals, merge_result
from config import DATA_DIR


def analyze_files_sequential(files: list[Path]) -> dict:
    """Membaca dan menganalisis setiap file secara berurutan."""
    totals, counts = empty_totals()
    for path in files:
        result = analyze_text(path.read_text(encoding="utf-8"))
        merge_result(totals, counts, result)
    return finalize_totals(totals, counts)


def main() -> None:
    """Menjalankan baseline untuk file yang ada di direktori data."""
    files = sorted(Path(DATA_DIR).glob("*.txt"))
    result = analyze_files_sequential(files)
    print(f"File dianalisis: {len(files)} | Total kata: {result['words']}")


if __name__ == "__main__":
    main()
