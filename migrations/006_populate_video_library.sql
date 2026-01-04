

-- Populate YouTube videos for existing exercises
-- These use YouTube embed URLs that work with iframe

-- Insert YouTube tutorial videos for existing exercises
INSERT IGNORE INTO exercise_videos (exercise_id, title, video_url, thumbnail_url, duration_seconds, description, common_mistakes, form_tips, difficulty_level) 
SELECT id, 'Proper Bench Press Form', 'https://www.youtube.com/embed/rT7DgCr-3pg', 'https://i.ytimg.com/vi/rT7DgCr-3pg/default.jpg', 420, 
'Complete guide to proper bench press form for maximum chest activation and safety by Jeff Nippard.', 
'Bouncing the bar off your chest, flaring elbows too wide, lowering bar to neck instead of chest, using too much leg drive', 
'Keep elbows at 45 degrees, lower bar to mid-chest, maintain tight shoulder blades, use leg drive, control the descent', 
'intermediate' 
FROM exercises WHERE name = 'Bench Press' LIMIT 1;

INSERT IGNORE INTO exercise_videos (exercise_id, title, video_url, thumbnail_url, duration_seconds, description, common_mistakes, form_tips, difficulty_level) 
SELECT id, 'Squat Form Mastery', 'https://www.youtube.com/embed/xwrCwvj3l2Q', 'https://i.ytimg.com/vi/xwrCwvj3l2Q/default.jpg', 480, 
'Master proper squat technique for strength and injury prevention.', 
'Knees caving inward, heels coming off ground, leaning too far forward, going too heavy too fast, incomplete range of motion', 
'Keep knees tracking over toes, maintain neutral spine, sit back into hips, keep chest up, go to parallel or below', 
'intermediate' 
FROM exercises WHERE name = 'Squat' LIMIT 1;

INSERT IGNORE INTO exercise_videos (exercise_id, title, video_url, thumbnail_url, duration_seconds, description, common_mistakes, form_tips, difficulty_level) 
SELECT id, 'Deadlift Form Guide', 'https://www.youtube.com/embed/VL5Ab2XrLic', 'https://i.ytimg.com/vi/VL5Ab2XrLic/default.jpg', 600, 
'Complete deadlift guide by Athlean-X covering conventional form and safety.', 
'Rounding lower back, bar drifting away from body, not engaging lats, jerking the weight, lifting hips too early', 
'Keep bar close to body, brace core before lift, engage lats, drive through heels, maintain neutral spine throughout', 
'advanced' 
FROM exercises WHERE name = 'Deadlift' LIMIT 1;

INSERT IGNORE INTO exercise_videos (exercise_id, title, video_url, thumbnail_url, duration_seconds, description, common_mistakes, form_tips, difficulty_level) 
SELECT id, 'Pull-up Progression', 'https://www.youtube.com/embed/p4zVDXhKAYE', 'https://i.ytimg.com/vi/p4zVDXhKAYE/default.jpg', 450, 
'Beginner-friendly guide to building pull-up strength and mastering the movement.', 
'Using momentum from lower body, not getting full extension at bottom, elbows not at sides, not pulling to chest', 
'Engage lats first, pull elbows down and back, bring chest to bar, maintain control both up and down', 
'intermediate' 
FROM exercises WHERE name = 'Pull-up' LIMIT 1;

INSERT IGNORE INTO exercise_videos (exercise_id, title, video_url, thumbnail_url, duration_seconds, description, common_mistakes, form_tips, difficulty_level) 
SELECT id, 'Shoulder Press Form', 'https://www.youtube.com/embed/bfPfBc2j5AQ', 'https://i.ytimg.com/vi/bfPfBc2j5AQ/default.jpg', 380, 
'Master the overhead press for shoulder strength and stability.', 
'Arching lower back excessively, pressing in front of face instead of over head, flaring elbows too wide, not engaging core', 
'Keep bar over mid-foot, brace core, press straight up, keep elbows slightly forward, maintain neutral wrist', 
'intermediate' 
FROM exercises WHERE name = 'Shoulder Press' LIMIT 1;

