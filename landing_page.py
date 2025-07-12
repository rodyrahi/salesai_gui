import os
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.sessions import SessionMiddleware
from authlib.integrations.starlette_client import OAuth
from dotenv import load_dotenv
import uvicorn

load_dotenv()

app = FastAPI()

# Blocked IPs
BLOCKED_IPS = {"185.177.72.3", "45.134.26.35", "52.169.54.134", "37.66.177.118", "209.38.22.242", "185.177.72.12"}

# Middleware to block IPs
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

# Add Session Middleware
app.add_middleware(SessionMiddleware, secret_key=os.getenv("SECRET_KEY"))

# Mount static files directory
app.mount("/static", StaticFiles(directory="static"), name="static")

# Configure templates directory
templates = Jinja2Templates(directory="templates")

# Configure OAuth
oauth = OAuth()
oauth.register(
    name='google',
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={
        'scope': 'openid email profile'
    }
)










from jose import jwt
import datetime

SECRET = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"









@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    user = request.session.get('user')
    user_agent = request.headers.get("user-agent", "").lower()
    
    print("loggedin user:", user)  # Debugging line to check user agent
    
    
    if user:
        
        # request.session['user'] = user

        # ✅ Make a signed JWT
        payload = {
            "sub": user["sub"],
            "email": user["email"],
            "name": user["name"],
            "exp": datetime.datetime.utcnow() + datetime.timedelta(minutes=30)
        }
        user_jwt = jwt.encode(payload, SECRET, algorithm=ALGORITHM)

        # Redirect to your main app with JWT
        return RedirectResponse(url=f"http://localhost:8080/auth/callback?token={user_jwt}")
    
    if any(mobile in user_agent for mobile in ["android", "iphone", "ipad", "mobile"]):
        template_name = "android_gui.html"
    else:
        template_name = "gui.html"
        
        
        
    
    return templates.TemplateResponse(template_name, {"request": request, "user": user})


@app.get("/about", response_class=HTMLResponse)
async def about(request: Request):
    return templates.TemplateResponse("about.html", {"request": request})


@app.get("/contact", response_class=HTMLResponse)
async def contact(request: Request):
    return templates.TemplateResponse("contact.html", {"request": request})


@app.get("/pricing", response_class=HTMLResponse)
async def pricing(request: Request):
    return templates.TemplateResponse("pricing.html", {"request": request})

# Login route
@app.get("/login")
async def login(request: Request):
    redirect_uri = request.url_for('auth')
    return await oauth.google.authorize_redirect(request, redirect_uri)

# @app.get("/auth")
# async def auth(request: Request):
#     token = await oauth.google.authorize_access_token(request)
#     resp = await oauth.google.get(
#         'https://openidconnect.googleapis.com/v1/userinfo',
#         token=token
#     )
#     user_info = await resp.json()  # ✅ must await json()
#     request.session['user'] = user_info  # already a dict
#     return RedirectResponse(url='/')


@app.get("/auth")
async def auth(request: Request):
    token = await oauth.google.authorize_access_token(request)
    userinfo_endpoint = oauth.google.server_metadata['userinfo_endpoint']
    resp = await oauth.google.get(userinfo_endpoint, token=token)
    user_info = resp.json()

    request.session['user'] = user_info

    # ✅ Make a signed JWT
    payload = {
        "sub": user_info["sub"],
        "email": user_info["email"],
        "name": user_info["name"],
        "exp": datetime.datetime.utcnow() + datetime.timedelta(minutes=30)
    }
    user_jwt = jwt.encode(payload, SECRET, algorithm=ALGORITHM)

    # Redirect to your main app with JWT
    return RedirectResponse(url=f"http://localhost:8080/auth/callback?token={user_jwt}")

# Logout route
@app.get("/logout")
async def logout(request: Request):
    request.session.pop('user', None)
    return RedirectResponse(url='/')


if __name__ == "__main__":
    uvicorn.run("landing_page:app", host="0.0.0.0", port=8090, reload=True)
