from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models import AuthUser
from app.database import SessionLocal
from app.security_config import hash_password

class AuthUserService():
    
    async def create_default_admin(self):
        async with SessionLocal() as session:
            result = await session.execute(select(AuthUser).where(AuthUser.email == "admin@example.com"))
            admin = result.scalar_one_or_none()

            if not admin:
                new_admin = AuthUser(
                    email="admin@example.com",
                    password_hash=hash_password("admin123"),
                    role="admin",
                    is_active=True
                )
                session.add(new_admin)
                await session.commit()
                print("✅ Default admin created")
            else:
                print("ℹ️ Admin already exists")
    