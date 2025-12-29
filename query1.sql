-- =========================
-- SCHEMA
-- =========================
DROP TABLE IF EXISTS plan_exercises;
DROP TABLE IF EXISTS workout_plans;

CREATE TABLE workout_plans (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(120) NOT NULL,
  days_per_week INT NOT NULL,
  primary_focus VARCHAR(20) NOT NULL
) ENGINE=InnoDB;

CREATE TABLE plan_exercises (
  id INT AUTO_INCREMENT PRIMARY KEY,
  plan_id INT NOT NULL,
  day INT NOT NULL,
  exercise_name VARCHAR(120) NOT NULL,
  muscle_group VARCHAR(20) NOT NULL,
  sets INT NOT NULL,
  reps VARCHAR(20) NOT NULL,
  rest_seconds INT NOT NULL,
  sort_order INT NOT NULL,
  CONSTRAINT fk_plan_exercises_plan
    FOREIGN KEY (plan_id) REFERENCES workout_plans(id)
    ON DELETE CASCADE,
  INDEX idx_plan_day (plan_id, day, sort_order)
) ENGINE=InnoDB;

-- =========================
-- PLANS (7 major focuses)
-- =========================
INSERT INTO workout_plans (name, days_per_week, primary_focus) VALUES
('Shoulder Focus Plan (3-day)', 3, 'shoulders'),
('Chest Focus Plan (3-day)',    3, 'chest'),
('Back Focus Plan (3-day)',     3, 'back'),
('Core Focus Plan (3-day)',     3, 'core'),
('Arms Focus Plan (3-day)',     3, 'arms'),
('Legs Focus Plan (3-day)',     3, 'legs'),
('Glutes Focus Plan (3-day)',   3, 'glutes');

-- NOTE: These inserts assume the plan ids are 1..7 in the same order above.
-- If your DB already had rows earlier, run TRUNCATE or verify ids.

-- =========================
-- PLAN 1: SHOULDERS
-- =========================
INSERT INTO plan_exercises (plan_id, day, exercise_name, muscle_group, sets, reps, rest_seconds, sort_order) VALUES
(1,1,'Overhead Press','shoulders',4,'6-10',120,1),
(1,1,'Lateral Raise','shoulders',3,'12-15',60,2),
(1,1,'Face Pull','back',3,'12-15',60,3),
(1,1,'Goblet Squat','legs',3,'8-12',90,4),
(1,1,'Plank','core',3,'30-60s',60,5),

(1,2,'Incline Dumbbell Press','chest',3,'8-12',90,1),
(1,2,'Arnold Press','shoulders',3,'8-12',90,2),
(1,2,'Rear Delt Fly','shoulders',3,'12-15',60,3),
(1,2,'Lat Pulldown / Pull-up','back',3,'8-12',90,4),
(1,2,'Dead Bug','core',3,'10-14',60,5),

(1,3,'Dumbbell Shoulder Press','shoulders',4,'8-12',90,1),
(1,3,'Upright Row (light)','shoulders',3,'10-12',75,2),
(1,3,'Triceps Pushdown','arms',3,'10-15',60,3),
(1,3,'Romanian Deadlift','legs',3,'8-10',120,4),
(1,3,'Side Plank','core',3,'20-45s',60,5);

-- =========================
-- PLAN 2: CHEST
-- =========================
INSERT INTO plan_exercises (plan_id, day, exercise_name, muscle_group, sets, reps, rest_seconds, sort_order) VALUES
(2,1,'Bench Press','chest',4,'6-10',120,1),
(2,1,'Incline Dumbbell Press','chest',3,'8-12',90,2),
(2,1,'Cable / Push-up Fly','chest',3,'12-15',60,3),
(2,1,'One-Arm Row','back',3,'8-12',90,4),
(2,1,'Hanging Knee Raise','core',3,'10-15',60,5),

(2,2,'Push-ups (controlled)','chest',4,'AMRAP',75,1),
(2,2,'Dips (assisted if needed)','chest',3,'6-12',90,2),
(2,2,'Overhead Press','shoulders',3,'6-10',120,3),
(2,2,'Split Squat','legs',3,'8-12',90,4),
(2,2,'Pallof Press','core',3,'10-12',60,5),

(2,3,'Incline Bench / Machine Press','chest',4,'8-12',90,1),
(2,3,'Chest Supported Fly','chest',3,'12-15',60,2),
(2,3,'Lat Pulldown / Pull-up','back',3,'8-12',90,3),
(2,3,'Triceps Pushdown','arms',3,'10-15',60,4),
(2,3,'Plank','core',3,'30-60s',60,5);

-- =========================
-- PLAN 3: BACK
-- =========================
INSERT INTO plan_exercises (plan_id, day, exercise_name, muscle_group, sets, reps, rest_seconds, sort_order) VALUES
(3,1,'Lat Pulldown / Pull-up','back',4,'6-10',120,1),
(3,1,'Seated Cable Row','back',3,'8-12',90,2),
(3,1,'Face Pull','back',3,'12-15',60,3),
(3,1,'Incline Dumbbell Press','chest',3,'8-12',90,4),
(3,1,'Dead Bug','core',3,'10-14',60,5),

(3,2,'Romanian Deadlift','legs',4,'6-10',120,1),
(3,2,'Single-Arm Dumbbell Row','back',3,'8-12',90,2),
(3,2,'Back Extension','back',3,'10-15',75,3),
(3,2,'Lateral Raise','shoulders',3,'12-15',60,4),
(3,2,'Side Plank','core',3,'20-45s',60,5),

