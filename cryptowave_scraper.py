"""
Scraper untuk cryptowave.co.id
Mengambil: judul, kategori, tanggal, URL artikel, dan gambar headline
"""

import requests
from bs4 import BeautifulSoup
import csv
import time
import json
from datetime import datetime

BASE_URL = "https://cryptowave.co.id"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}
 
def get_page(url: str) -> BeautifulSoup | None:
    """Fetch halaman dan return BeautifulSoup object."""
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return BeautifulSoup(response.text, "html.parser")
    except requests.RequestException as e:
        print(f"[ERROR] Gagal fetch {url}: {e}")
        return None


def parse_articles(soup: BeautifulSoup) -> list[dict]:
    """
    Parse daftar artikel dari halaman listing.
    Struktur HTML: setiap artikel ada dalam tag <a> yang membungkus gambar,
    diikuti kategori dan judul.
    """
    articles = []

    # Cari semua card artikel — pola: img + kategori + judul + tanggal
    # Berdasarkan hasil fetch, strukturnya: <a href="/articles/..."> > <img>
    # diikuti tag kategori dan judul dalam teks
    cards = soup.select("a[href*='/articles/']")

    seen_urls = set()
    for card in cards:
        href = card.get("href", "")
        if not href or href in seen_urls:
            continue
        seen_urls.add(href)

        full_url = BASE_URL + href if href.startswith("/") else href

        # Ambil gambar headline
        img = card.find("img")
        img_url = img.get("src", "") if img else ""

        # Cari judul — biasanya alt text gambar atau teks terdekat
        title = img.get("alt", "").strip() if img else ""

        # Cari parent container untuk kategori & tanggal
        parent = card.find_parent()
        category = "-"
        date_str = datetime.now().strftime("%Y-%m-%d")  # default ke tanggal sekarang jika tidak ditemukan

        if parent:
            text_content = parent.get_text(separator="|", strip=True)
            parts = [p.strip() for p in text_content.split("|") if p.strip()]

            for part in parts:
                # Deteksi tanggal (format: "June 15, 2026")
                if any(
                    month in part
                    for month in [
                        "January", "February", "March", "April", "May", "June",
                        "July", "August", "September", "October", "November", "December"
                    ]
                ):
                    date_str = part
                # Deteksi kategori (bukan judul panjang, bukan tanggal)
                elif len(part) < 40 and part not in title and "WITA" not in part:
                    if not category:
                        category = part

        if title:
            articles.append({
                "title": title,
                "category": category,
                "date": date_str,
                "url": full_url,
                "image_url": img_url,
            })

    return articles


def scrape_article_content(url: str) -> dict:
    """Scrape isi lengkap satu artikel."""
    soup = get_page(url)
    if not soup:
        return {}

    content = {}

    # Judul artikel 
    h1 = soup.find("h1")
    content["title"] = h1.get_text(strip=True) if h1 else ""

    # Paragraf isi artikel
    paragraphs = soup.select("article p, .article-body p, main p")
    content["body"] = "\n\n".join(p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True))

    return content


def get_total_pages(soup: BeautifulSoup) -> int:
    """Ambil jumlah total halaman dari pagination."""
    last_link = soup.select_one("a[href*='?page=']")
    # Cari link 'Last »' untuk total halaman
    pagination_links = soup.select("a[href*='page=']")
    max_page = 1
    for link in pagination_links:
        href = link.get("href", "")
        if "page=" in href:
            try:
                page_num = int(href.split("page=")[-1])
                if page_num > max_page:
                    max_page = page_num
            except ValueError:
                pass
    return max_page


def scrape(
    max_pages: int = 5,
    category: str = "",
    save_csv: bool = True,
    save_json: bool = True,
    delay: float = 1.5,
) -> list[dict]:
    """
    Scrape daftar artikel dari cryptowave.co.id.

    Args:
        max_pages  : jumlah halaman yang di-scrape (default 5)
        category   : filter kategori, misal 'breaking-news', 'web3', dll.
                     Kosongkan untuk scrape semua.
        save_csv   : simpan hasil ke CSV
        save_json  : simpan hasil ke JSON
        delay      : jeda antar request (detik) agar tidak kena rate-limit

    Returns:
        List of dict berisi data artikel
    """
    all_articles = []

    if category:
        base = f"{BASE_URL}/category/{category}"
    else:
        base = BASE_URL

    for page in range(1, max_pages + 1):
        url = f"{base}?page={page}" if page > 1 else base
        print(f"[INFO] Scraping halaman {page}: {url}")

        soup = get_page(url)
        if not soup:
            break

        articles = parse_articles(soup)
        if not articles:
            print(f"[INFO] Tidak ada artikel di halaman {page}, berhenti.")
            break

        all_articles.extend(articles)
        print(f"  → {len(articles)} artikel ditemukan (total: {len(all_articles)})")

        time.sleep(delay)  # jeda sopan antar request

    # Deduplikasi berdasarkan URL
    seen = set()
    unique_articles = []
    for a in all_articles:
        if a["url"] not in seen:
            seen.add(a["url"])
            unique_articles.append(a)

    print(f"\n[DONE] Total unik: {len(unique_articles)} artikel")

    # Simpan hasil
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    if save_csv:
        filename = f"cryptowave_{timestamp}.csv"
        with open(filename, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["title", "category", "date", "url", "image_url"])
            writer.writeheader()
            writer.writerows(unique_articles)
        print(f"[SAVED] CSV → {filename}")

    if save_json:
        filename = f"cryptowave_{timestamp}.json"
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(unique_articles, f, ensure_ascii=False, indent=2)
        print(f"[SAVED] JSON → {filename}")

    return unique_articles


# ─── Contoh Penggunaan ───────────────────────────────────────────────────────

if __name__ == "__main__":

    # 1. Scrape 3 halaman pertama (semua kategori)
    results = scrape(max_pages=3)

    # 2. Scrape kategori tertentu saja, misal Breaking News
    # results = scrape(max_pages=2, category="breaking-news")

    # 3. Scrape + ambil isi artikel lengkap (lebih lambat)
    # results = scrape(max_pages=1)
    # for article in results[:5]:  # ambil 5 artikel pertama
    #     content = scrape_article_content(article["url"])
    #     article["body"] = content.get("body", "")
    #     time.sleep(1)

    # Preview hasil
    print("\n=== Preview 3 Artikel Pertama ===")
    for i, article in enumerate(results[:3], 1):
        print(f"\n{i}. {article['title']}")
        print(f"   Kategori : {article['category']}")
        print(f"   Tanggal  : {article['date']}")
        print(f"   URL      : {article['url']}")
