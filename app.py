import os
import glob
import subprocess
import base64
import shutil
import io
from flask import Flask, render_template, request, jsonify
from PIL import Image

app = Flask(__name__)

# --- KONFIGURASI ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR_PATH = os.path.join(BASE_DIR, "models")
OUTPUT_BASE_DIR = os.path.join(BASE_DIR, "static", "generated")
IMAGE_SIZE = 256

os.makedirs(OUTPUT_BASE_DIR, exist_ok=True)

MODEL_NAME_MAP = {
    'Klasik Solo': 'batik_kawung',    
    'Modern Abstrak': 'batik_parang', 
    'Floral Pesisir': 'batik_floral',
    'Geometris Parang': 'batik_geometris'
}

def clean_output_folder():
    """Hapus folder generated lama agar bersih"""
    if os.path.exists(OUTPUT_BASE_DIR):
        shutil.rmtree(OUTPUT_BASE_DIR)
    os.makedirs(OUTPUT_BASE_DIR)

# --- FUNGSI CROP DIHAPUS KARENA SUDAH TIDAK PERLU ---

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/generate', methods=['POST'])
def generate():
    data = request.json
    dropdown_label = data.get('model', 'Klasik Solo')
    count = int(data.get('count', 4))
    
    model_folder_name = MODEL_NAME_MAP.get(dropdown_label)
    
    full_model_path = os.path.join(MODELS_DIR_PATH, model_folder_name)
    if not os.path.exists(full_model_path):
        return jsonify({'status': 'error', 'message': f'Model {model_folder_name} tidak ditemukan.'}), 404

    # 1. Bersihkan output lama
    clean_output_folder()
    
    print(f"🚀 Menjalankan CLI untuk: {model_folder_name} ({count} tiles)...")

    # 2. Command CLI
    cmd = [
        "lightweight_gan",
        "--name", model_folder_name,
        "--models_dir", MODELS_DIR_PATH,
        "--image-size", str(IMAGE_SIZE),
        "--generate",
        "--generate-types", "ema",
        "--num-image-tiles", str(count), # Meminta sejumlah 'count' gambar
        "--results_dir", OUTPUT_BASE_DIR
    ]

    try:
        subprocess.run(cmd, check=True, shell=True)
        
        # 3. LOGIKA BARU: AMBIL BANYAK FILE
        # Cari semua file jpg/png
        search_pattern_jpg = os.path.join(OUTPUT_BASE_DIR, "**", "*.jpg")
        search_pattern_png = os.path.join(OUTPUT_BASE_DIR, "**", "*.png")
        
        all_files = glob.glob(search_pattern_jpg, recursive=True) + \
                    glob.glob(search_pattern_png, recursive=True)

        if not all_files:
            return jsonify({'status': 'error', 'message': 'CLI sukses, tapi file gambar tidak ditemukan.'}), 500

        # Urutkan berdasarkan waktu (Terbaru di paling atas)
        all_files.sort(key=os.path.getmtime, reverse=True)
        
        # Ambil sejumlah 'count' file teratas
        # (Misal minta 4, ambil 4 file terbaru)
        target_files = all_files[:count]
        
        print(f"✅ Ditemukan {len(target_files)} file gambar terbaru.")

        # 4. Convert ke Base64
        results = []
        for i, file_path in enumerate(target_files):
            try:
                with open(file_path, "rb") as image_file:
                    b64_string = base64.b64encode(image_file.read()).decode('utf-8')
                    results.append({
                        'id': i,
                        'image': f"data:image/jpeg;base64,{b64_string}",
                        'label': f"Gen #{i+1}"
                    })
            except Exception as e:
                print(f"Gagal membaca file {file_path}: {e}")

        return jsonify({'status': 'success', 'data': results})

    except subprocess.CalledProcessError as e:
        print(f"❌ CLI Error: {e}")
        return jsonify({'status': 'error', 'message': 'Gagal menjalankan lightweight-gan.'}), 500
    except Exception as e:
        print(f"❌ System Error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)