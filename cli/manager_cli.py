import sys
sys.path.append("auction")

from auction_manager import AuctionManager
import argparse
# from auction_manager import AuctionManager
# from auction_repo import AuctionRepo
import config as cfg
import log


parser = argparse.ArgumentParser()
parser.add_argument('-v', '--verbose', help='verbosity level', action='count', default=0)
args = parser.parse_args()

class ManagerCli:

	def __init__(self):
		print(args.verbose)
		cfg.RUNCFG["verbose"] = args.verbose

		if args.verbose == 1:
			log.warning("Log verbosity is enabled.")

		elif args.verbose == 2:
			log.warning("HIGH verbosity is enabled!")

		else:
			log.warning("Only regular information will be shown.")

		self.__manager = AuctionManager()

c = ManagerCli()