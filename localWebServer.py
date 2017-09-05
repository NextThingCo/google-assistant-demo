from pydispatch import dispatcher
import thread
import eventlet

import time
from flask import Flask, render_template, url_for, request, jsonify, g
from flask_socketio import SocketIO, emit

eventlet.monkey_patch()

app = Flask(__name__, static_folder='webpage')
app.config['SECRET_KEY'] = 'H4114'
socketio = SocketIO(app)

class WebServer:
    def __init__(self):
        thread.start_new_thread(lambda: socketio.run(app,host='0.0.0.0',port=80), ())
        self.socket = socketio

    # Broadcast an event over the socket
    def emit(self,id,data):
        socketio.emit(id,data,broadcast=True)

    @app.route("/")
    def index():
        return app.send_static_file('index.html')

    @app.route('/<path:path>')
    def static_proxy(path):
        # send_static_file will guess the correct MIME type
        return app.send_static_file(path)

    # Socket event when a user connects to the web server
    @socketio.on('on_connect')
    def connectEvent(msg):
        dispatcher.send(signal='on_html_connection',data=msg)

    # Event when user requests a new wifi connection
    @socketio.on('on_wifi_connect')
    def connectEvent(data):
        dispatcher.send(signal='wifi_user_request_connection',data=data)

    def shutdown(self):
        self.socketio.shutdown(socketio.SHUT_RDWR)
        self.socketio = None
        self.server.terminate()
        self.server.join()