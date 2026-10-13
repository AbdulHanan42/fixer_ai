# Fixer AI backend

## Admin access

The admin dashboard is available at `/admin/dashboard`. Sign in with an account whose role is `admin`; successful login redirects to the admin dashboard automatically. The admin page loads pending mechanic profiles from `GET /api/v1/admin/mechanics/pending` and approves them through `PATCH /api/v1/admin/mechanics/{mechanic_id}/verify`.

To grant admin access to an existing customer account, run this command from the `backend` directory:

```powershell
.\.venv\Scripts\python.exe -m scripts.promote_admin customer@example.com
```

Register the account first using the normal customer registration flow. Then sign out and sign back in so the browser refreshes the account role. Public registration cannot create admin accounts.

For local development only, `python -m scripts.seed` creates the sample admin `admin@fixer.ai` with password `AdminPassword123!`. Do not use that sample password in a deployed environment.

## AI diagnosis

Set `GEMINI_API_KEY` in `backend/.env` to enable image diagnosis. The Gemini API uses `gemini-3.8-flash` by default; override it with `GEMINI_VISION_MODEL` if needed. Apply database changes with `alembic upgrade head` from the `backend` directory.

Authenticated customers can submit a multipart request to `POST /api/diagnosis/analyze` with `image` and `description` fields. The response includes possible issues, urgency, the exact matching service category, and verified mechanics offering that category. Distances are `null` because the analyze request does not include customer coordinates.
