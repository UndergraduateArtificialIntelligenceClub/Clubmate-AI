CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(32) UNIQUE NOT NULL, -- Max username len in discord is 32 I believe
    role INT NOT NULL DEFAULT 1, -- default to pleb user
    discord_id TEXT UNIQUE NOT NULL,
    email TEXT,
    name TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_users_discord_id ON users(discord_id);
CREATE INDEX idx_users_role ON users(role);


CREATE TABLE IF NOT EXISTS meetings (
    id SERIAL PRIMARY KEY,
    organizer_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    start_time TIMESTAMP WITH TIME ZONE NOT NULL,
    end_time TIMESTAMP WITH TIME ZONE NOT NULL,
    location TEXT,
    meeting_link TEXT,
    attendees JSONB DEFAULT '[]',
    google_calendar_event_id VARCHAR(1024), -- "the length of the ID must be between 5 and 1024 characters" refer to https://developers.google.com/workspace/calendar/api/v3/reference/events/insert for the length
    status VARCHAR(20) NOT NULL DEFAULT 'scheduled',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    CONSTRAINT meetings_time_valid CHECK (end_time > start_time)
);


CREATE INDEX idx_meetings_organizer ON meetings(organizer_id);
CREATE INDEX idx_meetings_start_time ON meetings(start_time);
CREATE INDEX idx_meetings_status ON meetings(status);
CREATE INDEX idx_meetings_google_event ON meetings(google_calendar_event_id);


CREATE TABLE IF NOT EXISTS logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    action VARCHAR(50) NOT NULL,
    details JSONB,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    status VARCHAR(20) NOT NULL
);

CREATE INDEX idx_logs_user_id ON logs(user_id);
CREATE INDEX idx_logs_action ON logs(action);
CREATE INDEX idx_logs_timestamp ON logs(timestamp);


-- USERS SEED DATA
INSERT INTO users (username, role, discord_id, email, name)
VALUES
('god', 0, '123456789012345678', 'admin@example.com', 'pleb1'),
('wee', 1, '987654321098765432', 'user1@example.com', 'pleb2'),
('woo', 1, '555555555555555555', 'user2@example.com', 'gary');

-- MEETINGS SEED DATA
INSERT INTO meetings (
    organizer_id, title, description, start_time, end_time,
    location, meeting_link, attendees, google_calendar_event_id, status
)
VALUES
(
    1,
    'Corporate Stuff',
    'yuh',
    NOW() + INTERVAL '1 day',
    NOW() + INTERVAL '1 day 1 hour',
    'Evil Basement',
    NULL,
    '["user1@example.com", "user2@example.com"]'::jsonb,
    'google_event_123',
    'scheduled'
);

-- LOGS SEED DATA
INSERT INTO logs (user_id, action, details, status)
VALUES
(1, 'create_meeting', '{"meeting_id":1}', 'success'),
(2, 'view_meeting', '{"meeting_id":1}', 'success'),
(1, 'cancel_meeting', '{"meeting_id":1}', 'failure');
