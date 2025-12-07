/**
 * KORA AI - 포트폴리오 페이지 JavaScript
 */

// 선택한 기업 목록
let selectedCompanies = [];
const MAX_COMPANIES = 10;
let currentMarket = 'kospi';
let allocationChart = null;
let searchTimeout = null;

document.addEventListener('DOMContentLoaded', function() {
    initPortfolio();
});

function initPortfolio() {
    const searchInput = document.getElementById('companySearch');
    const analyzeBtn = document.getElementById('analyzeBtn');
    const marketTabs = document.querySelectorAll('.market-tab');
    const amountInput = document.getElementById('investmentAmount');
    
    // 기업 검색
    if (searchInput) {
        searchInput.addEventListener('input', function() {
            clearTimeout(searchTimeout);
            const query = this.value.trim();
            
            if (query.length >= 2) {
                searchTimeout = setTimeout(() => searchCompanies(query), 300);
            } else {
                hideSearchDropdown();
            }
        });
        
        // 포커스 아웃 시 드롭다운 숨기기 (약간의 딜레이)
        searchInput.addEventListener('blur', function() {
            setTimeout(hideSearchDropdown, 200);
        });
    }
    
    // 시장 탭 전환
    marketTabs.forEach(tab => {
        tab.addEventListener('click', function() {
            marketTabs.forEach(t => t.classList.remove('active'));
            this.classList.add('active');
            currentMarket = this.dataset.market;
        });
    });
    
    // 분석 버튼
    if (analyzeBtn) {
        analyzeBtn.addEventListener('click', analyzePortfolio);
    }
    
    // 투자 금액 포맷
    if (amountInput) {
        amountInput.addEventListener('input', function() {
            let value = this.value.replace(/[^\d]/g, '');
            if (value) {
                this.value = parseInt(value).toLocaleString();
            }
        });
    }
}

// 기업 검색
async function searchCompanies(query) {
    try {
        const response = await fetch(`/api/companies/search?q=${encodeURIComponent(query)}&market=${currentMarket}`);
        const companies = await response.json();
        
        displaySearchResults(companies);
    } catch (error) {
        console.error('Search error:', error);
    }
}

// 검색 결과 표시
function displaySearchResults(companies) {
    const dropdown = document.getElementById('searchDropdown');
    if (!dropdown) return;
    
    if (companies.length === 0) {
        dropdown.innerHTML = '<div class="search-item no-result">검색 결과가 없습니다</div>';
    } else {
        dropdown.innerHTML = companies.map(company => `
            <div class="search-item" onclick="selectCompany('${company.code}', '${company.name || company.short_name}')">
                <span class="company-name">${company.name || company.short_name}</span>
                <span class="company-code">${company.code}</span>
            </div>
        `).join('');
    }
    
    dropdown.classList.remove('hidden');
}

function hideSearchDropdown() {
    const dropdown = document.getElementById('searchDropdown');
    if (dropdown) {
        dropdown.classList.add('hidden');
    }
}

// 기업 선택
function selectCompany(code, name) {
    if (selectedCompanies.length >= MAX_COMPANIES) {
        alert(`최대 ${MAX_COMPANIES}개까지 추가할 수 있습니다.`);
        return;
    }
    
    if (selectedCompanies.some(c => c.code === code)) {
        alert('이미 추가된 기업입니다.');
        return;
    }
    
    selectedCompanies.push({ code, name, market: currentMarket.toUpperCase() });
    updateCompaniesList();
    
    // 검색창 초기화
    const searchInput = document.getElementById('companySearch');
    if (searchInput) {
        searchInput.value = '';
    }
    hideSearchDropdown();
}

// 기업 제거
function removeCompany(code) {
    selectedCompanies = selectedCompanies.filter(c => c.code !== code);
    updateCompaniesList();
}

