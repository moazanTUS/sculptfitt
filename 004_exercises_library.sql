-- Exercises Library Table for Personalized Workout Plans
-- This table stores all available exercises with metadata for plan building

-- Drop old tables (if they exist with wrong schema)
DROP TABLE IF EXISTS plan_cache;
DROP TABLE IF EXISTS exercises;

CREATE TABLE exercises (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(100) NOT NULL,
  primary_muscle VARCHAR(50) NOT NULL,
  secondary_muscles JSON,  -- ["biceps", "shoulders"]
  difficulty ENUM('beginner', 'intermediate', 'advanced') NOT NULL,
  equipment VARCHAR(100),  -- 'barbell', 'dumbbell', 'machine', 'bodyweight', 'cables'
  
  -- Rep ranges by difficulty (will be auto-selected based on difficulty)
  beginner_reps VARCHAR(20) DEFAULT '10-15',
  intermediate_reps VARCHAR(20) DEFAULT '6-12',
  advanced_reps VARCHAR(20) DEFAULT '3-8',
  
  sets_beginner INT DEFAULT 3,
  sets_intermediate INT DEFAULT 3,
  sets_advanced INT DEFAULT 4,
  
  rest_seconds INT DEFAULT 90,
  instructions TEXT,
  form_cues TEXT,
  
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  KEY idx_primary_muscle (primary_muscle),
  KEY idx_difficulty (difficulty),
  UNIQUE KEY idx_name_difficulty (name, difficulty)
);

-- Insert comprehensive exercise library
INSERT INTO exercises (name, primary_muscle, secondary_muscles, difficulty, equipment, instructions, form_cues) VALUES

-- CHEST
('Barbell Bench Press', 'chest', '["triceps", "shoulders"]', 'intermediate', 'barbell', 'Lie flat on bench, grip shoulder-width, lower to chest, press up', 'Keep elbows 45 degrees, full chest contact'),
('Barbell Bench Press', 'chest', '["triceps", "shoulders"]', 'advanced', 'barbell', 'Lie flat on bench, grip shoulder-width, lower to chest, press up', 'Keep elbows 45 degrees, full chest contact'),
('Incline Dumbbell Press', 'chest', '["shoulders", "triceps"]', 'intermediate', 'dumbbell', 'Sit on incline bench, press dumbbells up', 'Controlled movement, avoid back arch'),
('Dumbbell Bench Press', 'chest', '["triceps", "shoulders"]', 'beginner', 'dumbbell', 'Lie flat, press dumbbells up from chest level', 'Full range of motion, controlled descent'),
('Push-ups', 'chest', '["triceps", "shoulders"]', 'beginner', 'bodyweight', 'Start in plank, lower body until chest near ground, push up', 'Keep core tight, straight body line'),
('Cable Flyes', 'chest', '["shoulders"]', 'intermediate', 'cables', 'Set cables at chest height, pull arms together across body', 'Slight bend in elbows, squeeze at peak'),
('Machine Chest Press', 'chest', '["triceps"]', 'beginner', 'machine', 'Sit on machine, press handles forward', 'Full range, smooth motion'),

-- BACK
('Barbell Rows', 'back', '["biceps", "shoulders"]', 'advanced', 'barbell', 'Bend at hips, grip shoulder-width, pull bar to chest', 'Keep back straight, explosive pull'),
('Dumbbell Rows', 'back', '["biceps"]', 'intermediate', 'dumbbell', 'Hinge at hips, row one dumbbell to hip', 'Squeeze shoulder blade, control descent'),
('Pull-ups', 'back', '["biceps", "shoulders"]', 'intermediate', 'bodyweight', 'Grip bar shoulder-width, pull chin above bar', 'Full range, avoid kipping'),
('Lat Pulldowns', 'back', '["biceps"]', 'beginner', 'cables', 'Sit, pull bar down to chest level', 'Lean back slightly, use back not arms'),
('Machine Rows', 'back', '["biceps"]', 'beginner', 'machine', 'Sit, pull handles toward chest', 'Squeeze back muscles at peak'),
('Face Pulls', 'back', '["shoulders"]', 'beginner', 'cables', 'Set cables at head height, pull toward face', 'Elbows up, good for shoulder health'),

-- SHOULDERS
('Barbell Shoulder Press', 'shoulders', '["triceps", "chest"]', 'advanced', 'barbell', 'Stand, press bar from shoulders overhead', 'Core tight, avoid lower back arch'),
('Dumbbell Shoulder Press', 'shoulders', '["triceps"]', 'intermediate', 'dumbbell', 'Sit or stand, press dumbbells overhead', 'Controlled, full range'),
('Lateral Raises', 'shoulders', '[]', 'beginner', 'dumbbell', 'Stand, raise dumbbells to sides up to shoulder height', 'Slight bend in elbows, controlled descent'),
('Machine Shoulder Press', 'shoulders', '["triceps"]', 'beginner', 'machine', 'Sit, press handles overhead', 'Full range, smooth motion'),
('Reverse Pec Deck', 'shoulders', '["back"]', 'beginner', 'machine', 'Sit facing machine, pull handles back', 'Good for rear delts'),

