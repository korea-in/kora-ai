/* ============================================
   KORA AI - Auth Page JavaScript
   auth.html specific scripts
   ============================================ */

document.addEventListener('DOMContentLoaded', function() {
    initAuthPage();
    checkAutoLogin();
});

// 상태 변수
let isVerified = false;

function initAuthPage() {
    const loginForm = document.getElementById('login-form');
    const signupForm = document.getElementById('signup-form');
    const resetForm = document.getElementById('reset-form');
    
    // 화면 전환 링크들
    const gotoSignup = document.getElementById('goto-signup');
    const gotoReset = document.getElementById('goto-reset');
    const gotoLoginFromSignup = document.getElementById('goto-login-from-signup');
    const gotoLoginFromReset = document.getElementById('goto-login-from-reset');

    // 회원가입으로 이동
    if (gotoSignup) {
        gotoSignup.addEventListener('click', function(e) {
            e.preventDefault();
            switchTab('signup');
        });
    }

    // 비밀번호 찾기로 이동
    if (gotoReset) {
        gotoReset.addEventListener('click', function(e) {
            e.preventDefault();
            switchTab('reset');
        });
    }

    // 로그인으로 돌아가기 (회원가입에서)
    if (gotoLoginFromSignup) {
        gotoLoginFromSignup.addEventListener('click', function(e) {
            e.preventDefault();
            switchTab('login');
        });
    }

    // 로그인으로 돌아가기 (비밀번호 찾기에서)
    if (gotoLoginFromReset) {
        gotoLoginFromReset.addEventListener('click', function(e) {
            e.preventDefault();
            switchTab('login');
            resetPasswordForm();
        });
    }

    // 로그인 폼 제출
    if (loginForm) {
        loginForm.addEventListener('submit', handleLogin);
    }

    // 회원가입 폼 제출
    if (signupForm) {
        signupForm.addEventListener('submit', handleSignup);
    }

    // 비밀번호 재설정 폼 제출
    if (resetForm) {
        resetForm.addEventListener('submit', handlePasswordReset);
    }
}

function switchTab(targetTab) {
    const forms = document.querySelectorAll('.auth-form');

    // 폼 전환
    forms.forEach(form => {
        form.classList.remove('active');
        if (form.id === `${targetTab}-form`) {
            form.classList.add('active');
        }
    });

    // 메시지 숨기기
    hideMessage();
}

// ============================================
// 자동 로그인 체크
// ============================================

function checkAutoLogin() {
    const savedEmail = localStorage.getItem('kora_remember_email');
    const savedToken = localStorage.getItem('kora_auth_token');
    
    if (savedEmail) {
        const loginEmail = document.getElementById('login-email');
        const rememberCheckbox = document.querySelector('input[name="remember"]');
        
        if (loginEmail) loginEmail.value = savedEmail;
        if (rememberCheckbox) rememberCheckbox.checked = true;
    }
    
    // 토큰이 있으면 자동 로그인 시도
    if (savedToken) {
        autoLogin(savedToken);
    }
}

