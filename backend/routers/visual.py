
from fastapi import APIRouter
from pydantic import BaseModel
from services.visual_service import generate_image_url, visual_response

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
