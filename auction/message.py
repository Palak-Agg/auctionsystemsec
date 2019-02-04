class Message(object):
	### Data to be sent over the wire, the actual message's content
	__data = {}

	""" A message encapsulates a request from any entity type to any entity type """
	def __init__(self, identity_type, packet_type, operation):
		self.__identity_type = identity_type
		self.__packet_type = packet_type
		self.__operation = operation
		self.__client_number = None
		self.__certificate = None

	def setClientSN(self, client_sn):
		self.__client_number = client_sn

	def setCertificate(self, cert):
		self.__certificate = cert

	"""
		Adds new data to the current __data dictionary 
		Arguments:
			new_data: dictionary
	"""
	def add_data(self, new_data):
		if not type(new_data) is dict:
			raise new TypeError("Expected dictionary as new_data argument!")
	
	""" Signs message using the connected CC device """	
	def sign_message(self, private_key=None):
		if self.__identity_type == "auction-client" and private_key != None:
			raise NotImplementedError("Set private key with auction-client identity type! Clients use CC's smartcard to sign data!")

		if self.__identity_type == "auction-repo" or self.__identity_type == "auction-manager" and private_key == None:
			raise ValueError("Expected private key argument with auction-repo or auction-manager identity type!")


		

	""" Verifies the message signature using the specified public key extract from the certificate """
	def verify_message_signature(self):
		pass
