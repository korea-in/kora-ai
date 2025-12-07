"""
Firebase 인증 서비스
- Firebase Admin SDK 초기화
- 사용자 인증 및 관리
"""

import os
import firebase_admin
from firebase_admin import credentials, auth, firestore
from functools import wraps
from flask import session, redirect, url_for, request, jsonify
from typing import Optional, Tuple

from app.models.user import User

# Firebase 초기화 상태
_firebase_initialized = False
_db = None


def _get_firebase_credentials_from_env():
    """환경변수에서 Firebase 인증 정보 딕셔너리 생성"""
    private_key = os.environ.get('FIREBASE_PRIVATE_KEY', '')
    # .env에서 읽은 \n 문자열을 실제 줄바꿈으로 변환
    if private_key:
        private_key = private_key.replace('\\n', '\n')
    
    return {
        "type": os.environ.get('FIREBASE_TYPE', 'service_account'),
        "project_id": os.environ.get('FIREBASE_PROJECT_ID', ''),
        "private_key_id": os.environ.get('FIREBASE_PRIVATE_KEY_ID', ''),
        "private_key": private_key,
        "client_email": os.environ.get('FIREBASE_CLIENT_EMAIL', ''),
        "client_id": os.environ.get('FIREBASE_CLIENT_ID', ''),
        "auth_uri": os.environ.get('FIREBASE_AUTH_URI', 'https://accounts.google.com/o/oauth2/auth'),
        "token_uri": os.environ.get('FIREBASE_TOKEN_URI', 'https://oauth2.googleapis.com/token'),
        "auth_provider_x509_cert_url": os.environ.get('FIREBASE_AUTH_PROVIDER_CERT_URL', 'https://www.googleapis.com/oauth2/v1/certs'),
        "client_x509_cert_url": os.environ.get('FIREBASE_CLIENT_CERT_URL', ''),
        "universe_domain": os.environ.get('FIREBASE_UNIVERSE_DOMAIN', 'googleapis.com')
    }


def init_firebase(app):
    """Flask 앱과 함께 Firebase 초기화"""
    global _firebase_initialized, _db
    
    if _firebase_initialized:
        return
    
    try:
        # 환경변수에서 인증 정보 가져오기
        cred_dict = _get_firebase_credentials_from_env()
        
        # 필수 값 확인
        if not cred_dict.get('project_id') or not cred_dict.get('private_key'):
            app.logger.warning("Firebase credentials not found in environment variables")
            return
        
        cred = credentials.Certificate(cred_dict)
        firebase_admin.initialize_app(cred)
        _db = firestore.client()
        _firebase_initialized = True
        app.logger.info("Firebase initialized successfully")
    except Exception as e:
        app.logger.error(f"Firebase initialization failed: {e}")


def get_db():
    """Firestore 클라이언트 반환"""
    return _db


def is_firebase_initialized():
    """Firebase 초기화 상태 확인"""
    return _firebase_initialized


# ============================================
# 사용자 관리 함수
# ============================================

def create_user(email: str, password: str, display_name: Optional[str] = None) -> Tuple[Optional[User], Optional[str]]:
    """
    새 사용자 생성
    
    Args:
        email: 이메일
        password: 비밀번호 (bcrypt로 해시되어 저장됨)
        display_name: 표시 이름
        
    Returns:
        (User 객체, 에러 메시지) - 성공 시 에러 메시지는 None
    """
    if not _firebase_initialized:
        return None, "Firebase not initialized"
    
    try:
        # Firebase Auth에 사용자 생성
        firebase_user = auth.create_user(
            email=email,
            password=password,
            display_name=display_name
        )
        
        # User 모델 생성 (비밀번호 bcrypt 해시 포함)
        user = User.create_new(
            uid=firebase_user.uid,
            email=email,
            password=password,  # bcrypt로 해시됨
            display_name=display_name
        )
        
        # Firestore에 사용자 정보 저장 (해시된 비밀번호 포함)
        if _db:
            user_data = user.to_dict()
            user_data['created_at'] = firestore.SERVER_TIMESTAMP
            user_data['updated_at'] = firestore.SERVER_TIMESTAMP
            
            _db.collection('users').document(firebase_user.uid).set(user_data)
        
        return user, None
        
    except auth.EmailAlreadyExistsError:
        return None, "이미 등록된 이메일입니다"
    except auth.InvalidPasswordError:
        return None, "비밀번호는 6자 이상이어야 합니다"
    except Exception as e:
        return None, str(e)


