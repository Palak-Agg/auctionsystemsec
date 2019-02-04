import sys
sys.path.append("auction")

import unittest
from auction_client import AuctionClient
from auction_manager import AuctionManager
from auction_repo import AuctionRepo
import config as cfg
import threading

threads = {}


class TestAuctionClient(unittest.TestCase):

	def __init__(self, *args, **kwargs):
		super(TestAuctionClient, self).__init__(*args, **kwargs)
		self.client1 = AuctionClient(1)
		self.client2 = AuctionClient(2)

	def test_create_auction(self):
		
		cfg.RUNCFG["verbose"] = 1

		result = None
		# try:
		result = self.client1.sendCreateAuctionRequest("First", "Desc", 15, "English")

		# except Exception as e:
		# 	print(str(e))

		assert(result != None)

	def test_terminate_auction(self):
		# Assume the test was created in test_create_auction

		result = None
		# try:
		result = self.client1.sendTerminateAuctionRequest(0)

		# except Exception as e:
		# 	print(str(e))
		
		assert(result != None)

	def test_terminate_inactive_auction(self):
		# Assume the test was already terminated in test_terminate_auction

		result = False

		try:
			result = self.client1.sendTerminateAuctionRequest(0)

		except Exception as e:
			result = "No ACTIVE auction" in str(e)

		assert(result)


	def test_terminate_nonexistent_auction_sn(self):
		result = False

		try:
			result = self.client1.sendTerminateAuctionRequest(-1)

		except Exception as e:
			result = "No ACTIVE auction" in str(e)

		assert(result)

	def test_list_auctions(self):
		result = False

		try:
			result = self.client1.sendListAuctionsRequest()
		except Exception as e:
			result = False # redundant

		assert(result != False)

	# def test_list_auctions_filter_active(self):
	# 	result = False

	# 	result = self.client1.sendCreateAuctionRequest("Second", "Desc", 15, "Blind")

	# 	try:
	# 		result = self.client1.sendListAuctionsRequest("active")
	# 		result = len(result) == 1

	# 	except Exception as e:
	# 		result = False # redundant

	# 	assert(result)


	# def test_list_auctions_filter_inactive(self):
	# 	result = False

	# 	try:
	# 		result = self.client1.sendListAuctionsRequest("inactive")
	# 		result = len(result) == 1

	# 	except Exception as e:
	# 		result = False # redundant

	# 	assert(result)

	def test_create_bid(self):
		result = False

		# try:
			# result = self.

	



def startManager():
	manager = AuctionManager()
	manager.startWorking()

def startRepo():
	repo = AuctionRepo()

threads["manager"] = threading.Thread(target=startManager)
threads["repo"] = threading.Thread(target=startRepo)

threads["manager"].start()
threads["repo"].start()

if __name__ == '__main__':
	unittest.main()