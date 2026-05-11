from pathlib import Path
import re

path = Path(r"C:\Users\ecaam\Desktop\horus-universal\frontend\src\components\MessageBubble.tsx")

content = path.read_text(encoding="utf-8")

pattern = r'''
<VisualMessageRenderer
  content=\{content\}
  imageUrl=\{\(message as any\)\?\.image_url\}
  visual=\{\(message as any\)\?\.visual\}
/>
'''

replacement = r'''
<VisualMessageRenderer
  content={content}
/>
'''

content = re.sub(pattern, replacement, content, flags=re.MULTILINE)

path.write_text(content, encoding="utf-8")

print("Removed invalid message references from MessageBubble.")
