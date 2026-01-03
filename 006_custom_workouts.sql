-- Custom User-Created Workouts
CREATE TABLE IF NOT EXISTS custom_workouts (
  id INT AUTO_INCREMENT PRIMARY KEY,
  clerk_user_id VARCHAR(255) NOT NULL,
  name VARCHAR(255) NOT NULL,
  description TEXT,
  days_per_week INT DEFAULT 3,
  difficulty ENUM('beginner', 'intermediate', 'advanced') DEFAULT 'beginner',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_user (clerk_user_id),
  INDEX idx_created (created_at)
);

-- Days in custom workouts
CREATE TABLE IF NOT EXISTS custom_workout_days (
  id INT AUTO_INCREMENT PRIMARY KEY,
  custom_workout_id INT NOT NULL,
  day_number INT NOT NULL,
  title VARCHAR(100),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (custom_workout_id) REFERENCES custom_workouts(id) ON DELETE CASCADE,
  INDEX idx_workout (custom_workout_id)
);

-- Exercises in custom workout days
CREATE TABLE IF NOT EXISTS custom_workout_exercises (
  id INT AUTO_INCREMENT PRIMARY KEY,
  custom_day_id INT NOT NULL,
  exercise_id INT,
  exercise_name VARCHAR(100) NOT NULL,
  sets INT DEFAULT 3,
  reps VARCHAR(50) DEFAULT '8-12',
  rest_seconds INT DEFAULT 60,
  notes TEXT,
  position INT DEFAULT 0,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (custom_day_id) REFERENCES custom_workout_days(id) ON DELETE CASCADE,
  FOREIGN KEY (exercise_id) REFERENCES exercises(id),
  INDEX idx_day (custom_day_id)
);
