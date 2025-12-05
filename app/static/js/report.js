/**
 * KORA AI - 보고서 페이지 JavaScript
 */

// 전역 변수
let reportData = null;
let aiAnalysis = null;
let priceChart = null;

// 로딩 메시지 목록 (미니멀)
const LOADING_MESSAGES = [
    "보고서를 불러오고 있어요",
    "주가 데이터를 수집하고 있어요",
    "재무 정보를 분석하고 있어요",
    "뉴스를 수집하고 있어요",
    "AI가 분석하고 있어요",
    "보고서를 작성하고 있어요",
    "거의 완료되었어요"
];

let loadingMessageIndex = 0;
let loadingMessageInterval = null;

// ============================================
// 초기화
// ============================================

document.addEventListener('DOMContentLoaded', async function() {
    // COMPANY_DATA 확인
    console.log('[DEBUG] COMPANY_DATA:', COMPANY_DATA);
    
    // 필수 데이터 확인
    if (!COMPANY_DATA.name || !COMPANY_DATA.ticker) {
        alert('기업 정보가 없습니다. 메인 화면에서 기업을 선택해주세요.');
        window.location.href = '/main';
        return;
    }
    
    // 네비게이션 초기화
    initNavigation();
    
    // 데이터 로드 시작
    await loadReport();
});

// 네비게이션 초기화
function initNavigation() {
    const navLinks = document.querySelectorAll('.nav-link');
    const sections = document.querySelectorAll('.section[id]');
    
    // 클릭 시 스크롤
    navLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const targetId = this.getAttribute('href').substring(1);
            const targetSection = document.getElementById(targetId);
            if (targetSection) {
                targetSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }
        });
    });
    
    // 스크롤 시 활성 네비게이션 업데이트
    window.addEventListener('scroll', () => {
        let current = '';
        const scrollPos = window.scrollY + 150;
        
        sections.forEach(section => {
            const sectionTop = section.offsetTop;
            const sectionHeight = section.offsetHeight;
            
            if (scrollPos >= sectionTop && scrollPos < sectionTop + sectionHeight) {
                current = section.getAttribute('id');
            }
        });
        
        navLinks.forEach(link => {
            link.classList.remove('active');
            if (link.getAttribute('href') === '#' + current) {
                link.classList.add('active');
            }
        });
    });
}

// 재무제표 탭 초기화
function initStatementTabs() {
    const tabs = document.querySelectorAll('.statement-tab');
    const contents = document.querySelectorAll('.statement-content');
    
    tabs.forEach(tab => {
        tab.addEventListener('click', function() {
            const targetTab = this.dataset.tab;
            
            // 탭 활성화
            tabs.forEach(t => t.classList.remove('active'));
            this.classList.add('active');
            
            // 컨텐츠 전환
            contents.forEach(c => {
                c.classList.remove('active');
                if (c.id === `${targetTab}-content`) {
                    c.classList.add('active');
                }
            });
        });
    });
}

async function loadReport() {
    showLoading(true);
    
    try {
        // 1단계: 데이터 수집
        updateLoadingStep('KRX 주가 데이터 조회', 10);
        await sleep(500);
        
        updateLoadingStep('DART 공시/재무 데이터 조회', 30);
        const dataResponse = await fetch('/api/report/data', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                company_name: COMPANY_DATA.name,
                ticker: COMPANY_DATA.ticker,
                corp_code: COMPANY_DATA.corpCode
            })
        });
        
        const dataResult = await dataResponse.json();
        
        if (!dataResult.success) {
            throw new Error(dataResult.error || '데이터 수집 실패');
        }
        
        reportData = dataResult.data;
        
        // 2단계: 기본 데이터 표시
        updateLoadingStep('기본 정보 표시', 50);
        displayBasicData(reportData);
        
        // 3단계: AI 분석 요청
        updateLoadingStep('AI 종합 분석 중...', 70);
        const analysisResponse = await fetch('/api/report/analyze', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ all_data: reportData })
        });
        
        const analysisResult = await analysisResponse.json();
        
        if (analysisResult.success) {
            aiAnalysis = analysisResult.analysis;
            displayAIAnalysis(aiAnalysis);
        }
        
        // 4단계: 차트 생성
        updateLoadingStep('차트 생성', 90);
        await createPriceChart();
        
        // 완료
        updateLoadingStep('완료!', 100);
        await sleep(500);
        showLoading(false);
        
        // 생성 시간 표시
        const generatedTimeEl = document.getElementById('generatedTime');
        if (generatedTimeEl) {
            generatedTimeEl.textContent = `생성: ${new Date().toLocaleString('ko-KR')}`;
        }
        
        // PDF 다운로드 버튼 활성화
        enablePdfDownload();
        
    } catch (error) {
        console.error('Report loading error:', error);
        alert('보고서 생성 중 오류가 발생했습니다: ' + error.message);
        showLoading(false);
    }
}

// ============================================
// 기본 데이터 표시
// ============================================

