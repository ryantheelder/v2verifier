from tkinter.ttk import *
import tkinter as tk
from PIL import Image
from PIL import ImageTk
import time
import threading
from threading import Thread
import json
from socket import socket

class GUI:

	def __init__(self, root):

		self.threadlock = threading.Lock()

		self.receivedPacketCount = 0
		self.processedPacketCount = 0
		self.authenticatedPacketCount = 0
		self.intactPacketCount = 0
		self.ontimePacketCount = 0

		self.receivedPacketCountText = tk.StringVar()
		self.processedPacketCountText = tk.StringVar()
		self.authenticatedPacketCountText = tk.StringVar()
		self.intactPacketCountText = tk.StringVar()
		self.ontimePacketCountText = tk.StringVar()
		self.receivedPacketCountValueText = tk.StringVar()
		self.processedPacketCountValueText = tk.StringVar()
		self.authenticatedPacketCountValueText = tk.StringVar()
		self.intactPacketCountValueText = tk.StringVar()
		self.ontimePacketCountValueText = tk.StringVar()
		self.receivedPacketCountPercentageText = tk.StringVar()
		self.processedPacketCountPercentageText = tk.StringVar()
		self.authenticatedPacketCountPercentageText = tk.StringVar()
		self.intactPacketCountPercentageText = tk.StringVar()
		self.ontimePacketCountPercentageText = tk.StringVar()
		
		self.root = root
		root.title("V2X Communications - Security Testbed")	

		self.root.grid_rowconfigure(1, weight=1)
		self.root.grid_columnconfigure(1, weight=1)

		CANVAS_HEIGHT = 600
		CANVAS_WIDTH = 800

		# create the drawing canvas
		#self.canvas = tk.Canvas(root, height=CANVAS_HEIGHT, width=CANVAS_WIDTH, bg='#247000')
		self.canvas = tk.Canvas(root, height=CANVAS_HEIGHT, width=CANVAS_WIDTH)

		# create textbox to display messages
		self.textWidget = tk.Text(root, height=300,font=36, bg="white", borderwidth=2)

		self.textWidget.tag_configure("valid", foreground="green")
		self.textWidget.tag_configure("attack", foreground="red")
		self.textWidget.tag_configure("information", foreground="orange")

		background = ImageTk.PhotoImage(Image.open("pic/background.jpg"))
		self.backgroundImage = background
		self.canvas.create_image(400, 300, image=self.backgroundImage, anchor=tk.CENTER)


		# build the counter window
		self.counters = LabelFrame(root, text="Packet Statistics")
		self.buildStatisticsLabelFrame()

		# Place core elements on canvas
		self.textWidget.grid(row=1,column=0,columnspan=2,)
		self.canvas.grid(row=0,column=0,sticky="nw")
		self.counters.grid(row=0,column=1,sticky="n")

	
	def runGUIReceiver(self):
		# Start the GUI service on port 6666
		self.s = socket()
		port = 6666
		self.s.bind(('127.0.0.1',port))
		print("Calling receive()")
		
		labelThread = Thread(target=self.updateStatisticsLabels)
		labelThread.start()
		
		self.receiver = Thread(target=self.receive, args=(self.s,))
		self.receiver.start()
		
	def receive(self, s):
		
		s.listen(4)
		c = s.accept()[0]

		BUFSIZ = 200
		
		while True:
			try:
				msg = c.recv(BUFSIZ).decode()
				# decode the JSON string
				data = json.loads(msg)

				self.receivedPacketCount += 1

				self.intactPacketCount += 1

				if data['sig']:
					self.authenticatedPacketCount += 1
				if data['recent']:
					self.ontimePacketCount += 1


				update = Thread(target=self.newPacket, args=(self.threadlock, 0, data['x'], data['y'], data['heading'], data['sig'], data['recent'], data['receiver'], data['elapsed'],))
				update.start()

			except json.decoder.JSONDecodeError as jsonError:
				print(msg)
				print("JSON decoding error - invalid data. Discarding.")
			except Exception as e:
				print("=====================================================================================")
				print("Error processing packet. Exception type:")
				print(type(e))
				print("")
				print("Error message:")
				print(e)
				print("End error message")
				print("=====================================================================================")

	def newPacket(self, lock, carid, x, y, heading, isValid, isRecent, isReceiver, elapsedTime):
		
		# cast coordinates to integers
		x = float(x)
		y = float(y)
		
		# load the appropriate image, depending on signature validation and whether the packet is local
		i = None
		if isReceiver:
			i = ImageTk.PhotoImage(Image.open("pic/receiver/" + heading + ".png"))
		else:
			if isValid:
				i = ImageTk.PhotoImage(Image.open("pic/" + heading + ".png"))
			else:
				i = ImageTk.PhotoImage(Image.open("pic/phantom/" + heading + ".png"))

		self.canvas.create_image(x, y, image=i, anchor=tk.CENTER, tags="car" + str(threading.currentThread().ident))
		
		with lock:
			# print results
			if not isReceiver:
				check = u'\u2713'
				rejected = u'\u2716'
				
				self.textWidget.insert(tk.END, "==========================================\n","black")
				if isValid:
					
					self.textWidget.insert(tk.END, check + "Message successfully authenticated\n","valid")
				else:
					self.textWidget.insert(tk.END, rejected + "Invalid signature!\n","attack")
				
				if isRecent:
					if elapsedTime > 0:
						self.textWidget.insert(tk.END, check + "Message is recent: " + str(round(elapsedTime,2)) + " milliseconds elapsed since transmission\n","valid")
					else:
						self.textWidget.insert(tk.END, check + "Message is recent: 0 milliseconds elapsed since transmission\n","valid")
						self.textWidget.insert(tk.END, "Message has future timestamp - check clock synchronization!\n", "information")
				else:
					self.textWidget.insert(tk.END, rejected + "Message out-of-date: " + str(round(elapsedTime,2)) + " milliseconds elapsed since transmission\n","information")
				
				if not isValid and not isRecent:
					self.textWidget.insert(tk.END, rejected + "!!!--- Invalid signature AND message expired: replay attack likely! ---!!!\n","attack")
				
				self.textWidget.insert(tk.END, "Vehicle reports location at (" + str(x) + "," + str(y) + "), traveling " + heading + "\n", "black")

				self.textWidget.insert(tk.END, "==========================================\n","black")
				self.textWidget.see(tk.END)
		time.sleep(0.1)

		self.canvas.delete("car" + str(threading.currentThread().ident))
		self.processedPacketCount += 1

	def updateStatisticsLabels(self):
		while True:
			if self.receivedPacketCount == 0:
				continue
			self.receivedPacketCountText.set("Received:")
			self.processedPacketCountText.set("Processed:")
			self.authenticatedPacketCountText.set("Authentic:")
			self.intactPacketCountText.set("Intact:")
			self.ontimePacketCountText.set("On time:")

			self.receivedPacketCountValueText.set(str(self.receivedPacketCount))
			self.processedPacketCountValueText.set(str(self.processedPacketCount))
			self.authenticatedPacketCountValueText.set(str(self.authenticatedPacketCount))
			self.intactPacketCountValueText.set(str(self.intactPacketCount))
			self.ontimePacketCountValueText.set(str(self.ontimePacketCount))
			
			self.receivedPacketCountPercentageText.set(str(round((self.receivedPacketCount/self.receivedPacketCount)*100,2)) + "%")
			self.processedPacketCountPercentageText.set(str(round((self.processedPacketCount/self.receivedPacketCount)*100,2)) + "%")
			self.authenticatedPacketCountPercentageText.set(str(round((self.authenticatedPacketCount/self.receivedPacketCount)*100,2)) + "%")
			self.intactPacketCountPercentageText.set(str(round((self.intactPacketCount/self.receivedPacketCount)*100,2)) + "%")
			self.ontimePacketCountPercentageText.set(str(round((self.ontimePacketCount/self.receivedPacketCount)*100,2)) + "%")

			time.sleep(0.1)

	def buildStatisticsLabelFrame(self):
		self.receivedPacketCountLabel = Label(self.counters, textvariable=self.receivedPacketCountText)	
		self.processedPacketCountLabel = Label(self.counters, textvariable=self.processedPacketCountText)	
		self.authenticatedPacketCountLabel = Label(self.counters, textvariable=self.authenticatedPacketCountText)	
		self.intactPacketCountLabel = Label(self.counters, textvariable=self.intactPacketCountText)	
		self.ontimePacketCountLabel = Label(self.counters, textvariable=self.ontimePacketCountText)

		self.receivedPacketCountValue = Label(self.counters, textvariable=self.receivedPacketCountValueText)	
		self.processedPacketCountValue = Label(self.counters, textvariable=self.processedPacketCountValueText)	
		self.authenticatedPacketCountValue = Label(self.counters, textvariable=self.authenticatedPacketCountValueText)	
		self.intactPacketCountValue = Label(self.counters, textvariable=self.intactPacketCountValueText)	
		self.ontimePacketCountValue = Label(self.counters, textvariable=self.ontimePacketCountValueText)

		self.receivedPacketCountPercentage = Label(self.counters, textvariable=self.receivedPacketCountPercentageText)	
		self.processedPacketCountPercentage = Label(self.counters, textvariable=self.processedPacketCountPercentageText)	
		self.authenticatedPacketCountPercentage = Label(self.counters, textvariable=self.authenticatedPacketCountPercentageText)	
		self.intactPacketCountPercentage = Label(self.counters, textvariable=self.intactPacketCountPercentageText)	
		self.ontimePacketCountPercentage = Label(self.counters, textvariable=self.ontimePacketCountPercentageText)

		self.receivedPacketCountLabel.grid(row=0, column=0)
		self.processedPacketCountLabel.grid(row=1, column=0)
		self.authenticatedPacketCountLabel.grid(row=2, column=0)
		self.intactPacketCountLabel.grid(row=3, column=0)
		self.ontimePacketCountLabel.grid(row=4, column=0)

		self.receivedPacketCountValue.grid(row=0, column=1, padx=(10,10))
		self.processedPacketCountValue.grid(row=1, column=1, padx=(10,10))
		self.authenticatedPacketCountValue.grid(row=2, column=1, padx=(10,10))
		self.intactPacketCountValue.grid(row=3, column=1, padx=(10,10))
		self.ontimePacketCountValue.grid(row=4, column=1, padx=(10,10))

		self.receivedPacketCountPercentage.grid(row=0, column=2)
		self.processedPacketCountPercentage.grid(row=1, column=2)
		self.authenticatedPacketCountPercentage.grid(row=2, column=2)
		self.intactPacketCountPercentage.grid(row=3, column=2)
		self.ontimePacketCountPercentage.grid(row=4, column=2)
	
	def printCounters(self):
		while True:
			print(str(self.receivedPacketCount))
			print(str(self.processedPacketCount))
			print(str(self.authenticatedPacketCount))
			print(str(self.intactPacketCount))
			print(str(self.ontimePacketCount))
			time.sleep(2)


	
