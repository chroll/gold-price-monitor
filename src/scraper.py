import requests
from bs4 import BeautifulSoup
import time
from utils import extract_price
import os  # Tambahkan ini

def scrape_galeri24_data(berat='1'):
    """Scrape data harga emas REAL dari website Galeri24 - OPTIMIZED VERSION"""
    try:
        url = "https://galeri24.co.id/harga-emas"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'id,en;q=0.9,en-US;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        
        print(f"🔍 Scraping data REAL untuk {berat} gram dari: {url}")
        
        # Gunakan session untuk koneksi yang lebih efisien
        session = requests.Session()
        session.headers.update(headers)
        
        # Timeout bertahap
        timeouts = [10, 15, 20]
        response = None
        
        for timeout in timeouts:
            try:
                response = session.get(url, timeout=timeout)
                response.raise_for_status()
                print(f"✅ Successfully connected with {timeout}s timeout")
                break
            except requests.exceptions.Timeout:
                print(f"⏰ Timeout {timeout}s, trying next...")
                continue
            except requests.exceptions.ConnectionError as e:
                print(f"🌐 Connection error: {e}")
                time.sleep(2)
                continue
        
        if response is None:
            raise Exception("All connection attempts failed")
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        harga_emas = {
            'GALERI 24': {'Jual': None, 'Buyback': None, 'error': None},
            'ANTAM': {'Jual': None, 'Buyback': None, 'error': None},
            'UBS': {'Jual': None, 'Buyback': None, 'error': None}
        }
        
        # Gunakan CSS selector yang lebih reliable
        containers = soup.select('div.grid.divide-neutral-200.border-neutral-200')
        print(f"📊 Found {len(containers)} price containers")
        
        found_vendors = []
        
        for container in containers:
            # Identifikasi vendor menggunakan CSS selector
            header = container.select_one('div.bg-primary-100')
            if not header:
                continue
                
            header_text = header.get_text(strip=True)
            vendor = None
            
            if header_text == 'Harga GALERI 24':
                vendor = 'GALERI 24'
            elif header_text == 'Harga ANTAM':
                vendor = 'ANTAM'
            elif header_text == 'Harga UBS':
                vendor = 'UBS'
            else:
                continue
                
            found_vendors.append(vendor)
            print(f"🏷️ Processing: {vendor}")
            
            # Process container untuk extract harga
            process_container(container, vendor, berat, harga_emas)
        
        print(f"📦 Vendors found: {found_vendors}")
        
        # Print summary hasil scraping
        print(f"\n📊 FINAL RESULTS SUMMARY for {berat}g:")
        for vendor in ['GALERI 24', 'ANTAM', 'UBS']:
            print(f"  {vendor}: Jual={harga_emas[vendor]['Jual']}, Buyback={harga_emas[vendor]['Buyback']}")
        
        # Check untuk error
        for vendor in ['GALERI 24', 'ANTAM', 'UBS']:
            errors = []
            if harga_emas[vendor]['Jual'] is None:
                errors.append(f"jual {berat}g")
            if harga_emas[vendor]['Buyback'] is None:
                errors.append(f"buyback {berat}g")
            
            if errors:
                harga_emas[vendor]['error'] = f"Data {', '.join(errors)} {vendor} tidak ditemukan"
        
        return harga_emas
        
    except Exception as e:
        error_msg = f"Error scraping: {str(e)}"
        print(f"❌ {error_msg}")
        return {
            'GALERI 24': {'Jual': None, 'Buyback': None, 'error': error_msg},
            'ANTAM': {'Jual': None, 'Buyback': None, 'error': error_msg},
            'UBS': {'Jual': None, 'Buyback': None, 'error': error_msg}
        }

def process_container(container, vendor, berat, harga_emas):
    """Process individual container to extract prices"""
    data_rows = container.select('div.grid.grid-cols-5.divide-x')
    print(f"   Found {len(data_rows)} data rows for {vendor}")
    
    for i, row in enumerate(data_rows):
        # Skip header row
        if row.select_one('div.bg-neutral-50'):
            print(f"   Skipping header row {i}")
            continue
            
        # Extract kolom
        cols = row.select('div')
        if len(cols) >= 3:
            row_berat = cols[0].get_text(strip=True)
            print(f"   Row {i}: berat='{row_berat}', jual='{cols[1].get_text(strip=True)}', buyback='{cols[2].get_text(strip=True)}'")
            
            # Jika ini berat yang kita cari (eksak)
            if row_berat == berat:
                harga_jual = cols[1].get_text(strip=True)
                harga_buyback = cols[2].get_text(strip=True)
                
                print(f"🎯 Found exact match {berat}g in {vendor}")
                
                jual_clean = extract_price(harga_jual)
                buyback_clean = extract_price(harga_buyback)
                
                if jual_clean and harga_emas[vendor]['Jual'] is None:
                    harga_emas[vendor]['Jual'] = jual_clean
                    print(f"✅ {vendor} Jual ({berat}g): Rp {jual_clean:,}")
                
                if buyback_clean and harga_emas[vendor]['Buyback'] is None:
                    harga_emas[vendor]['Buyback'] = buyback_clean
                    print(f"✅ {vendor} Buyback ({berat}g): Rp {buyback_clean:,}")
    
    # Jika tidak ditemukan dengan match eksak, coba cari dengan logika fuzzy
    if harga_emas[vendor]['Jual'] is None:
        print(f"❌ Tidak menemukan data eksak untuk {berat}g {vendor}, mencoba fuzzy matching...")
        for row in data_rows:
            if row.select_one('div.bg-neutral-50'):
                continue
                
            cols = row.select('div')
            if len(cols) >= 3:
                row_berat = cols[0].get_text(strip=True)
                
                # Fuzzy matching untuk berat
                berat_variations = [
                    berat,  # '2'
                    f"{berat} ",  # '2 '
                    f"{berat}g",  # '2g'
                    f"{berat} g",  # '2 g'
                    f"{berat} gram",  # '2 gram'
                ]
                
                if any(variation in row_berat for variation in berat_variations):
                    harga_jual = cols[1].get_text(strip=True)
                    harga_buyback = cols[2].get_text(strip=True)
                    
                    print(f"🎯 Found fuzzy match for {berat}g in {vendor}: '{row_berat}'")
                    
                    jual_clean = extract_price(harga_jual)
                    buyback_clean = extract_price(harga_buyback)
                    
                    if jual_clean and harga_emas[vendor]['Jual'] is None:
                        harga_emas[vendor]['Jual'] = jual_clean
                        print(f"✅ {vendor} Jual ({berat}g): Rp {jual_clean:,}")
                    
                    if buyback_clean and harga_emas[vendor]['Buyback'] is None:
                        harga_emas[vendor]['Buyback'] = buyback_clean
                        print(f"✅ {vendor} Buyback ({berat}g): Rp {buyback_clean:,}")