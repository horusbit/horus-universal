
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
