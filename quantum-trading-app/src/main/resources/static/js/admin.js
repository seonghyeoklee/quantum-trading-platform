// Quantum Trading Admin JavaScript

class QuantumAdmin {
    constructor() {
        this.init();
    }

    init() {
        this.initThemeToggle();
        this.initCurrentTime();
        this.initSidebarActive();
        this.initResponsive();
        this.initTooltips();
        this.initNewsTicker();
    }

    // ===== 테마 토글 기능 =====
    initThemeToggle() {
        const themeToggle = document.getElementById('theme-toggle');
        const themeIcon = document.getElementById('theme-icon');
        const body = document.body;

        // 저장된 테마 불러오기
        const savedTheme = localStorage.getItem('quantum-theme') || 'light';
        this.setTheme(savedTheme);

        // 토글 버튼 이벤트
        if (themeToggle) {
            themeToggle.addEventListener('click', () => {
                const currentTheme = body.getAttribute('data-theme');
                const newTheme = currentTheme === 'light' ? 'dark' : 'light';
                this.setTheme(newTheme);

                // 테마 변경 애니메이션
                themeToggle.style.transform = 'scale(0.8)';
                setTimeout(() => {
                    themeToggle.style.transform = 'scale(1)';
                }, 150);
            });
        }
    }

    setTheme(theme) {
        const body = document.body;
        const themeIcon = document.getElementById('theme-icon');

        body.setAttribute('data-theme', theme);
        localStorage.setItem('quantum-theme', theme);

        if (themeIcon) {
            if (theme === 'dark') {
                themeIcon.className = 'bi bi-moon-fill';
            } else {
                themeIcon.className = 'bi bi-sun-fill';
            }
        }

        // 테마 변경 이벤트 발생
        window.dispatchEvent(new CustomEvent('themeChanged', { detail: theme }));
    }

    // ===== 현재 시간 업데이트 =====
    initCurrentTime() {
        const timeElement = document.getElementById('current-time');
        if (timeElement) {
            this.updateTime();
            setInterval(() => this.updateTime(), 1000);
        }
    }

    updateTime() {
        const timeElement = document.getElementById('current-time');
        if (timeElement) {
            const now = new Date();
            const timeString = now.toLocaleTimeString('ko-KR', {
                hour12: false,
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit'
            });
            timeElement.textContent = timeString;
        }
    }

    // ===== 사이드바 활성화 상태 =====
    initSidebarActive() {
        const currentPath = window.location.pathname;
        const navLinks = document.querySelectorAll('.sidebar .nav-link');

        navLinks.forEach(link => {
            link.classList.remove('active');

            const href = link.getAttribute('href');
            if (href === currentPath || (currentPath === '/' && href === '/')) {
                link.classList.add('active');
            }
        });
    }

    // ===== 반응형 사이드바 =====
    initResponsive() {
        const sidebar = document.querySelector('.sidebar');
        const toggleButton = document.createElement('button');

        // 모바일에서만 토글 버튼 생성
        if (window.innerWidth <= 768) {
            this.createMobileSidebarToggle();
        }

        // 윈도우 리사이즈 이벤트
        window.addEventListener('resize', () => {
            if (window.innerWidth <= 768) {
                this.createMobileSidebarToggle();
            } else {
                const existingToggle = document.getElementById('mobile-sidebar-toggle');
                if (existingToggle) {
                    existingToggle.remove();
                }
                if (sidebar) {
                    sidebar.classList.remove('show');
                }
            }
        });
    }

    createMobileSidebarToggle() {
        const existingToggle = document.getElementById('mobile-sidebar-toggle');
        if (existingToggle) return;

        const navbar = document.querySelector('.navbar .container-fluid');
        const toggleButton = document.createElement('button');

        toggleButton.id = 'mobile-sidebar-toggle';
        toggleButton.className = 'btn btn-outline-light btn-sm me-2';
        toggleButton.innerHTML = '<i class="bi bi-list"></i>';

        // 로고 뒤에 삽입
        const brand = navbar.querySelector('.navbar-brand');
        brand.insertAdjacentElement('afterend', toggleButton);

        toggleButton.addEventListener('click', () => {
            const sidebar = document.querySelector('.sidebar');
            sidebar.classList.toggle('show');
        });

        // 사이드바 외부 클릭시 닫기
        document.addEventListener('click', (e) => {
            const sidebar = document.querySelector('.sidebar');
            const toggle = document.getElementById('mobile-sidebar-toggle');

            if (sidebar && toggle &&
                !sidebar.contains(e.target) &&
                !toggle.contains(e.target) &&
                sidebar.classList.contains('show')) {
                sidebar.classList.remove('show');
            }
        });
    }

