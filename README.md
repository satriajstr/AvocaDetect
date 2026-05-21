abis pull. bikin venv, aktifin. terus jalanin "pip install -r requirements.txt"
bikin struktur:
## Struktur Project

```text
AvocaDetect/
│
├── dataset/
│   ├── mentah/
│   ├── setengah_matang/
│   ├── matang/
│   └── terlalu_matang/
│
├── preprocessing/
│   ├── resize.py
│   ├── grayscale.py
│   ├── noise_reduction.py
│   └── segmentation.py
│
├── feature_extraction/
│   └── glcm.py
│
├── model/
│   ├── train_svm.py
│   └── test_svm.py
│
├── output/
│   ├── preprocessing/
│   ├── features/
│   └── results/
│
├── main.py
├── requirements.txt
└── README.md
```

## Library yang Digunakan

- OpenCV
- NumPy
- Matplotlib
- Scikit-image
- Scikit-learn
- Pandas

## Install Dependency

```bash
pip install -r requirements.txt
```

## Menjalankan Program

```bash
python main.py
```
