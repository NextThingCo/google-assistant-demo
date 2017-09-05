#from pydispatch import dispatcher
from localWebServer import WebServer
import time

class GoogleAssistantDemo():
	def __init__(self):
		#os.system("i2cset -f -y 0 0x34 0x30 0x03") # Turn off AXP current limiting
		self.webServer = WebServer()
		self.isRunning = True
		#while self.isRunning:
		#	time.sleep(0.1)

		p = subprocess.Popen('google-assistant-demo', stdout=subprocess.PIPE, bufsize=1)
		for line in iter(p.stdout.readline, b''):
			print line,
		p.stdout.close()
		p.wait()

demo = GoogleAssistantDemo()
demo.webServer.shutdown()
quit()