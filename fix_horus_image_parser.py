from pathlib import Path

path = Path(r"C:\Users\ecaam\Desktop\horus-universal\frontend\src\components\VisualMessageRenderer.tsx")

content = path.read_text(encoding="utf-8")

OLD = r'''
  const horusRegex = /\[HORUS_IMAGE\][\s\S]*?prompt:\s*([^\n\r]+)/gi;
  while ((match = horusRegex.exec(text)) !== null) {
    const prompt = match![1].trim();
    const url = buildPollinationsUrl(prompt);
    if (!images.find((img) => img.url === url)) {
      images.push({ url, label: "Imagen HORUS" });
    }
  }
'''

NEW = r'''
  const horusRegex = /\[HORUS_IMAGE\]\s*prompt:\s*(.*?)\s*model:/gis;

  while ((match = horusRegex.exec(text)) !== null) {

    const prompt = match![1]?.trim();

    if (!prompt) continue;

    const url = buildPollinationsUrl(prompt);

    if (!images.find((img) => img.url === url)) {
      images.push({
        url,
        label: "Imagen HORUS"
      });
    }
  }
'''

if OLD in content:
    content = content.replace(OLD, NEW)

# Better cleanup
content = content.replace(
    '.replace(/\\[HORUS_IMAGE\\][\\s\\S]*?prompt:\\s*([^\\n\\r]+)/gi, "")',
    '.replace(/\\[HORUS_IMAGE\\][\\s\\S]*?\\[HORUS_IMAGE\\]/gis, "")'
)

path.write_text(content, encoding="utf-8")

print("HORUS image block parser fixed.")
