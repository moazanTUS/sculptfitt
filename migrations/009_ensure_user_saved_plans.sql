-- Ensure user_saved_plans table exists and has correct structure
CREATE TABLE IF NOT EXISTS user_saved_plans (
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
  KEY idx_plan (plan_id),
  CONSTRAINT fk_usp_plan FOREIGN KEY (plan_id) REFERENCES workout_plans(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Check if columns exist and add them if missing
ALTER TABLE user_saved_plans 
ADD COLUMN IF NOT EXISTS saved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
ADD COLUMN IF NOT EXISTS user_plan_id INT NULL,
ADD COLUMN IF NOT EXISTS body_type VARCHAR(100),
ADD COLUMN IF NOT EXISTS focus1 VARCHAR(100),
ADD COLUMN IF NOT EXISTS focus2 VARCHAR(100),
ADD COLUMN IF NOT EXISTS focus3 VARCHAR(100);

-- Add indexes if they don't exist
ALTER TABLE user_saved_plans ADD INDEX IF NOT EXISTS idx_user (clerk_user_id);
ALTER TABLE user_saved_plans ADD INDEX IF NOT EXISTS idx_plan (plan_id);
