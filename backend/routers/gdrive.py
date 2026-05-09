"""
Router de Google Drive — HORUS Universal
OAuth2 flow + leer/listar archivos para inyectarlos como contexto.
"""
import logging
import urllib.parse
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse, JSONResponse
from pydantic import BaseModel
from config import settings
from auth.supabase_auth import get_optional_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/gdrive", tags=["gdrive"])

SCOPES = "https://www.googleapis.com/auth/drive.readonly"
REDIRECT_PATH = "/api/v1/gdrive/callback"


def _get_redirect_uri():
    base = getattr(settings, "APP_BASE_URL", "https://horus-backend.onrender.com")
    return base + REDIRECT_PATH


@router.get("/auth")
async def gdrive_auth(user=Depends(get_optional_user)):
    """Inicia el flujo OAuth2 con Google Drive."""
    client_id = getattr(settings, "GOOGLE_CLIENT_ID", "")
    if not client_id:
        raise HTTPException(400, "GOOGLE_CLIENT_ID no configurado en el servidor.")

    params = {
        "client_id": client_id,
        "redirect_uri": _get_redirect_uri(),
        "response_type": "code",
        "scope": SCOPES,
        "access_type": "offline",
        "prompt": "consent",
        "state": getattr(user, "id", "anon") if user else "anon",
    }
    url = "https://accounts.google.com/o/oauth2/v2/auth?" + urllib.parse.urlencode(params)
    return RedirectResponse(url)


@router.get("/callback")
async def gdrive_callback(code: str = Query(...), state: str = Query("")):
    """Recibe el código OAuth2 y lo intercambia por tokens."""
    import aiohttp
    client_id = getattr(settings, "GOOGLE_CLIENT_ID", "")
    client_secret = getattr(settings, "GOOGLE_CLIENT_SECRET", "")
    if not client_id or not client_secret:
        raise HTTPException(400, "Google OAuth no configurado.")

    async with aiohttp.ClientSession() as session:
        resp = await session.post("https://oauth2.googleapis.com/token", data={
            "code": code,
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": _get_redirect_uri(),
            "grant_type": "authorization_code",
        })
        tokens = await resp.json()

    if "error" in tokens:
        raise HTTPException(400, f"Error OAuth: {tokens['error']}")

    access_token = tokens.get("access_token", "")
    # Redirect back to frontend with token
    frontend_url = getattr(settings, "FRONTEND_URL", "https://horus-universal.vercel.app")
    return RedirectResponse(f"{frontend_url}/chat?gdrive_token={access_token}")


@router.get("/files")
async def list_drive_files(
    token: str = Query(...),
    query: str = Query("", description="Filtro de búsqueda en Drive"),
):
    """Lista archivos de Google Drive del usuario."""
    import aiohttp
    q = query or "mimeType != 'application/vnd.google-apps.folder'"
    params = {
        "q": q,
        "pageSize": 20,
        "fields": "files(id,name,mimeType,size,modifiedTime,webViewLink)",
        "orderBy": "modifiedTime desc",
    }
    async with aiohttp.ClientSession() as session:
        resp = await session.get(
            "https://www.googleapis.com/drive/v3/files",
            params=params,
            headers={"Authorization": f"Bearer {token}"},
        )
        data = await resp.json()

    if "error" in data:
        raise HTTPException(401, f"Error de Drive: {data['error'].get('message', 'token inválido')}")

    return {"files": data.get("files", [])}


@router.get("/read")
async def read_drive_file(
    token: str = Query(...),
    file_id: str = Query(...),
    file_name: str = Query("archivo"),
    mime_type: str = Query(""),
):
    """Lee el contenido de un archivo de Google Drive y lo retorna como contexto."""
    import aiohttp
    import io

    async with aiohttp.ClientSession() as session:
        # Google Docs → exportar como texto plano
        if "google-apps.document" in mime_type:
            url = f"https://www.googleapis.com/drive/v3/files/{file_id}/export"
            params = {"mimeType": "text/plain"}
        elif "google-apps.spreadsheet" in mime_type:
            url = f"https://www.googleapis.com/drive/v3/files/{file_id}/export"
            params = {"mimeType": "text/csv"}
        elif "google-apps.presentation" in mime_type:
            url = f"https://www.googleapis.com/drive/v3/files/{file_id}/export"
            params = {"mimeType": "text/plain"}
        else:
            # Archivo binario → descargar
            url = f"https://www.googleapis.com/drive/v3/files/{file_id}?alt=media"
            params = {}

        resp = await session.get(
            url, params=params,
            headers={"Authorization": f"Bearer {token}"},
        )
        if resp.status != 200:
            raise HTTPException(resp.status, "No se pudo leer el archivo de Drive.")
        content_bytes = await resp.read()

    # Convertir a texto
    MAX_CHARS = 8000
    try:
        text = content_bytes.decode("utf-8", errors="replace")
    except Exception:
        text = "(Archivo binario — no se puede leer como texto)"

    truncated = len(text) > MAX_CHARS
    text = text[:MAX_CHARS]

    trunc_note = " (truncado)" if truncated else ""
    context = (
        f"[📁 GOOGLE DRIVE: {file_name}{trunc_note}]\n"
        f"Contenido del archivo de Drive:\n\n{text}\n\n"
        f"[FIN DEL ARCHIVO — Responde basándote en este contenido]"
    )

    return {
        "file_id": file_id,
        "file_name": file_name,
        "chars": len(text),
        "truncated": truncated,
        "context": context,
    }
