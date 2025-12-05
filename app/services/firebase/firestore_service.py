"""
Firestore 데이터베이스 서비스
- 분석 기록 관리
- 인기 기업 관리
"""

from typing import List, Optional
from firebase_admin import firestore

from app.models.analysis import AnalysisHistory
from app.models.company import PopularCompany
from app.services.firebase.auth_service import get_db, increment_analysis_count


# ============================================
# 분석 기록 함수
# ============================================

def save_analysis_history(history: AnalysisHistory) -> Optional[str]:
    """
    분석 기록 저장
    
    Args:
        history: AnalysisHistory 객체
        
    Returns:
        생성된 문서 ID 또는 None
    """
    db = get_db()
    if not db:
        return None
    
    try:
        data = history.to_dict()
        data['created_at'] = firestore.SERVER_TIMESTAMP
        
        doc_ref = db.collection('analysis_history').add(data)
        
        # 사용자의 분석 횟수 증가
        increment_analysis_count(history.user_id)
        
        return doc_ref[1].id
        
    except Exception:
        return None


def get_user_analysis_history(user_id: str, limit: int = 20) -> List[AnalysisHistory]:
    """
    사용자의 분석 기록 조회
    
    Args:
        user_id: 사용자 UID
        limit: 조회 개수
        
    Returns:
        AnalysisHistory 객체 리스트
    """
    db = get_db()
    if not db:
        return []
    
    try:
        docs = db.collection('analysis_history') \
            .where('user_id', '==', user_id) \
            .order_by('created_at', direction=firestore.Query.DESCENDING) \
            .limit(limit) \
            .stream()
        
        return [AnalysisHistory.from_dict(doc.to_dict(), doc.id) for doc in docs]
        
    except Exception:
        return []


# ============================================
# 인기 기업 함수
# ============================================

def increment_company_view(market: str, company_code: str, company_name: str) -> bool:
    """
    기업 조회수 증가
    
    Args:
        market: 시장 (kospi/kosdaq)
        company_code: 기업 코드
        company_name: 기업명
        
    Returns:
        성공 여부
    """
    db = get_db()
    if not db:
        return False
    
    try:
        doc_id = PopularCompany.generate_doc_id(market, company_code)
        doc_ref = db.collection('popular').document(doc_id)
        doc = doc_ref.get()
        
        if doc.exists:
            doc_ref.update({
                'view_count': firestore.Increment(1),
                'last_viewed': firestore.SERVER_TIMESTAMP
            })
        else:
            company = PopularCompany.create_new(market, company_code, company_name)
            data = company.to_dict()
            data['created_at'] = firestore.SERVER_TIMESTAMP
            data['last_viewed'] = firestore.SERVER_TIMESTAMP
            doc_ref.set(data)
        
        return True
        
    except Exception:
        return False


def get_popular_companies(market: str, limit: int = 10) -> List[PopularCompany]:
    """
    인기 기업 목록 조회
    
    Args:
        market: 시장 (kospi/kosdaq)
        limit: 조회 개수
        
    Returns:
        PopularCompany 객체 리스트
    """
    db = get_db()
    if not db:
        return []
    
    try:
        docs = db.collection('popular') \
            .where('market', '==', market) \
            .order_by('view_count', direction=firestore.Query.DESCENDING) \
            .limit(limit) \
            .stream()
        
        return [PopularCompany.from_dict(doc.to_dict(), doc.id) for doc in docs]
        
    except Exception:
        return []

