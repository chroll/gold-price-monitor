import pytz
from datetime import datetime
import re
import os  # Tambahkan ini

INDONESIA_TZ = pytz.timezone('Asia/Jakarta')

def extract_price(text):
    """Extract numeric price from text dengan format Indonesia (1.234.567)"""
    try:
        if not text or text == '-':
            return None
            
        # Hapus 'Rp' dan spasi, lalu ambil hanya angka dan titik
        clean_text = text.replace('Rp', '').replace(' ', '')
        
        # Hapus semua titik (pemisah ribuan)
        clean_text = clean_text.replace('.', '')
        
        if clean_text and clean_text.isdigit():
            price = int(clean_text)
            # Validasi: harga emas harus reasonable
            if price > 100000 and price < 1000000000:  # Antara 100rb sampai 1M
                return price
            else:
                print(f"⚠️ Price out of range: {price}")
        else:
            print(f"⚠️ Invalid price format: '{text}' -> '{clean_text}'")
    except Exception as e:
        print(f"⚠️ Error extracting price from '{text}': {e}")
    return None

def get_current_timestamp():
    """Get current timestamp in WIB timezone"""
    now_wib = datetime.now(INDONESIA_TZ)
    today_date = now_wib.strftime("%Y-%m-%d")
    current_time_str = now_wib.strftime("%H:%M:%S")
    return today_date, current_time_str, now_wib

def format_display_date(tanggal, jam):
    """Format date for display in chart"""
    try:
        dt = datetime.strptime(f"{tanggal} {jam}", "%Y-%m-%d %H:%M:%S")
        return dt.strftime("%d %b %H:%M")
    except:
        return f"{tanggal} {jam}"