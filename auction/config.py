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
		"PORT": 7010,
		"PUBLIC_KEY_FILE_PATH": "keys/manager_pub.pem",
		"PRIVATE_KEY_FILE_PATH": "keys/manager_priv.pem",
		"SECRET_TOKEN": "blingbling"
	}

	CONFIG["AuctionRepo"] = {
		"IP": "127.0.0.1",
		"PORT": 7020,
		"PUBLIC_KEY_FILE_PATH": "keys/repo_pub.pem",
		"PRIVATE_KEY_FILE_PATH": "keys/repo_priv.pem",
		"SECRET_TOKEN": "blingbling"
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