# Demo deployment guide

Free-tier stack: **MongoDB Atlas M0** (database) + **Render** (API) + **Vercel** (frontend).

## 1. MongoDB Atlas (database)

1. Create a free cluster at https://cloud.mongodb.com (M0, any region).
2. Database Access → create a user with password.
3. Network Access → allow `0.0.0.0/0` (Render free tier has no static IP).
4. Copy the connection string:
   `mongodb+srv://<user>:<password>@<cluster>.mongodb.net`

## 2. Render (API)

1. https://dashboard.render.com → New → **Blueprint** → connect the
   `multichannel-helpdesk` GitHub repo. Render reads `render.yaml` automatically.
2. Fill the two prompted variables:
   - `MONGODB_URI` — the Atlas connection string
   - `CORS_ORIGINS` — your future Vercel URL (can be updated after step 3)
3. Deploy. Health check: `https://<service>.onrender.com/health`
4. Seed the demo data:
   ```bash
   curl -X POST https://<service>.onrender.com/api/demo/seed
   ```

## 3. Vercel (frontend)

1. https://vercel.com/new → import the GitHub repo.
2. Root Directory: `frontend` (framework auto-detected: Next.js).
3. Environment variable:
   - `NEXT_PUBLIC_API_URL` = `https://<service>.onrender.com`
4. Deploy, then update `CORS_ORIGINS` on Render with the final Vercel URL.

## 4. Smoke test

- Open the Vercel URL → login with `admin@demo.com` / `demo123`
- Dashboard shows seeded tickets; bot console answers `/chamados abertos`
- `POST /api/demo/simulate-whatsapp-message` creates a ticket

> Note: Render free tier sleeps after inactivity — the first request may take ~40s.
