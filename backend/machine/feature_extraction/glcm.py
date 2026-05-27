"""
GLCM Feature Extraction - AvocaDetect
======================================
Gray Level Co-occurrence Matrix untuk Analisis Tekstur Kulit Alpukat

Mengapa GLCM?
- Mengukur hubungan spasial antar piksel yang berdekatan (co-occurrence)
- Sangat efektif untuk membedakan tingkat kekasaran/kehalusan tekstur
- Kulit alpukat mentah (kasar, berbintil) vs matang (lebih halus) memiliki
  GLCM yang berbeda → bisa dibedakan oleh SVM

PERBAIKAN SEGMENTASI & GLCM:
- Segmentasi HANYA menghapus background, tekstur asli alpukat TETAP DIPERTAHANKAN
- Background menjadi hitam (0), permukaan alpukat tetap memiliki detail tekstur asli
- Enhancement tekstur dengan CLAHE + Unsharp Masking sebelum GLCM
- Visualisasi GLCM menggunakan log scale untuk distribusi yang lebih jelas
- Colormap VIRIDIS untuk representasi yang lebih baik

Mengapa GLCM matrix berbentuk diagonal?
- Untuk gambar dengan tekstur seragam/halus, piksel bersebelahan cenderung
  memiliki intensitas yang mirip → pasangan (i,j) dengan |i-j| kecil mendominasi
- Ini menghasilkan konsentrasi nilai di sekitar diagonal utama matriks
- Diagonal kuat = tekstur seragam (alpukat matang lebih seragam dari mentah)
- Diagonal lemah/tersebar = tekstur kasar/heterogen

Konfigurasi:
- distances = [1]        : hanya piksel bersebelahan langsung
- angles    = [0°,45°,90°,135°] : 4 arah untuk rotational invariance
- levels    = 32         : kuantisasi optimal untuk tekstur kulit

Author: AvocaDetect Team
"""

import os
import sys
import cv2
import numpy as np
from skimage.feature import graycomatrix, graycoprops

# Tambahkan path backend/machine ke sys.path agar bisa import preprocessing
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from preprocessing.preprocessing import preprocess_image, normalize_for_glcm


# =============================================================================
# KONFIGURASI GLCM
# =============================================================================

GLCM_DISTANCES = [1]                                        # jarak 1 piksel
GLCM_ANGLES    = [0, np.pi/4, np.pi/2, 3 * np.pi/4]      # 4 arah
GLCM_LEVELS    = 32                                         # jumlah level


# =============================================================================
# PERHITUNGAN GLCM MATRIX
# =============================================================================

def compute_glcm_matrix(roi_normalized):
    """
    Hitung GLCM matrix dari ROI yang sudah dikuantisasi.

    GLCM[i,j] = frekuensi pasangan piksel bersebelahan dengan intensitas (i,j)
    - symmetric=True: GLCM[i,j] = GLCM[j,i] (matriks simetris)
    - normed=True   : normalisasi sehingga sum = 1 (menjadi distribusi probabilitas)

    Parameters
    ----------
    roi_normalized : gambar uint8 dengan nilai [0, GLCM_LEVELS-1]

    Returns
    -------
    glcm : numpy array shape (levels, levels, n_distances, n_angles)
    """
    glcm = graycomatrix(
        roi_normalized,
        distances=GLCM_DISTANCES,
        angles=GLCM_ANGLES,
        levels=GLCM_LEVELS,
        symmetric=True,
        normed=True
    )
    return glcm


