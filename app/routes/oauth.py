"""
OAuth 소셜 로그인 라우트
카카오, 네이버: 직접 OAuth 연동
구글: Firebase Auth 사용
"""
import os
import requests
from flask import Blueprint, redirect, request, session, url_for, jsonify

oauth_bp = Blueprint('oauth', __name__)

# ============================================
# 카카오 OAuth
# ============================================

KAKAO_REST_API_KEY = os.getenv('KAKAO_REST_API_KEY')
KAKAO_REDIRECT_URI = os.getenv('KAKAO_REDIRECT_URI', 'http://127.0.0.1/auth/kakao/callback')

@oauth_bp.route('/auth/kakao')
def kakao_login():
    """카카오 로그인 시작"""
    # 환경변수를 매번 다시 읽기 (모듈 로드 시점 문제 해결)
    kakao_key = os.getenv('KAKAO_REST_API_KEY')
    kakao_redirect = os.getenv('KAKAO_REDIRECT_URI', 'http://127.0.0.1/auth/kakao/callback')
    
    print(f"[Kakao OAuth] REST API Key: {kakao_key[:10] if kakao_key else 'None'}...")
    print(f"[Kakao OAuth] Redirect URI: {kakao_redirect}")
    
    if not kakao_key:
        return jsonify({"error": "카카오 API 키가 설정되지 않았습니다."}), 500
    
    kakao_auth_url = (
        f"https://kauth.kakao.com/oauth/authorize"
        f"?client_id={kakao_key}"
        f"&redirect_uri={kakao_redirect}"
        f"&response_type=code"
    )
    return redirect(kakao_auth_url)


@oauth_bp.route('/auth/kakao/callback')
def kakao_callback():
    """카카오 로그인 콜백"""
    code = request.args.get('code')
    error = request.args.get('error')
    
    if error:
        return redirect(url_for('main.auth', error='카카오 로그인이 취소되었습니다.'))
    
    if not code:
        return redirect(url_for('main.auth', error='인증 코드를 받지 못했습니다.'))
    
    try:
        # 환경변수를 매번 다시 읽기
        kakao_key = os.getenv('KAKAO_REST_API_KEY')
        kakao_secret = os.getenv('KAKAO_CLIENT_SECRET')  # Client Secret (선택)
        kakao_redirect = os.getenv('KAKAO_REDIRECT_URI', 'http://127.0.0.1/auth/kakao/callback')
        
        # 1. Access Token 발급
        token_url = "https://kauth.kakao.com/oauth/token"
        token_data = {
            'grant_type': 'authorization_code',
            'client_id': kakao_key,
            'redirect_uri': kakao_redirect,
            'code': code
        }
        
        # Client Secret이 설정되어 있으면 추가
        if kakao_secret:
            token_data['client_secret'] = kakao_secret
            print(f"[Kakao OAuth] Using Client Secret")
        
        print(f"[Kakao OAuth] Token request - client_id: {kakao_key[:10] if kakao_key else 'None'}...")
        print(f"[Kakao OAuth] Token request - redirect_uri: {kakao_redirect}")
        
        token_response = requests.post(token_url, data=token_data)
        token_json = token_response.json()
        
        if 'access_token' not in token_json:
            print(f"[Kakao OAuth] Token error: {token_json}")
            return redirect(url_for('main.auth', error='카카오 인증에 실패했습니다.'))
        
        access_token = token_json['access_token']
        
        # 2. 사용자 정보 조회
        user_url = "https://kapi.kakao.com/v2/user/me"
        headers = {'Authorization': f'Bearer {access_token}'}
        user_response = requests.get(user_url, headers=headers)
        user_json = user_response.json()
        
        print(f"[Kakao OAuth] User info: {user_json}")
        
        # 3. 사용자 정보 추출
        kakao_id = str(user_json.get('id'))
        kakao_account = user_json.get('kakao_account', {})
        profile = kakao_account.get('profile', {})
        
        email = kakao_account.get('email') or f"kakao_{kakao_id}@kakao.com"
        name = profile.get('nickname') or '카카오 사용자'
        
        # 4. DB에 사용자 저장/조회 후 세션 설정
        user_id = save_or_get_social_user(email, name, 'kakao', kakao_id)
        
        if user_id:
            session['user_id'] = user_id
            session['user_name'] = name
            session['user_email'] = email
            session['login_type'] = 'kakao'
            
            # 크레딧 조회
            from app.services.firebase import get_user_credits
            credits = get_user_credits(user_id)
            session['user_credits'] = credits
            
            return redirect(url_for('main.main_page'))
        else:
            return redirect(url_for('main.auth', error='사용자 등록에 실패했습니다.'))
        
    except Exception as e:
        print(f"[Kakao OAuth] Error: {e}")
        import traceback
        traceback.print_exc()
        return redirect(url_for('main.auth', error='카카오 로그인 처리 중 오류가 발생했습니다.'))


