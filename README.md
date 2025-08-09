# Micro‑SaaS: UTM Link Shortener + QR + Analytics

A simple FastAPI app to create short links with optional UTM parameters, generate QR codes, and track click analytics. Includes a minimal admin dashboard protected by a token.

## Features
- Create short links with custom or auto-generated slugs
- Append UTM parameters automatically on redirect
- QR code for every link
- Click analytics (total clicks, daily chart for last 30 days, referrers)
- Minimal admin dashboard (token-protected)
- SQLite storage; Dockerized

## Quickstart

### 1) Local (Python)

Requirements: Python 3.10+

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env to set ADMIN_TOKEN (optional)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Open http://localhost:8000

- Dashboard: `/dashboard?token=YOUR_ADMIN_TOKEN` (or no token if you keep it empty)
- Create links in the dashboard
- Share `http://localhost:8000/l/<slug>`

### 2) Docker

```bash
docker build -t utm-shortener .
docker run -p 8000:8000 --env-file .env -v $PWD/data:/app/data utm-shortener
```

## Environment

See `.env.example`:

- `ADMIN_TOKEN`: Token to access the dashboard and stats pages. If empty, dashboard is open (not recommended for production).
- `DATABASE_URL`: Defaults to `sqlite:///data/data.db`.

## Monetization Ideas
- Free tier: limited links and analytics window
- Pro tier: custom domains, branded QR, export, team access (integrate Stripe Checkout)

## Project Structure

```
app/
  main.py
  database.py
  models.py
  templates/
    base.html
    index.html
    dashboard.html
    stats.html
  static/
    favicon.svg
```

## License
MIT

