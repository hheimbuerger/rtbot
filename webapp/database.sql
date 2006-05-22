CREATE DATABASE rtbot;
USE rtbot;

CREATE TABLE permissions (
    id int(11) NOT NULL AUTO_INCREMENT,
    handle varchar(10) NOT NULL,
    name varchar(40) NOT NULL,
    description varchar(255) NOT NULL,
    PRIMARY KEY(id)
);

CREATE TABLE users (
    id int(11) NOT NULL AUTO_INCREMENT,
    login varchar(20) NOT NULL,
    password varchar(40) NOT NULL,
    PRIMARY KEY(id)
);

CREATE TABLE permissions_users ( 
    user_id int(11) NOT NULL, 
    permission_id int(11) NOT NULL, 
    INDEX roles_users_FKIndex1(permission_id), 
    INDEX roles_users_FKIndex2(user_id), 
    FOREIGN KEY(permission_id) 
        REFERENCES permissions(id) 
            ON DELETE NO ACTION 
            ON UPDATE NO ACTION, 
    FOREIGN KEY(user_id) 
        REFERENCES users(id) 
            ON DELETE NO ACTION 
            ON UPDATE NO ACTION 
);

CREATE TABLE exceptions (
    id int(11) NOT NULL AUTO_INCREMENT,
    timestamp datetime NOT NULL,
    exception_type varchar(255) NOT NULL,
    meta_message varchar(255) NOT NULL,
    message varchar(255) NOT NULL,
    traceback text NOT NULL,
    handled_by int(11),
    handled_when datetime,
    PRIMARY KEY(id),
    FOREIGN KEY(handled_by)
        REFERENCES users(id)
            ON DELETE NO ACTION
            ON UPDATE NO ACTION
);

GRANT SELECT, UPDATE, INSERT, DELETE ON rtbot.* TO 'rtbotadmin'@'localhost' IDENTIFIED BY 'taco';
