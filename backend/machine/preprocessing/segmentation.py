"""
Segmentation Module - Standar Penelitian Computer Vision
Segmentasi objek alpukat dengan metode robust

Author: AvocaDetect Team
Pipeline: Thresholding → Morphological Operations → Contour Detection → Masking
"""

import cv2
import numpy as np


def segment_object(denoised_gray):
    """
    Segmentasi objek alpukat dari background
    
    Penjelasan:
    - Otsu's Thresholding: mencari threshold optimal secara otomatis
    - THRESH_BINARY_INV: objek gelap (alpukat) = putih (255), background terang = hitam (0)
    - Morphological operations: membersihkan noise dan mengisi lubang
    
    Parameters:
    - denoised_gray: gambar grayscale setelah noise reduction
    
    Returns:
    - binary_mask: mask biner (255 = objek, 0 = background)
    - thresh_value: nilai threshold yang digunakan
    """
    # Otsu's Thresholding
    # Otsu mencari threshold yang memaksimalkan variance antar kelas
    thresh_value, binary_mask = cv2.threshold(
        denoised_gray, 0, 255, 
        cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU
    )
    
    return binary_mask, thresh_value


def morphological_operations(binary_mask):
    """
    Operasi morfologi untuk membersihkan mask
    
    Penjelasan:
    - Closing: mengisi lubang kecil di dalam objek
    - Opening: menghilangkan noise kecil di luar objek
    - Urutan penting: Closing dulu, baru Opening
    
    Kernel ellipse lebih baik untuk objek organik (alpukat)
    
    Parameters:
    - binary_mask: mask biner hasil thresholding
    
    Returns:
    - cleaned_mask: mask setelah morphological operations
    """
    # Kernel ellipse 7x7 (cocok untuk objek organik)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
    
    # Morphological Closing
    # Menutup lubang kecil di dalam objek
    # Operasi: Dilation → Erosion
    closed = cv2.morphologyEx(binary_mask, cv2.MORPH_CLOSE, kernel, iterations=2)
    
    # Morphological Opening
    # Menghilangkan noise kecil di luar objek
    # Operasi: Erosion → Dilation
    opened = cv2.morphologyEx(closed, cv2.MORPH_OPEN, kernel, iterations=1)
    
    return opened


def extract_largest_contour(mask):
    """
    Ekstrak kontur terbesar (asumsi: alpukat adalah objek terbesar)
    
    Penjelasan:
    - Contour: boundary dari objek
    - RETR_EXTERNAL: hanya kontur luar
    - CHAIN_APPROX_SIMPLE: kompresi kontur (hemat memori)
    
    Parameters:
    - mask: mask biner
    
    Returns:
    - final_mask: mask dengan hanya kontur terbesar
    - largest_contour: kontur terbesar
    - area: luas kontur
    """
    # Find contours
    contours, _ = cv2.findContours(
        mask, 
        cv2.RETR_EXTERNAL, 
        cv2.CHAIN_APPROX_SIMPLE
    )
    
    if len(contours) == 0:
        return mask, None, 0
    
    # Ambil kontur terbesar berdasarkan area
    largest_contour = max(contours, key=cv2.contourArea)
    area = cv2.contourArea(largest_contour)
    
    # Buat mask baru dengan hanya kontur terbesar
    final_mask = np.zeros_like(mask)
    cv2.drawContours(final_mask, [largest_contour], -1, 255, -1)
    
    return final_mask, largest_contour, area


def create_masked_image(original, mask):
    """
    Terapkan mask ke gambar asli
    
    Penjelasan:
    - bitwise_and: operasi AND antara gambar dan mask
    - Piksel dengan mask=255 → pertahankan nilai asli
    - Piksel dengan mask=0 → jadikan hitam (0)
    
    Parameters:
    - original: gambar asli (BGR atau Grayscale)
    - mask: binary mask
    
    Returns:
    - masked: gambar dengan background hitam
    """
    masked = cv2.bitwise_and(original, original, mask=mask)
    return masked


