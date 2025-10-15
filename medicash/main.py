from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from .routers import auth, cards, txns, tools, travel, remit

app = FastAPI(title="MedICash")

app.include_router(auth.router)
app.include_router(cards.router)
app.include_router(txns.router)
app.include_router(tools.router)
app.include_router(travel.router)
app.include_router(remit.router)

app.mount("/static", StaticFiles(directory="medicash/static"), name="static")
templates = Jinja2Templates(directory="medicash/templates")


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})
