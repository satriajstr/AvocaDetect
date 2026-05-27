"""
Preprocessing Module - AvocaDetect
===================================
Pipeline Pengolahan Citra untuk Klasifikasi Kematangan Alpukat

Pipeline Lengkap:
  Input → Enhancement → Resize → Grayscale → Noise Reduction
        → Segmentasi → Morfologi → Masking → ROI Crop
        → Texture Enhancement → GLCM

PERBAIKAN SEGMENTASI:
  - Segmentasi HANYA menghasilkan binary mask (255=objek, 0=background)
  - Tekstur asli alpukat TIDAK DIUBAH sama sekali
  - Masking dengan bitwise_and mempertahankan detail tekstur permukaan
  - Background menjadi hitam, objek tetap memiliki variasi intensitas asli
  - Morfologi lengkap (closing + opening + largest component) untuk mask bersih

PERBAIKAN GLCM:
  - CLAHE untuk meningkatkan kontras lokal tekstur
  - Unsharp masking untuk mempertajam detail permukaan
  - Enhancement dilakukan SETELAH masking, SEBELUM normalisasi GLCM
  - Hasil: GLCM matrix lebih kaya informasi tekstur

Catatan Dataset:
  - Background  : cream / putih terang
  - Objek       : kulit alpukat (hijau gelap, hitam, cokelat)
  - Strategi    : THRESH_BINARY_INV → piksel gelap (alpukat) = 255

Author: AvocaDetect Team
"""

import cv2
import numpy as np


# =============================================================================
# 1. ENHANCEMENT — Tingkatkan pencahayaan jika gambar terlalu gelap
# =============================================================================

def enhance_brightness(image, threshold_mean=100):
    """
    Tingkatkan pencahayaan gambar menggunakan CLAHE pada channel L (LAB).

    Mengapa LAB?
    - Channel L merepresentasikan lightness secara perceptual
    - Modifikasi L tidak mempengaruhi hue/saturasi → warna tetap natural
    - CLAHE (Contrast Limited Adaptive Histogram Equalization) meningkatkan
      kontras lokal tanpa over-enhancement

    Parameters
    ----------
    image        : numpy array BGR
    threshold_mean : jika mean grayscale < nilai ini, enhancement diaktifkan

    Returns
    -------
    enhanced : gambar BGR dengan pencahayaan optimal
    """
    gray_temp = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    current_mean = np.mean(gray_temp)

    if current_mean < threshold_mean:
        # Konversi ke LAB untuk manipulasi brightness yang perceptually uniform
        lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)

        # CLAHE: clipLimit mencegah over-amplification noise
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        l_enhanced = clahe.apply(l)

        enhanced_lab = cv2.merge([l_enhanced, a, b])
        return cv2.cvtColor(enhanced_lab, cv2.COLOR_LAB2BGR)

    return image


# =============================================================================
# 2. RESIZE — Standarisasi ukuran gambar
# =============================================================================

def resize_image(image, target_size=512):
    """
    Resize gambar ke ukuran standar dengan mempertahankan aspect ratio.

    Mengapa resize diperlukan?
    - GLCM membutuhkan ukuran input yang konsisten di seluruh dataset
    - Mengurangi computational cost secara signifikan
    - 512×512 adalah trade-off optimal: detail cukup, tidak terlalu besar

    Parameters
    ----------
    image       : gambar input (BGR)
    target_size : ukuran sisi panjang (default: 512)

    Returns
    -------
    padded : gambar BGR 512×512 dengan padding putih (sesuai background cream)
    """
    h, w = image.shape[:2]

    # Hitung dimensi baru dengan aspect ratio terjaga
    if h > w:
        new_h = target_size
        new_w = int(w * target_size / h)
    else:
        new_w = target_size
        new_h = int(h * target_size / w)

    # Downscale menggunakan INTER_AREA (terbaik untuk shrinking)
    resized = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_AREA)

    # Padding simetris dengan warna putih (sama dengan background cream)
    delta_w = target_size - new_w
    delta_h = target_size - new_h
    top, bottom = delta_h // 2, delta_h - delta_h // 2
    left, right = delta_w // 2, delta_w - delta_w // 2

    padded = cv2.copyMakeBorder(
        resized, top, bottom, left, right,
        cv2.BORDER_CONSTANT, value=[255, 255, 255]
    )
    return padded