function displayBasicData(data) {
    const krx = data.krx || {};
    const dart = data.dart || {};
    const news = data.news || {};
    
    // 헬퍼 함수 - 안전하게 텍스트 설정
    const setTextSafe = (id, text) => {
        const el = document.getElementById(id);
        if (el) el.textContent = text;
    };
    
    const setClassSafe = (id, className) => {
        const el = document.getElementById(id);
        if (el) el.className = className;
    };
    
    // 현재가
    const current = krx.current_price || {};
    const currentPrice = current.close || 0;
    setTextSafe('currentPrice', formatPrice(currentPrice));
    
    const changeRate = current.change_rate || 0;
    const changeEl = document.getElementById('priceChange');
    if (changeEl) {
        changeEl.textContent = `${changeRate >= 0 ? '+' : ''}${changeRate.toFixed(2)}%`;
        changeEl.className = `card-change ${changeRate >= 0 ? 'positive' : 'negative'}`;
    }
    
    // 밸류에이션
    const val = krx.valuation || {};
    setTextSafe('perValue', val.per ? `${val.per}배` : '-');
    setTextSafe('pbrValue', val.pbr ? `${val.pbr}배` : '-');
    setTextSafe('epsValue', val.eps ? formatPrice(val.eps) : '-');
    setTextSafe('bpsValue', val.bps ? formatPrice(val.bps) : '-');
    setTextSafe('divYield', val.div_yield ? `${val.div_yield}%` : '-');
    
    // 52주 범위
    const yearly = krx.yearly_trend || {};
    if (yearly.low_price && yearly.high_price) {
        setTextSafe('week52Range', `${formatPrice(yearly.low_price)} ~ ${formatPrice(yearly.high_price)}`);
    }
    
    // 기술적 지표 (null 체크 추가)
    const rsi = krx.rsi || {};
    const mfi = krx.mfi || {};
    
    const rsiValueEl = document.getElementById('rsiValue');
    const rsiSignalEl = document.getElementById('rsiSignal');
    const rsiBarEl = document.getElementById('rsiBar');
    
    if (rsiValueEl) rsiValueEl.textContent = rsi.value || '-';
    if (rsiSignalEl) {
        rsiSignalEl.textContent = rsi.signal || '-';
        rsiSignalEl.className = `tech-signal ${getSignalClass(rsi.signal)}`;
    }
    if (rsiBarEl && rsi.value) {
        rsiBarEl.style.width = `${rsi.value}%`;
    }
    
    const mfiValueEl = document.getElementById('mfiValue');
    const mfiSignalEl = document.getElementById('mfiSignal');
    const mfiBarEl = document.getElementById('mfiBar');
    
    if (mfiValueEl) mfiValueEl.textContent = mfi.value || '-';
    if (mfiSignalEl) {
        mfiSignalEl.textContent = mfi.signal || '-';
        mfiSignalEl.className = `tech-signal ${getSignalClass(mfi.signal)}`;
    }
    if (mfiBarEl && mfi.value) {
        mfiBarEl.style.width = `${mfi.value}%`;
    }
    
    // 이동평균
    const ma = krx.moving_averages || {};
    const maCurrent = ma.current || {};
    setTextSafe('ma5', maCurrent.ma5 ? formatPrice(maCurrent.ma5) : '-');
    setTextSafe('ma20', maCurrent.ma20 ? formatPrice(maCurrent.ma20) : '-');
    setTextSafe('ma60', maCurrent.ma60 ? formatPrice(maCurrent.ma60) : '-');
    setTextSafe('ma120', maCurrent.ma120 ? formatPrice(maCurrent.ma120) : '-');
    setTextSafe('maSignal', ma.trend || '-');
    setClassSafe('maSignal', `tech-signal ${ma.trend === '상승 추세' ? 'positive' : ma.trend === '하락 추세' ? 'negative' : 'neutral'}`);
    
    // 기업 정보 테이블
    const companyInfo = dart.company_info || {};
    const tableBody = document.querySelector('#companyInfoTable tbody');
    if (tableBody) {
        tableBody.innerHTML = `
            <tr><td>회사명</td><td>${companyInfo.corp_name || COMPANY_DATA.name}</td></tr>
            <tr><td>대표자</td><td>${companyInfo.ceo_nm || '-'}</td></tr>
            <tr><td>업종</td><td>${companyInfo.induty_code || '-'}</td></tr>
            <tr><td>설립일</td><td>${formatDate(companyInfo.est_dt) || '-'}</td></tr>
            <tr><td>상장일</td><td>${formatDate(companyInfo.stock_lst_dt) || '-'}</td></tr>
            <tr><td>결산월</td><td>${companyInfo.acc_mt || '-'}월</td></tr>
            <tr><td>홈페이지</td><td><a href="${companyInfo.hm_url || '#'}" target="_blank">${companyInfo.hm_url || '-'}</a></td></tr>
        `;
    }
    
    // 뉴스 목록 (상위 5개만 표시)
    displayNewsList(news.items || []);
    
    // 공시 목록
    displayDisclosures(dart.disclosures || []);
    
    // 재무비율 분석
    displayFinancialRatios(dart.financial_index || {});
}

