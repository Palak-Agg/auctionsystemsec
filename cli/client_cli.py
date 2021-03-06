from __future__ import print_function, unicode_literals

import sys
sys.path.append("auction")

from auction_client import AuctionClient
import argparse

import config as cfg
import log
from pyfiglet import Figlet

from utils import IsInt


from PyInquirer import style_from_dict, Token, prompt, Separator
from pprint import pprint

parser = argparse.ArgumentParser()
parser.add_argument('-v', '--verbose', help='verbosity level', action='count', default=0)
parser.add_argument('--clientnumber', help='sets the client number', type=int)
args = parser.parse_args()

style = style_from_dict({
			Token.Separator: '#cc5454',
			Token.QuestionMark: '#673ab7 bold',
			Token.Selected: '#cc5454',  # default
			Token.Pointer: '#673ab7 bold',
			Token.Instruction: '',  # default
			Token.Answer: '#f44336 bold',
			Token.Question: '',
		})

class ClientCli:
	# __client

	def __init__(self):
		f = Figlet(font='big')
		print(f.renderText('Client'))

		cfg.RUNCFG["verbose"] = args.verbose

		if args.verbose == 1:
			log.warning("Log verbosity is enabled.")

		elif args.verbose == 2:
			log.warning("HIGH verbosity is enabled!")

		else:
			log.warning("Only regular information will be shown.")

		self.__client = AuctionClient(args.clientnumber)
		self.mainLoop()

	### Handles command processing
	def mainLoop(self):
		while True:
			print(">",end="",flush=True)
			cmd = input().lower().strip()

			tokens = cmd.split(" ")

			cmd = tokens[0]

			if cmd == "help":
				self.handleCmdHelp()
			elif cmd == "":
				continue

			elif cmd == "heartbeat" or cmd == "ht":
				self.handleCmdHeartbeat()

			elif cmd == "create-auction" or cmd == "ca":
				self.handleCmdCreateAuction()

			elif cmd == "terminate-auction" or cmd == "ta":
				self.handleCmdTerminateAuction()

			elif "list-auctions" in cmd or "la" in cmd:
				if len(tokens) == 2:
					self.handleCmdListAuctions(tokens[1])
				else:
					self.handleCmdListAuctions()

			elif "list-bids" in cmd or cmd == "lb":

				if len(tokens) == 2:
					self.handleCmdListBids(tokens[1])
				else:
					self.handleCmdListbids()

			elif "list-bids-client" in cmd or "lbc" in cmd:

				self.handleCmdListClientBids()

			elif "list-bids-auction" in cmd or "lba" in cmd:

				self.handleCmdListAuctionBids()

			elif cmd == "bid":
				self.handleCmdBid()

			elif cmd == "check-auction" or "cka" in cmd:
				self.handleCmdCheckAuctionOutcome()

			elif "validate-receipt" in cmd or "vr" in cmd:
				self.handleValidateReceipt()

			else:
				self.handleCmdHelp()

	####							####
	####	Handle command input	####
	####							####

	### Handles help command
	def handleCmdHelp(self):
		print("		heartbeat OR ht => checks if auction manager and auction repository entites are alive\n \
		create-auction OR ca => creates auction\n \
		terminate-auction OR ta => deletes auction\n \
		list-auction OR la => lists auctions\n \
		list-bids-client => lbc \
		create-auction OR ca => creates auction \
				")

	### Handles heartbeat command
	def handleCmdHeartbeat(self):
		# print(self.__client)
		try:
			self.__client.sendHeartbeatAuctionManager()
			log.info("Auction Manager is alive!")

			self.__client.sendHeartbeatAuctionRepo()
			log.info("Auction Repository is alive!")
		except Exception as e:
			log.error("Failed to sent heartbeat packet to auction manager!")

	### Handles create auction command and all the respective user input validation
	def handleCmdCreateAuction(self):

		# Ge1t auction name, description, duration and type of auction
		questions = [
			{
			'type': 'input',
			'name': 'name',
			'message': 'Choose a name for the Auction',
			'validate': lambda answer: 'Empty name or it exceeds 15 characters wide!' \
				if len(answer) > 15 or len(answer) == 0 else True
			},
			{
			'type': 'input',
			'name': 'description',
			'message': 'Describe the auction',
			'default': 'Yet another auction!',
			'validate': lambda answer: 'Description cannot be exceed 25 characters wide!' \
				if len(answer) > 25 or len(answer.strip()) == 0 else True
			},
			{
			'type': 'input',
			'name': 'duration',
			'default': '10',
			'message': 'Set the duration in SECONDS!',
			'validate': lambda dur: 'Invalid number. Must be greater than 10!' \
				if (not IsInt(dur) or int(dur) < 10) else True
			},
			{
			'type': 'rawlist',
			'message': 'What\'s the auction type?',
			'name': 'type',
			'choices': ["English", "Blind - CLEAR identity", "Blind - HIDDEN identity"],
			'validate': lambda answer: 'You must choose only one type of auction!' \
				if len(answer) > 1 else True
			}

		]

		answers = prompt(questions, style=style)

		# Refactor?
		if "Blind" in answers["type"]:
			if "CLEAR" in answers["type"]:
				answers["type"] = "Blind_Clear_Identity"

			elif "HIDDEN" in answers["type"]:
				answers["type"] = "Blind_Hidden_Identity"


		# try:
		response = self.__client.sendCreateAuctionRequest(answers["name"], 
												answers["description"], 
												int(answers["duration"]), 
												answers["type"])
		if not "operation-error" in response:
			log.info("Successfully created auction!")

		else:
			log.error(response["operation-error"])

		# except Exception as e:
		# log.error("Failed to send create-auction request!\n " + str(e))

	### Handles delete auction command
	def handleCmdTerminateAuction(self):
		log.high_debug("Hit handleCmdTerminateAuction!")

		# try:
		# auctions = self.__client.sendListAuctionsRequest()
		auctions = self.__client.sendListAuctionsRequest()

		if (len(auctions) == 0):
			log.info("No active auctions were found!")
			return

		log.high_debug(str(auctions))

		# Join serial number and name as the name may not be unique
		choices = [str(d["serialNumber"]) + " -> " + d["name"] for d in auctions]
		questions = [
			{
			'type': 'rawlist',
			'message': 'Choose the auction to terminate (only those created by you are shown)',
			'name': 'auction',
			'choices': choices,
			'validate': lambda answer: 'You need to choose at least one auction!' \
				if len(answer) == 0 else True
			}
		]

		answers = prompt(questions, style=style)

		# Get the id portion of the string
		serialNumber = answers["auction"].split(" -> ")[0].strip()

		log.high_debug("SERIAL NUMBER: " + str(serialNumber))

		# auction_sn = [d["serialNumber"] for d in auctions if d["name"] == serialNumber]

		try:
			self.__client.sendTerminateAuctionRequest(serialNumber)
			log.info("Successfully terminated auction!")

		except Exception as e:
			log.error("Failed to terminate Auction!\n" + str(e))

	### Handles list auctions command
	def handleCmdListAuctions(self, auctions_filter="all"):
		log.high_debug("Hit handleCmdListAuctions!")

		# try:
		auctions = self.__client.sendListAuctionsRequest(auctions_filter)

		log.high_debug("Received auctions: " + str(auctions))

		if (len(auctions) == 0):
			log.info("No active auctions were found!")
			return

		print(" {:10} {:15} {:3} {:14} {:25} {:6}"
			.format("[Active]", "Name", "SN", "Duration (s)", "Description", "Type"))

		# Pretty print auctions list
		for a in auctions:
			print("  {:10} {:15} {:3} {:14} {:25} {:6}"
				.format(
					"Yes" if a["isActive"] else "No",
					a["name"],
					a["serialNumber"],
					a["duration"],
					a["description"],
					a["type_of_auction"]))
		
		# except Exception as e:
		# 	log.error("Failed to retrieve Auctions List!\n" + str(e))

	### Handles bit on auction command
	def handleCmdBid(self):
		auctions = self.__client.sendListAuctionsRequest()

		if (len(auctions) == 0):
			log.info("No active auctions were found!")
			return

		log.high_debug("Auctions [raw]: " + str(auctions))

		# Join serial number and name as the name may not be unique
		choices = []

		for d in auctions:
			if not d["isActive"]:
				continue 

			if d["type_of_auction"] == "English":
				choices.append("{}  -> {} [Min:{}] ({})".format(
					str(d["serialNumber"]), 
					d["name"], 
					d["highestBid"]["bidValue"] if d["highestBid"] != None and d["highestBid"] != 0 else "0",
					d["type_of_auction"] ))

			else:
				choices.append("{} -> {} ({})".format(
					str(d["serialNumber"]), 
					d["name"],
					d["type_of_auction"]))

		if len(choices) == 0:
			log.info("No active auctions were found!")
			return

		questions = [
			{
			'type': 'rawlist',
			'message': 'Choose the auction to bid on',
			'name': 'auction',
			'choices': choices,
			'validate': lambda answer: 'You need to choose at least one auction!' \
				if len(answer) == 0 else True
			},
			{
			'type': 'input',
			'name': 'bid',
			'default': lambda a: self.getMinValue(choices, a["auction"], auctions),
			'message': 'Set the BID value!',
			'validate': lambda dur: 'Invalid number. Must be greater than 0!' \
				if (not IsInt(dur) or int(dur) <= 0) else True
			}
		]

		answers = prompt(questions, style=style)

		# Get the id portion of the string
		serialNumber = answers["auction"].split(" -> ")[0].strip()

		target_auction = [d for d in auctions if str(d["serialNumber"]) == str(serialNumber)][0]

		print(target_auction)

		# try:
			# if int(answers["bid"]) <= 
		self.__client.sendCreateBidRequest(serialNumber, answers["bid"], target_auction["type_of_auction"])
		log.info("Successfully created bid!")

		# except Exception as e:
		# 	log.warning(str(e))

	def getMinValue(self, choices, answer, auctions):
		# Get the id portion of the string
		serial_number = int(answer.split(" -> ")[0].strip())

		target_auction = [d for d in auctions if d["serialNumber"] == serial_number][0]

		if target_auction["type_of_auction"] == "Blind":
			return "1"

		log.high_debug(target_auction)
		return str(int(target_auction["minBidValue"]))

	def handleCmdListClientBids(self):
		bids = self.__client.showClientBids()

		for b in bids:
			print("Bid {} on {} ".format(b[1], b[0]))


	def handleCmdListAuctionBids(self):
		pass

	### Handles list bids command, filtered by client-sn or all 
	def handleCmdListBids(self, bids_filter="client"):
		log.high_debug("Hit handleCmdListBids!")

		try:					
			# Retrieve list for later use
			auctions = self.__client.sendListAuctionsRequest()

			# if bids_filter == "client":
			# 	
			serial_number = None

			if bids_filter == "auction":
				# Join serial number and name as the name may not be unique
				choices = [str(d["serialNumber"]) + " -> " + d["name"] for d in auctions]
				questions = [
					{
					'type': 'rawlist',
					'message': 'Choose the auction you want to peek',
					'name': 'auction',
					'choices': choices,
					'validate': lambda answer: 'You need to choose at least one auction!' \
						if len(answer) == 0 else True
					}]

				answers = prompt(questions, style=style)

				# Get the id portion of the string
				serial_number = answers["auction"].split(" -> ")[0].strip()

			response = self.__client.sendListBidsRequest(bids_filter, serial_number)

			bids = response["bids-list"]

			print(" {:10} {:10} {:5} {:3}"
				.format("Client-SN", "Auction-SN", "Index", "Value"))

			for b in bids:
				print(" {:10} {:10} {:5} {:3}"
					.format(b["clientId"], b["auctionSN"], b["index"], b["bidValue"]))


			# log.debug(bids)
		except Exception as e:
			log.error(str(e))

	# Handles check auction outcome command
	def handleCmdCheckAuctionOutcome(self):
		log.high_debug("Hit handleCmdCheckAuctionOutcome!")

		auctions = self.__client.sendListAuctionsRequest("client-outcome")

		if (len(auctions) == 0):
			log.info("No active auctions were found!")
			return

		log.high_debug(str(auctions))

		# Join serial number and name as the name may not be unique
		choices = [str(d["serialNumber"]) + " -> " + d["name"] for d in auctions]
		questions = [{
			'type': 'rawlist',
			'message': 'Choose the auction whose outcome you want to see',
			'name': 'auction',
			'choices': choices,
			'validate': lambda answer: 'You need to choose ONE auction!' \
				if len(answer) == 0 else True
			}]

		answers = prompt(questions, style=style)

		# Get the id portion of the string
		serial_number = int(answers["auction"].split(" -> ")[0].strip())

		# TODO: finish this
		# auction = self.__client.sendCheckAuctionOutcomeRequest(serial_number)

		target_auction = [d for d in auctions if d["serialNumber"] == serial_number][0]

		if target_auction["highestBid"] != None:

			print("Client with SN: {} won Auction '{}' [SN:{}] with bid value of {}".format(
				target_auction["highestBid"]["clientId"],
				target_auction["name"],
				target_auction["serialNumber"],
				target_auction["highestBid"]["bidValue"]))
		else:
			print ("Nobody bet on Auction '{}'".format(target_auction["name"]))

	# Handles receipt validation command
	def handleValidateReceipt(self):
		log.high_debug("Hit handleValidateReceipt!")

		# Join serial number and name as the name may not be unique
		# choices = [str(d["serialNumber"]) + " -> " + d["name"] for d in auctions]
		receipts = self.__client.loadCurrentClientReceipts()

		log.high_debug("CHOiceS:\n" + str(receipts))

		if receipts == None or len(receipts) == 0:
			log.warning("No receipts were found!")
			return

		choices = []

		for r in receipts:
			option = "AuctionSN: {}, Bid: {}".format(r[2], r[3])
			r.append(option)
			choices.append(option)

		questions = [{
			'type': 'rawlist',
			'message': 'Choose the receipt you want to validate',
			'name': 'receipt',
			'choices': choices,
			'validate': lambda answer: 'You need to choose ONE receipt!' \
				if len(answer) == 0 else True
			}]

		answers = prompt(questions, style=style)

		selected_receipt = None

		for r in receipts:
			if r[-1] == answers["receipt"]:
				selected_receipt = r[0]


		if selected_receipt == None:
			log.warning("Could not determine which receipt you wanted to validate! This should not happen.")
			return

		if self.__client.validateReceipt(selected_receipt):
			log.info("Receipt successfully validated!")

		else:
			log.error("Could not validate receipt!")

c = ClientCli()
