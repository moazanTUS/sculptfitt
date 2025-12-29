-- 003_bodytype_plans.sql
-- Add body_type support to workout plans

USE sculpfit;

-- Create index for efficient body_type + focus queries (if not exists)
CREATE INDEX IF NOT EXISTS idx_plans_bodytype_focus ON workout_plans(body_type, primary_focus);

-- ============================================
-- SAMPLE ECTOMORPH PLANS (Lower volume, strength focus)
-- ============================================

-- Ectomorph Chest Focus (3-day)
INSERT INTO workout_plans (name, days_per_week, primary_focus, body_type) VALUES
('Chest Focus - Ectomorph (3-day)', 3, 'chest', 'ectomorph');
SET @plan_id = LAST_INSERT_ID();

INSERT INTO workout_days (plan_id, day_number, title) VALUES
(@plan_id, 1, 'Day 1: Barbell Focus'),
(@plan_id, 2, 'Day 2: Dumbbell Press'),
(@plan_id, 3, 'Day 3: Volume Day');

-- Get the day IDs
SELECT id INTO @day1_id FROM workout_days WHERE plan_id = @plan_id AND day_number = 1;
SELECT id INTO @day2_id FROM workout_days WHERE plan_id = @plan_id AND day_number = 2;
SELECT id INTO @day3_id FROM workout_days WHERE plan_id = @plan_id AND day_number = 3;

-- Day 1 exercises
INSERT INTO workout_day_items (day_id, exercise_id, sets, reps, rest_seconds, position) 
SELECT @day1_id, id, 5, '3-5', 120, 1 FROM exercises WHERE name='Barbell Bench Press' LIMIT 1;
INSERT INTO workout_day_items (day_id, exercise_id, sets, reps, rest_seconds, position) 
SELECT @day1_id, id, 4, '5-7', 120, 2 FROM exercises WHERE name='Incline Barbell Press' LIMIT 1;
INSERT INTO workout_day_items (day_id, exercise_id, sets, reps, rest_seconds, position) 
SELECT @day1_id, id, 3, '8-10', 90, 3 FROM exercises WHERE name='Dips' LIMIT 1;

-- Day 2 exercises
INSERT INTO workout_day_items (day_id, exercise_id, sets, reps, rest_seconds, position) 
SELECT @day2_id, id, 4, '6-8', 120, 1 FROM exercises WHERE name='Dumbbell Bench Press' LIMIT 1;
INSERT INTO workout_day_items (day_id, exercise_id, sets, reps, rest_seconds, position) 
SELECT @day2_id, id, 3, '8-10', 90, 2 FROM exercises WHERE name='Incline Dumbbell Press' LIMIT 1;
INSERT INTO workout_day_items (day_id, exercise_id, sets, reps, rest_seconds, position) 
SELECT @day2_id, id, 3, '10-12', 75, 3 FROM exercises WHERE name='Cable Fly' LIMIT 1;

-- Day 3 exercises
INSERT INTO workout_day_items (day_id, exercise_id, sets, reps, rest_seconds, position) 
SELECT @day3_id, id, 3, '6-8', 120, 1 FROM exercises WHERE name='Machine Chest Press' LIMIT 1;
INSERT INTO workout_day_items (day_id, exercise_id, sets, reps, rest_seconds, position) 
SELECT @day3_id, id, 3, '8-10', 90, 2 FROM exercises WHERE name='Push-ups' LIMIT 1;
INSERT INTO workout_day_items (day_id, exercise_id, sets, reps, rest_seconds, position) 
SELECT @day3_id, id, 3, '12-15', 60, 3 FROM exercises WHERE name='Pec Deck' LIMIT 1;

-- ============================================
-- SAMPLE MESOMORPH PLANS (Balanced, high volume)
-- ============================================

-- Mesomorph Chest Focus (3-day)
INSERT INTO workout_plans (name, days_per_week, primary_focus, body_type) VALUES
('Chest Focus - Mesomorph (3-day)', 3, 'chest', 'mesomorph');
SET @plan_id = LAST_INSERT_ID();

INSERT INTO workout_days (plan_id, day_number, title) VALUES
(@plan_id, 1, 'Day 1: Strength & Power'),
(@plan_id, 2, 'Day 2: Hypertrophy'),
(@plan_id, 3, 'Day 3: Volume Burnout');

-- Get the day IDs
SELECT id INTO @day1_id FROM workout_days WHERE plan_id = @plan_id AND day_number = 1;
SELECT id INTO @day2_id FROM workout_days WHERE plan_id = @plan_id AND day_number = 2;
SELECT id INTO @day3_id FROM workout_days WHERE plan_id = @plan_id AND day_number = 3;

-- Day 1 exercises
INSERT INTO workout_day_items (day_id, exercise_id, sets, reps, rest_seconds, position) 
SELECT @day1_id, id, 4, '5-7', 120, 1 FROM exercises WHERE name='Barbell Bench Press' LIMIT 1;
INSERT INTO workout_day_items (day_id, exercise_id, sets, reps, rest_seconds, position) 
SELECT @day1_id, id, 4, '8-10', 90, 2 FROM exercises WHERE name='Incline Dumbbell Press' LIMIT 1;
INSERT INTO workout_day_items (day_id, exercise_id, sets, reps, rest_seconds, position) 
SELECT @day1_id, id, 3, '10-12', 75, 3 FROM exercises WHERE name='Cable Fly' LIMIT 1;

