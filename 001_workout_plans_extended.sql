-- ========================================
-- Extended Workout Plans Schema
-- Support for 3-day and 5-day split plans
-- ========================================

USE sculpfit;

-- Ensure all existing plans have days_per_week set to 3 if null
UPDATE workout_plans SET days_per_week = 3 WHERE id > 0 AND (days_per_week IS NULL OR days_per_week = 0);

-- Add new 5-day plans for each focus area
INSERT IGNORE INTO workout_plans (name, days_per_week, primary_focus) VALUES
('Shoulder Focus Plan (5-day)', 5, 'shoulders'),
('Chest Focus Plan (5-day)',    5, 'chest'),
('Back Focus Plan (5-day)',     5, 'back'),
('Core Focus Plan (5-day)',     5, 'core'),
('Arms Focus Plan (5-day)',     5, 'arms'),
('Legs Focus Plan (5-day)',     5, 'legs'),
('Glutes Focus Plan (5-day)',   5, 'glutes');
