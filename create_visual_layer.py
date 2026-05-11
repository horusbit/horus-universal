from pathlib import Path

root = Path(r"C:\Users\ecaam\Desktop\horus-universal")

(root / "backend/services").mkdir(parents=True, exist_ok=True)
(root / "backend/routers").mkdir(parents=True, exist_ok=True)

visual_service = root / "backend/services/visual_service.py"

visual_service.write_text("""
from urllib.parse import quote

def generate_image_url(prompt: str):
    encoded = quote(prompt)
    return f"https://image.pollinations.ai/prompt/{encoded}?width=1024&height=1024&enhance=true&nologo=true"

def visual_response(prompt: str):
    image_url = generate_image_url(prompt)

    return f'''Te prepare una propuesta visual inicial:

![Vista previa generada]({image_url})

Prompt utilizado:
{prompt}
'''
""", encoding="utf-8")

router = root / "backend/routers/visual.py"

router.write_text("""
from fastapi import APIRouter
from pydantic import BaseModel
from backend.services.visual_service import generate_image_url, visual_response

router = APIRouter(prefix="/api/v1/visual", tags=["visual"])

class VisualRequest(BaseModel):
    prompt: str

@router.get("/health")
def health():
    return {"status": "healthy", "service": "HORUS Visual Layer"}

@router.post("/generate")
def generate(req: VisualRequest):
    return {
        "success": True,
        "image_url": generate_image_url(req.prompt),
        "response": visual_response(req.prompt)
    }
""", encoding="utf-8")

main_path = root / "backend/main.py"
main = main_path.read_text(encoding="utf-8")

if "from backend.routers import visual" not in main:
    main = "from backend.routers import visual\n" + main

if "app.include_router(visual.router)" not in main:
    main += "\napp.include_router(visual.router)\n"

main_path.write_text(main, encoding="utf-8")

print("HORUS visual layer installed.")
