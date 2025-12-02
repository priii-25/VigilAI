"""
Authentication endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, EmailStr
from src.core.database import get_db
from src.core.security import hash_password, verify_password, create_access_token
from src.models.user import User

router = APIRouter()


class UserRegister(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    role: str = "user"


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


@router.post("/register", response_model=Token)
async def register(user_data: UserRegister, db: AsyncSession = Depends(get_db)):
    """Register new user"""
    # Check if user exists
    result = await db.execute(select(User).where(User.email == user_data.email))
    existing_user = result.scalar_one_or_none()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    new_user = User(
        email=user_data.email,
        hashed_password=hash_password(user_data.password),
        full_name=user_data.full_name,
        role=user_data.role
    )
    
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    
    # Generate token
    access_token = create_access_token({"sub": user_data.email, "role": user_data.role})
    
    return Token(access_token=access_token)


@router.post("/login", response_model=Token)
async def login(credentials: UserLogin, db: AsyncSession = Depends(get_db)):
    """User login"""
    # Find user
    result = await db.execute(select(User).where(User.email == credentials.email))
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )
    
    # Generate token
    access_token = create_access_token({"sub": user.email, "role": user.role})
    
    return Token(access_token=access_token)
