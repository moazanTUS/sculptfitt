-- Migration: Add Custom Workouts Tables
-- Date: 2024
-- Description: Creates tables for user-created custom workout functionality

-- ============================================
-- Custom User-Created Workouts
-- ============================================
CREATE TABLE IF NOT EXISTS custom_workouts (
  id INT AUTO_INCREMENT PRIMARY KEY,
  clerk_user_id VARCHAR(255) NOT NULL,
  name VARCHAR(255) NOT NULL,
  description TEXT,
  days_per_week INT NOT NULL DEFAULT 3,
  difficulty ENUM('beginner', 'intermediate', 'advanced') NOT NULL DEFAULT 'beginner',
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_user (clerk_user_id),
  INDEX idx_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================
-- Custom Workout Days
-- ============================================
CREATE TABLE IF NOT EXISTS custom_workout_days (
  id INT AUTO_INCREMENT PRIMARY KEY,
  custom_workout_id INT NOT NULL,
  day_number INT NOT NULL,
  title VARCHAR(255) NOT NULL DEFAULT 'Day',
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY uq_workout_day (custom_workout_id, day_number),
  INDEX idx_workout (custom_workout_id),
  CONSTRAINT fk_cwd_workout
    FOREIGN KEY (custom_workout_id) REFERENCES custom_workouts(id)
    ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================
-- Custom Workout Exercises
-- ============================================
CREATE TABLE IF NOT EXISTS custom_workout_exercises (
  id INT AUTO_INCREMENT PRIMARY KEY,
  custom_day_id INT NOT NULL,
  exercise_id INT NULL,
  exercise_name VARCHAR(255) NOT NULL,
  sets INT NOT NULL DEFAULT 3,
  reps VARCHAR(50) NOT NULL DEFAULT '8-12',
  rest_seconds INT NOT NULL DEFAULT 60,
  notes VARCHAR(255),
  position INT NOT NULL DEFAULT 1,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_day (custom_day_id),
  INDEX idx_exercise (exercise_id),
  INDEX idx_position (position),
  CONSTRAINT fk_cwe_day
    FOREIGN KEY (custom_day_id) REFERENCES custom_workout_days(id)
    ON DELETE CASCADE,
  CONSTRAINT fk_cwe_exercise
    FOREIGN KEY (exercise_id) REFERENCES exercises(id)
    ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
