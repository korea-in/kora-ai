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
    const headerHeight = 90; // 헤더 높이 + 여유 공간
    
    // 클릭 시 스크롤 (오프셋 적용)
    navLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const targetId = this.getAttribute('href').substring(1);
            const targetSection = document.getElementById(targetId);
            if (targetSection) {
                const targetPosition = targetSection.offsetTop - headerHeight;
                window.scrollTo({
                    top: targetPosition,
                    behavior: 'smooth'
                });
            }
        });
    });
    
    // 스크롤 시 활성 네비게이션 업데이트
    window.addEventListener('scroll', () => {
        let current = '';
        const scrollPos = window.scrollY + headerHeight + 50;
        
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

// 네비게이션 토글
function toggleNav() {
    const nav = document.getElementById('reportNav');
    const main = document.querySelector('.report-main');
    
    nav.classList.toggle('collapsed');
    main.classList.toggle('nav-collapsed');
}

// 채팅창 토글
function toggleChat() {
    const chat = document.getElementById('chatSidebar');
    const main = document.querySelector('.report-main');
    const toggleBtn = document.getElementById('chatToggleBtn');
    
    chat.classList.toggle('collapsed');
    main.classList.toggle('chat-collapsed');
    
    // 아이콘 방향 변경
    if (chat.classList.contains('collapsed')) {
        toggleBtn.innerHTML = '<i class="fas fa-chevron-left"></i>';
    } else {
        toggleBtn.innerHTML = '<i class="fas fa-chevron-right"></i>';
    }
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
        
        // 5단계: 요청사항 답변 (있는 경우)
        if (COMPANY_DATA.requestText && COMPANY_DATA.requestText.trim()) {
            await loadRequestAnswer();
        }
        
        // 6단계: 보고서 저장 및 크레딧 차감
        await saveReportAndDeductCredits();
        
        // 완료
        updateLoadingStep('완료!', 100);
        await sleep(500);
        showLoading(false);
        
        // PDF 다운로드 버튼 활성화
        enablePdfDownload();
        
    } catch (error) {
        console.error('Report loading error:', error);
        alert('보고서 생성 중 오류가 발생했습니다: ' + error.message);
        showLoading(false);
    }
}

// 보고서 저장 및 크레딧 차감
async function saveReportAndDeductCredits() {
    try {
        console.log('[saveReport] Starting save...');
        console.log('[saveReport] COMPANY_DATA:', COMPANY_DATA);
        console.log('[saveReport] aiAnalysis:', aiAnalysis ? 'exists' : 'null');
        
        const response = await fetch('/api/report/save', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                company_name: COMPANY_DATA.name,
                ticker: COMPANY_DATA.ticker,
                market: COMPANY_DATA.market,
                analysis: aiAnalysis,
                raw_data: reportData
            })
        });
        
        const result = await response.json();
        console.log('[saveReport] Response:', result);
        
        if (result.success) {
            console.log('[saveReport] Report saved successfully:', result.report_id);
            console.log('[saveReport] Credits remaining:', result.credits_remaining);
            
            // 크레딧 배지 업데이트 (헤더에 있는 경우)
            const creditBadge = document.querySelector('.credit-badge span');
            if (creditBadge) {
                creditBadge.textContent = result.credits_remaining;
            }
        } else {
            console.warn('[saveReport] Warning:', result.error);
            // 크레딧 부족 등의 오류는 사용자에게 알림하지 않음 (보고서는 이미 표시됨)
        }
    } catch (error) {
        console.error('[saveReport] Error:', error);
        // 저장 실패해도 보고서는 계속 표시
    }
}

