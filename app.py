import os
import httpx
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import Response

app = FastAPI()

UPSTREAM_BASE = os.getenv("UPSTREAM_BASE", "").rstrip("/")

ALLOWED_PATHS = {
    "/public/latest",
    "/public/search",
    "/public/team",
    "/public/match",
}

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.api_route(
    "/public/{path:path}",
    methods=["GET"]
)
async def proxy(path: str, request: Request):
    full_path = f"/public/{path}"

    if full_path not in ALLOWED_PATHS:
        raise HTTPException(status_code=404, detail="Not found")

    if not UPSTREAM_BASE:
        raise HTTPException(status_code=500, detail="UPSTREAM_BASE not configured")

    upstream_url = UPSTREAM_BASE + full_path

    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.get(
                upstream_url,
                params=dict(request.query_params),
                headers={"Accept": "application/json"},
            )

        return Response(
            content=resp.content,
            status_code=resp.status_code,
            media_type="application/json",
            headers={"Cache-Control": "no-store"},
        )

    except Exception:
        raise HTTPException(status_code=502, detail="Upstream unavailable")