-- BICEPS
('Barbell Curls', 'biceps', '["shoulders"]', 'intermediate', 'barbell', 'Stand, grip shoulder-width, curl bar to shoulders', 'No swinging, elbows at sides'),
('Dumbbell Curls', 'biceps', '[]', 'beginner', 'dumbbell', 'Stand, curl dumbbells to shoulders', 'Controlled movement, full range'),
('Cable Curls', 'biceps', '[]', 'beginner', 'cables', 'Stand, curl rope to shoulders', 'Constant tension'),
('Hammer Curls', 'biceps', '["forearms"]', 'beginner', 'dumbbell', 'Stand, curl dumbbells with neutral grip', 'Great for forearm development'),

-- TRICEPS
('Barbell Close Grip Bench', 'triceps', '["chest", "shoulders"]', 'intermediate', 'barbell', 'Lie flat, narrow grip, press bar up', 'Elbows tucked'),
('Dumbbell Tricep Extensions', 'triceps', '[]', 'beginner', 'dumbbell', 'Lie back, press dumbbells overhead', 'Keep elbows stationary'),
('Tricep Dips', 'triceps', '["shoulders", "chest"]', 'intermediate', 'bodyweight', 'Support body on bars, lower and press up', 'Lean forward for chest, upright for triceps'),
('Cable Pushdowns', 'triceps', '[]', 'beginner', 'cables', 'Stand, push rope down, extend arms fully', 'Constant tension, no swinging'),
('Overhead Tricep Extensions', 'triceps', '[]', 'beginner', 'dumbbell', 'Stand, hold one dumbbell overhead, lower behind head', 'Full range of motion'),

-- LEGS
('Barbell Squats', 'legs', '["quads", "glutes"]', 'intermediate', 'barbell', 'Bar on shoulders, squat down past parallel, stand up', 'Knees track over toes, chest up'),
('Barbell Squats', 'legs', '["quads", "glutes"]', 'advanced', 'barbell', 'Bar on shoulders, squat down past parallel, stand up', 'Knees track over toes, chest up'),
('Dumbbell Squats', 'legs', '["quads", "glutes"]', 'beginner', 'dumbbell', 'Hold dumbbells, squat down, stand up', 'Full range, controlled'),
('Leg Press', 'legs', '["quads", "glutes"]', 'beginner', 'machine', 'Sit, push platform away from body', 'Knees track straight, avoid locking out'),
('Leg Extensions', 'legs', '["quads"]', 'beginner', 'machine', 'Sit, extend legs straightening knees', 'Controlled, no swinging'),
('Leg Curls', 'legs', '["hamstrings"]', 'beginner', 'machine', 'Lie face down, curl weight toward glutes', 'Squeeze hamstrings'),
('Lunges', 'legs', '["quads", "glutes"]', 'intermediate', 'dumbbell', 'Step forward, lower back knee, push back up', 'Knee over ankle, torso upright'),
('Walking Lunges', 'legs', '["quads", "glutes"]', 'intermediate', 'dumbbell', 'Step and lunge forward continuously', 'Full range, controlled'),

-- BACK (Lower)
('Barbell Deadlifts', 'back', '["legs", "glutes"]', 'advanced', 'barbell', 'Feet hip-width, grip shoulder-width, deadlift bar from ground', 'Flat back, explosive pull'),
('Deadlifts', 'back', '["legs", "glutes"]', 'intermediate', 'barbell', 'Feet hip-width, grip shoulder-width, deadlift bar from ground', 'Flat back, explosive pull'),

-- CORE
('Planks', 'core', '[]', 'beginner', 'bodyweight', 'Hold plank position, body straight', 'Glutes squeezed, no sag'),
('Ab Wheel', 'core', '[]', 'intermediate', 'equipment', 'Roll wheel forward, contract abs to pull back', 'Full extension'),
('Cable Crunches', 'core', '[]', 'beginner', 'cables', 'Kneel facing cable machine, pull rope down crunching', 'Feel abs contract'),
('Hanging Leg Raises', 'core', '[]', 'intermediate', 'bodyweight', 'Hang from bar, raise legs to horizontal', 'Controlled movement'),
('Dead Bugs', 'core', '[]', 'beginner', 'bodyweight', 'Lie back, raise arms and legs, extend opposite limbs', 'Keep lower back neutral');

-- Create plan_cache table
CREATE TABLE IF NOT EXISTS plan_cache (
  id INT AUTO_INCREMENT PRIMARY KEY,
  user_profile_hash VARCHAR(255) UNIQUE NOT NULL,  -- hash of body_type + focus
  body_type ENUM('ectomorph', 'mesomorph', 'endomorph') NOT NULL,
  primary_focus VARCHAR(50) NOT NULL,
  secondary_focuses JSON,
  difficulty ENUM('beginner', 'intermediate', 'advanced') NOT NULL,
  plan_json LONGTEXT NOT NULL,
  hit_count INT DEFAULT 0,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  KEY idx_hash (user_profile_hash),
  KEY idx_body_type_focus (body_type, primary_focus)
);