// 재무비율 표시
function displayFinancialRatios(index) {
    if (!index) {
        console.log('Financial index data is empty');
        return;
    }
    
    // DART API 응답 구조: { "수익성지표": [...], "안정성지표": [...], ... }
    // 각 항목: { idx_nm: "지표명", idx_val: "값" }
    
    // 지표 매핑 함수
    const findRatioValue = (category, searchTerms) => {
        const items = index[category] || [];
        for (const term of searchTerms) {
            const found = items.find(item => item.idx_nm && item.idx_nm.includes(term));
            if (found && found.idx_val) {
                const val = parseFloat(found.idx_val.replace(/,/g, ''));
                if (!isNaN(val)) return val;
            }
        }
        return null;
    };
    
    // 유동성 지표 (안정성지표 카테고리에 포함됨)
    setRatioValue('currentRatio', findRatioValue('안정성지표', ['유동비율']), 150, 200, '%', true);
    setRatioValue('quickRatio', findRatioValue('안정성지표', ['당좌비율']), 100, 150, '%', true);
    
    // 안정성 지표
    setRatioValue('debtRatio', findRatioValue('안정성지표', ['부채비율']), 100, 200, '%', false);
    setRatioValue('equityRatio', findRatioValue('안정성지표', ['자기자본비율']), 50, 70, '%', true);
    setRatioValue('interestCoverage', findRatioValue('안정성지표', ['이자보상배율', '이자보상']), 3, 5, '배', true);
    
    // 수익성 지표
    setRatioValue('roe', findRatioValue('수익성지표', ['자기자본순이익률', 'ROE']), 10, 15, '%', true);
    setRatioValue('roa', findRatioValue('수익성지표', ['총자산순이익률', 'ROA']), 5, 10, '%', true);
    setRatioValue('npm', findRatioValue('수익성지표', ['매출액순이익률', '순이익률']), 5, 10, '%', true);
    setRatioValue('opm', findRatioValue('수익성지표', ['매출액영업이익률', '영업이익률']), 10, 15, '%', true);
    
    // 활동성 지표
    setRatioValue('assetTurnover', findRatioValue('활동성지표', ['총자산회전율', '총자본회전율']), 0.5, 1, '회', true);
    setRatioValue('inventoryTurnover', findRatioValue('활동성지표', ['재고자산회전율']), 5, 10, '회', true);
    setRatioValue('receivableTurnover', findRatioValue('활동성지표', ['매출채권회전율']), 5, 10, '회', true);
}

function setRatioValue(id, value, safeMin, goodMin, unit, higherIsBetter) {
    const valueEl = document.getElementById(id);
    const statusEl = document.getElementById(id + 'Status');
    const cardEl = document.getElementById(id + 'Card');
    
    if (!valueEl) return;
    
    if (value === undefined || value === null || isNaN(value)) {
        valueEl.textContent = '-';
        if (statusEl) statusEl.textContent = '데이터 없음';
        return;
    }
    
    const numValue = parseFloat(value);
    valueEl.textContent = numValue.toFixed(2) + unit;
    
    let status, statusClass;
    if (higherIsBetter) {
        if (numValue >= goodMin) {
            status = '양호'; statusClass = 'safe';
        } else if (numValue >= safeMin) {
            status = '보통'; statusClass = 'warning';
        } else {
            status = '주의'; statusClass = 'danger';
        }
    } else {
        // 부채비율 등 낮을수록 좋은 지표
        if (numValue <= safeMin) {
            status = '양호'; statusClass = 'safe';
        } else if (numValue <= goodMin) {
            status = '보통'; statusClass = 'warning';
        } else {
            status = '주의'; statusClass = 'danger';
        }
    }
    
    if (statusEl) {
        statusEl.textContent = status;
        statusEl.className = `ratio-status ${statusClass}`;
    }
    if (cardEl) {
        cardEl.className = `ratio-card ${statusClass}`;
    }
}

// 재무제표 표시
function displayFinancialStatements(financials) {
    const keyAccounts = financials.key_accounts || {};
    
    // 재무상태표
    displayBalanceSheet(keyAccounts);
    
    // 손익계산서
    displayIncomeStatement(keyAccounts);
    
    // 현금흐름표
    displayCashFlow(keyAccounts);
}

function displayBalanceSheet(accounts) {
    const tbody = document.getElementById('balanceSheetBody');
    if (!tbody) return;
    
    const items = [
        { name: '자산총계', key: '자산총계', highlight: true },
        { name: '  유동자산', key: '유동자산' },
        { name: '  비유동자산', key: '비유동자산' },
        { name: '부채총계', key: '부채총계', highlight: true },
        { name: '  유동부채', key: '유동부채' },
        { name: '  비유동부채', key: '비유동부채' },
        { name: '자본총계', key: '자본총계', highlight: true }
    ];
    
    tbody.innerHTML = items.map(item => {
        const data = accounts[item.key] || {};
        const amount = data.current ? formatBillion(data.current) : '-';
        const note = data.change_rate ? `전기 대비 ${data.change_rate}%` : '';
        const rowClass = item.highlight ? 'highlight' : '';
        return `<tr class="${rowClass}"><td>${item.name}</td><td class="amount">${amount}</td><td class="note">${note}</td></tr>`;
    }).join('');
}