// 요청사항 답변 로드
async function loadRequestAnswer() {
    const requestSection = document.getElementById('section-request');
    const requestQuestion = document.getElementById('requestQuestion');
    const answerLoading = document.getElementById('answerLoading');
    const answerContent = document.getElementById('answerContent');
    
    if (!requestSection || !requestQuestion) return;
    
    // 섹션 표시
    requestSection.classList.remove('hidden');
    requestQuestion.textContent = COMPANY_DATA.requestText;
    if (answerLoading) answerLoading.classList.remove('hidden');
    if (answerContent) answerContent.textContent = '';
    
    try {
        const response = await fetch('/api/report/request-answer', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                company_name: COMPANY_DATA.name,
                request_text: COMPANY_DATA.requestText,
                report_context: JSON.stringify({
                    krx: reportData?.krx,
                    dart: reportData?.dart,
                    analysis: aiAnalysis
                })
            })
        });
        
        const result = await response.json();
        
        if (answerLoading) answerLoading.classList.add('hidden');
        
        if (result.success && result.answer) {
            if (answerContent) answerContent.textContent = result.answer;
        } else {
            if (answerContent) answerContent.textContent = '답변을 생성하지 못했습니다. 다시 시도해주세요.';
        }
    } catch (error) {
        console.error('Request answer error:', error);
        if (answerLoading) answerLoading.classList.add('hidden');
        if (answerContent) answerContent.textContent = '답변 생성 중 오류가 발생했습니다.';
    }
}

// ============================================
// 기본 데이터 표시
// ============================================

function displayBasicData(data) {
    const krx = data.krx || {};
    const dart = data.dart || {};
    const news = data.news || {};
    
    // 디버깅용 로그
    console.log('📊 밸류에이션 데이터:', krx.valuation);
    console.log('💰 배당 데이터:', dart.dividend);
    
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
    const dividend = dart.dividend || [];
    
    // 디버깅: 밸류에이션 데이터 구조 확인
    console.log('📊 밸류에이션 데이터:', val);
    console.log('📊 BPS 값:', val.bps, '| PBR 값:', val.pbr);
    console.log('📊 시가총액:', krx.summary?.market_cap, '| 현재가:', krx.current_price?.close);
    
    // DART 주식수 정보
    const stockInfo = dart.stock_info || {};
    console.log('📊 DART 주식수 정보:', stockInfo);
    if (stockInfo.total_shares) {
        console.log('📊 DART 발행주식총수:', stockInfo.total_shares.toLocaleString());
    }
    
    // 자본총계 확인
    const keyAccounts = dart.financials?.key_accounts || {};
    let totalEquity = null;
    for (const [key, value] of Object.entries(keyAccounts)) {
        if (key.includes('자본총계') || key.includes('자산총계') || key.includes('부채총계')) {
            console.log(`📊 ${key}:`, value);
            if (key.includes('자본총계')) {
                totalEquity = value?.current || value;
            }
        }
    }
    
    // 디버깅: 배당 데이터 구조 확인
    if (dividend.length > 0) {
        console.log('📋 배당 데이터 상세:', dividend.map(d => ({ se: d.se, thstrm: d.thstrm })));
    }
    
    // BPS 계산 실패 원인 분석
    if (!val.bps) {
        const marketCap = krx.summary?.market_cap;
        const currentPrice = krx.current_price?.close;
        const dartShares = stockInfo.total_shares;
        
        let reason = [];
        if (!totalEquity) reason.push('자본총계 없음');
        if (!marketCap && !dartShares) reason.push('주식수 계산 불가 (시가총액/DART 모두 없음)');
        if (marketCap && !currentPrice) reason.push('현재가 없음');
        
        console.warn('⚠️ BPS를 구하지 못함. 원인:', reason.join(', ') || '알 수 없음');
        console.warn('⚠️ 디버깅 정보: 자본총계=', totalEquity, ', 시가총액=', marketCap, ', 현재가=', currentPrice, ', DART주식수=', dartShares);
    }
    
    setTextSafe('perValue', val.per ? `${val.per}배` : '-');
    setTextSafe('pbrValue', val.pbr ? `${val.pbr}배` : '-');
    setTextSafe('epsValue', val.eps ? formatPrice(val.eps) : '-');
    setTextSafe('bpsValue', val.bps ? formatPrice(val.bps) : '-');
    
    // 배당수익률 - DART 데이터 우선, 없으면 KRX 데이터
    let divYield = val.div_yield;
    let dpsValue = val.dps;
    
    if (dividend.length > 0) {
        // 현금배당수익률(%) 찾기 - 정확히 매칭
        const divYieldItem = dividend.find(d => d.se && d.se === '현금배당수익률(%)');
        if (divYieldItem && divYieldItem.thstrm && divYieldItem.thstrm !== '-') {
            const parsed = parseFloat(divYieldItem.thstrm.replace(/[^0-9.]/g, ''));
            if (!isNaN(parsed)) divYield = parsed;
        }
        
        // 주당 현금배당금(원) 찾기 - 정확히 매칭 (총액이 아닌 주당 배당금)
        const dpsItem = dividend.find(d => d.se && d.se === '주당 현금배당금(원)');
        if (dpsItem && dpsItem.thstrm && dpsItem.thstrm !== '-') {
            const parsed = parseInt(dpsItem.thstrm.replace(/[^0-9]/g, ''));
            if (!isNaN(parsed) && parsed > 0) dpsValue = parsed;
        }
    }
    
    setTextSafe('divYield', divYield ? `${divYield}%` : '-');
    setTextSafe('dpsValue', dpsValue ? formatPrice(dpsValue) : '-');
    
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
            <tr><td>업종</td><td>${companyInfo.induty_name || companyInfo.induty_code || '-'}</td></tr>
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
    
    // 재무비율 분석 (calculated_ratios도 함께 전달)
    displayFinancialRatios(dart.financial_index || {}, dart.calculated_ratios || {});
}

