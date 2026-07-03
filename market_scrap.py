from bs4 import BeautifulSoup
import requests
from datetime import date, datetime

def scrap_bisnis_market():
    now = datetime.now()
    url = 'https://market.bisnis.com/'
    agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    response = requests.get(url, headers={'User-Agent': agent})
    response.raise_for_status()  # Pastikan request berhasil, jika tidak akan memunculkan error
    soup = BeautifulSoup(response.text, 'html.parser')   
    block = soup.find_all('h2', class_='artTitle')
    block2 = soup.find('div', class_='artWrap -col')
    block2_secure = block2.find_all('h4', class_='artTitle') if block2 else []
    latest_news  = []
    updated_news = soup.find_all("div", class_="col-7 col-left mt50")
    for i in updated_news:
        block_new = i.find_all("h4", class_="artTitle")
        block_new_date = i.find_all("div", class_="artDate")
        
            
    # link = ['https://market.bisnis.com/read/20260613/94/1980605/volatilitas-komoditas-tak-redam-transaksi-bursa-berjangka', 'https://market.bisnis.com/read/20260613/94/1980605/volatilitas-komoditas-tak-redam-transaksi-bursa-berjangka', 'https://market.bisnis.com/read/20260612/94/1980537/jfx-perluas-akses-investasi-derivatif-fasilitasi-perdagangan-emas-hingga-minyak', 'https://market.bisnis.com/read/20260612/7/1980450/ihsg-dibuka-naik-125-ke-5959-saham-dssa-tpia-hingga-bbca-melaju' ]
    # for j in link:
    #     pass

    filename = f"bisnis_market_{date.today().strftime('%Y%m%d')}.csv"
    with open(filename, "a", encoding="utf-8") as f:
        f.write(f"\nData diambil pada: {now.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("berita terbaru(range 24 jam):\n")
        for index, i in enumerate(block_new):
            try:
                f.write(f"- {i.text.strip()}\n")
                f.write(f"  real-time = {now.strftime('%H:%M:%S')}\n")
                    
                    # Validasi: Pastikan tanggal di indeks ini memang ada
                if index < len(block_new_date):
                    f.write(f"- {block_new_date[index].text.strip()}\n")
                else:
                        f.write("- Tanggal tidak ditemukan\n") # Solusi jika artDate absen
                    
                f.write("=========================================================\n")
            except Exception as e:
                print(f"Error pada data ke-{index}: {e}")
        f.write("populer:\n")
        for i in block2:
            f.write(f"-{i.text.strip()}\n")
        f.write("berita rekomendasi:\n")
        for i in block:
            f.write(f"-{i.text.strip()}\n",)    
            
    print("Done")
    print(filename)

if __name__ == "__main__":
    scrap_bisnis_market()