def verify_user_password(email: str, password: str) -> Tuple[Optional[User], Optional[str]]:
    """
    비밀번호 검증
    
    Args:
        email: 이메일
        password: 비밀번호
        
    Returns:
        (User 객체, 에러 메시지) - 성공 시 에러 메시지는 None
    """
    print(f"[DEBUG] verify_user_password called - email: {email}")
    print(f"[DEBUG] Firebase initialized: {_firebase_initialized}, db: {_db is not None}")
    
    if not _firebase_initialized or not _db:
        return None, "Firebase not initialized"
    
    try:
        # Firebase Auth에서 사용자 조회
        firebase_user = auth.get_user_by_email(email)
        print(f"[DEBUG] Firebase Auth user found - uid: {firebase_user.uid}")
        
        # Firestore에서 사용자 정보 조회
        doc = _db.collection('users').document(firebase_user.uid).get()
        print(f"[DEBUG] Firestore doc exists: {doc.exists}")
        
        if not doc.exists:
            return None, "사용자 정보를 찾을 수 없습니다"
        
        user_data = doc.to_dict()
        print(f"[DEBUG] User data: {user_data}")
        print(f"[DEBUG] password_hash exists: {'password_hash' in user_data and user_data.get('password_hash') is not None}")
        
        user = User.from_dict(user_data)
        
        # 비밀번호 검증 (bcrypt)
        if not user.verify_password(password):
            print(f"[DEBUG] Password verification failed")
            return None, "비밀번호가 일치하지 않습니다"
        
        print(f"[DEBUG] Password verification success")
        return user, None
        
    except auth.UserNotFoundError:
        print(f"[DEBUG] User not found in Firebase Auth")
        return None, "등록되지 않은 이메일입니다"
    except Exception as e:
        print(f"[DEBUG] Exception: {str(e)}")
        return None, str(e)


def get_user_by_uid(uid: str) -> Optional[User]:
    """UID로 사용자 조회"""
    if not _firebase_initialized or not _db:
        return None
    
    try:
        doc = _db.collection('users').document(uid).get()
        
        if doc.exists:
            return User.from_dict(doc.to_dict())
        return None
        
    except Exception:
        return None


def get_user_by_email(email: str) -> Optional[User]:
    """이메일로 사용자 조회"""
    if not _firebase_initialized:
        return None
    
    try:
        firebase_user = auth.get_user_by_email(email)
        return get_user_by_uid(firebase_user.uid)
        
    except auth.UserNotFoundError:
        return None
    except Exception:
        return None


def get_firebase_user_by_email(email: str):
    """Firebase Auth에서 사용자 조회"""
    if not _firebase_initialized:
        return None
    
    try:
        return auth.get_user_by_email(email)
    except auth.UserNotFoundError:
        return None
    except Exception:
        return None


def verify_user_by_email_and_name(email: str, name: str) -> Tuple[Optional[User], Optional[str]]:
    """
    이메일과 이름으로 사용자 본인 확인
    
    Args:
        email: 이메일
        name: 가입 시 등록한 이름
        
    Returns:
        (User 객체, 에러 메시지) - 성공 시 에러 메시지는 None
    """
    print(f"[DEBUG] verify_user_by_email_and_name - email: {email}, name: {name}")
    
    if not _firebase_initialized or not _db:
        print("[DEBUG] Firebase not initialized")
        return None, "Firebase not initialized"
    
    try:
        # Firebase Auth에서 사용자 조회
        firebase_user = auth.get_user_by_email(email)
        print(f"[DEBUG] Firebase Auth user found - uid: {firebase_user.uid}")
        
        # Firestore에서 사용자 정보 조회
        doc = _db.collection('users').document(firebase_user.uid).get()
        print(f"[DEBUG] Firestore doc exists: {doc.exists}")
        
        if not doc.exists:
            return None, "사용자 정보를 찾을 수 없습니다"
        
        user = User.from_dict(doc.to_dict())
        print(f"[DEBUG] User display_name: {user.display_name}, input name: {name}")
        
        # 이름 검증
        if user.display_name != name:
            return None, "이름이 일치하지 않습니다"
        
        return user, None
        
    except auth.UserNotFoundError:
        print("[DEBUG] User not found in Firebase Auth")
        return None, "등록되지 않은 이메일입니다"
    except Exception as e:
        print(f"[DEBUG] Exception: {str(e)}")
        return None, str(e)


