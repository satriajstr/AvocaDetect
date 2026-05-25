import numpy as np

def otsu_threshold(image):
    """
    Menghitung threshold optimal secara manual menggunakan algoritma Otsu's Thresholding.
    Maksimalisasi variansi antar-kelas (between-class variance).
    """
    # Flatten citra untuk mempermudah perhitungan histogram
    pixels = image.flatten()
    
    # Hitung histogram manual menggunakan numpy
    hist, _ = np.histogram(pixels, bins=256, range=(0, 256))
    
    total_pixels = pixels.size
    current_max = 0.0
    threshold = 0
    
    # Akumulasi bobot dan sum untuk background (kelas B)
    sum_b = 0
    w_b = 0
    
    # Total sum intensitas citra keseluruhan
    total_sum = np.sum(np.arange(256) * hist)
    
    for t in range(256):
        w_b += hist[t]
        if w_b == 0:
            continue
        
        w_f = total_pixels - w_b
        if w_f == 0:
            break
            
        sum_b += t * hist[t]
        
        # Hitung rata-rata kelas background (mean_b) dan foreground (mean_f)
        mean_b = sum_b / w_b
        mean_f = (total_sum - sum_b) / w_f
        
        # Hitung Between-Class Variance
        var_between = w_b * w_f * (mean_b - mean_f) ** 2
        
        # Cari nilai maksimum variansi antar-kelas
        if var_between > current_max:
            current_max = var_between
            threshold = t
            
    return threshold

def segment_image(image):
    """
    Segmentasi citra grayscale secara manual menggunakan Otsu's Thresholding.
    Mengembalikan:
    - mask: Binary mask (0 untuk background, 255 untuk foreground)
    - segmented: Citra asli yang telah dipotong berdasarkan mask
    """
    # Pastikan citra bertipe grayscale (2D)
    if len(image.shape) > 2:
        # Jika gambar berwarna, konversi sementara ke grayscale untuk kalkulasi mask
        # Menggunakan formula luminansi
        b = image[:, :, 0].astype(np.float32)
        g = image[:, :, 1].astype(np.float32)
        r = image[:, :, 2].astype(np.float32)
        gray = np.clip(0.299 * r + 0.587 * g + 0.114 * b, 0, 255).astype(np.uint8)
    else:
        gray = image

    # Cari threshold optimal dengan algoritma Otsu manual
    thresh = otsu_threshold(gray)
    
    # Buat mask biner
    mask = np.where(gray > thresh, 255, 0).astype(np.uint8)
    
    # Terapkan masking pada citra asli (bisa berwarna atau grayscale)
    if len(image.shape) == 3:
        # Masking untuk gambar berwarna (broadcast mask pada 3 channel)
        mask_3d = mask[:, :, None]
        segmented = np.where(mask_3d == 255, image, 0).astype(np.uint8)
    else:
        segmented = np.where(mask == 255, image, 0).astype(np.uint8)
        
    return mask, segmented
