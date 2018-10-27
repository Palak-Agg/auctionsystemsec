import log
import config as cfg
import socket as skt
import sys

class AuctionManager:
	
	def __init__(self):
		self.startListening()

	def startListening(self):
		self.__IP = cfg.CONFIG["AuctionManager"]["IP"]

		# TODO: Should check if int conversion goes wrong
		self.__PORT = int(cfg.CONFIG["AuctionManager"]["PORT"])

		# log.debug("Read {0}:{1}".format(
		# 	self.__IP,
		# 	self.__PORT))

		# Create UDP socket
		self.__socket = skt.socket(skt.AF_INET, skt.SOCK_DGRAM)

		# Bind socket to the port
		server_address = (self.__IP, self.__PORT)

		log.debug("Trying to listening on {0}:{1}".format(
			self.__IP,
			self.__PORT))

		self.__socket.bind(server_address)

		log.info("Listening on {0}:{1}".format(
			self.__IP,
			self.__PORT))

		self.listenLoop()

	### Socket listening loop
	def listenLoop(self):
		log.high_debug("Hit handleRequest!")

		while True:
			data, address = self.__socket.recvfrom(4096)

			log.debug("Received {} bytes from {}".format(
				len(data),
				address
				))

		# TODO: handle client disconnection
		if data:
			self.handleRequest(address, data)

	### Handles incoming request and delegates accordingly
	def handleRequest(self, address, data):
		log.high_debug("Hit handleRequest!")

	
	####							 	####	
	####	Incoming request handlers	####
	####								####

	### 
	def handleAuctionCreationRequest(self):
		log.high_debug("Hit handleAuctionCreationRequest!")

	


v = AuctionManager()