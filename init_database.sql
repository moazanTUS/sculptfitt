-- Complete Sculpt Fitness Database Schema
-- Run this on your Railway MariaDB to initialize all tables

-- ============================================
-- Exercises Library
-- ============================================
CREATE TABLE IF NOT EXISTS exercises (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(100) NOT NULL,
  primary_muscle VARCHAR(50) NOT NULL,
  secondary_muscles JSON,
  difficulty ENUM('beginner', 'intermediate', 'advanced') NOT NULL,
  equipment VARCHAR(100),
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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================
-- Pre-built Workout Plans
-- ============================================
CREATE TABLE IF NOT EXISTS workout_plans (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(255) NOT NULL,
  description TEXT,
  body_type ENUM('ectomorph', 'mesomorph', 'endomorph'),
  primary_focus VARCHAR(100),
  focus VARCHAR(100),
  difficulty ENUM('beginner', 'intermediate', 'advanced'),
  days_per_week INT NOT NULL DEFAULT 3,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  KEY idx_body_focus (body_type, primary_focus)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================
-- Plan Exercises (Pre-built)
-- ============================================
CREATE TABLE IF NOT EXISTS plan_exercises (
  id INT AUTO_INCREMENT PRIMARY KEY,
  plan_id INT NOT NULL,
  day_number INT NOT NULL,
  exercise_id INT NOT NULL,
  position INT NOT NULL DEFAULT 1,
  sets INT NOT NULL DEFAULT 3,
  reps VARCHAR(50) NOT NULL DEFAULT '8-12',
  rest_seconds INT NOT NULL DEFAULT 60,
  notes VARCHAR(255),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  KEY idx_plan (plan_id),
  KEY idx_exercise (exercise_id),
  CONSTRAINT fk_pe_plan FOREIGN KEY (plan_id) REFERENCES workout_plans(id) ON DELETE CASCADE,
  CONSTRAINT fk_pe_exercise FOREIGN KEY (exercise_id) REFERENCES exercises(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================
-- User Saved Plans (from Pre-built Plans)
-- ============================================
CREATE TABLE IF NOT EXISTS user_saved_plans (
  id INT AUTO_INCREMENT PRIMARY KEY,
  clerk_user_id VARCHAR(255) NOT NULL,
  plan_id INT NOT NULL,
  saved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  user_plan_id INT NULL,
  KEY idx_user (clerk_user_id),
  KEY idx_plan (plan_id),
  CONSTRAINT fk_usp_plan FOREIGN KEY (plan_id) REFERENCES workout_plans(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================
-- User Editable Plans
-- ============================================
CREATE TABLE IF NOT EXISTS user_workout_plans (
  id INT AUTO_INCREMENT PRIMARY KEY,
  clerk_user_id VARCHAR(255) NOT NULL,
  source_plan_id INT NULL,
  name VARCHAR(255) NOT NULL,
  days_per_week INT NOT NULL DEFAULT 3,
  primary_focus VARCHAR(255) NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_uwp_user (clerk_user_id),
  INDEX idx_uwp_source (source_plan_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================
-- User Editable Workout Days
-- ============================================
CREATE TABLE IF NOT EXISTS user_workout_days (
  id INT AUTO_INCREMENT PRIMARY KEY,
  user_plan_id INT NOT NULL,
  day_number INT NOT NULL,
  title VARCHAR(255) NOT NULL DEFAULT '',
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY uq_uwd_plan_day (user_plan_id, day_number),
  INDEX idx_uwd_plan (user_plan_id),
  CONSTRAINT fk_uwd_plan FOREIGN KEY (user_plan_id) REFERENCES user_workout_plans(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================
-- User Editable Day Items
-- ============================================
CREATE TABLE IF NOT EXISTS user_workout_day_items (
  id INT AUTO_INCREMENT PRIMARY KEY,
  user_day_id INT NOT NULL,
  exercise_id INT NOT NULL,
  sets INT NOT NULL DEFAULT 3,
  reps VARCHAR(50) NOT NULL DEFAULT '8-12',
  rest_seconds INT NOT NULL DEFAULT 60,
  position INT NOT NULL DEFAULT 1,
  notes VARCHAR(255) NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_uwdi_day (user_day_id),
  INDEX idx_uwdi_ex (exercise_id),
  CONSTRAINT fk_uwdi_day FOREIGN KEY (user_day_id) REFERENCES user_workout_days(id) ON DELETE CASCADE,
  CONSTRAINT fk_uwdi_ex FOREIGN KEY (exercise_id) REFERENCES exercises(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================
-- Plan Cache (for performance)
-- ============================================
CREATE TABLE IF NOT EXISTS plan_cache (
  id INT AUTO_INCREMENT PRIMARY KEY,
  user_profile_hash VARCHAR(255) UNIQUE NOT NULL,
  body_type ENUM('ectomorph', 'mesomorph', 'endomorph') NOT NULL,
  focus VARCHAR(100) NOT NULL,
  cached_plan JSON NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  expires_at TIMESTAMP NULL,
  KEY idx_profile_hash (user_profile_hash)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================
-- Insert Sample Exercises
-- ============================================
INSERT INTO exercises (name, primary_muscle, secondary_muscles, difficulty, equipment, instructions, form_cues) VALUES
-- CHEST
('Barbell Bench Press', 'chest', '["triceps", "shoulders"]', 'intermediate', 'barbell', 'Lie flat on bench, grip shoulder-width, lower to chest, press up', 'Keep elbows 45 degrees, full chest contact'),
('Barbell Bench Press', 'chest', '["triceps", "shoulders"]', 'advanced', 'barbell', 'Lie flat on bench, grip shoulder-width, lower to chest, press up', 'Keep elbows 45 degrees, full chest contact'),
('Dumbbell Bench Press', 'chest', '["triceps", "shoulders"]', 'beginner', 'dumbbell', 'Lie flat, press dumbbells up from chest level', 'Full range of motion, controlled descent'),
('Incline Dumbbell Press', 'chest', '["shoulders", "triceps"]', 'intermediate', 'dumbbell', 'Sit on incline bench, press dumbbells up', 'Controlled movement, avoid back arch'),
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
