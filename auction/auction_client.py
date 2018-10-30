import log
import socket as skt
import config as cfg
import json

class AuctionClient:
	
	def __init__(self):
		log.high_debug("Hit AuctionClient __init__!")

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


			TODO: communication is working. But only through logging
			a mechanism should be in place to tell the 
			calling functions of how the operation went.

			i.e: how will client_cli.py know that the operation
			went as expected?


			response_data, server = self.__socket.recvfrom(4096)
			log.debug("Received {!r}".format(response_data))

		# except Exception as e:
		# 	log.error(str(e))

		finally:
			self.__socket.close()
			log.high_debug("Hit finally clause of __sendRequestAndWait")
		
		if response_data != None:
			return json.loads(response_data)
		else:
			log.error("Could not get a response from the server!")
			raise Exception()


	### Tests connectivity to the Auction Manager server ###
	def sendHeartbeatAuctionManager(self):
		log.high_debug("Hit sendHeartbeatAuctionManager!")
		data_dict = {
			"id-type": "auction-client",
			"packet-type": "request",
			"operation": "heartbeat" 
		}

		# try:
		response = self.__sendRequestAndWait("manager", data_dict)
		return True

		# except Exception as e:
		# 	log.error(str(e))
		# 	return False

	### Tests connectivity to the Auction Repo server ###
	def heartbeatAuctionRepo(self):
		pass

	### Top level function to handle Create Auction operation
	def createAuction(self):
		pass
	
	def sendCreateAuctionRequest(self):
		pass

