-- Video Library
-- Add columns to exercises table for video library support

-- These columns may or may not exist, so we'll add them and ignore errors if they do

ALTER TABLE exercises ADD description TEXT;
ALTER TABLE exercises ADD muscle_group VARCHAR(100);

CREATE TABLE IF NOT EXISTS exercise_videos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    exercise_id INT NOT NULL,
    title VARCHAR(255) NOT NULL,
    video_url VARCHAR(500) NOT NULL,
    thumbnail_url VARCHAR(500),
    duration_seconds INT,
    description TEXT,
    common_mistakes TEXT,
    form_tips TEXT,
    difficulty_level ENUM('beginner', 'intermediate', 'advanced') DEFAULT 'intermediate',
    views INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (exercise_id) REFERENCES exercises(id) ON DELETE CASCADE,
    INDEX idx_exercise (exercise_id)
);

-- Insert sample exercises with video data (only add new columns if needed)
INSERT IGNORE INTO exercises (name, primary_muscle, difficulty) VALUES
('Bench Press', 'Chest', 'intermediate'),
('Squat', 'Legs', 'intermediate'),
('Deadlift', 'Back', 'advanced'),
('Push-up', 'Chest', 'beginner'),
('Pull-up', 'Back', 'intermediate'),
('Shoulder Press', 'Shoulders', 'intermediate'),
('Barbell Row', 'Back', 'intermediate'),
('Bicep Curl', 'Biceps', 'beginner'),
('Tricep Dip', 'Triceps', 'beginner'),
('Leg Press', 'Legs', 'beginner');

-- Update exercises with description and muscle_group
UPDATE exercises SET description = 'Compound chest exercise performed on a flat bench', muscle_group = 'Chest' WHERE name = 'Bench Press';
UPDATE exercises SET description = 'Compound leg exercise targeting quads, hamstrings, and glutes', muscle_group = 'Legs' WHERE name = 'Squat';
UPDATE exercises SET description = 'Compound full-body exercise', muscle_group = 'Full Body' WHERE name = 'Deadlift';
UPDATE exercises SET description = 'Bodyweight chest and triceps exercise', muscle_group = 'Chest' WHERE name = 'Push-up';
UPDATE exercises SET description = 'Bodyweight back and bicep exercise', muscle_group = 'Back' WHERE name = 'Pull-up';
UPDATE exercises SET description = 'Compound shoulder exercise', muscle_group = 'Shoulders' WHERE name = 'Shoulder Press';
UPDATE exercises SET description = 'Compound back exercise', muscle_group = 'Back' WHERE name = 'Barbell Row';
UPDATE exercises SET description = 'Isolation arm exercise', muscle_group = 'Arms' WHERE name = 'Bicep Curl';
UPDATE exercises SET description = 'Compound triceps exercise', muscle_group = 'Arms' WHERE name = 'Tricep Dip';
UPDATE exercises SET description = 'Compound leg exercise on a machine', muscle_group = 'Legs' WHERE name = 'Leg Press';

