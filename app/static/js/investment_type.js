/**
 * KORA AI - 투자성향분석 페이지 JavaScript
 */

// 질문 데이터
const QUESTIONS = [
    {
        id: 1,
        text: "투자에 대한 전반적인 지식 수준은 어느 정도입니까?",
        options: [
            { text: "투자에 대해 거의 모름", score: 1 },
            { text: "기본적인 개념만 알고 있음", score: 2 },
            { text: "주식, 펀드 등 기본 상품은 이해함", score: 3 },
            { text: "다양한 금융상품에 대해 잘 알고 있음", score: 4 },
            { text: "전문 투자자 수준의 지식 보유", score: 5 }
        ]
    },
    {
        id: 2,
        text: "현재 투자 경험은 얼마나 됩니까?",
        options: [
            { text: "투자 경험 없음", score: 1 },
            { text: "1년 미만", score: 2 },
            { text: "1~3년", score: 3 },
            { text: "3~5년", score: 4 },
            { text: "5년 이상", score: 5 }
        ]
    },
    {
        id: 3,
        text: "투자 자금의 투자 예정 기간은 얼마입니까?",
        options: [
            { text: "6개월 미만", score: 1 },
            { text: "6개월 ~ 1년", score: 2 },
            { text: "1년 ~ 3년", score: 3 },
            { text: "3년 ~ 5년", score: 4 },
            { text: "5년 이상", score: 5 }
        ]
    },
    {
        id: 4,
        text: "예상 수익률은 어느 정도입니까?",
        options: [
            { text: "원금 보전이 최우선 (연 1~3%)", score: 1 },
            { text: "은행 금리 수준 (연 3~5%)", score: 2 },
            { text: "시장 평균 수익률 (연 5~10%)", score: 3 },
            { text: "시장 대비 초과 수익 (연 10~20%)", score: 4 },
            { text: "고수익 추구 (연 20% 이상)", score: 5 }
        ]
    },
    {
        id: 5,
        text: "투자 원금의 손실이 발생했을 때 어떻게 하시겠습니까?",
        options: [
            { text: "어떤 손실도 감수할 수 없음", score: 1 },
            { text: "10% 이내 손실까지 감수 가능", score: 2 },
            { text: "20% 이내 손실까지 감수 가능", score: 3 },
            { text: "30% 이내 손실까지 감수 가능", score: 4 },
            { text: "50% 이상 손실도 감수 가능", score: 5 }
        ]
    },
    {
        id: 6,
        text: "투자 자금이 전체 자산에서 차지하는 비중은?",
        options: [
            { text: "10% 미만 (여유 자금)", score: 5 },
            { text: "10~20%", score: 4 },
            { text: "20~30%", score: 3 },
            { text: "30~50%", score: 2 },
            { text: "50% 이상", score: 1 }
        ]
    },
    {
        id: 7,
        text: "투자 수익금의 주 사용 목적은 무엇입니까?",
        options: [
            { text: "생활비 보전", score: 1 },
            { text: "노후 자금 마련", score: 2 },
            { text: "주택 마련", score: 3 },
            { text: "자녀 교육비", score: 3 },
            { text: "여유 자금 증식", score: 5 }
        ]
    },
    {
        id: 8,
        text: "투자에 따른 원금 손실 시 감당 가능한 손실 금액은?",
        options: [
            { text: "손실 불가", score: 1 },
            { text: "투자 금액의 10% 이내", score: 2 },
            { text: "투자 금액의 20% 이내", score: 3 },
            { text: "투자 금액의 50% 이내", score: 4 },
            { text: "투자 금액 전액", score: 5 }
        ]
    },
    {
        id: 9,
        text: "주식 시장이 급락(20% 이상)했을 때 어떻게 하시겠습니까?",
        options: [
            { text: "즉시 전량 매도", score: 1 },
            { text: "일부 매도하여 손실 최소화", score: 2 },
            { text: "추이를 지켜보며 대기", score: 3 },
            { text: "오히려 추가 매수 기회로 활용", score: 4 },
            { text: "적극적으로 추가 매수", score: 5 }
        ]
    },
    {
        id: 10,
        text: "다음 중 가장 선호하는 투자 방식은?",
        options: [
            { text: "원금 보장형 상품만 투자", score: 1 },
            { text: "원금 손실 가능성이 낮은 안전한 상품 위주", score: 2 },
            { text: "안전자산과 위험자산에 적절히 분산", score: 3 },
            { text: "고수익 가능성이 있는 상품 위주", score: 4 },
            { text: "높은 위험을 감수하고 고수익 추구", score: 5 }
        ]
    }
];

