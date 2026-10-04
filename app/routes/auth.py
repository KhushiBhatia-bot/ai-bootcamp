import secrets
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.config import OTP_EXPIRY_MINUTES
from app.database import get_db
from app.models.email_verification import EmailVerification
from app.models.user import User
from app.schemas.auth import (
    LoginRequest,
    LoginResponse,
    RegisterRequest,
    RegisterResponse,
    VerifyEmailRequest,
    VerifyEmailResponse,
)
from app.services.email_service import send_otp_email
from pwdlib import PasswordHash
from app.services.auth_service import create_access_token
from app.dependencies.auth import get_current_user

router = APIRouter(
    prefix="/api/v1/auth",
    tags=["Authentication"],
)

password_hash = PasswordHash.recommended()


@router.post(
    "/register",
    response_model=RegisterResponse,
)
def register(
    request: RegisterRequest,
    db: Session = Depends(get_db),
):
    existing_user = (
        db.query(User)
        .filter(User.email == request.email)
        .first()
    )

    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Email is already registered",
        )

    # Hash the user's password
    hashed_password = password_hash.hash(request.password)

    user = User(
        email=request.email,
        password_hash=hashed_password,
        is_verified=False,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    # Generate a 6-digit OTP
    otp = f"{secrets.randbelow(1_000_000):06d}"

    # Hash the OTP before storing it
    otp_hash = password_hash.hash(otp)

    verification = EmailVerification(
        user_id=user.id,
        otp_hash=otp_hash,
        expires_at=datetime.utcnow()
        + timedelta(minutes=OTP_EXPIRY_MINUTES),
        attempts=0,
        used=False,
    )

    db.add(verification)
    db.commit()

    # Send OTP to the user's email
    send_otp_email(
        recipient_email=user.email,
        otp=otp,
    )

    return {
        "message": (
            "Registration successful. "
            "A verification code has been sent to your email."
        ),
        "email": user.email,
    }

@router.post(
    "/verify-email",
    response_model=VerifyEmailResponse,
)
def verify_email(
    request: VerifyEmailRequest,
    db: Session = Depends(get_db),
):
    user = (
        db.query(User)
        .filter(User.email == request.email)
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found",
        )

    if user.is_verified:
        raise HTTPException(
            status_code=400,
            detail="Email is already verified",
        )

    verification = (
        db.query(EmailVerification)
        .filter(
            EmailVerification.user_id == user.id,
            EmailVerification.used == False,
        )
        .order_by(
            EmailVerification.created_at.desc()
        )
        .first()
    )

    if not verification:
        raise HTTPException(
            status_code=400,
            detail="No active verification code found",
        )

    # Check expiry
    if datetime.utcnow() > verification.expires_at:
        raise HTTPException(
            status_code=400,
            detail="Verification code has expired",
        )

    # Check maximum attempts
    if verification.attempts >= 5:
        raise HTTPException(
            status_code=400,
            detail="Too many incorrect attempts",
        )

    # Check OTP
    if not password_hash.verify(
        request.otp,
        verification.otp_hash,
    ):
        verification.attempts += 1
        db.commit()

        raise HTTPException(
            status_code=400,
            detail="Invalid verification code",
        )

    # OTP is valid
    verification.used = True
    user.is_verified = True

    db.commit()

    return {
        "message": "Email verified successfully.",
        "email": user.email,
    }

@router.post(
    "/login",
    response_model=LoginResponse,
)
def login(
    request: LoginRequest,
    db: Session = Depends(get_db),
):
    user = (
        db.query(User)
        .filter(User.email == request.email)
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password",
        )

    if not password_hash.verify(
        request.password,
        user.password_hash,
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password",
        )

    if not user.is_verified:
        raise HTTPException(
            status_code=403,
            detail="Please verify your email before logging in",
        )

    access_token = create_access_token(user.id)

    return {
        "access_token": access_token,
        "token_type": "bearer",
    }

@router.get("/me")
def get_me(
    current_user: User = Depends(get_current_user),
):
    return {
        "id": current_user.id,
        "email": current_user.email,
        "is_verified": current_user.is_verified,
    }