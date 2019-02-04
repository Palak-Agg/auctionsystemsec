import log
import config as cfg
import socket as skt
import sys
import json
import threading
import time
import datetime
import traceback
from pprint import pprint
import copy
from certificates import validate_request, sign_data_with_cc, extract_auth_certificate, get_name_from_cert, sign_data_with_priv_key, verify_signature_static_key
from crypto_utils import *
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

			encoded_data = serialized_data.encode("UTF-8")
			log.debug("Sending {} bytes".format(len(encoded_data)))


			sent_bytes = self.__socket.sendto(serialized_data.encode("UTF-8"), server_address)

			self.__socket.settimeout(2)
			response_data, server = self.__socket.recvfrom(16384)
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
			data, address = self.__socket.recvfrom(16384)
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
					a.getHighestBid()

			lock.release()

			time.sleep(.500)

	####							 	####	
	####	Incoming request handlers	####
	####								####

	### Builds default parameters of response packet
	def buildResponse(self, operation, params=None):
		data_dict = {
			"id-type": "auction-repo",
			"operation": operation 
		}
		if params != None:
			data_dict.update(params)

		return data_dict

	### Builds default parameters of request packet
	def buildRequest(self, operation, params=None):
		data_dict = {
			"id-type": "auction-repo",
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

		log.debug("------------")
		log.debug(data)

		if not self.validate_manager_request(data):
			log.warning("Request failed because manager failed to be verified or the signature did not match!")
			# TODO: handle gracefully. Should send back an answer to client explaining why it failed
			return self.buildResponse(data["operation"], { "operation-error": "Certificate or signature check failed!" })

		else:
			log.debug("Manager authenticity verified")

		self.sign_data(data)

		# Generate unique serial number
		# TODO: actually generate a unique serial number
		data_dict = data["data"]

		auction = Auction(
			data_dict["auction-name"],
			self.__auctionIndex,
			data_dict["auction-duration"],
			time.time(),
			data_dict["auction-description"],
			data_dict["auction-type"])

		self.__auctionIndex = self.__auctionIndex + 1

		lock.acquire()
		self.__auctionsList.append(auction)
		lock.release()

		# TODO: SIGN DATA FROM MANAGER
		log.info("Operation: {} from client-sn: {} => OK [ADDED auction: {}]".format(
			data["operation"], 
			data["client-sn"],
			data_dict["auction-name"]))

		log.debug(data)

		return self.buildResponse("create-auction", data)

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

		data_dict = data["data"]
		
		lock.acquire()

		if data_dict["auctions-list-filter"] == "active":
			auctions_list = [d.__dict__() for d in self.__auctionsList if d.isActive] 

		elif data_dict["auctions-list-filter"] == "inactive":
			auctions_list = [d.__dict__() for d in self.__auctionsList if not d.isActive]

		elif data_dict["auctions-list-filter"] == "client-outcome":
			log.high_debug("HIT CLIENT OUTCOME FILTER")
			for a in self.__auctionsList:
				if a.isActive:
					continue

				# log.high_debug("DONE")
				# log.high_debug(a.bidsList())
				# log.high_debug([b.clientId for b in a.bidsList()])
				if int(data["client-sn"]) in [b.clientId for b in a.bidsList()]:
					auctions_list.append(a.__dict__())

		else:
			auctions_list = [d.__dict__() for d in self.__auctionsList]

		params["auctions-list"] = auctions_list
		log.high_debug("AUCTIONS:" + str(auctions_list))

		lock.release()

		log.info("Operation: {} with filter: {} from client-sn: {} => OK ".format(
			data["operation"],
			data_dict["auctions-list-filter"], 
			data["client-sn"]))

		return self.buildResponse("list-auctions", params)

	### Handles incoming create bid request
	def handleCreateBidRequest(self, data):
		log.high_debug("Hit handleCreateBidRequest!")
		log.high_debug("Data:\n " + str(data))
		data_dict = data["data"]

		# Ask manager to validate bid
		# request_params = {
		# 	"auction-sn": data_dict["auction-sn"],
		# 	"client-sn": data["client-sn"],
		# 	"bid-value": data_dict["bid-value"]
		# }

		# Sign and ask manager to validate client		
		self.sign_data(data)

		validated_response = self.__sendRequestAndWait("manager", data)

		if validated_response["bid-is-valid"] == False:
			log.warning("Bid did not pass Manager's validation process! Dropping it...")

			# Return right away if not valid
			response_params = {"operation-error": "Bid did not pass the validation process by the Auction Manager!"}

			response = self.buildResponse("create-bid", response_params)

			# Sign again since data has been updated
			self.sign_data(response)

			return response

		# Validate manager's authenticity
		if not self.validate_manager_request(validated_response):

			log.warning("Could not validate Manager's authenticity!")

			# Return right away if not valid
			response_params = {"operation-error": "Failed to verify Manager's authenticity! Aborting."}

			response = self.buildResponse("create-bid", response_params)

			# Sign again since data has been updated
			self.sign_data(response)

			return response

		# Sign client's original packet
		# self.sign_data(validated_response)

		response_params = validated_response
		log.debug("Auction Manager validated bid...")

		try:
			auction_sn = int(data_dict["auction-sn"])
			matched_auctions = [d for d in self.__auctionsList if d.serialNumber == auction_sn and d.isActive]

			if len(matched_auctions) == 0:

				log.error("Operation: {} from client-sn: {} => FAILED [{}] ".format(
					data["operation"], 
					data["client-sn"],
					"No ACTIVE auctions were found by SN!"))				

				response_params = {"operation-error": "No ACTIVE auctions were found by that Serial Number!"}

			else:
				target_auction = matched_auctions[0]
				log.high_debug(target_auction.getMinBidValue())

				# Check if greater than min
				if target_auction.type_of_auction == "English" and int(data_dict["bid-value"]) <= target_auction.getMinBidValue():
					response_params = {"operation-error": "Bid value is less or equal than the minimum value"}

					log.info("Operation: {} from client-sn: {} => FAILED [Bid of: {} on auction-sn: {} <= MIN value]".format(
						data["operation"], 
						data["client-sn"],
						data_dict["bid-value"],
						data_dict["auction-sn"]))	

				else:
					target_auction.addNewBid(data["client-sn"], data_dict["bid-value"], json.dumps(validated_response, sort_keys=True))

					log.high_debug(target_auction)

					log.info("Operation: {} from client-sn: {} => OK [Bid of: {} on auction-sn: {}]".format(
						data["operation"], 
						data["client-sn"],
						data_dict["bid-value"],
						data_dict["auction-sn"]))

		except Exception as e:
			log.error("Operation: {} from client-sn: {} => FAILED [{}] ".format(
				data["operation"], 
				data["client-sn"],
				str(e)))				

			response_params = {"operation-error": "A server internal error occured!"}

			log.error(str(e))

		response = self.buildResponse("create-bid", response_params)
		# self.sign_data(response_data)

		return response

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

	def validate_manager_request(self, data):
		# signed_data = copy.deepcopy(data)
		# signed_data.pop("manager-signature")
		# is_request_valid = verify_signature_static_key(cfg.CONFIG["AuctionManager"]["PUBLIC_KEY_FILE_PATH"], json.dumps(signed_data, sort_keys=True), bytes.fromhex(data["manager-signature"]))

		# if not is_request_valid:
			# log.warning("Request failed because client certificate failed to be verified or the signature did not match!")
			# TODO: handle gracefully. Should send back an answer to client explaining why it failed
			# return self.buildResponse(data["operation"], { "operation-error": "Certificate or signature check failed!" })

		# Sign data with Repository priv key
		# manager_signature = sign_data_with_priv_key(json.dumps(data, sort_keys=True), load_rsa_private_key(
		# 	cfg.CONFIG["AuctionRepo"]["PRIVATE_KEY_FILE_PATH"]))

		# data["repo-signature"] = manager_signature.hex()

		signed_data = copy.deepcopy(data)
		# signed_data.pop("client-signature", None)
		signed_data.pop("manager-signature", None)

		is_request_valid = verify_signature_static_key(cfg.CONFIG["AuctionManager"]["PUBLIC_KEY_FILE_PATH"], json.dumps(signed_data, sort_keys=True), bytes.fromhex(data["manager-signature"]))
		log.debug("Manager authenticity verified? " + str(is_request_valid))
		return is_request_valid

	def sign_data(self, data):
		# Sign data with Manager priv key
		repo_signature = sign_data_with_priv_key(json.dumps(data, sort_keys=True), load_rsa_private_key(
			cfg.CONFIG["AuctionRepo"]["PRIVATE_KEY_FILE_PATH"]))

		data["repo-signature"] = repo_signature.hex()

