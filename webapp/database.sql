CREATE DATABASE rtbot;
USE rtbot;

CREATE TABLE permissions (
    id int(11) NOT NULL AUTO_INCREMENT,
    handle varchar(10) NOT NULL,
    name varchar(40) NOT NULL,
    description varchar(255) NOT NULL,
    display_order int(2),
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

GRANT SELECT, UPDATE, INSERT, DELETE ON rtbot.* TO 'rtbotwebapp'@'localhost' IDENTIFIED BY 'f2nSrEeA';

INSERT INTO users(id, login, password) VALUES (1, 'admin', '4a0c8d97e9b95ca3935cfb747f2b544a3d055a3e');
INSERT INTO permissions(id, handle, name, description, display_order)
  VALUES(1, 'viewlogs', 'View logs', '... is allowed to view the bot''s logs', 1);
INSERT INTO permissions(id, handle, name, description, display_order)
  VALUES(2, 'watchlogs', 'Watch logs', '... is allowed to watch the logs in realtime', 2);
INSERT INTO permissions(id, handle, name, description, display_order)
  VALUES(3, 'viewexc', 'View exceptions', '... is allowed to view the recent exceptions', 3);
INSERT INTO permissions(id, handle, name, description, display_order)
  VALUES(4, 'confexc', 'Confirm exceptions', '... is allowed to confirm exceptions as solved', 4);
INSERT INTO permissions(id, handle, name, description, display_order)
  VALUES(5, 'delexc', 'Delete exceptions', '... is allowed to remove exceptions from the list', 5);
INSERT INTO permissions(id, handle, name, description, display_order)
  VALUES(6, 'updplugins', 'Update plugins', '... is allowed to update plugins from the repository and reload them', 6);
INSERT INTO permissions(id, handle, name, description, display_order)
  VALUES(7, 'manplugins', 'Manage plugins', '... is allowed to enable and disable plugins', 7);
INSERT INTO permissions(id, handle, name, description, display_order)
  VALUES(8, 'viewsrc', 'View source', '... is allowed to view all files in the bot directory', 8);
INSERT INTO permissions(id, handle, name, description, display_order)
  VALUES(9, 'updcore', 'Update core', '... is allowed to update the core and modules of the bot', 9);
INSERT INTO permissions(id, handle, name, description, display_order)
  VALUES(10, 'mancore', 'Manage bot runtime', '... is allowed to start, restart and stop the bot', 10);
INSERT INTO permissions(id, handle, name, description, display_order)
  VALUES(11, 'killproc', 'Kill bot processes', '... is allowed to kill zombie processes of the bot', 11);
INSERT INTO permissions(id, handle, name, description, display_order)
  VALUES(12, 'superadmin', 'Superadmin', '... is allowed to manage users', 12);
INSERT INTO permissions_users(user_id, permission_id) VALUES (1, 12);