async function autoLogin(token) {
    try {
        const response = await fetch('/check', {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        const result = await response.json();
        
        if (result.authenticated) {
            // 이미 로그인된 상태면 메인으로 이동
            window.location.href = '/main';
        }
    } catch (error) {
        // 토큰 만료 등의 이유로 실패하면 토큰 삭제
        localStorage.removeItem('kora_auth_token');
    }
}

// ============================================
// 로그인 처리
// ============================================

async function handleLogin(e) {
    e.preventDefault();
    
    const email = document.getElementById('login-email').value.trim();
    const password = document.getElementById('login-password').value;
    const remember = document.querySelector('input[name="remember"]').checked;
    const submitBtn = this.querySelector('.auth-btn');
    
    if (!email || !password) {
        showMessage('이메일과 비밀번호를 입력해주세요.', 'error');
        return;
    }
    
    // 버튼 로딩 상태
    setButtonLoading(submitBtn, true);
    
    try {
        const response = await fetch('/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ email, password })
        });
        
        const result = await response.json();
        
        if (result.success) {
            // 자동 로그인 저장
            if (remember) {
                localStorage.setItem('kora_remember_email', email);
                if (result.token) {
                    localStorage.setItem('kora_auth_token', result.token);
                }
            } else {
                localStorage.removeItem('kora_remember_email');
                localStorage.removeItem('kora_auth_token');
            }
            
            showMessage('로그인 성공! 잠시 후 이동합니다...', 'success');
            
            setTimeout(() => {
                window.location.href = '/main';
            }, 500);
        } else {
            showMessage(result.error || '아이디 또는 비밀번호를 확인해주세요.', 'error');
        }
    } catch (error) {
        console.error('Login error:', error);
        showMessage('로그인 중 오류가 발생했습니다. 다시 시도해주세요.', 'error');
    } finally {
        setButtonLoading(submitBtn, false);
    }
}

// ============================================
// 회원가입 처리
// ============================================

async function handleSignup(e) {
    e.preventDefault();
    
    const name = document.getElementById('signup-name').value.trim();
    const email = document.getElementById('signup-email').value.trim();
    const password = document.getElementById('signup-password').value;
    const passwordConfirm = document.getElementById('signup-password-confirm').value;
    const submitBtn = this.querySelector('.auth-btn');
    
    // 유효성 검사
    if (!name || !email || !password) {
        showMessage('모든 필드를 입력해주세요.', 'error');
        return;
    }
    
    if (password.length < 6) {
        showMessage('비밀번호는 6자 이상이어야 합니다.', 'error');
        return;
    }
    
    if (password !== passwordConfirm) {
        showMessage('비밀번호가 일치하지 않습니다.', 'error');
        return;
    }
    
    // 버튼 로딩 상태
    setButtonLoading(submitBtn, true);
    
    try {
        const response = await fetch('/signup', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ name, email, password })
        });
        
        const result = await response.json();
        
        if (result.success) {
            showMessage('회원가입 성공! 잠시 후 메인 페이지로 이동합니다...', 'success');
            
            setTimeout(() => {
                window.location.href = '/main';
            }, 1000);
        } else {
            showMessage(result.error || '회원가입에 실패했습니다. 다시 시도해주세요.', 'error');
        }
    } catch (error) {
        console.error('Signup error:', error);
        showMessage('회원가입 중 오류가 발생했습니다. 다시 시도해주세요.', 'error');
    } finally {
        setButtonLoading(submitBtn, false);
    }
}

// ============================================
// 비밀번호 재설정 처리
// ============================================