# =============================================================================
# 3. GRAYSCALE — Konversi ke satu channel
# =============================================================================

def convert_to_grayscale(image):
    """
    Konversi gambar BGR ke grayscale dengan perhitungan manual.

    Formula ITU-R BT.601 (standar internasional):
        Gray = 0.299·R + 0.587·G + 0.114·B
    
    Mengapa bobot berbeda?
    - Mata manusia lebih sensitif terhadap hijau (Green)
    - Kurang sensitif terhadap biru (Blue)
    - Merah (Red) di tengah-tengah

    Parameters
    ----------
    image : gambar BGR (numpy array shape H×W×3)

    Returns
    -------
    gray : gambar grayscale (numpy array shape H×W)
    """
    # Ekstrak channel BGR
    B = image[:, :, 0].astype(np.float32)
    G = image[:, :, 1].astype(np.float32)
    R = image[:, :, 2].astype(np.float32)
    
    # Hitung grayscale dengan formula manual
    # Gray = 0.299·R + 0.587·G + 0.114·B
    gray = 0.114 * B + 0.587 * G + 0.299 * R
    
    # Konversi kembali ke uint8 [0, 255]
    gray = np.clip(gray, 0, 255).astype(np.uint8)
    
    return gray


# =============================================================================
# 4. NOISE REDUCTION — Reduksi noise untuk segmentasi yang lebih bersih
# =============================================================================

def reduce_noise(gray_image, method='gaussian'):
    """
    Reduksi noise pada citra grayscale.

    Mengapa noise reduction sebelum GLCM?
    - Noise (variasi intensitas acak) mengganggu perhitungan co-occurrence
    - Noise membuat co-occurrence matrix lebih acak → fitur tidak informatif
    - Gaussian Blur: paling stabil untuk tekstur kulit alpukat (kernel 5×5)

    Parameters
    ----------
    gray_image : gambar grayscale
    method     : 'gaussian' | 'median' | 'bilateral'

    Returns
    -------
    denoised : gambar setelah noise reduction
    """
    if method == 'gaussian':
        # Gunakan cv2.GaussianBlur (optimized, jauh lebih cepat)
        return cv2.GaussianBlur(gray_image, (5, 5), 0)
    elif method == 'median':
        return cv2.medianBlur(gray_image, 5)
    elif method == 'bilateral':
        return cv2.bilateralFilter(gray_image, 9, 75, 75)
    return gray_image


# =============================================================================
# 5. SEGMENTASI — Pisahkan objek dari background
# =============================================================================

def segment_image(denoised_gray):
    """
    Segmentasi objek alpukat dari background cream menggunakan Otsu + morfologi.

    Mengapa segmentasi diperlukan sebelum GLCM?
    - Background (cream/putih) memiliki tekstur seragam yang berbeda dari alpukat
    - Jika background ikut dalam GLCM, fitur tekstur menjadi bias
    - Segmentasi memastikan GLCM hanya menganalisis tekstur objek alpukat
    
    PENTING: Segmentasi HANYA menghasilkan mask untuk memisahkan objek dari background.
    Tekstur asli alpukat TIDAK diubah sama sekali!

    Strategi untuk background cream:
    - Background terang (cream/putih) → intensitas tinggi
    - Alpukat (gelap: hijau tua, hitam, cokelat) → intensitas rendah
    - THRESH_BINARY_INV: piksel gelap (alpukat) → 255 (putih/objek)
    - THRESH_BINARY_INV: piksel terang (background) → 0 (hitam)

    Pipeline Morfologi:
    1. Otsu: binarisasi adaptif otomatis
    2. Closing (15×15): tutup lubang kecil di dalam objek
    3. Opening (9×9):   hapus noise kecil di background
    4. Largest component: ambil blob terbesar = objek utama
    5. Dilasi kecil: pastikan tepi objek tercakup

    Parameters
    ----------
    denoised_gray : gambar grayscale setelah noise reduction

    Returns
    -------
    clean_mask : binary mask uint8 (255=objek, 0=background)
    """
    # Otsu Thresholding
    _, binary = cv2.threshold(
        denoised_gray, 0, 255,
        cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU
    )

    # Morphological Closing - tutup lubang kecil
    kernel_close = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15))
    closed = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel_close, iterations=2)

    # Morphological Opening - hapus noise
    kernel_open = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9))
    opened = cv2.morphologyEx(closed, cv2.MORPH_OPEN, kernel_open, iterations=1)

    # Ambil Komponen Terbesar
    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(opened, connectivity=8)
    if num_labels > 1:
        largest_label = 1 + np.argmax(stats[1:, cv2.CC_STAT_AREA])
        clean_mask = np.where(labels == largest_label, 255, 0).astype(np.uint8)
    else:
        clean_mask = opened

    # Dilasi Kecil - pastikan tepi tidak terpotong
    kernel_dilate = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    clean_mask = cv2.dilate(clean_mask, kernel_dilate, iterations=1)

    return clean_mask


