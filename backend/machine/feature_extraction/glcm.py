"""
GLCM (Gray Level Co-occurrence Matrix) Feature Extraction
Ekstraksi fitur tekstur dari gambar alpukat
"""

import cv2
import numpy as np
from skimage.feature import graycomatrix, graycoprops

def extract_glcm_features(image_path, distances=[1], angles=[0, np.pi/4, np.pi/2, 3*np.pi/4]):
    """
    Ekstraksi fitur GLCM dari gambar
    
    Parameters:
    - image_path: path ke file gambar
    - distances: jarak pixel untuk GLCM (default: [1])
    - angles: sudut untuk GLCM (default: [0, 45, 90, 135 derajat])
    
    Returns:
    - features: array fitur GLCM [contrast, dissimilarity, homogeneity, energy, correlation, ASM]
    """
    
    # Baca gambar
    image = cv2.imread(image_path)
    if image is None:
        raise ValueError(f"Tidak dapat membaca gambar: {image_path}")
    
    # Konversi ke grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # Resize untuk konsistensi (opsional, sesuaikan dengan kebutuhan)
    gray = cv2.resize(gray, (256, 256))
    
    # Hitung GLCM
    glcm = graycomatrix(gray, distances=distances, angles=angles, 
                        levels=256, symmetric=True, normed=True)
    
    # Ekstraksi properti GLCM
    contrast = graycoprops(glcm, 'contrast').flatten()
    dissimilarity = graycoprops(glcm, 'dissimilarity').flatten()
    homogeneity = graycoprops(glcm, 'homogeneity').flatten()
    energy = graycoprops(glcm, 'energy').flatten()
    correlation = graycoprops(glcm, 'correlation').flatten()
    asm = graycoprops(glcm, 'ASM').flatten()
    
    # Gabungkan semua fitur
    features = np.concatenate([
        contrast.mean(), dissimilarity.mean(), homogeneity.mean(),
        energy.mean(), correlation.mean(), asm.mean(),
        contrast.std(), dissimilarity.std(), homogeneity.std(),
        energy.std(), correlation.std(), asm.std()
    ]).reshape(1, -1)
    
    return features

def extract_features_from_folder(folder_path, label):
    """
    Ekstraksi fitur dari semua gambar dalam folder
    
    Parameters:
    - folder_path: path ke folder berisi gambar
    - label: label klasifikasi (0: mentah, 1: setengah_matang, 2: matang, 3: terlalu_matang)
    
    Returns:
    - features_list: list of features
    - labels_list: list of labels
    """
    import os
    
    features_list = []
    labels_list = []
    
    # Ekstensi file gambar yang didukung
    valid_extensions = ['.jpg', '.jpeg', '.png', '.bmp']
    
    # Loop semua file dalam folder
    for filename in os.listdir(folder_path):
        file_ext = os.path.splitext(filename)[1].lower()
        
        if file_ext in valid_extensions:
            image_path = os.path.join(folder_path, filename)
            
            try:
                # Ekstraksi fitur
                features = extract_glcm_features(image_path)
                features_list.append(features.flatten())
                labels_list.append(label)
                
            except Exception as e:
                print(f"Error processing {filename}: {str(e)}")
                continue
    
    return features_list, labels_list

def extract_all_features(dataset_path):
    """
    Ekstraksi fitur dari semua kategori dataset
    
    Parameters:
    - dataset_path: path ke folder dataset utama
    
    Returns:
    - X: array fitur (n_samples, n_features)
    - y: array label (n_samples,)
    """
    import os
    
    # Mapping folder ke label
    categories = {
        'mentah': 0,
        'setengah_matang': 1,
        'matang': 2,
        'terlalu_matang': 3
    }
    
    all_features = []
    all_labels = []
    
    print("Memulai ekstraksi fitur GLCM...")
    
    for category, label in categories.items():
        folder_path = os.path.join(dataset_path, category)
        
        if not os.path.exists(folder_path):
            print(f"Warning: Folder {category} tidak ditemukan!")
            continue
        
        print(f"Memproses kategori: {category}...")
        features, labels = extract_features_from_folder(folder_path, label)
        
        all_features.extend(features)
        all_labels.extend(labels)
        
        print(f"  - {len(features)} gambar berhasil diproses")
    
    print(f"\nTotal: {len(all_features)} gambar berhasil diekstraksi fiturnya")
    
    return np.array(all_features), np.array(all_labels)
