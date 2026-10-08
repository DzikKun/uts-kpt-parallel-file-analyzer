"""Membuat kumpulan file teks sintetis yang hasilnya dapat diulang."""

import argparse
import random
import re
import string
from pathlib import Path

from config import DATA_DIR, DEFAULT_FILES, NIM


def build_vocabulary(rng: random.Random, size: int = 5000) -> list[str]:
    """Menyusun kosakata kata sintetis unik dari generator acak yang diberikan."""
    words: set[str] = set()
    while len(words) < size:
        length = rng.randint(4, 12)
        words.add("".join(rng.choice(string.ascii_lowercase) for _ in range(length)))
    return sorted(words)


def generate_files(file_count: int = DEFAULT_FILES, output_dir: str = DATA_DIR) -> None:
    """Menulis file ASCII 100–300 KB dan membersihkan file sisa bernomor besar."""
    if file_count < 0:
        raise ValueError("Jumlah file tidak boleh negatif")
    # Random lokal setara random.seed(NIM), tetapi tidak mengubah state global.
    rng = random.Random(int(NIM))
    vocabulary = build_vocabulary(rng)
    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)
    symbols = "!@#$%^&*()-_=+[]{};:,.?/"
    for index in range(file_count):
        target_size = rng.randint(100 * 1024, 300 * 1024)
        chunks: list[str] = []
        current_size = 0
        while current_size < target_size:
            token_kind = rng.random()
            if token_kind < 0.78:
                token = rng.choice(vocabulary)
            elif token_kind < 0.91:
                token = str(rng.randint(0, 10**12))
            else:
                token = "".join(rng.choice(symbols) for _ in range(rng.randint(1, 5)))
            chunk = token + ("\n" if rng.random() < 0.08 else " ")
            chunks.append(chunk)
            current_size += len(chunk)
        content = "".join(chunks).encode("ascii")[:target_size]
        (destination / f"file_{index + 1:04d}.txt").write_bytes(content)
        if (index + 1) % 200 == 0:
            print(f"Progres: {index + 1}/{file_count} file")
    pattern = re.compile(r"^file_(\d+)\.txt$")
    for path in destination.glob("file_*.txt"):
        match = pattern.match(path.name)
        if match and int(match.group(1)) > file_count:
            path.unlink()
    print(f"Berhasil membuat {file_count} file di: {destination}")


def main() -> None:
    """Membaca opsi CLI dan menjalankan generator data."""
    parser = argparse.ArgumentParser(description="Buat data teks sintetis")
    parser.add_argument("--files", type=int, default=DEFAULT_FILES, help="Jumlah file")
    parser.add_argument("--dir", default=DATA_DIR, help="Direktori keluaran")
    args = parser.parse_args()
    generate_files(args.files, args.dir)


if __name__ == "__main__":
    main()
