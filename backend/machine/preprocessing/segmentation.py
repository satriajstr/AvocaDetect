import cv2
import numpy as np

def segment_image(image):
    """
    Segmentasi gambar menggunakan Otsu Thresholding dengan morfologi.
    
    PENTING: Fungsi ini HANYA menghasilkan binary mask untuk memisahkan
    objek dari background. Tekstur asli alpukat TIDAK diubah - hanya
    digunakan untuk menentukan area mana yang objek (255) dan background (0).
    
    Proses:
    1. Otsu thresholding untuk binarisasi otomatis
    2. Morfologi closing untuk menutup lubang kecil
    3. Morfologi opening untuk menghapus noise
    4. Ambil komponen terbesar sebagai objek utama
    5. Dilasi kecil untuk memastikan tepi objek tercakup

    Return:
        mask   : binary mask (255=objek alpukat, 0=background)
        result : gambar grayscale dengan background dihitamkan, tekstur objek TETAP ASLI
    """
    # Otsu thresholding - threshold otomatis berdasarkan histogram
    _, binary = cv2.threshold(image, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    
    # Morfologi closing - tutup lubang kecil di dalam objek
    kernel_close = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15))
    closed = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel_close, iterations=2)
    
    # Morfologi opening - hapus noise kecil di background
    kernel_open = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9))
    opened = cv2.morphologyEx(closed, cv2.MORPH_OPEN, kernel_open, iterations=1)
    
    # Ambil komponen terbesar (objek alpukat utama)
    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(opened, connectivity=8)
    if num_labels > 1:
        # Cari label dengan area terbesar (skip label 0 = background)
        largest_label = 1 + np.argmax(stats[1:, cv2.CC_STAT_AREA])
        mask = np.where(labels == largest_label, 255, 0).astype(np.uint8)
    else:
        mask = opened
    
    # Dilasi kecil untuk memastikan tepi objek tidak terpotong
    kernel_dilate = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    mask = cv2.dilate(mask, kernel_dilate, iterations=1)

    # PENTING: Terapkan mask ke gambar ASLI dengan bitwise_and
    # Ini mempertahankan tekstur asli alpukat, hanya background yang jadi hitam
    result = cv2.bitwise_and(image, image, mask=mask)
    
    return mask, result
