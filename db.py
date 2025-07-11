from fastapi import FastAPI, Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from sqladmin import Admin, ModelView
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from contextlib import asynccontextmanager
import base64
import secrets

from models import Base, User

DATABASE_URL = "sqlite+aiosqlite:///./test.db"

engine = create_async_engine(DATABASE_URL, echo=True)
async_session = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield

app = FastAPI(lifespan=lifespan)

# -----------------------
# REAL Basic Auth Middleware
# -----------------------

class BasicAuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path.startswith("/admin"):
            auth = request.headers.get("Authorization")
            if not auth or not auth.startswith("Basic "):
                return Response(
                    status_code=401,
                    headers={"WWW-Authenticate": "Basic"},
                    content="Unauthorized"
                )
            encoded = auth.split(" ")[1]
            decoded = base64.b64decode(encoded).decode("utf-8")
            username, password = decoded.split(":", 1)

            if not (
                secrets.compare_digest(username, "rajvendra@69")
                and secrets.compare_digest(password, "kamingo@69")
            ):
                return Response(
                    status_code=401,
                    headers={"WWW-Authenticate": "Basic"},
                    content="Unauthorized"
                )
        return await call_next(request)

app.add_middleware(BasicAuthMiddleware)

# -----------------------
# SQLAdmin setup
# -----------------------

admin = Admin(app, engine)

class UserAdmin(ModelView, model=User):
    column_list = [User.id, User.name, User.email]

admin.add_view(UserAdmin)
