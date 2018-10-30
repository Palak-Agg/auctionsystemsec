import configparser
import log
import os.path

CONFIG = configparser.ConfigParser()

# Runtime configurations

RUNCFG = { 
	"verbose": 0 #0 = normal, 1: verbosity enabled, 2: high verbosity enabled
	}

def writeDefaults():
	global CONFIG
	CONFIG["AuctionManager"] = {
		"IP": "127.0.0.1",
		"PORT": 7010
	}

	CONFIG["AuctionRepo"] = {
		"IP": "127.0.0.1",
		"PORT": 7020
	}

	with open('appSettings.ini', 'w') as configFile:
		CONFIG.write(configFile)

def loadSettings():
	global CONFIG

	if (not os.path.isfile('appSettings.ini')):
		writeDefaults()

	CONFIG.read('appSettings.ini')
	# CONFIG["AuctionManager"]["PORT"] = int(CONFIG["AuctionManager"]["PORT"])
	# CONFIG["AuctionRepo"]["PORT"] = int(CONFIG["AuctionRepo"]["PORT"])


loadSettings()