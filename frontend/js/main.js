// ===== AvocaDetect - Main JavaScript =====
// Aplikasi Klasifikasi Kematangan Alpukat
// 
// PERBAIKAN UI/UX POPUP HASIL ANALISA:
// - Responsive chart dengan deteksi ukuran layar
// - Layout mobile yang lebih proporsional
// - Animasi dan transisi yang smooth
// - Event listeners untuk ESC key dan click outside
// - Memory management untuk chart instances
// - Notifikasi dengan icon dan styling modern

// ===== Paksa scroll ke atas saat pertama kali load =====
// Tanpa ini, browser menyimpan posisi scroll sebelumnya
// sehingga tampilan awal berbeda dari klik "Beranda"
if ('scrollRestoration' in history) {
    history.scrollRestoration = 'manual';
}
window.scrollTo(0, 0);

// ===== Smooth Scrolling =====
function scrollToDetection() {
    const detectionSection = document.getElementById('detection');
    detectionSection.scrollIntoView({ behavior: 'smooth' });
}

// Smooth scroll untuk semua link navigasi
document.addEventListener('DOMContentLoaded', function() {
    const navLinks = document.querySelectorAll('.nav-link');
    
    navLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const targetId = this.getAttribute('href').substring(1);
            const targetSection = document.getElementById(targetId);
            
            if (targetSection) {
                targetSection.scrollIntoView({ behavior: 'smooth' });
            }
        });
    });
});

// ===== Handler untuk Upload Gambar =====
function handleUpload() {
    // Buat input file secara dinamis
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = 'image/*';
    
    input.onchange = function(e) {
        const file = e.target.files[0];
        if (file) {
            // Validasi tipe file
            if (!file.type.startsWith('image/')) {
                alert('Mohon pilih file gambar yang valid!');
                return;
            }
            
            // Preview gambar
            const reader = new FileReader();
            reader.onload = function(event) {
                displayImagePreview(event.target.result);
                showNotification('Gambar berhasil diupload! Klik tombol "Deteksi Kematangan" untuk memulai.', 'success');
            };
            reader.readAsDataURL(file);
        }
    };
    
    input.click();
}

// ===== Handler untuk Kamera =====
function handleCamera() {
    // Cek apakah browser mendukung getUserMedia
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        alert('Browser Anda tidak mendukung akses kamera!');
        return;
    }
    
    // Tampilkan loading
    const previewContainer = document.querySelector('.preview-placeholder');
    previewContainer.innerHTML = `
        <div style="text-align: center;">
            <div class="loading-spinner"></div>
            <p style="margin-top: 1rem;">Memuat daftar kamera...</p>
        </div>
    `;
    
    // Dapatkan daftar semua kamera yang tersedia
    navigator.mediaDevices.enumerateDevices()
        .then(function(devices) {
            const videoDevices = devices.filter(device => device.kind === 'videoinput');
            
            if (videoDevices.length === 0) {
                alert('Tidak ada kamera yang terdeteksi di perangkat Anda!');
                resetPreview();
                return;
            }
            
            // Tampilkan pilihan kamera
            showCameraSelection(videoDevices);
        })
        .catch(function(error) {
            console.error('Error enumerating devices:', error);
            alert('Gagal mengakses daftar kamera.');
            resetPreview();
        });
}

// ===== Fungsi untuk Menampilkan Pilihan Kamera =====
function showCameraSelection(videoDevices) {
    const previewContainer = document.querySelector('.preview-placeholder');
    
    let optionsHTML = '';
    videoDevices.forEach((device, index) => {
        const label = device.label || `Kamera ${index + 1}`;
        const isFrontCamera = label.toLowerCase().includes('front') || label.toLowerCase().includes('depan');
        const isBackCamera = label.toLowerCase().includes('back') || label.toLowerCase().includes('belakang') || label.toLowerCase().includes('rear');
        
        let displayLabel = label;
        if (isFrontCamera) {
            displayLabel = `📱 ${label} (Depan)`;
        } else if (isBackCamera) {
            displayLabel = `📷 ${label} (Belakang)`;
        }
        
        optionsHTML += `<option value="${device.deviceId}">${displayLabel}</option>`;
    });
    
    previewContainer.innerHTML = `
        <div style="text-align: center; padding: 2rem;">
            <h3 style="margin-bottom: 1rem; color: var(--dark-green);">Pilih Kamera</h3>
            <select id="cameraSelect" style="
                width: 100%;
                max-width: 400px;
                padding: 0.75rem;
                font-size: 1rem;
                border: 2px solid var(--primary-green);
                border-radius: 8px;
                margin-bottom: 1.5rem;
                font-family: 'Poppins', sans-serif;
                cursor: pointer;
            ">
                ${optionsHTML}
            </select>
            <div>
                <button class="btn-primary" onclick="startSelectedCamera()" style="margin-right: 10px;">📸 Buka Kamera</button>
                <button class="btn-secondary" onclick="resetPreview()">❌ Batal</button>
            </div>
        </div>
    `;
}