def reset_user_password(email: str, name: str, new_password: str) -> Tuple[bool, Optional[str]]:
    """
    비밀번호 재설정
    
    Args:
        email: 이메일
        name: 가입 시 등록한 이름 (본인 확인용)
        new_password: 새 비밀번호
        
    Returns:
        (성공 여부, 에러 메시지)
    """
    if not _firebase_initialized or not _db:
        return False, "Firebase not initialized"
    
    try:
        # 먼저 본인 확인
        user, error = verify_user_by_email_and_name(email, name)
        
        if error:
            return False, error
        
        # Firebase Auth 비밀번호 업데이트
        auth.update_user(user.uid, password=new_password)
        
        # Firestore에 해시된 비밀번호 저장
        from app.models.user import User as UserModel
        password_hash = UserModel.hash_password(new_password)
        
        _db.collection('users').document(user.uid).update({
            'password_hash': password_hash,
            'updated_at': firestore.SERVER_TIMESTAMP
        })
        
        return True, None
        
    except Exception as e:
        return False, str(e)


def update_user(uid: str, **kwargs) -> bool:
    """사용자 정보 업데이트"""
    if not _db:
        return False
    
    try:
        update_data = {k: v for k, v in kwargs.items() if v is not None}
        update_data['updated_at'] = firestore.SERVER_TIMESTAMP
        
        _db.collection('users').document(uid).update(update_data)
        return True
        
    except Exception:
        return False


def update_last_login(uid: str) -> bool:
    """마지막 로그인 시간 업데이트"""
    return update_user(uid, last_login_at=firestore.SERVER_TIMESTAMP)


def increment_analysis_count(uid: str) -> bool:
    """분석 횟수 증가"""
    if not _db:
        return False
    
    try:
        _db.collection('users').document(uid).update({
            'analysis_count': firestore.Increment(1),
            'daily_analysis_used': firestore.Increment(1),
            'updated_at': firestore.SERVER_TIMESTAMP
        })
        return True
        
    except Exception:
        return False


def add_favorite_company(uid: str, company_code: str) -> bool:
    """관심 기업 추가"""
    if not _db:
        return False
    
    try:
        _db.collection('users').document(uid).update({
            'favorite_companies': firestore.ArrayUnion([company_code]),
            'updated_at': firestore.SERVER_TIMESTAMP
        })
        return True
        
    except Exception:
        return False


def remove_favorite_company(uid: str, company_code: str) -> bool:
    """관심 기업 제거"""
    if not _db:
        return False
    
    try:
        _db.collection('users').document(uid).update({
            'favorite_companies': firestore.ArrayRemove([company_code]),
            'updated_at': firestore.SERVER_TIMESTAMP
        })
        return True
        
    except Exception:
        return False


# ============================================
# 인증 함수
# ============================================

def verify_id_token(id_token: str) -> Tuple[Optional[dict], Optional[str]]:
    """Firebase ID 토큰 검증"""
    if not _firebase_initialized:
        return None, "Firebase not initialized"
    
    try:
        decoded_token = auth.verify_id_token(id_token)
        return decoded_token, None
        
    except auth.InvalidIdTokenError:
        return None, "Invalid token"
    except auth.ExpiredIdTokenError:
        return None, "Token expired"
    except Exception as e:
        return None, str(e)


# ============================================
# 데코레이터
# ============================================

def login_required(f):
    """로그인 필수 데코레이터"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            if request.is_json:
                return jsonify({'error': 'Login required'}), 401
            return redirect(url_for('main.auth'))
        return f(*args, **kwargs)
    return decorated_function