def create_contour_visualization(original, contour):
    """
    Visualisasi kontur pada gambar asli
    
    Penjelasan:
    - Menampilkan outline objek dengan warna kontras
    - Thickness=3: garis cukup tebal untuk terlihat jelas
    - Warna hijau (0, 255, 0) kontras dengan alpukat
    
    Parameters:
    - original: gambar asli BGR
    - contour: kontur objek
    
    Returns:
    - contour_img: gambar dengan kontur
    """
    contour_img = original.copy()
    
    if contour is not None:
        # Gambar kontur dengan warna hijau terang
        cv2.drawContours(contour_img, [contour], -1, (0, 255, 0), 3)
        
        # Tambahkan bounding box (opsional)
        x, y, w, h = cv2.boundingRect(contour)
        cv2.rectangle(contour_img, (x, y), (x+w, y+h), (255, 0, 0), 2)
    
    return contour_img


def segmentation_pipeline(denoised_gray, original_image):
    """
    Pipeline segmentasi lengkap
    
    Pipeline:
    1. Thresholding (Otsu)
    2. Morphological Closing
    3. Morphological Opening
    4. Extract largest contour
    5. Create final mask
    6. Apply mask to original
    
    Parameters:
    - denoised_gray: gambar grayscale setelah noise reduction
    - original_image: gambar asli BGR
    
    Returns:
    - binary_mask: mask biner awal
    - morphed_mask: mask setelah morphological operations
    - final_mask: mask final (hanya objek terbesar)
    - masked_image: gambar asli dengan background hitam
    - contour_image: gambar dengan outline kontur
    - contour: kontur objek
    - area: luas objek
    """
    # Step 1: Thresholding
    binary_mask, thresh_value = segment_object(denoised_gray)
    
    # Step 2: Morphological Operations
    morphed_mask = morphological_operations(binary_mask)
    
    # Step 3: Extract Largest Contour
    final_mask, contour, area = extract_largest_contour(morphed_mask)
    
    # Step 4: Create Masked Image
    masked_image = create_masked_image(original_image, final_mask)
    
    # Step 5: Create Contour Visualization
    contour_image = create_contour_visualization(original_image, contour)
    
    return binary_mask, morphed_mask, final_mask, masked_image, contour_image, contour, area


# ===== PENJELASAN ILMIAH =====
"""
MENGAPA SEGMENTASI DIPERLUKAN SEBELUM GLCM?

1. FOKUS PADA OBJEK:
   - GLCM menghitung co-occurrence matrix dari SELURUH gambar
   - Jika background tidak dihilangkan, tekstur background akan dominan
   - Background putih polos = homogen = akan mengacaukan statistik tekstur
   
2. CONTOH MASALAH TANPA SEGMENTASI:
   - Gambar 512x512 = 262,144 piksel
   - Alpukat hanya 30% = 78,643 piksel
   - Background 70% = 183,501 piksel
   - GLCM akan lebih banyak menghitung co-occurrence background!
   
3. SOLUSI DENGAN SEGMENTASI:
   - Ekstrak ROI (Region of Interest) = hanya area alpukat
   - GLCM hanya menghitung tekstur kulit alpukat
   - Fitur tekstur menjadi representatif untuk klasifikasi
   
4. MORPHOLOGICAL OPERATIONS:
   - Closing: mengisi lubang kecil (shadow di permukaan alpukat)
   - Opening: menghilangkan noise (refleksi kecil, debu)
   - Hasil: mask yang bersih dan akurat
   
5. LARGEST CONTOUR:
   - Asumsi: alpukat adalah objek terbesar dalam frame
   - Menghilangkan objek kecil yang tidak relevan
   - Fokus pada objek utama
   
TRADE-OFF:
- Threshold terlalu tinggi = objek terpotong
- Threshold terlalu rendah = background masuk
- Otsu's method = optimal untuk sebagian besar kasus
"""
