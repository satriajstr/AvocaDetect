"""
Training SVM Model - AvocaDetect
==================================
Klasifikasi Kematangan Alpukat menggunakan Support Vector Machine

Mengapa SVM?
- Efektif untuk data berdimensi relatif rendah (12 fitur GLCM)
- Margin maximization → generalisasi baik pada data baru
- RBF kernel: cocok untuk data non-linear seperti fitur tekstur
- probability=True (Platt scaling): menghasilkan confidence score yang valid

Mengapa StandardScaler sebelum SVM?
- SVM sensitif terhadap skala fitur
- Fitur dengan range besar akan mendominasi hyperplane → bias
- StandardScaler: transformasi ke mean=0, std=1 per fitur
- Hasilnya: setiap fitur berkontribusi proporsional terhadap keputusan

Parameter SVM yang digunakan:
- kernel='rbf' : Radial Basis Function — cocok untuk data non-linear
- C=10         : regularization (lebih besar = lebih fit, risiko overfit)
- gamma='scale': 1 / (n_features × X.var()) — adaptif terhadap data
- class_weight='balanced': handle ketidakseimbangan jumlah kelas

Author: AvocaDetect Team
"""

import os
import sys
import json
import pickle
import numpy as np

from sklearn.model_selection import train_test_split
from sklearn.svm import SVC
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
)

# Path root project
sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
)
from backend.machine.feature_extraction.glcm import extract_all_features

# Label kategori kematangan
CATEGORIES = ['Mentah', 'Setengah Matang', 'Matang', 'Terlalu Matang']


