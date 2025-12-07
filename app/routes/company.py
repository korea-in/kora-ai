from flask import Blueprint, jsonify, request
import csv
import os

company_bp = Blueprint('company', __name__)

def load_companies(market):
    """Load companies from CSV file"""
    companies = []
    base_path = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'corp_list')
    
    if market == 'kospi':
        file_path = os.path.join(base_path, 'kospi.csv')
    else:
        file_path = os.path.join(base_path, 'kosdaq.csv')
    
    try:
        # Try different encodings
        for encoding in ['cp949', 'euc-kr', 'utf-8']:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        # CSV 컬럼명: 단축코드, 한글 종목약명
                        code = row.get('단축코드', row.get('종목코드', ''))
                        name = row.get('한글 종목명', row.get('한글 정식명칭', ''))
                        short_name = row.get('한글 종목약명', '')
                        
                        if code:  # 코드가 있는 경우만 추가
                            companies.append({
                                'code': code,
                                'name': name or short_name,
                                'short_name': short_name,
                                'market': market.upper()
                            })
                break
            except (UnicodeDecodeError, KeyError):
                continue
    except FileNotFoundError:
        pass
    
    return companies

# Cache for companies
_company_cache = {
    'kospi': None,
    'kosdaq': None
}

def get_companies(market):
    """Get companies with caching"""
    if _company_cache[market] is None:
        _company_cache[market] = load_companies(market)
    return _company_cache[market]

@company_bp.route('/companies/search')
def search_companies():
    """Search companies by name"""
    query = request.args.get('q', '').strip().lower()
    market = request.args.get('market', 'kospi').lower()
    
    if not query:
        return jsonify([])
    
    companies = get_companies(market)
    
    # Filter companies matching the query
    results = []
    for company in companies:
        name = company.get('name', '').lower()
        short_name = company.get('short_name', '').lower()
        if query in name or query in short_name:
            results.append(company)
            if len(results) >= 10:
                break
    
    return jsonify(results)

@company_bp.route('/companies/popular')
def popular_companies():
    """Get popular companies based on report analysis count"""
    try:
        from app.services.firebase import get_popular_companies, get_report_based_popular
        
        # 보고서 기반 인기 기업 조회 (우선)
        report_popular = get_report_based_popular()
        
        kospi_from_reports = [c for c in report_popular if c.get('market', 'KOSPI').upper() == 'KOSPI'][:10]
        kosdaq_from_reports = [c for c in report_popular if c.get('market', 'KOSDAQ').upper() == 'KOSDAQ'][:10]
        
        # 보고서 기반 데이터가 충분하면 사용
        if len(kospi_from_reports) >= 3:
            kospi_result = [
                {
                    'code': c['ticker'],
                    'name': c['company_name'],
                    'short_name': c['company_name'],
                    'market': 'KOSPI',
                    'view_count': c.get('analysis_count', 0)
                }
                for c in kospi_from_reports
            ]
        else:
            # 기존 조회수 기반 데이터 사용
            kospi_popular = get_popular_companies('KOSPI', limit=10)
            if kospi_popular:
                kospi_result = [
                    {
                        'code': c.company_code,
                        'name': c.company_name,
                        'short_name': c.company_name,
                        'market': 'KOSPI',
                        'view_count': c.view_count
                    }
                    for c in kospi_popular
                ]
            else:
                kospi_result = get_companies('kospi')[:10]
                for c in kospi_result:
                    c['view_count'] = 0
        
        if len(kosdaq_from_reports) >= 3:
            kosdaq_result = [
                {
                    'code': c['ticker'],
                    'name': c['company_name'],
                    'short_name': c['company_name'],
                    'market': 'KOSDAQ',
                    'view_count': c.get('analysis_count', 0)
                }
                for c in kosdaq_from_reports
            ]
        else:
            kosdaq_popular = get_popular_companies('KOSDAQ', limit=10)
            if kosdaq_popular:
                kosdaq_result = [
                    {
                        'code': c.company_code,
                        'name': c.company_name,
                        'short_name': c.company_name,
                        'market': 'KOSDAQ',
                        'view_count': c.view_count
                    }
                    for c in kosdaq_popular
                ]
            else:
                kosdaq_result = get_companies('kosdaq')[:10]
                for c in kosdaq_result:
                    c['view_count'] = 0
        
        return jsonify({
            'kospi': kospi_result,
            'kosdaq': kosdaq_result
        })
        
    except Exception as e:
        print(f"Error getting popular companies: {e}")
        # 오류 시 기본 목록 반환
        kospi_companies = get_companies('kospi')[:10]
        kosdaq_companies = get_companies('kosdaq')[:10]
        
        return jsonify({
            'kospi': kospi_companies,
            'kosdaq': kosdaq_companies
        })


