# Reliquary

Zero-knowledge encrypted file hosting. The browser encrypts everything before
upload (AES-256-GCM, key derived from your password via PBKDF2); the server only
ever stores encrypted blobs. Keys never leave the browser.

- **Backend:** Django 6 + DRF, PostgreSQL 16, JWT auth
- **Frontend:** SvelteKit + TypeScript, Web Crypto API
- **Deploy:** Docker Compose

## Quick start (Docker Compose)

Everything — database, API, and frontend — runs from one file:

```bash
docker compose up --build
```

- Frontend: http://localhost:5173
- API: http://localhost:8000/api/

Migrations run automatically. Create an account from the login screen and you're in.

To stop: `docker compose down` (add `-v` to also wipe the database volume).

### Going to production

The default compose config uses dev settings and insecure secrets. For a real
deployment, override these via environment (e.g. an `.env` file or your host's
secret store):

| Variable | Change to |
|----------|-----------|
| `DJANGO_SETTINGS_MODULE` | `config.settings.prod` |
| `DJANGO_SECRET_KEY` | a long random value |
| `DJANGO_DEBUG` | `false` |
| `DJANGO_ALLOWED_HOSTS` | your domain(s) |
| `CORS_ALLOWED_ORIGINS` | your frontend URL |
| `POSTGRES_PASSWORD` / `DATABASE_URL` | a strong DB password |

Put the app behind a TLS-terminating reverse proxy (HTTPS is required for the
Web Crypto API on anything but localhost).

## Local development (without Docker)

**Backend** — requires [uv](https://docs.astral.sh/uv/) and a running Postgres:

```bash
docker compose up -d db
cd backend
cp .env.example .env
uv sync
uv run python manage.py migrate
uv run python manage.py runserver
```

**Frontend:**

```bash
cd frontend
npm install
npm run dev
```

## Project layout

```
reliquary/
├── docker-compose.yml      # db + backend + frontend
├── docs/adr/               # Architecture Decision Records
├── backend/                # Django API
│   ├── config/settings/    # base.py, dev.py, prod.py
│   └── apps/
│       ├── accounts/       # email user, JWT + Google OAuth
│       ├── files/          # folders + encrypted files
│       └── audit/          # audit log
└── frontend/               # SvelteKit app
```

## API

Base URL: `/api/`. Auth is JWT (access 15 min, refresh 7 days).

| Method | Path                       | Description                 |
|--------|----------------------------|-----------------------------|
| POST   | `/auth/register/`          | Create account              |
| POST   | `/auth/login/`             | Obtain access + refresh JWT |
| POST   | `/auth/token/refresh/`     | Refresh access token        |
| POST   | `/auth/google/`            | Sign in with Google         |
| GET    | `/auth/me/`                | Current user profile        |
| —      | `/folders/`, `/files/`     | Folders and encrypted files |

## How the encryption works

On login the browser derives an AES-256-GCM master key from your password
(PBKDF2, per-user salt). Files are encrypted before upload and decrypted after
download — entirely in the browser. The server stores only the ciphertext and
its nonce, never the key. The key is kept as a non-extractable key in IndexedDB,
so it survives refreshes but never exposes its raw bytes.
