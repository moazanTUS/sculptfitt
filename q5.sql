-- 005_editable_user_plans.sql
-- User-owned editable plan copies (safe editing)

ALTER TABLE user_saved_plans
  ADD COLUMN user_plan_id INT NULL,
  ADD INDEX idx_user_saved_plans_user_plan_id (user_plan_id);

-- Editable plan header
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

-- Editable days
CREATE TABLE IF NOT EXISTS user_workout_days (
  id INT AUTO_INCREMENT PRIMARY KEY,
  user_plan_id INT NOT NULL,
  day_number INT NOT NULL,
  title VARCHAR(255) NOT NULL DEFAULT '',
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

  UNIQUE KEY uq_uwd_plan_day (user_plan_id, day_number),
  INDEX idx_uwd_plan (user_plan_id),

  CONSTRAINT fk_uwd_plan
    FOREIGN KEY (user_plan_id) REFERENCES user_workout_plans(id)
    ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Editable day items
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

  CONSTRAINT fk_uwdi_day
    FOREIGN KEY (user_day_id) REFERENCES user_workout_days(id)
    ON DELETE CASCADE,

  CONSTRAINT fk_uwdi_ex
    FOREIGN KEY (exercise_id) REFERENCES exercises(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Link user_saved_plans -> editable copy
ALTER TABLE user_saved_plans
  ADD CONSTRAINT fk_user_saved_plans_user_plan
  FOREIGN KEY (user_plan_id) REFERENCES user_workout_plans(id)
  ON DELETE SET NULL;


show tables;