// ===== Fungsi untuk Memulai Kamera yang Dipilih =====
function startSelectedCamera() {
    const select = document.getElementById('cameraSelect');
    const deviceId = select.value;
    
    const constraints = {
        video: {
            deviceId: deviceId ? { exact: deviceId } : undefined,
            width: { ideal: 1920 },
            height: { ideal: 1080 }
        }
    };
    
    // Request akses kamera dengan device ID yang dipilih
    navigator.mediaDevices.getUserMedia(constraints)
        .then(function(stream) {
            // Buat elemen video untuk preview
            const previewContainer = document.querySelector('.preview-placeholder');
            previewContainer.innerHTML = `
                <video id="cameraStream" autoplay playsinline style="width: 100%; max-width: 500px; border-radius: 12px;"></video>
                <div style="margin-top: 1rem;">
                    <button class="btn-primary" onclick="capturePhoto()" style="margin-right: 10px;">📸 Ambil Foto</button>
                    <button class="btn-secondary" onclick="stopCamera()">❌ Tutup Kamera</button>
                </div>
            `;
            
            const video = document.getElementById('cameraStream');
            video.srcObject = stream;
            
            // Simpan stream untuk digunakan nanti
            window.currentStream = stream;
            
            showNotification('Kamera berhasil diaktifkan!', 'success');
        })
        .catch(function(error) {
            console.error('Error accessing camera:', error);
            alert('Gagal mengakses kamera. Pastikan Anda memberikan izin akses kamera.');
            resetPreview();
        });
}

// ===== Fungsi untuk Capture Foto dari Kamera =====
function capturePhoto() {
    const video = document.getElementById('cameraStream');
    if (!video) return;
    
    // Buat canvas untuk capture
    const canvas = document.createElement('canvas');
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    
    const context = canvas.getContext('2d');
    context.drawImage(video, 0, 0, canvas.width, canvas.height);
    
    // Konversi ke data URL
    const imageDataUrl = canvas.toDataURL('image/jpeg');
    
    // Stop kamera
    stopCamera();
    
    // Tampilkan hasil capture
    displayImagePreview(imageDataUrl);
    showNotification('Foto berhasil diambil! Klik tombol "Deteksi Kematangan" untuk memulai.', 'success');
}

// ===== Fungsi untuk Stop Kamera =====
function stopCamera() {
    if (window.currentStream) {
        window.currentStream.getTracks().forEach(track => track.stop());
        window.currentStream = null;
    }
    
    // Reset preview ke state awal
    resetPreview();
}

// ===== Fungsi untuk Display Image Preview =====
function displayImagePreview(imageUrl) {
    const previewContainer = document.querySelector('.preview-placeholder');
    previewContainer.innerHTML = `
        <img src="${imageUrl}" alt="Preview" style="max-width: 100%; max-height: 400px; border-radius: 12px; object-fit: contain;">
        <div style="margin-top: 1rem;">
            <button class="btn-secondary" onclick="resetPreview()">🔄 Ganti Gambar</button>
        </div>
    `;
    
    // Simpan image URL untuk deteksi
    window.currentImage = imageUrl;
}

// ===== Fungsi untuk Reset Preview =====
function resetPreview() {
    // Hapus gambar yang tersimpan
    window.currentImage = null;
    
    // Reset preview container ke state awal dengan icon kamera.png
    const previewContainer = document.querySelector('.preview-placeholder');
    if (!previewContainer) return;
    
    // Ambil base URL untuk path gambar
    const baseUrl = window.location.origin;
    
    previewContainer.innerHTML = `
        <img src="${baseUrl}/static/images/kamera.png" alt="camera" class="preview-icon-img" style="height: 10rem; width: auto; margin-bottom: 1rem;">
        <p>Area Preview Kamera</p>
        <p class="preview-hint">Upload gambar atau aktifkan kamera</p>
    `;
}

