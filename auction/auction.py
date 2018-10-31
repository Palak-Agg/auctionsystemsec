from bid import Bid
import datetime as date

class Auction:
	### Auction name
	# name

	### Uniquely generated serial number
	# serialNumber 

	### Duration
	# duration

	### Description
	# description

	### Type of auction. Possible types: 
	# typeOfAuction

	### Ctor
	def __init__(self, name, sn, duration, description, typeOfAuction):
		self.name = name
		self.serialNumber = sn
		self.duration = duration
		self.description = description
		self.type_of_auction = typeOfAuction
		self.isActive = True
		self.__list_of_bids = []

	### Create genesis block
	def createGenesisBlock(self):
		# bid = Bid(0, date.datetime.now(), 0, , -1, -1, -1)
		# self.addNewBid(bid)
		self.addNewBid(-1, -1, -1)

	### Appends new bid object to list
	def addNewBid(self, clientId, auctionSN, bidValue):
		previous_hash = -1

		if len(self.__list_of_bids) > 0:
			previous_hash = self.__list_of_bids[-1].previous_hash

		bid = Bid(clientId, auctionSN, bidValue, len(self.__list_of_bids), date.datetime.now(), previous_hash)

		self.__list_of_bids.append(bid)

	def __dict__(self):
		return {
				"name": self.name,
				"serialNumber": self.serialNumber,
				"duration": self.duration,
				"description": self.description,
				"type_of_auction": self.type_of_auction,
				"isActive": self.isActive
				}