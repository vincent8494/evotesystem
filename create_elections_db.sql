-- Create the database schema for the electoral system

-- Enable foreign key constraints
PRAGMA foreign_keys = ON;

-- Create tables
CREATE TABLE IF NOT EXISTS tbl_stream (
    stream_id INTEGER PRIMARY KEY AUTOINCREMENT,
    stream_name TEXT NOT NULL,
    stream_code TEXT UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS tbl_teacher (
    teacher_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    gender TEXT CHECK(gender IN ('male', 'female')),
    tsc_number TEXT UNIQUE
);

CREATE TABLE IF NOT EXISTS tbl_class (
    class_id INTEGER PRIMARY KEY AUTOINCREMENT,
    class_name TEXT NOT NULL,
    stream_id INTEGER,
    teacher_id INTEGER,
    FOREIGN KEY (stream_id) REFERENCES tbl_stream(stream_id),
    FOREIGN KEY (teacher_id) REFERENCES tbl_teacher(teacher_id)
);

CREATE TABLE IF NOT EXISTS tbl_electoral_post (
    post_id INTEGER PRIMARY KEY AUTOINCREMENT,
    post_name TEXT NOT NULL,
    gender_requirement TEXT CHECK(gender_requirement IN ('male', 'female', 'any')),
    level TEXT CHECK(level IN ('school', 'class', 'form'))
);

CREATE TABLE IF NOT EXISTS tbl_voters (
    voter_id INTEGER PRIMARY KEY AUTOINCREMENT,
    admission_no TEXT UNIQUE NOT NULL,
    full_name TEXT NOT NULL,
    gender TEXT CHECK(gender IN ('male', 'female')),
    class_id INTEGER,
    stream_id INTEGER,
    FOREIGN KEY (class_id) REFERENCES tbl_class(class_id),
    FOREIGN KEY (stream_id) REFERENCES tbl_stream(stream_id)
);

CREATE TABLE IF NOT EXISTS tbl_contestants (
    contestant_id INTEGER PRIMARY KEY AUTOINCREMENT,
    contestant_number TEXT NOT NULL,
    full_name TEXT NOT NULL,
    gender TEXT CHECK(gender IN ('male', 'female')),
    class_id INTEGER,
    stream_id INTEGER,
    post_id INTEGER,
    level TEXT CHECK(level IN ('school', 'class', 'form')),
    FOREIGN KEY (class_id) REFERENCES tbl_class(class_id),
    FOREIGN KEY (stream_id) REFERENCES tbl_stream(stream_id),
    FOREIGN KEY (post_id) REFERENCES tbl_electoral_post(post_id)
);

CREATE TABLE IF NOT EXISTS tbl_results (
    result_id INTEGER PRIMARY KEY AUTOINCREMENT,
    contestant_id INTEGER,
    voter_id INTEGER,
    post_id INTEGER,
    class_id INTEGER,
    stream_id INTEGER,
    valid_votes INTEGER DEFAULT 0,
    spoilt_votes INTEGER DEFAULT 0,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (contestant_id) REFERENCES tbl_contestants(contestant_id),
    FOREIGN KEY (voter_id) REFERENCES tbl_voters(voter_id),
    FOREIGN KEY (post_id) REFERENCES tbl_electoral_post(post_id),
    FOREIGN KEY (class_id) REFERENCES tbl_class(class_id),
    FOREIGN KEY (stream_id) REFERENCES tbl_stream(stream_id)
);

CREATE TABLE IF NOT EXISTS tbl_roles (
    role_id INTEGER PRIMARY KEY AUTOINCREMENT,
    role_name TEXT UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS tbl_users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role_id INTEGER,
    FOREIGN KEY (role_id) REFERENCES tbl_roles(role_id)
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_voters_class ON tbl_voters(class_id);
CREATE INDEX IF NOT EXISTS idx_voters_stream ON tbl_voters(stream_id);
CREATE INDEX IF NOT EXISTS idx_contestants_post ON tbl_contestants(post_id);
CREATE INDEX IF NOT EXISTS idx_results_contestant ON tbl_results(contestant_id);
CREATE INDEX IF NOT EXISTS idx_results_post ON tbl_results(post_id);

-- Insert default roles
INSERT OR IGNORE INTO tbl_roles (role_id, role_name) VALUES 
    (1, 'admin'),
    (2, 'officer'),
    (3, 'voter');

-- Insert admin user (default password: admin123)
INSERT OR IGNORE INTO tbl_users (username, password_hash, role_id) VALUES 
    ('admin', '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW', 1);