// ===== Handler untuk Deteksi =====
function handleDetect() {
    if (!window.currentImage) {
        showPopup('Gambar tidak ditemukan', 'error', 2000);
        return;
    }
    
    // Tampilkan loading popup
    showLoadingPopup();
    
    fetch(window.currentImage)
        .then(res => res.blob())
        .then(blob => {
            const formData = new FormData();
            formData.append('image', blob, 'image.jpg');
            
            return fetch('/detect', {
                method: 'POST',
                body: formData
            });
        })
        .then(response => response.json())
        .then(data => {
            // Tutup loading popup
            hideLoadingPopup();
            
            if (data.success) {
                showResultPopup(data.result, data.images);
            } else {
                showPopup(data.error, 'error', 2000);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            hideLoadingPopup();
            showPopup('Terjadi kesalahan saat memproses gambar', 'error', 2000);
        });
}

// ===== Fungsi untuk Loading Popup =====
function showLoadingPopup() {
    const loadingOverlay = document.createElement('div');
    loadingOverlay.id = 'loadingOverlay';
    loadingOverlay.className = 'loading-overlay';
    
    // Ambil base URL dari window.location
    const baseUrl = window.location.origin;
    
    loadingOverlay.innerHTML = `
        <div class="loading-popup">
            <div class="loading-avocado">🥑</div>
            <p class="loading-text">Sedang menganalisis...</p>
        </div>
    `;
    
    document.body.appendChild(loadingOverlay);
    setTimeout(() => loadingOverlay.classList.add('active'), 10);
}

function hideLoadingPopup() {
    const loadingOverlay = document.getElementById('loadingOverlay');
    if (loadingOverlay) {
        loadingOverlay.classList.remove('active');
        setTimeout(() => loadingOverlay.remove(), 300);
    }
}

// ===== Fungsi untuk Display Hasil Deteksi =====
function displayResults(results) {
    const resultContent = document.querySelector('.result-content');
    
    // Urutkan berdasarkan confidence tertinggi
    results.sort((a, b) => b.confidence - a.confidence);
    
    let html = '<div style="width: 100%;">';
    
    results.forEach(result => {
        html += `
            <div style="margin-bottom: 1.5rem;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                    <span style="font-weight: 600; color: var(--dark-green);">${result.label}</span>
                    <span style="font-weight: 700; color: ${result.color};">${result.confidence}%</span>
                </div>
                <div style="background: var(--gray-light); height: 12px; border-radius: 6px; overflow: hidden;">
                    <div style="background: ${result.color}; height: 100%; width: ${result.confidence}%; transition: width 0.5s ease;"></div>
                </div>
            </div>
        `;
    });
    
    // Tambahkan kesimpulan
    const topResult = results[0];
    html += `
        <div style="margin-top: 2rem; padding: 1.5rem; background: linear-gradient(135deg, var(--cream), var(--gray-light)); border-radius: 8px; border-left: 4px solid ${topResult.color};">
            <h4 style="color: var(--dark-green); margin-bottom: 0.5rem;">Kesimpulan:</h4>
            <p style="font-size: 1.1rem; font-weight: 600; color: ${topResult.color};">
                Alpukat terdeteksi dalam kondisi <strong>${topResult.label}</strong> dengan tingkat kepercayaan ${topResult.confidence}%
            </p>
        </div>
    `;
    
    html += '</div>';
    
    resultContent.innerHTML = html;
}

// ===== Fungsi untuk Popup Hasil =====
function showResultPopup(result, images) {
    const overlay = document.createElement('div');
    overlay.className = 'popup-overlay';
    
    const colorMap = {
        'Mentah': '#FF6B6B',
        'Setengah Matang': '#FFA94D',
        'Matang': '#51CF66',
        'Terlalu Matang': '#B34D4D'
    };
    
    const categoryColor = colorMap[result.category] || '#51CF66';
    
    overlay.innerHTML = `
        <div class="popup-content-modern">
            <button class="popup-close" onclick="closePopup()">&times;</button>
            
            <!-- Header -->
            <div class="popup-header">
                <div class="header-badge">Hasil Analisis</div>
                <h2>Klasifikasi Kematangan Alpukat</h2>
                <p class="popup-subtitle">Pipeline: Input → Resize → Grayscale → Noise Reduction → Segmentasi → GLCM → SVM</p>
            </div>
            
            <!-- Hasil Utama -->
            <div class="result-main-card" style="border-color: ${categoryColor};">
                <div class="result-icon" style="background: ${categoryColor}20;">
                    <span style="color: ${categoryColor};">🥑</span>
                </div>
                <div class="result-info">
                    <div class="result-label">Tingkat Kematangan</div>
                    <div class="result-category-row">
                        <div class="result-category" style="color: ${categoryColor};">${result.category}</div>
                        <div class="result-confidence-badge" style="background: ${categoryColor}; color: white;">
                            <span class="confidence-icon">✓</span>
                            <span>${result.confidence.toFixed(1)}%</span>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Probabilitas Chart -->
            <div class="probabilities-card">
                <h3 class="card-title">Distribusi Probabilitas</h3>
                <div class="prob-content">
                    <div class="prob-chart-section">
                        <canvas id="probChart"></canvas>
                    </div>
                    <div class="prob-legend-section">
                        ${Object.entries(result.probabilities).map(([cat, prob]) => `
                            <div class="legend-item-modern">
                                <div class="legend-left">
                                    <span class="legend-dot" style="background: ${colorMap[cat] || '#999'};"></span>
                                    <span class="legend-label">${cat}</span>
                                </div>
                                <div class="legend-right">
                                    <span class="legend-value">${prob.toFixed(1)}%</span>
                                    <div class="legend-bar">
                                        <div class="legend-bar-fill" style="width: ${prob}%; background: ${colorMap[cat] || '#999'};"></div>
                                    </div>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                </div>
            </div>
            
            <!-- Pipeline Images -->
            <div class="pipeline-card">
                <h3 class="card-title">Tahapan Preprocessing & Analisis</h3>
                <div class="pipeline-grid">
                    <div class="pipeline-item">
                        <div class="pipeline-image-wrapper">
                            <img src="${images.original}" alt="Original">
                        </div>
                        <div class="pipeline-label">
                            <span class="pipeline-number">1</span>
                            <span class="pipeline-text">Citra Asli</span>
                        </div>
                    </div>
                    <div class="pipeline-item">
                        <div class="pipeline-image-wrapper">
                            <img src="${images.grayscale}" alt="Grayscale">
                        </div>
                        <div class="pipeline-label">
                            <span class="pipeline-number">2</span>
                            <span class="pipeline-text">Grayscale</span>
                        </div>
                    </div>
                    <div class="pipeline-item">
                        <div class="pipeline-image-wrapper">
                            <img src="${images.denoised}" alt="Denoised">
                        </div>
                        <div class="pipeline-label">
                            <span class="pipeline-number">3</span>
                            <span class="pipeline-text">Noise Reduction</span>
                        </div>
                    </div>
                    <div class="pipeline-item">
                        <div class="pipeline-image-wrapper">
                            <img src="${images.segmentation}" alt="Segmentation">
                        </div>
                        <div class="pipeline-label">
                            <span class="pipeline-number">4</span>
                            <span class="pipeline-text">Segmentasi</span>
                        </div>
                    </div>
                    <div class="pipeline-item pipeline-item-glcm">
                        <div class="pipeline-image-wrapper glcm-wrapper">
                            <img src="${images.glcm}" alt="GLCM" class="glcm-heatmap">
                        </div>
                        <div class="pipeline-label">
                            <span class="pipeline-number">5</span>
                            <span class="pipeline-text">GLCM Matrix</span>
                        </div>
                        <!-- Footer card GLCM dengan info lengkap -->
                        <div class="glcm-footer">
                            <!-- Parameter GLCM -->
                            <div class="glcm-params-row">
                                <span class="glcm-param-label">Config:</span>
                                <div class="glcm-params-badges">
                                    <span class="glcm-badge" title="Distance: jarak antar piksel">D=1</span>
                                    <span class="glcm-badge" title="Angles: 0°, 45°, 90°, 135°">θ=4</span>
                                    <span class="glcm-badge" title="Levels: kuantisasi grayscale">L=32</span>
                                </div>
                            </div>
                            <!-- Color scale horizontal -->
                            <div class="glcm-colorscale-horizontal">
                                <span class="scale-label">Intensity:</span>
                                <div class="scale-gradient-wrapper">
                                    <span class="scale-marker-inline">Low</span>
                                    <div class="scale-gradient"></div>
                                    <span class="scale-marker-inline">High</span>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="pipeline-item">
                        <div class="pipeline-image-wrapper">
                            <img src="${images.svm}" alt="SVM">
                        </div>
                        <div class="pipeline-label">
                            <span class="pipeline-number">6</span>
                            <span class="pipeline-text">Hasil SVM</span>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Action Button -->
            <button class="btn-analyze-again-modern" onclick="analyzeAgain()">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                    <polyline points="23 4 23 10 17 10"></polyline>
                    <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"></path>
                </svg>
                <span>Analisa Gambar Lain</span>
            </button>
        </div>
    `;
    
    document.body.appendChild(overlay);
    setTimeout(() => overlay.classList.add('active'), 10);
    
    // Render donut chart dengan responsive sizing
    setTimeout(() => {
        const ctx = document.getElementById('probChart');
        if (ctx) {
            const categories = Object.keys(result.probabilities);
            const values = Object.values(result.probabilities);
            const colors = categories.map(cat => colorMap[cat] || '#999');
            
            // Deteksi ukuran layar untuk responsive chart
            const isMobile = window.innerWidth <= 480;
            const isTablet = window.innerWidth > 480 && window.innerWidth <= 768;
            
            // Destroy chart sebelumnya jika ada
            if (window.currentChart) {
                window.currentChart.destroy();
            }
            
            // Buat chart baru dan simpan instance-nya
            window.currentChart = new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: categories,
                    datasets: [{
                        data: values,
                        backgroundColor: colors,
                        borderWidth: 0,
                        hoverBorderWidth: isMobile ? 2 : 3,
                        hoverBorderColor: '#fff',
                        borderRadius: 4
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: true,
                    aspectRatio: 1,
                    plugins: {
                        legend: {
                            display: false
                        },
                        tooltip: {
                            enabled: !isMobile, // Disable tooltip di mobile untuk performa
                            backgroundColor: 'rgba(0,0,0,0.85)',
                            padding: isMobile ? 8 : 12,
                            titleFont: {
                                size: isMobile ? 12 : 14,
                                weight: '600',
                                family: 'Poppins'
                            },
                            bodyFont: {
                                size: isMobile ? 11 : 13,
                                family: 'Poppins'
                            },
                            cornerRadius: 8,
                            displayColors: true,
                            callbacks: {
                                label: function(context) {
                                    return context.label + ': ' + context.parsed.toFixed(1) + '%';
                                }
                            }
                        }
                    },
                    cutout: isMobile ? '65%' : '70%',
                    animation: {
                        animateRotate: true,
                        animateScale: true,
                        duration: 800,
                        easing: 'easeInOutQuart'
                    },
                    interaction: {
                        intersect: false,
                        mode: 'nearest'
                    }
                }
            });
        }
    }, 100);
}

// ===== Fungsi untuk Close Popup =====
function closePopup() {
    const overlay = document.querySelector('.popup-overlay');
    if (overlay) {
        overlay.classList.remove('active');
        setTimeout(() => {
            overlay.remove();
            // Cleanup chart instance jika ada
            if (window.currentChart) {
                window.currentChart.destroy();
                window.currentChart = null;
            }
        }, 300);
    }
}

// ===== Event listener untuk ESC key =====
document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
        const overlay = document.querySelector('.popup-overlay');
        if (overlay) {
            closePopup();
        }
    }
});

// ===== Event listener untuk click outside popup =====
document.addEventListener('click', function(e) {
    if (e.target.classList.contains('popup-overlay')) {
        closePopup();
    }
});

// ===== Fungsi untuk Analisa Kembali =====
function analyzeAgain() {
    // Tutup popup hasil
    closePopup();
    
    // Reset preview - hapus gambar sebelumnya dan tampilkan icon kamera
    resetPreview();
    
    // Scroll ke section deteksi
    scrollToDetection();
}

// ===== Fungsi untuk Popup Sederhana =====
function showPopup(message, type = 'info', duration = 2000) {
    const popup = document.createElement('div');
    popup.className = 'simple-popup';
    
    const colors = {
        success: '#51CF66',
        error: '#FF6B6B',
        info: '#4DABF7'
    };
    
    popup.style.cssText = `
        position: fixed;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        background: ${colors[type] || colors.info};
        color: white;
        padding: 2rem 3rem;
        border-radius: 12px;
        box-shadow: 0 8px 30px rgba(0,0,0,0.3);
        z-index: 10000;
        font-size: 1.1rem;
        font-weight: 600;
        text-align: center;
        animation: popupFadeIn 0.3s ease;
    `;
    
    popup.textContent = message;
    document.body.appendChild(popup);
    
    setTimeout(() => {
        popup.style.animation = 'popupFadeOut 0.3s ease';
        setTimeout(() => popup.remove(), 300);
    }, duration);
}

// ===== Fungsi untuk Notifikasi =====
function showNotification(message, type = 'info') {
    // Hapus notifikasi sebelumnya jika ada
    const existingNotif = document.querySelector('.notification');
    if (existingNotif) {
        existingNotif.style.animation = 'slideOutNotif 0.3s ease';
        setTimeout(() => existingNotif.remove(), 300);
    }
    
    // Buat elemen notifikasi
    const notification = document.createElement('div');
    notification.className = 'notification';
    
    // Icon berdasarkan tipe
    const icons = {
        success: '✓',
        error: '✕',
        info: 'ℹ'
    };
    
    // Styling berdasarkan tipe
    const colors = {
        success: '#51CF66',
        error: '#FF6B6B',
        info: '#4DABF7'
    };
    
    notification.innerHTML = `
        <div style="display: flex; align-items: center; gap: 0.75rem;">
            <span style="font-size: 1.25rem; font-weight: bold;">${icons[type] || icons.info}</span>
            <span style="flex: 1;">${message}</span>
        </div>
    `;
    
    notification.style.cssText = `
        position: fixed;
        top: 100px;
        right: 20px;
        background: ${colors[type] || colors.info};
        color: white;
        padding: 1rem 1.5rem;
        border-radius: 12px;
        box-shadow: 0 8px 24px rgba(0,0,0,0.2);
        z-index: 9999;
        max-width: 320px;
        font-weight: 500;
        font-size: 0.95rem;
        line-height: 1.4;
        font-family: 'Poppins', sans-serif;
    `;
    
    document.body.appendChild(notification);
    
    // Hapus setelah 3 detik
    setTimeout(() => {
        notification.style.animation = 'slideOutNotif 0.3s ease';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

// ===== CSS untuk Loading Spinner dan Popup =====
const style = document.createElement('style');
style.textContent = `
    .loading-overlay {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0, 0, 0, 0.7);
        backdrop-filter: blur(5px);
        z-index: 10000;
        display: flex;
        justify-content: center;
        align-items: center;
        opacity: 0;
        transition: opacity 0.3s ease;
    }
    
    .loading-overlay.active {
        opacity: 1;
    }
    
    .loading-popup {
        background: white;
        padding: 3rem 4rem;
        border-radius: 24px;
        box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        text-align: center;
        transform: scale(0.9);
        transition: transform 0.3s ease;
    }
    
    .loading-overlay.active .loading-popup {
        transform: scale(1);
    }
    
    .loading-avocado {
        font-size: 120px;
        animation: floatLoading 2s ease-in-out infinite;
        margin-bottom: 1rem;
        line-height: 1;
    }
    
    @keyframes floatLoading {
        0%, 100% {
            transform: translateY(0);
        }
        50% {
            transform: translateY(-20px);
        }
    }
    
    .loading-text {
        font-size: 1.2rem;
        font-weight: 600;
        color: #556B2F;
        margin: 0;
        font-family: 'Poppins', sans-serif;
    }
    
    .loading-spinner {
        border: 4px solid var(--gray-light);
        border-top: 4px solid var(--primary-green);
        border-radius: 50%;
        width: 50px;
        height: 50px;
        animation: spin 1s linear infinite;
        margin: 0 auto;
    }
    
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    
    @keyframes slideIn {
        from {
            transform: translateX(400px);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(400px);
            opacity: 0;
        }
    }
    
    @keyframes popupFadeIn {
        from {
            opacity: 0;
            transform: translate(-50%, -50%) scale(0.8);
        }
        to {
            opacity: 1;
            transform: translate(-50%, -50%) scale(1);
        }
    }
    
    @keyframes popupFadeOut {
        from {
            opacity: 1;
            transform: translate(-50%, -50%) scale(1);
        }
        to {
            opacity: 0;
            transform: translate(-50%, -50%) scale(0.8);
        }
    }
    
    .popup-overlay {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0, 0, 0, 0.85);
        backdrop-filter: blur(8px);
        z-index: 9999;
        display: flex;
        justify-content: center;
        align-items: center;
        opacity: 0;
        transition: opacity 0.3s ease;
        padding: 1rem;
        overflow-y: auto;
    }
    
    .popup-overlay.active {
        opacity: 1;
    }
    
    /* Container Popup Modern */
    .popup-content-modern {
        background: #ffffff;
        border-radius: 20px;
        padding: 0;
        max-width: 900px;
        width: 100%;
        max-height: 95vh;
        overflow-y: auto;
        position: relative;
        box-shadow: 0 25px 50px rgba(0,0,0,0.3);
        transform: scale(0.95);
        transition: transform 0.3s ease;
        font-family: 'Poppins', sans-serif;
    }
    
    .popup-overlay.active .popup-content-modern {
        transform: scale(1);
    }
    
    /* Scrollbar Custom */
    .popup-content-modern::-webkit-scrollbar {
        width: 8px;
    }
    
    .popup-content-modern::-webkit-scrollbar-track {
        background: #f1f1f1;
        border-radius: 10px;
    }
    
    .popup-content-modern::-webkit-scrollbar-thumb {
        background: #6B8E23;
        border-radius: 10px;
    }
    
    .popup-content-modern::-webkit-scrollbar-thumb:hover {
        background: #556B2F;
    }
    
    /* Close Button */
    .popup-close {
        position: sticky;
        top: 1rem;
        right: 1rem;
        float: right;
        background: rgba(255, 255, 255, 0.95);
        border: none;
        font-size: 1.5rem;
        color: #333;
        cursor: pointer;
        width: 36px;
        height: 36px;
        display: flex;
        align-items: center;
        justify-content: center;
        border-radius: 50%;
        transition: all 0.3s ease;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        z-index: 10;
        margin: 1rem 1rem 0 0;
    }
    
    .popup-close:hover {
        background: #f5f5f5;
        transform: rotate(90deg) scale(1.1);
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
    
    /* Header Section */
    .popup-header {
        text-align: center;
        padding: 2rem 2rem 1.5rem;
        background: linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%);
        border-bottom: 1px solid #e9ecef;
    }
    
    .header-badge {
        display: inline-block;
        background: linear-gradient(135deg, #6B8E23, #9ACD32);
        color: white;
        padding: 0.4rem 1.2rem;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 0.75rem;
    }
    
    .popup-header h2 {
        font-size: 1.5rem;
        font-weight: 700;
        color: #2d3748;
        margin: 0 0 0.5rem 0;
        line-height: 1.3;
    }
    
    .popup-subtitle {
        font-size: 0.8rem;
        color: #718096;
        font-weight: 400;
        margin: 0;
        line-height: 1.5;
    }
    
    /* Card Hasil Utama */
    .result-main-card {
        margin: 1.5rem;
        padding: 1.5rem;
        background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
        border-radius: 16px;
        border-left: 4px solid #6B8E23;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        display: flex;
        align-items: center;
        gap: 1.25rem;
    }
    
    .result-icon {
        width: 70px;
        height: 70px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 2.5rem;
        flex-shrink: 0;
    }
    
    .result-info {
        flex: 1;
    }
    
    .result-label {
        font-size: 0.75rem;
        color: #718096;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        font-weight: 600;
        margin-bottom: 0.5rem;
    }
    
    .result-category-row {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 1rem;
    }
    
    .result-category {
        font-size: 1.75rem;
        font-weight: 700;
        line-height: 1.2;
        flex: 1;
    }
    
    .result-confidence-badge {
        display: inline-flex;
        align-items: center;
        gap: 0.4rem;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
        flex-shrink: 0;
        white-space: nowrap;
    }
    
    .confidence-icon {
        font-size: 1rem;
        font-weight: bold;
    }
    
    /* Card Probabilitas */
    .probabilities-card {
        margin: 1.5rem;
        padding: 1.5rem;
        background: white;
        border-radius: 16px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
        border: 1px solid #e9ecef;
    }
    
    .card-title {
        font-size: 1rem;
        font-weight: 600;
        color: #2d3748;
        margin: 0 0 1.25rem 0;
        padding-bottom: 0.75rem;
        border-bottom: 2px solid #e9ecef;
    }
    
    .prob-content {
        display: grid;
        grid-template-columns: 200px 1fr;
        gap: 2rem;
        align-items: center;
    }
    
    .prob-chart-section {
        display: flex;
        justify-content: center;
        align-items: center;
    }
    
    .prob-chart-section canvas {
        max-width: 200px;
        max-height: 200px;
    }
    
    .prob-legend-section {
        display: flex;
        flex-direction: column;
        gap: 0.75rem;
    }
    
    .legend-item-modern {
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: 1rem;
        padding: 0.75rem;
        background: #f8f9fa;
        border-radius: 10px;
        transition: all 0.2s ease;
    }
    
    .legend-item-modern:hover {
        background: #e9ecef;
        transform: translateX(4px);
    }
    
    .legend-left {
        display: flex;
        align-items: center;
        gap: 0.6rem;
        flex: 1;
        min-width: 0;
    }
    
    .legend-dot {
        width: 14px;
        height: 14px;
        border-radius: 50%;
        flex-shrink: 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .legend-label {
        font-size: 0.85rem;
        font-weight: 500;
        color: #2d3748;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    
    .legend-right {
        display: flex;
        align-items: center;
        gap: 0.75rem;
        flex-shrink: 0;
    }
    
    .legend-value {
        font-size: 0.9rem;
        font-weight: 700;
        color: #2d3748;
        min-width: 50px;
        text-align: right;
    }
    
    .legend-bar {
        width: 60px;
        height: 6px;
        background: #e9ecef;
        border-radius: 3px;
        overflow: hidden;
    }
    
    .legend-bar-fill {
        height: 100%;
        border-radius: 3px;
        transition: width 0.5s ease;
    }
    
    /* Pipeline Card */
    .pipeline-card {
        margin: 1.5rem;
        padding: 1.5rem;
        background: white;
        border-radius: 16px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
        border: 1px solid #e9ecef;
    }
    
    .pipeline-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 1rem;
        margin-top: 1rem;
    }
    
    .pipeline-item {
        background: #f8f9fa;
        border-radius: 12px;
        overflow: hidden;
        transition: all 0.3s ease;
        border: 2px solid transparent;
    }
    
    .pipeline-item:hover {
        transform: translateY(-4px);
        box-shadow: 0 8px 16px rgba(0,0,0,0.1);
        border-color: #6B8E23;
    }
    
    .pipeline-image-wrapper {
        width: 100%;
        aspect-ratio: 1;
        overflow: hidden;
        background: white;
    }
    
    .pipeline-image-wrapper img {
        width: 100%;
        height: 100%;
        object-fit: cover;
    }
    
    .pipeline-label {
        padding: 0.75rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
        background: white;
    }
    
    .pipeline-number {
        width: 24px;
        height: 24px;
        background: linear-gradient(135deg, #6B8E23, #9ACD32);
        color: white;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 0.75rem;
        font-weight: 700;
        flex-shrink: 0;
    }
    
    .pipeline-text {
        font-size: 0.8rem;
        font-weight: 600;
        color: #2d3748;
        line-height: 1.2;
    }
    
    /* Button Analyze Again */
    .btn-analyze-again-modern {
        width: calc(100% - 3rem);
        margin: 1.5rem;
        background: linear-gradient(135deg, #6B8E23, #9ACD32);
        color: white;
        padding: 1rem 2rem;
        border: none;
        border-radius: 12px;
        font-size: 1rem;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.3s ease;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 0.75rem;
        box-shadow: 0 4px 12px rgba(107, 142, 35, 0.3);
        font-family: 'Poppins', sans-serif;
        position: relative;
        overflow: hidden;
    }
    
    .btn-analyze-again-modern::before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.3), transparent);
        transition: left 0.6s;
    }
    
    .btn-analyze-again-modern:hover::before {
        left: 100%;
    }
    
    .btn-analyze-again-modern:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(107, 142, 35, 0.4);
    }
    
    .btn-analyze-again-modern:active {
        transform: translateY(0);
    }
    
    .btn-analyze-again-modern svg {
        flex-shrink: 0;
    }
    
    /* ===== RESPONSIVE TABLET (max 768px) ===== */
    @media (max-width: 768px) {
        .popup-overlay {
            padding: 0.75rem;
            align-items: flex-start;
            overflow-y: auto;
        }
        
        .popup-content-modern {
            border-radius: 16px;
            max-height: none;
            margin: 1rem auto;
        }
        
        .popup-close {
            width: 34px;
            height: 34px;
            font-size: 1.4rem;
            margin: 0.85rem 0.85rem 0 0;
        }
        
        .popup-header {
            padding: 1.75rem 1.25rem 1.25rem;
        }
        
        .header-badge {
            font-size: 0.7rem;
            padding: 0.35rem 1rem;
        }
        
        .popup-header h2 {
            font-size: 1.3rem;
        }
        
        .popup-subtitle {
            font-size: 0.75rem;
            line-height: 1.4;
        }
        
        /* Card Hasil Utama Tablet */
        .result-main-card {
            margin: 1.25rem;
            padding: 1.5rem;
            gap: 1.25rem;
        }
        
        .result-icon {
            width: 65px;
            height: 65px;
            font-size: 2.25rem;
        }
        
        .result-category-row {
            flex-direction: column;
            align-items: flex-start;
            gap: 0.75rem;
        }
        
        .result-category {
            font-size: 1.6rem;
        }
        
        .result-confidence-badge {
            font-size: 0.85rem;
            padding: 0.4rem 0.9rem;
        }
        
        /* Probabilitas Tablet */
        .probabilities-card {
            margin: 1.25rem;
            padding: 1.5rem;
        }
        
        .card-title {
            font-size: 0.95rem;
            margin-bottom: 1.25rem;
        }
        
        .prob-content {
            grid-template-columns: 1fr;
            gap: 1.75rem;
        }
        
        .prob-chart-section {
            padding: 1rem 0;
        }
        
        .prob-chart-section canvas {
            max-width: 200px;
            max-height: 200px;
        }
        
        .legend-item-modern {
            padding: 0.75rem;
            gap: 0.85rem;
        }
        
        .legend-label {
            font-size: 0.85rem;
        }
        
        .legend-value {
            font-size: 0.9rem;
            min-width: 50px;
        }
        
        .legend-bar {
            width: 60px;
        }
        
        /* Pipeline Tablet */
        .pipeline-card {
            margin: 1.25rem;
            padding: 1.5rem;
        }
        
        .pipeline-grid {
            grid-template-columns: repeat(2, 1fr);
            gap: 1rem;
        }
        
        .pipeline-label {
            padding: 0.75rem;
        }
        
        .pipeline-number {
            width: 24px;
            height: 24px;
            font-size: 0.75rem;
        }
        
        .pipeline-text {
            font-size: 0.8rem;
        }
        
        /* Button Tablet */
        .btn-analyze-again-modern {
            width: calc(100% - 2.5rem);
            margin: 1.25rem;
            padding: 1rem 1.75rem;
            font-size: 0.95rem;
        }
    }
    
    /* ===== RESPONSIVE MOBILE (max 480px) ===== */
    @media (max-width: 480px) {
        .popup-overlay {
            padding: 0.5rem;
            align-items: flex-start;
        }
        
        .popup-content-modern {
            border-radius: 12px;
            margin: 0.5rem auto;
        }
        
        .popup-close {
            width: 30px;
            height: 30px;
            font-size: 1.25rem;
            margin: 0.65rem 0.65rem 0 0;
        }
        
        .popup-header {
            padding: 1.25rem 0.85rem 1rem;
        }
        
        .header-badge {
            font-size: 0.65rem;
            padding: 0.3rem 0.85rem;
            margin-bottom: 0.6rem;
        }
        
        .popup-header h2 {
            font-size: 1.05rem;
            line-height: 1.35;
            padding: 0 0.25rem;
        }
        
        .popup-subtitle {
            font-size: 0.65rem;
            line-height: 1.5;
            padding: 0 0.25rem;
        }
        
        /* Card Hasil Utama Mobile */
        .result-main-card {
            margin: 0.85rem;
            padding: 1.15rem 0.85rem;
            flex-direction: column;
            text-align: center;
            gap: 0.85rem;
        }
        
        .result-icon {
            width: 55px;
            height: 55px;
            font-size: 1.85rem;
            margin: 0 auto;
        }
        
        .result-label {
            font-size: 0.7rem;
        }
        
        .result-category-row {
            flex-direction: column;
            align-items: center;
            gap: 0.65rem;
        }
        
        .result-category {
            font-size: 1.35rem;
            line-height: 1.3;
        }
        
        .result-confidence-badge {
            font-size: 0.75rem;
            padding: 0.35rem 0.75rem;
            gap: 0.35rem;
        }
        
        /* Probabilitas Mobile */
        .probabilities-card {
            margin: 0.85rem;
            padding: 1rem 0.85rem;
        }
        
        .card-title {
            font-size: 0.85rem;
            margin-bottom: 1rem;
            padding-bottom: 0.65rem;
        }
        
        .prob-content {
            grid-template-columns: 1fr;
            gap: 1.25rem;
        }
        
        .prob-chart-section {
            padding: 0.5rem 0;
        }
        
        .prob-chart-section canvas {
            max-width: 160px !important;
            max-height: 160px !important;
        }
        
        .prob-legend-section {
            gap: 0.65rem;
        }
        
        .legend-item-modern {
            padding: 0.65rem 0.75rem;
            gap: 0.65rem;
            flex-wrap: wrap;
        }
        
        .legend-left {
            gap: 0.5rem;
            flex: 0 0 auto;
            min-width: 120px;
        }
        
        .legend-dot {
            width: 12px;
            height: 12px;
        }
        
        .legend-label {
            font-size: 0.75rem;
            white-space: normal;
            line-height: 1.3;
        }
        
        .legend-right {
            gap: 0.6rem;
            flex: 1;
            min-width: 0;
            justify-content: flex-end;
        }
        
        .legend-value {
            font-size: 0.8rem;
            min-width: 42px;
            flex-shrink: 0;
        }
        
        .legend-bar {
            width: 45px;
            height: 5px;
            flex-shrink: 0;
        }
        
        /* Pipeline Mobile */
        .pipeline-card {
            margin: 0.85rem;
            padding: 1rem 0.85rem;
        }
        
        .pipeline-grid {
            grid-template-columns: repeat(2, 1fr);
            gap: 0.65rem;
        }
        
        .pipeline-item {
            border-radius: 10px;
        }
        
        .pipeline-label {
            padding: 0.6rem 0.5rem;
            gap: 0.4rem;
        }
        
        .pipeline-number {
            width: 20px;
            height: 20px;
            font-size: 0.65rem;
        }
        
        .pipeline-text {
            font-size: 0.7rem;
            line-height: 1.25;
        }
        
        /* Button Mobile */
        .btn-analyze-again-modern {
            width: calc(100% - 1.7rem);
            margin: 0.85rem;
            padding: 0.85rem 1.25rem;
            font-size: 0.85rem;
            gap: 0.6rem;
        }
        
        .btn-analyze-again-modern svg {
            width: 18px;
            height: 18px;
        }
    }
    
    .popup-images-grid-6 {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 1rem;
        margin-bottom: 2rem;
    }
    
    .popup-image-item {
        text-align: center;
    }
    
    .popup-image-item img {
        width: 100%;
        height: auto;
        border-radius: 12px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        margin-bottom: 0.5rem;
        border: 2px solid #f0f0f0;
    }
    
    .popup-image-item p {
        font-size: 0.8rem;
        font-weight: 600;
        color: #555;
    }
    
    .popup-result-modern {
        background: linear-gradient(135deg, #fafafa, #f5f5f5);
        padding: 1.75rem 2rem;
        border-radius: 18px;
        border-left: 5px solid #6B8E23;
        margin-bottom: 1.5rem;
        box-shadow: 0 2px 12px rgba(0,0,0,0.06);
    }
    
    .result-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 1.75rem;
        padding-bottom: 0;
        border-bottom: none;
    }
    
    .result-category {
        font-size: 1.75rem;
        font-weight: 700;
        letter-spacing: -0.5px;
    }
    
    .result-confidence {
        text-align: right;
        display: flex;
        align-items: baseline;
        gap: 0.5rem;
    }
    
    .confidence-label {
        font-size: 0.7rem;
        color: #888;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .confidence-value {
        font-size: 1.75rem;
        font-weight: 700;
    }
    
    .probabilities-modern {
        background: white;
        padding: 1.5rem;
        border-radius: 14px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
    }
    
    .probabilities-modern h4 {
        font-size: 0.75rem;
        font-weight: 600;
        color: #666;
        margin-bottom: 1.25rem;
        text-transform: uppercase;
        letter-spacing: 0.8px;
        text-align: center;
    }
    
    .prob-chart-container {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 2rem;
        flex-wrap: wrap;
    }
    
    .prob-chart-wrapper {
        width: 180px;
        height: 180px;
        flex-shrink: 0;
    }
    
    .prob-legend {
        display: flex;
        flex-direction: column;
        gap: 0.75rem;
        flex: 1;
        min-width: 200px;
    }
    
    .legend-item {
        display: flex;
        align-items: center;
        gap: 0.6rem;
    }
    
    .legend-dot {
        width: 12px;
        height: 12px;
        border-radius: 50%;
        flex-shrink: 0;
    }
    
    .legend-label {
        font-size: 0.85rem;
        font-weight: 500;
        color: #333;
        flex: 1;
    }
    
    .legend-value {
        font-size: 0.8rem;
        font-weight: 600;
        color: #666;
    }
    
    .btn-analyze-again {
        width: 100%;
        max-width: 350px;
        margin: 1rem auto 0;
        background: linear-gradient(135deg, #5a7a1f, #7fb82e);
        color: white;
        padding: 0.7rem 1.5rem;
        border: none;
        border-radius: 50px;
        font-size: 0.9rem;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.3s ease;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 0.5rem;
        box-shadow: 0 3px 12px rgba(107, 142, 35, 0.25);
        font-family: 'Poppins', sans-serif;
        position: relative;
        overflow: hidden;
    }
    
    .btn-analyze-again::before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
        transition: left 0.5s;
    }
    
    .btn-analyze-again:hover::before {
        left: 100%;
    }
    
    .btn-analyze-again:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 24px rgba(107, 142, 35, 0.35);
    }
    
    .btn-analyze-again span:first-child {
        font-size: 1.1rem;
        filter: brightness(0) invert(1);
    }
    
    @media (max-width: 768px) {
        .loading-popup {
            padding: 2rem 2.5rem;
            margin: 0 1rem;
        }
        
        .loading-avocado {
            font-size: 80px;
        }
        
        .loading-text {
            font-size: 1rem;
        }
    }
`;

document.head.appendChild(style);