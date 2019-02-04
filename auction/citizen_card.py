from PyKCS11 import *
from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.serialization import load_der_public_key
from cryptography.hazmat.primitives.asymmetric import (padding, rsa, utils)
import unidecode
import pprint
import os.path
import json

class CitizenCard(object):
	__lib = '/usr/lib/libpteidpkcs11.so'
	__pkcs11 = PyKCS11.PyKCS11Lib()
	__pkcs11.load(lib)

	"""docstring for CitizenCard"""
	def __init__(self):
		self.__is_using_internal_device = False

	""" Get Cartao de Cidadao from smart card reader """
	def initialize_from_device(self):
		self.__slots = __pkcs11.getSlotList()

		for slot in slots:
			# Find Cartao de cidadao slot and save it
			if 'CARTAO DE CIDADAO' in pkcs11.getTokenInfo( slot ).label:
				self.__slot = slot
				self.__is_using_internal_device = True

	""" Extracts client certificate from connected smart card """
	def extract_auth_certificate():
		if not self.__is_using_internal_device:
			raise NotImplementedError("extract_auth_certificate should not be called when the instance was not initialized using internal device!")

		session = self.__pkcs11.openSession( self.__slot )
		self.__auth_certificate = session.findObjects( [(CKA_CLASS, CKO_CERTIFICATE), (CKA_LABEL, "CITIZEN AUTHENTICATION CERTIFICATE")])[0]
		self.__certificate_der = session.getAttributeValue( self.__auth_certificate, [CKA_VALUE])[0]

		# Make sure we close slot session		
		session.closeSession()

		return self.__certificate_der			

	### Native data is the whole packet
	def validate_request(native_data):
		cert = bytes.fromhex(native_data["certificate"])
		cert_chain_check = verify_certificate_chain(cert)

		# Check signature
		signature = bytes.fromhex(native_data["signature"])
		data = json.dumps(native_data["encrypted-data"], sort_keys=True)

		sign_check = verify_signature(cert, data, signature)

		return cert_chain_check and sign_check