// 투자 성향 유형 정의
const INVESTMENT_TYPES = {
    conservative: {
        name: '안정형',
        range: [10, 18],
        icon: 'fa-shield-alt',
        description: '투자에 대한 이해도가 낮고, 원금 보전을 최우선으로 하는 유형입니다. 예금, 적금 등 원금 보장형 상품이 적합합니다.',
        recommendations: [
            '정기예금, 적금 등 원금 보장 상품 위주로 투자',
            '투자 금액은 여유 자금 내에서 소액으로 시작',
            '고위험 상품은 피하고 안전자산 위주로 포트폴리오 구성',
            '투자 전 충분한 학습과 정보 수집 권장'
        ]
    },
    moderately_conservative: {
        name: '안정추구형',
        range: [19, 26],
        icon: 'fa-balance-scale',
        description: '안정적인 수익을 추구하면서도 약간의 위험은 감수할 수 있는 유형입니다. 채권형 펀드나 배당주 투자가 적합합니다.',
        recommendations: [
            '채권형 펀드, 배당주 등 안정적인 상품 위주 투자',
            '주식 비중은 전체의 20~30% 이내로 유지',
            '장기 투자 관점으로 접근하여 복리 효과 극대화',
            '분산 투자를 통한 리스크 관리 필요'
        ]
    },
    moderate: {
        name: '위험중립형',
        range: [27, 34],
        icon: 'fa-chart-pie',
        description: '수익과 위험의 균형을 추구하는 유형입니다. 주식과 채권에 균형있게 투자하는 혼합형 상품이 적합합니다.',
        recommendations: [
            '주식형 펀드와 채권형 펀드에 균형있게 분산 투자',
            '주식 비중은 전체의 40~60% 수준으로 조절',
            '성장주와 가치주를 적절히 혼합하여 포트폴리오 구성',
            '정기적인 리밸런싱으로 목표 비중 유지'
        ]
    },
    moderately_aggressive: {
        name: '적극투자형',
        range: [35, 42],
        icon: 'fa-chart-line',
        description: '높은 수익을 위해 상당한 위험을 감수할 수 있는 유형입니다. 성장주, 섹터 ETF 투자가 적합합니다.',
        recommendations: [
            '성장주, 테마 ETF 등 성장 가능성이 높은 상품 투자',
            '주식 비중을 전체의 70~80% 수준으로 확대 가능',
            '산업 트렌드 분석을 통한 유망 섹터 발굴',
            '손절 라인을 설정하여 리스크 관리'
        ]
    },
    aggressive: {
        name: '공격투자형',
        range: [43, 50],
        icon: 'fa-rocket',
        description: '최대 수익을 위해 높은 위험도 기꺼이 감수하는 유형입니다. 레버리지 상품, 파생상품 투자도 고려할 수 있습니다.',
        recommendations: [
            '고성장 주식, 소형주, 해외 신흥시장 등 적극 투자',
            '레버리지 ETF, 옵션 등 파생상품 활용 가능',
            '철저한 리서치와 시장 분석이 필수',
            '손실 감당 가능 범위 내에서 투자 규모 결정'
        ]
    }
};

// 상태 관리
let currentQuestionIndex = 0;
let answers = [];
let savedInvestmentType = null;

// 페이지 로드 시 기존 투자 성향 확인
document.addEventListener('DOMContentLoaded', async function() {
    await checkExistingInvestmentType();
});

// 기존 투자 성향 확인
async function checkExistingInvestmentType() {
    try {
        const response = await fetch('/api/profile/investment-type');
        const result = await response.json();
        
        if (result.success && result.investment_type) {
            savedInvestmentType = result;
            showSavedResult(result);
        }
    } catch (error) {
        console.error('Error checking investment type:', error);
    }
}

// 저장된 결과 표시
function showSavedResult(data) {
    const introSection = document.getElementById('introSection');
    const resultSection = document.getElementById('resultSection');
    
    // 소개 섹션 숨기고 결과 섹션 표시
    introSection.classList.add('hidden');
    resultSection.classList.remove('hidden');
    
    // 투자 유형 정보 가져오기
    const investmentType = INVESTMENT_TYPES[data.investment_type] || INVESTMENT_TYPES.moderate;
    
    // 결과 표시
    const badge = document.getElementById('resultBadge');
    badge.className = `result-badge ${data.investment_type}`;
    badge.innerHTML = `<i class="fas ${investmentType.icon}"></i>`;
    
    document.getElementById('resultType').innerHTML = `
        <h3>${investmentType.name}</h3>
        <p>투자성향 분석 점수: ${data.investment_score}점</p>
        <p class="analysis-date">분석일: ${data.analysis_date || '정보 없음'}</p>
    `;
    
    // 점수 바 애니메이션
    setTimeout(() => {
        const scorePercent = ((data.investment_score - 10) / 40) * 100;
        document.getElementById('scoreFill').style.width = `${Math.min(100, Math.max(0, scorePercent))}%`;
    }, 100);
    
    document.getElementById('resultDescription').innerHTML = `
        <p>${investmentType.description}</p>
    `;
    
    const recommendationsList = document.querySelector('#resultRecommendations ul');
    recommendationsList.innerHTML = investmentType.recommendations.map(rec => `
        <li>${rec}</li>
    `).join('');
    
    // 다시 분석 버튼 텍스트 변경
    const retryBtn = document.querySelector('.btn-retry');
    if (retryBtn) {
        retryBtn.innerHTML = '<i class="fas fa-redo"></i> 다시 진단하기';
    }
}

