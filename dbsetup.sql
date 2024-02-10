USE 597Project;

CREATE TABLE Users (
    user_id int NOT NULL AUTO_INCREMENT,
    username varchar(256) NOT NULL UNIQUE,
    password varchar(256) NOT NULL,
    PRIMARY KEY (user_id)
);