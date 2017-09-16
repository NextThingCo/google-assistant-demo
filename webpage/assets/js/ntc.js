var authInstructions = '<p>In order to use Google Assistant on your device, \
						you will to first set up a new project under your Google Account if you have not done so already. You should only have to do these steps once.</p> \
						<p>1: Follow <a target="_blank" href="https://developers.google.com/assistant/sdk/prototype/getting-started-other-platforms/config-dev-project-and-account">this link</a> \
						for instructions on setting up an account.</p> \
    					<p>2: Once completed, download the <b>client_secret_XXXXX.json</b> file from the Google API Console Project credentials section mentioned in the link above.<p>\
						<p>3: Upload your credentials file here by clicking the button below:</p> \
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
							<p><button class="btn" onclick="submitAuthCode()">Submit</button></p>'

var socket = io.connect('http://' + document.domain + ':' + location.port + "/");
var networks = null;
var bConnecting = false;
var wifiStatus = null

	socket.on('connect', function() {
		document.getElementById("connection_status").innerHTML = "Wifi"
		html = '<select name="ssid" id="ssid" onchange="selectNetwork(this)">'
		html+='<option value="">---SCANNING---</option>'
		document.getElementById("ssid").innerHTML = html;
		socket.emit('on_connect', {data: 'User connected'});
	});

	socket.on('disconnect', function() {
		socket.emit('on_disconnected', {data: 'User disconnected'});
	});

	socket.on('wifi_scan_complete', function(data){
		html = '<select name="ssid" id="ssid" onchange="selectNetwork(this)">'
		html+='<option value="">(Select a Network)</option>'
		networks = data
		$.each(networks, function(i, item){
			if(item['ssid']) {
				ssid = item['ssid']
				strength = item['strength']
				rating = ' *'
				if(strength>45) {
					rating = ' **'
				}
				if(strength>50) {
					rating = ' ***'
				}
				if(strength>54) {
					rating = ' ****'
				}	
				html+='<option value="' + ssid + '">'+ssid+rating+'</option>'
			}
		});
		html+="</select>"
		document.getElementById("ssid").innerHTML = html;
	});

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
		console.log(status)
		wifiStatus = status
		msg = null
		if(status == 'online') {
			document.getElementById("connection_status").innerHTML = "Wifi Status: Connected";
			msg = "You are connected!"
		} else if(status == 'connecting') {
			document.getElementById("connection_status").innerHTML = "Connecting...";
		} else if(status == 'rejected') {
			msg = "Connection failed. Did you enter the correct password?"
			document.getElementById("connection_status").innerHTML = "Connection failed";
			setOfflineMessage();
			alert(msg)
		} else if(status == 'disconnected') {
			msg = "Disconnected!"
			setOfflineMessage();
		} else {
			document.getElementById("connection_status").innerHTML = "Disconnected";
			document.getElementById("connection_status").innerHTML = "Wifi Status: Not Connected!";
			setOfflineMessage();
			msg = "Connection failure!"
		}
		if (bConnecting) {
			bConnecting = false
			document.getElementById("connect_button").innerHTML = '';
			if (msg) {
				alert(msg);
			}
		}
	});

	socket.on('google_assistant_event', function(eventName){
		msg = null
		console.log(eventName)
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
		console.log(status)
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

