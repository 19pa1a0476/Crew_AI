from typing import Optional
from sqlalchemy.orm import Session
from configuration import OKTAConfig
from fastapi import APIRouter, Depends, Header
from utilities.token_validator import validate_token
from utilities.pg_sql_db_util import get_db, get_or_create_user, get_user_by_external_id
from models.request_response_models import UserRequest

router = APIRouter()

@router.post("/create")
def create_user(user: UserRequest, db: Session = Depends(get_db), authorization: Optional[str] = Header(None)):
    """Create a new user or get existing user"""

    validate_token(
        bearer_token=authorization,
        metadata=OKTAConfig.OKTA_JWT_OAUTH_CONFIG,
        okta_enable=OKTAConfig.OKTA_ENABLED,
        user_id=user.user_id
    )

    db_user = get_or_create_user(
        db=db, 
        username=user.username, 
        external_id=user.user_id
    )
    return {
        "user_id": db_user.id,
        "external_id": db_user.external_id,
        "username": db_user.username
    }


@router.post("/get")
def create_user(user: UserRequest, db: Session = Depends(get_db), authorization: Optional[str] = Header(None)):
    """get existing user"""

    validate_token(
        bearer_token=authorization,
        metadata=OKTAConfig.OKTA_JWT_OAUTH_CONFIG,
        okta_enable=OKTAConfig.OKTA_ENABLED,
        user_id=user.user_id
    )

    db_user = get_user_by_external_id(
        db=db, 
        external_id=user.user_id
    )
    return {
        "user_id": db_user.id,
        "external_id": db_user.external_id,
        "username": db_user.username
    }