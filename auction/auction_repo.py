import log
import config as cfg
import socket as skt
import sys
import json

from auction import Auction

class AuctionRepo:
	
	def __init__(self):
		self.__auctionsList = []
		self.__auctionIndex = 0

		self.startListening()

	def startListening(self):
		self.__IP = cfg.CONFIG["AuctionRepo"]["IP"]

		# TODO: Should check if int conversion goes wrong
		self.__PORT = int(cfg.CONFIG["AuctionRepo"]["PORT"])

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
					response_data = self.handleHeartbeatRequest(native_data)

				elif native_data["operation"] == "create-auction":
					response_data = self.handleCreateAuctionRequest(native_data)

				elif native_data["operation"] == "delete-auction":
					response_data = self.handleDeleteAuctionRequest(native_data)				

				elif native_data["operation"] == "list-auctions":
					response_data = self.handleListAuctionsRequest(native_data)

				else:
					log.error("Unknown operation requested!")

				# log.high_debug("HERE: " + str(response_data))
				if response_data != None:
					log.debug("Sending response to origin...")
					self.__socket.sendto(json.dumps(response_data).encode(), address)

				# log.info("Sent {} bytes as a response to {}".format(
				# 	sent_bytes,
				# 	address))
				# # self.handleRequest(address, data
				log.info("Successfully processed request from {} of operation type: {}".format(address, native_data["operation"]))
			else:
				log.error("Data is corrupted or client disconneted!")

	####							 	####	
	####	Incoming request handlers	####
	####								####

	### Handles incoming heartbeat request
	### data: should be a valid message of the defined protocol structure
	def handleHeartbeatRequest(self, data):
		log.high_debug("Hit handleHeartbeatRequest!")

		return {
			"id-type": "auction-manager",
			"packet-type": "response",
			"operation": "heartbeat" 
			}

	### 
	def handleCreateAuctionRequest(self, data):
		log.high_debug("Hit handleCreateAuctionRequest!")
		log.debug(str(data))

		# TODO: VALIDATE DATA

		# Generate unique serial number
		# TODO: actually generate a unique serial number 

		auction = Auction(
			data["auction-name"],
			self.__auctionIndex,
			data["auction-duration"],
			data["auction-description"],
			data["auction-type"])

		self.__auctionIndex = self.__auctionIndex + 1

		self.__auctionsList.append(auction)

		log.info("Successfully added auction to list!")

		return {
			"id-type": "auction-repo",
			"packet-type": "response",
			"operation": "create-auction" 
			}

	### Handles incoming delete auction request
	def handleDeleteAuctionRequest(self, data):
		log.high_debug("Hit handleDeleteAuctionRequest!")

	### Handles incoming list auctions request
	def handleListAuctionsRequest(self, data):
		log.high_debug("Hit handleListAuctionsRequest!")

		log.high_debug(str(self.__auctionsList))

		return {
			"id-type": "auction-repo",
			"packet-type": "response",
			"operation": "list-auctions" ,
			"auctions-list": [d.__dict__() for d in self.__auctionsList]
			}
