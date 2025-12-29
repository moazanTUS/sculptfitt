import cv2
import numpy as np
import json
from collections import deque
from .base_analyzer import PoseAnalyzer


class SquatAnalyzer(PoseAnalyzer):
    def __init__(self, video_path):
        super().__init__(video_path)
        # Counters & state
        self.total_reps = 0
        self.perfect_reps = 0
        self.partial_reps = 0
        self.rep_in_progress = False
        self.lowest_hip_y = None

        # Smoothing buffers (FIX: initialize these)
        self.hip_buffer = deque(maxlen=5)
        self.knee_buffer = deque(maxlen=5)

        # History (optional metrics)
        self.hip_y_list = []

        # Tunables
        self.return_margin = 0.015  # how far above threshold to consider "back up"

        # Flash feedback
        self.feedback_text = ""
        self.feedback_counter = 0

    def analyze(self):
        while self.cap.isOpened():
            ret, frame = self.cap.read()
            if not ret:
                break

            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = self.pose.process(rgb)
            if not results.pose_landmarks:
                self.out.write(frame)
                continue

            lm = self.get_landmarks(results)

            # Average L/R for stability
            avg_hip_y = np.mean([lm["l_hip"][1], lm["r_hip"][1]])
            avg_knee_y = np.mean([lm["l_knee"][1], lm["r_knee"][1]])
            avg_ankle_y = np.mean([lm["l_ankle"][1], lm["r_ankle"][1]])
            self.hip_y_list.append(avg_hip_y)

            # Smooth
            self.hip_buffer.append(avg_hip_y)
            self.knee_buffer.append(avg_knee_y)
            if len(self.hip_buffer) < self.hip_buffer.maxlen:
                # warmup
                self.draw_pose(frame, results)
                self.out.write(frame)
                continue

            hip_smooth = float(np.mean(self.hip_buffer))
            knee_smooth = float(np.mean(self.knee_buffer))

            # Thresholds:
            # - parallel_line = knee line (perfect when hips >= knee)
            # - partial_line  = ~20% of knee->ankle distance above the knee (shallower than perfect)
            leg_segment = abs(avg_ankle_y - avg_knee_y)  # positive
            parallel_line = knee_smooth
            partial_line = knee_smooth - 0.20 * leg_segment  # move UP on screen for partial threshold

            # --- Rep logic ---
            # Start a rep when hips go below partial line (descending)
            if not self.rep_in_progress and hip_smooth >= partial_line:
                self.rep_in_progress = True
                self.lowest_hip_y = hip_smooth  # reset lowest

            if self.rep_in_progress:
                # Track deepest hip position during the rep
                if self.lowest_hip_y is None or hip_smooth > self.lowest_hip_y:
                    self.lowest_hip_y = hip_smooth

                # Rep completes when hips come back up above the partial threshold with a small margin
                if hip_smooth < (partial_line - self.return_margin):
                    self.total_reps += 1

                    # Classify by deepest point reached
                    if self.lowest_hip_y >= parallel_line:
                        # hips met/crossed knee line → perfect
                        self.perfect_reps += 1
                        self.feedback_text = "Perfect Rep ✅"
                    elif self.lowest_hip_y >= partial_line:
                        # hips got within 20% above knee → partial
                        self.partial_reps += 1
                        self.feedback_text = "Partial Rep ⚠️"
                    else:
                        # too shallow → ignore this rep count adjustment
                        self.total_reps -= 1
                        self.feedback_text = "Too Shallow"

                    self.feedback_counter = 10
                    self.rep_in_progress = False
                    self.lowest_hip_y = None

            # --- Visualization ---
            h, w = frame.shape[:2]
            hip_px = int(hip_smooth * h)
            knee_px = int(knee_smooth * h)
            partial_px = int(partial_line * h)

            # Lines: green = perfect (knee), yellow = partial threshold, blue = hip
            cv2.line(frame, (0, knee_px), (w, knee_px), (0, 255, 0), 2)        # perfect target
            cv2.line(frame, (0, partial_px), (w, partial_px), (0, 255, 255), 2) # partial band
            cv2.line(frame, (0, hip_px), (w, hip_px), (255, 0, 0), 2)           # hips

            self.draw_pose(frame, results)

            # HUD
            cv2.rectangle(frame, (0, 0), (480, 130), (0, 0, 0), -1)
            cv2.putText(frame, f"Total Reps: {self.total_reps}", (10, 40),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 2)
            cv2.putText(frame, f"Perfect: {self.perfect_reps}", (10, 80),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0,255,0), 2)
            cv2.putText(frame, f"Partial: {self.partial_reps}", (10, 115),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0,255,255), 2)

            if self.feedback_counter > 0:
                color = (0,255,0) if "Perfect" in self.feedback_text else (0,255,255)
                cv2.putText(frame, self.feedback_text, (int(w*0.25), int(h*0.5)),
                            cv2.FONT_HERSHEY_SIMPLEX, 1.5, color, 3)
                self.feedback_counter -= 1

            self.out.write(frame)
            cv2.imshow("SculpFit - Squat Analyzer", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        self.release()
        return self.generate_report()

    def generate_report(self):
        # Weighted form score (partials count half)
        form_score = round(
            (self.perfect_reps + 0.5 * self.partial_reps) / max(self.total_reps, 1) * 100, 2
        )
        result = {
            "exercise": "Squats",
            "total_reps": self.total_reps,
            "perfect_reps": self.perfect_reps,
            "partial_reps": self.partial_reps,
            "form_score": form_score,
            "feedback": ("Excellent — full depth on all reps!"
                         if self.perfect_reps == self.total_reps
                         else "Good work — aim to meet the green line for perfect depth."),
            "annotated_video": self.output_path
        }
        print("\n--- SculpFit Squat Report ---")
        print(json.dumps(result, indent=2))
        print(f"\nAnnotated video saved at: {self.output_path}\n")
        return result
