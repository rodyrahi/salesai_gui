from fastapi import FastAPI, Request, Form, Depends, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.sessions import SessionMiddleware
from authlib.integrations.starlette_client import OAuth
from starlette.config import Config
from sqladmin import Admin, ModelView
import uvicorn

from models import User
from database import SessionLocal, engine, Base

# ---------------------------------------------------------------
config = Config(".env")
oauth = OAuth(config)

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key=config("SECRET_KEY"))

# ---------------------------------------------------------------
# Blocked IPs
BLOCKED_IPS = {"185.177.72.3", "45.134.26.35", "52.169.54.134", "37.66.177.118", "209.38.22.242", "185.177.72.12"}

class BlockIPMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host
        if client_ip in BLOCKED_IPS:
            return JSONResponse(
                status_code=403,
                content={"detail": "Access forbidden: your IP is blocked."}
            )
        return await call_next(request)

app.add_middleware(BlockIPMiddleware)

# ---------------------------------------------------------------
# Static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# ---------------------------------------------------------------
# Admin credentials
ADMIN_USERNAME = config("ADMIN_USERNAME", cast=str, default="admin")
ADMIN_PASSWORD = config("ADMIN_PASSWORD", cast=str, default="changeme")

# ---------------------------------------------------------------
# Session-based admin auth dependency
def require_admin_session(request: Request):
    if not request.session.get("is_admin"):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

# ---------------------------------------------------------------
# Admin setup
admin = Admin(app=app, engine=engine, base_url="/sales_database")

class UserAdmin(ModelView, model=User):
    column_list = [User.sub, User.name, User.email]

admin.add_view(UserAdmin)

# ---------------------------------------------------------------
# Middleware to protect /sales_database
class AdminAuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path.startswith("/sales_database"):
            if not request.session.get("is_admin"):
                return RedirectResponse("/login")
        return await call_next(request)

# 👇 Custom middlewares first
app.add_middleware(AdminAuthMiddleware)





# ---------------------------------------------------------------
# OAuth (kept same as yours)
oauth.register(
    name='google',
    client_id=config('GOOGLE_CLIENT_ID'),
    client_secret=config('GOOGLE_CLIENT_SECRET'),
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={'scope': 'openid email profile'}
)

# ---------------------------------------------------------------
# Login form
@app.get("/login", response_class=HTMLResponse)
async def login_form(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
async def login(request: Request, username: str = Form(...), password: str = Form(...)):
    if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
        request.session["is_admin"] = True
        return RedirectResponse("/sales_database", status_code=302)
    else:
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Invalid username or password."},
            status_code=401
        )

# ---------------------------------------------------------------
@app.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/", status_code=302)

# ---------------------------------------------------------------
# Basic pages
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    user_agent = request.headers.get("user-agent", "").lower()
    if any(mobile in user_agent for mobile in ["android", "iphone", "ipad", "mobile"]):
        template_name = "android_gui.html"
    else:
        template_name = "gui.html"
    return templates.TemplateResponse(template_name, {"request": request})

@app.get("/about", response_class=HTMLResponse)
async def about(request: Request):
    return templates.TemplateResponse("about.html", {"request": request})

@app.get("/contact", response_class=HTMLResponse)
async def contact(request: Request):
    return templates.TemplateResponse("contact.html", {"request": request})

@app.get("/pricing", response_class=HTMLResponse)
async def pricing(request: Request):
    return templates.TemplateResponse("pricing.html", {"request": request})

# ---------------------------------------------------------------
if __name__ == "__main__":
    uvicorn.run("landing_page:app", host="0.0.0.0", port=8090, reload=True)
