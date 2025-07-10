from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.base import BaseHTTPMiddleware
import uvicorn

app = FastAPI()

# Blocked IPs
BLOCKED_IPS = {"185.177.72.3" ,"52.169.54.134"}

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

# Add the middleware
app.add_middleware(BlockIPMiddleware)

# Mount static files directory
app.mount("/static", StaticFiles(directory="static"), name="static")

# Configure templates directory
templates = Jinja2Templates(directory="templates")

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


if __name__ == "__main__":
    uvicorn.run("landing_page:app", host="0.0.0.0", port=8090, reload=False)