# ============================================
# 네이버 OAuth
# ============================================

NAVER_CLIENT_ID = os.getenv('NAVER_CLIENT_ID')
NAVER_CLIENT_SECRET = os.getenv('NAVER_CLIENT_SECRET')
NAVER_REDIRECT_URI = os.getenv('NAVER_REDIRECT_URI', 'http://127.0.0.1/auth/naver/callback')

@oauth_bp.route('/auth/naver')
def naver_login():
    """네이버 로그인 시작"""
    if not NAVER_CLIENT_ID:
        return jsonify({"error": "네이버 API 키가 설정되지 않았습니다."}), 500
    
    import secrets
    state = secrets.token_urlsafe(16)
    session['naver_state'] = state
    
    naver_auth_url = (
        f"https://nid.naver.com/oauth2.0/authorize"
        f"?response_type=code"
        f"&client_id={NAVER_CLIENT_ID}"
        f"&redirect_uri={NAVER_REDIRECT_URI}"
        f"&state={state}"
    )
    return redirect(naver_auth_url)


@oauth_bp.route('/auth/naver/callback')
def naver_callback():
    """네이버 로그인 콜백"""
    code = request.args.get('code')
    state = request.args.get('state')
    error = request.args.get('error')
    
    if error:
        return redirect(url_for('main.auth', error='네이버 로그인이 취소되었습니다.'))
    
    if not code:
        return redirect(url_for('main.auth', error='인증 코드를 받지 못했습니다.'))
    
    # State 검증
    saved_state = session.pop('naver_state', None)
    if state != saved_state:
        return redirect(url_for('main.auth', error='잘못된 요청입니다.'))
    
    try:
        # 1. Access Token 발급
        token_url = "https://nid.naver.com/oauth2.0/token"
        token_data = {
            'grant_type': 'authorization_code',
            'client_id': NAVER_CLIENT_ID,
            'client_secret': NAVER_CLIENT_SECRET,
            'code': code,
            'state': state
        }
        token_response = requests.post(token_url, data=token_data)
        token_json = token_response.json()
        
        if 'access_token' not in token_json:
            print(f"[Naver OAuth] Token error: {token_json}")
            return redirect(url_for('main.auth', error='네이버 인증에 실패했습니다.'))
        
        access_token = token_json['access_token']
        
        # 2. 사용자 정보 조회
        user_url = "https://openapi.naver.com/v1/nid/me"
        headers = {'Authorization': f'Bearer {access_token}'}
        user_response = requests.get(user_url, headers=headers)
        user_json = user_response.json()
        
        print(f"[Naver OAuth] User info: {user_json}")
        
        if user_json.get('resultcode') != '00':
            return redirect(url_for('main.auth', error='네이버 사용자 정보 조회에 실패했습니다.'))
        
        # 3. 사용자 정보 추출
        response = user_json.get('response', {})
        naver_id = response.get('id')
        email = response.get('email') or f"naver_{naver_id}@naver.com"
        name = response.get('name') or response.get('nickname') or '네이버 사용자'
        
        # 4. DB에 사용자 저장/조회 후 세션 설정
        user_id = save_or_get_social_user(email, name, 'naver', naver_id)
        
        if user_id:
            session['user_id'] = user_id
            session['user_name'] = name
            session['user_email'] = email
            session['login_type'] = 'naver'
            
            # 크레딧 조회
            from app.services.firebase import get_user_credits
            credits = get_user_credits(user_id)
            session['user_credits'] = credits
            
            return redirect(url_for('main.main_page'))
        else:
            return redirect(url_for('main.auth', error='사용자 등록에 실패했습니다.'))
        
    except Exception as e:
        print(f"[Naver OAuth] Error: {e}")
        import traceback
        traceback.print_exc()
        return redirect(url_for('main.auth', error='네이버 로그인 처리 중 오류가 발생했습니다.'))


