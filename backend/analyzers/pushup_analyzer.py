import cv2
import numpy as np
import json
from collections import deque
from .base_analyzer import PoseAnalyzer


class PushupAnalyzer(PoseAnalyzer):
    def __init__(self, video_path):
        super().__init__(video_path)
        # Counters
        self.total_reps = 0
        self.perfect_reps = 0
        self.partial_reps = 0

        # State machine
        self.state = "top"              # top → descending → bottom → ascending
        self.bottom_reached = False
        self.frames_in_state = 0
        self.rep_frames = 0

        # Smoothing
        self.sh_buf = deque(maxlen=7)
        self.el_buf = deque(maxlen=7)

        # Thresholds (normalized Y; y increases downward)
        self.DOWN_MARGIN = 0.02   # how far below elbow = depth
        self.TOP_MARGIN  = 0.02   # how far above elbow = full lockout
        self.BOTTOM_HOLD = 4      # frames shoulder must stay below elbow
        self.TOP_HOLD    = 4      # frames shoulder must stay above elbow
        self.MIN_ROM     = 0.012  # smallest ROM to still count as partial
        self.MAX_REP_FR  = 300    # bail-out (10s @30fps) to avoid stuck reps

        # Tracking for rep classification
        self.lowest_sh_y = None   # deepest shoulder y seen this rep
        self.top_reached_frames = 0
        self.bottom_hold_frames = 0

        # Feedback
        self.flash_text = ""
        self.flash_frames = 0

    def _smooth(self, q): return sum(q) / len(q)

    def _pick_side(self, lm):
        # Choose the side with greater shoulder–elbow separation (side view looks larger)
        l_sep = abs(lm["l_shoulder"][1] - lm["l_elbow"][1])
        r_sep = abs(lm["r_shoulder"][1] - lm["r_elbow"][1])
        if r_sep > l_sep:
            return lm["r_shoulder"][1], lm["r_elbow"][1]
        return lm["l_shoulder"][1], lm["l_elbow"][1]

    def _classify_and_reset(self, perfect: bool, partial: bool):
        self.total_reps += 1
        if perfect:
            self.perfect_reps += 1
            self.flash_text = "Perfect Rep ✅"
        elif partial:
            self.partial_reps += 1
            self.flash_text = "Partial Rep ⚠️"
        else:
            # no count if neither; but keep robustness: do not increment total
            self.total_reps -= 1  # in case called wrongly
            self.flash_text = "No Rep"
        self.flash_frames = 12

        # reset rep state
        self.state = "top"
        self.frames_in_state = 0
        self.rep_frames = 0
        self.bottom_reached = False
        self.lowest_sh_y = None
        self.top_reached_frames = 0
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

            # pick best side; smooth
            sh_y_raw, el_y_raw = self._pick_side(lm)
            self.sh_buf.append(sh_y_raw)
            self.el_buf.append(el_y_raw)
            if len(self.sh_buf) < self.sh_buf.maxlen:
                # warmup smoothing
                self.draw_pose(frame, results)
                self.out.write(frame)
                continue

            sh_y = self._smooth(self.sh_buf)
            el_y = self._smooth(self.el_buf)

            # relational flags
            below = (sh_y > el_y + self.DOWN_MARGIN)   # depth (shoulder below elbow)
            above = (sh_y < el_y - self.TOP_MARGIN)    # full lockout (shoulder above elbow)
            near_top = (sh_y < el_y)                   # above elbow (even if not full TOP_MARGIN)
            rom = abs(sh_y - el_y)                     # how far from elbow line (instant)

            # update trackers
            self.rep_frames += 1
            self.frames_in_state += 1
            if self.lowest_sh_y is None or sh_y > self.lowest_sh_y:
                self.lowest_sh_y = sh_y

            # hold counters
            if below:
                self.bottom_hold_frames += 1
            else:
                self.bottom_hold_frames = 0

            if above:
                self.top_reached_frames += 1
            else:
                self.top_reached_frames = 0

            # --- State machine with holds ---
            if self.state == "top":
                if below:
                    self.state = "descending"
                    self.frames_in_state = 0

            elif self.state == "descending":
                # Require sustained bottom to confirm depth
                if self.bottom_hold_frames >= self.BOTTOM_HOLD:
                    self.bottom_reached = True
                    self.state = "bottom"
                    self.frames_in_state = 0
                # If we reverse upward before real depth → keep waiting (counts partial later if enough ROM)
                elif near_top and self.frames_in_state > 6 and rom > self.MIN_ROM:
                    # down then reversed early: partial on reversal to top with no full lockout held
                    pass

            elif self.state == "bottom":
                # start ascending when we go above elbow line (not necessarily full lockout)
                if near_top:
                    self.state = "ascending"
                    self.frames_in_state = 0

            elif self.state == "ascending":
                # If we reach and HOLD full lockout → PERFECT
                if self.top_reached_frames >= self.TOP_HOLD:
                    # perfect only if bottom was truly reached and held
                    if self.bottom_reached:
                        self._classify_and_reset(perfect=True, partial=False)
                    else:
                        # got to lockout but never truly hit depth → partial
                        self._classify_and_reset(perfect=False, partial=True)

                # If we start descending again (lose near_top) before full lockout hold → PARTIAL (if ROM meaningful)
                elif not near_top and self.frames_in_state > 6:
                    if self.bottom_reached or (self.lowest_sh_y - el_y) > self.MIN_ROM:
                        self._classify_and_reset(perfect=False, partial=True)

            # Safety: too long stuck in a rep → classify by what we managed
            if self.rep_frames > self.MAX_REP_FR:
                if self.bottom_reached:
                    # hit depth but never locked out → partial
                    self._classify_and_reset(perfect=False, partial=True)
                else:
                    # barely moved → no rep
                    self._classify_and_reset(perfect=False, partial=False)

            # ----- Draw UI -----
            h, w = frame.shape[:2]
            sh_px = int(sh_y * h)
            el_px = int(el_y * h)
            cv2.line(frame, (0, el_px), (w, el_px), (0, 255, 0), 2)    # elbow line (green)
            cv2.line(frame, (0, sh_px), (w, sh_px), (255, 0, 0), 2)    # shoulder line (blue)

            self.draw_pose(frame, results)

            # HUD
            cv2.rectangle(frame, (0, 0), (520, 140), (0, 0, 0), -1)
            cv2.putText(frame, f"Total: {self.total_reps}", (10, 40),  cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 2)
            cv2.putText(frame, f"Perfect: {self.perfect_reps}", (10, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0,255,0), 2)
            cv2.putText(frame, f"Partial: {self.partial_reps}", (10, 115), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0,255,255), 2)
            cv2.putText(frame, f"State: {self.state}", (300, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (200,200,200), 2)

            if self.flash_frames > 0:
                color = (0,255,0) if "Perfect" in self.flash_text else (0,255,255)
                cv2.putText(frame, self.flash_text, (int(w*0.24), int(h*0.5)),
                            cv2.FONT_HERSHEY_SIMPLEX, 1.5, color, 3)
                self.flash_frames -= 1

            self.out.write(frame)
            cv2.imshow("SculpFit - Push-Up Analyzer", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        self.release()
        return self.generate_report()

    def generate_report(self):
        form_score = round((self.perfect_reps + 0.5*self.partial_reps)/max(self.total_reps,1)*100, 2)
        result = {
            "exercise": "Pushups",
            "total_reps": self.total_reps,
            "perfect_reps": self.perfect_reps,
            "partial_reps": self.partial_reps,
            "form_score": form_score,
            "feedback": ("Perfect lockout and depth!" if self.perfect_reps == self.total_reps
                         else "Aim for full lockout and clear depth on each rep."),
            "annotated_video": self.output_path
        }
        print(json.dumps(result, indent=2))
        return result
