import sys
sys.path.append("auction")

from auction_manager import AuctionManager
import argparse
# from auction_manager import AuctionManager
# from auction_repo import AuctionRepo
import config as cfg
import log
from pyfiglet import Figlet
import signal


parser = argparse.ArgumentParser()
parser.add_argument('-v', '--verbose', help='verbosity level', action='count', default=0)
args = parser.parse_args()

class ManagerCli:
	def __init__(self):
		# self.__manager = None
		self.__manager = AuctionManager()

		f = Figlet(font='big')
		print(f.renderText('Manager'))

		cfg.RUNCFG["verbose"] = args.verbose

		if args.verbose == 1:
			log.warning("Log verbosity is enabled.")

		elif args.verbose == 2:
			log.warning("HIGH verbosity is enabled!")

		else:
			log.warning("Only regular information will be shown.")

	def start(self):
		self.__manager.startWorking()
		
	def stop(self):
		self.__manager.stopWorking()

c = ManagerCli()

# def signal_handler(sig, frame):
# 		log.warning("Trying to exit safely...")
# 		c.stop()

# signal.signal(signal.SIGINT, signal_handler)

c.start()
