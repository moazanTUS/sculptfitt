import os
import mimetypes
import json
import io
from dataclasses import dataclass
from typing import Dict, Optional

import google.genai as genai
from google import genai as genai_types

SUPPORTED_MIME = {"image/jpeg", "image/png", "image/webp", "image/heic", "image/heif"}

BODYTYPE_JSON_PROMPT = """
You are an expert fitness assessment specialist. Analyze the provided image to determine body type and focus areas for a personalized workout plan.

BODY TYPE IDENTIFICATION (somatotype assessment):
- ECTOMORPH: Naturally lean, small bone structure, long limbs, narrow shoulders, minimal muscle definition, fast metabolism
- MESOMORPH: Athletic build, broad shoulders, naturally muscular appearance, moderate to good muscle definition, gains muscle easily
- ENDOMORPH: Rounder physique, larger bone structure, naturally carries more body fat, gains muscle but also gains fat easily

PRIMARY FOCUS SELECTION:
Choose the 1 main body part that would most benefit this person based on what you observe:
- If narrow shoulders: shoulders
- If flat chest: chest
- If weak back: back
- If underdeveloped legs: legs
- If needs overall: chest (good foundation)

SECONDARY FOCUSES:
Choose 2 other body parts for balanced development:
- Back and shoulders
- Chest and arms
- Legs and core
- etc.

ASSESSMENT RULES:
- Focus ONLY on visible musculature, bone structure, and proportions
- Do NOT guess age, health conditions, or medical history
- Be practical: choose areas that look underdeveloped or would create best balance

Return ONLY valid JSON (no markdown, no backticks).

JSON schema:
{
  "body_type": "ectomorph|mesomorph|endomorph",
  "primary_focus": "chest|back|shoulders|legs",
  "secondary_focuses": ["body_part_1", "body_part_2"],
  "rationale": "Brief explanation based on visible muscle development"
}
""".strip()


def generate_workout_prompt(body_type: str, primary_focus: str, secondary_focuses: list, difficulty: str = "intermediate", days_per_week: int = 4) -> str:
    """Generate a prompt for Gemini to create a personalized workout plan"""
    
    # Define rep ranges and sets by difficulty
    if difficulty == "beginner":
        rep_range = "10-15 reps"
        sets = "3 sets"
    elif difficulty == "advanced":
        rep_range = "3-8 reps"
        sets = "4 sets"
    else:  # intermediate
        rep_range = "6-12 reps"
        sets = "3 sets"
    
    secondary_str = ", ".join(secondary_focuses)
    
    # Build day descriptions based on days_per_week
    day_descriptions = ""
    if days_per_week >= 1:
        day_descriptions += f"- Day 1: Focus on {primary_focus}\n"
    if days_per_week >= 2:
        day_descriptions += f"- Day 2: Focus on {secondary_focuses[0] if secondary_focuses else 'back'}\n"
    if days_per_week >= 3:
        day_descriptions += f"- Day 3: Focus on {secondary_focuses[1] if len(secondary_focuses) > 1 else 'shoulders'}\n"
    if days_per_week >= 4:
        day_descriptions += f"- Day 4: Full body or weak areas\n"
    if days_per_week >= 5:
        day_descriptions += f"- Day 5: Upper body focus\n"
    if days_per_week >= 6:
        day_descriptions += f"- Day 6: Lower body focus\n"
    if days_per_week >= 7:
        day_descriptions += f"- Day 7: Active recovery or light cardio\n"
    
    return f"""
You are an expert personal trainer. Create a detailed {days_per_week}-day workout split for a {body_type} individual.

PROFILE:
- Body Type: {body_type}
- Primary Focus: {primary_focus}
- Secondary Focuses: {secondary_str}
- Difficulty Level: {difficulty}
- Rep Range: {rep_range}
- Sets per Exercise: {sets}

REQUIREMENTS:
1. Create exactly {days_per_week} days of workouts
{day_descriptions}
For each day include:
- 4-5 exercises per day
- Exercise name
- Muscle group
- {rep_range}
- {sets}
- Rest time (60-90 seconds)
- Brief form tips

Return ONLY valid JSON (no markdown, no backticks).

JSON schema:
{{
  "days": [
    {{
      "day": 1,
      "focus": "string (primary body part)",
      "exercises": [
        {{
          "name": "Exercise Name",
          "muscle_group": "Primary muscle",
          "reps": "10-15",
          "sets": 3,
          "rest_seconds": 90,
          "form_tips": "Brief form cues"
        }}
      ]
    }}
  ],
  "days_per_week": {days_per_week},
  "notes": "General notes about the program"
}}
""".strip()


