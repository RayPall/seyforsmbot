# ── callback_api.py ─────────────────────────────────────────────────────────────
"""
Malé FastAPI, které přijímá POST z Make na /callback
a uloží výsledek do stejné SQLite DB, kterou čte Streamlit.
"""
import sqlite3, datetime
from fastapi import FastAPI, Request, HTTPException

CALLBACK_DB = "posts.db"

app = FastAPI(title="LinkedIn bot – callback API")

@app.post("/callback")
async def make_callback(req: Request):
    try:
        data = await req.json()
        cid   = data["correlation_id"]   # stejné ID, jaké jsme poslali do Make
        email = data.get("email", "")
        post  = data["post"]             # vygenerovaný obsah
    except Exception:
        raise HTTPException(400, "Bad JSON payload")

    con = sqlite3.connect(CALLBACK_DB)
    cur = con.cursor()
    cur.execute("""UPDATE posts
                   SET content=?, received_at=?
                   WHERE correlation_id=?""",
                (post, datetime.datetime.utcnow().isoformat(), cid))
    con.commit()
    return {"status": "stored"}
