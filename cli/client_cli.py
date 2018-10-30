import sys
sys.path.append("auction")

from auction_client import AuctionClient
import argparse
# from auction_manager import AuctionManager
# from auction_repo import AuctionRepo
import config as cfg
import log

parser = argparse.ArgumentParser()
parser.add_argument('-v', '--verbose', help='verbosity level', action='count', default=0)
args = parser.parse_args()

class ClientCli:
	# __client

	def __init__(self):
		cfg.RUNCFG["verbose"] = args.verbose

		if args.verbose == 1:
			log.warning("Log verbosity is enabled.")

		elif args.verbose == 2:
			log.warning("HIGH verbosity is enabled!")

		else:
			log.warning("Only regular information will be shown.")

		self.__client = AuctionClient()
		self.mainLoop()

	### Handles command processing
	def mainLoop(self):
		while True:
			print(">",end="",flush=True)
			cmd = input().lower()

			if cmd == "help":
				print("Should print something ")

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
		try:
			self.__client.sendHeartbeatAuctionManager()
			log.info("Auction Manager is alive!")
		except Exception as e:
			log.error("Failed to sent heartbeat packet to auction manager!")

c = ClientCli()