-- skills table (updated with skill_type)
CREATE TABLE skills (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    skill_name VARCHAR(100) NOT NULL,
    skill_type ENUM('teach', 'learn') NOT NULL DEFAULT 'teach',
    skill_level ENUM('beginner', 'intermediate', 'advanced') NOT NULL,
    description TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;