function displayIncomeStatement(accounts) {
    const tbody = document.getElementById('incomeStatementBody');
    if (!tbody) return;
    
    const items = [
        { name: '매출액', key: '매출액', highlight: true },
        { name: '매출원가', key: '매출원가' },
        { name: '매출총이익', key: '매출총이익' },
        { name: '영업이익', key: '영업이익', highlight: true },
        { name: '당기순이익', key: '당기순이익', highlight: true }
    ];
    
    tbody.innerHTML = items.map(item => {
        const data = accounts[item.key] || {};
        const amount = data.current ? formatBillion(data.current) : '-';
        const isPositive = data.current && parseFloat(data.current) > 0;
        const isNegative = data.current && parseFloat(data.current) < 0;
        const note = data.change_rate ? `전기 대비 ${data.change_rate}%` : '';
        let rowClass = item.highlight ? 'highlight' : '';
        if (item.key.includes('이익') && isNegative) rowClass += ' negative';
        if (item.key.includes('이익') && isPositive) rowClass += ' positive';
        return `<tr class="${rowClass}"><td>${item.name}</td><td class="amount">${amount}</td><td class="note">${note}</td></tr>`;
    }).join('');
}

function displayCashFlow(accounts) {
    const tbody = document.getElementById('cashflowBody');
    if (!tbody) return;
    
    const items = [
        { name: '영업활동현금흐름', key: '영업활동현금흐름', highlight: true },
        { name: '투자활동현금흐름', key: '투자활동현금흐름' },
        { name: '재무활동현금흐름', key: '재무활동현금흐름' }
    ];
    
    tbody.innerHTML = items.map(item => {
        const data = accounts[item.key] || {};
        const amount = data.current ? formatBillion(data.current) : '-';
        const isPositive = data.current && parseFloat(data.current) > 0;
        const isNegative = data.current && parseFloat(data.current) < 0;
        let rowClass = item.highlight ? 'highlight' : '';
        if (isPositive) rowClass += ' positive';
        if (isNegative) rowClass += ' negative';
        const note = item.key === '영업활동현금흐름' && isPositive ? '🟢 양호' : 
                     item.key === '영업활동현금흐름' && isNegative ? '🔴 주의' : '';
        return `<tr class="${rowClass}"><td>${item.name}</td><td class="amount">${amount}</td><td class="note">${note}</td></tr>`;
    }).join('');
}

function formatBillion(value) {
    if (!value) return '-';
    const num = parseFloat(value);
    if (isNaN(num)) return '-';
    // 억 단위로 변환 (원래 값이 원 단위라고 가정)
    const billion = num / 100000000;
    return billion.toLocaleString('ko-KR', { maximumFractionDigits: 0 });
}

function displayNewsList(newsItems) {
    const container = document.getElementById('newsList');
    
    if (!newsItems || !newsItems.length) {
        container.innerHTML = '<div class="news-item">최근 뉴스가 없습니다.</div>';
        return;
    }
    
    // 상위 5개만 표시
    container.innerHTML = newsItems.slice(0, 5).map(news => `
        <div class="news-item">
            <div class="news-content">
                <div class="news-title">${news.title}</div>
                <div class="news-meta">
                    <span class="news-source">${news.source || '뉴스'}</span>
                    <span class="news-date">${formatDate(news.pub_date)}</span>
                </div>
            </div>
            <a href="${news.link}" target="_blank" class="news-link-btn" title="기사 보기">
                <i class="fas fa-external-link-alt"></i>
            </a>
        </div>
    `).join('');
}

function displayDisclosures(disclosures) {
    const container = document.getElementById('disclosureList');
    
    if (!disclosures.length) {
        container.innerHTML = '<div class="disclosure-item">최근 공시가 없습니다.</div>';
        return;
    }
    
    container.innerHTML = disclosures.slice(0, 5).map(disc => `
        <div class="disclosure-item">
            <span class="disclosure-date">${formatDate(disc.rcept_dt)}</span>
            <span class="disclosure-title">${disc.report_nm}</span>
            <a href="https://dart.fss.or.kr/dsaf001/main.do?rcpNo=${disc.rcept_no}" target="_blank" class="disclosure-link">
                <i class="fas fa-external-link-alt"></i>
            </a>
        </div>
    `).join('');
    
    // DART 링크 설정
    if (disclosures.length > 0) {
        const firstReport = disclosures.find(d => d.report_nm && d.report_nm.includes('보고서'));
        if (firstReport) {
            document.getElementById('dartLink').href = 
                `https://dart.fss.or.kr/dsaf001/main.do?rcpNo=${firstReport.rcept_no}`;
        }
    }
}

// ============================================
// AI 분석 결과 표시
// ============================================

