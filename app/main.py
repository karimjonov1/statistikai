import os
import io
import secrets
import string
from datetime import datetime, timedelta
from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode

from fastapi import FastAPI, Request, Depends, Form, HTTPException, status
from fastapi.responses import RedirectResponse, StreamingResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from .database import Base, engine, get_db
from .models import Link, Click

import qrcode
from dotenv import load_dotenv
import json

load_dotenv()

app = FastAPI(title="UTM Shortener + QR + Analytics")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")
STATIC_DIR = os.path.join(BASE_DIR, "static")
DATA_DIR = os.path.join(os.path.dirname(BASE_DIR), "data")

os.makedirs(DATA_DIR, exist_ok=True)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
templates = Jinja2Templates(directory=TEMPLATES_DIR)

ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", "").strip()

# Create tables
Base.metadata.create_all(bind=engine)


def is_authorized(request: Request) -> bool:
    if not ADMIN_TOKEN:
        return True
    token = request.query_params.get("token") or request.headers.get("X-Admin-Token")
    return token == ADMIN_TOKEN


def require_admin(request: Request):
    if not is_authorized(request):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")


def generate_slug(existing_checker, length: int = 6) -> str:
    alphabet = string.ascii_lowercase + string.digits
    for _ in range(100):
        candidate = "".join(secrets.choice(alphabet) for _ in range(length))
        if not existing_checker(candidate):
            return candidate
    raise RuntimeError("Failed to generate unique slug")


def build_target_with_utm(target_url: str, link: Link) -> str:
    url_parts = list(urlparse(target_url))
    query = dict(parse_qsl(url_parts[4], keep_blank_values=True))
    if link.utm_source:
        query["utm_source"] = link.utm_source
    if link.utm_medium:
        query["utm_medium"] = link.utm_medium
    if link.utm_campaign:
        query["utm_campaign"] = link.utm_campaign
    if link.utm_term:
        query["utm_term"] = link.utm_term
    if link.utm_content:
        query["utm_content"] = link.utm_content
    url_parts[4] = urlencode(query, doseq=True)
    return urlunparse(url_parts)


@app.get("/", response_class=HTMLResponse)
async def landing(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "is_secured": bool(ADMIN_TOKEN)},
    )


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, db: Session = Depends(get_db)):
    require_admin(request)
    links = db.query(Link).order_by(Link.created_at.desc()).all()
    return templates.TemplateResponse(
        "dashboard.html",
        {"request": request, "links": links, "token": request.query_params.get("token", "")},
    )


@app.post("/links")
async def create_link(
    request: Request,
    target_url: str = Form(...),
    slug: str | None = Form(None),
    utm_source: str | None = Form(None),
    utm_medium: str | None = Form(None),
    utm_campaign: str | None = Form(None),
    utm_term: str | None = Form(None),
    utm_content: str | None = Form(None),
    db: Session = Depends(get_db),
):
    require_admin(request)

    target_url = target_url.strip()
    if not (target_url.startswith("http://") or target_url.startswith("https://")):
        raise HTTPException(status_code=400, detail="URL must start with http:// or https://")

    def exists(s: str) -> bool:
        return db.query(Link).filter_by(slug=s).first() is not None

    if slug:
        slug = slug.strip().lower()
        if exists(slug):
            raise HTTPException(status_code=400, detail="Slug already taken")
    else:
        slug = generate_slug(exists)

    link = Link(
        slug=slug,
        target_url=target_url,
        utm_source=(utm_source or None),
        utm_medium=(utm_medium or None),
        utm_campaign=(utm_campaign or None),
        utm_term=(utm_term or None),
        utm_content=(utm_content or None),
    )
    db.add(link)
    db.commit()
    db.refresh(link)

    token_q = f"?token={ADMIN_TOKEN}" if ADMIN_TOKEN else ""
    return RedirectResponse(url=f"/dashboard{token_q}", status_code=status.HTTP_303_SEE_OTHER)


@app.get("/l/{slug}")
async def resolve_link(slug: str, request: Request, db: Session = Depends(get_db)):
    link = db.query(Link).filter_by(slug=slug).first()
    if not link:
        raise HTTPException(status_code=404, detail="Link not found")

    # Record click
    referrer = request.headers.get("referer")
    user_agent = request.headers.get("user-agent")
    ip_address = request.client.host if request.client else None
    db.add(Click(link_id=link.id, referrer=referrer, user_agent=user_agent, ip_address=ip_address))
    db.commit()

    target = build_target_with_utm(link.target_url, link)
    return RedirectResponse(url=target, status_code=status.HTTP_307_TEMPORARY_REDIRECT)


@app.get("/links/{slug}/qr.png")
async def qr_png(slug: str, request: Request, db: Session = Depends(get_db)):
    require_admin(request)
    link = db.query(Link).filter_by(slug=slug).first()
    if not link:
        raise HTTPException(status_code=404, detail="Link not found")

    short_url = str(request.url_for("resolve_link", slug=slug))
    img = qrcode.make(short_url)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return StreamingResponse(buf, media_type="image/png")


@app.get("/links/{slug}/stats", response_class=HTMLResponse)
async def link_stats(slug: str, request: Request, db: Session = Depends(get_db)):
    require_admin(request)
    link = db.query(Link).filter_by(slug=slug).first()
    if not link:
        raise HTTPException(status_code=404, detail="Link not found")

    # Last 30 days
    now = datetime.utcnow()
    start = now - timedelta(days=29)

    clicks = (
        db.query(Click)
        .filter(Click.link_id == link.id, Click.created_at >= start)
        .order_by(Click.created_at.asc())
        .all()
    )

    # Aggregate by day
    by_day = {}
    for i in range(30):
        day = (start + timedelta(days=i)).date()
        by_day[day.isoformat()] = 0
    for c in clicks:
        key = c.created_at.date().isoformat()
        if key in by_day:
            by_day[key] += 1

    labels = list(by_day.keys())
    values = [by_day[k] for k in labels]

    total_clicks = db.query(Click).filter(Click.link_id == link.id).count()
    recent_referrers = [c.referrer for c in clicks if c.referrer]

    return templates.TemplateResponse(
        "stats.html",
        {
            "request": request,
            "link": link,
            "labels_json": json.dumps(labels),
            "values_json": json.dumps(values),
            "total_clicks": total_clicks,
            "recent_referrers": recent_referrers[-10:],
            "token": request.query_params.get("token", ""),
        },
    )