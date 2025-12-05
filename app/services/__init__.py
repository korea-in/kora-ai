# Services Module
# 서비스별 구조화된 모듈

# Firebase Services
from app.services.firebase import (
    init_firebase,
    is_firebase_initialized,
    get_db,
    create_user,
    get_user_by_uid,
    get_user_by_email,
    get_firebase_user_by_email,
    update_user,
    update_last_login,
    increment_analysis_count,
    add_favorite_company,
    remove_favorite_company,
    verify_id_token,
    login_required,
    save_analysis_history,
    get_user_analysis_history,
    increment_company_view,
    get_popular_companies,
)

# Naver API Services
from app.services.naver import (
    search_news,
    search_company_news,
    NaverNewsItem,
    NaverNewsResponse,
)

# KRX 주식 데이터 Services
from app.services.krx import (
    get_current_price,
    get_price_history,
    get_yearly_trend,
    get_moving_averages,
    get_volume_trend,
    get_stock_summary,
    get_valuation,
    calculate_rsi,
    calculate_mfi,
    get_technical_indicators,
    StockPrice,
    StockSummary,
)

# OpenAI GPT-4o Services
from app.services.openai import (
    analyze_company,
    analyze_financials,
    analyze_news_sentiment,
    summarize_disclosure,
    generate_investment_report,
    chat_completion,
)

# DART API Services
# from app.services.dart import ...

__all__ = [
    # Firebase Auth
    'init_firebase',
    'is_firebase_initialized',
    'get_db',
    'create_user',
    'get_user_by_uid',
    'get_user_by_email',
    'get_firebase_user_by_email',
    'update_user',
    'update_last_login',
    'increment_analysis_count',
    'add_favorite_company',
    'remove_favorite_company',
    'verify_id_token',
    'login_required',
    # Firebase Firestore
    'save_analysis_history',
    'get_user_analysis_history',
    'increment_company_view',
    'get_popular_companies',
    # Naver
    'search_news',
    'search_company_news',
    'NaverNewsItem',
    'NaverNewsResponse',
    # KRX
    'get_current_price',
    'get_price_history',
    'get_yearly_trend',
    'get_moving_averages',
    'get_volume_trend',
    'get_stock_summary',
    'get_valuation',
    'calculate_rsi',
    'calculate_mfi',
    'get_technical_indicators',
    'StockPrice',
    'StockSummary',
    # OpenAI
    'analyze_company',
    'analyze_financials',
    'analyze_news_sentiment',
    'summarize_disclosure',
    'generate_investment_report',
    'chat_completion',
]
