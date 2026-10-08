"""Membuat grafik benchmark dengan label dan keterangan berbahasa Indonesia."""

import argparse
import csv
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def read_csv(path: Path) -> list[dict]:
    """Membaca berkas CSV menjadi daftar baris bernama kolom."""
    with path.open("r", newline="", encoding="utf-8") as csv_file:
        return list(csv.DictReader(csv_file))


def save_thread_plot(extended: list[dict], output_dir: Path) -> None:
    """Membuat grafik waktu berdasarkan thread dari CSV extended."""
    rows = sorted((row for row in extended if int(row["Process"]) == 3 and int(row["Data"]) == 2010),
                  key=lambda row: int(row["Thread"]))
    if not rows:
        print("Tidak ada data extended untuk grafik Waktu vs Jumlah Thread; grafik dilewati.")
        return
    x = [int(row["Thread"]) for row in rows]
    y = [float(row["Waktu"]) for row in rows]
    lower = [value - float(row["waktu_min"]) for value, row in zip(y, rows)]
    upper = [float(row["waktu_max"]) - value for value, row in zip(y, rows)]
    fig, axis = plt.subplots()
    axis.errorbar(x, y, yerr=[lower, upper], marker="o", capsize=5)
    axis.set(title="Waktu vs Jumlah Thread", xlabel="Jumlah thread", ylabel="Waktu (detik)")
    axis.grid(True, linestyle="--", alpha=0.5)
    fig.tight_layout()
    fig.savefig(output_dir / "waktu_vs_thread.png", dpi=150)
    plt.close(fig)


def save_process_plot(extended: list[dict], output_dir: Path) -> None:
    """Membuat grafik waktu berdasarkan proses dari CSV extended."""
    rows = sorted((row for row in extended if int(row["Thread"]) == 3 and int(row["Data"]) == 2010),
                  key=lambda row: int(row["Process"]))
    if not rows:
        print("Tidak ada data extended untuk grafik Waktu vs Jumlah Process; grafik dilewati.")
        return
    x = [int(row["Process"]) for row in rows]
    y = [float(row["Waktu"]) for row in rows]
    lower = [value - float(row["waktu_min"]) for value, row in zip(y, rows)]
    upper = [float(row["waktu_max"]) - value for value, row in zip(y, rows)]
    fig, axis = plt.subplots()
    axis.errorbar(x, y, yerr=[lower, upper], marker="o", capsize=5)
    axis.set(title="Waktu vs Jumlah Process", xlabel="Jumlah process", ylabel="Waktu (detik)")
    axis.grid(True, linestyle="--", alpha=0.5)
    fig.tight_layout()
    fig.savefig(output_dir / "waktu_vs_process.png", dpi=150)
    plt.close(fig)


def save_speedup_plot(results: list[dict], output_dir: Path) -> None:
    """Membuat grafik batang speedup untuk seluruh konfigurasi benchmark."""
    rows = sorted(results, key=lambda row: int(row["No"]))
    labels = [f"{row['Thread']}/{row['Process']}/{row['Data']}" for row in rows]
    values = [float(row["Speedup"]) for row in rows]
    fig, axis = plt.subplots(figsize=(12, 5))
    axis.bar(labels, values)
    axis.axhline(1, color="red", linestyle="--", label="Speedup = 1")
    axis.set(title="Speedup vs Konfigurasi", xlabel="No (T/P/D)", ylabel="Speedup")
    axis.grid(True, axis="y", linestyle="--", alpha=0.5)
    axis.legend()
    fig.tight_layout()
    fig.savefig(output_dir / "speedup_vs_konfigurasi.png", dpi=150)
    plt.close(fig)


def save_compute_plot(extended: list[dict], output_dir: Path) -> None:
    """Membuat grafik waktu komputasi rata-rata per berkas terhadap proses."""
    rows = sorted((row for row in extended if int(row["Thread"]) == 3 and int(row["Data"]) == 2010),
                  key=lambda row: int(row["Process"]))
    x = [int(row["Process"]) for row in rows]
    y = [float(row["ms_komputasi_per_berkas"]) for row in rows]
    fig, axis = plt.subplots()
    axis.plot(x, y, marker="o")
    axis.set(title="Komputasi Rata-rata per Berkas vs Process",
             xlabel="Jumlah process", ylabel="Milidetik per berkas")
    axis.grid(True, linestyle="--", alpha=0.5)
    fig.tight_layout()
    fig.savefig(output_dir / "komputasi_per_berkas_vs_process.png", dpi=150)
    plt.close(fig)


def main() -> None:
    """Membaca hasil benchmark dan menyimpan empat grafik PNG."""
    parser = argparse.ArgumentParser(description="Plot hasil Parallel File Analyzer")
    parser.add_argument("--results", default="bench_results.csv", help="CSV ringkasan benchmark")
    parser.add_argument("--extended", default="bench_extended.csv", help="CSV metrik tambahan")
    parser.add_argument("--out", default=".", help="Folder keluaran PNG")
    args = parser.parse_args()
    output_dir = Path(args.out)
    output_dir.mkdir(parents=True, exist_ok=True)
    results = read_csv(Path(args.results))
    extended = read_csv(Path(args.extended))
    save_thread_plot(extended, output_dir)
    save_process_plot(extended, output_dir)
    save_speedup_plot(results, output_dir)
    save_compute_plot(extended, output_dir)
    print(f"Pembuatan grafik selesai di: {output_dir}")


if __name__ == "__main__":
    main()
