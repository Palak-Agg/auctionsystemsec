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

			elif cmd == "delete-auction" or cmd == "da":
				self.handleCmdDeleteAuction()

			elif cmd == "list-auctions" or cmd == "la":
				self.handleCmdListAuctions()

			else:
				self.handleCmdHelp()

	####							####
	####	Handle command input	####
	####							####

	### Handles help command
	def handleCmdHelp(self):
		print("		heartbeat OR ht => checks if auction manager and auction repository entites are alive\n \
		create-auction OR ca => creates auction\n \
		delete-auction OR da => deletes auction\n \
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
		style = style_from_dict({
			Token.Separator: '#cc5454',
			Token.QuestionMark: '#673ab7 bold',
			Token.Selected: '#cc5454',  # default
			Token.Pointer: '#673ab7 bold',
			Token.Instruction: '',  # default
			Token.Answer: '#f44336 bold',
			Token.Question: '',
		})

		# Ge1t auction name, description, duration and type of auction
		questions = [
			{
			'type': 'input',
			'name': 'name',
			'message': 'Choose a name for the Auction',
			'validate': lambda answer: 'Name cannot be exceed 15 characters wide!' \
				if len(answer) > 15 else True
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
			log.error("Failed to send create-auction request!")

	### Handles delete auction command
	def handleCmdDeleteAuction(self):
		log.high_debug("Hit handleCmdDeleteAuction!")

		try:
			# auctions = self.__client.sendListAuctionsRequest()
			print(str(auctions))

		except Exception as e:
			log.error("Failed to retrieve Auctions List!")

	### Handles list auctions command
	def handleCmdListAuctions(self):
		log.high_debug("Hit handleCmdListAuctions!")

		try:
			auctions = self.__client.sendListAuctionsRequest()

			print("  {:15} {:3} {:14} {:25} {:6}"
				.format("Name", "SN", "Duration (s)", "Description", "Type"))

			# Pretty print auctions list
			for a in auctions:
				print("  {:15} {:3} {:14} {:25} {:6}"
					.format(
						a["name"],
						a["serialNumber"],
						a["duration"],
						a["description"],
						a["type_of_auction"],
						))
			
		except Exception as e:
			log.error("Failed to retrieve Auctions List!\n" + str(e))


c = ClientCli()
