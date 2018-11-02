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
				tokens = cmd.strip().split(" ")

				if len(tokens) == 2:
					self.handleCmdListAuctions(tokens[1])
				else:
					self.handleCmdListAuctions()
			elif "bid":
				self.handleCmdBid()

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
			'choices': ["English", "Blind"],
			'validate': lambda answer: 'You must choose only one type of auction!' \
				if len(answer) > 1 else True
			}

		]

		answers = prompt(questions, style=style)

		try:
			self.__client.sendCreateAuctionRequest(answers["name"], 
													answers["description"], 
													int(answers["duration"]), 
													answers["type"])
			log.info("Successfully created auction!")

		except Exception as e:
			log.error("Failed to send create-auction request!\n " + str(e))

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

		log.high_debug(str(auctions))

		# Join serial number and name as the name may not be unique
		choices = [str(d["serialNumber"]) + " -> " + d["name"] for d in auctions]
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
			'default': '10',
			'message': 'Set the BID value!',
			'validate': lambda dur: 'Invalid number. Must be greater than 0!' \
				if (not IsInt(dur) or int(dur) <= 0) else True
			}
		]

		answers = prompt(questions, style=style)

		# Get the id portion of the string
		serialNumber = answers["auction"].split(" -> ")[0].strip()

		try:
			self.__client.sendCreateBidRequest(serialNumber, answers["bid"])
			log.info("Successfully created bid!")
		except Exception as e:
			log.warning(str(e))


c = ClientCli()
