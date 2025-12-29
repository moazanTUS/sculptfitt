import cv2
import numpy as np
from collections import deque
import os
import mediapipe as mp
from mediapipe import solutions

# ✅ ALWAYS disable GUI calls when running under a server
# (the backend should set SCULPFIT_HEADLESS=1, but be defensive)
try:
    cv2.imshow = lambda *a, **k: None
    cv2.waitKey = lambda *a, **k: -1
    cv2.destroyAllWindows = lambda *a, **k: None
except Exception:
    pass
class PoseAnalyzer:
    def __init__(self, video_path):
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file not found at {video_path}")

        self.video_path = video_path
        print(f"[PoseAnalyzer] attempting to open video: {video_path}")
        self.cap = cv2.VideoCapture(video_path)
        if not self.cap.isOpened():
            raise FileNotFoundError(f"Unable to open video at {video_path} (cv2.VideoCapture failed)")

        print(f"[PoseAnalyzer] opened video: {video_path}")

        self.fps = int(self.cap.get(cv2.CAP_PROP_FPS))
        self.width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.output_path = os.path.splitext(video_path)[0] + "_annotated.mp4"
        print(f"[PoseAnalyzer] props fps={self.fps} size={self.width}x{self.height} output={self.output_path}")
        self.out = cv2.VideoWriter(self.output_path, cv2.VideoWriter_fourcc(*'mp4v'), self.fps, (self.width, self.height))
        self.mp_pose = solutions.pose
        self.pose = self.mp_pose.Pose()
        self.drawing = solutions.drawing_utils

        # shared smoothing buffers (add more if needed in subclasses)
        self.buffers = {}

    def _get(self, lm, landmark):
        p = lm[landmark]
        return (p.x, p.y)

    def get_landmarks(self, results):
        lm = results.pose_landmarks.landmark
        P = self.mp_pose.PoseLandmark
        return {
            # Upper body (CORRECT for push-ups)
            "l_shoulder": self._get(lm, P.LEFT_SHOULDER.value),
            "r_shoulder": self._get(lm, P.RIGHT_SHOULDER.value),
            "l_elbow":    self._get(lm, P.LEFT_ELBOW.value),
            "r_elbow":    self._get(lm, P.RIGHT_ELBOW.value),
            "l_wrist":    self._get(lm, P.LEFT_WRIST.value),
            "r_wrist":    self._get(lm, P.RIGHT_WRIST.value),
            # Lower body (still available if needed)
            "l_hip":      self._get(lm, P.LEFT_HIP.value),
            "r_hip":      self._get(lm, P.RIGHT_HIP.value),
            "l_knee":     self._get(lm, P.LEFT_KNEE.value),
            "r_knee":     self._get(lm, P.RIGHT_KNEE.value),
            "l_ankle":    self._get(lm, P.LEFT_ANKLE.value),
            "r_ankle":    self._get(lm, P.RIGHT_ANKLE.value),
        }

    def draw_pose(self, frame, results):
        self.drawing.draw_landmarks(frame, results.pose_landmarks, self.mp_pose.POSE_CONNECTIONS)

    def release(self):
        self.cap.release()
        self.out.release()
        self.pose.close()
        cv2.destroyAllWindows()
