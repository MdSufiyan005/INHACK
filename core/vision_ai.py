import os
import base64
from groq import Groq
from core.config import settings


def extract_text(image_path: str, intent: str) -> str:
    # Read image and encode as base64
    with open(image_path, "rb") as img_file:
        img_bytes = img_file.read()
        img_b64 = base64.b64encode(img_bytes).decode("utf-8")
    IMAGE_DATA_URL = f"data:image/jpeg;base64,{img_b64}"

    client = Groq(api_key=settings.GROQ_API_KEY)

    client = Groq(api_key=settings.GROQ_API_KEY)
    completion = client.chat.completions.create(
        model="meta-llama/llama-4-maverick-17b-128e-instruct",
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": (
                            f"The vendor selected '{intent}'. "
                            "Extract *all* line‑items from the receipt and output *only* one valid JSON document "
                            "with this exact structure (no markdown fences!):\n\n"
                            "{\n"
                            f"  \"intent\": \"{intent}\",\n"
                            "  \"items\": [\n"
                            "    {\n"
                            "      \"item_name\": \"string\",\n"
                            "      \"quantity\": int,\n"
                            "      \"price\": float,\n"
                            "      \"payment_method\": \"online|Cash\"\n"
                            "    },\n"
                            "    …\n"
                            "  ]\n"
                            "}\n"
                        )
                    },
                    {
                        "type": "image_url",
                        "image_url": {"url": IMAGE_DATA_URL}
                    }
                ]
            }
        ],
        temperature=0.0,
        max_completion_tokens=512,
        top_p=1,
        stream=False,
    )


    # Get the JSON string from the model's response
    content = completion.choices[0].message.content
    
    return content