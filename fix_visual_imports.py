from pathlib import Path

root = Path(r"C:\Users\ecaam\Desktop\horus-universal")

main_path = root / "backend/main.py"
visual_router_path = root / "backend/routers/visual.py"

# Fix main.py import
main = main_path.read_text(encoding="utf-8")
main = main.replace("from backend.routers import visual", "from routers import visual")
main_path.write_text(main, encoding="utf-8")

# Fix visual.py import
if visual_router_path.exists():
    visual = visual_router_path.read_text(encoding="utf-8")
    visual = visual.replace(
        "from backend.services.visual_service import generate_image_url, visual_response",
        "from services.visual_service import generate_image_url, visual_response"
    )
    visual_router_path.write_text(visual, encoding="utf-8")

print("Import paths fixed for Render backend startup.")
