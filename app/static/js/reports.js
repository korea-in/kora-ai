/**
 * KORA AI - 보고서함 페이지 JavaScript
 */

document.addEventListener('DOMContentLoaded', function() {
    initTabs();
    initFilters();
    loadMyReports();
    loadPublicReports();
});

// 탭 초기화
function initTabs() {
    const tabBtns = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');
    
    tabBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            const targetTab = this.dataset.tab;
            
            // 탭 버튼 활성화
            tabBtns.forEach(b => b.classList.remove('active'));
            this.classList.add('active');
            
            // 탭 콘텐츠 전환
            tabContents.forEach(content => {
                content.classList.remove('active');
                if (content.id === targetTab) {
                    content.classList.add('active');
                }
            });
        });
    });
}

// 필터 초기화
function initFilters() {
    const searchInput = document.getElementById('reportSearch');
    const marketFilter = document.getElementById('marketFilter');
    const sortFilter = document.getElementById('sortFilter');
    
    if (searchInput) {
        searchInput.addEventListener('input', debounce(filterReports, 300));
    }
    
    if (marketFilter) {
        marketFilter.addEventListener('change', filterReports);
    }
    
    if (sortFilter) {
        sortFilter.addEventListener('change', filterReports);
    }
}

// 디바운스 함수
function debounce(func, wait) {
    let timeout;
    return function(...args) {
        clearTimeout(timeout);
        timeout = setTimeout(() => func.apply(this, args), wait);
    };
}

// 내 보고서 로드
async function loadMyReports() {
    const grid = document.getElementById('myReportsGrid');
    const emptyState = document.getElementById('myReportsEmpty');
    const countEl = document.getElementById('myReportsCount');
    
    try {
        const response = await fetch('/api/reports/my');
        const data = await response.json();
        
        console.log('[loadMyReports] Response:', data);
        
        // 401 에러 (로그인 필요)
        if (response.status === 401) {
            console.log('[loadMyReports] Not logged in');
            if (grid) grid.innerHTML = '<div class="reports-loading"><p>로그인이 필요합니다</p></div>';
            if (emptyState) emptyState.classList.add('hidden');
            return;
        }
        
        let reports = [];
        if (data.success && data.reports) {
            reports = data.reports;
        }
        
        if (reports.length === 0) {
            if (grid) grid.innerHTML = '';
            if (emptyState) emptyState.classList.remove('hidden');
        } else {
            if (emptyState) emptyState.classList.add('hidden');
            if (grid) grid.innerHTML = reports.map(report => createReportCard(report, false)).join('');
        }
        
        if (countEl) countEl.textContent = reports.length;
        
    } catch (error) {
        console.error('Error loading my reports:', error);
        if (grid) grid.innerHTML = '<div class="reports-loading"><p>보고서를 불러오는데 실패했습니다</p></div>';
    }
}

// 공개 보고서 로드
async function loadPublicReports(market = 'all', search = '') {
    const grid = document.getElementById('publicReportsGrid');
    const emptyState = document.getElementById('publicReportsEmpty');
    const countEl = document.getElementById('publicReportsCount');
    
    try {
        const params = new URLSearchParams();
        if (market && market !== 'all') params.append('market', market);
        if (search) params.append('search', search);
        
        const response = await fetch(`/api/reports/public?${params.toString()}`);
        const data = await response.json();
        
        let reports = [];
        if (data.success && data.reports) {
            reports = data.reports;
        }
        
        if (reports.length === 0) {
            grid.innerHTML = '';
            emptyState.classList.remove('hidden');
        } else {
            emptyState.classList.add('hidden');
            grid.innerHTML = reports.map(report => createReportCard(report, true)).join('');
        }
        
        if (countEl) countEl.textContent = reports.length;
        
    } catch (error) {
        console.error('Error loading public reports:', error);
        grid.innerHTML = '<div class="reports-loading"><p>보고서를 불러오는데 실패했습니다</p></div>';
    }
}

