from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn

app = FastAPI()

# Mount static files directory
app.mount("/static", StaticFiles(directory="static"), name="static")

# Configure templates directory
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    user_agent = request.headers.get("user-agent", "").lower()
    if "android" in user_agent:
        template_name = "android_gui.html"
    else:
        template_name = "android_gui.html"
    return templates.TemplateResponse(template_name, {"request": request})

@app.get("/about", response_class=HTMLResponse)
async def about(request: Request):
    return templates.TemplateResponse("about.html", {"request": request})

@app.get("/contact", response_class=HTMLResponse)
async def contact(request: Request):
    return templates.TemplateResponse("contact.html", {"request": request})

if __name__ == "__main__":
    uvicorn.run("landing_page:app", host="0.0.0.0", port=8090, reload=False)
