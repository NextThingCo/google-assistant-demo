// Copyright (C) 2017 Next Thing Co. <software@nextthing.co>
//
// This program is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 2 of the License, or
// (at your option) any later version.
//
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
//
// You should have received a copy of the GNU General Public License
// along with this program.  If not, see <http://www.gnu.org/licenses/>

var authInstructions = '<p>In order to use Google Assistant on your device for development purposes,  \
						you will first need to set up a new project under your Google Account if you have not done so already.</p> \
						<p><b>You should only have to do these steps once per device.</b></p> \
						<p>1: Follow <a target="_blank" href="https://developers.google.com/assistant/sdk/prototype/getting-started-other-platforms/config-dev-project-and-account">this link</a> \
						for instructions on setting up an account.</p> \
    					<p>2: Once completed, you should now have a <b>client_secret_xxxxx.json</b> credentials file saved to the computer you are using to access this page.<p>\
						<p>3: Upload your credentials JSON file by clicking the <b>Choose File</b> button and then <b>Submit<b></p> \
						<form name="auth" id="auth" method="post" action="/" id="AUTH_CODE" > \
    					<p id="auth_code"</p> \
						</form>'

var authJsonButton 		= '<form name="auth" id="auth" method="post" action="" id="AUTH_FORM"> \
							<p id="client_json_button"></p> \
							<p id="client_upload_button"></p> \
							</form> \
							<form method="post" enctype=multipart/form-data action =""> \
							<input type="file" accept=".json" name="user_file"> \
							<input class="btn" type="submit"> \
							</form>'

var authURICopy1 		= "<p>You're almost finished! Simply click on the link listed below and sign into your Google account:<p>"
var authURICopy2 		= '<p>You will then see an authorization code. Copy this code and paste it into the box below to finish setup:</p> \
							<p>Paste code here: <input type="code" id="code"></p> \
							<p><button class="btn" onclick="submitAuthCode()">Submit</button></p> \
							<p><p><p> \
							<p><a id="clearCreds" title="Reset Credentials" href="#" onclick="resetGoogleCredentials();return false;">Reset Credentials</a></p>'