    // ===== 툴팁 초기화 =====
    initTooltips() {
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }

    // ===== 차트 테마 적용 =====
    getChartTheme() {
        const isDark = document.body.getAttribute('data-theme') === 'dark';
        return {
            backgroundColor: isDark ? '#2d3748' : '#ffffff',
            textColor: isDark ? '#a0aec0' : '#6c757d',
            gridColor: isDark ? '#4a5568' : '#e9ecef',
            borderColor: isDark ? '#4a5568' : '#dee2e6'
        };
    }

    // ===== 알림 표시 =====
    showNotification(message, type = 'info', duration = 5000) {
        const notification = document.createElement('div');
        notification.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
        notification.style.cssText = `
            top: 80px;
            right: 20px;
            z-index: 1050;
            max-width: 350px;
            box-shadow: 0 0.5rem 1rem rgba(0, 0, 0, 0.15);
        `;

        notification.innerHTML = `
            <div class="d-flex align-items-center">
                <i class="bi bi-info-circle me-2"></i>
                <span>${message}</span>
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        `;

        document.body.appendChild(notification);

        // 자동 제거
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, duration);
    }

    // ===== 로딩 상태 표시 =====
    showLoading(target) {
        const loadingElement = document.createElement('div');
        loadingElement.className = 'loading-overlay d-flex align-items-center justify-content-center';
        loadingElement.style.cssText = `
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background-color: rgba(var(--bs-body-bg-rgb), 0.8);
            z-index: 1000;
        `;
        loadingElement.innerHTML = '<div class="loading"></div>';

        if (typeof target === 'string') {
            target = document.querySelector(target);
        }

        if (target) {
            target.style.position = 'relative';
            target.appendChild(loadingElement);
        }

        return loadingElement;
    }

    hideLoading(loadingElement) {
        if (loadingElement && loadingElement.parentNode) {
            loadingElement.remove();
        }
    }

    // ===== AJAX 헬퍼 =====
    async fetchData(url, options = {}) {
        const loading = this.showLoading(document.body);

        try {
            const response = await fetch(url, {
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers
                },
                ...options
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            return data;
        } catch (error) {
            this.showNotification(`데이터를 불러오는 중 오류가 발생했습니다: ${error.message}`, 'danger');
            throw error;
        } finally {
            this.hideLoading(loading);
        }
    }

    // ===== 유틸리티 함수 =====
    formatNumber(num) {
        return new Intl.NumberFormat('ko-KR').format(num);
    }

    formatCurrency(num) {
        return new Intl.NumberFormat('ko-KR', {
            style: 'currency',
            currency: 'KRW'
        }).format(num);
    }

    formatPercent(num) {
        return new Intl.NumberFormat('ko-KR', {
            style: 'percent',
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        }).format(num / 100);
    }

    // ===== 뉴스 티커 =====
    initNewsTicker() {
        this.newsItems = [
            '삼성전자, 신규 반도체 공장 건설 발표...',
            'SK하이닉스, 3분기 실적 시장 예상치 상회',
            'KOSPI, 장중 2,550 돌파... 외인 매수 지속',
            'AI 관련주 급등세... 기관 투자 확대',
            '환율 상승세... 수출주에 호재',
            '금리 인하 기대감... 성장주로 자금 이동'
        ];
        this.currentNewsIndex = 0;

        this.updateNewsTicker();
        // 20초마다 뉴스 변경
        setInterval(() => this.updateNewsTicker(), 20000);
    }

    updateNewsTicker() {
        const newsElement = document.querySelector('.news-ticker span');
        if (newsElement && this.newsItems.length > 0) {
            newsElement.textContent = this.newsItems[this.currentNewsIndex];
            this.currentNewsIndex = (this.currentNewsIndex + 1) % this.newsItems.length;
        }
    }
}

// ===== 전역 인스턴스 생성 =====
let quantumAdmin;

document.addEventListener('DOMContentLoaded', function() {
    quantumAdmin = new QuantumAdmin();

    // 전역 함수로 노출
    window.quantumAdmin = quantumAdmin;
});

// ===== 테마 변경 감지를 위한 커스텀 이벤트 =====
window.addEventListener('themeChanged', function(event) {
    console.log('Theme changed to:', event.detail);

    // 차트가 있다면 테마 업데이트
    if (window.updateChartsTheme) {
        window.updateChartsTheme();
    }
});