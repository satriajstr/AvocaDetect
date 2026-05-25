"""
Main script untuk menjalankan proses machine learning
Preprocessing -> Feature Extraction -> Training -> Testing
"""

import sys
import os

# Tambahkan path root ke sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.machine.model.train_svm import train_model
from backend.machine.model.test_svm import predict_single_image

def main():
    """
    Fungsi utama untuk menjalankan pipeline machine learning
    """
    print("=" * 60)
    print("AvocaDetect - Machine Learning Pipeline")
    print("=" * 60)
    
    print("\nPilih opsi:")
    print("1. Training model SVM")
    print("2. Test prediksi gambar")
    print("3. Exit")
    
    choice = input("\nMasukkan pilihan (1/2/3): ")
    
    if choice == '1':
        # Training model
        dataset_path = 'dataset'
        try:
            print("\nMemulai training...\n")
            model, scaler, accuracy = train_model(dataset_path)
            print(f"\n✓ Training selesai dengan akurasi {accuracy*100:.2f}%")
        except Exception as e:
            print(f"\n✗ Error saat training: {str(e)}")
    
    elif choice == '2':
        # Test prediksi
        image_path = input("\nMasukkan path gambar untuk diprediksi: ")
        
        if not os.path.exists(image_path):
            print(f"\n✗ File tidak ditemukan: {image_path}")
            return
        
        try:
            print("\nMemproses gambar...\n")
            result = predict_single_image(image_path)
            
            print("Hasil Prediksi:")
            print(f"  Kategori: {result['category']}")
            print(f"  Confidence: {result['confidence']:.2f}%")
            print(f"\nProbabilitas semua kelas:")
            for category, prob in result['probabilities'].items():
                print(f"  {category}: {prob:.2f}%")
        except Exception as e:
            print(f"\n✗ Error saat prediksi: {str(e)}")
    
    elif choice == '3':
        print("\nTerima kasih!")
    else:
        print("\n✗ Pilihan tidak valid!")

if __name__ == "__main__":
    main()
