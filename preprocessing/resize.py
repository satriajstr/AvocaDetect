import cv2

# Ukuran standar untuk semua gambar dalam pipeline
TARGET_SIZE = (512, 512)

def resize_image(image):
    """
    Resize gambar ke ukuran TARGET_SIZE (512x512).
    Menggunakan INTER_AREA untuk downscale agar kualitas tetap baik.
    """
    return cv2.resize(image, TARGET_SIZE, interpolation=cv2.INTER_AREA)
