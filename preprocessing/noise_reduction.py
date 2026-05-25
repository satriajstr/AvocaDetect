import cv2

def reduce_noise(image, kernel_size=(5, 5), sigma=0):
    """
    Terapkan Gaussian Blur untuk mengurangi noise pada gambar grayscale.
    kernel_size: ukuran kernel (harus ganjil), default (5,5)
    sigma: standar deviasi Gaussian, 0 = dihitung otomatis dari kernel
    """
    return cv2.GaussianBlur(image, kernel_size, sigma)
