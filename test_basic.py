"""Tes dasar determinisme, hitungan teks, dan kesetaraan hasil paralel."""

import hashlib
from pathlib import Path
import tempfile

from analyzer import analyze_text
from generate_data import generate_files
from hybrid import analyze_files_hybrid
from sequential import analyze_files_sequential


def file_hashes(folder: Path) -> list[str]:
    """Menghitung hash SHA-256 file secara berurutan berdasarkan nama."""
    return [hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted(folder.glob("file_*.txt"))]


def test_generator_and_analyzers() -> None:
    """Memastikan generator deterministik dan semua mode analisis setara."""
    sample = analyze_text("Hello, World 123 !!")
    assert sample["vowels"] == 3
    assert sample["words"] == 2
    assert sample["numbers"] == 1
    assert sample["symbols"] == 3
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        first_folder = root / "first"
        second_folder = root / "second"
        generate_files(20, str(first_folder))
        generate_files(20, str(second_folder))
        assert file_hashes(first_folder) == file_hashes(second_folder)
        files = sorted(first_folder.glob("file_*.txt"))
        sequential_result = analyze_files_sequential(files)
        hybrid_2_result = analyze_files_hybrid(files, threads=2, procs=2)[0]
        hybrid_3_result = analyze_files_hybrid(files, threads=3, procs=3)[0]
        assert sequential_result == hybrid_2_result == hybrid_3_result


if __name__ == "__main__":
    test_generator_and_analyzers()
    print("SEMUA TES LULUS")
