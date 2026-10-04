CREATE DATABASE IF NOT EXISTS studyos CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE studyos;
CREATE TABLE IF NOT EXISTS subjects (
 subject_id INT AUTO_INCREMENT PRIMARY KEY,
 name VARCHAR(120) NOT NULL UNIQUE,
 description TEXT,
 color VARCHAR(20) DEFAULT '#4C78A8',
 created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS topics (
 topic_id INT AUTO_INCREMENT PRIMARY KEY,
 subject_id INT NOT NULL,
 parent_topic_id INT NULL,
 name VARCHAR(160) NOT NULL,
 status ENUM('Not started','In progress','Completed') NOT NULL DEFAULT 'Not started',
 estimated_minutes INT NOT NULL DEFAULT 45,
 UNIQUE KEY uq_topic (subject_id,name),
 FOREIGN KEY (subject_id) REFERENCES subjects(subject_id) ON DELETE CASCADE,
 FOREIGN KEY (parent_topic_id) REFERENCES topics(topic_id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS topic_prerequisites (
 topic_id INT NOT NULL,
 prerequisite_topic_id INT NOT NULL,
 PRIMARY KEY(topic_id,prerequisite_topic_id),
 FOREIGN KEY(topic_id) REFERENCES topics(topic_id) ON DELETE CASCADE,
 FOREIGN KEY(prerequisite_topic_id) REFERENCES topics(topic_id) ON DELETE CASCADE,
 CHECK (topic_id <> prerequisite_topic_id)
);
CREATE TABLE IF NOT EXISTS tasks (
 task_id INT AUTO_INCREMENT PRIMARY KEY,
 title VARCHAR(200) NOT NULL,
 subject_id INT NULL,
 due_at DATETIME NULL,
 priority ENUM('Low','Medium','High') NOT NULL DEFAULT 'Medium',
 status ENUM('To do','In progress','Done') NOT NULL DEFAULT 'To do',
 notes TEXT,
 created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
 FOREIGN KEY(subject_id) REFERENCES subjects(subject_id) ON DELETE SET NULL
);
CREATE TABLE IF NOT EXISTS exams (
 exam_id INT AUTO_INCREMENT PRIMARY KEY,
 subject_id INT NOT NULL,
 title VARCHAR(200) NOT NULL,
 starts_at DATETIME NOT NULL,
 location VARCHAR(200),
 notes TEXT,
 FOREIGN KEY(subject_id) REFERENCES subjects(subject_id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS routine_blocks (
 routine_id INT AUTO_INCREMENT PRIMARY KEY,
 weekday TINYINT NOT NULL COMMENT 'Monday=0 to Sunday=6',
 title VARCHAR(120) NOT NULL,
 category ENUM('Sleep','Meal','Snack','Break','College','Tuition','Exercise','Nap','Personal','Other') NOT NULL DEFAULT 'Other',
 starts_at TIME NOT NULL,
 ends_at TIME NOT NULL,
 enabled BOOLEAN NOT NULL DEFAULT TRUE
);
CREATE TABLE IF NOT EXISTS events (
 event_id INT AUTO_INCREMENT PRIMARY KEY,
 title VARCHAR(200) NOT NULL,
 category ENUM('College','Tuition','Commute','Going out','Appointment','Exercise','Personal','Other') NOT NULL DEFAULT 'Other',
 starts_at DATETIME NOT NULL,
 ends_at DATETIME NOT NULL,
 location VARCHAR(200),
 notes TEXT
);
CREATE TABLE IF NOT EXISTS study_sessions (
 session_id INT AUTO_INCREMENT PRIMARY KEY,
 title VARCHAR(200) NOT NULL,
 topic_id INT NULL,
 task_id INT NULL,
 starts_at DATETIME NOT NULL,
 ends_at DATETIME NOT NULL,
 status ENUM('Planned','Done','Skipped') NOT NULL DEFAULT 'Planned',
 FOREIGN KEY(topic_id) REFERENCES topics(topic_id) ON DELETE SET NULL,
 FOREIGN KEY(task_id) REFERENCES tasks(task_id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS daily_checkins (
 check_date DATE PRIMARY KEY,
 available_minutes INT NOT NULL DEFAULT 0,
 changes_note TEXT,
 reflection TEXT,
 updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
