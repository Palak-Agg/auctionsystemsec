import log
import config as cfg
import socket as skt
import sys
import json
import threading
import time
import datetime
import traceback

from auction import Auction

lock = threading.Lock()

class AuctionRepo:
	
	def __init__(self):
		self.__auctionsList = []
		self.__auctionIndex = 0

		self.__checkAuctionsThread = threading.Thread(target=self.checkAuctionsDurationLoop)
		self.__checkAuctionsThread.start()

		self.startListening()

	### Sends content to specified target and waits
	### for response.
	### target: manager OR repo
	### operation: one of the possible operation types
	### data: content to be sent
	def __sendRequestAndWait(self, target, data):
		log.high_debug("Hit sendRequestAndWait!")
		# self.__socket = skt.socket(skt.AF_INET, skt.SOCK_DGRAM)

		dict_key = "AuctionRepo"
		if (target.lower() == "manager"):
			dict_key = "AuctionManager"

		ip = cfg.CONFIG[dict_key]["IP"]
		port = int(cfg.CONFIG[dict_key]["PORT"])

		server_address = (ip, port)
		log.high_debug(str(server_address))
		response_data = None

		try:
			serialized_data = json.dumps(data)

			log.high_debug("Sending {} bytes to {}:{}".format(
				len(serialized_data),
				ip,
				port))

			sent_bytes = self.__socket.sendto(serialized_data.encode("UTF-8"), server_address)

			self.__socket.settimeout(2)
			response_data, server = self.__socket.recvfrom(4096)
			log.high_debug("Received {!r}".format(response_data))

		# except Exception as e:
		# 	log.error(str(e))

		except skt.timeout as e:
			log.error("No response from peer, closing socket...")
			raise e

		finally:
			log.high_debug("Hit finally clause of __sendRequestAndWait")
		
		if response_data != None:
			return json.loads(response_data)

		return None


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

		log.high_debug("Trying to listening on {0}:{1}".format(
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
			log.info("Listening...")
			self.__socket.settimeout(None)
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

				elif native_data["operation"] == "create-bid":
					response_data = self.handleCreateBidRequest(native_data)

				elif native_data["operation"] == "list-bids":
					response_data = self.handleListBidsRequest(native_data)

				else:
					log.error("Unknown operation requested!")

				log.high_debug("Processed request...")
				# log.high_debug("HERE: " + str(response_data))
				if response_data != None:
					log.high_debug("Sending response to origin...")
					self.__socket.sendto(json.dumps(response_data).encode(), address)

				# log.info("Sent {} bytes as a response to {}".format(
				# 	sent_bytes,
				# 	address))
				# # self.handleRequest(address, data
				# log.info("Operation: {} from {} => OK".format(native_data["operation"], address))
			else:
				log.error("Internal socket error!!!")

	### Checks auction termination date indefinitely (runs on its own thread) 
	def checkAuctionsDurationLoop(self):
		log.high_debug("Hit checkAuctionsDurationLoop!")

		while True:
			lock.acquire()

			for a in [d for d in self.__auctionsList if d.isActive]:
				if a.endTime < time.time():
					a.isActive = False
					log.info("Auction \'{}\' with SN:{} set to terminate on {} has reached an end.".format(
						a.name,
						a.serialNumber,
						datetime.datetime.utcfromtimestamp(a.endTime)))

					### Determine who won. There's no need to do this now, but it makes sense
					a.getWinningBid()

			lock.release()

			time.sleep(.500)

	####							 	####	
	####	Incoming request handlers	####
	####								####

	### Builds default parameters of response packet
	def buildResponse(self, operation, params=None):
		data_dict = {
			"id-type": "auction-repo",
			"packet-type": "response",
			"operation": operation 
		}
		if params != None:
			data_dict.update(params)

		return data_dict

	### Builds default parameters of request packet
	def buildRequest(self, operation, params=None):
		data_dict = {
			"id-type": "auction-repo",
			"packet-type": "request",
			"operation": operation 
		}
		if params != None:
			data_dict.update(params)

		return data_dict

	### Handles incoming heartbeat request
	### data: should be a valid message of the defined protocol structure
	def handleHeartbeatRequest(self, data):
		log.high_debug("Hit handleHeartbeatRequest!")

		log.info("Operation: {} from client-sn:  {} => OK".format(data["operation"], data["client-sn"]))

		return self.buildResponse("heartbeat")

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
			time.time(),
			data["auction-description"],
			data["auction-type"])

		self.__auctionIndex = self.__auctionIndex + 1

		lock.acquire()
		self.__auctionsList.append(auction)
		lock.release()

		log.info("Operation: {} from client-sn: {} => OK [ADDED auction: {}]".format(
			data["operation"], 
			data["client-sn"],
			data["auction-name"]))

		return self.buildResponse("create-auction")

	### Handles incoming delete auction request
	def handleTerminateAuctionRequest(self, data):
		log.high_debug("Hit handleTerminateAuctionRequest!")
		log.high_debug("Incoming data:" + str(data))

		lock.acquire()
		target_auct = [d for d in self.__auctionsList if d.serialNumber == data["auction-sn"] and d.isActive]
		lock.release()
		log.high_debug("Target auctions: " + str(target_auct))

		params = None

		if len(target_auct) > 1:
			log.error("INTERNAL ERROR. Duplicate serial numbers found on auctions list.")
			raise Exception("INTERNAL ERROR. Duplicate serial numbers found on auctions list.")

		elif len(target_auct) == 1:
			# self.__auctionsList.remove(target_auct[0])
			target_auct[0].isActive = False

			log.info("Operation: {} from client-sn: {} => OK [TERMINATED auction: {}]".format(
				data["operation"], 
				data["client-sn"],
				target_auct[0].name))

			# Operation OK, no need for additional parameters on response
		else:
			log.error("Operation: {} from client-sn:  {} => FAILED [Could NOT find  ACTIVE auction {}]".format(
				data["operation"], 
				data["client-sn"],
				data["auction-sn"]))

			params = {
				"operation-error": "No ACTIVE auction was found by the specified serial number!"				
				}

		return self.buildResponse("terminate-auction", params)

		### TODO: should I notify the clients the auction has been terminated?
		### If so, how?

	### Handles incoming list auctions request
	def handleListAuctionsRequest(self, data):
		log.high_debug("Hit handleListAuctionsRequest!")

		auctions_list = []
		params = {}
		
		lock.acquire()
		if data["auctions-list-filter"] == "active":
			auctions_list = [d.__dict__() for d in self.__auctionsList if d.isActive] 

		elif data["auctions-list-filter"] == "inactive":
			auctions_list = [d.__dict__() for d in self.__auctionsList if not d.isActive]

		else:
			auctions_list = [d.__dict__() for d in self.__auctionsList]

		params["auctions-list"] = auctions_list
		log.high_debug(str(auctions_list))

		lock.release()

		log.info("Operation: {} from client-sn: {} => OK ".format(
			data["operation"], 
			data["client-sn"]))

		return self.buildResponse("list-auctions", params)

	### Handles incoming create bid request
	def handleCreateBidRequest(self, data):
		log.high_debug("Hit handleCreateBidRequest!")
		log.debug("Data: " + str(data))

		# Ask manager to validate bid
		request_params = {
			"auction-sn": data["auction-sn"],
			"client-sn": data["client-sn"],
			"bid-value": data["bid-value"]
			}

		request_data_dict = self.buildRequest("validate-bid", request_params)

		validate_response = self.__sendRequestAndWait("manager", request_data_dict)

		response_params = None

		if validate_response["bid-is-valid"] == False:
			# Return right away if not valid
			response_params = {"operation-error": "Bid did not pass the validation process by the Auction Manager!"}
			return self.buildResponse("create-bid", response_params)

		log.debug("Auction Manager validated bid...")

		try:
			auction_sn = int(data["auction-sn"])
			matched_auctions = [d for d in self.__auctionsList if d.serialNumber == auction_sn and d.isActive]

			if len(matched_auctions) == 0:

				log.error("Operation: {} from client-sn: {} => FAILED [{}] ".format(
					data["operation"], 
					data["client-sn"],
					"No ACTIVE auctions were found by SN!"))				

				response_params = {"operation-error": "No ACTIVE auctions were found by that Serial Number!"}

			else:
				target_auction = matched_auctions[0]

				target_auction.addNewBid(data["client-sn"], data["bid-value"])

				log.high_debug(target_auction)

				log.info("Operation: {} from client-sn: {} => OK [Bid of: {} on auction-sn: {}]".format(
					data["operation"], 
					data["client-sn"],
					data["bid-value"],
					data["auction-sn"]))	

		except Exception as e:
			log.error("Operation: {} from client-sn: {} => FAILED [] ".format(
				data["operation"], 
				data["client-sn"]))				
			response_params = {"operation-error": "A server internal error occured!"}

			log.error(str(e))

		return self.buildResponse("create-bid", response_params)

	### Handles incoming request to list bids filtered by client-sn or auction-sn
	def handleListBidsRequest(self, data):
		log.high_debug("Hit handleListBidsRequest!")
		bids_list = []

		params = {}

		if data["bids-list-filter"] == "client":
			client_sn = int(data["client-sn"])

			for a in self.__auctionsList:
				bids_list = bids_list + [d for d in a.bidsList() if d.clientId == client_sn]
				
		elif data["bids-list-filter"] == "auction":
			log.high_debug("HIT AUCTION FILTER")

			auction_sn = int(data["auction-sn"])

			target_auction = [d for d in self.__auctionsList if d.serialNumber == auction_sn]

			if len(target_auction) > 1:
				log.error("INTERNAL ERROR. Duplicate serial numbers found on auctions list.")
				raise Exception("INTERNAL ERROR. Duplicate serial numbers found on auctions list.")

			elif len(target_auction) == 1:
				target_auction = target_auction[0]
				bids_list = target_auction.bidsList()

				log.info("Operation: {} from client-sn: {} => OK [#Bids: {}]".format(
					data["operation"], 
					data["client-sn"],
					len(bids_list)))

				# Operation OK, no need for additional parameters on response
			else:
				log.error("Operation: {} from client-sn:  {} => FAILED [Could NOT find  ACTIVE auction {}]".format(
					data["operation"], 
					data["client-sn"],
					data["auction-sn"]))

				params = {
					"operation-error": "No ACTIVE auction was found by the specified serial number!"				
					}

		params["bids-list"] = [d.__dict__() for d in bids_list]	

		log.high_debug(params["bids-list"])

		return self.buildResponse("list-bids", params)

