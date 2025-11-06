from flask import Flask, render_template, jsonify, request
from data_manager import DataManager
from chart_generator import ChartGenerator
import threading

app = Flask(__name__)

# Initialize managers
data_manager = DataManager()
chart_generator = ChartGenerator(data_manager)

# Global variable untuk menyimpan data terbaru semua berat
latest_data_cache = {
    '1': None,
    '2': None
}
cache_lock = threading.Lock()

def update_all_data():
    """Update data untuk semua berat secara bersamaan"""
    print("=== Updating data for all weights simultaneously ===")
    
    def update_weight(berat):
        try:
            print(f"🔄 Updating data for {berat}g...")
            df_history = data_manager.update_excel_data(berat)
            
            with cache_lock:
                latest_data_cache[berat] = df_history
                
            print(f"✅ Data updated for {berat}g")
        except Exception as e:
            print(f"❌ Error updating data for {berat}g: {e}")
    
    # Buat thread untuk setiap berat
    threads = []
    for berat in ['1', '2']:
        thread = threading.Thread(target=update_weight, args=(berat,))
        thread.start()
        threads.append(thread)
    
    # Tunggu semua thread selesai
    for thread in threads:
        thread.join()
    
    print("✅ All data updates completed")

# Update data saat startup
print("=== Starting Gold Price Monitor with Simultaneous Data Update ===")
update_all_data()

@app.route('/')
def home():
    print("=== Home Route Called ===")
    berat = request.args.get('berat', '1')
    
    # Gunakan data dari cache
    with cache_lock:
        df_history = latest_data_cache.get(berat)
    
    # Jika cache kosong, ambil data existing
    if df_history is None or df_history.empty:
        print(f"🔄 Cache empty for {berat}g, getting existing data")
        df_history = data_manager.get_existing_data(berat)
    
    chart_data = chart_generator.get_chart_data(berat)
    
    return render_template('index.html', 
                          dates=chart_data['dates'],
                          g24_jual=chart_data['g24_jual'],
                          antam_jual=chart_data['antam_jual'],
                          ubs_jual=chart_data['ubs_jual'],
                          g24_buyback=chart_data['g24_buyback'],
                          antam_buyback=chart_data['antam_buyback'],
                          ubs_buyback=chart_data['ubs_buyback'],
                          latest=chart_data['latest'],
                          current_berat=berat)

@app.route('/api/gold-data')
def api_gold_data():
    print("=== API Gold Data Called ===")
    berat = request.args.get('berat', '1')
    chart_data = chart_generator.get_chart_data(berat)
    if chart_data:
        return jsonify(chart_data)
    else:
        return jsonify({'error': 'Data tidak tersedia'}), 404

@app.route('/api/update-data')
def api_update_data():
    """API untuk update data berdasarkan berat - HANYA JIKA DATA LENGKAP"""
    berat = request.args.get('berat', '1')
    print(f"=== API Update Data Called for {berat}g ===")
    
    # Update data untuk berat tertentu
    df_history = data_manager.update_excel_data(berat)
    
    # Update cache
    with cache_lock:
        latest_data_cache[berat] = df_history
    
    # Jika tidak ada data baru yang disimpan, beri warning
    if df_history.empty or len(df_history) == 0:
        print("⚠️ No new data saved in API call")
    
    chart_data = chart_generator.get_chart_data(berat)
    if chart_data:
        return jsonify(chart_data)
    else:
        return jsonify({'error': 'Data tidak tersedia'}), 404

@app.route('/api/force-update')
def api_force_update():
    """API untuk force update data"""
    berat = request.args.get('berat', '1')
    print(f"=== API Force Update Called for {berat}g ===")
    
    try:
        # Force save tanpa pengecekan kelengkapan
        df_history = data_manager.force_update_data(berat)
        
        # Update cache
        with cache_lock:
            latest_data_cache[berat] = df_history
        
        print(f"✅ Force updated data for {berat}g")
        chart_data = chart_generator.get_chart_data(berat)
        return jsonify(chart_data)
        
    except Exception as e:
        print(f"❌ Error in force update: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/update-all')
def api_update_all():
    """API untuk update semua data sekaligus"""
    print("=== API Update All Called ===")
    
    try:
        update_all_data()
        return jsonify({'message': 'All data updated successfully'})
    except Exception as e:
        print(f"❌ Error updating all data: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("=== Starting Flask Application with REAL Data ===")
    app.run(debug=True, host='0.0.0.0', port=5000)