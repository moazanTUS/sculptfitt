import os
import mimetypes
import json
from dataclasses import dataclass
from typing import Dict, Optional

from google import genai
from google.genai import types

SUPPORTED_MIME = {"image/jpeg", "image/png", "image/webp", "image/heic", "image/heif"}

BODYTYPE_JSON_PROMPT = """
You are an expert fitness assessment specialist. Analyze the provided image to determine body type and fitness focus areas.

BODY TYPE IDENTIFICATION (somatotype assessment):
- ECTOMORPH: Naturally lean, small bone structure, long limbs, narrow shoulders, minimal muscle definition, fast metabolism. Best for strength building and hypertrophy work.
- MESOMORPH: Athletic build, broad shoulders, naturally muscular appearance, moderate to good muscle definition, gains muscle easily. Best for hypertrophy and strength training.
- ENDOMORPH: Rounder physique, larger bone structure, naturally carries more body fat, gains muscle but also gains fat easily. Best for fat loss with muscle preservation.

BODY PART FOCUS SELECTION:
Based on what you observe in the image, choose 3 body parts that would most benefit this person's fitness goals:
- If you see narrow shoulders or small frame: prioritize shoulders, chest, and back
- If you see a strong athletic build: focus on maintaining/building chest, shoulders, and legs
- If you see someone wanting to improve definition: prioritize core, legs, and whichever area looks less developed
- Always include legs unless the person appears to have well-developed lower body already
- Core should be included for most people as it's foundational
- Focus on the areas that look like they need the most work based on muscle development and balance

ASSESSMENT RULES:
- Do NOT guess age, health conditions, medical history, or body fat percentage
- Focus ONLY on visible musculature, bone structure, and proportions
- Be practical: choose body parts that would realistically help THIS person improve their physique
- Avoid "mixed" unless you truly cannot determine - defaulting to mesomorph is acceptable

Return ONLY valid JSON (no markdown, no extra text, no backticks).

JSON schema:
{
  "body_type": "ectomorph|mesomorph|endomorph",
  "focus_areas": ["body_part_1", "body_part_2", "body_part_3"],
  "rationale": "Brief explanation of why you selected this body type and these focus areas"
}
""".strip()


@dataclass
class UserImageAnalyzer:
    image_path: str
    model: str = "gemini-2.5-flash"
    api_key: Optional[str] = None  # can hardcode for now if you want

    def analyze(self) -> Dict:
        if not os.path.isfile(self.image_path):
            raise FileNotFoundError(f"Image not found: {self.image_path}")

        mime_type, _ = mimetypes.guess_type(self.image_path)
        if mime_type not in SUPPORTED_MIME:
            raise ValueError(f"Unsupported image type: {mime_type}")

        with open(self.image_path, "rb") as f:
            image_bytes = f.read()

        client = genai.Client(api_key=self.api_key) if self.api_key else genai.Client()

        image_part = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)

        resp = client.models.generate_content(
            model=self.model,
            contents=[image_part, BODYTYPE_JSON_PROMPT],
            config={"response_mime_type": "application/json"},
        )

        text = (resp.text or "").strip()
        print(f"[Gemini] Raw response:\n{text}\n")

        try:
            data = json.loads(text)
            print(f"[Gemini] Parsed JSON: {data}\n")
        except json.JSONDecodeError:
            raise ValueError(f"Gemini returned non-JSON:\n{text}")

        return {
            "type": "user_image",
            "input_image": self.image_path,
            "mime_type": mime_type,
            "model": self.model,
            "result": data,
        }
