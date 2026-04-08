// ===== OISO Map - Frontend =====

const API_BASE = '/api/v1';

// 대구 전통시장 인근 좌표 (기본 중심점)
const DEFAULT_CENTER = [35.869, 128.580];
const DEFAULT_ZOOM = 16;

let map;
let markerLayer;
let activeMarkerId = null;

// ===== 초기화 =====

document.addEventListener('DOMContentLoaded', () => {
    initMap();
    loadMarkers();
    initPanelEvents();
});

// ===== 지도 초기화 =====

function initMap() {
    map = L.map('map', {
        center: DEFAULT_CENTER,
        zoom: DEFAULT_ZOOM,
        zoomControl: true,
    });

    // OpenStreetMap 타일
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://openstreetmap.org/copyright">OpenStreetMap</a>',
        maxZoom: 19,
    }).addTo(map);

    markerLayer = L.layerGroup().addTo(map);
}

// ===== 마커 로드 =====

async function loadMarkers() {
    const overlay = document.getElementById('loading-overlay');

    try {
        const res = await fetch(`${API_BASE}/marker/`);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);

        const markers = await res.json();
        
        // 통계 업데이트
        document.getElementById('marker-count').textContent = markers.length;
        const totalImages = markers.reduce((sum, m) => sum + m.image_count, 0);
        document.getElementById('image-count').textContent = totalImages;

        if (markers.length === 0) {
            showEmptyState();
            overlay.classList.add('hidden');
            return;
        }

        // 마커 렌더링
        markers.forEach((m, i) => {
            const icon = L.divIcon({
                className: '',
                html: `<div class="custom-marker" style="animation-delay: ${i * 0.08}s">
                         <span class="marker-inner">🏪</span>
                       </div>`,
                iconSize: [36, 36],
                iconAnchor: [18, 36],
                popupAnchor: [0, -36],
            });

            const leafletMarker = L.marker([m.latitude, m.longitude], { icon })
                .addTo(markerLayer);

            // 팝업 내용
            const tagsHtml = m.tags.map(t => `<span class="popup-tag">${t}</span>`).join('');
            const popupHtml = `
                <div class="popup-content">
                    <h3>마커 #${m.id}</h3>
                    <div class="popup-tags">${tagsHtml}</div>
                    <div class="popup-meta">📷 이미지 ${m.image_count}장</div>
                    <button class="popup-btn" onclick="openMarkerDetail(${m.id})">상세 보기</button>
                </div>
            `;
            leafletMarker.bindPopup(popupHtml, { maxWidth: 250 });
        });

        // 마커가 모두 보이도록 지도 조정
        if (markers.length > 1) {
            const bounds = L.latLngBounds(markers.map(m => [m.latitude, m.longitude]));
            map.fitBounds(bounds, { padding: [60, 60] });
        } else {
            map.setView([markers[0].latitude, markers[0].longitude], DEFAULT_ZOOM);
        }

    } catch (err) {
        console.error('마커 로드 실패:', err);
        showEmptyState('마커를 불러올 수 없습니다. 서버를 확인해주세요.');
    } finally {
        overlay.classList.add('hidden');
    }
}

// ===== 마커 상세 조회 =====

async function openMarkerDetail(markerId) {
    const panel = document.getElementById('detail-panel');

    try {
        const res = await fetch(`${API_BASE}/marker/${markerId}`);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);

        const detail = await res.json();
        activeMarkerId = markerId;

        // 패널 내용 채우기
        document.getElementById('panel-title').textContent = `마커 #${detail.id}`;
        document.getElementById('panel-coords').textContent = 
            `${detail.latitude.toFixed(6)}, ${detail.longitude.toFixed(6)}`;
        document.getElementById('panel-img-count').textContent = `${detail.image_count}장`;
        document.getElementById('panel-date').textContent = formatDate(detail.created_at);

        // 태그
        const tagsContainer = document.getElementById('panel-tags');
        tagsContainer.innerHTML = detail.tags
            .map(t => `<span class="panel-tag">${t}</span>`)
            .join('');

        // 이미지
        const imagesContainer = document.getElementById('panel-images');
        if (detail.images && detail.images.length > 0) {
            imagesContainer.innerHTML = detail.images.map(img => `
                <div class="image-card" onclick="openLightbox('${img.file_url}')">
                    <img src="${img.file_url}" alt="${img.original_filename}" loading="lazy"
                         onerror="this.parentElement.innerHTML='<div style=\\'padding:20px;text-align:center;color:var(--text-muted)\\'>🖼️<br>이미지 로드 실패</div>'" />
                    <div class="image-card-overlay">
                        <div class="image-card-name">${img.original_filename}</div>
                        ${img.captured_at ? `<div>${img.captured_at}</div>` : ''}
                    </div>
                </div>
            `).join('');
        } else {
            imagesContainer.innerHTML = `
                <div style="grid-column: 1/-1; text-align:center; padding:24px; color:var(--text-muted);">
                    등록된 이미지가 없습니다.
                </div>
            `;
        }

        // 팝업 닫고 패널 열기
        map.closePopup();
        panel.classList.add('open');

    } catch (err) {
        console.error('상세 조회 실패:', err);
    }
}

// ===== 패널 이벤트 =====

function initPanelEvents() {
    document.getElementById('panel-close').addEventListener('click', closePanel);
    document.getElementById('panel-handle').addEventListener('click', closePanel);

    // ESC 키로 닫기
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            closeLightbox();
            closePanel();
        }
    });
}

function closePanel() {
    document.getElementById('detail-panel').classList.remove('open');
    activeMarkerId = null;
}

// ===== Lightbox =====

function openLightbox(url) {
    // 동적 생성
    let lightbox = document.querySelector('.lightbox');
    if (!lightbox) {
        lightbox = document.createElement('div');
        lightbox.className = 'lightbox';
        lightbox.addEventListener('click', closeLightbox);
        document.body.appendChild(lightbox);
    }
    lightbox.innerHTML = `<img src="${url}" />`;
    requestAnimationFrame(() => lightbox.classList.add('active'));
}

function closeLightbox() {
    const lightbox = document.querySelector('.lightbox');
    if (lightbox) lightbox.classList.remove('active');
}

// ===== Empty State =====

function showEmptyState(message) {
    const existing = document.querySelector('.empty-state');
    if (existing) return;

    const el = document.createElement('div');
    el.className = 'empty-state';
    el.innerHTML = `
        <div class="icon">📍</div>
        <h3>${message || '등록된 마커가 없습니다'}</h3>
        <p>이미지를 업로드하면 자동으로<br>지도에 마커가 생성됩니다.</p>
    `;
    document.body.appendChild(el);
}

// ===== Helpers =====

function formatDate(isoString) {
    if (!isoString) return '-';
    const d = new Date(isoString);
    return d.toLocaleDateString('ko-KR', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
    });
}
