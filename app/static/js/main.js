/* ============================================
   KORA AI - Main Page JavaScript
   main.html specific scripts
   ============================================ */

document.addEventListener('DOMContentLoaded', function() {
    initMainPage();
});

function initMainPage() {
    // State
    let selectedMarket = 'kospi';
    let selectedCompany = null;
    let selectedRequest = null;
    
    // Elements
    const marketChips = document.querySelectorAll('.market-chip');
    const searchInput = document.getElementById('company-search');
    const clearSearchBtn = document.getElementById('clear-search');
    const searchResults = document.getElementById('search-results');
    const actionChips = document.querySelectorAll('.action-chip');
    const customRequestInput = document.getElementById('custom-request');
    const customSubmitBtn = document.getElementById('custom-submit');
    const generateReportBtn = document.getElementById('generate-report');
    const trendingTabs = document.querySelectorAll('.trending-tab');
    const refreshTrendingBtn = document.getElementById('refresh-trending');
    
    // ==========================================
    // Market Selection
    // ==========================================
    
    marketChips.forEach(chip => {
        chip.addEventListener('click', function() {
            marketChips.forEach(c => c.classList.remove('active'));
            this.classList.add('active');
            selectedMarket = this.dataset.market;
            
            // Clear and reload
            if (searchInput) searchInput.value = '';
            if (searchResults) searchResults.classList.remove('active');
            selectedCompany = null;
            updateReportButton();
        });
    });
    
    // ==========================================
    // Company Search
    // ==========================================
    
    let searchTimeout;
    if (searchInput) {
        searchInput.addEventListener('input', function() {
            const query = this.value.trim();
            
            clearTimeout(searchTimeout);
            
            if (query.length > 0) {
                if (clearSearchBtn) clearSearchBtn.style.display = 'flex';
            } else {
                if (clearSearchBtn) clearSearchBtn.style.display = 'none';
                if (searchResults) searchResults.classList.remove('active');
                return;
            }
            
            if (query.length < 1) return;
            
            searchTimeout = setTimeout(() => {
                searchCompanies(query);
            }, 300);
        });
    }
    
    if (clearSearchBtn) {
        clearSearchBtn.addEventListener('click', function() {
            if (searchInput) searchInput.value = '';
            this.style.display = 'none';
            if (searchResults) searchResults.classList.remove('active');
            selectedCompany = null;
            updateReportButton();
        });
    }
    
    // Close search results on outside click
    document.addEventListener('click', function(e) {
        if (!e.target.closest('.search-box-wrapper') && searchResults) {
            searchResults.classList.remove('active');
        }
    });
    
    async function searchCompanies(query) {
        try {
            const response = await fetch(`/api/companies/search?q=${encodeURIComponent(query)}&market=${selectedMarket}`);
            const companies = await response.json();
            displaySearchResults(companies);
        } catch (error) {
            console.error('Search error:', error);
            if (searchResults) {
                searchResults.innerHTML = '<div class="search-no-results">검색 중 오류가 발생했습니다</div>';
                searchResults.classList.add('active');
            }
        }
    }
    
    function displaySearchResults(companies) {
        if (!searchResults) return;
        
        if (companies.length === 0) {
            searchResults.innerHTML = '<div class="search-no-results">검색 결과가 없습니다</div>';
        } else {
            searchResults.innerHTML = companies.map(company => `
                <div class="search-result-item" data-code="${company.code}" data-name="${company.short_name || company.name}">
                    <span class="result-name">${company.short_name || company.name}</span>
                    <span class="result-code">${company.code}</span>
                </div>
            `).join('');
            
            searchResults.querySelectorAll('.search-result-item').forEach(item => {
                item.addEventListener('click', function(e) {
                    e.stopPropagation();
                    e.preventDefault();
                    
                    const code = this.dataset.code;
                    const name = this.dataset.name;
                    
                    // 검색 결과 먼저 닫기
                    searchResults.classList.remove('active');
                    
                    // 검색 타이머 취소 (중복 검색 방지)
                    clearTimeout(searchTimeout);
                    
                    // 검색창 값 설정 (input 이벤트 발생 방지를 위해 직접 설정)
                    if (searchInput) {
                        searchInput.value = name;
                    }
                    
                    // 기업 선택
                    selectCompany(code, name);
                });
            });
        }
        searchResults.classList.add('active');
    }
    
    // ==========================================
    // Action Chips (Quick Requests)
    // ==========================================
    
    actionChips.forEach(chip => {
        chip.addEventListener('click', function() {
            actionChips.forEach(c => c.classList.remove('active'));
            this.classList.add('active');
            selectedRequest = this.dataset.request;
            
            if (customRequestInput) {
                customRequestInput.value = selectedRequest;
            }
            
            updateReportButton();
        });
    });
    
    // Custom Request Input
    if (customRequestInput) {
        customRequestInput.addEventListener('input', function() {
            if (this.value.trim()) {
                actionChips.forEach(c => c.classList.remove('active'));
                selectedRequest = this.value.trim();
            }
            updateReportButton();
        });
        
        customRequestInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                handleCustomSubmit();
            }
        });
    }
    
    if (customSubmitBtn) {
        customSubmitBtn.addEventListener('click', handleCustomSubmit);
    }
    
    function handleCustomSubmit() {
        const customText = customRequestInput?.value.trim();
        if (customText) {
            selectedRequest = customText;
            updateReportButton();
            
            if (selectedCompany) {
                generateReportBtn?.click();
            } else {
                alert('먼저 분석할 기업을 선택해주세요.');
            }
        }
    }
    
    // ==========================================
    // Trending Sidebar
    // ==========================================
    
    trendingTabs.forEach(tab => {
        tab.addEventListener('click', function() {
            trendingTabs.forEach(t => t.classList.remove('active'));
            this.classList.add('active');
            
            const market = this.dataset.market;
            document.querySelectorAll('.trending-list').forEach(list => {
                list.classList.remove('active');
            });
            const targetList = document.getElementById(`${market}-trending`);
            if (targetList) targetList.classList.add('active');
        });
    });
    
    async function loadTrendingCompanies() {
        try {
            const response = await fetch('/api/companies/popular');
            const data = await response.json();
            
            displayTrendingCompanies('kospi-trending', data.kospi);
            displayTrendingCompanies('kosdaq-trending', data.kosdaq);
            
            const updateTime = document.getElementById('update-time');
            if (updateTime) updateTime.textContent = '방금 전 업데이트';
        } catch (error) {
            console.error('Trending companies error:', error);
        }
    }
    
    function formatViewCount(count) {
        if (!count || count === 0) return '0';
        if (count >= 1000) {
            return (count / 1000).toFixed(1).replace(/\.0$/, '') + 'K';
        }
        return count.toString();
    }
    
    function displayTrendingCompanies(elementId, companies) {
        const container = document.getElementById(elementId);
        if (!container || !companies) return;
        
        container.innerHTML = companies.map((company, index) => {
            // 실제 조회수가 있으면 사용, 없으면 0 표시
            const views = company.view_count || 0;
            return `
                <div class="trending-item" data-code="${company.code}" data-name="${company.short_name || company.name}">
                    <span class="trending-rank">${index + 1}</span>
                    <div class="trending-info">
                        <div class="trending-name">${company.short_name || company.name}</div>
                        <div class="trending-code">${company.code}</div>
                    </div>
                    <div class="trending-views">
                        <i class="fas fa-eye"></i>
                        ${formatViewCount(views)}
                    </div>
                </div>
            `;
        }).join('');
        
        container.querySelectorAll('.trending-item').forEach(item => {
            item.addEventListener('click', function() {
                selectCompany(this.dataset.code, this.dataset.name);
                if (searchInput) searchInput.value = this.dataset.name;
                
                const market = elementId.replace('-trending', '');
                if (market !== selectedMarket) {
                    selectedMarket = market;
                    marketChips.forEach(c => c.classList.remove('active'));
                    const targetChip = document.querySelector(`.market-chip[data-market="${market}"]`);
                    if (targetChip) targetChip.classList.add('active');
                }
            });
        });
    }
    
    if (refreshTrendingBtn) {
        refreshTrendingBtn.addEventListener('click', function() {
            loadTrendingCompanies();
        });
    }
    
    // ==========================================
    // Company Selection
    // ==========================================
    
    function selectCompany(code, name) {
        selectedCompany = { code, name };
        updateReportButton();
        
        // 조회수 기록 (인기 기업 추적용)
        recordCompanyView(code, name, selectedMarket);
    }
    
    // 기업 조회 기록
    async function recordCompanyView(code, name, market) {
        try {
            await fetch('/api/companies/view', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    code: code,
                    name: name,
                    market: market.toUpperCase()
                })
            });
        } catch (error) {
            console.error('Error recording view:', error);
        }
    }
    
    function updateReportButton() {
        if (generateReportBtn) {
            generateReportBtn.disabled = !selectedCompany;
        }
    }
    
    if (generateReportBtn) {
        generateReportBtn.addEventListener('click', async function() {
            if (!selectedCompany) {
                alert('기업을 먼저 선택해주세요.');
                return;
            }
            
            // 먼저 크레딧 확인
            this.disabled = true;
            this.innerHTML = '<i class="fas fa-hourglass-half"></i> 크레딧 확인 중...';
            
            try {
                // 크레딧 체크
                const creditResponse = await fetch('/api/credits/check');
                const creditData = await creditResponse.json();
                
                const REQUIRED_CREDITS = 300;
                
                if (!creditData.success || creditData.credits < REQUIRED_CREDITS) {
                    const currentCredits = creditData.credits || 0;
                    alert(`크레딧이 부족합니다.\n\n필요: ${REQUIRED_CREDITS} 크레딧\n보유: ${currentCredits} 크레딧\n\n크레딧 충전 페이지로 이동합니다.`);
                    window.location.href = '/credits';
                    return;
                }
                
                this.innerHTML = '<i class="fas fa-hourglass-half"></i> 준비 중...';
                
                // DART corp_code 조회
                const corpResponse = await fetch(`/api/companies/corp-code?ticker=${selectedCompany.code}`);
                const corpData = await corpResponse.json();
                
                const corpCode = corpData.corp_code || '';
                
                // 요청사항 가져오기
                const requestText = customRequestInput?.value.trim() || '';
                
                // 보고서 페이지로 이동
                const params = new URLSearchParams({
                    company: selectedCompany.name,
                    ticker: selectedCompany.code,
                    corp_code: corpCode,
                    market: selectedMarket.toUpperCase()
                });
                
                // 요청사항이 있으면 추가
                if (requestText) {
                    params.append('request', requestText);
                }
                
                window.location.href = `/report?${params.toString()}`;
            } catch (error) {
                console.error('Error:', error);
                alert('오류가 발생했습니다. 다시 시도해주세요.');
                this.disabled = false;
                this.innerHTML = '<i class="fas fa-chart-line"></i> 요약 보고서 생성';
            }
        });
    }
    
    // ==========================================
    // Initialize
    // ==========================================
    
    loadTrendingCompanies();
}

