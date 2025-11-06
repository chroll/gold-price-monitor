import pandas as pd
import os  # Tambahkan ini
from utils import format_display_date

class ChartGenerator:
    def __init__(self, data_manager):
        self.data_manager = data_manager
    
    def get_chart_data(self, berat='1'):
        """Mengambil data untuk chart dari file Excel"""
        excel_file = self.data_manager.get_excel_file(berat)
        
        if not os.path.exists(excel_file):
            print(f"❌ File Excel untuk {berat}g tidak ditemukan: {excel_file}")
            return self.create_empty_chart_data(berat, f'Data untuk {berat} gram belum tersedia.')
        
        try:
            df_history = self.data_manager.get_existing_data(berat)
            
            if df_history.empty:
                print(f"📭 File Excel untuk {berat}g kosong")
                return self.create_empty_chart_data(berat, f'Data untuk {berat} gram masih kosong.')
                
            print(f"📊 Data loaded for chart {berat}g: {len(df_history)} rows")
            
            # Pastikan kolom UBS ada
            if 'UBS_Jual' not in df_history.columns:
                df_history['UBS_Jual'] = None
                print("➕ Added missing UBS_Jual column")
            if 'UBS_Buyback' not in df_history.columns:
                df_history['UBS_Buyback'] = None
                print("➕ Added missing UBS_Buyback column")
            
            # Filter hanya data yang memiliki harga (tidak null)
            df_history = df_history.dropna(subset=['GALERI24_Jual', 'ANTAM_Jual', 'UBS_Jual'], how='all')
            
            if df_history.empty:
                print(f"📭 Tidak ada data valid untuk {berat}g")
                return self.create_empty_chart_data(berat, f'Data untuk {berat} gram tidak valid.')
            
            # FILTER: Hanya ambil data ketika harga berubah
            df_filtered = self.filter_changed_prices(df_history)
            print(f"📈 Filtered data (price changes only): {len(df_filtered)} rows")
            
            df_filtered['Tanggal'] = df_filtered['Tanggal'].astype(str)
            df_filtered['Jam'] = df_filtered['Jam'].astype(str)
            df_filtered['TanggalJam'] = df_filtered['Tanggal'] + ' ' + df_filtered['Jam']
            
            df_sorted = df_filtered.sort_values(by='TanggalJam', ascending=True)
            
            dates_display = []
            for index, row in df_sorted.iterrows():
                dates_display.append(format_display_date(row['Tanggal'], row['Jam']))
            
            # Pastikan tidak ada nilai NaN dalam data chart
            result = {
                'berat': berat,
                'dates': dates_display,
                'g24_jual': df_sorted['GALERI24_Jual'].fillna(0).tolist(),
                'antam_jual': df_sorted['ANTAM_Jual'].fillna(0).tolist(),
                'ubs_jual': df_sorted['UBS_Jual'].fillna(0).tolist(),
                'g24_buyback': df_sorted['GALERI24_Buyback'].fillna(0).tolist(),
                'antam_buyback': df_sorted['ANTAM_Buyback'].fillna(0).tolist(),
                'ubs_buyback': df_sorted['UBS_Buyback'].fillna(0).tolist(),
                'latest': df_history.iloc[-1].fillna(0).to_dict() if not df_history.empty else {},
                'isEmpty': False
            }
            
            print(f"✅ Chart data prepared untuk {berat}g: {len(result['dates'])} data points")
            return result
            
        except Exception as e:
            print(f"❌ Error membaca data Excel untuk {berat}g: {e}")
            import traceback
            traceback.print_exc()
            return self.create_empty_chart_data(berat, f'Error membaca data: {str(e)}')
    
    def filter_changed_prices(self, df):
        """Filter data hanya ketika harga berubah - INCLUDING UBS"""
        if len(df) <= 1:
            return df
        
        df_sorted = df.sort_values(by=['Tanggal', 'Jam']).reset_index(drop=True)
        filtered_indices = [0]  # Selalu sertakan data pertama
        
        for i in range(1, len(df_sorted)):
            current = df_sorted.iloc[i]
            previous = df_sorted.iloc[i-1]
            
            # Cek apakah ada perubahan harga (termasuk UBS)
            price_changed = (
                current['GALERI24_Jual'] != previous['GALERI24_Jual'] or
                current['GALERI24_Buyback'] != previous['GALERI24_Buyback'] or
                current['ANTAM_Jual'] != previous['ANTAM_Jual'] or
                current['ANTAM_Buyback'] != previous['ANTAM_Buyback'] or
                current['UBS_Jual'] != previous['UBS_Jual'] or
                current['UBS_Buyback'] != previous['UBS_Buyback']
            )
            
            if price_changed:
                filtered_indices.append(i)
        
        # Selalu sertakan data terakhir
        if len(df_sorted) - 1 not in filtered_indices:
            filtered_indices.append(len(df_sorted) - 1)
        
        return df_sorted.iloc[filtered_indices].reset_index(drop=True)
    
    def create_empty_chart_data(self, berat, error_message):
        """Membuat data chart kosong dengan pesan error"""
        return {
            'berat': berat,
            'dates': [],
            'g24_jual': [],
            'antam_jual': [],
            'ubs_jual': [],
            'g24_buyback': [],
            'antam_buyback': [],
            'ubs_buyback': [],
            'latest': {},
            'error': error_message,
            'isEmpty': True
        }