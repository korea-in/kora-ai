from flask import Blueprint, jsonify, request
import csv
import os
import random

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

@company_bp.route('/companies/random')
def random_companies():
    """Get random 5 companies from selected market"""
    market = request.args.get('market', 'kospi').lower()
    
    companies = get_companies(market)
    
    if len(companies) < 5:
        return jsonify(companies)
    
    random_selection = random.sample(companies, 5)
    return jsonify(random_selection)

@company_bp.route('/companies/popular')
def popular_companies():
    """Get popular companies (mock data for now)"""
    # 인기 회사 목록 (실제로는 조회수 기반으로 구현)
    kospi_companies = get_companies('kospi')[:10]
    kosdaq_companies = get_companies('kosdaq')[:10]
    
    return jsonify({
        'kospi': kospi_companies,
        'kosdaq': kosdaq_companies
    })


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
        
        response = requests.get(url, params=params)
        
        if response.status_code == 200:
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
        
        print(f"DART corp list loaded: {len(_dart_corp_cache)} companies")
        
    except Exception as e:
        print(f"Error loading DART corp list: {e}")