-- Day 2 exercises
INSERT INTO workout_day_items (day_id, exercise_id, sets, reps, rest_seconds, position) 
SELECT @day2_id, id, 4, '8-10', 90, 1 FROM exercises WHERE name='Dumbbell Bench Press' LIMIT 1;
INSERT INTO workout_day_items (day_id, exercise_id, sets, reps, rest_seconds, position) 
SELECT @day2_id, id, 4, '8-12', 75, 2 FROM exercises WHERE name='Incline Barbell Press' LIMIT 1;
INSERT INTO workout_day_items (day_id, exercise_id, sets, reps, rest_seconds, position) 
SELECT @day2_id, id, 3, '12-15', 60, 3 FROM exercises WHERE name='Machine Chest Press' LIMIT 1;

-- Day 3 exercises
INSERT INTO workout_day_items (day_id, exercise_id, sets, reps, rest_seconds, position) 
SELECT @day3_id, id, 4, '10-12', 75, 1 FROM exercises WHERE name='Push-ups' LIMIT 1;
INSERT INTO workout_day_items (day_id, exercise_id, sets, reps, rest_seconds, position) 
SELECT @day3_id, id, 3, '12-15', 60, 2 FROM exercises WHERE name='Pec Deck' LIMIT 1;
INSERT INTO workout_day_items (day_id, exercise_id, sets, reps, rest_seconds, position) 
SELECT @day3_id, id, 3, '15-20', 45, 3 FROM exercises WHERE name='Cable Fly' LIMIT 1;

-- ============================================
-- SAMPLE ENDOMORPH PLANS (High volume, conditioning)
-- ============================================

-- Endomorph Chest Focus (3-day)
INSERT INTO workout_plans (name, days_per_week, primary_focus, body_type) VALUES
('Chest Focus - Endomorph (3-day)', 3, 'chest', 'endomorph');
SET @plan_id = LAST_INSERT_ID();

INSERT INTO workout_days (plan_id, day_number, title) VALUES
(@plan_id, 1, 'Day 1: High Volume'),
(@plan_id, 2, 'Day 2: Conditioning'),
(@plan_id, 3, 'Day 3: Burnout');

-- Get the day IDs
SELECT id INTO @day1_id FROM workout_days WHERE plan_id = @plan_id AND day_number = 1;
SELECT id INTO @day2_id FROM workout_days WHERE plan_id = @plan_id AND day_number = 2;
SELECT id INTO @day3_id FROM workout_days WHERE plan_id = @plan_id AND day_number = 3;

-- Day 1 exercises
INSERT INTO workout_day_items (day_id, exercise_id, sets, reps, rest_seconds, position) 
SELECT @day1_id, id, 4, '8-10', 75, 1 FROM exercises WHERE name='Barbell Bench Press' LIMIT 1;
INSERT INTO workout_day_items (day_id, exercise_id, sets, reps, rest_seconds, position) 
SELECT @day1_id, id, 4, '10-12', 60, 2 FROM exercises WHERE name='Incline Dumbbell Press' LIMIT 1;
INSERT INTO workout_day_items (day_id, exercise_id, sets, reps, rest_seconds, position) 
SELECT @day1_id, id, 3, '12-15', 45, 3 FROM exercises WHERE name='Dips' LIMIT 1;
INSERT INTO workout_day_items (day_id, exercise_id, sets, reps, rest_seconds, position) 
SELECT @day1_id, id, 3, '15-20', 45, 4 FROM exercises WHERE name='Push-ups' LIMIT 1;

-- Day 2 exercises
INSERT INTO workout_day_items (day_id, exercise_id, sets, reps, rest_seconds, position) 
SELECT @day2_id, id, 4, '12-15', 60, 1 FROM exercises WHERE name='Machine Chest Press' LIMIT 1;
INSERT INTO workout_day_items (day_id, exercise_id, sets, reps, rest_seconds, position) 
SELECT @day2_id, id, 3, '12-15', 45, 2 FROM exercises WHERE name='Cable Fly' LIMIT 1;
INSERT INTO workout_day_items (day_id, exercise_id, sets, reps, rest_seconds, position) 
SELECT @day2_id, id, 3, '15-20', 45, 3 FROM exercises WHERE name='Pec Deck' LIMIT 1;
INSERT INTO workout_day_items (day_id, exercise_id, sets, reps, rest_seconds, position) 
SELECT @day2_id, id, 2, '20-30', 30, 4 FROM exercises WHERE name='Push-ups' LIMIT 1;

-- Day 3 exercises
INSERT INTO workout_day_items (day_id, exercise_id, sets, reps, rest_seconds, position) 
SELECT @day3_id, id, 5, '15-20', 45, 1 FROM exercises WHERE name='Push-ups' LIMIT 1;
INSERT INTO workout_day_items (day_id, exercise_id, sets, reps, rest_seconds, position) 
SELECT @day3_id, id, 3, '12-15', 30, 2 FROM exercises WHERE name='Cable Fly' LIMIT 1;

-- Note: After running this, update existing plans to have body_type = 'all'
UPDATE workout_plans SET body_type = 'all' WHERE body_type IS NULL OR body_type = '';
