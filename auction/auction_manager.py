import log
import config as cfg
import socket as skt
import sys
import json
from pprint import pprint
import copy
from certificates import validate_request, sign_data_with_cc, extract_auth_certificate, get_name_from_cert, sign_data_with_priv_key, verify_signature_static_key
from crypto_utils import *

class AuctionManager:
	__auctions = {}

	def __init__(self):
		# auction_id: ["symmetric key to be used to hide values"]
		self.__auctions = {}
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

			encoded_data = serialized_data.encode("UTF-8")
			log.debug("Sending {} bytes".format(len(encoded_data)))

			sent_bytes = self.__socket.sendto(serialized_data.encode("UTF-8"), server_address)

			self.__socket.settimeout(2)
			response_data, server = self.__socket.recvfrom(16384)
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

		log.debug("Trying to listen on {0}:{1}".format(
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

				elif native_data["operation"] == "create-bid":
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

	def addAuction(self):
		self.__auctions[self.__auctions_idx] = []
		self.__auctions_idx = self.__auctions_idx + 1

	####							 	####	
	####	Incoming request handlers	####
	####								####

	### Builds default parameters of response packet
	def buildResponse(self, operation, params=None):
		data_dict = {
			"id-type": "auction-manager",
			"operation": operation 
		}
		if params != None:
			data_dict.update(params)

		return data_dict


	def buildRequest(self, operation, params=None):
		pass

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

		log.high_debug("Received Create Auction Request:\n " + str(data))

		# Check certificate chain and signature
		self.validate_client_request(data)

		# Sign with Manager private key
		self.sign_data(data)

		repo_response = self.__sendRequestAndWait("repo", data)

		# Validate repo response

		if not "operation-error" in repo_response:
			log.info("Operation: {} from client-sn: {} => OK [ADDED auction: {}]".format(
				data["operation"], 
				data["client-sn"],
				data["data"]["auction-name"]))

		else:
			log.info("Operation: {} from client-sn: {} => FAILED [Could NOT add auction: {}]".format(
				data["operation"], 
				data["client-sn"],
				data["data"]["auction-name"]))

			return repo_response

		log.debug(repo_response)

		if not self.validate_repo_request(repo_response):
			log.warning("Could not verify Repository's authenticity! Aborting")
			repo_response["operation-error"] = "Could not verify Repository's authenticity! Aborting"
		
		else:
			log.debug("Repository authenticity verified")

		return repo_response

	### Handles incoming delete auction request
	def handleTerminateAuctionRequest(self, data):
		log.high_debug("Hit handleDeleteAuctionRequest!")
		
		# data["id-type"] = "auction-manager"

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

		# repo_response["id-type"] = "auction-manager"

		return repo_response

	### Handles incoming create bid request
	def handleBidValidationRequest(self, data):
		log.high_debug("Hit handleBidValidationRequest!")

		is_valid = self.validate_client_request(data)

		if is_valid != True:
			# In case of error, is_valid holds the error message
			data["operation-error"] = is_valid

			return data

		data_dict = data["data"]
		data["bid-is-valid"] = True

		# response = self.buildResponse("validate-bid", {"bid-is-valid": True})
		# Sign data
		self.sign_data(data)

		log.info("Operation: {} from Auction Repo => OK [Client-SN: {} Auction SN: {} Bid Value: {}]".format(
			data["operation"], 
			data["client-sn"],
			data_dict["auction-sn"],
			data_dict["bid-value"]))

		return data

	def validate_client_request(self, data):
		# signed_data = copy.deepcopy(data)
		# signed_data.pop("repo-signature", None)

		cert = bytes.fromhex(data["client-certificate"])

		if data["is-identity-hidden"]:
			hybrid_key = bytes.fromhex(data["hybrid-cert-key"])

			priv_key = load_rsa_private_key(cfg.CONFIG["AuctionManager"]["PRIVATE_KEY_FILE_PATH"])

			sym_key = decrypt_data_asym(hybrid_key, priv_key)

			# log.debug("HYBRID KEY:" + str(hybrid_key))
			# log.debug("SYM key: " + str(sym_key))

			# log.debug("CERT type: " + str(type(cert)))

			cert = decrypt_data_sym(cert, bytes(sym_key))

		is_request_valid = validate_request(json.dumps(data["data"], sort_keys=True), cert, data["client-signature"])

		if not is_request_valid:
			error_string = "Auction request failed because client certificate failed to be verified or the signature did not match!"
			log.warning(error_string)
			# TODO: handle gracefully. Should send back an answer to client explaining why it failed
			# return self.buildResponse(data["operation"], { "operation-error": "Certificate or signature check failed!" })
			return error_string

		log.info("Certificate passed check? " + str(is_request_valid))

		return True

	def validate_repo_request(self, data):
		signed_data = copy.deepcopy(data)
		# signed_data.pop("client-signature", None)
		signed_data.pop("repo-signature", None)

		is_request_valid = verify_signature_static_key(cfg.CONFIG["AuctionRepo"]["PUBLIC_KEY_FILE_PATH"], json.dumps(signed_data, sort_keys=True), bytes.fromhex(data["repo-signature"]))
		log.debug("Repository authenticity verified? " + str(is_request_valid))
		return is_request_valid

	def sign_data(self, data):
		# Sign data with Manager priv key
		manager_signature = sign_data_with_priv_key(json.dumps(data, sort_keys=True), load_rsa_private_key(cfg.CONFIG["AuctionManager"]["PRIVATE_KEY_FILE_PATH"]))
		data["manager-signature"] = manager_signature.hex()
