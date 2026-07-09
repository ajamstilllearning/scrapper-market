📰 Indonesian Crypto & Market News Scraper

Kumpulan script Python untuk mengambil data berita dari dua sumber berita Indonesia:


cryptowave.co.id — berita kripto & Web3
market.bisnis.com — berita pasar keuangan & saham



📁 Struktur File

.
├── cryptowave_scraper.py   # Scraper untuk cryptowave.co.id
├── market_scrap.py         # Scraper untuk market.bisnis.com
|──jack.py                  # scraper untuk idx.co.id/id
└── README.md


⚙️ Requirements

bashpip install requests beautifulsoup4

Python 3.10+ direkomendasikan (menggunakan type hint modern seperti X | Y).


🚀 Deskripsi tambahan

1. cryptowave_scraper.py

Mengambil daftar artikel dari cryptowave.co.id beserta metadata-nya.

Data yang diambil:


Judul artikel
Kategori
Tanggal terbit
URL artikel
URL gambar headline


Jalankan langsung:

bashpython cryptowave_scraper.py

Atau gunakan sebagai modul:

pythonfrom cryptowave_scraper import scrape, scrape_article_content

# Scrape 3 halaman pertama (semua kategori)
results = scrape(max_pages=3)

# Scrape kategori tertentu saja
results = scrape(max_pages=2, category="breaking-news")

# Scrape + ambil isi artikel lengkap
results = scrape(max_pages=1)
for article in results[:5]:
    content = scrape_article_content(article["url"])
    article["body"] = content.get("body", "")

Parameter fungsi scrape():

ParameterDefaultKeteranganmax_pages5Jumlah halaman yang di-scrapecategory""Filter kategori (misal: "breaking-news", "web3")save_csvTrueSimpan hasil ke file CSVsave_jsonTrueSimpan hasil ke file JSONdelay1.5Jeda antar request (detik)

Output: File CSV dan JSON dengan nama cryptowave_YYYYMMDD_HHMMSS.csv/json


2. market_scrap.py

Mengambil berita terkini dari market.bisnis.com dan menyimpannya ke CSV harian.

Data yang diambil:


Berita terbaru (range 24 jam)
Berita populer
Berita rekomendasi


Jalankan:

bashpython market_scrap.py

Output: File CSV dengan nama bisnis_market_YYYYMMDD.csv — otomatis di-append jika file sudah ada (cocok untuk dijalankan terjadwal/cron job).


📄 Contoh Output

cryptowave (JSON)

json[
  {
    "title": "Bitcoin Tembus $100K di Tengah Sentimen Positif",
    "category": "Breaking News",
    "date": "June 28, 2026",
    "url": "https://cryptowave.co.id/articles/bitcoin-tembus-100k",
    "image_url": "https://cryptowave.co.id/images/btc.jpg"
  }
]

bisnis market (CSV)

Data diambil pada: 2026-06-30 08:00:00
berita terbaru(range 24 jam):
-IHSG Dibuka Naik 1,25% ke 5.959
real-time = 08:00:00
-30 Juni 2026
=========================...


📌 Catatan


Kedua scraper menggunakan User-Agent browser agar tidak diblokir.
cryptowave_scraper.py memiliki delay antar request untuk menghindari rate-limit.
market_scrap.py dirancang untuk dijalankan berkala (misal via cron atau Task Scheduler).
Pastikan koneksi internet stabil saat menjalankan scraper.

3. jack.py

### 📂 Penjelasan Struktur dan Output File

Seluruh data hasil ekstraksi akan otomatis disimpan dan diorganisir ke dalam folder `./idx_data/` dengan rincian sebagai berikut:

* **`idx_data/json/stock_summary_YYYYMMDD.json`**
  Berkas data mentah (*raw data*) hasil *scraping* ringkasan perdagangan saham harian yang dipisahkan per tanggal (format: TahunBulanHari).
* **`idx_data/json/index_summary_YYYYMMDD.json`**
  Berkas data mentah (*raw data*) ringkasan pergerakan indeks bursa harian yang dipisahkan per tanggal.
* **`idx_data/idx_data_combined.json`**
  Satu berkas JSON utama yang menggabungkan seluruh data kompilasi dari semua tanggal yang berhasil diambil (hari ini + 3 hari sebelumnya).
* **`idx_data/stock_summary_combined.csv`**
  Data gabungan ringkasan saham seluruh tanggal yang sudah dikonversi ke format tabular (CSV) agar mudah dianalisis menggunakan Excel, Google Sheets, atau Pandas.
* **`idx_data/index_summary_combined.csv`**
  Data gabungan ringkasan indeks seluruh tanggal yang sudah dikonversi ke format tabular (CSV) siap pakai.



📜 Lisensi

Proyek ini dibuat untuk keperluan personal/edukasi. Harap hormati robots.txt dan kebijakan penggunaan masing-masing situs.
