"""
Testing dan Prediksi Model SVM
"""

import os
import pickle
import numpy as np
import sys

# Tambahkan path root project
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

from backend.machine.feature_extraction.glcm import extract_glcm_features

def load_model(model_path='backend/machine/model/svm_model.pkl', 
               scaler_path='backend/machine/model/scaler.pkl'):
    """
    Load model SVM dan scaler yang sudah di-training
    
    Parameters:
    - model_path: path ke file model
    - scaler_path: path ke file scaler
    
    Returns:
    - model: trained SVM model
    - scaler: fitted StandardScaler
    """
    
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model tidak ditemukan di: {model_path}")
    
    if not os.path.exists(scaler_path):
        raise FileNotFoundError(f"Scaler tidak ditemukan di: {scaler_path}")
    
    with open(model_path, 'rb') as f:
        model = pickle.load(f)
    
    with open(scaler_path, 'rb') as f:
        scaler = pickle.load(f)
    
    return model, scaler

def predict_single_image(image_path, model=None, scaler=None):
    """
    Prediksi tingkat kematangan alpukat dari satu gambar
    
    Parameters:
    - image_path: path ke gambar
    - model: trained SVM model (optional, akan di-load jika None)
    - scaler: fitted StandardScaler (optional, akan di-load jika None)
    
    Returns:
    - prediction: label prediksi (0-3)
    - category: nama kategori
    - probabilities: probabilitas untuk setiap kelas (jika tersedia)
    """
    
    # Load model jika belum di-load
    if model is None or scaler is None:
        model, scaler = load_model()
    
    # Ekstraksi fitur dari gambar
    features = extract_glcm_features(image_path)
    
    # Normalisasi fitur
    features_scaled = scaler.transform(features)
    
    # Prediksi
    prediction = model.predict(features_scaled)[0]
    
    # Mapping label ke kategori
    categories = {
        0: 'Mentah',
        1: 'Setengah Matang',
        2: 'Matang',
        3: 'Terlalu Matang'
    }
    
    category = categories[prediction]
    
    # Hitung confidence (decision function)
    decision_values = model.decision_function(features_scaled)[0]
    
    # Konversi ke probabilitas sederhana (normalisasi)
    # Karena SVM tidak memberikan probabilitas langsung
    exp_values = np.exp(decision_values - np.max(decision_values))
    probabilities = exp_values / exp_values.sum()
    
    # Buat dictionary hasil
    result = {
        'prediction': int(prediction),
        'category': category,
        'confidence': float(probabilities[prediction] * 100),
        'probabilities': {
            'Mentah': float(probabilities[0] * 100),
            'Setengah Matang': float(probabilities[1] * 100),
            'Matang': float(probabilities[2] * 100),
            'Terlalu Matang': float(probabilities[3] * 100)
        }
    }
    
    return result

def predict_batch(image_paths, model=None, scaler=None):
    """
    Prediksi batch untuk multiple gambar
    
    Parameters:
    - image_paths: list of image paths
    - model: trained SVM model (optional)
    - scaler: fitted StandardScaler (optional)
    
    Returns:
    - results: list of prediction results
    """
    
    # Load model jika belum di-load
    if model is None or scaler is None:
        model, scaler = load_model()
    
    results = []
    
    for image_path in image_paths:
        try:
            result = predict_single_image(image_path, model, scaler)
            results.append({
                'image_path': image_path,
                'result': result,
                'success': True
            })
        except Exception as e:
            results.append({
                'image_path': image_path,
                'error': str(e),
                'success': False
            })
    
    return results

if __name__ == "__main__":
    # Contoh testing
    print("="*60)
    print("TESTING MODEL SVM")
    print("="*60)
    
    # Test dengan satu gambar
    test_image = "dataset/matang/IMG_1001_jpeg.rf.0e08cb13387d0b9d7b759c024b9ec016.jpg"
    
    if os.path.exists(test_image):
        print(f"\nTesting dengan gambar: {test_image}")
        
        try:
            result = predict_single_image(test_image)
            
            print(f"\nHasil Prediksi:")
            print(f"  Kategori: {result['category']}")
            print(f"  Confidence: {result['confidence']:.2f}%")
            print(f"\nProbabilitas semua kelas:")
            for category, prob in result['probabilities'].items():
                print(f"  {category}: {prob:.2f}%")
                
        except Exception as e:
            print(f"\nError: {str(e)}")
    else:
        print(f"\nGambar test tidak ditemukan: {test_image}")
        print("Silakan jalankan training terlebih dahulu dengan: python backend/machine/model/train_svm.py")
