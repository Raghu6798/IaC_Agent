import base64
import os
from pathlib import Path
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from config.settings import settings
from dotenv import load_dotenv

from utils.ui import show_info, show_error,show_success

load_dotenv()
gemini = ChatGoogleGenerativeAI(model="gemini-3.1-pro-preview", api_key=os.getenv("GOOGLE_API_KEY"))

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
def refactoring_code(refactored_code: str, error_file_path: str):
    """
    Overwrite the specified file with the provided refactored code.

    Args:
        refactored_code (str): The new code to write into the file.
        error_file_path (str): The path to the file to be overwritten.

    Returns:
        str: A success message if the file was written, or an error message if writing failed.
    """
    try:
        show_info(f"Writing refactored code to {error_file_path}")
        with open(error_file_path, "w", encoding="utf-8") as file:
            file.write(refactored_code)
        show_info(f"Successfully wrote refactored code to {error_file_path}")
        return f"Successfully wrote refactored code to {error_file_path}"
    except Exception as e:
        show_error(f"Error writing to {error_file_path}: {e}")
        return f"Error writing to {error_file_path}: {e}"

@tool 
def write_code(code: str, file_path: str):
    """
    Writes the given code to the specified file path.

    Args:
        code (str): The code to write to the file.
        file_path (str): The path to the file to write the code to.

    Returns:
        str: A success message if the file was written, or an error message if writing failed.
    """
    try:
        show_info(f"Writing code to {file_path}")
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as file:
            file.write(code)
        show_info(f"Successfully wrote code to {file_path}")
        return f"Successfully wrote code to {file_path}"
    except Exception as e:
        show_error(f"Error writing to {file_path}: {e}")
        return f"Error writing to {file_path}: {e}"

if __name__ == "__main__":
    print(read_image("assets/Architecture_diagram.jpeg"))