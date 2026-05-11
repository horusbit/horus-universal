from pathlib import Path

root = Path(r"C:\Users\ecaam\Desktop\horus-universal")

main_path = root / "backend/main.py"
visual_path = root / "backend/routers/visual.py"

# Fix visual.py imports
visual = visual_path.read_text(encoding="utf-8")

visual = visual.replace(
    "from backend.services.visual_service import generate_image_url, visual_response",
    "from services.visual_service import generate_image_url, visual_response"
)

visual_path.write_text(visual, encoding="utf-8")

# Fix main.py to import visual router exactly like other routers
main = main_path.read_text(encoding="utf-8")

main = main.replace("from routers import visual\n", "")
main = main.replace("app.include_router(visual.router)", "")

if "from routers.visual import router as visual_router" not in main:
    main = main.replace(
        "from routers.images import router as images_router",
        "from routers.images import router as images_router\nfrom routers.visual import router as visual_router"
    )

if "app.include_router(visual_router)" not in main:
    main = main.replace(
        "app.include_router(images_router)",
        "app.include_router(images_router)\napp.include_router(visual_router)"
    )

main_path.write_text(main, encoding="utf-8")

print("Visual imports fixed.")