async function handlePasswordReset(e) {
    e.preventDefault();
    
    const email = document.getElementById('reset-email').value.trim();
    const name = document.getElementById('reset-name').value.trim();
    const submitBtn = document.getElementById('reset-btn');
    
    if (!email || !name) {
        showMessage('이메일과 이름을 입력해주세요.', 'error');
        return;
    }
    
    // 1단계: 본인 확인
    if (!isVerified) {
        setButtonLoading(submitBtn, true);
        
        try {
            const response = await fetch('/verify-user', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ email, name })
            });
            
            const result = await response.json();
            
            if (result.success) {
                isVerified = true;
                showNewPasswordFields();
                showMessage('본인 확인 완료! 새 비밀번호를 입력해주세요.', 'success');
            } else {
                showMessage(result.error || '입력하신 정보와 일치하는 계정을 찾을 수 없습니다.', 'error');
            }
        } catch (error) {
            console.error('Verify error:', error);
            showMessage('확인 중 오류가 발생했습니다. 다시 시도해주세요.', 'error');
        } finally {
            setButtonLoading(submitBtn, false);
        }
        return;
    }
    
    // 2단계: 비밀번호 변경
    const newPassword = document.getElementById('reset-new-password').value;
    const newPasswordConfirm = document.getElementById('reset-new-password-confirm').value;
    
    if (!newPassword || newPassword.length < 6) {
        showMessage('새 비밀번호는 6자 이상이어야 합니다.', 'error');
        return;
    }
    
    if (newPassword !== newPasswordConfirm) {
        showMessage('새 비밀번호가 일치하지 않습니다.', 'error');
        return;
    }
    
    setButtonLoading(submitBtn, true);
    
    try {
        const response = await fetch('/reset-password', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ email, name, new_password: newPassword })
        });
        
        const result = await response.json();
        
        if (result.success) {
            showMessage('비밀번호가 성공적으로 변경되었습니다! 로그인 해주세요.', 'success');
            
            setTimeout(() => {
                switchTab('login');
                resetPasswordForm();
                // 이메일 자동 입력
                document.getElementById('login-email').value = email;
            }, 1500);
        } else {
            showMessage(result.error || '비밀번호 변경에 실패했습니다.', 'error');
        }
    } catch (error) {
        console.error('Reset password error:', error);
        showMessage('비밀번호 변경 중 오류가 발생했습니다.', 'error');
    } finally {
        setButtonLoading(submitBtn, false);
    }
}

function showNewPasswordFields() {
    const section = document.getElementById('new-password-section');
    const btnText = document.getElementById('reset-btn-text');
    const emailInput = document.getElementById('reset-email');
    const nameInput = document.getElementById('reset-name');
    
    if (section) {
        section.style.display = 'block';
        // 새 비밀번호 필드에 required 추가
        document.getElementById('reset-new-password').required = true;
        document.getElementById('reset-new-password-confirm').required = true;
    }
    if (btnText) btnText.textContent = '비밀번호 변경';
    if (emailInput) emailInput.disabled = true;
    if (nameInput) nameInput.disabled = true;
}

function resetPasswordForm() {
    isVerified = false;
    
    const section = document.getElementById('new-password-section');
    const btnText = document.getElementById('reset-btn-text');
    const emailInput = document.getElementById('reset-email');
    const nameInput = document.getElementById('reset-name');
    const form = document.getElementById('reset-form');
    
    if (section) section.style.display = 'none';
    if (btnText) btnText.textContent = '본인 확인';
    if (emailInput) {
        emailInput.disabled = false;
        emailInput.value = '';
    }
    if (nameInput) {
        nameInput.disabled = false;
        nameInput.value = '';
    }
    if (form) form.reset();
    
    // required 제거
    const newPw = document.getElementById('reset-new-password');
    const newPwConfirm = document.getElementById('reset-new-password-confirm');
    if (newPw) newPw.required = false;
    if (newPwConfirm) newPwConfirm.required = false;
}

// ============================================
// 유틸리티 함수
// ============================================

function showMessage(message, type = 'info') {
    const messageDiv = document.getElementById('auth-message');
    if (!messageDiv) return;
    
    messageDiv.textContent = message;
    messageDiv.className = `auth-message ${type}`;
    messageDiv.style.display = 'block';
    
    // 에러가 아니면 5초 후 자동 숨김
    if (type !== 'error') {
        setTimeout(() => {
            hideMessage();
        }, 5000);
    }
}

function hideMessage() {
    const messageDiv = document.getElementById('auth-message');
    if (messageDiv) {
        messageDiv.style.display = 'none';
    }
}

function setButtonLoading(btn, loading) {
    if (!btn) return;
    
    if (loading) {
        btn.disabled = true;
        btn.classList.add('loading');
        const span = btn.querySelector('span');
        if (span) span.dataset.original = span.textContent;
        if (span) span.textContent = '처리 중...';
    } else {
        btn.disabled = false;
        btn.classList.remove('loading');
        const span = btn.querySelector('span');
        if (span && span.dataset.original) {
            span.textContent = span.dataset.original;
        }
    }
}
