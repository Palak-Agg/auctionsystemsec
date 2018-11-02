import log
import socket as skt
import config as cfg
import json

class AuctionClient:

	### Alphanumeric string identifying the client
	### This will be replaced by the citizen card number
	ClientID = -1
	
	def __init__(self, clientNumber):
		log.high_debug("Hit AuctionClient __init__!")
		self.ClientID = clientNumber
		log.info("Client number: " + str(self.ClientID))

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
			self.__socket.close()
			log.high_debug("Hit finally clause of __sendRequestAndWait")
		
		if response_data != None:
			return json.loads(response_data)

		return None

	def buildRequest(self, operation, params=None):
		data_dict = {
			"id-type": "auction-client",
			"client-number": self.ClientID,
			"packet-type": "request",
			"operation": operation 
		}
		if params != None:
			data_dict.update(params)

		return data_dict


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

	### Sends create auction request to the Auction Manager	
	def sendCreateAuctionRequest(self, name, description, duration, type_of_auction):
		log.high_debug("Hit sendCreateAuctionRequest!")

		params = {
			"auction-name": name,
			"auction-description": description,
			"auction-duration": duration,
			"auction-type": type_of_auction
		}

		data_dict = self.buildRequest("create-auction", params)

		log.debug(str(data_dict))
		response = self.__sendRequestAndWait("manager", data_dict)
		log.high_debug("RESPONSE:" + str(response))
		return response

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
	def sendCreateBidRequest(self, auctionSN, bidValue):
		log.high_debug("Hit sendCreateBidRequest!")

		try:
			auctionSN = int(auctionSN)
			bidValue = int(bidValue)

			params = {
				"auction-sn": auctionSN,
				"bid-value": bidValue
			}

			data_dict = self.buildRequest("create-bid", params)

			log.high_debug("Data: " + str(data_dict))

			response = self.__sendRequestAndWait("repo", data_dict)

			if "operation-error" in response:
				raise Exception(response["operation-error"])

			return response

		except ValueError as e:
			log.error("Invalid data type! Serial number and bid value must be integers!")
