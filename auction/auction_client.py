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


			# TODO: communication is working. But only through logging
			# a mechanism should be in place to tell the 
			# calling functions of how the operation went.

			# i.e: how will client_cli.py know that the operation
			# went as expected?

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

		return response

	### Tests connectivity to the Auction Repository server ###
	def sendHeartbeatAuctionRepo(self):
		log.high_debug("Hit sendHeartbeatAuctionRepo!")
		data_dict = {
			"id-type": "auction-client",
			"packet-type": "request",
			"operation": "heartbeat" 
		}

		response = self.__sendRequestAndWait("repo", data_dict)

		return response


		# except skt.timeout:
		# 	log.error("Could not send Heartbeat to Auction Manager!")


	### Tests connectivity to the Auction Repo server ###
	def heartbeatAuctionRepo(self):
		pass

	### Top level function to handle Create Auction operation
	def createAuction(self):
		pass
	
	def sendCreateAuctionRequest(self):
		pass