def create_glcm_visualization(glcm, roi_normalized, size=512):
    """
    Buat visualisasi GLCM yang lebih informatif dan representatif.
    
    Visualisasi ini menggabungkan:
    1. GLCM matrix dengan colormap yang lebih baik
    2. Histogram distribusi intensitas ROI
    3. Informasi statistik dasar
    4. Thumbnail ROI untuk referensi
    
    Parameters
    ----------
    glcm : GLCM matrix dari compute_glcm_matrix()
    roi_normalized : ROI yang sudah dinormalisasi ke 32 levels
    size : ukuran output (default: 512x512)
    
    Returns
    -------
    visualization : gambar BGR untuk ditampilkan
    """
    # Ambil GLCM untuk distance=1, angle=0° (paling representatif)
    glcm_2d = glcm[:, :, 0, 0]
    
    # Normalisasi dengan log scale untuk visualisasi yang lebih baik
    # Log scale membuat nilai kecil lebih terlihat
    glcm_log = np.log1p(glcm_2d * 1000)  # log1p = log(1 + x) untuk menghindari log(0)
    glcm_norm = (glcm_log / (glcm_log.max() + 1e-10) * 255).astype(np.uint8)
    
    # Resize ke ukuran target dengan interpolasi nearest (mempertahankan struktur matriks)
    glcm_resized = cv2.resize(glcm_norm, (size, size), interpolation=cv2.INTER_NEAREST)
    
    # Gunakan colormap VIRIDIS (lebih baik dari MAGMA untuk data matriks)
    glcm_colored = cv2.applyColorMap(glcm_resized, cv2.COLORMAP_VIRIDIS)
    
    # Tambah grid untuk tampilan matriks yang lebih profesional
    grid_step = size // 8  # 8 garis grid
    for i in range(0, size, grid_step):
        cv2.line(glcm_colored, (i, 0), (i, size-1), (40, 40, 40), 1, cv2.LINE_AA)
        cv2.line(glcm_colored, (0, i), (size-1, i), (40, 40, 40), 1, cv2.LINE_AA)
    
    # Tambah border luar
    cv2.rectangle(glcm_colored, (0, 0), (size-1, size-1), (80, 80, 80), 2)
    
    # Tambah thumbnail ROI di pojok kanan bawah
    thumb_size = 96
    roi_thumb = cv2.resize(roi_normalized, (thumb_size, thumb_size), interpolation=cv2.INTER_AREA)
    roi_thumb_bgr = cv2.cvtColor(roi_thumb, cv2.COLOR_GRAY2BGR)
    
    # Posisi thumbnail
    y_start = size - thumb_size - 10
    x_start = size - thumb_size - 10
    
    # Tambah background gelap untuk thumbnail
    cv2.rectangle(glcm_colored, 
                  (x_start-2, y_start-2), 
                  (x_start+thumb_size+1, y_start+thumb_size+1), 
                  (20, 20, 20), -1)
    
    # Paste thumbnail
    glcm_colored[y_start:y_start+thumb_size, x_start:x_start+thumb_size] = roi_thumb_bgr
    
    # Border putih untuk thumbnail
    cv2.rectangle(glcm_colored, 
                  (x_start-1, y_start-1), 
                  (x_start+thumb_size, y_start+thumb_size), 
                  (255, 255, 255), 1)
    
    # Tambah label "ROI" di atas thumbnail
    cv2.putText(glcm_colored, "ROI", 
                (x_start, y_start-5), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1, cv2.LINE_AA)
    
    return glcm_colored


# =============================================================================
# EKSTRAKSI FITUR STATISTIK DARI GLCM
# =============================================================================

def extract_features_from_glcm(glcm):
    """
    Ekstrak 6 fitur dari GLCM, dihitung sebagai mean dan std dari 4 arah.
    Total: 6 fitur × 2 statistik = 12 fitur per gambar.

    Penjelasan setiap fitur:
    +-----------------+----------------------------------------------------+
    | Fitur           | Makna Fisik                                        |
    +-----------------+----------------------------------------------------+
    | Contrast        | Perbedaan intensitas antar piksel berdekatan        |
    |                 | Tinggi = tekstur kasar (alpukat mentah)             |
    | Correlation     | Linearitas hubungan antar piksel                    |
    |                 | Tinggi = pola berulang (tekstur seragam)            |
    | Energy          | Keseragaman distribusi co-occurrence                |
    |                 | Tinggi = tekstur sangat seragam/homogen             |
    | Homogeneity     | Kedekatan nilai ke diagonal GLCM                    |
    |                 | Tinggi = piksel bersebelahan mirip (halus)          |
    | ASM             | Angular Second Moment (kuadrat dari Energy)         |
    |                 | Tinggi = tekstur sangat seragam                     |
    | Dissimilarity   | Perbedaan absolut antar piksel (mirip Contrast)     |
    |                 | Tinggi = tekstur tidak seragam                      |
    +-----------------+----------------------------------------------------+

    Mengapa rata-rata 4 arah?
    - Menjadikan fitur rotation-invariant
    - Alpukat bisa difoto dari berbagai sudut → fitur harus konsisten

    Parameters
    ----------
    glcm : GLCM matrix dari compute_glcm_matrix()

    Returns
    -------
    features_array : numpy array shape (1, 12)
                     [contrast_mean, correlation_mean, energy_mean,
                      homogeneity_mean, asm_mean, dissimilarity_mean,
                      contrast_std,  correlation_std,  energy_std,
                      homogeneity_std,  asm_std,  dissimilarity_std]
    """
    contrast      = graycoprops(glcm, 'contrast')
    correlation   = graycoprops(glcm, 'correlation')
    energy        = graycoprops(glcm, 'energy')
    homogeneity   = graycoprops(glcm, 'homogeneity')
    asm           = graycoprops(glcm, 'ASM')
    dissimilarity = graycoprops(glcm, 'dissimilarity')

    # Mean dan Std dari semua arah (kolom = arah)
    features = np.array([
        contrast.mean(),      correlation.mean(),      energy.mean(),
        homogeneity.mean(),   asm.mean(),              dissimilarity.mean(),
        contrast.std(),       correlation.std(),        energy.std(),
        homogeneity.std(),    asm.std(),               dissimilarity.std()
    ]).reshape(1, -1)

    return features


