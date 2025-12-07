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


def get_report_based_popular(limit: int = 20) -> List[dict]:
    """
    보고서 기반 인기 기업 목록 조회
    
    Returns:
        기업별 분석 횟수 기준 인기 기업 리스트
    """
    db = get_db()
    if not db:
        return []
    
    try:
        # 모든 보고서에서 기업별 분석 횟수 집계
        reports = db.collection('reports').stream()
        
        company_counts = {}
        for doc in reports:
            data = doc.to_dict()
            company = data.get('company_name')
            ticker = data.get('ticker')
            market = data.get('market', 'KOSPI')
            
            if company and ticker:
                key = f"{company}|{ticker}|{market}"
                company_counts[key] = company_counts.get(key, 0) + 1
        
        # 분석 횟수로 정렬
        sorted_companies = sorted(company_counts.items(), key=lambda x: x[1], reverse=True)[:limit]
        
        result = []
        for key, count in sorted_companies:
            parts = key.split('|')
            result.append({
                'company_name': parts[0],
                'ticker': parts[1],
                'market': parts[2] if len(parts) > 2 else 'KOSPI',
                'analysis_count': count
            })
        
        return result
        
    except Exception as e:
        print(f"Error getting report-based popular: {e}")
        return []


# ============================================
# 보고서 저장/조회 함수
# ============================================

def save_report(user_id: str, report_data: dict) -> Optional[str]:
    """
    보고서 저장 - 전체 데이터 포함
    
    Args:
        user_id: 사용자 UID
        report_data: 보고서 데이터 (JSON 직렬화 가능)
        
    Returns:
        생성된 문서 ID 또는 None
    """
    db = get_db()
    if not db:
        print("[save_report] DB connection failed")
        return None
    
    try:
        print(f"[save_report] Saving report for user: {user_id}")
        
        # analysis에서 필요한 정보 추출
        analysis = report_data.get('analysis') or {}
        raw_data = report_data.get('raw_data') or {}
        
        # 기본 메타 데이터
        data = {
            'user_id': user_id,
            'company_name': report_data.get('company_name', ''),
            'ticker': report_data.get('ticker', ''),
            'market': report_data.get('market', ''),
            'investment_score': analysis.get('investment_score', 0),
            'investment_opinion': analysis.get('investment_opinion', ''),
            'investment_grade': analysis.get('investment_grade', ''),
            'fair_price': analysis.get('fair_price', 0),
            'evaluation_summary': analysis.get('evaluation_summary', ''),
            'is_public': True,
            'view_count': 0,
            'created_at': firestore.SERVER_TIMESTAMP
        }
        
        # 전체 AI 분석 결과 저장
        data['ai_analysis'] = analysis
        
        # KRX 데이터 저장 (밸류에이션, 주가, 기술적 지표 등)
        krx_data = raw_data.get('krx', {})
        data['krx_data'] = {
            'current_price': krx_data.get('current_price', {}),
            'summary': krx_data.get('summary', {}),
            'valuation': krx_data.get('valuation', {}),
            'yearly_trend': krx_data.get('yearly_trend', {}),
            'moving_averages': krx_data.get('moving_averages', {}),
            'rsi': krx_data.get('rsi', {}),
            'mfi': krx_data.get('mfi', {}),
            'price_history': krx_data.get('price_history', [])[-100:]  # 최근 100일만
        }
        
        # DART 데이터 저장 (재무지표, 배당, 공시 등)
        dart_data = raw_data.get('dart', {})
        data['dart_data'] = {
            'company_info': dart_data.get('company_info', {}),
            'financial_index': dart_data.get('financial_index', {}),
            'financials': dart_data.get('financials', {}),
            'dividend': dart_data.get('dividend', []),
            'disclosures': dart_data.get('disclosures', [])[:10],  # 최근 10개
            'stock_info': dart_data.get('stock_info', {}),
            'calculated_ratios': dart_data.get('calculated_ratios', {})
        }
        
        # 뉴스 데이터 저장
        news_data = raw_data.get('news', {})
        data['news_data'] = {
            'total': news_data.get('total', 0),
            'items': news_data.get('items', [])[:5]  # 표시용 5개
        }
        
        print(f"[save_report] Data prepared: company={data['company_name']}, score={data['investment_score']}")
        
        doc_ref = db.collection('reports').add(data)
        report_id = doc_ref[1].id
        print(f"[save_report] Report saved with ID: {report_id}")
        return report_id
        
    except Exception as e:
        print(f"[save_report] Error: {e}")
        import traceback
        traceback.print_exc()
        return None


