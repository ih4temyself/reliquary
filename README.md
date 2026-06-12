# Reliquary

Secure encrypted file hosting with client-side (zero-knowledge) E2E encryption.
The server only ever stores encrypted blobs; encryption keys never leave the browser.

- **Backend:** Django 6 + Django REST Framework, PostgreSQL 16, JWT auth
- **Frontend:** SvelteKit + TypeScript, Web Crypto API (AES-256-GCM)
- **Deploy:** Docker Compose

## Project layout

```
reliquary/
├── docker-compose.yml      # Postgres (dev)
├── docs/adr/               # Architecture Decision Records
├── backend/                # Django API
│   ├── config/             # project: split settings, urls, wsgi/asgi
│   │   └── settings/       # base.py, dev.py, prod.py
│   └── apps/
│       ├── accounts/       # custom email user, JWT auth
│       ├── files/          # folders + encrypted files
│       └── audit/          # audit log
└── frontend/               # SvelteKit (planned)
```

## Backend setup

Requires [uv](https://docs.astral.sh/uv/) and Docker.

```bash
docker compose up -d db

cd backend
cp .env.example .env
uv sync
uv run python manage.py migrate
uv run python manage.py runserver
```

API root: `http://localhost:8000/api/`

### Auth endpoints

| Method | Path                       | Description                  |
|--------|----------------------------|------------------------------|
| POST   | `/api/auth/register/`      | Create account               |
| POST   | `/api/auth/login/`         | Obtain access + refresh JWT  |
| POST   | `/api/auth/token/refresh/` | Refresh access token         |
| POST   | `/api/auth/token/verify/`  | Verify a token               |
| GET    | `/api/auth/me/`            | Current user profile         |
| PATCH  | `/api/auth/me/`            | Update profile               |

Access tokens live 15 minutes, refresh tokens 7 days.