function displayAIAnalysis(analysis) {
    if (!analysis) return;
    
    // 적정주가
    const fairPrice = analysis.fair_price || 0;
    const fairPriceEl = document.getElementById('fairPrice');
    if (fairPriceEl) fairPriceEl.textContent = formatPrice(fairPrice);
    
    const currentPrice = reportData?.krx?.current_price?.close || 0;
    const fairPriceBadge = document.getElementById('fairPriceBadge');
    const diff = ((fairPrice - currentPrice) / currentPrice * 100).toFixed(1);
    
    if (fairPrice > currentPrice * 1.1) {
        fairPriceBadge.textContent = `저평가 (+${diff}%)`;
        fairPriceBadge.className = 'card-badge undervalued';
    } else if (fairPrice < currentPrice * 0.9) {
        fairPriceBadge.textContent = `고평가 (${diff}%)`;
        fairPriceBadge.className = 'card-badge overvalued';
    } else {
        fairPriceBadge.textContent = '적정 수준';
        fairPriceBadge.className = 'card-badge fair';
    }
    
    // 투자 점수
    const score = analysis.investment_score || 0;
    const scoreValueEl = document.getElementById('scoreValue');
    if (scoreValueEl) scoreValueEl.textContent = score;
    
    // 원형 프로그레스
    const circle = document.getElementById('scoreCircle');
    if (circle) {
        const circumference = 2 * Math.PI * 45;
        circle.style.strokeDashoffset = circumference - (score / 100) * circumference;
    }
    
    // 등급
    const gradeEl = document.getElementById('investmentGrade');
    if (gradeEl) gradeEl.textContent = analysis.investment_grade || '-';
    
    // 투자 의견
    const opinionBadge = document.getElementById('investmentOpinion');
    const opinion = analysis.investment_opinion || '분석 중';
    if (opinionBadge) {
        opinionBadge.textContent = opinion;
        
        if (opinion.includes('매수')) {
            opinionBadge.className = 'opinion-badge buy';
        } else if (opinion.includes('매도')) {
            opinionBadge.className = 'opinion-badge sell';
        } else {
            opinionBadge.className = 'opinion-badge hold';
        }
    }
    
    const opinionSubEl = document.getElementById('opinionSub');
    if (opinionSubEl) opinionSubEl.textContent = analysis.current_vs_fair || '';
    
    // 뉴스 분석
    const newsAnalysis = analysis.news_analysis || {};
    const newsScoreEl = document.getElementById('newsScore');
    const newsSentimentEl = document.getElementById('newsSentiment');
    if (newsScoreEl) newsScoreEl.textContent = newsAnalysis.overall_score || '-';
    if (newsSentimentEl) newsSentimentEl.textContent = newsAnalysis.overall_sentiment || '-';
    
    // 뉴스 감성 업데이트
    if (newsAnalysis.top_news) {
        updateNewsWithSentiment(newsAnalysis.top_news);
    }
    
    // 평가 요약
    const evalSummaryEl = document.getElementById('evaluationSummary');
    if (evalSummaryEl) {
        evalSummaryEl.textContent = analysis.evaluation_summary || 'AI 분석을 완료하지 못했습니다.';
    }
    
    // 점수 브레이크다운
    const financial = analysis.financial_health || {};
    const growth = analysis.growth_potential || {};
    const profit = analysis.profitability || {};
    
    updateBreakdown('financial', financial.score, financial.grade);
    updateBreakdown('growth', growth.score, growth.grade);
    updateBreakdown('profit', profit.score, profit.grade);
    
    // 상세 평가 아코디언
    displayDetailEvaluations(analysis.detail_key_list, analysis.detail_evaluations);
    
    // 가격 예측
    const forecast = analysis.price_forecast || {};
    const forecast3mEl = document.getElementById('forecast3m');
    const forecast6mEl = document.getElementById('forecast6m');
    const forecast12mEl = document.getElementById('forecast12m');
    
    if (forecast3mEl) forecast3mEl.textContent = formatPrice(forecast['3month'] || 0);
    if (forecast6mEl) forecast6mEl.textContent = formatPrice(forecast['6month'] || 0);
    if (forecast12mEl) forecast12mEl.textContent = formatPrice(forecast['12month'] || 0);
    
    if (forecast.disclaimer) {
        const disclaimerEl = document.getElementById('forecastDisclaimer');
        if (disclaimerEl) disclaimerEl.textContent = '⚠️ ' + forecast.disclaimer;
    }
}

function updateBreakdown(type, score, grade) {
    const bar = document.getElementById(`${type}Bar`);
    const gradeEl = document.getElementById(`${type}Grade`);
    
    if (bar && score) {
        bar.style.width = `${score}%`;
    }
    if (gradeEl && grade) {
        gradeEl.textContent = grade;
        gradeEl.style.color = getGradeColor(grade);
    }
}

function displayDetailEvaluations(keyList, evaluations) {
    const container = document.getElementById('detailAccordion');
    
    if (!keyList || !evaluations) {
        container.innerHTML = '<p>상세 평가를 불러올 수 없습니다.</p>';
        return;
    }
    
    // 모든 항목을 기본으로 열린 상태로 표시
    container.innerHTML = keyList.map((key) => `
        <div class="accordion-item open">
            <div class="accordion-header" onclick="toggleAccordion(this)">
                <span class="accordion-title">
                    <i class="fas ${getKeyIcon(key)}"></i>
                    ${key}
                </span>
                <i class="fas fa-chevron-down accordion-icon"></i>
            </div>
            <div class="accordion-content">
                <div class="accordion-body">${evaluations[key] || '평가 내용 없음'}</div>
            </div>
        </div>
    `).join('');
}

function updateNewsWithSentiment(topNews) {
    const newsItems = document.querySelectorAll('.news-item');
    
    topNews.forEach((news, index) => {
        if (newsItems[index]) {
            const dot = newsItems[index].querySelector('.news-sentiment-dot');
            if (dot) {
                dot.className = `news-sentiment-dot ${news.sentiment === '긍정' ? 'positive' : news.sentiment === '부정' ? 'negative' : 'neutral'}`;
            }
        }
    });
}

// ============================================
// 차트 생성
// ============================================

let currentChartMode = '1y'; // '1y' or 'forecast'

