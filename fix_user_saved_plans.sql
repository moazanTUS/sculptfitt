-- Disable foreign key checks to allow dropping table
SET FOREIGN_KEY_CHECKS = 0;

-- Drop the corrupted table
DROP TABLE IF EXISTS user_saved_plans;

-- Recreate with correct structure
CREATE TABLE user_saved_plans (
  id INT AUTO_INCREMENT PRIMARY KEY,
  clerk_user_id VARCHAR(255) NOT NULL,
  plan_id INT NOT NULL,
  saved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  user_plan_id INT NULL,
  body_type VARCHAR(100),
  focus1 VARCHAR(100),
  focus2 VARCHAR(100),
  focus3 VARCHAR(100),
  KEY idx_user (clerk_user_id),
  KEY idx_plan (plan_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Re-enable foreign key checks
SET FOREIGN_KEY_CHECKS = 1;

-- Verify the structure
DESCRIBE user_saved_plans;
