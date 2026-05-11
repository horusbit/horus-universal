from pathlib import Path

main_path = Path(r"C:\Users\ecaam\Desktop\horus-universal\backend\main.py")

content = main_path.read_text(encoding="utf-8")

# Remove visual router imports safely
content = content.replace(
    "from routers.visual import router as visual_router\n",
    ""
)

content = content.replace(
    "\napp.include_router(visual_router)",
    ""
)

content = content.replace(
    "app.include_router(visual_router)\n",
    ""
)

main_path.write_text(content, encoding="utf-8")

print("Visual router temporarily disabled.")
