-- Normalize pre-made workout templates so Explore Workouts is coherent.
-- Applies deterministic exercise mapping for all seeded templates.

START TRANSACTION;

-- Plan 3: Beginner Full Body (3 days, balanced)
UPDATE plan_exercises pe
JOIN workout_plans wp ON wp.id = pe.plan_id
SET pe.exercise_id = 1, pe.sets = 3, pe.reps = '8-12', pe.rest_seconds = 90
WHERE wp.name = 'Beginner Full Body' AND pe.day_number = 1 AND pe.position = 1;

UPDATE plan_exercises pe
JOIN workout_plans wp ON wp.id = pe.plan_id
SET pe.exercise_id = 12, pe.sets = 3, pe.reps = '10-15', pe.rest_seconds = 90
WHERE wp.name = 'Beginner Full Body' AND pe.day_number = 1 AND pe.position = 2;

UPDATE plan_exercises pe
JOIN workout_plans wp ON wp.id = pe.plan_id
SET pe.exercise_id = 31, pe.sets = 3, pe.reps = '10-15', pe.rest_seconds = 75
WHERE wp.name = 'Beginner Full Body' AND pe.day_number = 1 AND pe.position = 3;

UPDATE plan_exercises pe
JOIN workout_plans wp ON wp.id = pe.plan_id
SET pe.exercise_id = 4, pe.sets = 3, pe.reps = '10-12', pe.rest_seconds = 75
WHERE wp.name = 'Beginner Full Body' AND pe.day_number = 2 AND pe.position = 1;

UPDATE plan_exercises pe
JOIN workout_plans wp ON wp.id = pe.plan_id
SET pe.exercise_id = 16, pe.sets = 3, pe.reps = '10-15', pe.rest_seconds = 75
WHERE wp.name = 'Beginner Full Body' AND pe.day_number = 2 AND pe.position = 2;

UPDATE plan_exercises pe
JOIN workout_plans wp ON wp.id = pe.plan_id
SET pe.exercise_id = 36, pe.sets = 3, pe.reps = '10-12', pe.rest_seconds = 75
WHERE wp.name = 'Beginner Full Body' AND pe.day_number = 2 AND pe.position = 3;

UPDATE plan_exercises pe
JOIN workout_plans wp ON wp.id = pe.plan_id
SET pe.exercise_id = 8, pe.sets = 3, pe.reps = '12-15', pe.rest_seconds = 60
WHERE wp.name = 'Beginner Full Body' AND pe.day_number = 3 AND pe.position = 1;

UPDATE plan_exercises pe
JOIN workout_plans wp ON wp.id = pe.plan_id
SET pe.exercise_id = 17, pe.sets = 3, pe.reps = '12-15', pe.rest_seconds = 60
WHERE wp.name = 'Beginner Full Body' AND pe.day_number = 3 AND pe.position = 2;

UPDATE plan_exercises pe
JOIN workout_plans wp ON wp.id = pe.plan_id
SET pe.exercise_id = 30, pe.sets = 3, pe.reps = '10-12', pe.rest_seconds = 75
WHERE wp.name = 'Beginner Full Body' AND pe.day_number = 3 AND pe.position = 3;

-- Plan 4: Intermediate Push/Pull/Legs
UPDATE plan_exercises pe
JOIN workout_plans wp ON wp.id = pe.plan_id
SET pe.exercise_id = 1, pe.sets = 4, pe.reps = '6-10', pe.rest_seconds = 90
WHERE wp.name = 'Intermediate Push/Pull/Legs' AND pe.day_number = 1 AND pe.position = 1;

UPDATE plan_exercises pe
JOIN workout_plans wp ON wp.id = pe.plan_id
SET pe.exercise_id = 36, pe.sets = 4, pe.reps = '8-12', pe.rest_seconds = 90
WHERE wp.name = 'Intermediate Push/Pull/Legs' AND pe.day_number = 1 AND pe.position = 2;

UPDATE plan_exercises pe
JOIN workout_plans wp ON wp.id = pe.plan_id
SET pe.exercise_id = 9, pe.sets = 3, pe.reps = '8-12', pe.rest_seconds = 75
WHERE wp.name = 'Intermediate Push/Pull/Legs' AND pe.day_number = 1 AND pe.position = 3;

UPDATE plan_exercises pe
JOIN workout_plans wp ON wp.id = pe.plan_id
SET pe.exercise_id = 164, pe.sets = 4, pe.reps = '6-10', pe.rest_seconds = 90
WHERE wp.name = 'Intermediate Push/Pull/Legs' AND pe.day_number = 2 AND pe.position = 1;

