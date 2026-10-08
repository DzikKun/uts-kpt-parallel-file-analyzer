"""Menjalankan benchmark sekuensial dan hybrid dengan pencatatan yang dapat dilanjutkan."""

import argparse
import csv
from datetime import datetime
from pathlib import Path
import random
import time

from config import DATA_DIR, NAMA, NIM
from hybrid import analyze_files_hybrid
from sequential import analyze_files_sequential


CONFIGURATIONS = [
    (1, 3, 1, 2010), (2, 3, 2, 2010), (3, 3, 3, 2010),
    (4, 3, 4, 2010), (5, 3, 6, 2010), (6, 1, 3, 2010),
    (7, 6, 3, 2010), (8, 3, 3, 500), (9, 3, 3, 1000),
    (10, 6, 4, 2010),
]
RAW_FIELDS = ["urutan", "jenis", "nomor_konfigurasi", "thread", "proses", "data",
              "ulangan", "waktu", "baca_total", "komputasi_total", "jam_mulai"]
RESULT_FIELDS = ["No", "Thread", "Process", "Data", "Waktu", "Speedup", "Efisiensi"]
EXTENDED_FIELDS = RESULT_FIELDS + ["waktu_min", "waktu_max", "baseline_rata", "baseline_min",
                                   "baseline_max", "ms_komputasi_per_berkas", "baca_total_rata",
                                   "komputasi_total_rata", "utilisasi", "efisiensi_2core"]


def make_trials(repeats: int, scale: float) -> list[dict]:
    """Membentuk dan mengacak trial dengan seed yang konsisten dari NIM."""
    trials = []
    for number, threads, processes, size in CONFIGURATIONS:
        data_count = max(1, int(size * scale))
        for repetition in range(1, repeats + 1):
            trials.append({"jenis": "hybrid", "nomor_konfigurasi": number,
                           "thread": threads, "proses": processes,
                           "data": data_count, "ulangan": repetition})
    unique_sizes = sorted({trial["data"] for trial in trials})
    for data_count in unique_sizes:
        for repetition in range(1, repeats + 1):
            trials.append({"jenis": "baseline", "nomor_konfigurasi": "",
                           "thread": "", "proses": "", "data": data_count,
                           "ulangan": repetition})
    random.Random(int(NIM)).shuffle(trials)
    for order, trial in enumerate(trials, start=1):
        trial["urutan"] = order
    return trials


def trial_key(row: dict) -> tuple:
    """Membuat identitas unik trial untuk melewati pekerjaan yang sudah tersimpan."""
    return (row["jenis"], str(row["nomor_konfigurasi"]), str(row["data"]), str(row["ulangan"]))


def load_raw(path: Path) -> list[dict]:
    """Membaca semua rekaman CSV yang sudah ada untuk fitur resume."""
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8") as csv_file:
        return list(csv.DictReader(csv_file))


def write_trial(path: Path, row: dict) -> None:
    """Menambahkan satu hasil benchmark dan langsung memastikan data tersimpan."""
    needs_header = not path.exists() or path.stat().st_size == 0
    with path.open("a", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=RAW_FIELDS)
        if needs_header:
            writer.writeheader()
        writer.writerow(row)
        csv_file.flush()


def summarize(raw_rows: list[dict], trials: list[dict]) -> tuple[list[dict], list[dict]]:
    """Menghitung rata-rata, rentang waktu, speedup, dan metrik tambahan."""
    required = {trial_key(trial) for trial in trials}
    selected = [row for row in raw_rows if trial_key(row) in required]
    hybrid_rows = []
    extended_rows = []
    for number, threads, processes, _ in CONFIGURATIONS:
        data_count = next(trial["data"] for trial in trials
                          if trial["jenis"] == "hybrid" and trial["nomor_konfigurasi"] == number)
        matches = [row for row in selected if row["jenis"] == "hybrid"
                   and int(row["nomor_konfigurasi"]) == number and int(row["data"]) == data_count]
        baseline = [row for row in selected if row["jenis"] == "baseline" and int(row["data"]) == data_count]
        if not matches or not baseline:
            continue
        times = [float(row["waktu"]) for row in matches]
        baseline_times = [float(row["waktu"]) for row in baseline]
        average = sum(times) / len(times)
        baseline_average = sum(baseline_times) / len(baseline_times)
        speedup = baseline_average / average if average else 0.0
        read_average = sum(float(row["baca_total"]) for row in matches) / len(matches)
        computation_average = sum(float(row["komputasi_total"]) for row in matches) / len(matches)
        utilization = computation_average / (average * processes) if average and processes else 0.0
        standard = {"No": number, "Thread": threads, "Process": processes, "Data": data_count,
                    "Waktu": average, "Speedup": speedup,
                    "Efisiensi": speedup / processes * 100 if processes else 0.0}
        extended = dict(standard)
        extended.update({
            "waktu_min": min(times), "waktu_max": max(times),
            "baseline_rata": baseline_average, "baseline_min": min(baseline_times),
            "baseline_max": max(baseline_times),
            "ms_komputasi_per_berkas": computation_average / data_count * 1000,
            "baca_total_rata": read_average, "komputasi_total_rata": computation_average,
            "utilisasi": utilization,
            "efisiensi_2core": speedup / min(processes, 2) * 100,
        })
        hybrid_rows.append(standard)
        extended_rows.append(extended)
    return hybrid_rows, extended_rows


