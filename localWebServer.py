from pydispatch import dispatcher
from wsgiref import handlers

import SocketServer
import eventlet
import logging
import thread
import time
import json
import os

from flask import Flask, render_template, url_for, request, jsonify, g, redirect
from flask_uploads import UploadSet, configure_uploads, DOCUMENTS, IMAGES
from flask_socketio import SocketIO, emit

# Patch system modules to be greenthread-friendly
eventlet.monkey_patch()

# Another monkey patch to avoid annoying (and useless?) socket pipe warnings when users disconnect
SocketServer.BaseServer.handle_error = lambda *args, **kwargs: None
handlers.BaseHandler.log_exception = lambda *args, **kwargs: None

# Turn off more annoying log messages that aren't helpful.
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

app = Flask(__name__, static_folder='webpage')
app.config['SECRET_KEY'] = 'H4114'
app.config['UPLOADED_JSON_DEST'] = '/tmp/'
socketio = SocketIO(app, async_mode='threading', ping_timeout=30, logger=False, engineio_logger=False)

# Configure server to accept uploads of JSON files
docs = UploadSet('json', ('json'))
configure_uploads(app, docs)

class WebServer:
    # Start the web server on port 80
    def __init__(self):
        thread.start_new_thread(lambda: socketio.run(app,host='0.0.0.0',port=80), ())
        self.socket = socketio

    # Broadcast an event over the socket
    def broadcast(self,id,data):
        with app.app_context():
            try:
                socketio.emit(id,data,broadcast=True)
            except:
                pass

    # Define the routes for our web app's URLs.
    @app.route("/")
    def index():
        return app.send_static_file('index.html')

    # Guess the correct MIME type for static files
    @app.route('/<path:path>')
    def static_proxy(path):
        return app.send_static_file(path)

    # Route for uploading the client JSON file from the user's local machine to the host.
    @app.route("/", methods = ['GET', 'POST'])
    def upload():
        if request.method == 'POST' and 'user_file' in request.files:
            try:
                # Dump the uploaded file to a JSON format in the tmp directory.
                filename = docs.save(request.files['user_file'],name='client.json')
                with open('/tmp/'+filename) as json_file:
                    data = json.load(json_file)
                    # Dispatch the JSON object
                    dispatcher.send(signal='google_auth_client_json_received',data=data)
                    # Refresh page to re-establish a socket connection.
                    return redirect("/", code=302)
            except Exception as e:
                print e

        return ('', 204) # Return nothing

    # Socket event when a user connects to the web server
    @socketio.on('on_connect')
    def connectEvent(msg):
        dispatcher.send(signal='on_html_connection',data=msg)

    @socketio.on('on disconnect')
    def disconnectEvent():
        print('disconnected')

    # Socket event when user requests a new wifi connection
    @socketio.on('on_wifi_connect')
    def networkConnectEvent(data):
        dispatcher.send(signal='wifi_user_request_connection',data=data)

    # Socket event when the use has entered an authorization code after signing into their Google acct
    @socketio.on('on_submit_auth_code')
    def authCodeEvent(data):
        dispatcher.send(signal='google_auth_code_received',code=data['code'])

    def shutdown(self):
        global socketio
        socketio.stop()
        socketio.shutdown(socketio.SHUT_RDWR)