UPDATE plan_exercises pe
JOIN workout_plans wp ON wp.id = pe.plan_id
SET pe.exercise_id = 31, pe.sets = 4, pe.reps = '8-12', pe.rest_seconds = 90
WHERE wp.name = 'Intermediate Push/Pull/Legs' AND pe.day_number = 2 AND pe.position = 2;

UPDATE plan_exercises pe
JOIN workout_plans wp ON wp.id = pe.plan_id
SET pe.exercise_id = 32, pe.sets = 3, pe.reps = '10-12', pe.rest_seconds = 75
WHERE wp.name = 'Intermediate Push/Pull/Legs' AND pe.day_number = 2 AND pe.position = 3;

UPDATE plan_exercises pe
JOIN workout_plans wp ON wp.id = pe.plan_id
SET pe.exercise_id = 12, pe.sets = 4, pe.reps = '6-10', pe.rest_seconds = 120
WHERE wp.name = 'Intermediate Push/Pull/Legs' AND pe.day_number = 3 AND pe.position = 1;

UPDATE plan_exercises pe
JOIN workout_plans wp ON wp.id = pe.plan_id
SET pe.exercise_id = 16, pe.sets = 4, pe.reps = '8-12', pe.rest_seconds = 90
WHERE wp.name = 'Intermediate Push/Pull/Legs' AND pe.day_number = 3 AND pe.position = 2;

UPDATE plan_exercises pe
JOIN workout_plans wp ON wp.id = pe.plan_id
SET pe.exercise_id = 17, pe.sets = 3, pe.reps = '10-15', pe.rest_seconds = 75
WHERE wp.name = 'Intermediate Push/Pull/Legs' AND pe.day_number = 3 AND pe.position = 3;

-- Plan 5: Advanced Chest Focus (ensure chest-only and full Day 4)
UPDATE plan_exercises pe
JOIN workout_plans wp ON wp.id = pe.plan_id
SET pe.exercise_id = 2, pe.sets = 4, pe.reps = '3-8', pe.rest_seconds = 120
WHERE wp.name = 'Advanced Chest Focus' AND pe.day_number = 1 AND pe.position = 1;

UPDATE plan_exercises pe
JOIN workout_plans wp ON wp.id = pe.plan_id
SET pe.exercise_id = 4, pe.sets = 4, pe.reps = '6-10', pe.rest_seconds = 90
WHERE wp.name = 'Advanced Chest Focus' AND pe.day_number = 1 AND pe.position = 2;

UPDATE plan_exercises pe
JOIN workout_plans wp ON wp.id = pe.plan_id
SET pe.exercise_id = 6, pe.sets = 4, pe.reps = '10-12', pe.rest_seconds = 75
WHERE wp.name = 'Advanced Chest Focus' AND pe.day_number = 1 AND pe.position = 3;

UPDATE plan_exercises pe
JOIN workout_plans wp ON wp.id = pe.plan_id
SET pe.exercise_id = 8, pe.sets = 4, pe.reps = '6-10', pe.rest_seconds = 120
WHERE wp.name = 'Advanced Chest Focus' AND pe.day_number = 2 AND pe.position = 1;

UPDATE plan_exercises pe
JOIN workout_plans wp ON wp.id = pe.plan_id
SET pe.exercise_id = 10, pe.sets = 4, pe.reps = '6-10', pe.rest_seconds = 120
WHERE wp.name = 'Advanced Chest Focus' AND pe.day_number = 2 AND pe.position = 2;

UPDATE plan_exercises pe
JOIN workout_plans wp ON wp.id = pe.plan_id
SET pe.exercise_id = 9, pe.sets = 4, pe.reps = '6-10', pe.rest_seconds = 90
WHERE wp.name = 'Advanced Chest Focus' AND pe.day_number = 2 AND pe.position = 3;

UPDATE plan_exercises pe
JOIN workout_plans wp ON wp.id = pe.plan_id
SET pe.exercise_id = 85, pe.sets = 4, pe.reps = '6-10', pe.rest_seconds = 90
WHERE wp.name = 'Advanced Chest Focus' AND pe.day_number = 3 AND pe.position = 1;

UPDATE plan_exercises pe
JOIN workout_plans wp ON wp.id = pe.plan_id
SET pe.exercise_id = 86, pe.sets = 4, pe.reps = '6-10', pe.rest_seconds = 90
WHERE wp.name = 'Advanced Chest Focus' AND pe.day_number = 3 AND pe.position = 2;