INSERT INTO exercise_videos (exercise_id, title, video_url, thumbnail_url, duration_seconds, description, common_mistakes, form_tips, difficulty_level) VALUES
(1, 'How to Bench Press Correctly', 'https://www.youtube.com/embed/rT7DgCr-3pg', 'https://i.ytimg.com/vi/rT7DgCr-3pg/default.jpg', 420, 'Complete guide to proper bench press form for maximum chest activation and safety.', 'Bouncing the bar off your chest, flaring elbows too wide, lowering bar to neck instead of chest, using too much leg drive', 'Keep elbows at 45 degrees, lower bar to mid-chest, maintain tight shoulder blades, use leg drive, control the descent', 'intermediate'),
(2, 'Perfect Squat Form Guide', 'https://www.youtube.com/embed/xwrCwvj3l2Q', 'https://i.ytimg.com/vi/xwrCwvj3l2Q/default.jpg', 480, 'Master proper squat technique for strength and injury prevention.', 'Knees caving inward, heels coming off ground, leaning too far forward, going too heavy too fast, incomplete range of motion', 'Keep knees tracking over toes, maintain neutral spine, sit back into hips, keep chest up, go to parallel or below', 'intermediate'),
(3, 'Deadlift Form Masterclass', 'https://www.youtube.com/embed/VL5Ab2XrLic', 'https://i.ytimg.com/vi/VL5Ab2XrLic/default.jpg', 600, 'Complete deadlift guide covering conventional, sumo, and Romanian variations.', 'Rounding lower back, bar drifting away from body, not engaging lats, jerking the weight, lifting hips too early', 'Keep bar close to body, brace core before lift, engage lats, drive through heels, maintain neutral spine throughout', 'advanced'),
(4, 'Push-ups for Beginners', 'https://www.youtube.com/embed/IODxDxX7oi4', 'https://i.ytimg.com/vi/IODxDxX7oi4/default.jpg', 300, 'Learn proper push-up form with progressions for all fitness levels.', 'Elbows flaring too wide, sagging hips, neck craning forward, hands too narrow, not getting full range of motion', 'Keep elbows at 45 degrees, maintain straight line from head to heels, lower chest to hands, maintain core tension', 'beginner'),
(5, 'How to Do Your First Pull-up', 'https://www.youtube.com/embed/p4zVDXhKAYE', 'https://i.ytimg.com/vi/p4zVDXhKAYE/default.jpg', 450, 'Beginner-friendly guide to building pull-up strength and mastering the movement.', 'Using momentum from lower body, not getting full extension at bottom, elbows not at sides, not pulling to chest', 'Engage lats first, pull elbows down and back, bring chest to bar, maintain control both up and down', 'intermediate'),
(6, 'Shoulder Press Technique', 'https://www.youtube.com/embed/bfPfBc2j5AQ', 'https://i.ytimg.com/vi/bfPfBc2j5AQ/default.jpg', 380, 'Master the overhead press for shoulder strength and stability.', 'Arching lower back excessively, pressing in front of face instead of over head, flaring elbows too wide, not engaging core', 'Keep bar over mid-foot, brace core, press straight up, keep elbows slightly forward, maintain neutral wrist', 'intermediate'),
(7, 'Barbell Row Form Guide', 'https://www.youtube.com/embed/eQvfvGKwFS0', 'https://i.ytimg.com/vi/eQvfvGKwFS0/default.jpg', 420, 'Learn proper barbell row technique for a strong back.', 'Rounding your back, elbows flaring too far out, not pulling high enough, moving hips, not engaging lats', 'Keep chest up, pull bar to lower chest, keep elbows at 45 degrees, engage lats throughout movement', 'intermediate'),
(8, 'Barbell Curl Form', 'https://www.youtube.com/embed/9Fa-MJ8K8zQ', 'https://i.ytimg.com/vi/9Fa-MJ8K8zQ/default.jpg', 240, 'Perfect your barbell curl for bigger biceps.', 'Swinging the weight, elbows moving forward, not getting full range of motion, too much weight', 'Keep elbows pinned at sides, control the weight down, squeeze at the top, avoid momentum', 'beginner'),
(9, 'Tricep Dips Tutorial', 'https://www.youtube.com/embed/-v6PJvnJC_g', 'https://i.ytimg.com/vi/-v6PJvnJC_g/default.jpg', 320, 'Master tricep dips for arm and chest strength.', 'Elbows flaring out, leaning too far forward, going down too far, momentum from legs, incomplete range of motion', 'Keep elbows tucked, lower slowly, go until upper arms parallel to ground, maintain upright posture, control the movement', 'beginner'),
(10, 'Leg Press Technique', 'https://www.youtube.com/embed/v7c2K6rIFOo', 'https://i.ytimg.com/vi/v7c2K6rIFOo/default.jpg', 380, 'Learn proper leg press form for safe and effective leg training.', 'Knees caving inward, locking knees out completely, going too heavy, not getting full range of motion, feet too narrow', 'Keep feet at shoulder width, lower until knees at 90 degrees, dont lock knees, maintain even weight distribution', 'beginner')
ON DUPLICATE KEY UPDATE id=id;
