import hashlib as hasher

class Bid:
	## SN. This should probably be generated in the Auction Repo (?)
	# serialNumber

	## Client ID
	# clientId 

	## Auction SN
	# auctionSN

	## The value of the respective bid
	# bidValue

	### Blockchain members

	## Index of the bid relative to the Blockchain
	# index

	## Local time of when it was created
	# timestamp

	## Hash of the previous block/bid
	# previous_hash

	## This block's hash
	# block_hash

	### Ctor
	def __init__(
			self,
		 	clientId, 
		 	auctionSN,
		 	value,
			index,
			timestamp,
			previous_hash):
		self.clientId = clientId
		self.auctionSN = auctionSN
		self.bidValue = value
		self.index = index
		self.timestamp = timestamp
		self.previous_hash = previous_hash
		self.block_hash = self.hash_block()

	### Hash this block's data
	def hash_block(self):
		sha = hasher.sha256()
		sha.update((str(self.clientId) + 
					str(self.auctionSN) + 
					str(self.bidValue) + 
					str(self.index) + 
					str(self.timestamp) + 
					str(self.previous_hash)).encode("UTF-8"))

		return sha.hexdigest()

	def __dict__(self):
		return {
				"clientId": self.clientId,
				"auctionSN": self.auctionSN,
				"bidValue": self.bidValue,
				"index": self.index,
				"previous_hash": self.previous_hash,
				"block_hash": self.block_hash
				}

	def __str__(self):
		return str(self.__dict__())