def get_user_reports(user_id: str, limit: int = 50) -> List[dict]:
    """
    사용자의 보고서 목록 조회
    
    Args:
        user_id: 사용자 UID
        limit: 조회 개수
        
    Returns:
        보고서 목록
    """
    db = get_db()
    if not db:
        print("[get_user_reports] DB connection failed")
        return []
    
    try:
        print(f"[get_user_reports] Querying reports for user_id: {user_id}")
        
        # 인덱스 없이 조회 (order_by 제거)
        docs = db.collection('reports') \
            .where('user_id', '==', user_id) \
            .limit(limit) \
            .stream()
        
        reports = []
        for doc in docs:
            data = doc.to_dict()
            data['id'] = doc.id
            # report_json은 제외하고 메타 정보만 반환
            if 'report_json' in data:
                del data['report_json']
            # created_at을 문자열로 변환
            if data.get('created_at'):
                data['created_at_str'] = data['created_at'].strftime('%Y-%m-%d %H:%M') if hasattr(data['created_at'], 'strftime') else str(data['created_at'])
            reports.append(data)
        
        # Python에서 정렬 (최신순)
        reports.sort(key=lambda x: x.get('created_at') or '', reverse=True)
        
        print(f"[get_user_reports] Found {len(reports)} reports")
        return reports
        
    except Exception as e:
        print(f"Error getting user reports: {e}")
        return []


def get_public_reports(limit: int = 50, market: str = None, search: str = None, exclude_user_id: str = None) -> List[dict]:
    """
    공개 보고서 목록 조회
    
    Args:
        limit: 조회 개수
        market: 시장 필터 (KOSPI/KOSDAQ)
        search: 기업명 검색어
        exclude_user_id: 제외할 사용자 ID (내 보고서 제외)
        
    Returns:
        보고서 목록
    """
    db = get_db()
    if not db:
        return []
    
    try:
        # 인덱스 없이 조회 (order_by 제거)
        # 단일 where 조건만 사용
        docs = db.collection('reports') \
            .where('is_public', '==', True) \
            .limit(limit * 2) \
            .stream()
        
        reports = []
        for doc in docs:
            data = doc.to_dict()
            data['id'] = doc.id
            # report_json은 제외
            if 'report_json' in data:
                del data['report_json']
            
            # 본인 보고서 제외
            if exclude_user_id and data.get('user_id') == exclude_user_id:
                continue
            
            # 시장 필터링 (클라이언트 사이드)
            if market and market != 'all':
                if data.get('market') != market:
                    continue
            
            # 검색어 필터링 (클라이언트 사이드)
            if search:
                if search.lower() not in data.get('company_name', '').lower():
                    continue
            
            # created_at을 문자열로 변환
            if data.get('created_at'):
                data['created_at_str'] = data['created_at'].strftime('%Y-%m-%d %H:%M') if hasattr(data['created_at'], 'strftime') else str(data['created_at'])
            
            reports.append(data)
        
        # Python에서 정렬 (최신순)
        reports.sort(key=lambda x: x.get('created_at') or '', reverse=True)
        
        return reports[:limit]
        
    except Exception as e:
        print(f"Error getting public reports: {e}")
        return []


def get_report_by_id(report_id: str, user_id: str = None) -> Optional[dict]:
    """
    보고서 상세 조회
    
    Args:
        report_id: 보고서 문서 ID
        user_id: 요청한 사용자 ID (소유자 확인용)
        
    Returns:
        보고서 데이터 또는 None
    """
    db = get_db()
    if not db:
        return None
    
    try:
        doc = db.collection('reports').document(report_id).get()
        
        if not doc.exists:
            return None
        
        data = doc.to_dict()
        data['id'] = doc.id
        
        # 소유자 여부 표시
        data['is_owner'] = (user_id == data.get('user_id'))
        
        # created_at을 문자열로 변환
        if data.get('created_at'):
            try:
                data['created_at_str'] = data['created_at'].strftime('%Y-%m-%d %H:%M')
            except:
                data['created_at_str'] = str(data['created_at'])
        
        # 조회수 증가 (본인 보고서가 아닌 경우)
        if not data['is_owner']:
            db.collection('reports').document(report_id).update({
                'view_count': firestore.Increment(1)
            })
        
        return data
        
    except Exception as e:
        print(f"Error getting report: {e}")
        return None


def use_user_credits(user_id: str, amount: int, reason: str = '') -> bool:
    """
    사용자 크레딧 차감
    
    Args:
        user_id: 사용자 UID
        amount: 차감할 크레딧 양
        reason: 차감 사유
        
    Returns:
        성공 여부
    """
    db = get_db()
    if not db:
        return False
    
    try:
        user_ref = db.collection('users').document(user_id)
        user_doc = user_ref.get()
        
        if not user_doc.exists:
            return False
        
        user_data = user_doc.to_dict()
        current_credits = user_data.get('credits', 0)
        
        if current_credits < amount:
            return False
        
        user_ref.update({
            'credits': current_credits - amount,
            'total_credits_used': firestore.Increment(amount),
            'updated_at': firestore.SERVER_TIMESTAMP
        })
        
        # 크레딧 사용 기록 저장
        db.collection('credit_history').add({
            'user_id': user_id,
            'amount': -amount,
            'reason': reason,
            'created_at': firestore.SERVER_TIMESTAMP
        })
        
        return True
        
    except Exception as e:
        print(f"Error using credits: {e}")
        return False


def get_user_credits(user_id: str) -> int:
    """
    사용자 크레딧 조회
    
    Args:
        user_id: 사용자 UID
        
    Returns:
        보유 크레딧
    """
    db = get_db()
    if not db:
        return 0
    
    try:
        doc = db.collection('users').document(user_id).get()
        
        if doc.exists:
            return doc.to_dict().get('credits', 0)
        return 0
        
    except Exception:
        return 0

