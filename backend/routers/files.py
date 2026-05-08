"""
Router de Files — HORUS Universal Fase 7
Sube archivos, extrae texto y lo pasa como contexto a los agentes.
Soporta: PDF, DOCX, TXT, MD, imágenes (JPG/PNG)
"""
import io
import base64
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/files", tags=["files"])

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
SUPPORTED_TYPES = {
    "application/pdf": "pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
    "text/plain": "txt",
    "text/markdown": "txt",
    "image/jpeg": "image",
    "image/jpg": "image",
    "image/png": "image",
    "image/webp": "image",
}


@router.post("/extract")
async def extract_file(file: UploadFile = File(...)):
    """
    Recibe un archivo y extrae su contenido como texto.
    Devuelve: { filename, type, text, size, truncated }
    """
    content_type = file.content_type or ""
    file_type = SUPPORTED_TYPES.get(content_type)

    # Detectar por extensión si content_type falla
    if not file_type and file.filename:
        ext = file.filename.rsplit(".", 1)[-1].lower()
        ext_map = {"pdf": "pdf", "docx": "docx", "txt": "txt", "md": "txt",
                   "jpg": "image", "jpeg": "image", "png": "image", "webp": "image"}
        file_type = ext_map.get(ext)

    if not file_type:
        raise HTTPException(
            status_code=415,
            detail=f"Tipo de archivo no soportado: {content_type}. Usa PDF, DOCX, TXT o imágenes."
        )

    data = await file.read()
    if len(data) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="Archivo muy grande (máx 10 MB).")

    try:
        if file_type == "pdf":
            text = _extract_pdf(data)
        elif file_type == "docx":
            text = _extract_docx(data)
        elif file_type == "txt":
            text = data.decode("utf-8", errors="replace")
        elif file_type == "image":
            text = _encode_image(data, content_type)
        else:
            text = ""

        # Limitar texto a 8000 caracteres
        truncated = len(text) > 8000
        if truncated:
            text = text[:8000] + "\n\n[...documento truncado a 8000 caracteres...]"

        return {
            "filename": file.filename,
            "type": file_type,
            "text": text,
            "size": len(data),
            "truncated": truncated,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[Files] Error extrayendo {file.filename}: {e}")
        raise HTTPException(status_code=500, detail=f"Error procesando archivo: {str(e)}")


def _extract_pdf(data: bytes) -> str:
    """Extrae texto de un PDF usando PyPDF2."""
    try:
        import PyPDF2
        reader = PyPDF2.PdfReader(io.BytesIO(data))
        pages = []
        for i, page in enumerate(reader.pages):
            if i >= 50:  # máx 50 páginas
                pages.append("[...PDF truncado a 50 páginas...]")
                break
            text = page.extract_text() or ""
            if text.strip():
                pages.append(f"[Página {i+1}]\n{text}")
        return "\n\n".join(pages) if pages else "No se pudo extraer texto del PDF."
    except ImportError:
        raise HTTPException(status_code=503, detail="PyPDF2 no disponible.")


def _extract_docx(data: bytes) -> str:
    """Extrae texto de un archivo DOCX."""
    try:
        from docx import Document
        doc = Document(io.BytesIO(data))
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        return "\n\n".join(paragraphs) if paragraphs else "Documento vacío."
    except ImportError:
        raise HTTPException(status_code=503, detail="python-docx no disponible.")


def _encode_image(data: bytes, content_type: str) -> str:
    """Codifica imagen en base64 para enviarla al modelo de visión."""
    b64 = base64.b64encode(data).decode("utf-8")
    mime = content_type if content_type in ("image/jpeg", "image/png", "image/webp") else "image/jpeg"
    return f"[IMAGE_BASE64:{mime}]{b64}[/IMAGE_BASE64]"
