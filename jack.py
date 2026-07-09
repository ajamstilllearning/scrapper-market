"""
IDX (Bursa Efek Indonesia) Scraper
===================================
Menarik data "Trading Summary" (ringkasan perdagangan saham) dan
"Index Summary" (ringkasan indeks) dari www.idx.co.id, untuk:
    - hari ini (tanggal saat script dijalankan)
    - 3 hari kalender sebelumnya (hari libur bursa/weekend otomatis dilewati saat
      request, IDX akan mengembalikan data kosong untuk tanggal non-trading)

Output disimpan ke folder ./idx_data/ dalam format:
    - JSON per tanggal            : idx_data/json/stock_summary_YYYYMMDD.json
    - JSON per tanggal (index)    : idx_data/json/index_summary_YYYYMMDD.json
    - JSON gabungan semua tanggal : idx_data/idx_data_combined.json
    - CSV gabungan stock summary  : idx_data/stock_summary_combined.csv
    - CSV gabungan index summary  : idx_data/index_summary_combined.csv

CATATAN PENTING
----------------
1. www.idx.co.id dilindungi Cloudflare bot-protection. Kadang request
   biasa (requests) akan mendapat HTTP 403. Script ini:
     a. Mencoba dulu dengan `requests` + header menyerupai browser.
     b. Jika gagal / 403, otomatis fallback ke `cloudscraper` (bila terpasang)
        yang bisa menembus tantangan Cloudflare dasar.
   Install dependency fallback (opsional tapi disarankan):
       pip install cloudscraper

2. IDX HANYA memiliki data untuk hari bursa (Senin-Jumat, bukan libur
   nasional). Kalau tanggal yang diminta adalah weekend/libur, endpoint
   akan mengembalikan list kosong -- ini normal, bukan error.

3. Endpoint yang dipakai adalah endpoint internal (bukan API resmi
   berbayar IDX Data Services), jadi strukturnya bisa berubah sewaktu-waktu
   tanpa pemberitahuan. Gunakan secara wajar (rate-limit sendiri, jangan
   spam request) dan sesuai Terms of Service IDX.

4. Untuk data yang jauh lebih lengkap (profil emiten, laporan keuangan,
   corporate action, dll) IDX menyediakan endpoint terpisah-terpisah;
   silakan minta lagi kalau mau saya tambahkan modul untuk itu.
"""

import csv
import json
import os
import time
from datetime import datetime, timedelta

import requests

# ---------------------------------------------------------------------------
# Konfigurasi
# ---------------------------------------------------------------------------

BASE_URL = "https://www.idx.co.id"
STOCK_SUMMARY_ENDPOINT = f"{BASE_URL}/primary/TradingSummary/GetStockSummary"
INDEX_SUMMARY_ENDPOINT = f"{BASE_URL}/primary/TradingSummary/GetIndexSummary"

OUTPUT_DIR = "idx_data"
JSON_DIR = os.path.join(OUTPUT_DIR, "json")

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7",
    "Referer": f"{BASE_URL}/id/data-pasar/ringkasan-perdagangan/ringkasan-saham",
    "X-Requested-With": "XMLHttpRequest",
}

REQUEST_TIMEOUT = 20
RETRY_COUNT = 3
RETRY_DELAY_SEC = 3


# ---------------------------------------------------------------------------
# Utility: siapkan session (dengan fallback cloudscraper jika tersedia)
# ---------------------------------------------------------------------------

def build_session():
    """Coba pakai cloudscraper (lebih tahan Cloudflare). Kalau tidak ada,
    fallback ke requests.Session biasa."""
    try:
        import cloudscraper  
        session = cloudscraper.create_scraper(
            browser={"browser": "chrome", "platform": "windows", "mobile": False}
        )
        print("[info] Menggunakan cloudscraper untuk melewati proteksi Cloudflare.")
    except ImportError:
        session = requests.Session()
        print(
            "[warn] Modul 'cloudscraper' tidak ditemukan. Menggunakan requests biasa "
            "(kemungkinan bisa terblokir Cloudflare / HTTP 403). "
            "Install dengan: pip install cloudscraper"
        )
    session.headers.update(HEADERS)
    return session


# ---------------------------------------------------------------------------
# Utility: daftar tanggal (hari ini + 3 hari sebelumnya)
# ---------------------------------------------------------------------------

def get_target_dates(n_days_back=3):
    """Kembalikan list objek datetime: hari ini, lalu n_days_back hari
    sebelumnya (kalender, bukan hari bursa)."""
    today = datetime.now()
    return [today - timedelta(days=offset) for offset in range(0, n_days_back + 1)]


# ---------------------------------------------------------------------------
# Fetcher generik dengan retry
# ---------------------------------------------------------------------------