var socket = io.connect('http://' + document.domain + ':' + location.port + "/");
var networks = null;
var bConnecting = false;
var wifiStatus = null
var connectedSSID = null
var signalStrengthCharacter = '&diams;'

	socket.on('connect', function() {
		document.getElementById("connection_status").innerHTML = "Wifi"
		html = '<select name="ssid" id="ssid" onchange="selectNetwork(this)">'
		html+='<option value="">---SCANNING---</option>'
		document.getElementById("ssid").innerHTML = html;
		socket.emit('on_connect', {data: 'User connected'});
	});

	socket.on('wifi_scan_complete', function(data){	
		networks = data
		list = []
		connectedSSID = null
		$.each(networks, function(i, item){
			if(item['ssid']) {
				ssid = item['ssid']
				if(item['online']) {
					connectedSSID = ssid
				} else {
					strength = item['strength']
					level = 1
					if(strength>34) {
						level=2
					}
					if(strength>44) {
						level=3
					}
					if(strength>54) {
						level=4
					}
					rating = ''
					for (var i = 0; i < level; i++) {
						rating += signalStrengthCharacter
						
					}
					list.push([ssid,rating])
				}
			}
		});

		html = '<select name="ssid" id="ssid" onchange="selectNetwork(this)">'
		if (wifiStatus!='online' && !connectedSSID) {
			html+='<option value="">(Select a Network)</option>'
		} else if (connectedSSID) {
			html+='<option value="' + ssid + '">(Connected: '+connectedSSID+')</option>'
		}
		for (var i = 0; i < list.length; i++) {
			html+='<option value="' + list[i][0] + '">'+list[i][0]+'&nbsp;&nbsp;'+list[i][1]+'</option>'
		}
		html+="</select>"
		document.getElementById("ssid").innerHTML = html;
	});

	function resetGoogleCredentials() {
		socket.emit('on_reset_googleCredentials');
		window.location.reload()
	}

	function setAntenna(status,bNoUpdate){
		if(status==1) {
			html ='<input type="checkbox" id="antenna" name="antenna" value="1" onchange="setAntenna(0)" checked> \
			<label for="antenna"><b>External Antenna is Enabled</b><br> (be sure to <a target=_blank href="https://docs.getchip.com/chip_pro_devkit.html#connect-antenna">connect your antenna</a> for best results)</label><br>'
		} else {
			html ='<input type="checkbox" id="antenna" name="antenna" value="0" onchange="setAntenna(1)"> \
			<label for="antenna"><b>External Antenna is Disabled</b><br> (use of an <a target=_blank href="https://docs.getchip.com/chip_pro_devkit.html#connect-antenna">external antenna</a> is strongly recommended)</label><br>'
		}
		if(!bNoUpdate) {
			socket.emit('on_antenna_set', {status:status});
		}
		
		document.getElementById("antenna_button").innerHTML = html;
	}

	function selectNetwork(select){
		if(select.value=='') {
			document.getElementById("password_field").innerHTML = '';
			document.getElementById("connect_button").innerHTML = '';
			return;
		}
	    passwordHTML = '';
	    $.each(networks, function(i, item){
	    	if(item['ssid'] == select.value) {
				if (item['security'] != 'none') {
					passwordHTML = '<input type="password" placeholder="Password" id="password">'
				}
			}
			document.getElementById("password_field").innerHTML = passwordHTML;
			document.getElementById("connect_button").innerHTML = '<button class="btn" onclick="connectToNetwork()">Connect</button>';
		});
	}

	function setOfflineMessage() {
		document.getElementById("auth_status").innerHTML = 'Google Assistant is offline.'
		document.getElementById("auth_message").innerHTML = 'Please connect to the internet before using Google Assistant.';
		document.getElementById("auth_input").innerHTML = '';
	}

	function connectToNetwork() {
		bConnecting = true;
		selectedSsid =  document.getElementById('ssid').value
		document.getElementById("connection_status").innerHTML = 'Attempting to connect...'
		document.getElementById("connect_button").innerHTML = "Connecting..."
		inputPassphrase = document.getElementById('password').value
		socket.emit('on_wifi_connect', {ssid:selectedSsid,passphrase:inputPassphrase});
	}

	socket.on('wifi_connection_status', function(status){
		wifiStatus = status
		msg = null
		if(status == 'online') {
			document.getElementById("connection_status").innerHTML = "Wifi Status: Connected";
			msg = "You are connected!"
		} else if(status == 'connecting') {
			document.getElementById("connection_status").innerHTML = "Connecting...";
		} else if(status == 'rejected' && !bConnecting) {
			msg = "Connection failed. Did you enter the correct password?"
			document.getElementById("connection_status").innerHTML = "Connection failed";
			alert(msg)
		} else if(status == 'offline') {
			document.getElementById("connection_status").innerHTML = "Wifi Status: Connected, No Internet :(";
			setOfflineMessage();
		} else {
			msg = "Disconnected!"
			document.getElementById("connection_status").innerHTML = "Wifi Status: Not Connected!";
			setOfflineMessage();
			msg = "Connection failure!"
		}
		if (bConnecting) {
			bConnecting = false
			document.getElementById("connect_button").innerHTML = '';
			//if (msg) {
			//	alert(msg);
			//}
		}
	});

	socket.on('wifi_antenna_status', function(status){
		setAntenna(status,true)
	});

	socket.on('google_assistant_event', function(eventName){
		msg = null
		if(wifiStatus!='online') {
			setOfflineMessage()
		} else if(eventName=='ON_LOADING') {
			document.getElementById("auth_status").innerHTML = 'Google Assistant is starting...'
			document.getElementById("auth_message").innerHTML = 'Loading... please wait a moment...';
		} else if(eventName=='ON_CONVERSATION_TURN_STARTED') {
			document.getElementById("auth_message").innerHTML = 'Waiting user to finish speaking...';
		} else if(eventName=='ON_RESPONDING_STARTED') {
				document.getElementById("auth_message").innerHTML = 'Assistant is responding...';
		} else if(eventName=='ON_CONVERSATION_TURN_FINISHED' || eventName=='ON_START_FINISHED' || eventName=='TIMEOUT') {
			document.getElementById("auth_message").innerHTML = 'Ready! Say "Hey Google" or "OK Google" and ask your question.';
			document.getElementById("auth_status").innerHTML = 'Google Assistant is running!'
		}
	});

	socket.on('auth_status', function(status){
		msg = null
		if(wifiStatus!='online') {
			setOfflineMessage()
		} else if(status=='authentication_required') {
			document.getElementById("auth_status").innerHTML = "Google authorization required!";
			document.getElementById("auth_message").innerHTML = authInstructions;
			document.getElementById("auth_input").innerHTML = authJsonButton;
		} else if (status=='authentication_uri_created') {
			document.getElementById("auth_status").innerHTML = "Google authorization in progress...";		
		} else if (status=='authentication_invalid') {
			document.getElementById("auth_status").innerHTML = "Authorization failed! :(";		
		} else if (status=='authorized') {
			document.getElementById("auth_status").innerHTML = "Google Assistant is authorized!";		
		} else if (status=='no_connection') {
			document.getElementById("auth_status").innerHTML = "Please connect to the internet before using Google Assistant.";		
		}
	});


	socket.on('google_authorized', function(){
		document.getElementById("auth_status").innerHTML = "Google Assistant is authorized and ready for use!";
		document.getElementById("auth_message").innerHTML = "";	
		document.getElementById("auth_input").innerHTML = "";
	});

	
	socket.on('google_show_authentication_uri', function(code){
		document.getElementById("auth_message").innerHTML = authURICopy1 + "<p><a target='_blank' href=" + code + ">Click HERE to sign in!</a></p>";
		document.getElementById("auth_input").innerHTML = authURICopy2;
	});

	function submitAuthCode() {
		authCode =  document.getElementById('code').value
		socket.emit('on_submit_auth_code', {code:authCode});
	}

