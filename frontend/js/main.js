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
    
    // Reset preview
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
    const previewContainer = document.querySelector('.preview-placeholder');
    previewContainer.innerHTML = `
        <span class="preview-icon">📷</span>
        <p>Area Preview Kamera</p>
        <p class="preview-hint">Upload gambar atau aktifkan kamera</p>
    `;
    
    window.currentImage = null;
}

// ===== Handler untuk Deteksi =====
function handleDetect() {
    if (!window.currentImage) {
        showPopup('Gambar tidak ditemukan', 'error', 2000);
        return;
    }
    
    showPopup('Sedang memproses...', 'info', 1000);
    
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
            if (data.success) {
                showResultPopup(data.result, data.images);
            } else {
                showPopup(data.error, 'error', 2000);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showPopup('Terjadi kesalahan saat memproses gambar', 'error', 2000);
        });
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
            
            <div class="popup-header">
                <h2>Hasil Analisis Klasifikasi</h2>
                <p class="popup-subtitle">Pipeline: Input → Resize → Grayscale → Noise Reduction → Segmentasi → GLCM → SVM</p>
            </div>
            
            <div class="popup-images-grid-6">
                <div class="popup-image-item">
                    <img src="${images.original}" alt="Original">
                    <p>1. Citra Asli</p>
                </div>
                <div class="popup-image-item">
                    <img src="${images.grayscale}" alt="Grayscale">
                    <p>2. Grayscale</p>
                </div>
                <div class="popup-image-item">
                    <img src="${images.denoised}" alt="Denoised">
                    <p>3. Noise Reduction</p>
                </div>
                <div class="popup-image-item">
                    <img src="${images.segmentation}" alt="Segmentation">
                    <p>4. Segmentasi</p>
                </div>
                <div class="popup-image-item">
                    <img src="${images.glcm}" alt="GLCM">
                    <p>5. GLCM Matrix</p>
                </div>
                <div class="popup-image-item">
                    <img src="${images.svm}" alt="SVM">
                    <p>6. Hasil SVM</p>
                </div>
            </div>
            
            <div class="popup-result-modern" style="border-left-color: ${categoryColor};">
                <div class="result-header">
                    <div class="result-category" style="color: ${categoryColor};">
                        ${result.category}
                    </div>
                    <div class="result-confidence">
                        <span class="confidence-label">Confidence</span>
                        <span class="confidence-value" style="color: ${categoryColor};">${result.confidence.toFixed(1)}%</span>
                    </div>
                </div>
                
                <div class="probabilities-modern">
                    <h4>Probabilitas Klasifikasi</h4>
                    <div class="prob-chart-container">
                        <div class="prob-chart-wrapper">
                            <canvas id="probChart"></canvas>
                        </div>
                        <div class="prob-legend">
                            ${Object.entries(result.probabilities).map(([cat, prob]) => `
                                <div class="legend-item">
                                    <span class="legend-dot" style="background: ${colorMap[cat] || '#999'};"></span>
                                    <span class="legend-label">${cat}</span>
                                    <span class="legend-value">${prob.toFixed(1)}%</span>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                </div>
            </div>
            
            <button class="btn-analyze-again" onclick="analyzeAgain()">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" style="flex-shrink: 0;">
                    <polyline points="23 4 23 10 17 10"></polyline>
                    <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"></path>
                </svg>
                <span>Analisa Kembali</span>
            </button>
        </div>
    `;
    
    document.body.appendChild(overlay);
    setTimeout(() => overlay.classList.add('active'), 10);
    
    // Render donut chart setelah DOM ready
    setTimeout(() => {
        const ctx = document.getElementById('probChart');
        if (ctx) {
            const categories = Object.keys(result.probabilities);
            const values = Object.values(result.probabilities);
            const colors = categories.map(cat => colorMap[cat] || '#999');
            
            new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: categories,
                    datasets: [{
                        data: values,
                        backgroundColor: colors,
                        borderWidth: 3,
                        borderColor: '#fff'
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: true,
                    plugins: {
                        legend: {
                            display: false
                        },
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    return context.label + ': ' + context.parsed.toFixed(1) + '%';
                                }
                            }
                        }
                    },
                    cutout: '65%'
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
        setTimeout(() => overlay.remove(), 300);
    }
}

// ===== Fungsi untuk Analisa Kembali =====
function analyzeAgain() {
    closePopup();
    resetPreview();
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
        existingNotif.remove();
    }
    
    // Buat elemen notifikasi
    const notification = document.createElement('div');
    notification.className = 'notification';
    notification.textContent = message;
    
    // Styling berdasarkan tipe
    const colors = {
        success: '#51CF66',
        error: '#FF6B6B',
        info: '#4DABF7'
    };
    
    notification.style.cssText = `
        position: fixed;
        top: 100px;
        right: 20px;
        background: ${colors[type] || colors.info};
        color: white;
        padding: 1rem 1.5rem;
        border-radius: 8px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        z-index: 9999;
        animation: slideIn 0.3s ease;
        max-width: 300px;
        font-weight: 500;
    `;
    
    document.body.appendChild(notification);
    
    // Hapus setelah 3 detik
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

// ===== CSS untuk Loading Spinner dan Popup =====
const style = document.createElement('style');
style.textContent = `
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
        background: rgba(0, 0, 0, 0.8);
        z-index: 9999;
        display: flex;
        justify-content: center;
        align-items: center;
        opacity: 0;
        transition: opacity 0.3s ease;
        padding: 20px;
        overflow-y: auto;
    }
    
    .popup-overlay.active {
        opacity: 1;
    }
    
    .popup-content-modern {
        background: white;
        border-radius: 24px;
        padding: 2.5rem;
        max-width: 1100px;
        width: 100%;
        max-height: 90vh;
        overflow-y: auto;
        position: relative;
        box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        transform: scale(0.9);
        transition: transform 0.3s ease;
        font-family: 'Poppins', sans-serif;
    }
    
    .popup-overlay.active .popup-content-modern {
        transform: scale(1);
    }
    
    .popup-close {
        position: absolute;
        top: 1.5rem;
        right: 1.5rem;
        background: #f5f5f5;
        border: none;
        font-size: 1.8rem;
        color: #333;
        cursor: pointer;
        width: 40px;
        height: 40px;
        display: flex;
        align-items: center;
        justify-content: center;
        border-radius: 50%;
        transition: all 0.3s ease;
    }
    
    .popup-close:hover {
        background: #e0e0e0;
        transform: rotate(90deg);
    }
    
    .popup-header {
        text-align: center;
        margin-bottom: 2rem;
    }
    
    .popup-header h2 {
        font-size: 1.8rem;
        font-weight: 700;
        color: #556B2F;
        margin-bottom: 0.5rem;
    }
    
    .popup-subtitle {
        font-size: 0.85rem;
        color: #666;
        font-weight: 400;
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
        .popup-content-modern {
            padding: 2rem 1.5rem;
            margin: 1rem;
        }
        
        .popup-images-grid-6 {
            grid-template-columns: repeat(2, 1fr);
            gap: 0.75rem;
        }
        
        .popup-header h2 {
            font-size: 1.5rem;
        }
        
        .popup-subtitle {
            font-size: 0.75rem;
        }
        
        .result-header {
            flex-direction: column;
            gap: 1rem;
            text-align: center;
        }
        
        .result-category {
            font-size: 1.5rem;
        }
        
        .confidence-value {
            font-size: 1.5rem;
        }
        
        .prob-chart-container {
            flex-direction: column;
            gap: 1.5rem;
        }
        
        .prob-chart-wrapper {
            width: 160px;
            height: 160px;
        }
        
        .prob-legend {
            width: 100%;
        }
        
        .popup-close {
            top: 1rem;
            right: 1rem;
        }
    }
`;
document.head.appendChild(style);

// ===== Navbar Scroll Effect =====
window.addEventListener('scroll', function() {
    const navbar = document.querySelector('.navbar');
    if (window.scrollY > 50) {
        navbar.style.boxShadow = '0 4px 20px rgba(0,0,0,0.15)';
    } else {
        navbar.style.boxShadow = '0 2px 10px rgba(0,0,0,0.1)';
    }
});

// ===== Console Welcome Message =====
console.log('%c🥑 AvocaDetect ', 'background: #6B8E23; color: white; font-size: 20px; padding: 10px; border-radius: 5px;');
console.log('%cKlasifikasi Kematangan Alpukat Berbasis Tekstur', 'color: #6B8E23; font-size: 14px;');
console.log('%cTugas Besar Pengolahan Citra Digital', 'color: #999; font-size: 12px;');
