var socket = io.connect('http://' + document.domain + ':' + location.port);
var networks = null;
var bConnecting = false;

socket.on('connect', function() {
	socket.emit('on_connect', {data: 'User connected'});
});

socket.on('wifi_scan_complete', function(data){
	console.log("WIFI SCAN!!!!")
	html = '<select name="ssid" id="ssid" onchange="selectNetwork(this)">'
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
		//console.log(data[i]['ssid'])
	});
	html+="</select>"
	document.getElementById("ssid").innerHTML = html;
});

function selectNetwork(select){
    console.log(select.value)
    passwordHTML = '';
    $.each(networks, function(i, item){
    	console.log(item['security'])
    	if(item['ssid'] == select.value) {
			if (item['security'] != 'none') {
				passwordHTML = 'Password: <input type="password" id="password">'
			}
		}
		document.getElementById("password_field").innerHTML = passwordHTML;
		document.getElementById("connect_button").innerHTML = '<button onclick="connectToNetwork()">Connect</button>';
	});
}

function connectToNetwork() {
	bConnecting = true;
	selectedSsid =  document.getElementById('ssid').value
	document.getElementById("connection_status").innerHTML = 'Attempting to connect to ' + document.getElementById('ssid').value + '...'
	document.getElementById("connect_button").innerHTML = "Connecting..."
	inputPassphrase = document.getElementById('password').value
	console.log(selectedSsid)
	socket.emit('on_wifi_connect', {ssid:selectedSsid,passphrase:inputPassphrase});
}

socket.on('wifi_connection_status', function(status){
	msg = null
	if(status == 'online') {
		document.getElementById("connection_status").innerHTML = "Wifi Status: Connected";
		msg = "You are connected!"
	} else if(status == 'rejected') {
		msg = "Connection failed. Did you enter the correct password?"
		document.getElementById("connection_status").innerHTML = "Connection failed";
	} else if(status == 'disconnected') {
		msg = "Disconnected!"
	} else {
		document.getElementById("connection_status").innerHTML = "Disconnected";
		document.getElementById("connection_status").innerHTML = "Wifi Status: Not Connected!";
		msg = "Connection failure!"
	}
	if (bConnecting) {
		bConnecting = false
		document.getElementById("connect_button").innerHTML = '<button onclick="connectToNetwork()">Connect</button>';
		alert(msg);
	}
});

socket.on('auth_status', function(status){
	msg = null
	console.log(status)
	if(status=='authentication_required') {
		document.getElementById("auth_status").innerHTML = "Google authorization required!";		
	} else if (status=='authentication_uri_created') {
		document.getElementById("auth_status").innerHTML = "Google authorization in progress.";		
	} else if (status=='authentication_invalid') {e
		document.getElementById("auth_status").innerHTML = "Authorization failed! :(";		
	} else if (status=='authorized') {
		document.getElementById("auth_status").innerHTML = "Google Assistant is authorized and ready for use!";		
	} else if (status=='no_connection') {
		document.getElementById("auth_status").innerHTML = "Please connect to the internet before using Google Assistant.";		
	}
});


socket.on('google_authorized', function(){
	document.getElementById("auth_status").innerHTML = "Google Assistant is authorized and ready for use!";		
});

function submitAuthCode() {
	authCode =  document.getElementById('code').value
	console.log("FUDGE: " + authCode)
	socket.emit('on_submit_auth_code', {code:authCode});
}

socket.on('google_show_authentication_uri', function(code){
	document.getElementById("auth_link").innerHTML = code;
	
	formCode = 'Authorization Code: <input type="code" id="code">'
	formCode = formCode + '<button onclick="submitAuthCode()">Submit</button>';
	document.getElementById("auth_code").innerHTML = formCode;
	console.log("OK NOW")
	console.log(code)
});

