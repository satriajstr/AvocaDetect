"""
Prediksi Model SVM - AvocaDetect
==================================
Load model yang sudah di-training dan lakukan prediksi kematangan alpukat.

Perbedaan dari versi lama:
- Menggunakan predict_proba() (Platt scaling) bukan softmax manual
  → confidence score lebih valid secara statistik
- Return juga feature_dict untuk ditampilkan sebagai tabel di UI

Author: AvocaDetect Team
"""

import os
import sys
import pickle
import numpy as np

# Path root project
sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
)

from backend.machine.feature_extraction.glcm import extract_glcm_features

# Label kategori
CATEGORIES = {
    0: 'Mentah',
    1: 'Setengah Matang',
    2: 'Matang',
    3: 'Terlalu Matang',
}


def load_model(
    model_path  = 'backend/machine/model/svm_model.pkl',
    scaler_path = 'backend/machine/model/scaler.pkl',
):
    """
    Load model SVM dan scaler dari file .pkl.

    Parameters
    ----------
    model_path  : str — path ke file model
    scaler_path : str — path ke file scaler

    Returns
    -------
    model  : trained SVC dengan probability=True
    scaler : fitted StandardScaler
    """
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model tidak ditemukan: {model_path}")
    if not os.path.exists(scaler_path):
        raise FileNotFoundError(f"Scaler tidak ditemukan: {scaler_path}")

    with open(model_path, 'rb') as f:
        model = pickle.load(f)

    with open(scaler_path, 'rb') as f:
        scaler = pickle.load(f)

    return model, scaler


def predict_single_image(image_path, model=None, scaler=None):
    """
    Prediksi tingkat kematangan alpukat dari satu gambar.

    Menggunakan predict_proba() (Platt scaling) yang diaktifkan
    saat training dengan probability=True.
    Hasilnya lebih valid dibanding softmax manual pada decision_function.

    Parameters
    ----------
    image_path : str — path ke file gambar
    model      : SVC (optional, di-load otomatis jika None)
    scaler     : StandardScaler (optional)

    Returns
    -------
    dict dengan keys:
        prediction   : int (0–3)
        category     : str
        confidence   : float (%)
        probabilities: dict {kategori: float(%)}
    """
    # Load model jika belum diberikan
    if model is None or scaler is None:
        model, scaler = load_model()

    # Ekstraksi fitur GLCM dari gambar
    features = extract_glcm_features(image_path)

    # Normalisasi fitur menggunakan scaler yang sudah di-fit saat training
    features_scaled = scaler.transform(features)

    # Prediksi kelas
    prediction = model.predict(features_scaled)[0]
    category   = CATEGORIES[prediction]

    # Confidence menggunakan predict_proba() (Platt scaling)
    # Lebih valid dibanding softmax manual karena dikalibrasi saat training
    probabilities_raw = model.predict_proba(features_scaled)[0]
    confidence        = float(probabilities_raw[prediction] * 100)

    result = {
        'prediction':    int(prediction),
        'category':      category,
        'confidence':    round(confidence, 2),
        'probabilities': {
            cat: round(float(probabilities_raw[i] * 100), 2)
            for i, cat in CATEGORIES.items()
        },
    }

    return result


def predict_batch(image_paths, model=None, scaler=None):
    """
    Prediksi batch untuk multiple gambar.

    Parameters
    ----------
    image_paths : list of str
    model       : SVC (optional)
    scaler      : StandardScaler (optional)

    Returns
    -------
    list of dicts dengan keys: image_path, result/error, success
    """
    if model is None or scaler is None:
        model, scaler = load_model()

    results = []
    for image_path in image_paths:
        try:
            result = predict_single_image(image_path, model, scaler)
            results.append({'image_path': image_path, 'result': result, 'success': True})
        except Exception as e:
            results.append({'image_path': image_path, 'error': str(e), 'success': False})

    return results


if __name__ == '__main__':
    print("=" * 60)
    print("TESTING MODEL SVM — AvocaDetect")
    print("=" * 60)

    test_image = "dataset/matang/IMG_1001_jpeg.rf.0e08cb13387d0b9d7b759c024b9ec016.jpg"

    if os.path.exists(test_image):
        try:
            result = predict_single_image(test_image)
            print(f"\nGambar    : {test_image}")
            print(f"Kategori  : {result['category']}")
            print(f"Confidence: {result['confidence']:.2f}%")
            print("\nProbabilitas:")
            for cat, prob in result['probabilities'].items():
                bar = '#' * int(prob / 5)
                print(f"  {cat:>18} : {prob:6.2f}%  {bar}")
        except Exception as e:
            import traceback
            print(f"Error: {e}")
            traceback.print_exc()
    else:
        print(f"\nGambar test tidak ditemukan: {test_image}")
        print("Jalankan training terlebih dahulu: python train_model.py")
