import log
import config as cfg
import socket as skt
import sys
import json

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
		log.high_debug("Hit listenLoop!")

		while True:
			data, address = self.__socket.recvfrom(4096)
			decoded_data = data.decode()
			native_data = json.loads(decoded_data)
			# print(native_data)
			log.high_debug("Received {} bytes from {}".format(
				len(data),
				address
				))

			# TODO: handle client disconnection
			if data:
				response_data = None

				if native_data["operation"] == "heartbeat":
					response_data = self.handleHeartbeatRequest()
				else:
					log.error("Unknown operation requested!")

				if response_data != None:
					self.__socket.sendto(json.dumps(response_data).encode(), address)

				# log.info("Sent {} bytes as a response to {}".format(
				# 	sent_bytes,
				# 	address))
				# # self.handleRequest(address, data
			else:
				log.error("Data is corrupted or client disconneted!")

	### Handles incoming request and delegates accordingly
	def handleRequest(self, address, data):
		log.high_debug("Hit handleRequest!")

	### Handles incoming heartbeat request
	def handleHeartbeatRequest(self):
		return {
			"id-type": "auction-manager",
			"packet-type": "response",
			"operation": "heartbeat" 
		}
	
	####							 	####	
	####	Incoming request handlers	####
	####								####

	### 
	def handleAuctionCreationRequest(self):
		log.high_debug("Hit handleAuctionCreationRequest!")


c = AuctionManager()