function showChart(mode) {
    currentChartMode = mode;
    
    // 버튼 활성화 상태 변경
    document.getElementById('chart1y').classList.toggle('active', mode === '1y');
    document.getElementById('chartForecast').classList.toggle('active', mode === 'forecast');
    
    // 범례 및 면책조항 표시
    const legend = document.getElementById('chartLegend');
    const disclaimer = document.getElementById('chartDisclaimer');
    
    if (mode === '1y') {
        legend.innerHTML = `
            <span class="legend-item"><span class="dot price"></span> 종가</span>
            <span class="legend-item"><span class="dot ma5"></span> 5일선</span>
            <span class="legend-item"><span class="dot ma20"></span> 20일선</span>
            <span class="legend-item"><span class="dot ma60"></span> 60일선</span>
        `;
        disclaimer.style.display = 'none';
    } else {
        legend.innerHTML = `
            <span class="legend-item"><span class="dot price"></span> 실제 주가</span>
            <span class="legend-item"><span class="dot forecast"></span> AI 예측</span>
        `;
        disclaimer.style.display = 'block';
    }
    
    // 차트 다시 그리기
    createPriceChart();
}

async function createPriceChart() {
    const ctx = document.getElementById('priceChart');
    if (!ctx) return;
    
    // 기존 차트 제거
    if (priceChart) {
        priceChart.destroy();
    }
    
    const priceHistory = reportData?.krx?.price_history || [];
    
    if (!priceHistory.length) {
        return;
    }
    
    if (currentChartMode === '1y') {
        createYearlyChart(ctx, priceHistory);
    } else {
        createForecastChart(ctx, priceHistory);
    }
}

function createYearlyChart(ctx, priceHistory) {
    // 1년 실적 차트 (예측 없음)
    const labels = priceHistory.map(p => p.date);
    const prices = priceHistory.map(p => p.close);
    
    // 이동평균 계산
    const ma5 = calculateMA(prices, 5);
    const ma20 = calculateMA(prices, 20);
    const ma60 = calculateMA(prices, 60);
    
    priceChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [
                {
                    label: '종가',
                    data: prices,
                    borderColor: '#0066cc',
                    backgroundColor: 'rgba(0, 102, 204, 0.1)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.1,
                    pointRadius: 0,
                    pointHoverRadius: 4
                },
                {
                    label: '5일선',
                    data: ma5,
                    borderColor: '#f59e0b',
                    borderWidth: 1.5,
                    fill: false,
                    tension: 0.1,
                    pointRadius: 0
                },
                {
                    label: '20일선',
                    data: ma20,
                    borderColor: '#10b981',
                    borderWidth: 1.5,
                    fill: false,
                    tension: 0.1,
                    pointRadius: 0
                },
                {
                    label: '60일선',
                    data: ma60,
                    borderColor: '#8b5cf6',
                    borderWidth: 1.5,
                    fill: false,
                    tension: 0.1,
                    pointRadius: 0
                }
            ]
        },
        options: getChartOptions()
    });
}

function createForecastChart(ctx, priceHistory) {
    // 최근 6개월 + 1년 예측 차트
    const forecast = aiAnalysis?.price_forecast || {};
    
    // 최근 6개월 데이터 추출
    const sixMonthsAgo = new Date();
    sixMonthsAgo.setMonth(sixMonthsAgo.getMonth() - 6);
    
    const recentHistory = priceHistory.filter(p => new Date(p.date) >= sixMonthsAgo);
    const recentLabels = recentHistory.map(p => p.date);
    const recentPrices = recentHistory.map(p => p.close);
    
    // 월별 예측 데이터 생성
    const forecastLabels = [];
    const forecastPrices = [];
    
    if (forecast['3month'] && forecast['6month'] && forecast['12month']) {
        const lastDate = new Date(priceHistory[priceHistory.length - 1].date);
        const lastPrice = recentPrices[recentPrices.length - 1];
        
        // 시작점
        forecastLabels.push(priceHistory[priceHistory.length - 1].date);
        forecastPrices.push(lastPrice);
        
        // 월별 보간 (1~12개월)
        for (let i = 1; i <= 12; i++) {
            const futureDate = new Date(lastDate);
            futureDate.setMonth(futureDate.getMonth() + i);
            forecastLabels.push(futureDate.toISOString().split('T')[0]);
            
            // 보간 계산
            let price;
            if (i <= 3) {
                price = lastPrice + (forecast['3month'] - lastPrice) * (i / 3);
            } else if (i <= 6) {
                price = forecast['3month'] + (forecast['6month'] - forecast['3month']) * ((i - 3) / 3);
            } else {
                price = forecast['6month'] + (forecast['12month'] - forecast['6month']) * ((i - 6) / 6);
            }
            forecastPrices.push(Math.round(price));
        }
    }
    
    // 전체 라벨 (실제 + 예측)
    const allLabels = [...recentLabels, ...forecastLabels.slice(1)];
    
    priceChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: allLabels,
            datasets: [
                {
                    label: '실제 주가',
                    data: [...recentPrices, ...Array(forecastLabels.length - 1).fill(null)],
                    borderColor: '#0066cc',
                    backgroundColor: 'rgba(0, 102, 204, 0.1)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.1,
                    pointRadius: 0,
                    pointHoverRadius: 4
                },
                {
                    label: 'AI 예측',
                    data: [...Array(recentPrices.length - 1).fill(null), ...forecastPrices],
                    borderColor: '#94a3b8',
                    borderWidth: 2,
                    borderDash: [5, 5],
                    fill: false,
                    tension: 0.3,
                    pointRadius: 3,
                    pointBackgroundColor: '#94a3b8'
                }
            ]
        },
        options: getChartOptions()
    });
}

