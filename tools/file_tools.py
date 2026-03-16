import base64
import os
from pathlib import Path
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from config import settings

gemini = ChatGoogleGenerativeAI(model=settings.GEMINI_MODEL, api_key=settings.GOOGLE_API_KEY)

@tool 
def read_image(image_path: str) -> str:

    """Read an image from the given path and return its content.
    
    Args:
        image_path (str): The path to the image.

    Returns:
        str: The description of the image.

    """
    image_path = Path(image_path)
    if not image_path.exists():
        raise ValueError(f"Image not found at {image_path}")
    with open(image_path, "rb") as f:
        image_bytes = base64.b64encode(f.read()).decode("utf-8")
    
    try:
        if "jpeg" in image_path.suffix:
            msg = HumanMessage(
    content=[
        {"type": "text", "text": "Describe the local image."},
        {
            "type": "image",
            "base64": image_bytes,
            "mime_type": "image/jpeg",
        },
    ]
)
        elif "png" in image_path.suffix:
            msg = HumanMessage(
    content=[
        {"type": "text", "text": "Describe the local image."},
        {
            "type": "image",
            "base64": image_bytes,
            "mime_type": "image/png",
        },
    ]
)
        elif "jpg" in image_path.suffix:
            msg = HumanMessage(
    content=[
        {"type": "text", "text": "Describe the local image."},
        {
            "type": "image",
            "base64": image_bytes,
            "mime_type": "image/jpg",
        },
    ]
)
        else:
            raise ValueError(f"Unsupported image format: {image_path.suffix}")
    except Exception as e:
        raise ValueError(f"Error reading image: {e}")
    resp = gemini.invoke([msg])
    return resp.content


@tool
def inspect_a_file(path: str):
    """
    Reads and returns the content of the file at the given path as a string.
    Handles file not found and decoding errors gracefully.

    Args:
        path (str): The path to the file to inspect.

    Returns:
        str: The content of the file, or an error message if the file cannot be read.
    """
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        return content
    except FileNotFoundError:
        return f"Error: File not found: {path}"
    except UnicodeDecodeError:
        return f"Error: Could not decode file (not UTF-8): {path}"
    except Exception as e:
        return f"Error reading file {path}: {e}"

@tool 
def write_file(code:str,file_path: str) -> str:
    """
    Writes the given code to the specified file path.
    Args:
        code (str): The code to write to the file.
        file_path (str): The path to the file to write the code to.
    Returns:
        str: A message indicating that the file was written successfully.
    """
    with open(file_path, "w") as f:
        f.write(code)
    return f"File '{file_path}' written successfully."