def save_csv(path: Path, fields: list[str], rows: list[dict]) -> None:
    """Menulis tabel CSV hasil akhir dengan kolom sesuai urutan yang ditentukan."""
    with path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    """Menjalankan trial, memverifikasi hasil, dan menghasilkan ringkasan CSV."""
    parser = argparse.ArgumentParser(description="Benchmark Parallel File Analyzer")
    parser.add_argument("--dir", default=DATA_DIR, help="Folder file .txt")
    parser.add_argument("--repeats", type=int, default=3, help="Ulangan setiap trial")
    parser.add_argument("--cooldown", type=float, default=20, help="Jeda antartrial dalam detik")
    parser.add_argument("--limit-scale", type=float, default=1.0, help="Pengali ukuran data")
    parser.add_argument("--out", default="bench", help="Awalan nama file keluaran")
    args = parser.parse_args()
    if args.repeats < 1 or args.cooldown < 0 or args.limit_scale <= 0:
        parser.error("repeats harus >= 1, cooldown >= 0, dan limit-scale > 0")
    directory = Path(args.dir)
    if not directory.is_dir():
        print(f"Folder data tidak ditemukan: {directory}")
        return 1
    all_files = sorted(directory.glob("*.txt"))
    if not all_files:
        print(f"Tidak ada file .txt di: {directory}")
        return 1
    trials = make_trials(args.repeats, args.limit_scale)
    max_count = max(trial["data"] for trial in trials)
    if len(all_files) < max_count:
        print(f"File tidak cukup: perlu {max_count}, tersedia {len(all_files)}")
        return 1
    for path in all_files:
        path.read_bytes()
    file_sets = {count: all_files[:count] for count in sorted({trial["data"] for trial in trials})}
    print("Urutan trial:")
    for trial in trials:
        label = (f"konfigurasi {trial['nomor_konfigurasi']}" if trial["jenis"] == "hybrid"
                 else "baseline")
        print(f"{trial['urutan']}: {trial['jenis']} {label}, data={trial['data']}, ulangan={trial['ulangan']}")
    expected = {count: analyze_files_sequential(files) for count, files in file_sets.items()}
    prefix = Path(args.out)
    prefix.parent.mkdir(parents=True, exist_ok=True)
    raw_path = Path(f"{prefix}_raw.csv")
    old_rows = load_raw(raw_path)
    old_completed = {trial_key(row) for row in old_rows}
    completed = set(old_completed)
    print(f"Hybrid Project by: {NAMA} ({NIM})")
    pending = [trial for trial in trials if trial_key(trial) not in completed]
    for trial_index, trial in enumerate(pending):
        started_at = datetime.now().astimezone().isoformat(timespec="seconds")
        if trial["jenis"] == "baseline":
            started = time.perf_counter()
            result = analyze_files_sequential(file_sets[trial["data"]])
            elapsed = time.perf_counter() - started
            read_total = ""
            computation_total = ""
        else:
            result, elapsed, read_total, computation_total = analyze_files_hybrid(
                file_sets[trial["data"]], trial["thread"], trial["proses"]
            )
            if result != expected[trial["data"]]:
                print(f"PERINGATAN: hasil BERBEDA pada konfigurasi {trial['nomor_konfigurasi']} ulangan {trial['ulangan']}")
                write_trial(raw_path, {**trial, "waktu": elapsed, "baca_total": read_total,
                                       "komputasi_total": computation_total, "jam_mulai": started_at})
                return 1
        row = {**trial, "waktu": elapsed, "baca_total": read_total,
               "komputasi_total": computation_total, "jam_mulai": started_at}
        write_trial(raw_path, row)
        completed.add(trial_key(trial))
        print(f"Selesai {trial['urutan']}/{len(trials)}: {trial['jenis']} data={trial['data']} "
              f"ulangan={trial['ulangan']} waktu={elapsed:.4f} s")
        if trial_index + 1 < len(pending):
            time.sleep(args.cooldown)
    for trial in trials:
        if trial_key(trial) in old_completed:
            print(f"Lewati trial selesai: urutan {trial['urutan']}")
    all_rows = load_raw(raw_path)
    extended_rows: list[dict] = []
    results, extended_rows = summarize(all_rows, trials)
    save_csv(Path(f"{prefix}_results.csv"), RESULT_FIELDS, results)
    save_csv(Path(f"{prefix}_extended.csv"), EXTENDED_FIELDS, extended_rows)
    print("\nNo | Thread | Process | Data | Waktu (s) | Speedup | Efisiensi")
    for row in results:
        print(f"{row['No']} | {row['Thread']} | {row['Process']} | {row['Data']} | "
              f"{row['Waktu']:.4f} | {row['Speedup']:.2f} | {row['Efisiensi']:.1f}%")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
