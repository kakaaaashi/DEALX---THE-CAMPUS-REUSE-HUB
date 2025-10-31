DealX - Final package (ready-to-deploy)

What to do next:
1. Ensure these environment variables are set on Render:
   - CLOUDINARY_URL = cloudinary://<api_key>:<api_secret>@dj1ldcjda
   - SECRET_KEY = dealxsecretkey
2. Start command on Render: gunicorn app:app
3. Build command: pip install -r requirements.txt
4. After deploy, open the provided Render URL. Upload an item to verify images stored in Cloudinary.

Notes:
- SQLite DB (items.db) is created automatically on first request.
- If you previously had data in another items.db, copy it into the repo root before deploying.
