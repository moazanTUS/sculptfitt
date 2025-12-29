import cv2
import numpy as np
import json
from collections import deque
from .base_analyzer import PoseAnalyzer


class ShoulderPressAnalyzer(PoseAnalyzer):
    """
    Shoulder Press analyzer based on WRIST vertical travel (not elbow angle).
    Robust for barbell + front-ish view.

    Rep definition:
      bottom (wrists near shoulders) -> rising -> top hold (wrists above head line) -> falling -> bottom hold
    """

    def __init__(self, video_path):
        super().__init__(video_path)

        # counters
        self.total_reps = 0
        self.perfect_reps = 0
        self.partial_reps = 0

        # states
        # bottom -> rising -> top -> falling
        self.state = "bottom"
        self.rep_frames = 0

        # smoothing
        self.wy_buf = deque(maxlen=7)   # avg wrist y
        self.sy_buf = deque(maxlen=7)   # avg shoulder y
        self.hy_buf = deque(maxlen=7)   # avg hip y
        self.ny_buf = deque(maxlen=7)   # nose y (head reference)

        # thresholds (normalized y; smaller = higher on screen)
        # Dynamic thresholds are computed each frame based on shoulder/hip span.
        self.BOTTOM_MARGIN = 0.06   # how close wrists must be to shoulders to count as bottom
        self.TOP_MARGIN    = 0.04   # how far above "head line" wrists must be to count as top
        self.TOP_HOLD      = 4      # frames to hold top
        self.BOTTOM_HOLD   = 4      # frames to confirm bottom reset

        self.MIN_ROM       = 0.08   # minimum wrist travel (normalized) to count as a rep at all
        self.MAX_REP_FR    = 300

        # per-rep trackers
        self.bottom_wy = None   # highest wrist y (lowest on screen) during bottom
        self.top_wy = None      # lowest wrist y (highest on screen) during rep
        self.top_hold_frames = 0
        self.bottom_hold_frames = 0

        # feedback
        self.flash_text = ""
        self.flash_frames = 0

    def _smooth(self, q):
        return float(sum(q) / len(q))

    def _avg_lr(self, lm, a, b):
        return (lm[a][0] + lm[b][0]) / 2.0, (lm[a][1] + lm[b][1]) / 2.0

    def _classify_and_reset(self, perfect: bool, partial: bool):
        self.total_reps += 1
        if perfect:
            self.perfect_reps += 1
            self.flash_text = "Perfect Rep ✅"
        elif partial:
            self.partial_reps += 1
            self.flash_text = "Partial Rep ⚠️"
        else:
            self.total_reps -= 1
            self.flash_text = "No Rep"

        self.flash_frames = 12

        # reset to bottom waiting
        self.state = "bottom"
        self.rep_frames = 0
        self.bottom_wy = None
        self.top_wy = None
        self.top_hold_frames = 0
        self.bottom_hold_frames = 0

    def analyze(self):
        while self.cap.isOpened():
            ok, frame = self.cap.read()
            if not ok:
                break

            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = self.pose.process(rgb)
            if not results.pose_landmarks:
                self.out.write(frame)
                continue

            lm = self.get_landmarks(results)

            # We need nose; base class doesn't include it.
            # Safest way: pull from results directly (normalized coordinates).
            nose = results.pose_landmarks.landmark[self.mp_pose.PoseLandmark.NOSE.value]
            nose_y = nose.y

            # averaged landmarks for stability
            _, sh_y = self._avg_lr(lm, "l_shoulder", "r_shoulder")
            _, hip_y = self._avg_lr(lm, "l_hip", "r_hip")
            _, wr_y = self._avg_lr(lm, "l_wrist", "r_wrist")

            # smooth
            self.sy_buf.append(sh_y)
            self.hy_buf.append(hip_y)
            self.wy_buf.append(wr_y)
            self.ny_buf.append(nose_y)

            if len(self.wy_buf) < self.wy_buf.maxlen:
                self.draw_pose(frame, results)
                self.out.write(frame)
                cv2.imshow("SculpFit - Shoulder Press Analyzer", frame)
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break
                continue

            sh = self._smooth(self.sy_buf)
            hip = self._smooth(self.hy_buf)
            wy = self._smooth(self.wy_buf)
            ny = self._smooth(self.ny_buf)

            # body scale proxy (bigger means person takes more of frame)
            torso = max(abs(hip - sh), 1e-6)

            # Dynamic reference lines:
            # - bottom_line: around shoulder height (wrists near shoulders)
            # - head_line: slightly ABOVE nose (so top is "clearly overhead")
            bottom_line = sh + self.BOTTOM_MARGIN * torso
            head_line = ny - (0.20 * torso)  # above nose/forehead region

            # conditions
            at_bottom = (wy >= bottom_line)               # wrists low enough (near shoulders)
            at_top = (wy <= (head_line - self.TOP_MARGIN * torso))  # wrists clearly overhead

            # rep trackers
            self.rep_frames += 1
            if self.bottom_wy is None or wy > self.bottom_wy:
                self.bottom_wy = wy
            if self.top_wy is None or wy < self.top_wy:
                self.top_wy = wy

            # hold counters
            if at_top:
                self.top_hold_frames += 1
            else:
                self.top_hold_frames = 0

            if at_bottom:
                self.bottom_hold_frames += 1
            else:
                self.bottom_hold_frames = 0

            # --- state machine ---
            if self.state == "bottom":
                # wait for a real start: wrists leave bottom zone upward
                if not at_bottom:
                    self.state = "rising"
                    self.rep_frames = 0
                    self.bottom_wy = wy
                    self.top_wy = wy

            elif self.state == "rising":
                # if top reached and held -> count
                if self.top_hold_frames >= self.TOP_HOLD:
                    rom = (self.bottom_wy - self.top_wy) if (self.bottom_wy is not None and self.top_wy is not None) else 0.0

                    if rom >= self.MIN_ROM:
                        # Perfect = clear top hold (already true) + clear bottom seen during rep start
                        self._classify_and_reset(perfect=True, partial=False)
                    else:
                        self._classify_and_reset(perfect=False, partial=False)

                # if they reverse downward without reaching top hold -> go to falling (possible partial later)
                elif at_bottom and self.rep_frames > 6:
                    # never got overhead hold, but might still be a partial if ROM is meaningful
                    rom = (self.bottom_wy - self.top_wy) if (self.bottom_wy is not None and self.top_wy is not None) else 0.0
                    if rom >= self.MIN_ROM:
                        self._classify_and_reset(perfect=False, partial=True)
                    else:
                        self._classify_and_reset(perfect=False, partial=False)

            # Safety timeout
            if self.rep_frames > self.MAX_REP_FR and self.state != "bottom":
                rom = (self.bottom_wy - self.top_wy) if (self.bottom_wy is not None and self.top_wy is not None) else 0.0
                if rom >= self.MIN_ROM:
                    self._classify_and_reset(perfect=False, partial=True)
                else:
                    self._classify_and_reset(perfect=False, partial=False)

            # --- draw ---
            h, w = frame.shape[:2]
            def yline(y, color):
                yy = int(y * h)
                cv2.line(frame, (0, yy), (w, yy), color, 2)

            # lines: shoulders/bottom, head/top, wrists
            yline(sh, (0, 255, 255))                 # shoulder reference
            yline(bottom_line, (0, 200, 255))        # bottom zone line
            yline(head_line, (0, 255, 0))            # top target line
            yline(wy, (255, 0, 0))                   # wrist line

            self.draw_pose(frame, results)

            cv2.rectangle(frame, (0, 0), (620, 160), (0, 0, 0), -1)
            cv2.putText(frame, f"Total: {self.total_reps}", (10, 40),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 2)
            cv2.putText(frame, f"Perfect: {self.perfect_reps}", (10, 80),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0,255,0), 2)
            cv2.putText(frame, f"Partial: {self.partial_reps}", (10, 115),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0,255,255), 2)
            cv2.putText(frame, f"State: {self.state}", (360, 40),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.9, (200,200,200), 2)

            if self.flash_frames > 0:
                color = (0,255,0) if "Perfect" in self.flash_text else (0,255,255)
                cv2.putText(frame, self.flash_text, (int(w*0.18), int(h*0.55)),
                            cv2.FONT_HERSHEY_SIMPLEX, 1.5, color, 3)
                self.flash_frames -= 1

            self.out.write(frame)


        self.release()
        return self.generate_report()

    def generate_report(self):
        form_score = round(
            (self.perfect_reps + 0.5*self.partial_reps) / max(self.total_reps, 1) * 100, 2
        )
        result = {
            "exercise": "Shoulder Press",
            "total_reps": self.total_reps,
            "perfect_reps": self.perfect_reps,
            "partial_reps": self.partial_reps,
            "form_score": form_score,
            "feedback": (
                "Nice overhead lockout + pause!"
                if self.perfect_reps == self.total_reps
                else "Try to press fully overhead and pause briefly at the top."
            ),
            "annotated_video": self.output_path
        }
        print(json.dumps(result, indent=2))
        return result
