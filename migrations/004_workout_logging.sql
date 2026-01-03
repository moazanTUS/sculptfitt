-- Workout Logging Tables
-- Track completed workouts and exercise performance

CREATE TABLE IF NOT EXISTS workout_sessions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    clerk_user_id VARCHAR(255) NOT NULL,
    workout_plan_id INT NOT NULL,
    workout_plan_type ENUM('custom', 'ai', 'saved') DEFAULT 'ai',
    workout_name VARCHAR(255) NOT NULL,
    day_number INT DEFAULT 1,
    session_date DATE NOT NULL,
    completed_at TIMESTAMP NULL,
    duration_minutes INT DEFAULT NULL,
    notes TEXT,
    rating INT DEFAULT NULL CHECK (rating >= 1 AND rating <= 5),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_user_date (clerk_user_id, session_date),
    INDEX idx_workout_plan (workout_plan_id, workout_plan_type)
);

CREATE TABLE IF NOT EXISTS workout_session_exercises (
    id INT AUTO_INCREMENT PRIMARY KEY,
    session_id INT NOT NULL,
    exercise_id INT,
    exercise_name VARCHAR(255) NOT NULL,
    planned_sets INT,
    planned_reps VARCHAR(50),
    planned_rest_seconds INT DEFAULT 60,
    completed_sets INT DEFAULT 0,
    completed_reps VARCHAR(50),
    weight_used DECIMAL(8,2) DEFAULT NULL,
    rpe INT DEFAULT NULL CHECK (rpe >= 1 AND rpe <= 10),
    notes TEXT,
    position INT DEFAULT 1,
    completed_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES workout_sessions(id) ON DELETE CASCADE,
    FOREIGN KEY (exercise_id) REFERENCES exercises(id) ON DELETE SET NULL,
    INDEX idx_session (session_id)
);

CREATE TABLE IF NOT EXISTS workout_progress (
    id INT AUTO_INCREMENT PRIMARY KEY,
    clerk_user_id VARCHAR(255) NOT NULL,
    exercise_id INT,
    exercise_name VARCHAR(255) NOT NULL,
    personal_record_weight DECIMAL(8,2) DEFAULT NULL,
    personal_record_reps INT DEFAULT NULL,
    personal_record_date DATE,
    total_times_completed INT DEFAULT 0,
    last_completed_date DATE,
    average_rpe DECIMAL(3,1) DEFAULT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (exercise_id) REFERENCES exercises(id) ON DELETE SET NULL,
    UNIQUE KEY unique_user_exercise (clerk_user_id, exercise_id)
);
