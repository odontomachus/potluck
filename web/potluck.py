# -*- coding: utf-8 -*-
import sys
import json
import random
import md5
import uuid

from bottle import route, get, post, request, abort, Bottle
from gevent import monkey; monkey.patch_all()
from gevent import Greenlet

from gevent.pywsgi import WSGIServer
from geventwebsocket import WebSocketHandler, WebSocketError
from gevent.queue import Queue, Empty

import ConfigParser
import MySQLdb

app = Bottle()

session_id = md5.md5(str(random.random())).hexdigest()

update_queue = {}

def connect_db(host, port, user, password, db):
    try:
        return MySQLdb.connect(host=host, port=port, user=user, passwd=password, db=db)
    except MySQLdb.Error, e:
        sys.stderr.write("[ERROR] %d: %s\n" % (e.args[0], e.args[1]))
        abort(500)

errors = {
    'response': {'en':'Please select a response.', 'fr': 'Veuillez choisir une des réponses.'},
    'food': {'en': 'Plate must be less than 255 characters.', 'fr': u'Vous devez entrer moins de 255 charactères.'},
    'required': {'en': 'Required.', 'fr': 'Obligatoire.'}
}



class Reservation:
    def __init__(self, hash):
        cp = ConfigParser.ConfigParser()
        cp.read('site.cfg');

        (db_name, db_user, db_pass) = map(lambda x: cp.get('db', x, None), ('db', 'user', 'pass'))

        self.dbconn = connect_db('localhost', 3301, db_name, db_pass, db_user)
        sql = 'SELECT name, response, food FROM guests WHERE hash=%s'
        try:
            self.cursor = self.dbconn.cursor()
            self.dbconn.set_character_set('utf8')
            self.cursor.execute('SET NAMES utf8;')
            self.cursor.execute('SET CHARACTER SET utf8;')
            self.cursor.execute('SET character_set_connection=utf8;')

            self.cursor.execute(sql, (hash,))
            result = self.cursor.fetchone()
        except MySQLdb.Error, e:
            sys.stderr.write("[ERROR] %d: %s\n" % (e.args[0], e.args[1]))
            abort(500)
        if not result:
            abort(404)

        self.name = result[0] or ''
        self.hash = hash
        self.food = result[2] or ''
        self.response = result[1]
        self.errors = {'food':('','')}
        self.has_errors = False
        self.users = self.get_users()
        self.update()


    def get_users(self):
        # Get other users.
        sql = 'SELECT name, response, food FROM guests ORDER BY name'
        users = {'yes':'', 'no': '', 'maybe': '', 'invited':''}
        try:
            self.cursor.execute(sql)
            results = self.cursor.fetchall()
            for name, response, food in results:
                response = response or 'invited'
                users[response] += '<li>'+name
                if response == 'yes':
                    users[response] += '''
                    <div class="food">
                    {food}
                    </div>
                    '''.format(food=food)
                users[response] += '</li>\n'
            return users
        except MySQLdb.Error, e:
            sys.stderr.write("[ERROR] %d: %s\n" % (e.args[0], e.args[1]))
            abort(500)


    def update(self):
        self.classes = {
            'yes': 'selected' if self.response == 'yes' else '',
            'no': 'selected' if self.response == 'no' else '',
            'maybe': 'selected' if self.response == 'maybe' else '',
            }
        self.show_food = '' if self.response == 'yes' else 'hidden'


    def save(self):
        sql = 'UPDATE guests SET response=%s, food=%s WHERE hash=%s'
        try:
            self.cursor.execute(sql, (self.__dict__['response'], self.__dict__['food'], self.__dict__['hash']))
            self.dbconn.commit()

        except MySQLdb.Error, e:
            sys.stderr.write("[ERROR] %d: %s\n" % (e.args[0], e.args[1]))
            abort(500)

    def set(self, attr, value):
        """Validate incoming data and set it if appropriate."""
        if attr=='food':
            if len(value) > 254:
                self.errors['food'] = ('error', errors['food'][request.lang])
                self.has_errors = True
                return
        elif attr=='response':
            if value not in ('yes', 'no', 'maybe'):
                self.errors['response'] = ('error', errors['response'][request.lang])
                self.has_errors = True
                return
        else:
            return
        self.__dict__[attr] = value
    

    def __getattr__(self, attr):
        return self.__dict__[attr]

def getlang(lang):
    if lang == 'en' or lang == 'fr':
        return lang
    abort(404)

def template(user):
    return open('templates/potluck.html').read().format(user=user, users=user.users, session=session_id)

@app.get('/<lang>/rsvp/<hash>')
def rsvp(hash, lang):
    request.lang = getlang(lang)
    reservation = Reservation(hash)
    if not reservation.name:
        abort(404, "Invalid path")
    return template(reservation)

@app.post('/<lang>/rsvp/<hash>')
def save(hash, lang):
    request.lang = getlang(lang)
    reservation = Reservation(hash)
    if not reservation.name:
        abort(404, "Invalid path")
    reservation.set('food', request.forms.food)
    reservation.set('response', request.forms.response)
    reservation.update()

    if not reservation.has_errors:
        reservation.save()
        users = reservation.get_users()
        for channel in update_queue.values():
            channel.put(json.dumps(users))

    return template(reservation)


@app.route('/updates')
def updates():
    wsock = request.environ.get('wsgi.websocket')
    uid = uuid.uuid1()
    queue = Queue()
    if not wsock:
        abort(400, 'Expected WebSocket request.')

    try:
        message = wsock.receive()
        if message!='id:'+session_id:
            wsock.close()
            return
        update_queue[uid] = queue

    except WebSocketError:
        return

    while True:
        try:
            message = queue.get()
            if message:
                wsock.send(message)
        except WebSocketError:
            del update_queue[uid]
            break

server = WSGIServer(('0.0.0.0', 8116), app,
                    handler_class=WebSocketHandler)
server.serve_forever()
