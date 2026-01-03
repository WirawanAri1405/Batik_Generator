import os
import glob
import subprocess
import base64
import shutil
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# --- KONFIGURASI ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR_PATH = os.path.join(BASE_DIR, "models")
OUTPUT_BASE_DIR = os.path.join(BASE_DIR, "static", "generated")
IMAGE_SIZE = 256

os.makedirs(OUTPUT_BASE_DIR, exist_ok=True)

MODEL_NAME_MAP = {
    'batik kawung': 'batik_kawung',    
    'batik parang': 'batik_parang', 
    'batik megamendung': 'batik_megamendung',
    'batik campur': 'train'
}

def clean_output_folder():
    """Hapus folder generated lama agar bersih"""
    if os.path.exists(OUTPUT_BASE_DIR):
        shutil.rmtree(OUTPUT_BASE_DIR)
    os.makedirs(OUTPUT_BASE_DIR)

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

    clean_output_folder()
    
    print(f"[GENERATE] Menjalankan CLI untuk: {model_folder_name} ({count} tiles)...")

    cmd = [
        "lightweight_gan",
        "--name", model_folder_name,
        "--models_dir", MODELS_DIR_PATH,
        "--image-size", str(IMAGE_SIZE),
        "--generate",
        "--generate-types", "ema",
        "--num-image-tiles", str(count),
        "--results_dir", OUTPUT_BASE_DIR
    ]

    try:
        subprocess.run(cmd, check=True, shell=True)
        
        # Cari file gambar (jpg/png)
        search_pattern_jpg = os.path.join(OUTPUT_BASE_DIR, "**", "*.jpg")
        search_pattern_png = os.path.join(OUTPUT_BASE_DIR, "**", "*.png")
        
        all_files = glob.glob(search_pattern_jpg, recursive=True) + \
                    glob.glob(search_pattern_png, recursive=True)

        if not all_files:
            return jsonify({'status': 'error', 'message': 'CLI sukses, tapi file gambar tidak ditemukan.'}), 500

        all_files.sort(key=os.path.getmtime, reverse=True)
        target_files = all_files[:count]
        
        results = []
        for i, file_path in enumerate(target_files):
            try:
                with open(file_path, "rb") as image_file:
                    b64_string = base64.b64encode(image_file.read()).decode('utf-8')
                    results.append({
                        'id': i,
                        'image': f"data:image/jpeg;base64,{b64_string}",
                        'type': 'image'
                    })
            except Exception as e:
                print(f"Gagal membaca file {file_path}: {e}")

        return jsonify({'status': 'success', 'data': results, 'mode': 'static'})

    except subprocess.CalledProcessError as e:
        print(f"❌ CLI Error: {e}")
        return jsonify({'status': 'error', 'message': 'Gagal menjalankan lightweight-gan.'}), 500
    except Exception as e:
        print(f"❌ System Error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

# --- FITUR BARU: INTERPOLATION ---
@app.route('/api/interpolate', methods=['POST'])
def interpolate():
    data = request.json
    dropdown_label = data.get('model', 'Klasik Solo')
    
    model_folder_name = MODEL_NAME_MAP.get(dropdown_label)
    full_model_path = os.path.join(MODELS_DIR_PATH, model_folder_name)
    
    if not os.path.exists(full_model_path):
        return jsonify({'status': 'error', 'message': f'Model {model_folder_name} tidak ditemukan.'}), 404

    clean_output_folder()
    
    print(f"[INTERPOLATION] Menjalankan CLI untuk: {model_folder_name}...")

    # Command khusus interpolasi
    cmd = [
        "lightweight_gan",
        "--name", model_folder_name,
        "--models_dir", MODELS_DIR_PATH,
        "--image-size", str(IMAGE_SIZE),
        "--generate-interpolation", # Flag utama
        "--results_dir", OUTPUT_BASE_DIR,
        "--num-image-tiles",str(1),
        "--interpolation-num-steps",str(300)
    ]

    try:
        subprocess.run(cmd, check=True, shell=True)
        
        # Cari file GIF hasil interpolasi
        search_pattern_gif = os.path.join(OUTPUT_BASE_DIR, "**", "*.gif")
        gif_files = glob.glob(search_pattern_gif, recursive=True)

        if not gif_files:
            return jsonify({'status': 'error', 'message': 'CLI sukses, tapi file GIF interpolasi tidak ditemukan.'}), 500

        # Ambil file GIF terbaru
        target_file = max(gif_files, key=os.path.getmtime)
        
        try:
            with open(target_file, "rb") as image_file:
                b64_string = base64.b64encode(image_file.read()).decode('utf-8')
                result = {
                    'image': f"data:image/gif;base64,{b64_string}",
                    'label': 'Interpolation Result',
                    'type': 'gif'
                }
        except Exception as e:
            return jsonify({'status': 'error', 'message': f"Gagal membaca file GIF: {e}"}), 500

        # Mengembalikan array data berisi 1 item (GIF)
        return jsonify({'status': 'success', 'data': [result], 'mode': 'interpolation'})

    except subprocess.CalledProcessError as e:
        print(f"❌ CLI Error: {e}")
        return jsonify({'status': 'error', 'message': 'Gagal menjalankan lightweight-gan interpolation.'}), 500
    except Exception as e:
        print(f"❌ System Error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)