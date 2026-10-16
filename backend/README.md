# Backend deployment and privacy

## Render deployment

The existing Render API is `https://escape-game-tknl.onrender.com`. Keep the
repository root as the Render service root so both the backend package and
`data/processed/` assets are available. Configure the existing Render Web
Service with:

- Build command: `pip install -r backend/requirements.txt`
- Start command: `uvicorn backend.api.app:app --host 0.0.0.0 --port $PORT`
- Health check path: `/health`
- `APP_ENV=production`
- `CORS_ORIGINS=https://playescape.vercel.app`
- `GOOGLE_CLIENT_ID=<your Google OAuth web client ID>`

Render's free filesystem is ephemeral. Without `ESCAPE_DATABASE_PATH`, the
database is stored under `/tmp/escape.sqlite3` so the free service can start;
game history and accounts can be lost when Render restarts or redeploys it.
For durable data, attach a persistent disk and set
`ESCAPE_DATABASE_PATH=/var/data/escape.sqlite3`; a persistent disk requires a
paid Render web-service plan. Do not sync a Blueprint that creates another
service or disk unless you intend to replace the existing service.

The repository-root `.python-version` pins the runtime to Python 3.12.11.
SQLite is suitable for this single-instance deployment. Render disks are
available to one instance only; for multiple instances, move to a shared
database such as PostgreSQL. Back up the disk and verify restoring a backup
before launch.

## Vercel deployment

Keep the existing Vercel project root directory set to `frontend`, with build
command `npm run build` and output directory `dist`. Set this Production
environment variable in Vercel, then redeploy because Vite embeds it at build
time:

- `VITE_GOOGLE_CLIENT_ID=<the same public Google OAuth web client ID>`

The production API path is fixed to `/api` and does not depend on an old
`VITE_API_URL` value left in Vercel. The expected OAuth variable is listed in
`frontend/.env.production.example`.
The committed `frontend/vercel.json` proxies `/api/*` through the Vercel site
to Render. This keeps session cookies first-party in the browser; Render's
`SameSite` setting can remain `Lax` instead of relying on third-party cookies.

## Database and game sessions

Development defaults to `backend/escape.sqlite3`. In production, a configured
`ESCAPE_DATABASE_PATH` must be absolute. Render's free filesystem uses an
ephemeral database by default.
The browser receives an anonymous session cookie, and completed games are
tracked for that browser. Signing in links guest history to a Google account so
stats can be recovered on another device. Account identity uses Google's
stable `sub` claim, not email address. Passwords are never collected or stored.

The backend verifies Google ID token signature, audience, issuer, and
expiration before creating a server session. The session cookie is `HttpOnly`;
only its hash is stored in SQLite. Guest session credentials expire after one
year; signed-in sessions expire after 30 days. Expired guest game records are
removed during subsequent API requests. Deleting an account removes its
profile, sessions, games, and results from the application database.

## Privacy notice

The published notice is at `/privacy.html` and linked in the game footer. The
support/privacy contact address is configured in the notice.