UPDATE plan_exercises pe
JOIN workout_plans wp ON wp.id = pe.plan_id
SET pe.exercise_id = 87, pe.sets = 4, pe.reps = '8-12', pe.rest_seconds = 90
WHERE wp.name = 'Advanced Chest Focus' AND pe.day_number = 3 AND pe.position = 3;

-- Rebuild day 4 deterministically to 3 slots
DELETE pe
FROM plan_exercises pe
JOIN workout_plans wp ON wp.id = pe.plan_id
WHERE wp.name = 'Advanced Chest Focus' AND pe.day_number = 4;

INSERT INTO plan_exercises (plan_id, day_number, exercise_id, position, sets, reps, rest_seconds)
SELECT wp.id, 4, 1, 1, 4, '4-8', 120
FROM workout_plans wp
WHERE wp.name = 'Advanced Chest Focus';

INSERT INTO plan_exercises (plan_id, day_number, exercise_id, position, sets, reps, rest_seconds)
SELECT wp.id, 4, 2, 2, 4, '6-10', 90
FROM workout_plans wp
WHERE wp.name = 'Advanced Chest Focus';

INSERT INTO plan_exercises (plan_id, day_number, exercise_id, position, sets, reps, rest_seconds)
SELECT wp.id, 4, 87, 3, 3, '8-12', 90
FROM workout_plans wp
WHERE wp.name = 'Advanced Chest Focus';

-- Plan 6: Advanced Leg Day
UPDATE plan_exercises pe
JOIN workout_plans wp ON wp.id = pe.plan_id
SET pe.exercise_id = 12, pe.sets = 5, pe.reps = '3-8', pe.rest_seconds = 120
WHERE wp.name = 'Advanced Leg Day' AND pe.day_number = 1 AND pe.position = 1;

UPDATE plan_exercises pe
JOIN workout_plans wp ON wp.id = pe.plan_id
SET pe.exercise_id = 16, pe.sets = 4, pe.reps = '8-12', pe.rest_seconds = 90
WHERE wp.name = 'Advanced Leg Day' AND pe.day_number = 1 AND pe.position = 2;

UPDATE plan_exercises pe
JOIN workout_plans wp ON wp.id = pe.plan_id
SET pe.exercise_id = 17, pe.sets = 4, pe.reps = '10-15', pe.rest_seconds = 75
WHERE wp.name = 'Advanced Leg Day' AND pe.day_number = 1 AND pe.position = 3;

UPDATE plan_exercises pe
JOIN workout_plans wp ON wp.id = pe.plan_id
SET pe.exercise_id = 15, pe.sets = 4, pe.reps = '6-12', pe.rest_seconds = 90
WHERE wp.name = 'Advanced Leg Day' AND pe.day_number = 2 AND pe.position = 1;

UPDATE plan_exercises pe
JOIN workout_plans wp ON wp.id = pe.plan_id
SET pe.exercise_id = 169, pe.sets = 4, pe.reps = '10-15', pe.rest_seconds = 75
WHERE wp.name = 'Advanced Leg Day' AND pe.day_number = 2 AND pe.position = 2;

UPDATE plan_exercises pe
JOIN workout_plans wp ON wp.id = pe.plan_id
SET pe.exercise_id = 239, pe.sets = 3, pe.reps = '45-60 sec', pe.rest_seconds = 60
WHERE wp.name = 'Advanced Leg Day' AND pe.day_number = 2 AND pe.position = 3;

UPDATE plan_exercises pe
JOIN workout_plans wp ON wp.id = pe.plan_id
SET pe.exercise_id = 12, pe.sets = 5, pe.reps = '3-8', pe.rest_seconds = 120
WHERE wp.name = 'Advanced Leg Day' AND pe.day_number = 3 AND pe.position = 1;

UPDATE plan_exercises pe
JOIN workout_plans wp ON wp.id = pe.plan_id
SET pe.exercise_id = 16, pe.sets = 4, pe.reps = '6-10', pe.rest_seconds = 120
WHERE wp.name = 'Advanced Leg Day' AND pe.day_number = 3 AND pe.position = 2;

UPDATE plan_exercises pe
JOIN workout_plans wp ON wp.id = pe.plan_id
SET pe.exercise_id = 17, pe.sets = 4, pe.reps = '10-12', pe.rest_seconds = 90
WHERE wp.name = 'Advanced Leg Day' AND pe.day_number = 3 AND pe.position = 3;

COMMIT;