// 재무비율 표시 - DART 데이터 기반 동적 생성
function displayFinancialRatios(index, calculatedRatios) {
    console.log('📊 Financial Index:', index);
    console.log('📊 Calculated Ratios:', calculatedRatios);
    
    const container = document.getElementById('ratiosContainer');
    const titleEl = document.getElementById('ratiosSectionTitle');
    
    if (!container) return;
    
    // 지표별 메타 정보 (정상 범위, 공식, 설명)
    const ratioMeta = {
        // 수익성 지표
        'ROE': { range: '10% 이상 양호', formula: '당기순이익 ÷ 자기자본 × 100', unit: '%', higherBetter: true },
        'ROA': { range: '5% 이상 양호', formula: '당기순이익 ÷ 총자산 × 100', unit: '%', higherBetter: true },
        '총자산영업이익률': { range: '5% 이상 양호', formula: '영업이익 ÷ 총자산 × 100', unit: '%', higherBetter: true },
        '순이익률': { range: '업종 평균 비교', formula: '당기순이익 ÷ 매출액 × 100', unit: '%', higherBetter: true },
        '총포괄이익률': { range: '업종 평균 비교', formula: '총포괄이익 ÷ 매출액 × 100', unit: '%', higherBetter: true },
        '매출총이익률': { range: '업종 평균 비교', formula: '매출총이익 ÷ 매출액 × 100', unit: '%', higherBetter: true },
        '영업이익률': { range: '10% 이상 양호', formula: '영업이익 ÷ 매출액 × 100', unit: '%', higherBetter: true },
        '자기자본영업이익률': { range: '높을수록 양호', formula: '영업이익 ÷ 자기자본 × 100', unit: '%', higherBetter: true },
        '납입자본이익률': { range: '높을수록 양호', formula: '당기순이익 ÷ 납입자본 × 100', unit: '%', higherBetter: true },
        
        // 안정성 지표
        '부채비율': { range: '100% 이하 양호', formula: '부채총계 ÷ 자기자본 × 100', unit: '%', higherBetter: false },
        '자기자본비율': { range: '50% 이상 양호', formula: '자기자본 ÷ 총자산 × 100', unit: '%', higherBetter: true },
        '유동비율': { range: '150~200% 양호', formula: '유동자산 ÷ 유동부채 × 100', unit: '%', higherBetter: true },
        '당좌비율': { range: '100% 이상 양호', formula: '(유동자산-재고) ÷ 유동부채 × 100', unit: '%', higherBetter: true },
        '이자보상배율': { range: '3배 이상 양호', formula: '영업이익 ÷ 이자비용', unit: '배', higherBetter: true },
        '재무레버리지': { range: '낮을수록 안정', formula: '총자산 ÷ 자기자본', unit: '%', higherBetter: false },
        '자본유보율': { range: '높을수록 양호', formula: '잉여금 ÷ 납입자본 × 100', unit: '%', higherBetter: true },
        '비유동비율': { range: '100% 이하 양호', formula: '비유동자산 ÷ 자기자본 × 100', unit: '%', higherBetter: false },
        
        // 성장성 지표
        '매출액증가율(YoY)': { range: '양수 양호', formula: '(금년매출-전년매출) ÷ 전년매출 × 100', unit: '%', higherBetter: true },
        '영업이익증가율(YoY)': { range: '양수 양호', formula: '(금년영업이익-전년) ÷ 전년 × 100', unit: '%', higherBetter: true },
        '순이익증가율(YoY)': { range: '양수 양호', formula: '(금년순이익-전년) ÷ 전년 × 100', unit: '%', higherBetter: true },
        '총자산증가율': { range: '양수 양호', formula: '(금년총자산-전년) ÷ 전년 × 100', unit: '%', higherBetter: true },
        '자기자본증가율': { range: '양수 양호', formula: '(금년자본-전년) ÷ 전년 × 100', unit: '%', higherBetter: true },
        '총포괄이익증가율(YoY)': { range: '양수 양호', formula: '(금년-전년) ÷ 전년 × 100', unit: '%', higherBetter: true },
        '부채총계증가율': { range: '낮을수록 안정', formula: '(금년부채-전년) ÷ 전년 × 100', unit: '%', higherBetter: false },
        
        // 활동성 지표
        '총자산회전율': { range: '1회 이상 양호', formula: '매출액 ÷ 총자산', unit: '회', higherBetter: true },
        '재고자산회전율': { range: '높을수록 양호', formula: '매출원가 ÷ 평균재고', unit: '회', higherBetter: true },
        '매출채권회전율': { range: '높을수록 양호', formula: '매출액 ÷ 평균매출채권', unit: '회', higherBetter: true },
        '자기자본회전율': { range: '높을수록 양호', formula: '매출액 ÷ 자기자본', unit: '회', higherBetter: true },
        '배당성향(%)': { range: '20~40% 적정', formula: '배당금 ÷ 당기순이익 × 100', unit: '%', higherBetter: null }
    };
    
    // 카테고리 순서 및 설명
    const categories = [
        { key: '수익성지표', title: '수익성 지표', desc: '이익 창출 능력', icon: 'fas fa-chart-line' },
        { key: '안정성지표', title: '안정성 지표', desc: '재무구조 안정성', icon: 'fas fa-shield-alt' },
        { key: '성장성지표', title: '성장성 지표', desc: '기업 성장 추이', icon: 'fas fa-seedling' },
        { key: '활동성지표', title: '활동성 지표', desc: '자산 활용 효율성', icon: 'fas fa-sync-alt' }
    ];
    
    // 기준일 추출
    let baseDate = '';
    for (const cat of categories) {
        const items = index[cat.key] || [];
        if (items.length > 0 && items[0].stlm_dt) {
            baseDate = items[0].stlm_dt;
            break;
        }
    }
    
    // 제목에 기준일 추가
    if (titleEl && baseDate) {
        titleEl.innerHTML = `<i class="fas fa-balance-scale"></i> 재무비율 분석 <span class="ratio-date">(${baseDate} 기준)</span>`;
    }
    
    let html = '';
    let hasAnyData = false;
    
    for (const cat of categories) {
        const items = index[cat.key] || [];
        
        // idx_val이 유효한 숫자인 항목만 필터링
        const filteredItems = items.filter(item => {
            if (!item.idx_val || item.idx_val === '-' || item.idx_val === '') return false;
            // #####, NaN, 비정상 문자열 필터링
            const val = String(item.idx_val).trim();
            if (val.includes('#') || val.includes('N/A') || val.includes('nan')) return false;
            // 숫자로 변환 가능한지 확인
            const num = parseFloat(val.replace(/,/g, ''));
            return !isNaN(num) && isFinite(num);
        });
        
        // 같은 지표명(idx_nm)이 여러 개인 경우 가장 최근(첫 번째) 항목만 유지
        const seenNames = new Set();
        const validItems = filteredItems.filter(item => {
            const name = item.idx_nm || '';
            if (seenNames.has(name)) return false;
            seenNames.add(name);
            return true;
        });
        
        if (validItems.length === 0) continue;
        hasAnyData = true;
        
        html += `
            <div class="ratio-category">
                <h3 class="ratio-category-title"><i class="${cat.icon}"></i> ${cat.title} <span class="cat-desc">(${cat.desc})</span></h3>
                <div class="ratio-grid">
        `;
        
        for (const item of validItems) {
            const name = item.idx_nm || '';
            const value = parseFloat(String(item.idx_val).replace(/,/g, ''));
            const meta = ratioMeta[name] || { range: '-', formula: '-', unit: '%', higherBetter: null };
            
            // 상태 계산
            let statusClass = 'neutral';
            let statusText = '-';
            
            if (meta.higherBetter !== null && !isNaN(value)) {
                if (meta.higherBetter) {
                    statusClass = value > 0 ? 'safe' : 'danger';
                    statusText = value > 0 ? '양호' : '주의';
                } else {
                    // 부채비율 등 특수 케이스
                    if (name.includes('부채비율')) {
                        statusClass = value <= 100 ? 'safe' : value <= 200 ? 'warning' : 'danger';
                        statusText = value <= 100 ? '양호' : value <= 200 ? '보통' : '주의';
                    } else {
                        statusClass = value < 50 ? 'safe' : 'warning';
                        statusText = value < 50 ? '양호' : '보통';
                    }
                }
            }
            
            html += `
                <div class="ratio-card ${statusClass}">
                    <div class="ratio-header">
                        <span class="ratio-name">${name}</span>
                        <span class="ratio-tooltip">
                            <i class="fas fa-question-circle"></i>
                            <span class="tooltip-text">적정: ${meta.range}<br>공식: ${meta.formula}</span>
                        </span>
                    </div>
                    <div class="ratio-value">${value.toFixed(2)}${meta.unit}</div>
                    <div class="ratio-status ${statusClass}">${statusText}</div>
                </div>
            `;
        }
        
        html += '</div></div>';
    }
    
    if (!hasAnyData) {
        html = '<div class="ratio-no-data"><i class="fas fa-info-circle"></i> 재무비율 데이터가 없습니다.</div>';
    }
    
    container.innerHTML = html;
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
    
    // DART 링크 설정 - 해당 기업의 정기보고서 목록 페이지로 이동
    const dartLinkEl = document.getElementById('dartLink');
    if (dartLinkEl && COMPANY_DATA.corpCode) {
        // DART 정기보고서 검색 페이지에서 해당 기업 조회
        dartLinkEl.href = `https://dart.fss.or.kr/dsab002/main.do?crp_cd=${COMPANY_DATA.corpCode}`;
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
    const grade = analysis.investment_grade || '';
    
    const scoreValueEl = document.getElementById('scoreValue');
    if (scoreValueEl) scoreValueEl.textContent = score;
    
    // 원형 프로그레스 (시계방향 애니메이션)
    const circle = document.getElementById('scoreCircle');
    if (circle) {
        const circumference = 2 * Math.PI * 45; // 약 283
        
        // 점수에 따른 색상 설정
        let strokeColor;
        if (score >= 80) {
            strokeColor = '#10b981'; // 녹색 (매우 양호)
        } else if (score >= 60) {
            strokeColor = '#3b82f6'; // 파란색 (양호)
        } else if (score >= 40) {
            strokeColor = '#f59e0b'; // 주황색 (보통)
        } else {
            strokeColor = '#ef4444'; // 빨간색 (주의)
        }
        circle.style.stroke = strokeColor;
        
        // 초기값 설정 (0에서 시작)
        circle.style.strokeDasharray = circumference;
        circle.style.strokeDashoffset = circumference;
        
        // 약간의 딜레이 후 애니메이션 시작
        setTimeout(() => {
            circle.style.transition = 'stroke-dashoffset 1.5s ease-out, stroke 0.5s ease';
            circle.style.strokeDashoffset = circumference - (score / 100) * circumference;
        }, 100);
    }
    
    // 제목에 등급 표시
    const scoreLabelEl = document.getElementById('scoreLabel');
    if (scoreLabelEl) {
        scoreLabelEl.textContent = grade ? `투자 점수(${grade})` : '투자 점수';
    }
    
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
    const newsSummaryTextEl = document.getElementById('newsSummaryText');
    
    if (newsScoreEl) newsScoreEl.textContent = newsAnalysis.overall_score || '-';
    if (newsSentimentEl) {
        const sentiment = newsAnalysis.overall_sentiment || '-';
        newsSentimentEl.textContent = sentiment;
        // 감성에 따라 클래스 추가
        newsSentimentEl.classList.remove('positive', 'negative', 'neutral');
        if (sentiment.includes('긍정')) {
            newsSentimentEl.classList.add('positive');
        } else if (sentiment.includes('부정')) {
            newsSentimentEl.classList.add('negative');
        } else {
            newsSentimentEl.classList.add('neutral');
        }
    }
    if (newsSummaryTextEl && newsAnalysis.summary) {
        newsSummaryTextEl.textContent = newsAnalysis.summary;
    }
    
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
    
    // 사업 분야 요약
    displayBusinessSummary(analysis.business_summary);
    
    // 요청사항 답변
    displayRequestAnswer(analysis.request_answer);
}

// 사업 분야 요약 표시
function displayBusinessSummary(businessSummary) {
    const container = document.getElementById('businessSummary');
    if (!container) return;
    
    if (!businessSummary) {
        container.innerHTML = '<p style="color: #64748b; text-align: center;">사업 분야 정보를 불러올 수 없습니다.</p>';
        return;
    }
    
    container.innerHTML = `
        <div class="business-grid">
            <div class="business-item">
                <div class="business-item-title"><i class="fas fa-industry"></i> 업종</div>
                <div class="business-item-content">${businessSummary.industry || '-'}</div>
            </div>
            <div class="business-item">
                <div class="business-item-title"><i class="fas fa-box"></i> 주력 상품/서비스</div>
                <div class="business-item-content">${businessSummary.main_products || '-'}</div>
            </div>
            <div class="business-item">
                <div class="business-item-title"><i class="fas fa-users"></i> 주요 경쟁사</div>
                <div class="business-item-content">${businessSummary.competitors || '-'}</div>
            </div>
            <div class="business-item">
                <div class="business-item-title"><i class="fas fa-chart-area"></i> 시장 동향</div>
                <div class="business-item-content">${businessSummary.market_trend || '-'}</div>
            </div>
        </div>
    `;
}

// 요청사항 답변 표시
function displayRequestAnswer(requestAnswer) {
    const section = document.getElementById('section-request');
    const questionEl = document.getElementById('requestQuestion');
    const loadingEl = document.getElementById('answerLoading');
    const contentEl = document.getElementById('answerContent');
    
    if (!section || !requestAnswer || !requestAnswer.question) {
        return; // 요청사항이 없으면 섹션 숨김 유지
    }
    
    // 요청사항 섹션 표시
    section.classList.remove('hidden');
    
    if (questionEl) questionEl.textContent = requestAnswer.question;
    if (loadingEl) loadingEl.classList.add('hidden');
    if (contentEl) contentEl.textContent = requestAnswer.answer || '답변을 생성하지 못했습니다.';
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

// 토글 스위치로 차트 변경
function toggleForecastChart() {
    const toggle = document.getElementById('forecastToggle');
    showChart(toggle.checked ? 'forecast' : '1y');
}

function showChart(mode) {
    currentChartMode = mode;
    
    // 버튼 상태 및 텍스트 업데이트
    const btn1y = document.getElementById('chart1y');
    const btnForecast = document.getElementById('chartForecast');
    
    if (mode === '1y') {
        btn1y.classList.add('active');
        btnForecast.classList.remove('active');
        btn1y.textContent = '1년 실적';
        btnForecast.textContent = '1년 예측보기';
    } else {
        btn1y.classList.remove('active');
        btnForecast.classList.add('active');
        btn1y.textContent = '현재 주가 보기';
        btnForecast.textContent = '1년 예측';
    }
    
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
            <span class="legend-item"><span class="dot price"></span> 월평균 주가</span>
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
    // 월별 평균으로 변환 + 1년 예측 차트
    const forecast = aiAnalysis?.price_forecast || {};
    
    // 과거 12개월 데이터를 월별 평균으로 변환
    const monthlyData = aggregateToMonthly(priceHistory);
    const monthlyLabels = monthlyData.map(m => m.label);
    const monthlyPrices = monthlyData.map(m => m.avgPrice);
    
    // 월별 예측 데이터 생성
    const forecastLabels = [];
    const forecastPrices = [];
    
    if (forecast['3month'] && forecast['6month'] && forecast['12month']) {
        const lastLabel = monthlyLabels[monthlyLabels.length - 1];
        const lastPrice = monthlyPrices[monthlyPrices.length - 1];
        
        // 시작점
        forecastLabels.push(lastLabel);
        forecastPrices.push(lastPrice);
        
        // 월별 보간 (1~12개월)
        const lastDate = new Date(monthlyData[monthlyData.length - 1].date);
        for (let i = 1; i <= 12; i++) {
            const futureDate = new Date(lastDate);
            futureDate.setMonth(futureDate.getMonth() + i);
            const monthLabel = `${futureDate.getFullYear()}-${String(futureDate.getMonth() + 1).padStart(2, '0')}`;
            forecastLabels.push(monthLabel);
            
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
    
    // 전체 라벨 (과거 월별 + 예측)
    const allLabels = [...monthlyLabels, ...forecastLabels.slice(1)];
    
    priceChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: allLabels,
            datasets: [
                {
                    label: '월평균 주가',
                    data: [...monthlyPrices, ...Array(forecastLabels.length - 1).fill(null)],
                    borderColor: '#0066cc',
                    backgroundColor: 'rgba(0, 102, 204, 0.1)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.2,
                    pointRadius: 4,
                    pointHoverRadius: 6,
                    pointBackgroundColor: '#0066cc'
                },
                {
                    label: 'AI 예측',
                    data: [...Array(monthlyPrices.length - 1).fill(null), ...forecastPrices],
                    borderColor: '#94a3b8',
                    borderWidth: 2,
                    borderDash: [5, 5],
                    fill: false,
                    tension: 0.3,
                    pointRadius: 4,
                    pointBackgroundColor: '#94a3b8'
                }
            ]
        },
        options: getChartOptions()
    });
}

// 일별 데이터를 월별 평균으로 변환
function aggregateToMonthly(priceHistory) {
    const monthlyMap = new Map();
    
    priceHistory.forEach(p => {
        const date = new Date(p.date);
        const monthKey = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`;
        
        if (!monthlyMap.has(monthKey)) {
            monthlyMap.set(monthKey, { prices: [], date: date });
        }
        monthlyMap.get(monthKey).prices.push(p.close);
    });
    
    const result = [];
    monthlyMap.forEach((value, key) => {
        const avgPrice = Math.round(value.prices.reduce((a, b) => a + b, 0) / value.prices.length);
        result.push({
            label: key,
            date: value.date,
            avgPrice: avgPrice
        });
    });
    
    // 날짜순 정렬
    result.sort((a, b) => new Date(a.date) - new Date(b.date));
    
    return result;
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
        resetProgressSteps();
        startLoadingMessages();
    } else {
        overlay.classList.add('hidden');
        stopLoadingMessages();
        // 섹션 순차 표시 애니메이션
        revealSections();
    }
}

// 프로세스 바 초기화
function resetProgressSteps() {
    const progressFill = document.getElementById('loadingProgressFill');
    if (progressFill) progressFill.style.width = '0%';
    
    ['step1', 'step2', 'step3', 'step4'].forEach(id => {
        const step = document.getElementById(id);
        if (step) {
            step.classList.remove('active', 'completed');
        }
    });
}

// 프로세스 단계 업데이트
function updateProgressStep(stepNum, isCompleted = false) {
    const progressFill = document.getElementById('loadingProgressFill');
    const stepEl = document.getElementById(`step${stepNum}`);
    
    // 프로그레스 바 업데이트
    const progressPercent = {
        1: 25,
        2: 50,
        3: 75,
        4: 100
    };
    
    if (progressFill && progressPercent[stepNum]) {
        progressFill.style.width = `${progressPercent[stepNum]}%`;
    }
    
    // 이전 단계들 완료 처리
    for (let i = 1; i < stepNum; i++) {
        const prevStep = document.getElementById(`step${i}`);
        if (prevStep) {
            prevStep.classList.remove('active');
            prevStep.classList.add('completed');
        }
    }
    
    // 현재 단계 처리
    if (stepEl) {
        if (isCompleted) {
            stepEl.classList.remove('active');
            stepEl.classList.add('completed');
        } else {
            stepEl.classList.add('active');
            stepEl.classList.remove('completed');
        }
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
    // 로딩 메시지 업데이트
    const loadingStepEl = document.getElementById('loadingStep');
    if (loadingStepEl) {
        loadingStepEl.textContent = step;
    }
    
    // 프로세스 단계 업데이트 (진행률 기준)
    if (progress <= 25) {
        updateProgressStep(1, progress >= 25);  // 데이터 수집
    } else if (progress <= 50) {
        updateProgressStep(2, progress >= 50);  // 지표 분석
    } else if (progress <= 75) {
        updateProgressStep(3, progress >= 75);  // AI 분석
    } else {
        updateProgressStep(4, progress >= 100); // 보고서 생성
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

