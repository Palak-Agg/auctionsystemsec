2import sys
sys.path.append("auction")

from auction_client import AuctionClient
# from auction_manager import AuctionManager
# from auction_repo import AuctionRepo
import config as cfg

class ClientCli:
	# __client

	def __init__(self):
		self.__client = AuctionClient()
		self.mainLoop()

	### Handles command processing
	def mainLoop(self):
		while True:
			print(">",end="",flush=True)
			cmd = input().lower()

			if cmd == "help":
				print("dayum")

			elif cmd == "heartbeat" or cmd == "ht":
				self.handleCmdHeartbeat()

	####							####
	####	Handle command input	####
	####							####

	### Handles help command
	def handleCmdHelp(self):
		print("HELP INFO")

	### Handles heartbeat command
	def handleCmdHeartbeat(self):
		# print(self.__client)
		self.__client.sendHeartbeatAuctionManager()

c = ClientCli()