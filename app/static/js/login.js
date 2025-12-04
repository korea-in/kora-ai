// login.js
// 로그인 페이지 JavaScript

$(document).ready(function() {
    KORA.log('로그인 페이지 초기화');
    
    // 요소 캐싱
    const $loginForm = $('#loginForm');
    const $emailInput = $('#email');
    const $passwordInput = $('#password');
    const $loginBtn = $('#loginBtn');
    const $togglePassword = $('#togglePassword');
    const $rememberMe = $('#rememberMe');
    
    // 저장된 이메일 불러오기
    const savedEmail = KORA.storage.get('remember_email', '');
    if (savedEmail) {
        $emailInput.val(savedEmail);
        $rememberMe.prop('checked', true);
    }
    
    // 비밀번호 보기 토글
    $togglePassword.on('click', function() {
        const $eyeOpen = $(this).find('.eye-open');
        const $eyeClosed = $(this).find('.eye-closed');
        
        if ($passwordInput.attr('type') === 'password') {
            $passwordInput.attr('type', 'text');
            $eyeOpen.addClass('hidden');
            $eyeClosed.removeClass('hidden');
        } else {
            $passwordInput.attr('type', 'password');
            $eyeOpen.removeClass('hidden');
            $eyeClosed.addClass('hidden');
        }
    });
    
    // 입력 필드 포커스 효과
    $('.kora-input').on('focus', function() {
        $(this).closest('.input-group').addClass('focused');
    }).on('blur', function() {
        $(this).closest('.input-group').removeClass('focused');
    });
    
    // 실시간 유효성 검사
    $emailInput.on('blur', function() {
        const email = $(this).val().trim();
        if (email && !KORA.util.isValidEmail(email)) {
            showInputError($emailInput, '올바른 이메일 형식이 아닙니다.');
        } else {
            clearInputError($emailInput);
        }
    });
    
    $passwordInput.on('blur', function() {
        const password = $(this).val();
        if (password && !KORA.util.isValidPassword(password)) {
            showInputError($passwordInput, '비밀번호는 8자 이상이어야 합니다.');
        } else {
            clearInputError($passwordInput);
        }
    });
    
    // 입력 시 에러 클리어
    $('.kora-input').on('input', function() {
        clearInputError($(this));
    });
    
    // 로그인 폼 제출
    $loginForm.on('submit', function(e) {
        e.preventDefault();
        
        const email = $emailInput.val().trim();
        const password = $passwordInput.val();
        
        // 유효성 검사
        let isValid = true;
        
        if (!email) {
            showInputError($emailInput, '이메일을 입력해주세요.');
            isValid = false;
        } else if (!KORA.util.isValidEmail(email)) {
            showInputError($emailInput, '올바른 이메일 형식이 아닙니다.');
            isValid = false;
        }
        
        if (!password) {
            showInputError($passwordInput, '비밀번호를 입력해주세요.');
            isValid = false;
        } else if (!KORA.util.isValidPassword(password)) {
            showInputError($passwordInput, '비밀번호는 8자 이상이어야 합니다.');
            isValid = false;
        }
        
        if (!isValid) {
            // 폼 흔들기 효과
            $('.login-card').addClass('shake');
            setTimeout(function() {
                $('.login-card').removeClass('shake');
            }, 500);
            return;
        }
        
        // 로그인 유지 체크 시 이메일 저장
        if ($rememberMe.is(':checked')) {
            KORA.storage.set('remember_email', email);
        } else {
            KORA.storage.remove('remember_email');
        }
        
        // 로그인 요청
        performLogin(email, password);
    });
    
    // 로그인 실행
    function performLogin(email, password) {
        // 버튼 로딩 상태
        $loginBtn.addClass('loading').prop('disabled', true);
        
        KORA.log('로그인 시도:', email);
        
        // TODO: 실제 로그인 API 연동
        // 현재는 시뮬레이션
        setTimeout(function() {
            // 로딩 해제
            $loginBtn.removeClass('loading').prop('disabled', false);
            
            // 성공 시뮬레이션 (나중에 실제 API로 교체)
            KORA.toast('로그인 기능은 곧 추가될 예정입니다.', 'warning');
            
            // 실제 로그인 성공 시
            // KORA.toast('로그인 성공!', 'success');
            // window.location.href = '/dashboard';
            
        }, 1500);
        
        /* 실제 API 연동 코드 (Firebase 연동 후 활성화)
        KORA.api.post('/auth/login', {
            email: email,
            password: password
        }).done(function(response) {
            if (response.success) {
                KORA.toast('로그인 성공!', 'success');
                KORA.storage.set('user', response.user);
                window.location.href = '/dashboard';
            } else {
                showLoginError(response.message || '로그인에 실패했습니다.');
            }
        }).fail(function(xhr) {
            const message = xhr.responseJSON?.message || '서버 오류가 발생했습니다.';
            showLoginError(message);
        }).always(function() {
            $loginBtn.removeClass('loading').prop('disabled', false);
        });
        */
    }
    
    // 입력 필드 에러 표시
    function showInputError($input, message) {
        $input.addClass('error');
        
        // 기존 에러 메시지 제거
        $input.closest('.input-group').find('.error-message').remove();
        
        // 에러 메시지 추가
        const $errorMsg = $('<p>')
            .addClass('error-message show')
            .text(message);
        
        $input.closest('.relative').after($errorMsg);
    }
    
    // 입력 필드 에러 제거
    function clearInputError($input) {
        $input.removeClass('error');
        $input.closest('.input-group').find('.error-message').remove();
    }
    
    // 로그인 에러 표시
    function showLoginError(message) {
        KORA.toast(message, 'error');
        $('.login-card').addClass('shake');
        setTimeout(function() {
            $('.login-card').removeClass('shake');
        }, 500);
    }
    
    // Enter 키로 다음 필드 이동
    $emailInput.on('keypress', function(e) {
        if (e.which === 13) {
            e.preventDefault();
            $passwordInput.focus();
        }
    });
    
    // 구글 로그인 버튼
    $('.kora-btn-social').on('click', function() {
        KORA.toast('Google 로그인은 곧 추가될 예정입니다.', 'warning');
        
        // TODO: Firebase Google Auth 연동
    });
    
    // 비밀번호 찾기 링크
    $('a[href="#"]').on('click', function(e) {
        e.preventDefault();
        const linkText = $(this).text().trim();
        
        if (linkText === '비밀번호 찾기') {
            KORA.toast('비밀번호 찾기 기능은 곧 추가될 예정입니다.', 'warning');
        } else if (linkText === '회원가입') {
            KORA.toast('회원가입 기능은 곧 추가될 예정입니다.', 'warning');
        }
    });
});

