# -*- coding: utf-8 -*-
import sys
import subprocess
import csv
import md5
import time

import ConfigParser
import MySQLdb

def connect_db(host, port, user, password, db):
    try:
        return MySQLdb.connect(host=host, port=port, user=user, passwd=password, db=db)
    except MySQLdb.Error, e:
        sys.stderr.write("[ERROR] %d: %s\n" % (e.args[0], e.args[1]))

class Guest:
    def __init__(self):
        cp = ConfigParser.ConfigParser()
        cp.read('web/site.cfg');

        (db_name, db_user, db_pass) = map(lambda x: cp.get('db', x, None), ('db', 'user', 'pass'))

        self.dbconn = connect_db('localhost', 3301, db_name, db_pass, db_user)
        try:
            self.cursor = self.dbconn.cursor()
            self.dbconn.set_character_set('utf8')
            self.cursor.execute('SET NAMES utf8;')
            self.cursor.execute('SET CHARACTER SET utf8;')
            self.cursor.execute('SET character_set_connection=utf8;')
        except MySQLdb.Error, e:
            sys.stderr.write("[ERROR] %d: %s\n" % (e.args[0], e.args[1]))

    def save(self):
        if self.new:
            sql = 'INSERT INTO guests (name, email, hash, sent) VALUES(%s, %s, %s, 1)'
        else:
            sql = 'UPDATE guests SET name=%s, email=%s WHERE hash=%s'
        try:
            self.cursor.execute(sql, (guest.name, guest.email, guest.hash))
            self.dbconn.commit()
        except MySQLdb.Error, e:
            sys.stderr.write("[ERROR] %d: %s\n" % (e.args[0], e.args[1]))

with open('email.html') as htmlfile:
    html = htmlfile.read()

with open('invites.csv', 'rb') as csvfile:
    reader = csv.DictReader(csvfile, ['name', 'email', 'hash'])
    buffer = []
    for row in reader:
        buffer.append(row)
        guest = Guest()
        guest.name = row['name']
        guest.email = row['email']
        guest.new = False
        guest.hash = row['hash']

        if not row['hash']:
            guest.new = True
            guest.hash = md5.md5('line' + 'afeajafej.xlfej' + str(time.time())+str(buffer)).hexdigest()
            row['hash'] = guest.hash
            body = html.format(row=row)
            
            p = subprocess.Popen(['mutt',  '-e', 'set content_type=text/html', '-s', "Potluck", row['email']], stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE)
            res = p.communicate(input=body)
            print(res)
        guest.save()

with open('invites.csv', 'wb') as csvout:
    writer = csv.DictWriter(csvout, ['name', 'email', 'hash'])
    writer.writerows(buffer)