// 보고서 카드 생성
function createReportCard(report, isPublic) {
    // Firebase 필드명 매핑
    const score = report.investment_score || report.score || 0;
    const scoreClass = score >= 70 ? 'high' : (score >= 50 ? 'medium' : 'low');
    const companyName = report.company_name || '알 수 없음';
    const firstChar = companyName.charAt(0);
    const market = report.market || 'KOSPI';
    const ticker = report.ticker || '';
    const opinion = report.investment_opinion || '';
    const createdAt = report.created_at_str || report.created_at || '날짜 없음';
    
    // report.id가 문자열(Firebase doc id)일 수 있음
    const reportId = report.id;
    
    return `
        <div class="report-card ${isPublic ? 'public' : ''}" onclick="openReport('${reportId}', ${isPublic})">
            <div class="report-card-header">
                <div class="company-info">
                    <div class="company-logo">${firstChar}</div>
                    <div class="company-details">
                        <h3>${companyName}</h3>
                        <div class="company-meta">
                            <span class="market-badge ${market.toLowerCase()}">${market}</span>
                            <span>${ticker}</span>
                            ${isPublic && report.author ? `<span>by ${report.author}</span>` : ''}
                        </div>
                    </div>
                </div>
                <div class="score-badge ${scoreClass}">
                    <span class="score-value">${score}</span>
                    <span class="score-label">점</span>
                </div>
            </div>
            
            <p class="report-summary">${opinion ? `투자의견: ${opinion}` : '투자 분석 보고서'}</p>
            
            <div class="report-card-footer">
                <span class="report-date">
                    <i class="far fa-clock"></i> ${createdAt}
                </span>
                <span class="view-btn">
                    ${isPublic ? '<i class="fas fa-coins"></i> 100' : '<i class="fas fa-arrow-right"></i>'} 
                    ${isPublic ? '크레딧' : '보기'}
                </span>
            </div>
        </div>
    `;
}

// 보고서 열기
function openReport(reportId, isPublic) {
    console.log('Opening report:', reportId, 'isPublic:', isPublic);
    
    if (isPublic) {
        // 크레딧 확인 후 열기
        const creditsEl = document.getElementById('userCredits');
        const credits = creditsEl ? parseInt(creditsEl.textContent) : 0;
        
        if (credits < 100) {
            alert('크레딧이 부족합니다. 크레딧을 충전해주세요.');
            window.location.href = '/credits';
            return;
        }
        
        if (confirm('이 보고서를 열람하면 100 크레딧이 차감됩니다. 계속하시겠습니까?')) {
            window.location.href = `/report/view/${reportId}`;
        }
    } else {
        window.location.href = `/report/view/${reportId}`;
    }
}

// 필터 적용
function filterReports() {
    const searchTerm = document.getElementById('reportSearch').value;
    const market = document.getElementById('marketFilter').value;
    
    // 현재 활성 탭 확인
    const activeTab = document.querySelector('.tab-btn.active').dataset.tab;
    
    if (activeTab === 'public-reports') {
        // 공개 보고서는 서버 사이드 필터링
        loadPublicReports(market, searchTerm);
    } else {
        // 내 보고서는 클라이언트 사이드 필터링
        const cards = document.querySelectorAll('#myReportsGrid .report-card');
        
        cards.forEach(card => {
            const companyName = card.querySelector('h3').textContent.toLowerCase();
            const cardMarket = card.querySelector('.market-badge').textContent;
            
            const matchesSearch = !searchTerm || companyName.includes(searchTerm.toLowerCase());
            const matchesMarket = market === 'all' || cardMarket === market;
            
            card.style.display = (matchesSearch && matchesMarket) ? 'block' : 'none';
        });
    }
}

// 모달 닫기
function closeModal() {
    document.getElementById('reportModal').classList.add('hidden');
}


