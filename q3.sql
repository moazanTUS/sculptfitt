USE sculpfit;

-- Days inside each plan
CREATE TABLE IF NOT EXISTS workout_days (
  id INT AUTO_INCREMENT PRIMARY KEY,
  plan_id INT NOT NULL,
  day_number INT NOT NULL,
  title VARCHAR(100) NULL,
  UNIQUE KEY uq_plan_day (plan_id, day_number),
  FOREIGN KEY (plan_id) REFERENCES workout_plans(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- Master exercise list
CREATE TABLE IF NOT EXISTS exercises (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(120) NOT NULL,
  muscle_group VARCHAR(30) NOT NULL,
  UNIQUE KEY uq_exercise_name (name)
) ENGINE=InnoDB;

-- Items for each day (exercise + sets/reps/rest)
CREATE TABLE IF NOT EXISTS workout_day_items (
  id INT AUTO_INCREMENT PRIMARY KEY,
  day_id INT NOT NULL,
  exercise_id INT NOT NULL,
  sets INT NOT NULL,
  reps VARCHAR(20) NOT NULL,
  rest_seconds INT NOT NULL,
  position INT NOT NULL DEFAULT 1,
  FOREIGN KEY (day_id) REFERENCES workout_days(id) ON DELETE CASCADE,
  FOREIGN KEY (exercise_id) REFERENCES exercises(id) ON DELETE RESTRICT,
  INDEX (day_id),
  INDEX (exercise_id)
) ENGINE=InnoDB;






