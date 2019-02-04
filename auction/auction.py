from bid import Bid
import datetime as date
import time

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
	def __init__(self, name, sn, duration, createTime, description, typeOfAuction):
		self.name = name
		self.serialNumber = sn
		self.duration = duration
		self.description = description
		self.createTime = createTime
		self.type_of_auction = typeOfAuction
		self.isActive = True
		self.__list_of_bids = []

		self.__winningBid = None
		self.endTime = float(duration) + createTime
		self.createGenesisBlock()

	### Create genesis block
	def createGenesisBlock(self):
		# bid = Bid(0, date.datetime.now(), 0, , -1, -1, -1)
		# self.addNewBid(bid)
		self.addNewBid(-1, -1, 0)

	### Appends new bid object to list
	def addNewBid(self, clientId, bidValue, receipt):
		previous_hash = -1

		if len(self.__list_of_bids) > 0:
			previous_hash = self.__list_of_bids[-1].previous_hash

		bid = Bid(int(clientId), self.serialNumber, bidValue, len(self.__list_of_bids), time.time(), previous_hash, receipt)
		

		self.__list_of_bids.append(bid)

	### Retrives the bid object with the highest bid value
	def getHighestBid(self):
		if len(self.__list_of_bids) == 1:
			return None

		if self.type_of_auction != "English":
			# Ignore genesis

			if not self.isActive:
				self.__winningBid = max(self.__list_of_bids[1:], key=(lambda bid: bid.bidValue))

			else:
				self.__winningBid = None

		else:
			# Ignore genesis
			self.__winningBid = self.__list_of_bids[1:][-1]

		return self.__winningBid

	def getMinBidValue(self):
		if not self.isActive:
			return None

		elif len(self.__list_of_bids) == 1:
			return 0

		bid = None
		if self.type_of_auction == "Blind":
			# Ignore genesis
			bid = max(self.__list_of_bids[1:], key=(lambda bid: bid.bidValue))

		else:
			# Ignore genesis
			bid = self.__list_of_bids[1:][-1]

		return bid.bidValue if bid != None else 0

	### Simple wrapper to get all bids
	def bidsList(self):
		return self.__list_of_bids[1:]

	### Serialiazable representation of the object
	def __dict__(self):
		highestBid = self.getHighestBid()
		minBidValue = 1

		if highestBid != None:
			highestBid = highestBid.__dict__()
			minBidValue = int(highestBid["bidValue"]) + 1

		else:
			highestBid = 0

		return {
				"name": self.name,
				"serialNumber": self.serialNumber,
				"duration": self.duration,
				"description": self.description,
				"type_of_auction": self.type_of_auction,
				"isActive": self.isActive,
				"highestBid": highestBid,
				"minBidValue": minBidValue,
				"bids": [d.__dict__() for d in self.__list_of_bids]
			}

	def __str__(self):
		return str(self.__dict__())
