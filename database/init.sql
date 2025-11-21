CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(32) UNIQUE NOT NULL, -- Max username len in discord is 32 I believe
    role INT NOT NULL DEFAULT 0,
    discord_id TEXT UNIQUE,
    email TEXT,
    name TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);


INSERT INTO users (username, role, discord_id, email, name)
VALUES (
  'president',
  0,                          -- role, refer to ../customtypes.py to ensure this matches admin
  '123456789012345678',
  'sirRumpustiltskinnedtheTurd@ualberta.ca',
  'god'
);
