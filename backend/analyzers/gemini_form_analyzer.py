import cv2
import os
import base64
import io
import tempfile
import numpy as np
from pathlib import Path
import google.genai as genai

try:
    import mediapipe as mp
    HAS_MEDIAPIPE = True
except ImportError:
    HAS_MEDIAPIPE = False
    mp = None

class GeminiFormAnalyzer:
    """
    Universal form analyzer using Gemini Vision.
    Works for any exercise - no custom logic needed.
    Supports both file path and in-memory BytesIO video data.
    """
    
    def __init__(self, video_path=None, video_bytes=None, api_key=None, num_frames=5, start_time=None, end_time=None, rep_count=None):
        # Handle both file path and in-memory BytesIO
        if video_bytes:
            # Create a temporary file from BytesIO for cv2 processing
            self.temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
            self.temp_file.write(video_bytes.getvalue())
            self.temp_file.close()
            self.video_path = self.temp_file.name
            self.is_temp = True
            print(f"[GeminiFormAnalyzer] Created temporary file: {self.video_path}")
        elif video_path:
            if not os.path.exists(video_path):
                raise FileNotFoundError(f"Video file not found at {video_path}")
            self.video_path = video_path
            self.is_temp = False
        else:
            raise ValueError("Must provide either video_path or video_bytes")
        
        self.num_frames = num_frames
        self.start_time = start_time  # in seconds
        self.end_time = end_time      # in seconds
        self.rep_count = rep_count    # number of reps to analyze
        
        # Initialize MediaPipe for rep detection (optional for Gemini-based analysis)
        self.mp_pose = None
        self.pose = None
        if HAS_MEDIAPIPE and hasattr(mp, 'solutions'):
            try:
                self.mp_pose = mp.solutions.pose
                self.pose = self.mp_pose.Pose(
                    static_image_mode=False,
                    model_complexity=1,
                    enable_segmentation=False,
                    min_detection_confidence=0.5
                )
            except Exception as e:
                print(f"[GeminiFormAnalyzer] Warning: Could not initialize MediaPipe: {e}")
                self.mp_pose = None
                self.pose = None
        
        # Initialize Gemini
        if not api_key:
            api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in environment")
        
        self.api_key = api_key
        self.client = genai.Client(api_key=api_key)
        
        # List available models and pick the best one for content generation with images
        try:
            available_models = self.client.models.list()
            available_names = [m.name for m in available_models]
            print(f"[GeminiFormAnalyzer] Found {len(available_names)} available models")
            
            # Prefer gemini-2.5-flash (multimodal, text output)
            # Avoid -image suffix models (those generate images, not text)
            best_model = None
            for name in available_names:
                # Skip embedding, image generation, audio, and special models
                if any(skip in name.lower() for skip in ['embedding', 'imagen', 'veo', 'aqa', 'robotics', 'computer-use', 'research', 'audio', '-image']):
                    continue
                # Prefer flash models without lite
                if 'gemini-2.5-flash' in name and 'lite' not in name and 'preview' not in name:
                    best_model = name
                    break
                elif 'gemini-2.5-flash' in name and 'lite' not in name:
                    best_model = name
            
            if not best_model:
                # Fallback to any flash model (but not -image variants)
                for name in available_names:
                    if 'flash' in name.lower() and 'embedding' not in name.lower() and '-image' not in name.lower():
                        best_model = name
                        break
            
            if not best_model:
                best_model = 'gemini-2.5-flash'
            
            print(f"[GeminiFormAnalyzer] Using model: {best_model}")
            self.model = best_model
        except Exception as e:
            print(f"[GeminiFormAnalyzer] Error listing models: {e}, using gemini-2.5-flash")
            self.model = 'gemini-2.5-flash'
        
        print(f"[GeminiFormAnalyzer] initialized with video: {video_path}")
    
    
    def extract_frames(self):
        """Extract key frames from video based on user-provided rep count."""
        # Use user-provided rep count
        rep_count = self.rep_count if self.rep_count else 3
        self._detected_rep_count = rep_count
        
        print(f"[GeminiFormAnalyzer] Using user-provided {rep_count} reps for frame extraction")
        
        cap = cv2.VideoCapture(self.video_path)
        if not cap.isOpened():
            raise FileNotFoundError(f"Cannot open video: {self.video_path}")
        
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        # Calculate frame range based on time constraints
        start_frame = int(self.start_time * fps) if self.start_time else 0
        end_frame = int(self.end_time * fps) if self.end_time else total_frames
        start_frame = max(0, min(start_frame, total_frames - 1))
        end_frame = max(start_frame + 1, min(end_frame, total_frames))
        
        # Distribute frames evenly across the selected time range based on rep count
        num_frames = min(self.num_frames, max(rep_count, 3))
        frame_indices = np.linspace(start_frame, end_frame - 1, num_frames, dtype=int)
        
        frames = []
        for frame_idx in frame_indices:
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
            ret, frame = cap.read()
            if ret:
                frames.append(frame)
        
        cap.release()
        
        time_range = f"{self.start_time or 0:.1f}s-{self.end_time or (total_frames/fps):.1f}s" if self.start_time or self.end_time else "full video"
        print(f"[GeminiFormAnalyzer] extracted {len(frames)} frames from {time_range}")
        return frames
    
    def frames_to_base64(self, frames):
        """Convert frames to base64 for API."""
        encoded = []
        for frame in frames:
            _, buffer = cv2.imencode('.jpg', frame)
            b64 = base64.b64encode(buffer).decode('utf-8')
            encoded.append(b64)
        return encoded
    
    def analyze(self, exercise=None):
        """Analyze form and return feedback."""
        try:
            # Extract frames
            frames = self.extract_frames()
            if not frames:
                raise ValueError("Could not extract frames from video")
            
            # Convert to base64
            encoded_frames = self.frames_to_base64(frames)
            
            # Build prompt
            exercise_text = f"Exercise: {exercise}" if exercise else "Exercise: General workout"
            prompt = f"""Analyze these workout frames and provide SHORT, CONCISE feedback.

{exercise_text}

If form is EXCELLENT: Just praise it! (2-3 sentences max)
If form needs work:
✓ 1-2 things done well
⚠️ 1-2 main things to improve
💡 1 key tip

Keep it brief, direct, and encouraging. Max 100 words."""
            
            # Send to Gemini with images - use google.genai API format with Blob
            content_parts = [prompt]
            
            # Add each frame as a Part with inline_data
            for i, b64_data in enumerate(encoded_frames):
                # Decode base64 back to bytes for Blob
                image_bytes = base64.b64decode(b64_data)
                # Create Part with inline_data (Blob)
                blob = genai.types.Blob(mime_type="image/jpeg", data=image_bytes)
                part = genai.types.Part(inline_data=blob)
                content_parts.append(part)
            
            print(f"[GeminiFormAnalyzer] sending {len(frames)} frames to Gemini...")
            print(f"[GeminiFormAnalyzer] content_parts: {len(content_parts)} parts (1 text + {len(content_parts)-1} images)")
            
            try:
                response = self.client.models.generate_content(
                    model=self.model,
                    contents=content_parts
                )
            except Exception as e:
                print(f"[GeminiFormAnalyzer] Exception calling generate_content: {e}")
                raise
            
            print(f"[GeminiFormAnalyzer] Got response object")
            
            # Handle case where response is blocked or has no content
            if not response.candidates:
                print(f"[GeminiFormAnalyzer] Response has no candidates")
                return {
                    "success": False,
                    "error": f"Gemini API returned no candidates. This may be due to safety filters.",
                    "type": "gemini_analysis",
                }
            
            candidate = response.candidates[0]
            print(f"[GeminiFormAnalyzer] First candidate finish_reason: {candidate.finish_reason}")
            
            if not candidate.content or not candidate.content.parts:
                print(f"[GeminiFormAnalyzer] Candidate has no content/parts")
                return {
                    "success": False,
                    "error": f"Gemini API returned empty response (finish_reason: {candidate.finish_reason}). This may be due to safety filters or unsupported content.",
                    "type": "gemini_analysis",
                }
            
            # Extract text from response - handle both text and other part types
            feedback_text = None
            print(f"[GeminiFormAnalyzer] Extracting text from response...")
            print(f"[GeminiFormAnalyzer] Response type: {type(response)}")
            print(f"[GeminiFormAnalyzer] Response dir: {[x for x in dir(response) if not x.startswith('_')][:20]}")
            
            if hasattr(response, 'text'):
                try:
                    feedback_text = response.text
                    print(f"[GeminiFormAnalyzer] Got text via response.text: {len(feedback_text) if feedback_text else 0} chars")
                except (ValueError, AttributeError) as e:
                    print(f"[GeminiFormAnalyzer] response.text failed: {e}")
                    # If .text fails, extract from parts
                    for part in candidate.content.parts:
                        if hasattr(part, 'text') and part.text:
                            feedback_text = part.text
                            print(f"[GeminiFormAnalyzer] Got text from part: {len(feedback_text)} chars")
                            break
            
            if not feedback_text:
                print(f"[GeminiFormAnalyzer] No text extracted from response.text, checking parts...")
                print(f"[GeminiFormAnalyzer] Candidate type: {type(candidate)}")
                print(f"[GeminiFormAnalyzer] Candidate.content type: {type(candidate.content) if hasattr(candidate, 'content') else 'no content'}")
                if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
                    print(f"[GeminiFormAnalyzer] Part types: {[type(p).__name__ for p in candidate.content.parts]}")
                    print(f"[GeminiFormAnalyzer] Parts content: {[str(p)[:100] for p in candidate.content.parts]}")
                # Fallback: iterate through parts

                for part in candidate.content.parts:
                    print(f"[GeminiFormAnalyzer] Part type: {type(part).__name__}, has text attr: {hasattr(part, 'text')}")
                    if hasattr(part, 'text') and part.text:
                        feedback_text = part.text
                        print(f"[GeminiFormAnalyzer] Got text from fallback: {len(feedback_text)} chars")
                        break
            
            if not feedback_text:
                print(f"[GeminiFormAnalyzer] Could not extract text from response")
                print(f"[GeminiFormAnalyzer] Response parts: {[type(p).__name__ for p in response.candidates[0].content.parts]}")
                return {
                    "success": False,
                    "error": "Could not extract text feedback from Gemini response",
                    "type": "gemini_analysis",
                }
            
            print(f"[GeminiFormAnalyzer] received analysis from Gemini")
            
            # Parse response into structured format
            result = {
                "success": True,
                "type": "gemini_analysis",
                "exercise": exercise or "General",
                "num_frames_analyzed": len(frames),
                "feedback": feedback_text,
                "raw_response": feedback_text,
            }
            
            # Add detected rep count if available
            if hasattr(self, '_detected_rep_count') and self._detected_rep_count:
                result["detected_reps"] = self._detected_rep_count
            
            return result
        
        except Exception as e:
            print(f"[GeminiFormAnalyzer] error: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": str(e),
                "type": "gemini_analysis",
            }
        finally:
            # Cleanup temporary file if created
            self._cleanup()
    
    def _cleanup(self):
        """Clean up temporary files if they were created"""
        if self.is_temp and hasattr(self, 'temp_file'):
            try:
                os.remove(self.temp_file.name)
                print(f"[GeminiFormAnalyzer] Cleaned up temporary file: {self.temp_file.name}")
            except Exception as e:
                print(f"[GeminiFormAnalyzer] Error cleaning up temp file: {e}")