# ============================================
# 구글 로그인 (Firebase 사용)
# ============================================

@oauth_bp.route('/auth/google')
def google_login():
    """구글 로그인 - Firebase를 통해 처리되므로 클라이언트에서 직접 처리"""
    # Firebase Auth는 클라이언트 사이드에서 처리
    # 이 라우트는 사용되지 않음
    return redirect(url_for('main.auth'))


@oauth_bp.route('/auth/google/callback', methods=['POST'])
def google_callback():
    """구글 로그인 콜백 - Firebase ID 토큰 검증"""
    try:
        data = request.get_json()
        id_token = data.get('id_token')
        
        if not id_token:
            return jsonify({"success": False, "error": "ID 토큰이 없습니다."}), 400
        
        # Firebase Admin SDK로 토큰 검증
        from firebase_admin import auth
        decoded_token = auth.verify_id_token(id_token)
        
        uid = decoded_token['uid']
        email = decoded_token.get('email', '')
        name = decoded_token.get('name', '구글 사용자')
        
        # DB에 사용자 저장/조회
        user_id = save_or_get_social_user(email, name, 'google', uid)
        
        if user_id:
            session['user_id'] = user_id
            session['user_name'] = name
            session['user_email'] = email
            session['login_type'] = 'google'
            
            # 크레딧 조회
            from app.services.firebase import get_user_credits
            credits = get_user_credits(user_id)
            session['user_credits'] = credits
            
            return jsonify({"success": True, "redirect": "/main"})
        else:
            return jsonify({"success": False, "error": "사용자 등록에 실패했습니다."}), 500
        
    except Exception as e:
        print(f"[Google OAuth] Error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500


# ============================================
# 소셜 사용자 저장/조회 함수
# ============================================

def save_or_get_social_user(email: str, name: str, provider: str, provider_id: str) -> str:
    """
    소셜 로그인 사용자를 DB에 저장하거나 기존 사용자 조회
    
    Returns:
        user_id (str) 또는 None
    """
    try:
        from app.services.firebase import get_db
        db = get_db()
        
        if not db:
            print("[save_or_get_social_user] DB 연결 실패")
            return None
        
        # 이메일로 기존 사용자 조회
        users_ref = db.collection('users')
        existing = users_ref.where('email', '==', email).limit(1).stream()
        
        for doc in existing:
            user_data = doc.to_dict()
            print(f"[save_or_get_social_user] 기존 사용자 발견: {doc.id}")
            
            # 소셜 로그인 정보 업데이트 (필요시)
            if user_data.get('login_type') != provider:
                doc.reference.update({
                    'login_type': provider,
                    'provider_id': provider_id
                })
            
            return doc.id
        
        # 새 사용자 생성
        from google.cloud.firestore import SERVER_TIMESTAMP
        
        user_id = f"{provider}_{provider_id}"
        new_user = {
            'email': email,
            'name': name,
            'login_type': provider,
            'provider_id': provider_id,
            'credits': 500,  # 신규 가입 크레딧
            'created_at': SERVER_TIMESTAMP
        }
        
        users_ref.document(user_id).set(new_user)
        print(f"[save_or_get_social_user] 새 사용자 생성: {user_id}")
        
        return user_id
        
    except Exception as e:
        print(f"[save_or_get_social_user] Error: {e}")
        import traceback
        traceback.print_exc()
        return None
