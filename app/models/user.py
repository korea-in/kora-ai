"""
User 모델
Firestore users 컬렉션 데이터 구조 정의
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional, List, Dict, Any
import bcrypt


def hash_password(password: str) -> str:
    """비밀번호를 bcrypt로 해시"""
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')


def verify_password(password: str, hashed: str) -> bool:
    """비밀번호 검증"""
    try:
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    except Exception:
        return False


@dataclass
class User:
    """
    사용자 정보 모델
    
    Firestore Collection: users
    Document ID: Firebase Auth UID
    """
    
    # 필수 필드
    uid: str                          # Firebase Auth UID
    email: str                        # 이메일
    
    # 보안 (비밀번호는 bcrypt 해시로 저장)
    password_hash: Optional[str] = None     # bcrypt 해시된 비밀번호
    
    # 프로필 정보
    display_name: Optional[str] = None      # 표시 이름
    photo_url: Optional[str] = None         # 프로필 이미지 URL
    phone_number: Optional[str] = None      # 전화번호
    
    # 앱 관련 정보
    analysis_count: int = 0                 # 분석 실행 횟수
    favorite_companies: List[str] = field(default_factory=list)  # 관심 기업 코드 목록
    preferred_market: str = "kospi"         # 선호 시장 (kospi/kosdaq)
    
    # 구독/등급 정보
    subscription_tier: str = "free"         # 구독 등급 (free/basic/premium)
    daily_analysis_limit: int = 5           # 일일 분석 제한 횟수
    daily_analysis_used: int = 0            # 오늘 사용한 분석 횟수
    
    # 크레딧 시스템
    credits: int = 500                      # 보유 크레딧 (회원가입시 500 지급)
    total_credits_used: int = 0             # 총 사용한 크레딧
    total_credits_purchased: int = 0        # 총 구매한 크레딧
    
    # 투자 성향 분석
    investment_type: Optional[str] = None           # 투자 성향 (안정형/안정추구형/위험중립형/적극투자형/공격투자형)
    investment_score: Optional[int] = None          # 투자 성향 점수 (0~100)
    investment_analysis_date: Optional[datetime] = None  # 투자 성향 분석 일자
    
    # 설정
    email_notifications: bool = True        # 이메일 알림 수신
    push_notifications: bool = True         # 푸시 알림 수신
    
    # 타임스탬프
    created_at: Optional[datetime] = None   # 가입일
    updated_at: Optional[datetime] = None   # 정보 수정일
    last_login_at: Optional[datetime] = None  # 마지막 로그인
    
    # 계정 상태
    is_active: bool = True                  # 활성 상태
    is_verified: bool = False               # 이메일 인증 여부
    
    def to_dict(self) -> Dict[str, Any]:
        """Firestore 저장용 딕셔너리 변환"""
        data = {
            'uid': self.uid,
            'email': self.email,
            'password_hash': self.password_hash,  # bcrypt 해시
            'display_name': self.display_name,
            'photo_url': self.photo_url,
            'phone_number': self.phone_number,
            'analysis_count': self.analysis_count,
            'favorite_companies': self.favorite_companies,
            'preferred_market': self.preferred_market,
            'subscription_tier': self.subscription_tier,
            'daily_analysis_limit': self.daily_analysis_limit,
            'daily_analysis_used': self.daily_analysis_used,
            'credits': self.credits,
            'total_credits_used': self.total_credits_used,
            'total_credits_purchased': self.total_credits_purchased,
            'investment_type': self.investment_type,
            'investment_score': self.investment_score,
            'email_notifications': self.email_notifications,
            'push_notifications': self.push_notifications,
            'is_active': self.is_active,
            'is_verified': self.is_verified,
        }
        
        # datetime 필드는 Firestore SERVER_TIMESTAMP 사용을 위해 별도 처리
        # created_at, updated_at, last_login_at, investment_analysis_date은 저장 시 처리
        
        return data
    
    def verify_password(self, password: str) -> bool:
        """비밀번호 검증"""
        if not self.password_hash:
            return False
        return verify_password(password, self.password_hash)
    
    def set_password(self, password: str) -> None:
        """비밀번호 설정 (해시 저장)"""
        self.password_hash = hash_password(password)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'User':
        """Firestore 문서에서 User 객체 생성"""
        return cls(
            uid=data.get('uid', ''),
            email=data.get('email', ''),
            password_hash=data.get('password_hash'),
            display_name=data.get('display_name'),
            photo_url=data.get('photo_url'),
            phone_number=data.get('phone_number'),
            analysis_count=data.get('analysis_count', 0),
            favorite_companies=data.get('favorite_companies', []),
            preferred_market=data.get('preferred_market', 'kospi'),
            subscription_tier=data.get('subscription_tier', 'free'),
            daily_analysis_limit=data.get('daily_analysis_limit', 5),
            daily_analysis_used=data.get('daily_analysis_used', 0),
            credits=data.get('credits', 500),
            total_credits_used=data.get('total_credits_used', 0),
            total_credits_purchased=data.get('total_credits_purchased', 0),
            investment_type=data.get('investment_type'),
            investment_score=data.get('investment_score'),
            investment_analysis_date=data.get('investment_analysis_date'),
            email_notifications=data.get('email_notifications', True),
            push_notifications=data.get('push_notifications', True),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at'),
            last_login_at=data.get('last_login_at'),
            is_active=data.get('is_active', True),
            is_verified=data.get('is_verified', False),
        )
    
    @classmethod
    def create_new(cls, uid: str, email: str, password: str = None, display_name: Optional[str] = None) -> 'User':
        """새 사용자 생성용 팩토리 메서드"""
        user = cls(
            uid=uid,
            email=email,
            display_name=display_name or email.split('@')[0],
        )
        if password:
            user.set_password(password)
        return user
    
    def can_analyze(self) -> bool:
        """분석 가능 여부 확인"""
        if not self.is_active:
            return False
        return self.daily_analysis_used < self.daily_analysis_limit
    
    def get_remaining_analyses(self) -> int:
        """남은 분석 횟수"""
        return max(0, self.daily_analysis_limit - self.daily_analysis_used)
    
    def has_credits(self, amount: int) -> bool:
        """크레딧 보유 여부 확인"""
        return self.credits >= amount
    
    def use_credits(self, amount: int) -> bool:
        """크레딧 사용 (성공 시 True 반환)"""
        if self.has_credits(amount):
            self.credits -= amount
            self.total_credits_used += amount
            return True
        return False
    
    def add_credits(self, amount: int, is_purchase: bool = False) -> None:
        """크레딧 추가"""
        self.credits += amount
        if is_purchase:
            self.total_credits_purchased += amount
    
    def get_investment_type_label(self) -> str:
        """투자 성향 한글 라벨 반환"""
        labels = {
            'conservative': '안정형',
            'moderately_conservative': '안정추구형',
            'moderate': '위험중립형',
            'moderately_aggressive': '적극투자형',
            'aggressive': '공격투자형'
        }
        return labels.get(self.investment_type, '미분석')
    
    def __repr__(self) -> str:
        return f"User(uid={self.uid}, email={self.email}, name={self.display_name})"

