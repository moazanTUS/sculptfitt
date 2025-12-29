USE sculpfit;

-- Create days for plan 4
INSERT IGNORE INTO workout_days (plan_id, day_number, title) VALUES
(4, 1, 'Day 1'),
(4, 2, 'Day 2'),
(4, 3, 'Day 3');

-- Insert exercises (deduped by unique name)
INSERT IGNORE INTO exercises (name, muscle_group) VALUES
('Plank', 'core'),
('Dead Bug', 'core'),
('Hanging Knee Raise', 'core'),
('Overhead Press', 'shoulders'),
('Goblet Squat', 'legs'),
('Pallof Press', 'core'),
('Side Plank', 'core'),
('Cable Chop', 'core'),
('Lat Pulldown / Pull-up', 'back'),
('Incline Dumbbell Press', 'chest'),
('Ab Wheel / Rollout', 'core'),
('Reverse Crunch', 'core'),
('Back Extension', 'back'),
('Lateral Raise', 'shoulders'),
('Romanian Deadlift', 'legs');

-- Day 1 items
INSERT INTO workout_day_items (day_id, exercise_id, sets, reps, rest_seconds, position)
SELECT d.id, e.id, x.sets, x.reps, x.rest, x.pos
FROM workout_days d
JOIN (
  SELECT 'Plank' name, 4 sets, '30-75s' reps, 60 rest, 1 pos UNION ALL
  SELECT 'Dead Bug', 3, '10-14', 60, 2 UNION ALL
  SELECT 'Hanging Knee Raise', 3, '10-15', 60, 3 UNION ALL
  SELECT 'Overhead Press', 3, '6-10', 120, 4 UNION ALL
  SELECT 'Goblet Squat', 3, '8-12', 90, 5
) x ON 1=1
JOIN exercises e ON e.name = x.name
WHERE d.plan_id = 4 AND d.day_number = 1;

-- Day 2 items
INSERT INTO workout_day_items (day_id, exercise_id, sets, reps, rest_seconds, position)
SELECT d.id, e.id, x.sets, x.reps, x.rest, x.pos
FROM workout_days d
JOIN (
  SELECT 'Pallof Press' name, 4 sets, '10-12' reps, 60 rest, 1 pos UNION ALL
  SELECT 'Side Plank', 3, '20-45s', 60, 2 UNION ALL
  SELECT 'Cable Chop', 3, '10-12', 60, 3 UNION ALL
  SELECT 'Lat Pulldown / Pull-up', 3, '8-12', 90, 4 UNION ALL
  SELECT 'Incline Dumbbell Press', 3, '8-12', 90, 5
) x ON 1=1
JOIN exercises e ON e.name = x.name
WHERE d.plan_id = 4 AND d.day_number = 2;

-- Day 3 items
INSERT INTO workout_day_items (day_id, exercise_id, sets, reps, rest_seconds, position)
SELECT d.id, e.id, x.sets, x.reps, x.rest, x.pos
FROM workout_days d
JOIN (
  SELECT 'Ab Wheel / Rollout' name, 4 sets, '6-12' reps, 75 rest, 1 pos UNION ALL
  SELECT 'Reverse Crunch', 3, '10-15', 60, 2 UNION ALL
  SELECT 'Back Extension', 3, '10-15', 75, 3 UNION ALL
  SELECT 'Lateral Raise', 3, '12-15', 60, 4 UNION ALL
  SELECT 'Romanian Deadlift', 3, '6-10', 120, 5
) x ON 1=1
JOIN exercises e ON e.name = x.name
WHERE d.plan_id = 4 AND d.day_number = 3;
SELECT id, name, primary_focus FROM workout_plans ORDER BY id DESC LIMIT 5;
SELECT * FROM workout_days ORDER BY id DESC LIMIT 10;
SELECT * FROM workout_day_items ORDER BY id DESC LIMIT 10;