# =============================================================================
# 6. VISUALISASI SEGMENTASI — Tampilan profesional
# =============================================================================

def get_masked_original(original_bgr, binary_mask):
    """
    Terapkan binary mask ke gambar original → objek berwarna, background putih.

    Lebih informatif dibanding binary mask polos:
    - Memperlihatkan warna/tekstur nyata kulit alpukat
    - Background putih = bersih dan mudah dibaca

    Parameters
    ----------
    original_bgr : gambar BGR 512×512
    binary_mask  : mask biner uint8 (255=objek, 0=background)

    Returns
    -------
    masked_image : gambar BGR dengan background putih, objek berwarna asli
    """
    # Buat background putih
    white_bg = np.full_like(original_bgr, 255, dtype=np.uint8)

    # Buat mask 3-channel untuk blending
    mask_3ch = cv2.cvtColor(binary_mask, cv2.COLOR_GRAY2BGR).astype(np.float32) / 255.0

    # Blend: piksel objek dari original, piksel background dari white
    masked = (
        original_bgr.astype(np.float32) * mask_3ch
        + white_bg.astype(np.float32) * (1.0 - mask_3ch)
    ).astype(np.uint8)

    return masked


def get_contour_overlay(original_bgr, binary_mask):
    """
    Gambar kontur objek di atas gambar original.

    Visualisasi kontur membantu memverifikasi segmentasi secara intuitif:
    - Garis tepi berwarna menunjukkan batas objek yang terdeteksi
    - Tidak mengubah tampilan gambar asli

    Parameters
    ----------
    original_bgr : gambar BGR 512×512
    binary_mask  : mask biner uint8 (255=objek, 0=background)

    Returns
    -------
    overlay : gambar BGR original dengan kontur berwarna kuning
    """
    overlay = original_bgr.copy()

    # Temukan kontur luar dari mask
    contours, _ = cv2.findContours(
        binary_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )

    if contours:
        # Kontur kuning tebal (mudah terlihat di semua warna kulit alpukat)
        cv2.drawContours(overlay, contours, -1, (0, 220, 255), 3)

        # Glow effect: kontur lebih tebal + blend transparan
        glow = original_bgr.copy()
        cv2.drawContours(glow, contours, -1, (0, 200, 255), 8)
        overlay = cv2.addWeighted(overlay, 0.80, glow, 0.20, 0)

    return overlay


# =============================================================================
# 7. PIPELINE LENGKAP
# =============================================================================

def preprocess_pipeline(image):
    """
    Pipeline preprocessing dasar (tanpa segmentasi).

    Digunakan internal oleh preprocess_image().

    Returns
    -------
    resized  : gambar BGR 512×512
    gray     : grayscale
    denoised : setelah noise reduction
    """
    enhanced = enhance_brightness(image)
    resized  = resize_image(enhanced, target_size=512)
    gray     = convert_to_grayscale(resized)
    denoised = reduce_noise(gray, method='gaussian')
    return resized, gray, denoised


