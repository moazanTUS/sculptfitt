USE sculpfit;

CREATE TABLE IF NOT EXISTS user_saved_plans (
  id INT AUTO_INCREMENT PRIMARY KEY,
  clerk_user_id VARCHAR(255) NOT NULL,
  plan_id INT NOT NULL,
  body_type VARCHAR(30),
  focus1 VARCHAR(20),
  focus2 VARCHAR(20),
  focus3 VARCHAR(20),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (plan_id) REFERENCES workout_plans(id) ON DELETE CASCADE,
  INDEX (clerk_user_id),
  INDEX (created_at)
) ENGINE=InnoDB;
