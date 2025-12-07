/**
 * KORA AI - 개인정보 페이지 JavaScript
 */

document.addEventListener('DOMContentLoaded', function() {
    initProfileForm();
    initPasswordForm();
});

// 프로필 폼 초기화
function initProfileForm() {
    const form = document.getElementById('profileForm');
    
    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const formData = new FormData(form);
        const data = {
            display_name: formData.get('display_name'),
            phone_number: formData.get('phone_number'),
            preferred_market: formData.get('preferred_market'),
            email_notifications: formData.get('email_notifications') === 'on'
        };
        
        const btn = form.querySelector('.btn-primary');
        const originalText = btn.innerHTML;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 저장 중...';
        btn.disabled = true;
        
        try {
            // TODO: API 연동
            // const response = await fetch('/api/profile/update', {
            //     method: 'POST',
            //     headers: { 'Content-Type': 'application/json' },
            //     body: JSON.stringify(data)
            // });
            
            await new Promise(resolve => setTimeout(resolve, 1000));
            
            // 화면 업데이트
            document.getElementById('displayName').textContent = data.display_name;
            
            alert('정보가 저장되었습니다.');
            
        } catch (error) {
            console.error('Profile update error:', error);
            alert('저장 중 오류가 발생했습니다.');
        } finally {
            btn.innerHTML = originalText;
            btn.disabled = false;
        }
    });
}

// 비밀번호 변경 폼 초기화
function initPasswordForm() {
    const form = document.getElementById('passwordForm');
    
    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const currentPassword = document.getElementById('currentPassword').value;
        const newPassword = document.getElementById('newPassword').value;
        const confirmPassword = document.getElementById('confirmPassword').value;
        
        if (!currentPassword || !newPassword || !confirmPassword) {
            alert('모든 필드를 입력해주세요.');
            return;
        }
        
        if (newPassword !== confirmPassword) {
            alert('새 비밀번호가 일치하지 않습니다.');
            return;
        }
        
        if (newPassword.length < 6) {
            alert('비밀번호는 최소 6자 이상이어야 합니다.');
            return;
        }
        
        const btn = form.querySelector('.btn-secondary');
        const originalText = btn.innerHTML;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 변경 중...';
        btn.disabled = true;
        
        try {
            // TODO: API 연동
            // const response = await fetch('/api/profile/change-password', {
            //     method: 'POST',
            //     headers: { 'Content-Type': 'application/json' },
            //     body: JSON.stringify({
            //         current_password: currentPassword,
            //         new_password: newPassword
            //     })
            // });
            
            await new Promise(resolve => setTimeout(resolve, 1000));
            
            alert('비밀번호가 변경되었습니다.');
            form.reset();
            
        } catch (error) {
            console.error('Password change error:', error);
            alert('비밀번호 변경 중 오류가 발생했습니다.');
        } finally {
            btn.innerHTML = originalText;
            btn.disabled = false;
        }
    });
}

// 탈퇴 확인 모달
function confirmWithdrawal() {
    document.getElementById('withdrawalModal').classList.remove('hidden');
}

function closeWithdrawalModal() {
    document.getElementById('withdrawalModal').classList.add('hidden');
    document.getElementById('withdrawalConfirm').value = '';
}

// 탈퇴 처리
async function processWithdrawal() {
    const confirmText = document.getElementById('withdrawalConfirm').value;
    
    if (confirmText !== '탈퇴합니다') {
        alert('"탈퇴합니다"를 정확히 입력해주세요.');
        return;
    }
    
    try {
        // TODO: API 연동
        // const response = await fetch('/api/profile/withdraw', {
        //     method: 'POST'
        // });
        
        await new Promise(resolve => setTimeout(resolve, 1000));
        
        alert('회원 탈퇴가 완료되었습니다. 이용해 주셔서 감사합니다.');
        window.location.href = '/';
        
    } catch (error) {
        console.error('Withdrawal error:', error);
        alert('탈퇴 처리 중 오류가 발생했습니다.');
    }
}

// ESC 키로 모달 닫기
document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
        closeWithdrawalModal();
    }
});