def preprocess_image(image):
    """
    Pipeline preprocessing LENGKAP termasuk segmentasi dan ROI cropping.

    Pipeline:
    1. Enhancement  (CLAHE jika gelap)
    2. Resize        (512×512 dengan padding putih)
    3. Grayscale     (konversi ke single channel)
    4. Noise Reduction (Gaussian Blur 5×5)
    5. Segmentasi    (Otsu + morfologi)
    6. Masking       (apply mask ke grayscale)
    7. ROI Cropping  (bounding box area objek)

    Parameters
    ----------
    image : gambar BGR input (numpy array dari cv2.imread)

    Returns
    -------
    resized       : gambar BGR 512×512
    gray          : grayscale dari gambar resize
    denoised      : setelah noise reduction
    binary_mask   : mask segmentasi (0/255)
    gray_masked   : grayscale yang sudah dimasking
    roi_cropped   : crop region of interest (grayscale)
    """
    # Step 1–4: Preprocessing dasar
    resized, gray, denoised = preprocess_pipeline(image)

    # Step 5: Segmentasi
    binary_mask = segment_image(denoised)

    # Step 6: Masking — hanya area objek yang diproses GLCM
    gray_masked = cv2.bitwise_and(denoised, denoised, mask=binary_mask)

    # Step 7: Crop ROI bounding box
    coords = cv2.findNonZero(binary_mask)
    if coords is not None:
        x, y, w, h = cv2.boundingRect(coords)
        roi_cropped = gray_masked[y:y + h, x:x + w]
    else:
        roi_cropped = gray_masked

    # Fallback: jika ROI kosong gunakan seluruh gambar
    if roi_cropped.size == 0:
        roi_cropped = denoised

    return resized, gray, denoised, binary_mask, gray_masked, roi_cropped


# =============================================================================
# 8. NORMALISASI ROI UNTUK GLCM
# =============================================================================

def enhance_texture_for_glcm(roi):
    """
    Tingkatkan detail tekstur pada ROI sebelum ekstraksi GLCM.
    
    Teknik yang digunakan:
    1. Histogram equalization untuk meningkatkan kontras lokal
    2. Unsharp masking untuk mempertajam detail tekstur
    
    Mengapa enhancement diperlukan?
    - Tekstur kulit alpukat kadang memiliki kontras rendah
    - Enhancement membuat pola tekstur lebih jelas untuk GLCM
    - Meningkatkan separabilitas antar kelas kematangan
    
    Parameters
    ----------
    roi : gambar grayscale ROI (hasil masking)
    
    Returns
    -------
    enhanced : ROI dengan tekstur yang lebih jelas
    """
    # CLAHE untuk meningkatkan kontras lokal
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(roi)
    
    # Unsharp masking untuk mempertajam tekstur
    # 1. Blur gambar
    blurred = cv2.GaussianBlur(enhanced, (0, 0), 2.0)
    # 2. Hitung detail = original - blurred
    # 3. Tambahkan detail ke original dengan weight
    enhanced = cv2.addWeighted(enhanced, 1.5, blurred, -0.5, 0)
    
    # Clip ke range [0, 255]
    enhanced = np.clip(enhanced, 0, 255).astype(np.uint8)
    
    return enhanced


def normalize_for_glcm(roi, levels=32):
    """
    Kuantisasi intensitas ROI ke rentang [0, levels-1] untuk GLCM dengan perhitungan manual.

    Mengapa normalisasi penting sebelum GLCM?
    - GLCM dibangun dari frekuensi co-occurrence pasangan intensitas piksel
    - Dengan levels=256, matriks sangat sparse → fitur tidak informatif
    - levels=32 adalah trade-off optimal: detail tekstur cukup, matriks padat
    - Min-max normalisasi memastikan seluruh rentang [0, 31] digunakan
    
    Implementasi Manual:
    1. Cari nilai minimum dan maksimum dari ROI
    2. Normalisasi ke range [0, 1]: (pixel - min) / (max - min)
    3. Scale ke [0, levels-1]: normalized * (levels - 1)
    4. Konversi ke integer uint8

    Parameters
    ----------
    roi    : gambar grayscale ROI (hasil masking)
    levels : jumlah level intensitas (default: 32)

    Returns
    -------
    normalized : gambar uint8 dengan nilai [0, levels-1]
    """
    # Enhancement tekstur sebelum normalisasi
    roi_enhanced = enhance_texture_for_glcm(roi)
    
    # Konversi ke float untuk perhitungan presisi tinggi
    roi_float = roi_enhanced.astype(np.float32)
    
    # Cari nilai minimum dan maksimum (manual)
    roi_min = np.min(roi_float)
    roi_max = np.max(roi_float)

    if roi_max > roi_min:
        # Normalisasi ke [0, 1]
        normalized = (roi_float - roi_min) / (roi_max - roi_min)
        
        # Scale ke [0, levels-1]
        normalized = normalized * (levels - 1)
    else:
        # Gambar seragam → semua nilai = 0
        normalized = np.zeros_like(roi_float)

    # Konversi ke uint8
    return normalized.astype(np.uint8)
