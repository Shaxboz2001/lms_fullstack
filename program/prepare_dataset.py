import os
import random
import shutil
from glob import glob

# Sinflar
CLASSES = ["crazing", "inclusion", "patches", "pitted_surface", "rolled_in_scale", "scratches"]

def prepare_dataset(root="NEU-DET", output="dataset"):
    os.makedirs(f"{output}/images/train", exist_ok=True)
    os.makedirs(f"{output}/images/val", exist_ok=True)
    os.makedirs(f"{output}/labels/train", exist_ok=True)
    os.makedirs(f"{output}/labels/val", exist_ok=True)

    for cls in CLASSES:
        img_files = glob(os.path.join(root, cls, "*.jpg"))
        random.shuffle(img_files)

        split = int(0.8 * len(img_files))
        train_files, val_files = img_files[:split], img_files[split:]

        for files, split_name in [(train_files, "train"), (val_files, "val")]:
            for f in files:
                # Rasmni ko‘chirish
                shutil.copy(f, f"{output}/images/{split_name}/{os.path.basename(f)}")

                # Label fayli YOLO formatda bo‘lishi kerak
                label_path = f.replace(".jpg", ".txt")
                if os.path.exists(label_path):
                    shutil.copy(label_path, f"{output}/labels/{split_name}/{os.path.basename(label_path)}")

if __name__ == "__main__":
    prepare_dataset()