function getChartOptions() {
    return {
        responsive: true,
        maintainAspectRatio: false,
        interaction: {
            intersect: false,
            mode: 'index'
        },
        plugins: {
            legend: {
                display: false
            },
            tooltip: {
                callbacks: {
                    label: function(context) {
                        if (context.parsed.y !== null) {
                            return `${context.dataset.label}: ${context.parsed.y.toLocaleString()}원`;
                        }
                        return '';
                    }
                }
            }
        },
        scales: {
            x: {
                grid: {
                    display: false
                },
                ticks: {
                    maxTicksLimit: 12
                }
            },
            y: {
                grid: {
                    color: '#f3f4f6'
                },
                ticks: {
                    callback: function(value) {
                        return value.toLocaleString() + '원';
                    }
                }
            }
        }
    };
}

function calculateMA(prices, period) {
    const ma = [];
    for (let i = 0; i < prices.length; i++) {
        if (i < period - 1) {
            ma.push(null);
        } else {
            const sum = prices.slice(i - period + 1, i + 1).reduce((a, b) => a + b, 0);
            ma.push(Math.round(sum / period));
        }
    }
    return ma;
}

// ============================================
// 채팅 기능
// ============================================

function toggleChat() {
    const sidebar = document.getElementById('chatSidebar');
    sidebar.classList.toggle('collapsed');
}

function toggleMobileChat() {
    const sidebar = document.getElementById('chatSidebar');
    const toggleBtn = document.getElementById('mobileChatToggle');
    
    sidebar.classList.toggle('open');
    
    // 버튼 아이콘 변경
    if (sidebar.classList.contains('open')) {
        toggleBtn.innerHTML = '<i class="fas fa-times"></i>';
    } else {
        toggleBtn.innerHTML = '<i class="fas fa-comments"></i>';
    }
}

async function sendChatMessage() {
    const input = document.getElementById('chatInput');
    const message = input.value.trim();
    
    if (!message) return;
    
    // 사용자 메시지 표시
    addChatMessage(message, 'user');
    input.value = '';
    
    // 로딩 표시
    const loadingMsg = addChatMessage('답변 생성 중...', 'bot');
    
    try {
        const response = await fetch('/api/report/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                message: message,
                report_context: JSON.stringify({
                    company: COMPANY_DATA.name,
                    analysis: aiAnalysis
                })
            })
        });
        
        const result = await response.json();
        
        // 로딩 메시지 제거
        loadingMsg.remove();
        
        if (result.success) {
            addChatMessage(result.response, 'bot');
        } else {
            addChatMessage('죄송합니다. 응답을 생성하지 못했습니다.', 'bot');
        }
    } catch (error) {
        loadingMsg.remove();
        addChatMessage('오류가 발생했습니다. 다시 시도해주세요.', 'bot');
    }
}

function addChatMessage(text, type) {
    const container = document.getElementById('chatMessages');
    const msgDiv = document.createElement('div');
    msgDiv.className = `chat-message ${type}`;
    msgDiv.innerHTML = `<div class="message-content">${text}</div>`;
    container.appendChild(msgDiv);
    container.scrollTop = container.scrollHeight;
    return msgDiv;
}

function handleChatKeypress(event) {
    if (event.key === 'Enter') {
        sendChatMessage();
    }
}

// ============================================
// 유틸리티 함수
// ============================================

function formatPrice(price) {
    if (!price) return '-';
    return Number(price).toLocaleString() + '원';
}

function formatDate(dateStr) {
    if (!dateStr) return '-';
    
    // YYYYMMDD 형식
    if (dateStr.length === 8 && !dateStr.includes('-')) {
        return `${dateStr.slice(0, 4)}-${dateStr.slice(4, 6)}-${dateStr.slice(6, 8)}`;
    }
    
    // 이미 포맷된 경우
    return dateStr.split('T')[0];
}

function getSignalClass(signal) {
    if (!signal) return 'neutral';
    if (signal.includes('강세') || signal.includes('유입')) return 'positive';
    if (signal.includes('약세') || signal.includes('유출') || signal.includes('과매')) return 'negative';
    return 'neutral';
}

function getGradeColor(grade) {
    switch(grade) {
        case 'A': case 'A+': return '#10b981';
        case 'B': case 'B+': return '#3b82f6';
        case 'C': return '#f59e0b';
        case 'D': return '#f97316';
        case 'F': return '#ef4444';
        default: return '#6b7280';
    }
}

function getKeyIcon(key) {
    const icons = {
        '재무건전성': 'fa-shield-alt',
        '성장성': 'fa-chart-line',
        '수익성': 'fa-coins',
        '시장평가': 'fa-balance-scale',
        '기술적분석': 'fa-chart-bar',
        '뉴스동향': 'fa-newspaper',
        '리스크': 'fa-exclamation-triangle'
    };
    return icons[key] || 'fa-circle';
}

function toggleAccordion(header) {
    const item = header.parentElement;
    item.classList.toggle('open');
}

