from pydispatch import dispatcher
import eventlet
import thread
import time
import json
import os

from flask import Flask, render_template, url_for, request, jsonify, g
from flask_uploads import UploadSet, configure_uploads, DOCUMENTS, IMAGES
from flask_socketio import SocketIO, emit

eventlet.monkey_patch()

app = Flask(__name__, static_folder='webpage')
app.config['SECRET_KEY'] = 'H4114'
app.config['UPLOADED_JSON_DEST'] = '/tmp/'
socketio = SocketIO(app)
docs = UploadSet('json', ('json'))

configure_uploads(app, docs)

class WebServer:
    # Start the web server on port 80
    def __init__(self):
        thread.start_new_thread(lambda: socketio.run(app,host='0.0.0.0',port=80), ())
        self.socket = socketio

    # Broadcast an event over the socket
    def emit(self,id,data):
        socketio.emit(id,data,broadcast=True)

    # Define the routes for our web app's URLs.
    @app.route("/")
    def index():
        return app.send_static_file('index.html')

    # Empty for now
    @app.route("/", methods = ['POST'])
    def post():
        return ('', 204) # Return nothing

    @app.route('/<path:path>')
    def static_proxy(path):
        # send_static_file will guess the correct MIME type
        return app.send_static_file(path)

    # Route for uploading the client JSON file from the user's local machine to the host.
    @app.route("/upload", methods = ['GET', 'POST'])
    def upload():
        if request.method == 'POST' and 'user_file' in request.files:
            try:
                # Dump the uploaded file to a JSON format in the tmp directory.
                filename = docs.save(request.files['user_file'],name='client.json')
                with open('/tmp/'+filename) as json_file:
                    data = json.load(json_file)
                    # Dispatch the JSON object
                    dispatcher.send(signal='google_auth_client_json_received',data=data)
            except Exception as e:
                print e

        return ('', 204) # Return nothing

    # Socket event when a user connects to the web server
    @socketio.on('on_connect')
    def connectEvent(msg):
        dispatcher.send(signal='on_html_connection',data=msg)

    # Socket event when user requests a new wifi connection
    @socketio.on('on_wifi_connect')
    def networkConnectEvent(data):
        print "REOLKJWER"
        dispatcher.send(signal='wifi_user_request_connection',data=data)

    # Socket event when the use has entered an authorization code after signing into their Google acct
    @socketio.on('on_submit_auth_code')
    def authCodeEvent(data):
        dispatcher.send(signal='google_auth_code_received',code=data['code'])

    def shutdown(self):
        try:
            self.socketio.shutdown(socketio.SHUT_RDWR)
            self.socketio = None
        except:
            pass