from pathlib import Path

path = Path(r"C:\Users\ecaam\Desktop\horus-universal\frontend\src\components\VisualMessageRenderer.tsx")

content = path.read_text(encoding="utf-8")

inject = r'''

function looksLikeVisualPrompt(text: string) {
  if (!text) return false;

  const t = text.toLowerCase();

  const keywords = [
    "logo",
    "branding",
    "mockup",
    "render",
    "vector style",
    "high resolution",
    "corporate branding",
    "flat vector",
    "centered composition",
    "professional minimalist",
    "8k quality",
    "modern sans-serif",
    "white background"
  ];

  const matches = keywords.filter(k => t.includes(k)).length;

  return matches >= 3;
}
'''

if "looksLikeVisualPrompt" not in content:
    content = inject + "\n" + content

target = '''
  const images = extractImages(content || "");
  const text = cleanText(content || "");
'''

replacement = r'''
  let images = extractImages(content || "");
  let text = cleanText(content || "");

  // AUTO-CONVERT RAW VISUAL PROMPTS INTO IMAGES
  if (images.length === 0 && looksLikeVisualPrompt(text)) {

    const cleanedPrompt = text
      .replace("↗ abrir", "")
      .trim();

    const url = buildPollinationsUrl(cleanedPrompt);

    images = [
      {
        url,
        label: "Imagen generada"
      }
    ];
  }
'''

if target in content:
    content = content.replace(target, replacement)

path.write_text(content, encoding="utf-8")

print("Auto visual prompt detection installed.")
