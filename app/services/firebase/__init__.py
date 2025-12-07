# Firebase Services
from app.services.firebase.auth_service import (
    init_firebase,
    is_firebase_initialized,
    get_db,
    create_user,
    verify_user_password,
    get_user_by_uid,
    get_user_by_email,
    get_firebase_user_by_email,
    verify_user_by_email_and_name,
    reset_user_password,
    update_user,
    update_last_login,
    increment_analysis_count,
    add_favorite_company,
    remove_favorite_company,
    verify_id_token,
    login_required
)

from app.services.firebase.firestore_service import (
    save_analysis_history,
    get_user_analysis_history,
    increment_company_view,
    get_popular_companies,
    get_report_based_popular,
    save_report,
    get_user_reports,
    get_public_reports,
    get_report_by_id,
    use_user_credits,
    get_user_credits
)

__all__ = [
    # Auth
    'init_firebase',
    'is_firebase_initialized',
    'get_db',
    'create_user',
    'verify_user_password',
    'get_user_by_uid',
    'get_user_by_email',
    'get_firebase_user_by_email',
    'verify_user_by_email_and_name',
    'reset_user_password',
    'update_user',
    'update_last_login',
    'increment_analysis_count',
    'add_favorite_company',
    'remove_favorite_company',
    'verify_id_token',
    'login_required',
    # Firestore
    'save_analysis_history',
    'get_user_analysis_history',
    'increment_company_view',
    'get_popular_companies',
    'get_report_based_popular',
    # Reports
    'save_report',
    'get_user_reports',
    'get_public_reports',
    'get_report_by_id',
    'use_user_credits',
    'get_user_credits',
]

