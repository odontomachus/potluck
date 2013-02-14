CREATE TABLE guests (
       name varchar(127),
       response ENUM("yes", "no", "maybe") default NULL,
       email varchar(127),
       food varchar(255),
       hash char(32),
       sent tinyint(1) unsigned,
       UNIQUE INDEX (hash),
       UNIQUE INDEX(name)
) CHARACTER SET = utf8 COLLATE = utf8_bin;
       
