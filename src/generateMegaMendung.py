# ===============================
# Cek GPU dan CUDA
# ===============================
import torch

def check_gpu():
    print("CUDA Available :", torch.cuda.is_available())
    if torch.cuda.is_available():
        print("GPU           :", torch.cuda.get_device_name(0))
        print("CUDA Version  :", torch.version.cuda)
    else:
        raise RuntimeError("CUDA tidak terdeteksi!")

check_gpu()


# ===============================
# Path Dataset (Single Folder)
# ===============================
from pathlib import Path

DATA_DIR = Path("../batik_train/batik-megamendung")
print("Dataset path exists:", DATA_DIR.exists())


# ===============================
# Preprocessing Dataset
# Resize + Cleaning (Single Class)
# ===============================
from PIL import Image

IMAGE_SIZE = 256
VALID_EXT = (".jpg", ".png", ".jpeg")

def preprocess_dataset(folder: Path):
    print("\n[INFO] Preprocessing Mega Mendung dataset...")
    count = 0

    for img_path in folder.iterdir():
        if img_path.suffix.lower() in VALID_EXT:
            try:
                img = Image.open(img_path).convert("RGB")
                img = img.resize((IMAGE_SIZE, IMAGE_SIZE))
                img.save(img_path)
                count += 1
            except Exception as e:
                print("Skip:", img_path, e)

    print(f"[INFO] Images processed: {count}")

preprocess_dataset(DATA_DIR)


# ===============================
# Validasi Dataset (Non-Conditional)
# ===============================
def validate_dataset(folder: Path):
    print("\n[INFO] Validating dataset (Single Class)...")

    imgs = [
        p for p in folder.iterdir()
        if p.suffix.lower() in VALID_EXT
    ]

    print("Dataset type : Single class (Mega Mendung)")
    print(f"Total images : {len(imgs)}")

validate_dataset(DATA_DIR)