@company_bp.route('/companies/view', methods=['POST'])
def record_company_view():
    """Record company view for popularity tracking"""
    try:
        data = request.get_json()
        market = data.get('market', 'KOSPI').upper()
        company_code = data.get('code', '')
        company_name = data.get('name', '')
        
        if not company_code:
            return jsonify({"success": False, "error": "코드가 필요합니다."})
        
        from app.services.firebase import increment_company_view
        
        success = increment_company_view(market, company_code, company_name)
        
        return jsonify({"success": success})
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@company_bp.route('/companies/corp-code')
def get_corp_code():
    """Get DART corp_code from stock ticker"""
    ticker = request.args.get('ticker', '').strip()
    
    if not ticker:
        return jsonify({'error': 'ticker is required', 'corp_code': ''})
    
    try:
        # DART에서 기업 고유번호 조회
        import requests
        from dotenv import load_dotenv
        load_dotenv()
        
        api_key = os.environ.get('DART_API_KEY', '')
        
        if not api_key:
            return jsonify({'error': 'DART API key not configured', 'corp_code': ''})
        
        # DART 기업 목록에서 종목코드로 검색
        # 먼저 캐시된 DART 기업 목록을 사용하거나 API 호출
        corp_code = find_corp_code_by_ticker(ticker, api_key)
        
        return jsonify({
            'ticker': ticker,
            'corp_code': corp_code
        })
        
    except Exception as e:
        return jsonify({'error': str(e), 'corp_code': ''})


# DART corp_code 캐시
_dart_corp_cache = {}

def find_corp_code_by_ticker(ticker, api_key):
    """DART corp_code 조회 (캐시 사용)"""
    global _dart_corp_cache
    
    # 캐시 확인
    if ticker in _dart_corp_cache:
        return _dart_corp_cache[ticker]
    
    # 캐시가 없으면 DART API 호출하여 전체 목록 로드
    if not _dart_corp_cache:
        load_dart_corp_list(api_key)
    
    return _dart_corp_cache.get(ticker, '')


def load_dart_corp_list(api_key):
    """DART 기업 목록 로드 (한번만 실행)"""
    global _dart_corp_cache
    
    try:
        import requests
        import zipfile
        import io
        import xml.etree.ElementTree as ET
        
        # DART 기업코드 목록 다운로드
        url = "https://opendart.fss.or.kr/api/corpCode.xml"
        params = {"crtfc_key": api_key}
        
        print(f"[DART] Requesting corp list from API...")
        response = requests.get(url, params=params, timeout=30)
        
        print(f"[DART] Response status: {response.status_code}, size: {len(response.content)} bytes")
        
        if response.status_code != 200:
            print(f"[DART] API error: HTTP {response.status_code}")
            return
        
        # 응답이 ZIP 파일인지 확인 (ZIP 파일은 PK로 시작)
        if not response.content.startswith(b'PK'):
            # ZIP이 아니면 에러 응답 (JSON 또는 XML)
            try:
                error_text = response.content.decode('utf-8')[:500]
                print(f"[DART] API returned non-ZIP response: {error_text}")
            except:
                print(f"[DART] API returned non-ZIP response (unable to decode)")
            return
        
        # ZIP 파일 압축 해제
        with zipfile.ZipFile(io.BytesIO(response.content)) as z:
            with z.open('CORPCODE.xml') as f:
                tree = ET.parse(f)
                root = tree.getroot()
                
                for corp in root.findall('list'):
                    stock_code = corp.findtext('stock_code', '').strip()
                    corp_code = corp.findtext('corp_code', '').strip()
                    
                    if stock_code:
                        _dart_corp_cache[stock_code] = corp_code
        
        print(f"[DART] Corp list loaded successfully: {len(_dart_corp_cache)} companies")
        
    except zipfile.BadZipFile as e:
        print(f"[DART] BadZipFile error: API may have returned an error message instead of ZIP")
    except requests.exceptions.Timeout:
        print(f"[DART] Request timeout - API may be slow or unavailable")
    except Exception as e:
        print(f"[DART] Error loading corp list: {type(e).__name__}: {e}")
