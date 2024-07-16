from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from .. import crud, schemas, models, email_utils
from ..database import get_db
from .utils import create_access_token, create_refresh_token, verify_refresh_token, get_current_user
from ..redis_utils import set_user_session, delete_user_session
from datetime import datetime, timedelta

router = APIRouter()
ACCESS_TOKEN_EXPIRE_MINUTES = 30

from ..redis_utils import set_user_session


@router.post("/token", response_model=schemas.Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = crud.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )

    # 存储token到Redis
    set_user_session(user.id, access_token, int(access_token_expires.total_seconds()))

    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/refresh", response_model=schemas.Token)
async def refresh_token(token: str, db: Session = Depends(get_db)):
    username = verify_refresh_token(token)
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = crud.get_user_by_username(db, username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    access_token = create_access_token(data={"sub": user.username})
    refresh_token = create_refresh_token(data={"sub": user.username})
    set_user_session(user.id, access_token, ACCESS_TOKEN_EXPIRE_MINUTES * 60)
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}


@router.post("/logout")
async def logout(current_user: models.User = Depends(get_current_user)):
    delete_user_session(current_user.id)
    return {"message": "Successfully logged out"}


@router.post("/revoke")
async def revoke_token(token: str):
    await revoke_token(token)
    return {"message": "Token revoked"}


@router.post("/login/email-verification")
async def login_email_verification(email: str, db: Session = Depends(get_db)):
    user = crud.get_user_by_email(db, email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    verification_code = crud.create_verification_code(db, user.id)
    await email_utils.send_email(
        email,
        "Login Verification Code",
        f"Your verification code is: {verification_code}"
    )
    return {"message": "Verification code sent"}


@router.post("/login/email-verify", response_model=schemas.Token)
async def verify_email_login(verification: schemas.EmailVerification, db: Session = Depends(get_db)):
    user = crud.get_user_by_email(db, verification.email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not crud.verify_code(db, user.id, verification.verification_code):
        raise HTTPException(status_code=400, detail="Invalid or expired verification code")

    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/reset", status_code=status.HTTP_200_OK)
async def request_password_reset(email: schemas.EmailSchema, db: Session = Depends(get_db)):
    user = crud.get_user_by_email(db, email.email)
    if user:
        token = crud.create_password_reset_token(db, email.email)
        await email_utils.send_email(
            email.email,
            "Password Reset",
            f"Your password reset token is: {token}"
        )
    return {"message": "If an account with that email exists, we have sent a password reset token"}


@router.post("/users/{user_id}/reset_password", status_code=status.HTTP_200_OK)
def reset_password(reset_data: schemas.PasswordReset, db: Session = Depends(get_db)):
    success = crud.reset_password(db, reset_data.token, reset_data.new_password)
    if not success:
        raise HTTPException(status_code=400, detail="Invalid or expired token")
    return {"message": "Password has been reset successfully"}