def get_feature_dict(glcm):
    """
    Kembalikan fitur GLCM sebagai dictionary bernama untuk tabel di UI.

    Parameters
    ----------
    glcm : GLCM matrix dari compute_glcm_matrix()

    Returns
    -------
    dict : { nama_fitur (str) : nilai (float) }
           12 entri total (6 mean + 6 std)
    """
    contrast      = graycoprops(glcm, 'contrast')
    correlation   = graycoprops(glcm, 'correlation')
    energy        = graycoprops(glcm, 'energy')
    homogeneity   = graycoprops(glcm, 'homogeneity')
    asm           = graycoprops(glcm, 'ASM')
    dissimilarity = graycoprops(glcm, 'dissimilarity')

    return {
        'Contrast (mean)':      round(float(contrast.mean()),      6),
        'Correlation (mean)':   round(float(correlation.mean()),   6),
        'Energy (mean)':        round(float(energy.mean()),        6),
        'Homogeneity (mean)':   round(float(homogeneity.mean()),   6),
        'ASM (mean)':           round(float(asm.mean()),           6),
        'Dissimilarity (mean)': round(float(dissimilarity.mean()), 6),
        'Contrast (std)':       round(float(contrast.std()),       6),
        'Correlation (std)':    round(float(correlation.std()),    6),
        'Energy (std)':         round(float(energy.std()),         6),
        'Homogeneity (std)':    round(float(homogeneity.std()),    6),
        'ASM (std)':            round(float(asm.std()),            6),
        'Dissimilarity (std)':  round(float(dissimilarity.std()),  6),
    }


# =============================================================================
# EKSTRAKSI DARI SATU FILE GAMBAR
# =============================================================================

def extract_glcm_features(image_path):
    """
    End-to-end ekstraksi fitur GLCM dari satu file gambar.

    Parameters
    ----------
    image_path : str — path ke file gambar

    Returns
    -------
    features : numpy array shape (1, 12)
    """
    image = cv2.imread(image_path)
    if image is None:
        raise ValueError(f"Tidak dapat membaca gambar: {image_path}")

    # Full preprocessing pipeline
    _, _, _, _, _, roi_cropped = preprocess_image(image)

    # Normalisasi ke 32 level untuk GLCM
    roi_normalized = normalize_for_glcm(roi_cropped, levels=GLCM_LEVELS)

    # Hitung GLCM dan ekstrak fitur
    glcm     = compute_glcm_matrix(roi_normalized)
    features = extract_features_from_glcm(glcm)

    return features


# =============================================================================
# EKSTRAKSI DARI FOLDER DATASET
# =============================================================================

def extract_features_from_folder(folder_path, label):
    """
    Ekstraksi fitur GLCM dari semua gambar dalam satu folder.

    Parameters
    ----------
    folder_path : path ke folder
    label       : label kelas integer (0–3)

    Returns
    -------
    features_list : list of 1D numpy arrays
    labels_list   : list of integers
    """
    features_list = []
    labels_list   = []
    valid_ext     = {'.jpg', '.jpeg', '.png', '.bmp'}

    filenames = sorted(os.listdir(folder_path))  # sorted untuk reproducibility
    for filename in filenames:
        if os.path.splitext(filename)[1].lower() not in valid_ext:
            continue

        image_path = os.path.join(folder_path, filename)
        try:
            features = extract_glcm_features(image_path)
            features_list.append(features.flatten())
            labels_list.append(label)
        except Exception as e:
            print(f"    [ERR] Gagal memproses {filename}: {e}")

    return features_list, labels_list


def extract_all_features(dataset_path):
    """
    Ekstraksi fitur GLCM dari seluruh dataset.

    Struktur folder yang diharapkan:
        dataset/
        +-- mentah/
        +-- setengah_matang/
        +-- matang/
        +-- terlalu_matang/

    Parameters
    ----------
    dataset_path : path ke folder dataset

    Returns
    -------
    X : numpy array shape (n_samples, 12)
    y : numpy array shape (n_samples,)
    """
    # Mapping nama folder ke label integer
    categories = {
        'mentah':          0,
        'setengah_matang': 1,
        'matang':          2,
        'terlalu_matang':  3,
    }

    all_features = []
    all_labels   = []

    sep = "=" * 70
    print(f"\n{sep}")
    print("  EKSTRAKSI FITUR GLCM — AvocaDetect")
    print(f"  Konfigurasi:")
    print(f"    distances = {GLCM_DISTANCES}")
    print(f"    angles    = [0°, 45°, 90°, 135°]")
    print(f"    levels    = {GLCM_LEVELS}")
    print(f"    features  = contrast, correlation, energy,")
    print(f"                homogeneity, ASM, dissimilarity")
    print(f"    statistik = mean + std per fitur = 12 fitur total")
    print(f"{sep}")

    for category, label in categories.items():
        folder_path = os.path.join(dataset_path, category)

        if not os.path.exists(folder_path):
            print(f"\n  [!] Folder '{category}' tidak ditemukan, dilewati.")
            continue

        print(f"\n  [{label + 1}/4] Memproses: {category.upper()}")
        print(f"  {'-' * 50}")

        features, labels = extract_features_from_folder(folder_path, label)
        all_features.extend(features)
        all_labels.extend(labels)

        print(f"  [OK] {len(features)} gambar berhasil diekstraksi")

    print(f"\n{sep}")
    print(f"  SELESAI: {len(all_features)} gambar, {12} fitur per gambar")
    print(f"{sep}\n")

    return np.array(all_features), np.array(all_labels)