// 분석 시작
function startAnalysis() {
    document.getElementById('introSection').classList.add('hidden');
    document.getElementById('resultSection').classList.add('hidden');
    document.getElementById('quizSection').classList.remove('hidden');
    document.getElementById('totalQuestions').textContent = QUESTIONS.length;
    
    currentQuestionIndex = 0;
    answers = new Array(QUESTIONS.length).fill(null);
    
    showQuestion(0);
}

// 질문 표시
function showQuestion(index) {
    const question = QUESTIONS[index];
    const content = document.getElementById('quizContent');
    
    content.innerHTML = `
        <div class="question-text">${question.text}</div>
        <div class="answer-options">
            ${question.options.map((opt, i) => `
                <div class="answer-option ${answers[index] === i ? 'selected' : ''}" onclick="selectAnswer(${i})">
                    <input type="radio" name="answer" id="opt${i}" value="${opt.score}">
                    <label for="opt${i}">${opt.text}</label>
                </div>
            `).join('')}
        </div>
    `;
    
    document.getElementById('currentQuestion').textContent = index + 1;
    document.getElementById('progressFill').style.width = `${((index + 1) / QUESTIONS.length) * 100}%`;
    
    document.getElementById('prevBtn').disabled = index === 0;
    document.getElementById('nextBtn').textContent = index === QUESTIONS.length - 1 ? '결과 보기' : '다음';
    if (index === QUESTIONS.length - 1) {
        document.getElementById('nextBtn').innerHTML = '결과 보기 <i class="fas fa-check"></i>';
    } else {
        document.getElementById('nextBtn').innerHTML = '다음 <i class="fas fa-arrow-right"></i>';
    }
}

// 답변 선택
function selectAnswer(optionIndex) {
    answers[currentQuestionIndex] = optionIndex;
    
    document.querySelectorAll('.answer-option').forEach((opt, i) => {
        opt.classList.toggle('selected', i === optionIndex);
    });
}

// 이전 질문
function prevQuestion() {
    if (currentQuestionIndex > 0) {
        currentQuestionIndex--;
        showQuestion(currentQuestionIndex);
    }
}

// 다음 질문
function nextQuestion() {
    if (answers[currentQuestionIndex] === null) {
        alert('답변을 선택해주세요.');
        return;
    }
    
    if (currentQuestionIndex < QUESTIONS.length - 1) {
        currentQuestionIndex++;
        showQuestion(currentQuestionIndex);
    } else {
        showResult();
    }
}

// 결과 표시
function showResult() {
    // 총점 계산
    let totalScore = 0;
    answers.forEach((answerIndex, qIndex) => {
        if (answerIndex !== null) {
            totalScore += QUESTIONS[qIndex].options[answerIndex].score;
        }
    });
    
    // 투자 유형 결정
    let investmentType = null;
    for (const [key, type] of Object.entries(INVESTMENT_TYPES)) {
        if (totalScore >= type.range[0] && totalScore <= type.range[1]) {
            investmentType = { key, ...type };
            break;
        }
    }
    
    // 기본값 설정
    if (!investmentType) {
        investmentType = { key: 'moderate', ...INVESTMENT_TYPES.moderate };
    }
    
    // 화면 전환
    document.getElementById('quizSection').classList.add('hidden');
    document.getElementById('resultSection').classList.remove('hidden');
    
    // 결과 표시
    const badge = document.getElementById('resultBadge');
    badge.className = `result-badge ${investmentType.key}`;
    badge.innerHTML = `<i class="fas ${investmentType.icon}"></i>`;
    
    document.getElementById('resultType').innerHTML = `
        <h3>${investmentType.name}</h3>
        <p>투자성향 분석 점수: ${totalScore}점</p>
    `;
    
    // 점수 바 애니메이션
    setTimeout(() => {
        const scorePercent = ((totalScore - 10) / 40) * 100;
        document.getElementById('scoreFill').style.width = `${scorePercent}%`;
    }, 100);
    
    document.getElementById('resultDescription').innerHTML = `
        <p>${investmentType.description}</p>
    `;
    
    const recommendationsList = document.querySelector('#resultRecommendations ul');
    recommendationsList.innerHTML = investmentType.recommendations.map(rec => `
        <li>${rec}</li>
    `).join('');
    
    // TODO: 서버에 결과 저장
    saveResult(investmentType.key, totalScore);
}

// 결과 저장
async function saveResult(type, score) {
    try {
        const response = await fetch('/api/profile/investment-type', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                investment_type: type, 
                investment_score: score 
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            console.log('Investment type saved:', type, score);
        } else {
            console.error('Error saving result:', result.error);
        }
    } catch (error) {
        console.error('Error saving result:', error);
    }
}

// 다시 진단
function retryAnalysis() {
    document.getElementById('resultSection').classList.add('hidden');
    startAnalysis();
}


