from pathlib import Path

path = Path(r"C:\Users\ecaam\Desktop\horus-universal\frontend\src\components\MessageBubble.tsx")

content = path.read_text(encoding="utf-8")

broken = '<VisualMessageRenderer content=<VisualMessageRenderer content={content} imageUrl={(message as any)?.image_url} visual={(message as any)?.visual} /> />'

fixed = '''
<VisualMessageRenderer
  content={content}
  imageUrl={(message as any)?.image_url}
  visual={(message as any)?.visual}
/>
'''

content = content.replace(broken, fixed)

path.write_text(content, encoding="utf-8")

print("Fixed nested VisualMessageRenderer JSX.")