def fetch_json(session, url, params, label):
    for attempt in range(1, RETRY_COUNT + 1):
        try:
            resp = session.get(url, params=params, timeout=REQUEST_TIMEOUT)
            if resp.status_code == 200:
                try:
                    return resp.json()
                except ValueError:
                    print(f"[error] {label}: respons bukan JSON valid.")
                    return None
            else:
                print(
                    f"[warn] {label}: HTTP {resp.status_code} "
                    f"(percobaan {attempt}/{RETRY_COUNT})"
                )
        except requests.RequestException as exc:
            print(f"[warn] {label}: request error - {exc} (percobaan {attempt}/{RETRY_COUNT})")

        if attempt < RETRY_COUNT:
            time.sleep(RETRY_DELAY_SEC)

    print(f"[error] {label}: gagal setelah {RETRY_COUNT} percobaan.")
    return None


def fetch_stock_summary(session, date_obj):
    date_str = date_obj.strftime("%Y%m%d")
    params = {"length": 9999, "start": 0, "date": date_str}
    label = f"Stock Summary {date_str}"
    print(f"[fetch] {label} ...")
    data = fetch_json(session, STOCK_SUMMARY_ENDPOINT, params, label)
    return date_str, data


def fetch_index_summary(session, date_obj):
    date_str = date_obj.strftime("%Y%m%d")
    params = {"length": 9999, "start": 0, "date": date_str}
    label = f"Index Summary {date_str}"
    print(f"[fetch] {label} ...")
    data = fetch_json(session, INDEX_SUMMARY_ENDPOINT, params, label)
    return date_str, data


# ---------------------------------------------------------------------------
# Penyimpanan
# ---------------------------------------------------------------------------

def ensure_dirs():
    os.makedirs(JSON_DIR, exist_ok=True)


def save_json(obj, filename):
    path = os.path.join(JSON_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
    print(f"[save] {path}")


def save_combined_json(combined, filename="idx_data_combined.json"):
    path = os.path.join(OUTPUT_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(combined, f, ensure_ascii=False, indent=2)
    print(f"[save] {path}")


def extract_records(payload):
    """IDX biasanya membungkus list data dalam payload['data'].
    Fungsi ini mencoba beberapa kemungkinan struktur agar tetap robust."""
    if payload is None:
        return []
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        for key in ("data", "Data", "results", "Results"):
            if key in payload and isinstance(payload[key], list):
                return payload[key]
    return []


def save_combined_csv(all_records_by_date, filename):
    """all_records_by_date: dict {date_str: [record_dict, ...]}"""
    path = os.path.join(OUTPUT_DIR, filename)

    # Kumpulkan semua field unik supaya header CSV lengkap walau field
    # antar tanggal sedikit berbeda.
    fieldnames = ["scrape_date"]
    seen_fields = set(fieldnames)
    rows = []

    for date_str, records in all_records_by_date.items():
        for rec in records:
            row = {"scrape_date": date_str}
            row.update(rec)
            rows.append(row)
            for k in rec.keys():
                if k not in seen_fields:
                    seen_fields.add(k)
                    fieldnames.append(k)

    if not rows:
        print(f"[warn] Tidak ada data untuk ditulis ke {filename} (kemungkinan semua tanggal libur bursa / gagal fetch).")
        return

    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"[save] {path} ({len(rows)} baris)")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    ensure_dirs()
    session = build_session()

    target_dates = get_target_dates(n_days_back=3)  # hari ini + 3 hari sebelumnya
    print(f"[info] Tanggal target: {[d.strftime('%Y-%m-%d') for d in target_dates]}")

    combined = {
        "scraped_at": datetime.now().isoformat(),
        "source": BASE_URL,
        "stock_summary": {},
        "index_summary": {},
    }

    stock_records_by_date = {}
    index_records_by_date = {}

    for date_obj in target_dates:
        # --- Stock Summary ---
        date_str, stock_payload = fetch_stock_summary(session, date_obj)
        combined["stock_summary"][date_str] = stock_payload
        save_json(stock_payload, f"stock_summary_{date_str}.json")
        stock_records_by_date[date_str] = extract_records(stock_payload)

        time.sleep(1)  # sopan ke server, hindari rate-limit

        # --- Index Summary ---
        date_str, index_payload = fetch_index_summary(session, date_obj)
        combined["index_summary"][date_str] = index_payload
        save_json(index_payload, f"index_summary_{date_str}.json")
        index_records_by_date[date_str] = extract_records(index_payload)

        time.sleep(1)

    # Simpan gabungan
    save_combined_json(combined)
    save_combined_csv(stock_records_by_date, "stock_summary_combined.csv")
    save_combined_csv(index_records_by_date, "index_summary_combined.csv")

    # Ringkasan singkat ke layar (fokus data hari ini)
    today_str = target_dates[0].strftime("%Y%m%d")
    today_stock_count = len(stock_records_by_date.get(today_str, []))
    today_index_count = len(index_records_by_date.get(today_str, []))
    print("\n=== RINGKASAN ===")
    print(f"Tanggal hari ini      : {today_str}")
    print(f"Jumlah saham (hari ini): {today_stock_count}")
    print(f"Jumlah indeks (hari ini): {today_index_count}")
    print(f"Semua file tersimpan di folder: ./{OUTPUT_DIR}/")


if __name__ == "__main__":
    main()