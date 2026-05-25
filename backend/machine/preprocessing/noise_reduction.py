import numpy as np
from numpy.lib.stride_tricks import sliding_window_view

def get_gaussian_kernel_2d(kernel_size, sigma):
    k_h, k_w = kernel_size
    
    # Hitung sigma jika <= 0 (seperti di OpenCV)
    sigma_y = sigma if sigma > 0 else 0.3 * ((k_h - 1) * 0.5 - 1) + 0.8
    sigma_x = sigma if sigma > 0 else 0.3 * ((k_w - 1) * 0.5 - 1) + 0.8
    
    # Buat kernel 1D Gaussian
    ax_y = np.linspace(-(k_h - 1) / 2.0, (k_h - 1) / 2.0, k_h)
    ax_x = np.linspace(-(k_w - 1) / 2.0, (k_w - 1) / 2.0, k_w)
    
    kernel_y = np.exp(-0.5 * np.square(ax_y) / np.square(sigma_y))
    kernel_x = np.exp(-0.5 * np.square(ax_x) / np.square(sigma_x))
    
    # Normalisasi kernel 1D
    kernel_y /= np.sum(kernel_y)
    kernel_x /= np.sum(kernel_x)
    
    # Kalikan luar untuk mendapatkan kernel 2D
    return np.outer(kernel_y, kernel_x)

def _convolve2d(image, kernel):
    kh, kw = kernel.shape
    pad_h = kh // 2
    pad_w = kw // 2
    
    # Gunakan edge padding agar piksel tepi tidak menjadi hitam gelap
    padded = np.pad(image, ((pad_h, pad_h), (pad_w, pad_w)), mode='edge')
    
    # Gunakan sliding window view untuk konvolusi super cepat
    windows = sliding_window_view(padded, (kh, kw))
    
    # Hitung perkalian elemen-wise dan jumlahkan pada axis kernel
    blurred = np.sum(windows * kernel, axis=(2, 3))
    return np.clip(blurred, 0, 255).astype(np.uint8)

def reduce_noise(image, kernel_size=(5, 5), sigma=0):
    """
    Terapkan Gaussian Blur manual untuk mengurangi noise pada gambar (Grayscale atau Berwarna).
    kernel_size: tuple ukuran kernel (harus bernilai ganjil), default (5,5)
    sigma: standar deviasi Gaussian, jika 0 dihitung otomatis dari ukuran kernel
    """
    kernel = get_gaussian_kernel_2d(kernel_size, sigma)
    
    if len(image.shape) == 2:
        return _convolve2d(image, kernel)
    elif len(image.shape) == 3:
        # Proses per channel untuk gambar berwarna
        channels = []
        for c in range(image.shape[2]):
            channels.append(_convolve2d(image[:, :, c], kernel))
        return np.stack(channels, axis=-1)
        
    return image

