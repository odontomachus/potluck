# -*- coding: utf-8 -*-
import time
import sys

from bottle import route, run, get, post, request, abort
import cgi

import MySQLdb

def connect_db(host, port, user, password, db):
    try:
        return MySQLdb.connect(host=host, port=port, user=user, passwd=password, db=db)
    except MySQLdb.Error, e:
        sys.stderr.write("[ERROR] %d: %s\n" % (e.args[0], e.args[1]))
        abort(500)

errors = {
    'name': {'en': 'Name must be less than 124 characters.', 'fr': u'Vous devez entrer moins de 124 charactères.'},
    'food': {'en': 'Plate must be less than 255 characters.', 'fr': u'Vous devez entrer moins de 255 charactères.'},
    'comment': {'en': 'Comment must be less than 1024 characters.', 'fr': u'Vous devez entrer moins de 1024 charactères.'},
    'guests': {'en': 'Invalid selection.', 'fr': 'Choix invalide.'},
    'required': {'en': 'Required.', 'fr': 'Obligatoire.'}
}

class Reservation:
    def __init__(self, hash):
        self.dbconn = connect_db('localhost', 3301, 'picnic', 'aFL8-XpYy2', 'picnic')
        sql = 'SELECT id, name, coming, comment, food, guests, email, created, updated, lang FROM reservations WHERE hash=%s'
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
        self.id = result[0]
        self.name = result[1] if result[1] else ''
        self.hash = hash
        self.lang = result[9]
        self.guests = result[5]
        self.coming = 'checked' if result[2] else ''
        self.created = int(result[7]) if result[7] else int(time.time())
        self.updated = int(time.time())
        self.email = result[6]
        self.food = result[4] if result[4] else ''
        self.comment = result[3] if result[3] else ''
        self.errors = {'name':('',''), 'guests':('',''), 'food':('',''), 'comment':('','')}
        self.has_errors = False

    def save(self):
        coming = 1 if self.coming == 'checked' else 0
        sql = 'UPDATE reservations SET name=%s, coming=%s, comment=%s, food=%s, guests=%s, created=%s, updated=%s WHERE hash=%s'
        try:
            print (self.__dict__['name'], coming, self.__dict__['comment'], self.__dict__['food'], self.__dict__['guests'], self.__dict__['created'], self.__dict__['updated'], self.hash)
            self.cursor.execute(sql, (self.__dict__['name'], coming, self.__dict__['comment'], self.__dict__['food'], self.__dict__['guests'], self.__dict__['created'], self.__dict__['updated'], self.hash))
            self.dbconn.commit()

        except MySQLdb.Error, e:
            sys.stderr.write("[ERROR] %d: %s\n" % (e.args[0], e.args[1]))
            abort(500)

    # @TODO validation
    def set(self, attr, value):
        """Validate incoming data and set it if appropriate."""
        if attr=='name':
            if len(value) > 126:
                self.errors['name'] = ('error', errors['name'][request.lang])
                self.has_errors = True
                return
            if not value:
                self.errors['name'] = ('error', errors['required'][request.lang])
                self.has_errors = True
                return
        elif attr=='food':
            if len(value) > 255:
                self.errors['food'] = ('error', errors['food'][request.lang])
                self.has_errors = True
                return
        elif attr=='comment':
            if len(value) > 1023:
                self.errors['comment'] = ('error', errors['comment'][request.lang])
                self.has_errors = True
                return
        elif attr=='guests':
            try:
                value = int(value)
                if value > 4 or value < 1:
                    self.errors['guests'] = ('error', errors['guests'][request.lang])
                    self.has_errors = True
                    return
            except ValueError:
                self.errors['guests'] = ('error', errors['guests'][request.lang])
                self.has_errors = True
                return
        self.__dict__[attr] = value
    

    def __getattr__(self, attr):
        return self.__dict__[attr]

def getlang(lang):
    if lang == 'en' or lang == 'fr':
        return lang
    abort(404)

def form(hash, lang, reservation):
    guests = ['', '', '', '']
    if reservation.guests > 0: guests[reservation.guests-1] = 'selected'
    template = file('templates/form_'+lang+'.html').read().format(reservation=reservation, guests=guests)
    
    return template

@get('/<lang>/rsvp/<hash>')
def rsvp(hash, lang):
    request.lang = getlang(lang)
    reservation = Reservation(hash)
    if not reservation.id:
        abort(404, "Invalid path")
    return form(hash, lang, reservation)

@post('/<lang>/rsvp/<hash>')
def save(hash, lang):
    request.lang = getlang(lang)
    reservation = Reservation(hash)
    if not reservation.id:
        abort(404, "Invalid path")
    reservation.set('name', request.forms.name)
    reservation.set('guests', request.forms.guests)
    reservation.set('coming', 'checked' if request.forms.coming == '1' else '')
    reservation.updated = int(time.time())
    reservation.set('food', request.forms.food)
    reservation.set('comment', request.forms.comment)
    if request.lang == 'en':
        message = 'See you there!' if reservation.coming else 'We\'ll miss you'
    else:
        message = u'A bientot!' if reservation.coming else 'La prochaine fois'

    if not reservation.has_errors:
        reservation.save()
        return file('templates/thanks.html').read().format(message=(message,))
    else:
        return form(hash, lang, reservation)

run(server='twisted', host='localhost', port=8106)