INSERT IGNORE INTO exercise_videos (exercise_id, title, video_url, thumbnail_url, duration_seconds, description, common_mistakes, form_tips, difficulty_level) 
SELECT id, 'Barbell Row Technique', 'https://www.youtube.com/embed/eQvfvGKwFS0', 'https://i.ytimg.com/vi/eQvfvGKwFS0/default.jpg', 420, 
'Learn proper barbell row technique for a strong back.', 
'Rounding your back, elbows flaring too far out, not pulling high enough, moving hips, not engaging lats', 
'Keep chest up, pull bar to lower chest, keep elbows at 45 degrees, engage lats throughout movement', 
'intermediate' 
FROM exercises WHERE name = 'Barbell Row' LIMIT 1;

INSERT IGNORE INTO exercise_videos (exercise_id, title, video_url, thumbnail_url, duration_seconds, description, common_mistakes, form_tips, difficulty_level) 
SELECT id, 'Perfect Bicep Curl', 'https://www.youtube.com/embed/9Fa-MJ8K8zQ', 'https://i.ytimg.com/vi/9Fa-MJ8K8zQ/default.jpg', 240, 
'Master the barbell curl for bigger biceps.', 
'Swinging the weight, elbows moving forward, not getting full range of motion, too much weight', 
'Keep elbows pinned at sides, control the weight down, squeeze at the top, avoid momentum', 
'beginner' 
FROM exercises WHERE name = 'Bicep Curl' LIMIT 1;

INSERT IGNORE INTO exercise_videos (exercise_id, title, video_url, thumbnail_url, duration_seconds, description, common_mistakes, form_tips, difficulty_level) 
SELECT id, 'Tricep Dips Guide', 'https://www.youtube.com/embed/-v6PJvnJC_g', 'https://i.ytimg.com/vi/-v6PJvnJC_g/default.jpg', 320, 
'Master tricep dips for arm and chest strength.', 
'Elbows flaring out, leaning too far forward, going down too far, momentum from legs, incomplete range of motion', 
'Keep elbows tucked, lower slowly, go until upper arms parallel to ground, maintain upright posture, control the movement', 
'beginner' 
FROM exercises WHERE name = 'Tricep Dip' LIMIT 1;

INSERT IGNORE INTO exercise_videos (exercise_id, title, video_url, thumbnail_url, duration_seconds, description, common_mistakes, form_tips, difficulty_level) 
SELECT id, 'Leg Press Form', 'https://www.youtube.com/embed/v7c2K6rIFOo', 'https://i.ytimg.com/vi/v7c2K6rIFOo/default.jpg', 380, 
'Learn proper leg press form for safe and effective leg training.', 
'Knees caving inward, locking knees out completely, going too heavy, not getting full range of motion, feet too narrow', 
'Keep feet at shoulder width, lower until knees at 90 degrees, dont lock knees, maintain even weight distribution', 
'beginner' 
FROM exercises WHERE name = 'Leg Press' LIMIT 1;

INSERT IGNORE INTO exercise_videos (exercise_id, title, video_url, thumbnail_url, duration_seconds, description, common_mistakes, form_tips, difficulty_level) 
SELECT id, 'Perfect Push-ups', 'https://www.youtube.com/embed/IODxDxX7oi4', 'https://i.ytimg.com/vi/IODxDxX7oi4/default.jpg', 300, 
'Learn proper push-up form with progressions for all fitness levels.', 
'Elbows flaring too wide, sagging hips, neck craning forward, hands too narrow, not getting full range of motion', 
'Keep elbows at 45 degrees, maintain straight line from head to heels, lower chest to hands, maintain core tension', 
'beginner' 
FROM exercises WHERE name = 'Push-up' LIMIT 1;
