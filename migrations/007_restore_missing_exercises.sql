-- Add missing core exercises that are referenced by existing workouts and plans
-- These exercises were already in the database and referenced by workout/plan data

INSERT IGNORE INTO exercises (id, name, primary_muscle, difficulty) VALUES
(1, 'Bench Press', 'Chest', 'intermediate'),
(2, 'Incline Bench Press', 'Chest', 'intermediate'),
(4, 'Dumbbell Bench Press', 'Chest', 'intermediate'),
(6, 'Cable Flyes', 'Chest', 'beginner'),
(8, 'Push-up', 'Chest', 'beginner'),
(9, 'Dips', 'Chest', 'intermediate'),
(10, 'Machine Chest Press', 'Chest', 'beginner'),
(12, 'Barbell Squat', 'Legs', 'intermediate'),
(15, 'Dumbbell Squat', 'Legs', 'intermediate'),
(16, 'Leg Press', 'Legs', 'beginner'),
(17, 'Leg Curl', 'Legs', 'beginner'),
(20, 'Deadlift', 'Back', 'advanced'),
(23, 'Barbell Row', 'Back', 'intermediate'),
(29, 'Pull-up', 'Back', 'intermediate'),
(30, 'Lat Pulldown', 'Back', 'beginner'),
(31, 'Seated Row', 'Back', 'beginner'),
(32, 'Dumbbell Row', 'Back', 'intermediate'),
(33, 'T-Bar Row', 'Back', 'intermediate'),
(34, 'Face Pulls', 'Shoulders', 'beginner'),
(35, 'Shoulder Press', 'Shoulders', 'intermediate'),
(36, 'Dumbbell Shoulder Press', 'Shoulders', 'intermediate'),
(85, 'Incline Dumbbell Bench Press', 'Chest', 'intermediate'),
(86, 'Decline Bench Press', 'Chest', 'intermediate'),
(87, 'Smith Machine Bench Press', 'Chest', 'intermediate')
ON DUPLICATE KEY UPDATE id=id;
