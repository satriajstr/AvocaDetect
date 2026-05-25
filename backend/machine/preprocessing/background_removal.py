"""
Modul Preprocessing untuk Klasifikasi Alpukat
Menangani background removal dan masking untuk ekstraksi fitur GLCM yang akurat
"""

import cv2
import numpy as np

def remove_background(image):
    """
    Menghapus background dari gambar alpukat menggunakan thresholding
    PERBAIKAN: Alpukat tetap berwarna, background menjadi hitam
    
    Parameters:
    - image: gambar BGR dari cv2.imread()
    
    Returns:
    - masked_image: gambar dengan background hitam (0)
    - binary_mask: mask biner (255 = objek alpukat, 0 = background)
    - gray_masked: grayscale dengan background hitam
    """
    
    # 1. Konversi ke grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # 2. Gaussian Blur untuk mengurangi noise
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    
    # 3. Otsu's Thresholding untuk segmentasi otomatis
    # PERBAIKAN: Gunakan THRESH_BINARY_INV agar alpukat = 255 (putih), background = 0 (hitam)
    _, binary_mask = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    
    # 4. Morphological Operations untuk membersihkan noise
    # Closing: mengisi lubang kecil di dalam objek
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
    binary_mask = cv2.morphologyEx(binary_mask, cv2.MORPH_CLOSE, kernel)
    
    # Opening: menghilangkan noise kecil di luar objek
    binary_mask = cv2.morphologyEx(binary_mask, cv2.MORPH_OPEN, kernel)
    
    # 5. Cari kontur terbesar (asumsi: alpukat adalah objek terbesar)
    contours, _ = cv2.findContours(binary_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    if len(contours) > 0:
        # Ambil kontur terbesar
        largest_contour = max(contours, key=cv2.contourArea)
        
        # Buat mask baru dengan hanya kontur terbesar
        binary_mask = np.zeros_like(binary_mask)
        cv2.drawContours(binary_mask, [largest_contour], -1, 255, -1)
    
    # 6. Terapkan mask ke gambar grayscale
    # HASIL: Alpukat mempertahankan nilai grayscale asli, background = 0 (hitam)
    gray_masked = cv2.bitwise_and(gray, gray, mask=binary_mask)
    
    # 7. Terapkan mask ke gambar berwarna (untuk visualisasi)
    # HASIL: Alpukat berwarna asli, background = hitam
    masked_image = cv2.bitwise_and(image, image, mask=binary_mask)
    
    return masked_image, binary_mask, gray_masked


def preprocess_for_glcm(image_path):
    """
    Pipeline preprocessing lengkap untuk ekstraksi GLCM
    
    Parameters:
    - image_path: path ke file gambar
    
    Returns:
    - gray_masked: grayscale dengan background hitam (untuk GLCM)
    - binary_mask: mask biner (untuk visualisasi)
    - masked_color: gambar berwarna dengan background hitam (untuk visualisasi)
    """
    
    # Baca gambar
    image = cv2.imread(image_path)
    if image is None:
        raise ValueError(f"Tidak dapat membaca gambar: {image_path}")
    
    # Resize untuk konsistensi
    image = cv2.resize(image, (512, 512))
    
    # Hapus background
    masked_color, binary_mask, gray_masked = remove_background(image)
    
    return gray_masked, binary_mask, masked_color


def extract_roi_for_glcm(gray_masked, binary_mask):
    """
    Ekstrak Region of Interest (ROI) untuk perhitungan GLCM
    Menghindari piksel background (0) dalam perhitungan
    
    Parameters:
    - gray_masked: grayscale dengan background hitam
    - binary_mask: mask biner
    
    Returns:
    - roi_cropped: ROI yang sudah di-crop (hanya area objek)
    - bbox: bounding box (x, y, w, h)
    """
    
    # Cari bounding box dari mask
    coords = cv2.findNonZero(binary_mask)
    x, y, w, h = cv2.boundingRect(coords)
    
    # Crop ROI dari grayscale
    roi_cropped = gray_masked[y:y+h, x:x+w]
    
    # Resize ROI untuk konsistensi ukuran
    roi_cropped = cv2.resize(roi_cropped, (256, 256))
    
    return roi_cropped, (x, y, w, h)


def normalize_glcm_input(roi_image):
    """
    Normalisasi intensitas untuk GLCM
    Mengurangi jumlah gray levels dari 256 ke 32 untuk efisiensi
    
    Parameters:
    - roi_image: ROI grayscale
    
    Returns:
    - normalized: gambar dengan 32 gray levels
    """
    
    # Normalisasi ke range 0-31 (32 levels)
    # Ini mengurangi kompleksitas komputasi GLCM tanpa kehilangan informasi tekstur
    normalized = (roi_image / 8).astype(np.uint8)
    
    return normalized
