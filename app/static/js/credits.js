/**
 * KORA AI - 크레딧 충전 페이지 JavaScript
 */

let selectedCredits = 0;
let selectedPrice = 0;

// 패키지 선택
function selectPackage(credits, price) {
    selectedCredits = credits;
    selectedPrice = price;
    
    // 모달 표시
    document.getElementById('modalCredits').textContent = credits.toLocaleString() + ' 크레딧';
    document.getElementById('modalPrice').textContent = '₩' + price.toLocaleString();
    document.getElementById('paymentModal').classList.remove('hidden');
}

// 결제 모달 닫기
function closePaymentModal() {
    document.getElementById('paymentModal').classList.add('hidden');
}

// 결제 처리
async function processPayment() {
    const paymentMethod = document.querySelector('input[name="payment"]:checked').value;
    
    // 결제 처리 중 표시
    const btn = document.querySelector('.modal-footer .btn-primary');
    const originalText = btn.innerHTML;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 처리 중...';
    btn.disabled = true;
    
    try {
        // 실제 결제 API 호출
        const response = await fetch('/api/credits/purchase', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                credits: selectedCredits,
                price: selectedPrice,
                method: paymentMethod
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            // 크레딧 업데이트
            document.getElementById('currentCredits').textContent = result.credits_total.toLocaleString();
            
            // 총 충전 업데이트
            const totalPurchased = parseInt(document.getElementById('totalPurchased').textContent.replace(/,/g, '')) || 0;
            document.getElementById('totalPurchased').textContent = (totalPurchased + selectedCredits).toLocaleString();
            
            // 이력 추가
            addHistoryItem('charge', `${selectedCredits.toLocaleString()} 크레딧 패키지 구매`, `+${selectedCredits.toLocaleString()}`);
            
            closePaymentModal();
            alert('크레딧이 충전되었습니다!');
        } else {
            alert('충전 실패: ' + (result.error || '알 수 없는 오류'));
        }
        
    } catch (error) {
        console.error('Payment error:', error);
        alert('결제 처리 중 오류가 발생했습니다.');
    } finally {
        btn.innerHTML = originalText;
        btn.disabled = false;
    }
}

// 이력 추가
function addHistoryItem(type, desc, amount) {
    const historyList = document.getElementById('creditHistory');
    const now = new Date();
    const dateStr = now.toLocaleString('ko-KR', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
    });
    
    const amountClass = amount.startsWith('+') ? 'plus' : 'minus';
    
    const newItem = document.createElement('div');
    newItem.className = 'history-item';
    newItem.innerHTML = `
        <div class="history-info">
            <span class="history-type ${type}">${type === 'charge' ? '충전' : type === 'use' ? '사용' : '보너스'}</span>
            <span class="history-desc">${desc}</span>
        </div>
        <div class="history-meta">
            <span class="history-amount ${amountClass}">${amount}</span>
            <span class="history-date">${dateStr}</span>
        </div>
    `;
    
    historyList.insertBefore(newItem, historyList.firstChild);
}

// ESC 키로 모달 닫기
document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
        closePaymentModal();
    }
});

// 모달 외부 클릭으로 닫기
document.getElementById('paymentModal').addEventListener('click', function(e) {
    if (e.target === this) {
        closePaymentModal();
    }
});


