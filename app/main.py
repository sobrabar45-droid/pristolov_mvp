from pathlib import Path
from secrets import compare_digest

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import text

from app.config import settings
from app.database import engine
from app.models import Base
import app.models  # noqa: F401

from app.routes.dev import router as dev_router
from app.routes.cashier import router as cashier_router
from app.routes.join import router as join_router
from app.routes.delegation import router as delegation_router
from app.routes.player import router as player_router
from app.routes.gold import router as gold_router
from app.services.scenario_service import ensure_scenario_schema
from app.services.expedition_service import ensure_expedition_schema
from app.services.house_service import ensure_house_schema
from app.services.tower_service import ensure_tower_schema
from app.services.duel_service import ensure_duel_schema

BASE_DIR = Path(__file__).resolve().parent
QUESTIONS_MEDIA_DIR = BASE_DIR / "static" / "questions_media"
QUESTIONS_MEDIA_DIR.mkdir(parents=True, exist_ok=True)
PROTECTED_ROUTE_PREFIXES = ("/dev", "/gold", "/cashier")
ADMIN_TOKEN_HEADER = "X-Admin-Token"

app = FastAPI(title="приСтолов Digital MVP")

def _is_protected_route(path: str) -> bool:
    return any(
        path == prefix or path.startswith(f"{prefix}/")
        for prefix in PROTECTED_ROUTE_PREFIXES
    )


@app.middleware("http")
async def protect_operator_routes(request: Request, call_next):
    admin_token = (settings.ADMIN_ROUTE_TOKEN or "").strip()

    # Local/dev remains usable without a token; public VPS deployment must set ADMIN_ROUTE_TOKEN.
    if admin_token and _is_protected_route(request.url.path):
        supplied_token = request.headers.get(ADMIN_TOKEN_HEADER, "")
        if not supplied_token or not compare_digest(supplied_token, admin_token):
            return PlainTextResponse("Admin route token required", status_code=403)

    return await call_next(request)


app.mount("/static/questions_media", StaticFiles(directory=str(QUESTIONS_MEDIA_DIR)), name="questions_media")
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="app/templates")

Base.metadata.create_all(bind=engine)
ensure_scenario_schema(engine)
ensure_expedition_schema(engine)
ensure_house_schema(engine)
ensure_tower_schema(engine)
ensure_duel_schema(engine)

# ВАЖНО:
# dev роутер подключаем только ОДИН раз и только с префиксом /dev
app.include_router(dev_router, prefix="/dev", tags=["dev"])
app.include_router(cashier_router)
app.include_router(join_router)
app.include_router(delegation_router)
app.include_router(player_router)
app.include_router(gold_router)


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={}
    )


@app.get("/health")
def health():
    db_status = "unknown"

    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        db_status = "ok"
    except Exception as e:
        db_status = f"error: {str(e)}"

    return {
        "app": "ok",
        "database": db_status,
        "database_url_loaded": True,
    }
