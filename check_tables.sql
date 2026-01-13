-- Check table structures
DESCRIBE user_saved_plans;
DESCRIBE user_workout_day_items;
DESCRIBE user_workout_days;
DESCRIBE user_workout_plans;

-- Check row counts
SELECT 'user_saved_plans' as table_name, COUNT(*) as row_count FROM user_saved_plans
UNION ALL
SELECT 'user_workout_day_items', COUNT(*) FROM user_workout_day_items
UNION ALL
SELECT 'user_workout_days', COUNT(*) FROM user_workout_days
UNION ALL
SELECT 'user_workout_plans', COUNT(*) FROM user_workout_plans;

-- Show sample data from user_workout_day_items
SELECT 'Sample user_workout_day_items:' as info;
SELECT * FROM user_workout_day_items LIMIT 3;
