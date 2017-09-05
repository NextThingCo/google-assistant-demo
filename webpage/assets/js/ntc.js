var socket = io.connect('http://' + document.domain + ':' + location.port);
var networks = null;
var bConnecting = false;

socket.on('connect', function() {
	socket.emit('on_connect', {data: 'User connected'});
});

socket.on('wifi_scan_complete', function(data){
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
	document.getElementById("connect_button").innerHTML = 'Connecting...'
	socket.emit('on_wifi_connect', {ssid:"NTC 2461",passphrase:"ntc2461@ccess"});
}

socket.on('wifi_connection_status', function(status){
	msg = null
	if(status) {
		document.getElementById("connection_status").innerHTML = "Wifi Status: Connected";
		msg = "You are connected!"
	} else {
		document.getElementById("connection_status").innerHTML = "Wifi Status: Not Connected!";
		msg = "Connection failure!"
	}
	if (bConnecting) {
		bConnecting = false
		document.getElementById("connect_button").innerHTML = '<button onclick="connectToNetwork()">Connect</button>';
		alert(msg);
	}
});