(3,3,'Chest-Supported Row','back',4,'8-12',90,1),
(3,3,'Straight-Arm Pulldown','back',3,'12-15',60,2),
(3,3,'Biceps Curl','arms',3,'10-15',60,3),
(3,3,'Goblet Squat','legs',3,'8-12',90,4),
(3,3,'Plank','core',3,'30-60s',60,5);

-- =========================
-- PLAN 4: CORE
-- =========================
INSERT INTO plan_exercises (plan_id, day, exercise_name, muscle_group, sets, reps, rest_seconds, sort_order) VALUES
(4,1,'Plank','core',4,'30-75s',60,1),
(4,1,'Dead Bug','core',3,'10-14',60,2),
(4,1,'Hanging Knee Raise','core',3,'10-15',60,3),
(4,1,'Overhead Press','shoulders',3,'6-10',120,4),
(4,1,'Goblet Squat','legs',3,'8-12',90,5),

(4,2,'Pallof Press','core',4,'10-12',60,1),
(4,2,'Side Plank','core',3,'20-45s',60,2),
(4,2,'Cable Chop','core',3,'10-12',60,3),
(4,2,'Lat Pulldown / Pull-up','back',3,'8-12',90,4),
(4,2,'Incline Dumbbell Press','chest',3,'8-12',90,5),

(4,3,'Ab Wheel / Rollout','core',4,'6-12',75,1),
(4,3,'Reverse Crunch','core',3,'10-15',60,2),
(4,3,'Back Extension','back',3,'10-15',75,3),
(4,3,'Lateral Raise','shoulders',3,'12-15',60,4),
(4,3,'Romanian Deadlift','legs',3,'6-10',120,5);

-- =========================
-- PLAN 5: ARMS
-- =========================
INSERT INTO plan_exercises (plan_id, day, exercise_name, muscle_group, sets, reps, rest_seconds, sort_order) VALUES
(5,1,'Close-Grip Bench Press','arms',4,'6-10',120,1),
(5,1,'Triceps Pushdown','arms',3,'10-15',60,2),
(5,1,'Biceps Curl','arms',3,'10-15',60,3),
(5,1,'Lat Pulldown / Pull-up','back',3,'8-12',90,4),
(5,1,'Plank','core',3,'30-60s',60,5),

(5,2,'Dips (assisted if needed)','arms',4,'6-12',90,1),
(5,2,'Hammer Curl','arms',3,'10-12',60,2),
(5,2,'Lateral Raise','shoulders',3,'12-15',60,3),
(5,2,'Split Squat','legs',3,'8-12',90,4),
(5,2,'Dead Bug','core',3,'10-14',60,5),

(5,3,'Incline Dumbbell Curl','arms',4,'8-12',60,1),
(5,3,'Overhead Triceps Extension','arms',3,'10-12',60,2),
(5,3,'Row (any variation)','back',3,'8-12',90,3),
(5,3,'Push-ups (controlled)','chest',3,'AMRAP',75,4),
(5,3,'Goblet Squat','legs',3,'8-12',90,5);

-- =========================
-- PLAN 6: LEGS
-- =========================
INSERT INTO plan_exercises (plan_id, day, exercise_name, muscle_group, sets, reps, rest_seconds, sort_order) VALUES
(6,1,'Squat (any variation)','legs',4,'6-10',150,1),
(6,1,'Romanian Deadlift','legs',3,'6-10',120,2),
(6,1,'Walking Lunge','legs',3,'10-12/leg',90,3),
(6,1,'Lat Pulldown / Pull-up','back',3,'8-12',90,4),
(6,1,'Plank','core',3,'30-60s',60,5),

(6,2,'Leg Press','legs',4,'8-12',120,1),
(6,2,'Leg Curl','legs',3,'10-15',75,2),
(6,2,'Calf Raise','legs',3,'12-20',60,3),
(6,2,'Overhead Press','shoulders',3,'6-10',120,4),
(6,2,'Dead Bug','core',3,'10-14',60,5),

(6,3,'Split Squat','legs',4,'8-12/leg',90,1),
(6,3,'Hip Hinge (light RDL)','legs',3,'10-12',90,2),
(6,3,'Step-ups','legs',3,'10-12/leg',75,3),
(6,3,'Incline Dumbbell Press','chest',3,'8-12',90,4),
(6,3,'Side Plank','core',3,'20-45s',60,5);

-- =========================
-- PLAN 7: GLUTES
-- =========================
INSERT INTO plan_exercises (plan_id, day, exercise_name, muscle_group, sets, reps, rest_seconds, sort_order) VALUES
(7,1,'Hip Thrust','glutes',4,'6-12',120,1),
(7,1,'Romanian Deadlift','legs',3,'6-10',120,2),
(7,1,'Bulgarian Split Squat','legs',3,'8-12/leg',90,3),
(7,1,'Row (any variation)','back',3,'8-12',90,4),
(7,1,'Plank','core',3,'30-60s',60,5),

(7,2,'Glute Bridge','glutes',4,'10-15',75,1),
(7,2,'Cable Kickback','glutes',3,'12-15',60,2),
(7,2,'Walking Lunge','legs',3,'10-12/leg',90,3),
(7,2,'Overhead Press','shoulders',3,'6-10',120,4),
(7,2,'Dead Bug','core',3,'10-14',60,5),

(7,3,'Hip Thrust (lighter)','glutes',4,'10-15',90,1),
(7,3,'Step-ups','legs',3,'10-12/leg',75,2),
(7,3,'Back Extension (glute focus)','glutes',3,'10-15',75,3),
(7,3,'Push-ups (controlled)','chest',3,'AMRAP',75,4),
(7,3,'Side Plank','core',3,'20-45s',60,5);
