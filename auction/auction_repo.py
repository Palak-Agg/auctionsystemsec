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

				elif native_data["operation"] == "terminate-auction":
					response_data = self.handleTerminateAuctionRequest(native_data)				

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
				# log.info("Operation: {} from {} => OK".format(native_data["operation"], address))
			else:
				log.error("Internal socket error!!!")

	####							 	####	
	####	Incoming request handlers	####
	####								####

	### Handles incoming heartbeat request
	### data: should be a valid message of the defined protocol structure
	def handleHeartbeatRequest(self, data):
		log.high_debug("Hit handleHeartbeatRequest!")

		log.info("Operation: {} from client-number:  {} => OK".format(data["operation"], data["client-number"]))

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

		log.info("Operation: {} from client-number: {} => OK [ADDED auction: {}]".format(
			data["operation"], 
			data["client-number"],
			data["auction-name"]))

		return {
			"id-type": "auction-repo",
			"packet-type": "response",
			"operation": "create-auction" 
			}

	### Handles incoming delete auction request
	def handleTerminateAuctionRequest(self, data):
		log.high_debug("Hit handleTerminateAuctionRequest!")
		log.high_debug("Incoming data:" + str(data))
		target_auct = [d for d in self.__auctionsList if d.serialNumber == data["auction-sn"] and d.isActive]
		log.high_debug("Target auctions: " + str(target_auct))

		if len(target_auct) > 1:
			log.error("INTERNAL ERROR. Duplicate serial numbers found on auctions list.")
			raise Exception("INTERNAL ERROR. Duplicate serial numbers found on auctions list.")

		elif len(target_auct) == 1:
			# self.__auctionsList.remove(target_auct[0])
			target_auct[0].isActive = False

			log.info("Operation: {} from client-number: {} => OK [TERMINATED auction: {}]".format(
				data["operation"], 
				data["client-number"],
				target_auct[0].name))

			return {
				"id-type": "auction-repo",
				"packet-type": "response",
				"operation": "terminate-auction"
				
				}
		else:
			log.info("Operation: {} from client-number:  {} => FAILED [Could NOT find  ACTIVE auction {}]".format(
				data["operation"], 
				data["client-number"],
				data["auction-sn"]))

			return {
				"id-type": "auction-repo",
				"packet-type": "response",
				"operation": "terminate-auction",
				"operation-error": "No ACTIVE auction was found by the specified serial number!"				
				}

		### TODO: should I notify the clients the auction has been terminated?
		### If so, how?

	### Handles incoming list auctions request
	def handleListAuctionsRequest(self, data):
		log.high_debug("Hit handleListAuctionsRequest!")

		auctions_list = None

		if data["auctions-list-filter"] == "active":
			auctions_list = [d.__dict__() for d in self.__auctionsList if d.isActive] 

		elif data["auctions-list-filter"] == "inactive":
			auctions_list = [d.__dict__() for d in self.__auctionsList if not d.isActive] 

		else:
			auctions_list = [d.__dict__() for d in self.__auctionsList]

		log.high_debug(str(auctions_list))

		log.info("Operation: {} from client-number: {} => OK ".format(
			data["operation"], 
			data["client-number"]))

		return {
			"id-type": "auction-repo",
			"packet-type": "response",
			"operation": "list-auctions",
			"auctions-list": auctions_list
			}
