// common.js
// KORA AI 공통 JavaScript

// jQuery 로드 확인
if (typeof jQuery === 'undefined') {
    console.error('KORA AI: jQuery가 로드되지 않았습니다.');
}

// KORA 네임스페이스
const KORA = {
    // API 기본 URL
    API_BASE: '/api',
    
    // 디버그 모드
    DEBUG: true,
    
    // 로그 함수
    log: function(message, data) {
        if (this.DEBUG) {
            console.log('[KORA]', message, data || '');
        }
    },
    
    // 에러 로그
    error: function(message, error) {
        console.error('[KORA Error]', message, error || '');
    },
    
    // 토스트 알림 표시
    toast: function(message, type = 'success', duration = 3000) {
        // 기존 토스트 제거
        $('.kora-toast').remove();
        
        // 토스트 생성
        const $toast = $('<div>')
            .addClass('kora-toast')
            .addClass(type)
            .text(message)
            .appendTo('body');
        
        // 자동 제거
        setTimeout(function() {
            $toast.fadeOut(300, function() {
                $(this).remove();
            });
        }, duration);
        
        return $toast;
    },
    
    // API 호출 헬퍼
    api: {
        // GET 요청
        get: function(endpoint, params) {
            return $.ajax({
                url: KORA.API_BASE + endpoint,
                method: 'GET',
                data: params,
                dataType: 'json'
            });
        },
        
        // POST 요청
        post: function(endpoint, data) {
            return $.ajax({
                url: KORA.API_BASE + endpoint,
                method: 'POST',
                data: JSON.stringify(data),
                contentType: 'application/json',
                dataType: 'json'
            });
        },
        
        // PUT 요청
        put: function(endpoint, data) {
            return $.ajax({
                url: KORA.API_BASE + endpoint,
                method: 'PUT',
                data: JSON.stringify(data),
                contentType: 'application/json',
                dataType: 'json'
            });
        },
        
        // DELETE 요청
        delete: function(endpoint) {
            return $.ajax({
                url: KORA.API_BASE + endpoint,
                method: 'DELETE',
                dataType: 'json'
            });
        }
    },
    
    // 유틸리티 함수
    util: {
        // 이메일 유효성 검사
        isValidEmail: function(email) {
            const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            return regex.test(email);
        },
        
        // 비밀번호 유효성 검사 (최소 8자, 영문, 숫자 포함)
        isValidPassword: function(password) {
            return password.length >= 8;
        },
        
        // 문자열 자르기
        truncate: function(str, length) {
            if (str.length <= length) return str;
            return str.substring(0, length) + '...';
        },
        
        // 숫자 포맷 (천 단위 콤마)
        formatNumber: function(num) {
            return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',');
        },
        
        // 날짜 포맷
        formatDate: function(date, format) {
            const d = new Date(date);
            const year = d.getFullYear();
            const month = String(d.getMonth() + 1).padStart(2, '0');
            const day = String(d.getDate()).padStart(2, '0');
            const hours = String(d.getHours()).padStart(2, '0');
            const minutes = String(d.getMinutes()).padStart(2, '0');
            
            if (format === 'datetime') {
                return `${year}-${month}-${day} ${hours}:${minutes}`;
            }
            return `${year}-${month}-${day}`;
        },
        
        // 디바운스
        debounce: function(func, wait) {
            let timeout;
            return function executedFunction(...args) {
                const later = () => {
                    clearTimeout(timeout);
                    func(...args);
                };
                clearTimeout(timeout);
                timeout = setTimeout(later, wait);
            };
        },
        
        // 쓰로틀
        throttle: function(func, limit) {
            let inThrottle;
            return function(...args) {
                if (!inThrottle) {
                    func.apply(this, args);
                    inThrottle = true;
                    setTimeout(() => inThrottle = false, limit);
                }
            };
        }
    },
    
    // 로컬 스토리지 헬퍼
    storage: {
        // 저장
        set: function(key, value) {
            try {
                localStorage.setItem('kora_' + key, JSON.stringify(value));
                return true;
            } catch (e) {
                KORA.error('Storage set failed', e);
                return false;
            }
        },
        
        // 조회
        get: function(key, defaultValue) {
            try {
                const item = localStorage.getItem('kora_' + key);
                return item ? JSON.parse(item) : defaultValue;
            } catch (e) {
                KORA.error('Storage get failed', e);
                return defaultValue;
            }
        },
        
        // 삭제
        remove: function(key) {
            try {
                localStorage.removeItem('kora_' + key);
                return true;
            } catch (e) {
                KORA.error('Storage remove failed', e);
                return false;
            }
        },
        
        // 전체 삭제
        clear: function() {
            try {
                Object.keys(localStorage).forEach(function(key) {
                    if (key.startsWith('kora_')) {
                        localStorage.removeItem(key);
                    }
                });
                return true;
            } catch (e) {
                KORA.error('Storage clear failed', e);
                return false;
            }
        }
    },
    
    // 로딩 표시
    loading: {
        show: function(target) {
            const $target = $(target || 'body');
            if (!$target.find('.kora-loading-overlay').length) {
                $target.append(`
                    <div class="kora-loading-overlay">
                        <div class="kora-spinner"></div>
                    </div>
                `);
            }
            $target.find('.kora-loading-overlay').addClass('show');
        },
        
        hide: function(target) {
            const $target = $(target || 'body');
            $target.find('.kora-loading-overlay').removeClass('show');
        }
    }
};

// DOM 준비 완료 시 실행
$(document).ready(function() {
    KORA.log('KORA AI 초기화 완료');
    
    // 모든 AJAX 요청에 에러 핸들러 추가
    $(document).ajaxError(function(event, jqXHR, settings, error) {
        KORA.error('AJAX 요청 실패:', {
            url: settings.url,
            status: jqXHR.status,
            error: error
        });
        
        // 401 에러 시 로그인 페이지로 리다이렉트
        if (jqXHR.status === 401) {
            window.location.href = '/login';
        }
    });
});

// 전역 에러 핸들러
window.onerror = function(message, source, lineno, colno, error) {
    KORA.error('전역 에러:', {
        message: message,
        source: source,
        line: lineno,
        column: colno,
        error: error
    });
};

