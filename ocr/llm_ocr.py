"""
OCR using GPT-4o vision via OpenRouter.
Converts each PDF page to an image and sends it to the LLM for text extraction.
"""

import os
import base64
from pathlib import Path
from openai import OpenAI
from pdf2image import convert_from_path
from dotenv import load_dotenv

load_dotenv()

PDF_PATH = Path("dps/samples/DPS - UCM .pdf")
API_KEY  = os.environ["OPENROUTER_API_KEY"]
MODEL    = "openai/gpt-4o"

client = OpenAI(
    api_key=API_KEY,
    base_url="https://openrouter.ai/api/v1",
)


def image_to_base64(image) -> str:
    from io import BytesIO
    buf = BytesIO()
    image.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("utf-8")


def ocr_page(image, page_num: int) -> str:
    print(f"  Extracting page {page_num}...")
    b64 = image_to_base64(image)

    response = client.chat.completions.create(
        model=MODEL,
        messages=[{
            "role": "user",
            "content": [
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/png;base64,{b64}"}
                },
                {
                    "type": "text",
                    "text": (
                        "Extract all text from this document page. "
                        "Preserve tables as markdown. "
                        "Preserve headings, bullet points, and structure. "
                        "Return only the extracted content, no commentary."
                    )
                }
            ]
        }],
        temperature=0.0,
    )
    return response.choices[0].message.content


def run():
    print(f"Loading PDF: {PDF_PATH}\n")
    pages = convert_from_path(str(PDF_PATH), dpi=200)
    print(f"Found {len(pages)} page(s). Sending to GPT-4o via OpenRouter...\n")

    for i, page in enumerate(pages, 1):
        text = ocr_page(page, i)
        print(f"{'=' * 60}")
        print(f"PAGE {i}")
        print(f"{'=' * 60}")
        print(text)
        print()


if __name__ == "__main__":
    run()
