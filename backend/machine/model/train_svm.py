"""
Training SVM Model untuk Klasifikasi Kematangan Alpukat
"""

import os
import numpy as np
import pickle
from sklearn.model_selection import train_test_split
from sklearn.svm import SVC
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
import sys

# Tambahkan path root project
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

from backend.machine.feature_extraction.glcm import extract_all_features

def train_model(dataset_path, model_save_path='backend/machine/model/svm_model.pkl', 
                scaler_save_path='backend/machine/model/scaler.pkl'):
    """
    Training model SVM untuk klasifikasi kematangan alpukat
    
    Parameters:
    - dataset_path: path ke folder dataset
    - model_save_path: path untuk menyimpan model
    - scaler_save_path: path untuk menyimpan scaler
    
    Returns:
    - model: trained SVM model
    - scaler: fitted StandardScaler
    - accuracy: akurasi model
    """
    
    print("="*60)
    print("TRAINING MODEL SVM - KLASIFIKASI KEMATANGAN ALPUKAT")
    print("="*60)
    
    # 1. Ekstraksi fitur dari dataset
    print("\n[1/5] Ekstraksi fitur GLCM dari dataset...")
    X, y = extract_all_features(dataset_path)
    
    if len(X) == 0:
        raise ValueError("Tidak ada data yang berhasil diekstraksi!")
    
    # 2. Split data training dan testing
    print("\n[2/5] Split data training dan testing (80:20)...")
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    print(f"  - Data training: {len(X_train)} samples")
    print(f"  - Data testing: {len(X_test)} samples")
    
    # 3. Normalisasi fitur
    print("\n[3/5] Normalisasi fitur menggunakan StandardScaler...")
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # 4. Training model SVM
    print("\n[4/5] Training model SVM...")
    print("  - Kernel: RBF")
    print("  - C: 10")
    print("  - Gamma: scale")
    
    model = SVC(kernel='rbf', C=10, gamma='scale', random_state=42)
    model.fit(X_train_scaled, y_train)
    
    print("  ✓ Training selesai!")
    
    # 5. Evaluasi model
    print("\n[5/5] Evaluasi model...")
    y_pred = model.predict(X_test_scaled)
    
    accuracy = accuracy_score(y_test, y_pred)
    print(f"\n  Akurasi: {accuracy*100:.2f}%")
    
    # Label kategori
    categories = ['Mentah', 'Setengah Matang', 'Matang', 'Terlalu Matang']
    
    print("\n  Classification Report:")
    print(classification_report(y_test, y_pred, target_names=categories))
    
    print("\n  Confusion Matrix:")
    cm = confusion_matrix(y_test, y_pred)
    print(cm)
    
    # 6. Simpan model dan scaler
    print("\n[6/6] Menyimpan model dan scaler...")
    
    # Buat folder jika belum ada
    os.makedirs(os.path.dirname(model_save_path), exist_ok=True)
    
    with open(model_save_path, 'wb') as f:
        pickle.dump(model, f)
    print(f"  ✓ Model disimpan di: {model_save_path}")
    
    with open(scaler_save_path, 'wb') as f:
        pickle.dump(scaler, f)
    print(f"  ✓ Scaler disimpan di: {scaler_save_path}")
    
    print("\n" + "="*60)
    print("TRAINING SELESAI!")
    print("="*60)
    
    return model, scaler, accuracy

if __name__ == "__main__":
    # Path ke dataset
    dataset_path = 'dataset'
    
    # Training model
    try:
        model, scaler, accuracy = train_model(dataset_path)
        print(f"\n✓ Model berhasil di-training dengan akurasi {accuracy*100:.2f}%")
    except Exception as e:
        print(f"\n✗ Error: {str(e)}")
