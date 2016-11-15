#!/usr/bin/env python
# coding: utf-8
# Copyright (c) 2013-2014 Abram Hindle
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import flask
'''
additional import: redirect, jsonify, url_for
redirect for redirecting url, jsonify for passing dict object from server to client
url_for better implementation
'''

from flask import Flask, request, redirect, jsonify, url_for
from flask_sockets import Sockets
import gevent
from gevent import queue
import time
import json
import os

app = Flask(__name__)
sockets = Sockets(app)
app.debug = True

'''
from gevent tutorial, chat server
http://sdiehl.github.io/gevent-tutorial/
'''
# make a list elem for clients
clients = list()
# the class for handling client side queue
class Client:
    def __init__(self):
        #set up a queue
        self.queue = queue.Queue()

    def put(self, v):
        # queue.put_nowait(v) does
        # put(v, false), indicate v is not waiting
        self.queue.put_nowait(v)

    def get(self):
        return self.queue.get()

class World:
    def __init__(self):
        self.clear()
        # we've got listeners now!
        self.listeners = list()
        
    def add_set_listener(self, listener):
        self.listeners.append( listener )

    def update(self, entity, key, value):
        entry = self.space.get(entity,dict())
        entry[key] = value
        self.space[entity] = entry
        self.update_listeners( entity )

    def set(self, entity, data):
        self.space[entity] = data
        self.update_listeners( entity )

    def update_listeners(self, entity):
        '''update the set listeners'''
        for listener in self.listeners:
            listener(entity, self.get(entity))

    def clear(self):
        # world clear
        self.space = dict()

    def get(self, entity):
        # gets specific entity of the world
        return self.space.get(entity,dict())
    
    def world(self):
        # shows world
        return self.space

myWorld = World()        

# in here we need to set listener in the client list
def set_listener( entity, data ):
    ''' do something with the update ! '''
    # put listeners in client
    temp = {}
    temp[entity] = data
    # from clients list we append it to listener
    for elem in clients:
        elem.put(json.dumps(temp))

myWorld.add_set_listener( set_listener )
        
@app.route('/')
def hello():
    '''Return something coherent here.. perhaps redirect to /static/index.html '''
    #return redirect(url_for("static", filename="index.html"))
    return redirect("/static/index.html", code = 302)

def read_ws(ws,client):
    '''A greenlet function that reads from the websocket and updates the world'''
    # XXX: TODO IMPLEMENT ME
    # read until none
    while true:
        # ws is websocket, need to receive it first
        web = we.receive()
        #if (web != None):
        if (web is not None):
            #print(web)
            # cant just print web, we need to use json load
            web = json.loads(web)
            print(web)
            for key, data in web.iteritems():
                myWorld.set(key, data)
                send_all(json.dumps(web))
        else:
            print("ws is empty")

    return None

@sockets.route('/subscribe')
def subscribe_socket(ws):
    '''Fufill the websocket URL of /subscribe, every update notify the
       websocket and read updates from the websocket '''
    # XXX: TODO IMPLEMENT ME
    # create new Client
    client = Client()
    clients.append(client)
    # http://www.gevent.org/gevent.html
    # gevent.spawn creates an greenlet object
    g = gevent.spawn(read_ws, ws, client)
    # at this stage we are subscribing
    # send the web socket to my world
    ws.send(json.dumps(myWorld.world()))
    try:
        while True:
            temp = client.get()
            ws.send(temp)
    except Exception as e:
        print("websocket error %s " % e)
    finally:
        clients.remove(client)
        # end gevent
        gevent.kill(g)
    return None


def flask_post_json():
    '''Ah the joys of frameworks! They do so much work for you
       that they get in the way of sane operation!'''
    if (request.json != None):
        return request.json
    elif (request.data != None and request.data != ''):
        return json.loads(request.data)
    else:
        return json.loads(request.form.keys()[0])

@app.route("/entity/<entity>", methods=['POST','PUT'])
def update(entity):
    '''update the entities via this interface'''
    # both methods take same action
    temp = flask_post_json()
    for key, value in temp.iteritems():
        myWorld.update(entity, key, value)
    return json.dumps(myWorld.get(entiy))

@app.route("/world", methods=['POST','GET'])    
def world():
    '''you should probably return the world here'''
    if request.method == "GET":
        # if method is get then, return world
        return json.dumps(myWorld.world())
    if request.method == "POST":
        # prep for post json
        temp = flask_post_json()
        # if method is post then, set the world
        for key, data in temp.iteritems():
            myWorld.set(key, value)
        # return world
        return json.dumps(myWorld.world())

@app.route("/entity/<entity>")    
def get_entity(entity):
    '''This is the GET version of the entity interface, return a representation of the entity'''
    return json.dumps(myWorld.get(entity))


@app.route("/clear", methods=['POST','GET'])
def clear():
    '''Clear the world out!'''
    myWorld.clear()
    # return the myWorld in json
    # use json dumps, not flask jsonify since jsonify dont return all elem
    return json.dumps(myWorld.world())



if __name__ == "__main__":
    ''' This doesn't work well anymore:
        pip install gunicorn
        and run
        gunicorn -k flask_sockets.worker sockets:app
    '''
    app.run()
