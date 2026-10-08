"""Analyzer paralel yang menggabungkan thread untuk I/O dan proses untuk CPU."""

import argparse
from concurrent.futures import FIRST_COMPLETED, ProcessPoolExecutor, ThreadPoolExecutor, wait
from pathlib import Path
import sys
import time

from analyzer import analyze_text, empty_totals, finalize_totals, merge_result
from config import DATA_DIR, DEFAULT_PROCS, DEFAULT_THREADS, NAMA, NIM
from sequential import analyze_files_sequential


def read_text(path: Path) -> tuple[str, float]:
    """Membaca satu file dan mengembalikan durasi bacanya."""
    started = time.perf_counter()
    text = path.read_text(encoding="utf-8")
    return text, time.perf_counter() - started


def analyze_timed(text: str) -> tuple[dict, float]:
    """Menganalisis teks dan mengembalikan durasi komputasinya."""
    started = time.perf_counter()
    result = analyze_text(text)
    return result, time.perf_counter() - started


def analyze_files_hybrid(files: list[Path], threads: int = DEFAULT_THREADS,
                         procs: int = DEFAULT_PROCS) -> tuple[dict, float, float, float]:
    """Menjalankan pipeline terbatas; wall time termasuk startup kedua pool."""
    if threads < 1 or procs < 1:
        raise ValueError("Threads dan processes harus minimal 1")
    started = time.perf_counter()
    totals, counts = empty_totals()
    read_total = 0.0
    computation_total = 0.0
    read_limit, process_limit = threads * 4, procs * 4
    paths = iter(files)
    with ThreadPoolExecutor(max_workers=threads) as reader_pool, ProcessPoolExecutor(max_workers=procs) as analyzer_pool:
        reading = set()
        analyzing = set()
        ready_texts: list[str] = []
        exhausted = False
        while reading or analyzing or ready_texts or not exhausted:
            while (len(reading) + len(analyzing) + len(ready_texts) < read_limit + process_limit
                   and not exhausted):
                try:
                    path = next(paths)
                except StopIteration:
                    exhausted = True
                    break
                reading.add(reader_pool.submit(read_text, path))
            while ready_texts and len(analyzing) < process_limit:
                analyzing.add(analyzer_pool.submit(analyze_timed, ready_texts.pop()))
            if not reading and not analyzing and not ready_texts:
                break
            completed, _ = wait(reading | analyzing, return_when=FIRST_COMPLETED)
            for future in completed:
                if future in reading:
                    reading.remove(future)
                    text, duration = future.result()
                    read_total += duration
                    ready_texts.append(text)
                else:
                    analyzing.remove(future)
                    result, duration = future.result()
                    computation_total += duration
                    merge_result(totals, counts, result)
    wall_time = time.perf_counter() - started
    return finalize_totals(totals, counts), wall_time, read_total, computation_total


def main() -> int:
    """Warm-up, membandingkan baseline dan hybrid, lalu mencetak ringkasan."""
    parser = argparse.ArgumentParser(description="Analisis file secara hybrid")
    parser.add_argument("--threads", type=int, default=DEFAULT_THREADS)
    parser.add_argument("--procs", type=int, default=DEFAULT_PROCS)
    parser.add_argument("--dir", default=DATA_DIR)
    parser.add_argument("--limit", type=int, help="Jumlah file pertama yang dianalisis")
    args = parser.parse_args()
    directory = Path(args.dir)
    if not directory.is_dir():
        print(f"Folder data tidak ditemukan: {directory}")
        return 1
    files = sorted(directory.glob("*.txt"))
    if args.limit is not None:
        if args.limit < 1:
            print("--limit harus bernilai minimal 1")
            return 1
        files = files[:args.limit]
    if not files:
        print(f"Tidak ada file .txt untuk dianalisis di: {directory}")
        return 1
    for path in files:
        path.read_bytes()
    baseline_started = time.perf_counter()
    sequential_result = analyze_files_sequential(files)
    baseline_time = time.perf_counter() - baseline_started
    hybrid_result, wall_time, read_total, computation_total = analyze_files_hybrid(
        files, args.threads, args.procs
    )
    fields = ("vowels", "words", "numbers", "symbols", "top_words")
    same_result = all(sequential_result[key] == hybrid_result[key] for key in fields)
    speedup = baseline_time / wall_time if wall_time else 0.0
    efficiency = speedup / args.procs * 100 if args.procs else 0.0
    print(f"Hybrid Project by: {NAMA} ({NIM})")
    print(f"Threads: {args.threads} | Processes: {args.procs} | Data: {len(files)}")
    print(f"Total Time: {wall_time:.2f} s | Speedup: {speedup:.2f} | Efficiency: {efficiency:.1f}%")
    print("Contoh hasil analisis:")
    print(f"Total kata: {hybrid_result['words']} | Vokal: {hybrid_result['vowels']} | Angka: {hybrid_result['numbers']} | Simbol: {hybrid_result['symbols']}")
    print("5 kata teratas: " + ", ".join(f"{word} ({count})" for word, count in hybrid_result["top_words"][:5]))
    print(f"Verifikasi hasil: {'SAMA' if same_result else 'BERBEDA'}")
    print(f"Detail: baca_total={read_total:.6f} s | komputasi_total={computation_total:.6f} s | wall={wall_time:.6f} s")
    return 0 if same_result else 1


if __name__ == "__main__":
    sys.exit(main())
