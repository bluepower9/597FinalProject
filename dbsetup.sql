USE 597Project;

DROP TABLE excerpts;
DROP TABLE documents;
DROP TABLE login_sessions;
DROP TABLE users;
DROP TABLE invalid_jwt_tokens;


CREATE TABLE IF NOT EXISTS users (
    user_id int NOT NULL AUTO_INCREMENT,
    username varchar(64) NOT NULL UNIQUE,
    email varchar(64) NOT NULL,
    password VARBINARY(64) NOT NULL,
    salt VARBINARY(64) NOT NULL,

    PRIMARY KEY (user_id)
);

CREATE TABLE IF NOT EXISTS login_sessions(
    user_id int NOT NULL,
    session_id VARCHAR(64),
    start_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    PRIMARY KEY (session_id),
    FOREIGN KEY (user_id) references users(user_id)

);

CREATE TABLE IF NOT EXISTS invalid_jwt_tokens (
    token VARCHAR(256) NOT NULL UNIQUE,
    PRIMARY KEY (token)
);

CREATE TABLE IF NOT EXISTS documents (
    doc_id int NOT NULL AUTO_INCREMENT,
    user_id int NOT NULL,
    title varchar(256) NOT NULL,

    PRIMARY KEY (doc_id),
    FOREIGN KEY (user_id) references users(user_id)
);

CREATE TABLE IF NOT EXISTS excerpts (
    excerpt_id int NOT NULL AUTO_INCREMENT,
    excerpt varchar(2048) NOT NULL,
    doc_id int NOT NULL,

    PRIMARY KEY (excerpt_id),
    FOREIGN KEY (doc_id) references documents(doc_id)
);