import pandas as pd
import os
import threading
import time  # Tambahkan ini
from utils import get_current_timestamp
from scraper import scrape_galeri24_data

# Constants
EXCEL_FILE_1G = 'Harga_Emas_1Gram.xlsx'
EXCEL_FILE_2G = 'Harga_Emas_2Gram.xlsx'
SHEET_NAME = 'Data_Harian'

# Lock untuk mencegah race condition
file_lock = threading.Lock()

class DataManager:
    def __init__(self):
        self.ensure_excel_structure()
    
    def get_excel_file(self, berat):
        """Get Excel file path based on weight"""
        return EXCEL_FILE_1G if berat == '1' else EXCEL_FILE_2G
    
    def ensure_excel_structure(self):
        """Memastikan file Excel memiliki struktur kolom yang benar termasuk UBS"""
        print("🔄 Ensuring Excel file structure...")
        
        for berat in ['1', '2']:
            excel_file = self.get_excel_file(berat)
            
            if os.path.exists(excel_file):
                try:
                    # Baca file
                    df = pd.read_excel(excel_file, sheet_name=SHEET_NAME)
                    
                    # Definisikan struktur kolom yang diharapkan
                    expected_columns = {
                        'Tanggal': 'object',
                        'Jam': 'object', 
                        'GALERI24_Jual': 'float64',
                        'GALERI24_Buyback': 'float64',
                        'ANTAM_Jual': 'float64',
                        'ANTAM_Buyback': 'float64',
                        'UBS_Jual': 'float64',
                        'UBS_Buyback': 'float64'
                    }
                    
                    needs_update = False
                    
                    # Tambahkan kolom yang missing
                    for col, dtype in expected_columns.items():
                        if col not in df.columns:
                            df[col] = None
                            needs_update = True
                            print(f"➕ Added missing column '{col}' to {berat}g file")
                    
                    # Konversi tipe data
                    for col, dtype in expected_columns.items():
                        if col in df.columns:
                            try:
                                df[col] = df[col].astype(dtype)
                            except:
                                # Jika konversi gagal, set ke None
                                df[col] = None
                    
                    if needs_update:
                        # Simpan kembali dengan struktur yang benar
                        df = df[list(expected_columns.keys())]
                        df.to_excel(excel_file, index=False, sheet_name=SHEET_NAME)
                        print(f"✅ Updated structure for {berat}g file")
                    else:
                        print(f"✅ Structure already correct for {berat}g file")
                    
                except Exception as e:
                    print(f"❌ Error checking structure for {berat}g: {e}")
                    # Buat file baru jika corrupt
                    self.create_new_excel_file(berat)
            else:
                # Buat file baru jika tidak ada
                self.create_new_excel_file(berat)
    
    def create_new_excel_file(self, berat):
        """Create new Excel file with proper structure"""
        try:
            expected_columns = ['Tanggal', 'Jam', 'GALERI24_Jual', 'GALERI24_Buyback', 
                              'ANTAM_Jual', 'ANTAM_Buyback', 'UBS_Jual', 'UBS_Buyback']
            df_new = pd.DataFrame(columns=expected_columns)
            excel_file = self.get_excel_file(berat)
            df_new.to_excel(excel_file, index=False, sheet_name=SHEET_NAME)
            print(f"🆕 Created new file for {berat}g")
        except Exception as e:
            print(f"❌ Failed to create new file for {berat}g: {e}")
    
    def get_gold_data(self, berat='1'):
        """Fungsi utama untuk mendapatkan data harga emas berdasarkan berat"""
        print(f"=== Getting COMPLETE gold data for {berat} gram ===")
        
        max_retries = 3
        best_data = None
        best_data_score = 0  # Score berdasarkan jumlah vendor yang berhasil
        
        for attempt in range(max_retries):
            try:
                print(f"🔄 Attempt {attempt + 1}/{max_retries} - Focus on getting UBS data")
                harga_emas_hari_ini = scrape_galeri24_data(berat)
                
                # Hitung score: 3 point jika semua vendor ada
                score = 0
                if harga_emas_hari_ini['GALERI 24']['Jual']: score += 1
                if harga_emas_hari_ini['ANTAM']['Jual']: score += 1
                if harga_emas_hari_ini['UBS']['Jual']: score += 1
                
                print(f"📊 Data score: {score}/3 (GALERI24: {bool(harga_emas_hari_ini['GALERI 24']['Jual'])}, ANTAM: {bool(harga_emas_hari_ini['ANTAM']['Jual'])}, UBS: {bool(harga_emas_hari_ini['UBS']['Jual'])})")
                
                # Jika dapat data lengkap, langsung break
                if score == 3:
                    print(f"🎉 PERFECT! Got complete data on attempt {attempt + 1}")
                    best_data = harga_emas_hari_ini
                    break
                
                # Simpan data terbaik yang didapat
                if score > best_data_score:
                    best_data_score = score
                    best_data = harga_emas_hari_ini
                    print(f"📈 New best data with score {score}")
                
                # Jika belum dapat data lengkap, tunggu dan coba lagi
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 3  # Tunggu lebih lama
                    print(f"⏳ Waiting {wait_time}s for next attempt...")
                    time.sleep(wait_time)
                    
            except Exception as e:
                print(f"❌ Attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 3
                    print(f"⏳ Waiting {wait_time}s before retry...")
                    time.sleep(wait_time)
        
        # Gunakan data terbaik yang berhasil dikumpulkan
        if best_data is None:
            best_data = {
                'GALERI 24': {'Jual': None, 'Buyback': None, 'error': 'All attempts failed'},
                'ANTAM': {'Jual': None, 'Buyback': None, 'error': 'All attempts failed'},
                'UBS': {'Jual': None, 'Buyback': None, 'error': 'All attempts failed'}
            }
        
        today_date, current_time_str, now_wib = get_current_timestamp()
        
        # Tambahkan timestamp
        best_data['timestamp'] = current_time_str
        best_data['berat'] = berat
        best_data['date'] = today_date
        
        print(f"🎯 Final data score: {best_data_score}/3")
        return today_date, current_time_str, now_wib, best_data
    
    def update_excel_data(self, berat='1'):
        """Mengambil data terbaru dan menyimpannya ke Excel HANYA JIKA SEMUA DATA LENGKAP"""
        # Gunakan lock untuk mencegah race condition
        with file_lock:
            try:
                excel_file = self.get_excel_file(berat)
                today_date, current_time_str, current_datetime, data = self.get_gold_data(berat)
                
                print(f"🔄 Processing data for {berat}g - {today_date} {current_time_str}")
                
                # Check jika data berhasil diambil - DENGAN VALIDASI KETAT
                g24_jual = data['GALERI 24']['Jual']
                g24_buyback = data['GALERI 24']['Buyback']
                antam_jual = data['ANTAM']['Jual']
                antam_buyback = data['ANTAM']['Buyback']
                ubs_jual = data['UBS']['Jual']
                ubs_buyback = data['UBS']['Buyback']
                
                print(f"📊 Data validation for {berat}g:")
                print(f"   GALERI24: Jual={g24_jual}, Buyback={g24_buyback}")
                print(f"   ANTAM: Jual={antam_jual}, Buyback={antam_buyback}")
                print(f"   UBS: Jual={ubs_jual}, Buyback={ubs_buyback}")
                
                # ✅ KRITERIA UNTUK MENYIMPAN: SEMUA VENDOR HARUS ADA HARGA JUALNYA
                all_vendors_have_data = all([
                    g24_jual is not None,
                    antam_jual is not None, 
                    ubs_jual is not None
                ])
                
                if not all_vendors_have_data:
                    missing_vendors = []
                    if g24_jual is None: missing_vendors.append("GALERI24")
                    if antam_jual is None: missing_vendors.append("ANTAM")
                    if ubs_jual is None: missing_vendors.append("UBS")
                    
                    print(f"🚫 SKIPPING SAVE: Data tidak lengkap. Missing: {', '.join(missing_vendors)}")
                    
                    # Return data lama jika ada, tanpa menyimpan data baru
                    return self.get_existing_data(berat)
                
                # ✅ JIKA SEMUA DATA LENGKAP, LANJUTKAN PENYIMPANAN
                print(f"✅ ALL DATA COMPLETE: Proceeding with save for {berat}g")
                
                df_old = self.get_existing_data(berat)
                
                print(f"💾 Saving COMPLETE data for {berat}g")
                
                # Buat DataFrame baru
                df_new_series = pd.DataFrame({
                    'Tanggal': [today_date],
                    'Jam': [current_time_str],
                    'GALERI24_Jual': [g24_jual],
                    'GALERI24_Buyback': [g24_buyback],
                    'ANTAM_Jual': [antam_jual],
                    'ANTAM_Buyback': [antam_buyback],
                    'UBS_Jual': [ubs_jual],
                    'UBS_Buyback': [ubs_buyback]
                })
                
                # Gabungkan dengan data lama
                if not df_old.empty:
                    df_combined = pd.concat([df_old, df_new_series], ignore_index=True)
                else:
                    df_combined = df_new_series
                
                # Pastikan urutan kolom
                column_order = ['Tanggal', 'Jam', 'GALERI24_Jual', 'GALERI24_Buyback', 
                              'ANTAM_Jual', 'ANTAM_Buyback', 'UBS_Jual', 'UBS_Buyback']
                df_combined = df_combined[column_order]
                
                try:
                    # Simpan ke Excel
                    df_combined.to_excel(excel_file, index=False, sheet_name=SHEET_NAME)
                    print(f"✅ Data lengkap berhasil disimpan ke {excel_file}")
                    print(f"📈 Total rows untuk {berat}g: {len(df_combined)}")
                    
                    # Verifikasi data yang disimpan
                    print(f"💾 VERIFIED SAVED DATA for {berat}g:")
                    print(f"   GALERI 24 Jual: Rp {g24_jual:,}")
                    print(f"   GALERI 24 Buyback: Rp {g24_buyback:,}")
                    print(f"   ANTAM Jual: Rp {antam_jual:,}")
                    print(f"   ANTAM Buyback: Rp {antam_buyback:,}")
                    print(f"   UBS Jual: Rp {ubs_jual:,}")
                    print(f"   UBS Buyback: Rp {ubs_buyback:,}")
                    
                except Exception as e:
                    print(f"❌ Error menyimpan ke Excel: {e}")
                
                return df_combined
                
            except Exception as e:
                print(f"❌ Error dalam update_excel_data untuk {berat}g: {e}")
                # Return data lama jika ada
                return self.get_existing_data(berat)
    
    def get_existing_data(self, berat='1'):
        """Hanya mengambil data existing dari Excel tanpa scraping baru"""
        excel_file = self.get_excel_file(berat)
        
        if not os.path.exists(excel_file):
            return pd.DataFrame()
        
        try:
            df = pd.read_excel(excel_file, sheet_name=SHEET_NAME, dtype={'Tanggal': str, 'Jam': str})
            print(f"📁 Using existing data with {len(df)} rows for {berat}g")
            return df
        except Exception as e:
            print(f"❌ Error reading existing data: {e}")
            return pd.DataFrame()
    
    def force_update_data(self, berat='1'):
        """Force update data tanpa pengecekan kelengkapan"""
        excel_file = self.get_excel_file(berat)
        today_date, current_time_str, current_datetime, data = self.get_gold_data(berat)
        
        df_old = self.get_existing_data(berat)
        
        df_new_series = pd.DataFrame({
            'Tanggal': [today_date],
            'Jam': [current_time_str],
            'GALERI24_Jual': [data['GALERI 24']['Jual']],
            'GALERI24_Buyback': [data['GALERI 24']['Buyback']],
            'ANTAM_Jual': [data['ANTAM']['Jual']],
            'ANTAM_Buyback': [data['ANTAM']['Buyback']],
            'UBS_Jual': [data['UBS']['Jual']],
            'UBS_Buyback': [data['UBS']['Buyback']]
        })
        
        df_combined = pd.concat([df_old, df_new_series], ignore_index=True)
        df_combined.to_excel(excel_file, index=False, sheet_name=SHEET_NAME)
        
        print(f"✅ Force updated data for {berat}g")
        return df_combined