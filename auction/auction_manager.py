import log
import config as cfg
import socket as skt
import sys
import json

class AuctionManager:
	def __init__(self):
		self.__stop_listening = False

	def startWorking(self):
		self.startListening()

	def stopWorking(self):
		log.high_debug("Asking loop to return...")
		self.__stop_listening = True

	### TODO: this, along with every socket related operation, should probably 
	### be an independent module, sharing functionality across all modules

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
		log.debug(str(server_address))
		response_data = None

		try:
			serialized_data = json.dumps(data)

			log.debug("Sending {} bytes to {}:{}".format(
				len(serialized_data),
				ip,
				port))

			sent_bytes = self.__socket.sendto(serialized_data.encode("UTF-8"), server_address)

			self.__socket.settimeout(2)
			response_data, server = self.__socket.recvfrom(4096)
			log.debug("Received {!r}".format(response_data))

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

			# Check if we've been asked to stop listening
			if self.__stop_listening:
				log.high_debug("STOPPING listenLoop!")
				return None
				
			log.info("Listening...")

			# Restore socket to blocking mode
			self.__socket.settimeout(None)
			# try:
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

				elif native_data["operation"] == "validate-bid":
					response_data = self.handleBidValidationRequest(native_data)

				else:
					log.error("Unknown operation requested!")

				if response_data != None:
					# log.high_debug(str(self.__socket))
					log.high_debug("Sending response to origin...")
					self.__socket.sendto(json.dumps(response_data).encode(), address)

				# log.info("Sent {} bytes as a response to {}".format(
				# 	sent_bytes,
				# 	address))
				# # self.handleRequest(address, data
				# log.info("Successfully processed request from {} of operation type: {}".format(address, native_data["operation"]))
				# log.info("Operation: {} from {} => OK".format(native_data["operation"], address))

			else:
				log.error("Data is corrupted or client disconneted!")

	####							 	####	
	####	Incoming request handlers	####
	####								####

	### Builds default parameters of response packet
	def buildResponse(self, operation, params=None):
		data_dict = {
			"id-type": "auction-manager",
			"packet-type": "response",
			"operation": operation 
		}
		if params != None:
			data_dict.update(params)

		return data_dict

	### 
	def handleAuctionCreationRequest(self):
		log.high_debug("Hit handleAuctionCreationRequest!")

	### Handles incoming heartbeat request
	### data: should be a valid message of the defined protocol structure
	def handleHeartbeatRequest(self, data):
		log.high_debug("Hit handleHeartbeatRequest!")
		log.info("Operation: {} from client-sn:  {} => OK".format(data["operation"], data["client-sn"]))

		return {
			"id-type": "auction-manager",
			"packet-type": "response",
			"operation": "heartbeat" 
		}

	### Handles incoming Create Auction request
	def handleCreateAuctionRequest(self, data):
		log.high_debug("Hit handleCreateAuctionRequest!")

		log.debug(str(data))
		# TODO: Check if data is valid!

		# Replace identity type
		data["id-type"] = "auction-manager"
		
		repo_response = self.__sendRequestAndWait("repo", data)

		if not "operation-error" in repo_response:
			log.info("Operation: {} from client-sn: {} => OK [ADDED auction: {}]".format(
				data["operation"], 
				data["client-sn"],
				data["auction-name"]))

		else:
			log.info("Operation: {} from client-sn: {} => FAILED [Could NOT add auction: {}]".format(
				data["operation"], 
				data["client-sn"],
				data["auction-name"]))

		repo_response["id-type"] = "auction-manager"

		return repo_response

	### Handles incoming delete auction request
	def handleTerminateAuctionRequest(self, data):
		log.high_debug("Hit handleDeleteAuctionRequest!")
		
		data["id-type"] = "auction-manager"

		repo_response = self.__sendRequestAndWait("repo", data)

		if not "operation-error" in repo_response:
			log.info("Operation: {} from client-sn: {} => OK [TERMINATED auction-sn: {}]".format(
				data["operation"], 
				data["client-sn"],
				data["auction-sn"]))

		else:
			log.info("Operation: {} from client-sn:  {} => FAILED [Could NOT find  ACTIVE auction-sn {}]".format(
				data["operation"], 
				data["client-sn"],
				data["auction-sn"]))

		repo_response["id-type"] = "auction-manager"

		return repo_response

	### Handles incoming create bid request
	def handleBidValidationRequest(self, data):
		log.high_debug("Hit handleBidValidationRequest!")

		response = self.buildResponse("validate-bid", {"bid-is-valid": True})

		log.info("Operation: {} from Auction Repo => OK [Client-SN: {} Auction SN: {} Bid Value: {}]".format(
			data["operation"], 
			data["client-sn"],
			data["auction-sn"],
			data["bid-value"]))

		return response
