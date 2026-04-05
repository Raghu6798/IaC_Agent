from langchain_core.tools import tool
from mistralai.client import Mistral
from concurrent.futures import ThreadPoolExecutor
import asyncio
import base64
import threading
from functools import lru_cache
from config.settings import settings
from dotenv import load_dotenv

load_dotenv()
# Thread pool for blocking I/O operations
io_executor = ThreadPoolExecutor(max_workers=4)

# Thread-safe pixtral client singleton
_pixtral_lock = threading.Lock()
pixtral = None

@lru_cache(maxsize=1)
def _get_pixtral():
    global pixtral
    if pixtral is None:
        with _pixtral_lock:
            # Double check inside the lock
            if pixtral is None:
                pixtral = Mistral(
                    api_key=os.getenv("MISTRAL_API_KEY"),
                )
    return pixtral

@tool 
async def encode_image(image_path: str) -> str:
    """Encode an image to base64."""
    loop = asyncio.get_running_loop()
    
    def _read_and_encode():
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")
            
    # Run blocking file read in ThreadPoolExecutor
    image_strings = await loop.run_in_executor(io_executor, _read_and_encode)

    vision_language_input =  [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "What's in this image?"
                },
                {
                    "type": "image_url",
                    "image_url": f"data:image/jpeg;base64,{image_strings}"
                }
            ]
        }
    ]
    
    def _call_api():
        client = _get_pixtral()
        return client.chat.completions.create(
            model="mistral-small-latest",
            messages=vision_language_input,
        )
        
    # Run blocking API call in ThreadPoolExecutor
    vision_resp = await loop.run_in_executor(io_executor, _call_api)
    return vision_resp

if __name__ == "__main__":
    print(asyncio.run(encode_image.ainvoke("assets/Architecture_diagram.jpeg")))