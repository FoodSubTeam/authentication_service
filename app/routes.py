from fastapi import APIRouter, Depends, HTTPException, Header, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models import AuthUser
from app.schemas import AuthUserSchema, LoginRequest, AdminCreateUser
from app.database import SessionLocal
from app.kafka import KafkaProducerSingleton
from app.security_config import hash_password, verify_password, create_access_token
from app.security import require_role
from app.topics import Topic, MessageType
import json
import logging

router = APIRouter()

async def get_db():
    async with SessionLocal() as session:
        yield session


@router.post("/auth/register")
async def register_user(user: AuthUserSchema, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(AuthUser).where(AuthUser.email == user.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")

    new_user = AuthUser(
        email=user.email,
        password_hash=hash_password(user.password),
        role="customer",
        is_active=True
    )
    db.add(new_user)
    await db.commit()
    
    message = {
        "type": MessageType.SEND_AUTH_URL.value,
        "data": {
            "email": user.email,
            "given_name": user.first_name,
            "family_name": user.last_name
        }
    }

    KafkaProducerSingleton.produce_message(Topic.AUTH_LOGIN_URL.value, json.dumps(message))
    logging.warning("Sent new user data.")

    return {"message": "User registered successfully"}


@router.post("/auth/login")
async def login(data: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(AuthUser).where(AuthUser.email == data.email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token({
        "sub": str(user.id),
        "email": user.email,
        "role": user.role
    })

    return {"access_token": token, "token_type": "bearer"}


@router.post("/auth/create_user")
async def create_user_by_admin(
    user: AdminCreateUser,
    current_user=Depends(require_role(["admin"])),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(AuthUser).where(AuthUser.email == user.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already exists")

    new_user = AuthUser(
        email=user.email,
        password_hash=hash_password(user.password),
        role=user.role,
        is_active=True
    )
    db.add(new_user)
    await db.commit()
    
    message = {
        "type": MessageType.SEND_AUTH_URL.value,
        "data": {
            "email": user.email,
            "role": user.role
        }
    }

    KafkaProducerSingleton.produce_message(Topic.AUTH_LOGIN_URL.value, json.dumps(message))
    logging.warning("Sent new user data from admin.")

    return {"message": f"{user.role.capitalize()} user created."}


@router.get("/auth/users")
async def get_auth_users(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(AuthUser))
    users = result.scalars().all()
    return {"users": users}


# Test endpoint
@router.get("/auth/test")
async def test_auth():
    logging.warning("auth test hit")
    return {"message": "ok"}


@router.get("/auth/debug-headers")
async def debug_headers(request: Request):
    return dict(request.headers)