def train_model(
    dataset_path,
    model_save_path  = 'backend/machine/model/svm_model.pkl',
    scaler_save_path = 'backend/machine/model/scaler.pkl',
    report_save_path = 'backend/machine/model/eval_report.json',
):
    """
    Training model SVM untuk klasifikasi kematangan alpukat.

    Alur:
    1. Ekstraksi fitur GLCM dari dataset
    2. Train-test split (80:20, stratified)
    3. Normalisasi fitur (StandardScaler)
    4. Training SVM (RBF, C=10, gamma=scale, probability=True)
    5. Evaluasi (accuracy, precision, recall, f1, confusion matrix)
    6. Simpan model, scaler, dan eval report JSON

    Parameters
    ----------
    dataset_path      : str — path ke folder dataset
    model_save_path   : str — path simpan model .pkl
    scaler_save_path  : str — path simpan scaler .pkl
    report_save_path  : str — path simpan eval report .json

    Returns
    -------
    model    : trained SVC
    scaler   : fitted StandardScaler
    accuracy : float — akurasi pada test set [0, 1]
    """
    sep = "=" * 65

    print(f"\n{sep}")
    print("  AVOCADETECT — TRAINING MODEL SVM")
    print(f"  Klasifikasi Kematangan Alpukat | GLCM + SVM")
    print(f"{sep}")

    # -------------------------------------------------------------------------
    # STEP 1: Ekstraksi Fitur
    # -------------------------------------------------------------------------
    print("\n[1/5] Ekstraksi fitur GLCM dari dataset...")
    X, y = extract_all_features(dataset_path)

    if len(X) == 0:
        raise ValueError("Tidak ada data yang berhasil diekstraksi dari dataset!")

    print(f"  [OK] Total sampel  : {len(X)}")
    print(f"  [OK] Jumlah fitur  : {X.shape[1]}")
    print(f"  [OK] Distribusi kelas:")
    for i, cat in enumerate(CATEGORIES):
        count = int(np.sum(y == i))
        print(f"      {cat:>18} : {count} sampel")

    # -------------------------------------------------------------------------
    # STEP 2: Train-Test Split
    # -------------------------------------------------------------------------
    print("\n[2/5] Train-Test Split (80% training / 20% testing, stratified)...")
    X_train, X_test, y_train, y_test = train_test_split(
        X, y,
        test_size=0.2,
        random_state=42,
        stratify=y,          # Pastikan proporsi kelas sama di train & test
    )
    print(f"  [OK] Data training : {len(X_train)} sampel")
    print(f"  [OK] Data testing  : {len(X_test)} sampel")

    # -------------------------------------------------------------------------
    # STEP 3: Normalisasi Fitur
    # -------------------------------------------------------------------------
    print("\n[3/5] Normalisasi fitur (StandardScaler)...")
    print("  Mentransformasi fitur ke mean=0, std=1")
    print("  Catatan: scaler di-fit HANYA pada training data (hindari data leakage)")

    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)   # fit + transform
    X_test_scaled  = scaler.transform(X_test)         # hanya transform (tidak fit ulang)

    print("  [OK] Normalisasi selesai")

    # -------------------------------------------------------------------------
    # STEP 4: Training SVM
    # -------------------------------------------------------------------------
    print("\n[4/5] Training SVM...")
    print("  Konfigurasi:")
    print("    kernel        : rbf (Radial Basis Function)")
    print("    C             : 10  (regularization strength)")
    print("    gamma         : scale (adaptif berdasarkan variance data)")
    print("    probability   : True (Platt scaling untuk valid confidence score)")
    print("    class_weight  : balanced (handle class imbalance)")

    model = SVC(
        kernel='rbf',
        C=10,
        gamma='scale',
        probability=True,          # Aktifkan untuk predict_proba()
        random_state=42,
        class_weight='balanced',   # Handle bila jumlah sampel per kelas tidak sama
    )
    model.fit(X_train_scaled, y_train)
    print("  [OK] Training selesai!")

    # -------------------------------------------------------------------------
    # STEP 5: Evaluasi
    # -------------------------------------------------------------------------
    print("\n[5/5] Evaluasi model pada test set...")

    y_pred = model.predict(X_test_scaled)

    accuracy  = accuracy_score(y_test, y_pred)
    precision = precision_score(y_test, y_pred, average='weighted', zero_division=0)
    recall    = recall_score(y_test, y_pred, average='weighted', zero_division=0)
    f1        = f1_score(y_test, y_pred, average='weighted', zero_division=0)
    cm        = confusion_matrix(y_test, y_pred)

    print(f"\n  {'-' * 45}")
    print(f"  Accuracy  : {accuracy  * 100:.2f}%")
    print(f"  Precision : {precision * 100:.2f}%  (weighted)")
    print(f"  Recall    : {recall    * 100:.2f}%  (weighted)")
    print(f"  F1-Score  : {f1        * 100:.2f}%  (weighted)")
    print(f"  {'-' * 45}")

    print("\n  Classification Report:")
    print(classification_report(y_test, y_pred, target_names=CATEGORIES))

    print("  Confusion Matrix:")
    header = f"  {'':>20}" + "".join(f"  {c[:10]:>10}" for c in CATEGORIES)
    print(header)
    for i, cat in enumerate(CATEGORIES):
        row = f"  {cat:>20}" + "".join(f"  {cm[i][j]:>10}" for j in range(len(CATEGORIES)))
        print(row)

    # -------------------------------------------------------------------------
    # Simpan Model, Scaler, dan Eval Report
    # -------------------------------------------------------------------------
    os.makedirs(os.path.dirname(model_save_path), exist_ok=True)

    with open(model_save_path, 'wb') as f:
        pickle.dump(model, f)
    print(f"\n  [OK] Model disimpan  : {model_save_path}")

    with open(scaler_save_path, 'wb') as f:
        pickle.dump(scaler, f)
    print(f"  [OK] Scaler disimpan : {scaler_save_path}")

    # -------------------------------------------------------------------------
    # Hitung rata-rata fitur GLCM per kelas (untuk ditampilkan di UI)
    # -------------------------------------------------------------------------
    FEATURE_NAMES = [
        'Contrast (mean)', 'Correlation (mean)', 'Energy (mean)',
        'Homogeneity (mean)', 'ASM (mean)', 'Dissimilarity (mean)',
        'Contrast (std)', 'Correlation (std)', 'Energy (std)',
        'Homogeneity (std)', 'ASM (std)', 'Dissimilarity (std)',
    ]
    glcm_class_stats = {}
    for i, cat in enumerate(CATEGORIES):
        mask = y == i
        class_features = X[mask]
        glcm_class_stats[cat] = {
            name: round(float(class_features[:, j].mean()), 6)
            for j, name in enumerate(FEATURE_NAMES)
        }

    # Simpan eval report sebagai JSON untuk ditampilkan di UI
    eval_report = {
        'accuracy':          round(accuracy  * 100, 2),
        'precision':         round(precision * 100, 2),
        'recall':            round(recall    * 100, 2),
        'f1_score':          round(f1        * 100, 2),
        'confusion_matrix':  cm.tolist(),
        'categories':        CATEGORIES,
        'n_train':           len(X_train),
        'n_test':            len(X_test),
        'n_features':        int(X.shape[1]),
        'glcm_class_stats':  glcm_class_stats,
        'model_params': {
            'kernel':       'rbf',
            'C':            10,
            'gamma':        'scale',
            'probability':  True,
            'class_weight': 'balanced',
        },
    }
    with open(report_save_path, 'w') as f:
        json.dump(eval_report, f, indent=2)
    print(f"  [OK] Eval report     : {report_save_path}")

    print(f"\n{sep}")
    print(f"  TRAINING SELESAI!  Akurasi: {accuracy * 100:.2f}%")
    print(f"{sep}\n")

    return model, scaler, accuracy


if __name__ == '__main__':
    dataset_path = 'dataset'
    try:
        model, scaler, accuracy = train_model(dataset_path)
        print(f"\n[OK] Model siap digunakan. Akurasi: {accuracy * 100:.2f}%")
    except Exception as e:
        import traceback
        print(f"\n[ERR] Error: {e}")
        traceback.print_exc()