// 기업 목록 업데이트
function updateCompaniesList() {
    const container = document.getElementById('companiesList');
    const countSpan = document.querySelector('.selected-companies .count');
    const analyzeBtn = document.getElementById('analyzeBtn');
    const amountSection = document.getElementById('amountSection');
    
    if (countSpan) {
        countSpan.textContent = `(${selectedCompanies.length}/${MAX_COMPANIES})`;
    }
    
    if (analyzeBtn) {
        analyzeBtn.disabled = selectedCompanies.length < 2;
    }
    
    // 금액 섹션 표시/숨김
    if (amountSection) {
        if (selectedCompanies.length >= 2) {
            amountSection.classList.remove('hidden');
        } else {
            amountSection.classList.add('hidden');
        }
    }
    
    if (!container) return;
    
    if (selectedCompanies.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-building"></i>
                <p>기업을 검색하여 추가해주세요</p>
            </div>
        `;
    } else {
        container.innerHTML = selectedCompanies.map(company => `
            <div class="company-chip">
                <span class="chip-market ${company.market.toLowerCase()}">${company.market}</span>
                <span class="chip-name">${company.name}</span>
                <span class="chip-code">${company.code}</span>
                <button class="remove-btn" onclick="removeCompany('${company.code}')">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        `).join('');
    }
}

// 포트폴리오 분석
async function analyzePortfolio() {
    if (selectedCompanies.length < 2) {
        alert('최소 2개 이상의 기업을 선택해주세요.');
        return;
    }
    
    const amountInput = document.getElementById('investmentAmount');
    const totalAmount = parseInt(amountInput?.value.replace(/[^\d]/g, '') || '10000000');
    
    const analyzeBtn = document.getElementById('analyzeBtn');
    const loadingSection = document.getElementById('loadingSection');
    const resultSection = document.getElementById('portfolioResult');
    const builderSection = document.querySelector('.portfolio-builder');
    const amountSection = document.getElementById('amountSection');
    
    // UI 상태 변경
    if (analyzeBtn) analyzeBtn.disabled = true;
    if (loadingSection) loadingSection.classList.remove('hidden');
    if (resultSection) resultSection.classList.add('hidden');
    if (builderSection) builderSection.classList.add('hidden');
    if (amountSection) amountSection.classList.add('hidden');
    
    try {
        const response = await fetch('/api/portfolio/analyze', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                companies: selectedCompanies,
                total_amount: totalAmount,
                investment_type: USER_INVESTMENT_TYPE,
                investment_score: USER_INVESTMENT_SCORE
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            displayAnalysisResult(result.analysis, totalAmount);
        } else {
            alert('분석 실패: ' + (result.error || '알 수 없는 오류'));
            resetToBuilder();
        }
        
    } catch (error) {
        console.error('Analysis error:', error);
        alert('분석 중 오류가 발생했습니다.');
        resetToBuilder();
    } finally {
        if (loadingSection) loadingSection.classList.add('hidden');
    }
}

// 분석 결과 표시
function displayAnalysisResult(analysis, totalAmount) {
    const resultSection = document.getElementById('portfolioResult');
    if (!resultSection) return;
    
    resultSection.classList.remove('hidden');
    
    // 1. 자산 배분 파이 차트
    createAllocationChart(analysis.allocations);
    
    // 2. 리스크 미터
    updateRiskMeter(analysis.risk_score, analysis.risk_level);
    
    // 3. 예상 수익률
    document.getElementById('returnMin').textContent = `${analysis.expected_return_min}%`;
    document.getElementById('returnMax').textContent = `${analysis.expected_return_max}%`;
    
    // 4. AI 조언
    document.getElementById('aiAdvice').innerHTML = analysis.advice.replace(/\n/g, '<br>');
    
    // 5. 기업별 배분 테이블
    createAllocationTable(analysis.allocations, totalAmount);
}

// 파이 차트 생성
function createAllocationChart(allocations) {
    const ctx = document.getElementById('allocationChart')?.getContext('2d');
    if (!ctx) return;
    
    // 기존 차트 제거
    if (allocationChart) {
        allocationChart.destroy();
    }
    
    const colors = [
        '#4F46E5', '#06B6D4', '#10B981', '#F59E0B', '#EF4444',
        '#8B5CF6', '#EC4899', '#14B8A6', '#F97316', '#6366F1'
    ];
    
    const labels = allocations.map(a => a.name);
    const data = allocations.map(a => a.percentage);
    
    allocationChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                data: data,
                backgroundColor: colors.slice(0, allocations.length),
                borderWidth: 2,
                borderColor: '#fff'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return `${context.label}: ${context.raw}%`;
                        }
                    }
                }
            }
        }
    });
    
    // 범례 생성
    const legendContainer = document.getElementById('allocationLegend');
    if (legendContainer) {
        legendContainer.innerHTML = allocations.map((a, i) => `
            <div class="legend-item">
                <span class="legend-color" style="background: ${colors[i]}"></span>
                <span class="legend-name">${a.name}</span>
                <span class="legend-value">${a.percentage}%</span>
            </div>
        `).join('');
    }
}

// 리스크 미터 업데이트
function updateRiskMeter(score, level) {
    const riskFill = document.getElementById('riskFill');
    const riskScore = document.getElementById('riskScore');
    const riskLabel = document.getElementById('riskLabel');
    
    if (riskFill) {
        riskFill.style.width = `${score}%`;
        
        // 색상 변경
        if (score < 30) {
            riskFill.style.background = 'linear-gradient(90deg, #10B981, #34D399)';
        } else if (score < 60) {
            riskFill.style.background = 'linear-gradient(90deg, #F59E0B, #FBBF24)';
        } else {
            riskFill.style.background = 'linear-gradient(90deg, #EF4444, #F87171)';
        }
    }
    
    if (riskScore) riskScore.textContent = score;
    if (riskLabel) riskLabel.textContent = level;
}

// 배분 테이블 생성
function createAllocationTable(allocations, totalAmount) {
    const tableContainer = document.getElementById('allocationTable');
    if (!tableContainer) return;
    
    const tableHTML = `
        <table>
            <thead>
                <tr>
                    <th>기업명</th>
                    <th>비중</th>
                    <th>투자금액</th>
                    <th>투자 의견</th>
                </tr>
            </thead>
            <tbody>
                ${allocations.map(a => `
                    <tr>
                        <td>
                            <div class="company-cell">
                                <span class="name">${a.name}</span>
                                <span class="code">${a.code}</span>
                            </div>
                        </td>
                        <td><strong>${a.percentage}%</strong></td>
                        <td>${Math.round(totalAmount * a.percentage / 100).toLocaleString()}원</td>
                        <td><span class="opinion ${a.opinion_class}">${a.opinion}</span></td>
                    </tr>
                `).join('')}
            </tbody>
        </table>
    `;
    
    tableContainer.innerHTML = tableHTML;
}

// 분석 초기화
function resetAnalysis() {
    const resultSection = document.getElementById('portfolioResult');
    const builderSection = document.querySelector('.portfolio-builder');
    const amountSection = document.getElementById('amountSection');
    const analyzeBtn = document.getElementById('analyzeBtn');
    
    if (resultSection) resultSection.classList.add('hidden');
    if (builderSection) builderSection.classList.remove('hidden');
    if (amountSection && selectedCompanies.length >= 2) amountSection.classList.remove('hidden');
    if (analyzeBtn) analyzeBtn.disabled = selectedCompanies.length < 2;
}

function resetToBuilder() {
    const builderSection = document.querySelector('.portfolio-builder');
    const amountSection = document.getElementById('amountSection');
    const analyzeBtn = document.getElementById('analyzeBtn');
    
    if (builderSection) builderSection.classList.remove('hidden');
    if (amountSection && selectedCompanies.length >= 2) amountSection.classList.remove('hidden');
    if (analyzeBtn) analyzeBtn.disabled = selectedCompanies.length < 2;
}

// 포트폴리오 저장
async function savePortfolio() {
    try {
        const response = await fetch('/api/portfolio/save', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                companies: selectedCompanies,
                name: `내 포트폴리오 ${new Date().toLocaleDateString()}`
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            alert('포트폴리오가 저장되었습니다!');
        } else {
            alert('저장 실패: ' + (result.error || '알 수 없는 오류'));
        }
    } catch (error) {
        console.error('Save error:', error);
        alert('저장 중 오류가 발생했습니다.');
    }
}