@dataclass
class UserImageAnalyzer:
    image_path: Optional[str] = None
    image_bytes: Optional[io.BytesIO] = None
    model: str = "gemini-2.5-flash"
    api_key: Optional[str] = None  # can hardcode for now if you want
    difficulty: str = "intermediate"
    days_per_week: int = 4

    def analyze(self) -> Dict:
        # Get image bytes from either file path or BytesIO object
        if self.image_bytes:
            # Process from memory (BytesIO)
            image_bytes = self.image_bytes.getvalue()
            mime_type = "image/jpeg"  # Default; Gemini is flexible
            input_source = "memory"
        elif self.image_path:
            # Process from file path (backward compatibility)
            if not os.path.isfile(self.image_path):
                raise FileNotFoundError(f"Image not found: {self.image_path}")

            mime_type, _ = mimetypes.guess_type(self.image_path)
            if mime_type not in SUPPORTED_MIME:
                raise ValueError(f"Unsupported image type: {mime_type}")

            with open(self.image_path, "rb") as f:
                image_bytes = f.read()
            input_source = self.image_path
        else:
            raise ValueError("Must provide either image_path or image_bytes")

        # Configure genai with API key
        if self.api_key:
            genai.configure(api_key=self.api_key)
        
        # Create model instance
        model = genai.GenerativeModel(self.model)
        
        # Create image part using Blob
        image_blob = genai.types.Blob(mime_type=mime_type, data=image_bytes)

        # Step 1: Analyze body type and focus - use GenerativeModel API
        model = genai.GenerativeModel(self.model)
        resp = model.generate_content(
            [image_blob, BODYTYPE_JSON_PROMPT],
            generation_config={"response_mime_type": "application/json"},
        )

        text = (resp.text or "").strip()
        print(f"[Gemini] Body analysis response:\n{text}\n")

        try:
            body_analysis = json.loads(text)
            print(f"[Gemini] Parsed body analysis: {body_analysis}\n")
        except json.JSONDecodeError:
            raise ValueError(f"Gemini returned non-JSON:\n{text}")

        # Step 2: Generate personalized workout plan
        workout_prompt = generate_workout_prompt(
            body_analysis.get("body_type", "mesomorph"),
            body_analysis.get("primary_focus", "chest"),
            body_analysis.get("secondary_focuses", ["back", "shoulders"]),
            self.difficulty,
            self.days_per_week
        )
        
        workout_resp = model.generate_content(
            [workout_prompt],
            generation_config={"response_mime_type": "application/json"},
        )
        
        workout_text = (workout_resp.text or "").strip()
        print(f"[Gemini] Workout plan response:\n{workout_text}\n")
        
        try:
            workout_plan = json.loads(workout_text)
            print(f"[Gemini] Parsed workout plan: Generated {len(workout_plan.get('days', []))} days\n")
        except json.JSONDecodeError:
            print(f"Warning: Could not parse workout plan, returning empty")
            workout_plan = {"days": [], "days_per_week": 4, "notes": "Error generating plan"}

        # Merge results
        result = body_analysis.copy()
        result["workout_plan"] = workout_plan

        return {
            "type": "user_image",
            "input_source": input_source,
            "mime_type": mime_type,
            "model": self.model,
            "result": result,
        }