function showLoading(show) {
    const overlay = document.getElementById('loadingOverlay');
    if (show) {
        overlay.classList.remove('hidden');
        startLoadingMessages();
    } else {
        overlay.classList.add('hidden');
        stopLoadingMessages();
        // 섹션 순차 표시 애니메이션
        revealSections();
    }
}

function startLoadingMessages() {
    loadingMessageIndex = 0;
    updateLoadingMessage();
    
    loadingMessageInterval = setInterval(() => {
        loadingMessageIndex = (loadingMessageIndex + 1) % (LOADING_MESSAGES.length - 1);
        updateLoadingMessage();
    }, 2000); // 2초마다 메시지 변경
}

function stopLoadingMessages() {
    if (loadingMessageInterval) {
        clearInterval(loadingMessageInterval);
        loadingMessageInterval = null;
    }
    // 완료 메시지 표시
    const stepEl = document.getElementById('loadingStep');
    if (stepEl) {
        stepEl.textContent = LOADING_MESSAGES[LOADING_MESSAGES.length - 1];
    }
}

function updateLoadingMessage() {
    const stepEl = document.getElementById('loadingStep');
    const textEl = document.getElementById('loadingText');
    
    if (stepEl) {
        stepEl.classList.add('fade-out');
        setTimeout(() => {
            stepEl.textContent = LOADING_MESSAGES[loadingMessageIndex];
            stepEl.classList.remove('fade-out');
            stepEl.classList.add('fade-in');
            setTimeout(() => stepEl.classList.remove('fade-in'), 300);
        }, 300);
    }
}

function updateLoadingStep(step, progress) {
    // 특정 단계별 메시지 설정
    const stepMessages = {
        10: 1,   // KRX
        30: 2,   // DART
        50: 3,   // 뉴스
        70: 4,   // AI 분석
        90: 5,   // 차트
        100: 6   // 완료
    };
    
    if (stepMessages[progress] !== undefined) {
        loadingMessageIndex = stepMessages[progress];
        updateLoadingMessage();
    }
}

async function revealSections() {
    const sections = document.querySelectorAll('.section');
    
    for (let i = 0; i < sections.length; i++) {
        const section = sections[i];
        section.classList.add('section-hidden');
        
        await sleep(150);
        
        section.classList.remove('section-hidden');
        section.classList.add('section-reveal');
        
        // 애니메이션 후 클래스 제거
        setTimeout(() => {
            section.classList.remove('section-reveal');
        }, 600);
    }
}

function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

function regenerateReport() {
    location.reload();
}

// ============================================
// PDF 다운로드
// ============================================

async function downloadPDF() {
    const btn = document.getElementById('downloadPdfBtn');
    if (!btn) return;
    
    const originalText = btn.innerHTML;
    
    btn.disabled = true;
    btn.innerHTML = '<i class="fas fa-hourglass-half"></i> 생성 중...';
    
    try {
        // 채팅 사이드바 숨기기
        const chatSidebar = document.getElementById('chatSidebar');
        let originalDisplay = '';
        if (chatSidebar) {
            originalDisplay = chatSidebar.style.display;
            chatSidebar.style.display = 'none';
        }
        
        // 메인 콘텐츠 스타일 임시 조정
        const reportMain = document.querySelector('.report-main');
        let originalPadding = '';
        if (reportMain) {
            originalPadding = reportMain.style.paddingRight;
            reportMain.style.paddingRight = '32px';
        }
        
        // 로딩 오버레이 숨기기
        const loadingOverlay = document.getElementById('loadingOverlay');
        if (loadingOverlay) loadingOverlay.classList.add('hidden');
        
        // PDF 옵션
        const opt = {
            margin: [10, 10, 10, 10],
            filename: `KORA_AI_${COMPANY_DATA.name}_분석보고서_${formatDateForFile()}.pdf`,
            image: { type: 'jpeg', quality: 0.98 },
            html2canvas: { 
                scale: 2,
                useCORS: true,
                logging: false
            },
            jsPDF: { 
                unit: 'mm', 
                format: 'a4', 
                orientation: 'portrait' 
            },
            pagebreak: { mode: ['avoid-all', 'css', 'legacy'] }
        };
        
        // PDF 생성
        const element = document.querySelector('.report-container');
        await html2pdf().set(opt).from(element).save();
        
        // 원래 스타일 복원
        if (chatSidebar) chatSidebar.style.display = originalDisplay;
        if (reportMain) reportMain.style.paddingRight = originalPadding;
        
        btn.innerHTML = '<i class="fas fa-check"></i> 저장 완료!';
        setTimeout(() => {
            btn.innerHTML = originalText;
            btn.disabled = false;
        }, 2000);
        
    } catch (error) {
        console.error('PDF generation error:', error);
        alert('PDF 생성 중 오류가 발생했습니다.');
        btn.innerHTML = originalText;
        btn.disabled = false;
    }
}

function formatDateForFile() {
    const now = new Date();
    return `${now.getFullYear()}${String(now.getMonth() + 1).padStart(2, '0')}${String(now.getDate()).padStart(2, '0')}`;
}

function enablePdfDownload() {
    const btn = document.getElementById('downloadPdfBtn');
    if (btn) {
        btn.disabled = false;
    }
}

