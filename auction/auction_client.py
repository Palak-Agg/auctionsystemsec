import log
import socket as skt
import config as cfg
import json
from certificates import sign_data_with_cc, extract_auth_certificate, get_name_from_cert, verify_signature_static_key
from crypto_utils import *
import base64
from pprint import pprint
import os
import copy

class AuctionClient:

	### Alphanumeric string identifying the client
	### This will be replaced by the citizen card number
	ClientID = -1
	
	def __init__(self, clientNumber):
		log.high_debug("Hit AuctionClient __init__!")
		self.ClientID = clientNumber
		log.info("Client number: " + str(self.ClientID))

	### Save bid receipt to non-volatile memory
	def saveReceipt(self, data, cert, sym_key):
		log.high_debug("Hit saveReceipt!")

		if not os.path.exists("receipts"):
			os.makedirs("receipts")

		log.high_debug(str(cert))
		cc_name = get_name_from_cert(cert)

		file_path = "receipts/" + cc_name.replace(" ", "_") + ".receipt"

		# Make sure we get a non-existent file name
		counter = 0
		while True:
			if not os.path.isfile(file_path):
				break

			file_path = "receipts/" + cc_name.replace(" ", "_") + "_" + str(counter) + ".receipt"
			counter += 1

		with open(file_path, "w") as file:
			file.write("{},{},{},{}\n".format(hash_sha_str(cert).hex(), data["data"]["auction-sn"], data["data"]["bid-value"], sym_key.hex()))
			file.write(json.dumps(data))

	def loadReceipts(self):
		'''
			Return [[Recept dict, certificate hash, auction SN, bid value, SYM_KEY(used to encrypt bid value) ]]
		'''
		log.high_debug("Hit loadReceipt!")

		files = os.listdir("receipts")

		return_list = []

		for f in files:

			file = open("receipts/" + f)

			# Known data structure. First line == certificate hash, auction serial number, bid value, SYM KEY // Second line: receipt
			meta_data = file.readline()
			receipt = file.readline()
			meta_data_tokens = meta_data.split(',')

			if len(meta_data_tokens) == 3:
				return_list.append([json.loads(receipt), meta_data_tokens[0], meta_data_tokens[1], meta_data_tokens[2]])

			elif len(meta_data_tokens) == 4:
				return_list.append([json.loads(receipt), meta_data_tokens[0], meta_data_tokens[1], meta_data_tokens[2], meta_data_tokens[3]])

		log.high_debug(return_list)

		return return_list


	### Sends content to specified target and waits
	### for response.
	### target: manager OR repo
	### operation: one of the possible operation types
	### data: content to be sent
	def __sendRequestAndWait(self, target, data):
		log.high_debug("Hit sendRequestAndWait!")
		self.__socket = skt.socket(skt.AF_INET, skt.SOCK_DGRAM)

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

		except skt.timeout as e:
			log.error("No response from peer, closing socket...")
			raise e

		finally:
			self.__socket.close()
			log.high_debug("Hit finally clause of __sendRequestAndWait")
		
		log.high_debug("Response_data:\n" + str(response_data))
		if response_data != None:
			return json.loads(response_data)

		return None

	def setCertificate(self, data_dict, cert, is_identity_hidden, public_key=None, sym_key=None):
		data_dict["is-identity-hidden"] = is_identity_hidden

		if is_identity_hidden:
			# Generate symmetric key
			if sym_key == None:
				sym_key = generate_key()

			log.high_debug("Symmetric key: " + str(sym_key.hex()))

			# Create hybrid key, encrypting symmetric key using target's public key
			hybrid_key = encrypt_data_asym(sym_key, public_key)
			data_dict["hybrid-cert-key"] = bytes(hybrid_key).hex()

			cert = encrypt_data_sym(bytes(cert), sym_key)

		# Certificate in DER format
		data_dict["client-certificate"] = bytes(cert).hex()

	def setBidValue(self, data_dict, bid_value, is_value_hidden, public_key=None):
		sym_key = None
		if is_value_hidden:
			if public_key == None:
				raise ValueError("Public key was not specified!")

			# Generate symmetric key
			sym_key = generate_key()

			log.high_debug("Symmetric key: " + str(sym_key.hex()))

			# Create hybrid key, encrypting symmetric key using target's public key
			hybrid_key = encrypt_data_asym(sym_key, public_key)
			# data_dict["hybrid-bid-value-key"] = bytes(hybrid_key).hex()

			bid_value = encrypt_data_sym(bytes(bid_value), sym_key)

		data_dict["bid-value"] = bytes(bid_value).hex()

		return sym_key

	def buildRequest(self, operation, params, sign_data=False, target=None):
		data_dict = {
			"id-type": "auction-client",
			"client-sn": self.ClientID,
			"operation": operation,
			"data": params
		}

		return data_dict

	### Sends create auction request to the Auction Manager	
	def sendCreateAuctionRequest(self, name, description, duration, type_of_auction):
		log.high_debug("Hit sendCreateAuctionRequest!")

		params_dict = {
			"auction-name": name,
			"auction-description": description,
			"auction-duration": duration,
			"auction-type": type_of_auction,
		}

		# request = self.buildRequest()

		data_dict = self.buildRequest("create-auction", params_dict, True, "manager")

		self.sign_data(data_dict)

		log.high_debug("Create Auction Request:\n" + str(data_dict))
		response = self.__sendRequestAndWait("manager", data_dict)

		return response

	### Tests connectivity to the Auction Manager server ###
	def sendHeartbeatAuctionManager(self):
		log.high_debug("Hit sendHeartbeatAuctionManager!")
		data_dict = self.buildRequest("heartbeat")

		# try:
		response = self.__sendRequestAndWait("manager", data_dict)

		return response

	### Tests connectivity to the Auction Repository server ###
	def sendHeartbeatAuctionRepo(self):
		log.high_debug("Hit sendHeartbeatAuctionRepo!")
		data_dict = self.buildRequest("heartbeat")

		response = self.__sendRequestAndWait("repo", data_dict)

		return response

		# except skt.timeout:
		# 	log.error("Could not send Heartbeat to Auction Manager!")

	### Sends list auctions request to the Auction REPO
	def sendListAuctionsRequest(self, auctions_filter="all"):
		log.high_debug("Hit sendListAuctionsRequest!")

		params = {
			"auctions-list-filter": auctions_filter
		}

		data_dict = self.buildRequest("list-auctions", params)

		log.debug(str(data_dict))
		response = self.__sendRequestAndWait("repo", data_dict)

		if "auctions-list" in response:
			return response["auctions-list"]

		else:
			raise Exception("Failed to parse auctions-list!")


	### Sends terminate auction request to REPO
	def sendTerminateAuctionRequest(self, serialNumber):
		log.high_debug("Hit high_debug!")

		try:
			serialNumber = int(serialNumber)

			params = {
				"auction-sn": serialNumber
			}

			data_dict = self.buildRequest("terminate-auction", params)

			response = self.__sendRequestAndWait("manager", data_dict)

			if "operation-error" in response:
				raise Exception(response["operation-error"])
			return response

		except ValueError as e:
			log.error("Invalid data type! Serial Number must be an integer!")

	### Sends create bid request
	def sendCreateBidRequest(self, auctionSN, bidValue, type_of_auction):
		log.high_debug("Hit sendCreateBidRequest!")

		try:
			auctionSN = int(auctionSN)
			bidValue = int(bidValue)

			params = {
				"auction-sn": auctionSN,
				"bid-value": bidValue
			}

			data_dict = self.buildRequest("create-bid", params, True, "repo")

			cert = extract_auth_certificate()
			manager_pub_key = load_rsa_public_key(cfg.CONFIG["AuctionManager"]["PUBLIC_KEY_FILE_PATH"])

			sym_key = None
			# English: hidden identity, clear value // Blind_hidden_id: hidden identity and value // Blind_Clear_Identity: clear identity, hidden value
			if type_of_auction == "English":
				self.setCertificate(data_dict, cert, True, manager_pub_key)
				# data_dict["client-name"] = get_name_from_cert(cert)
				self.setBidValue(data_dict, bidValue, False)	

			elif type_of_auction == "Blind_Hidden_Identity":
				self.setCertificate(data_dict, cert, True, manager_pub_key)
				sym_key = self.setBidValue(data_dict, bidValue, True, manager_pub_key)

			else:
				self.setCertificate(data_dict, cert, False)
				sym_key = self.setBidValue(data_dict, bidValue, True, manager_pub_key)

			signature = sign_data_with_cc(json.dumps(data_dict["data"], sort_keys=True))
			data_dict["client-signature"] = signature.hex()

			pprint(data_dict)

			response = self.__sendRequestAndWait("repo", data_dict)

			if "operation-error" in response:
				raise Exception(response["operation-error"])

			# Make sure we save receitp
			self.saveReceipt(response, cert, sym_key)

			return response

		except ValueError as e:
			log.error("Invalid data type! Serial number and bid value must be integers!")

	### Sends list bids request to repo
	def sendListBidsRequest(self, bids_filter="client", auction_sn=None):
		log.high_debug("Hit sendListParticipatedInAuctions!")

		if bids_filter == "auction" and auction_sn == None:
			log.error("No auction serial number specified!")
			return None

		params = { "bids-list-filter": bids_filter, "auction-sn": auction_sn }

		data_dict = self.buildRequest("list-bids", params)

		log.high_debug("Data: " + str(data_dict))

		response = self.__sendRequestAndWait("repo", data_dict)

		if "operation-error" in response:
			raise Exception(response["operation-error"])

		return response

	### Checks receipt validity 
	def validateReceipt(self, receipt):
		log.high_debug("Hit validateReceipt!")	

		repo_signed_data = copy.deepcopy(receipt)
		repo_signed_data.pop("manager-signature", None)

		repo_signed_data = json.dumps(repo_signed_data, sort_keys=True)

		log.high_debug("MANAGER VERIFICATION DATA\n" + str(repo_signed_data))
		log.high_debug(bytes.fromhex(receipt["manager-signature"]).hex())

		manager_sign = verify_signature_static_key(cfg.CONFIG["AuctionManager"]["PUBLIC_KEY_FILE_PATH"], repo_signed_data, bytes.fromhex(receipt["manager-signature"]))

		log.debug("Is manager valid?" + str(manager_sign))

		repo_signed_data = copy.deepcopy(receipt)
		repo_signed_data.pop("manager-signature", None)
		repo_signed_data.pop("repo-signature", None)
		repo_signed_data.pop("bid-is-valid")
		repo_signed_data = json.dumps(repo_signed_data, sort_keys=True)

		repo_sign = verify_signature_static_key(cfg.CONFIG["AuctionRepo"]["PUBLIC_KEY_FILE_PATH"], repo_signed_data, bytes.fromhex(receipt["repo-signature"]))

		log.debug("Is Repository valid?" + str(repo_sign))

		return manager_sign and repo_sign

	def showClientBids(self):
		log.high_debug("Hit showClientBids!")
		# [Recept dict, certificate hash, auction SN, bid value, SYM_KEY(used to encrypt bid value)
		receipts = self.loadCurrentClientReceipts()
		log.high_debug("Receipts: \n" + str(receipts))
		# Return: [ [AuctionSN, BidValue] ] 
		bids = []

		for r in receipts:
			data = r[0]
			data_dict = data["data"]
			bid_value = data_dict["bid-value"]

			log.high_debug("DATA!!!: \n" + str(data))

			if not IsInt(data_dict["bid-value"]):
				bid_value = decrypt_data_sym(bytes(data_dict["bid-value"], bytes.fromhex(r[-1])))

			bids.append([data_dict["auction-sn"], bid_value])

		log.high_debug("Bids: \n" + str(bids))

		return bids

	def loadCurrentClientReceipts(self):
		log.high_debug("Hit loadCurrentClientReceipts!")
		# Return [[Recept dict, certificate hash, auction SN, bid value]]
		receipts = self.loadReceipts()

		current_cc_cert_hash = hash_sha_str(bytes(extract_auth_certificate())).hex()
		client_receipts = []

		for r in receipts:
			if r[1] == current_cc_cert_hash:
				# client_receipts.append("AuctionSN: {}, bid value: {}".format(r[2], r[3]))
				client_receipts.append(r)

		log.high_debug("Client Receipts:\n" + str(client_receipts))

		return client_receipts

	# Sends check auction outcome request to manager
	def sendCheckAuctionOutcomeRequest(self, auction_sn):
		log.high_debug("Hit sendCheckAuctionOutcomeRequest!")

	def sign_data(self, data_dict):
		type_of_auction = data_dict["data"]["auction-type"]
		cert = extract_auth_certificate()

		# English: hidden identity, clear value // Blind_hidden_id: hidden identity and value // Blind_Clear_Identity: clear identity, hidden value
		if type_of_auction == "English":
			self.setCertificate(data_dict, cert, True, load_rsa_public_key(cfg.CONFIG["AuctionManager"]["PUBLIC_KEY_FILE_PATH"]))
			# data_dict["client-name"] = get_name_from_cert(cert)

		elif type_of_auction == "Blind_Hidden_Identity":
			self.setCertificate(data_dict, cert, True, load_rsa_public_key(cfg.CONFIG["AuctionManager"]["PUBLIC_KEY_FILE_PATH"]))

		else:
			self.setCertificate(data_dict, cert, False)

		signature = sign_data_with_cc(json.dumps(data_dict["data"], sort_keys=True))
		data_dict["client-signature"] = signature.hex()
		pprint(data_dict)

		return data_dict
