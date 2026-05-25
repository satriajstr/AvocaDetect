import cv2
import os
from backend.machine.preprocessing import resize_image, to_grayscale, reduce_noise, segment_image

DATASET_DIR = "dataset"
OUTPUT_DIR  = os.path.join("output", "preprocessing")
CLASSES     = ["mentah", "setengah_matang", "matang", "terlalu_matang"]
IMG_EXTS    = (".jpg", ".jpeg", ".png", ".bmp")


def save(path, image):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    cv2.imwrite(path, image)


def preprocess_image(img_path):
    """
    Jalankan full pipeline preprocessing pada satu gambar.
    Return dict berisi setiap tahap hasil preprocessing.
    """
    image = cv2.imread(img_path)
    if image is None:
        raise ValueError(f"Gambar tidak bisa dibaca: {img_path}")

    resized    = resize_image(image)
    gray       = to_grayscale(resized)
    blurred    = reduce_noise(gray)
    mask, segmented = segment_image(blurred)

    return {
        "resized":    resized,
        "gray":       gray,
        "blurred":    blurred,
        "mask":       mask,
        "segmented":  segmented,
    }


def run_batch():
    total, errors = 0, 0

    for cls in CLASSES:
        input_dir  = os.path.join(DATASET_DIR, cls)
        output_dir = os.path.join(OUTPUT_DIR, cls)

        if not os.path.isdir(input_dir):
            print(f"[SKIP] Folder tidak ditemukan: {input_dir}")
            continue

        files = [f for f in os.listdir(input_dir) if f.lower().endswith(IMG_EXTS)]
        if not files:
            print(f"[SKIP] Tidak ada gambar di: {input_dir}")
            continue

        print(f"\n[INFO] Memproses kelas '{cls}' — {len(files)} gambar")

        for fname in files:
            img_path = os.path.join(input_dir, fname)
            name     = os.path.splitext(fname)[0]

            try:
                stages = preprocess_image(img_path)

                # Simpan setiap tahap ke subfolder masing-masing
                for stage, img in stages.items():
                    out_path = os.path.join(output_dir, stage, f"{name}.jpg")
                    save(out_path, img)

                total += 1
                print(f"  [OK] {fname}")

            except Exception as e:
                errors += 1
                print(f"  [ERROR] {fname}: {e}")

    print(f"\n{'='*40}")
    print(f"Selesai. Berhasil: {total} | Gagal: {errors}")
    print(f"Output disimpan di: {OUTPUT_DIR}")


if __name__ == "__main__":
    run_batch()
