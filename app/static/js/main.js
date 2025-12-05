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
    let randomRefreshInterval = null;
    const REFRESH_INTERVAL = 5000; // 5초
    
    // Elements
    const marketChips = document.querySelectorAll('.market-chip');
    const searchInput = document.getElementById('company-search');
    const clearSearchBtn = document.getElementById('clear-search');
    const searchResults = document.getElementById('search-results');
    const randomResults = document.getElementById('random-results');
    const randomRefreshBtn = document.getElementById('random-refresh');
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
            
            // Restart random refresh
            startRandomRefresh();
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
                item.addEventListener('click', function() {
                    selectCompany(this.dataset.code, this.dataset.name);
                    searchResults.classList.remove('active');
                    if (searchInput) searchInput.value = this.dataset.name;
                });
            });
        }
        searchResults.classList.add('active');
    }
    
    // ==========================================
    // Random Recommendations (5초 자동 새로고침)
    // ==========================================
    
    function startRandomRefresh() {
        if (randomRefreshInterval) clearInterval(randomRefreshInterval);
        
        loadRandomCompanies();
        
        randomRefreshInterval = setInterval(() => {
            loadRandomCompanies();
        }, REFRESH_INTERVAL);
    }
    
    if (randomRefreshBtn) {
        randomRefreshBtn.addEventListener('click', function() {
            if (randomRefreshInterval) clearInterval(randomRefreshInterval);
            
            loadRandomCompanies();
            
            randomRefreshInterval = setInterval(() => {
                loadRandomCompanies();
            }, REFRESH_INTERVAL);
        });
    }
    
    async function loadRandomCompanies() {
        if (!randomResults) return;
        
        try {
            const currentChips = randomResults.querySelectorAll('.random-chip');
            currentChips.forEach(chip => chip.classList.add('fade-out'));
            
            await new Promise(resolve => setTimeout(resolve, 400));
            
            const response = await fetch(`/api/companies/random?market=${selectedMarket}`);
            const companies = await response.json();
            
            displayRandomResults(companies);
        } catch (error) {
            console.error('Random error:', error);
        }
    }
    
    function displayRandomResults(companies) {
        if (!randomResults) return;
        
        randomResults.innerHTML = companies.map(company => `
            <div class="random-chip fade-in" data-code="${company.code}" data-name="${company.short_name || company.name}">
                ${company.short_name || company.name}
            </div>
        `).join('');
        
        randomResults.querySelectorAll('.random-chip').forEach(chip => {
            chip.addEventListener('click', function() {
                selectCompany(this.dataset.code, this.dataset.name);
                if (searchInput) searchInput.value = this.dataset.name;
            });
        });
        
        // Check for overflow and update fade effect
        setTimeout(() => updateRandomChipsOverflow(), 100);
    }
    
    // Check if random chips container has overflow
    function updateRandomChipsOverflow() {
        const wrapper = document.getElementById('random-chips-wrapper');
        if (!wrapper || !randomResults) return;
        
        const hasOverflow = randomResults.scrollWidth > randomResults.clientWidth;
        const scrollLeft = randomResults.scrollLeft;
        const maxScroll = randomResults.scrollWidth - randomResults.clientWidth;
        
        // Show/hide left fade
        if (scrollLeft > 5) {
            wrapper.classList.add('has-overflow-left');
        } else {
            wrapper.classList.remove('has-overflow-left');
        }
        
        // Show/hide right fade
        if (hasOverflow && scrollLeft < maxScroll - 5) {
            wrapper.classList.add('has-overflow-right');
        } else {
            wrapper.classList.remove('has-overflow-right');
        }
    }
    
    // Listen for scroll on random chips
    if (randomResults) {
        randomResults.addEventListener('scroll', updateRandomChipsOverflow);
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
        if (count >= 1000) {
            return (count / 1000).toFixed(1).replace(/\.0$/, '') + 'K';
        }
        return count.toString();
    }
    
    function generateViewCount(index) {
        const baseViews = Math.floor(Math.random() * 5000) + 500;
        const rankBonus = (10 - index) * 300;
        return baseViews + rankBonus;
    }
    
    function displayTrendingCompanies(elementId, companies) {
        const container = document.getElementById(elementId);
        if (!container || !companies) return;
        
        container.innerHTML = companies.map((company, index) => {
            const views = generateViewCount(index);
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
            
            // DART corp_code 조회
            this.disabled = true;
            this.innerHTML = '<i class="fas fa-hourglass-half"></i> 준비 중...';
            
            try {
                const corpResponse = await fetch(`/api/companies/corp-code?ticker=${selectedCompany.code}`);
                const corpData = await corpResponse.json();
                
                const corpCode = corpData.corp_code || '';
                
                // 보고서 페이지로 이동
                const params = new URLSearchParams({
                    company: selectedCompany.name,
                    ticker: selectedCompany.code,
                    corp_code: corpCode,
                    market: selectedMarket.toUpperCase()
                });
                
                window.location.href = `/report?${params.toString()}`;
            } catch (error) {
                console.error('Error getting corp_code:', error);
                // corp_code 없이도 이동 (일부 기능 제한될 수 있음)
                const params = new URLSearchParams({
                    company: selectedCompany.name,
                    ticker: selectedCompany.code,
                    corp_code: '',
                    market: selectedMarket.toUpperCase()
                });
                window.location.href = `/report?${params.toString()}`;
            }
        });
    }
    
    // ==========================================
    // Initialize
    // ==========================================
    
    startRandomRefresh();
    loadTrendingCompanies();
}

