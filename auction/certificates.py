from PyKCS11 import *
from cryptography import x509
from cryptography import exceptions
from cryptography.hazmat.backends import default_backend
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.serialization import load_der_public_key
from cryptography.hazmat.primitives.asymmetric import (padding, rsa, utils)
import unidecode
import pprint
import os.path
import log
import json
from crypto_utils import load_rsa_public_key

lib = '/usr/lib/libpteidpkcs11.so'
pkcs11 = PyKCS11.PyKCS11Lib()
pkcs11.load(lib)

slots = pkcs11.getSlotList()	

def sign_data_with_cc(data):
	for slot in slots:
		if 'CARTAO DE CIDADAO' in pkcs11.getTokenInfo( slot ).label:
			session = pkcs11.openSession( slot )

			privKey = session.findObjects([(CKA_CLASS, CKO_PRIVATE_KEY),
											(CKA_LABEL, 'CITIZEN AUTHENTICATION KEY')])[0]

			signature = bytes(session.sign(privKey, bytes(data, 'utf-8'), Mechanism(CKM_SHA1_RSA_PKCS)))
			
			session.closeSession()

			return signature

def sign_data_with_priv_key(data, privKey):
	signature = privKey.sign(
		bytes(data, 'utf-8'),
		padding.PKCS1v15(),
		hashes.SHA1()
 	)

	return signature

def verify_signature_static_key(public_key_file_path, data, signature):
	public_key = load_rsa_public_key(public_key_file_path)

	# try:
	if type(data) == str:
		public_key.verify(signature, bytes(data, 'utf-8'), padding.PKCS1v15(), hashes.SHA1())

	else:
		public_key.verify(signature, bytes(data), padding.PKCS1v15(), hashes.SHA1())

	return True

	# except exceptions.InvalidSignature as e:
	# 	log.error(str(e))
	# 	return False

	# ex
'''
	Args:
		certificate: raw DER format
		data: 
'''
def verify_signature(certificate, data, signature):
	target_cert = x509.load_der_x509_certificate(bytes(certificate), default_backend())

	try:
		target_cert.public_key().verify(signature, bytes(data, 'utf-8'), padding.PKCS1v15(), hashes.SHA1())
		return True

	except Exception as e:
		print("ERROR: " + str(e))
		return False

'''
Args:
	target_cert: x509 format certificate
'''
def verify_certificate_chain(certificate):
	target_cert = x509.load_der_x509_certificate(bytes(certificate), default_backend())

	# Stop when certificate is self-signed
	while True:
		# Get issuer's certificate
		# issuer_name = target_cert.issuer.get_attributes_for_oid(NameOID.COMMON_NAME)[0].value
		# file_path = "CCCerts/" + unidecode.unidecode(issuer_name) + ".cer"

		# print (os.path.isfile(file_path))

		# Get issuer's certificate
		issuer_name = target_cert.issuer.get_attributes_for_oid(NameOID.COMMON_NAME)[0].value
		subject_name = target_cert.subject.get_attributes_for_oid(NameOID.COMMON_NAME)[0].value

		# Certificate is self-signed, stop.
		if issuer_name == subject_name:
			log.debug("{} is self-signed, stopping!".format(subject_name))
			return True

		issuer_cert_path = "CCCerts/" + unidecode.unidecode(issuer_name) + ".cer"

		if not os.path.isfile(issuer_cert_path):
			raise RuntimeError("Certificate file not found: " + issuer_cert_path)

		with open(issuer_cert_path,'rb') as file:
			root_cert = None
			crl = None

			file_content = file.read()

			# Try to read in DER format, on error, try PEM. TODO: handle case in which both fail, i.e: wrong format file
			try:
				root_cert = x509.load_der_x509_certificate(file_content, default_backend())
				# crl = x509.load_der_x509_crl(file_content, default_backend())

			except ValueError:
				root_cert = x509.load_pem_x509_certificate(file_content, default_backend())
				# crl = x509.load_der_x509_crl(file_content, default_backend())

			try:
				root_cert.public_key().verify(
							target_cert.signature,
							target_cert.tbs_certificate_bytes,
							padding.PKCS1v15(),
							target_cert.signature_hash_algorithm)
				log.debug ("{} WAS VERIFIED BY => {}".format(subject_name, issuer_name))

				# Go 1 level up the chain
				target_cert = root_cert

			except:
				return False

def get_name_from_cert(cert):
	target_cert = x509.load_der_x509_certificate(bytes(cert), default_backend()) 
	subject_name = target_cert.subject.get_attributes_for_oid(NameOID.COMMON_NAME)[0].value
	return subject_name

def extract_auth_certificate():
	slots = pkcs11.getSlotList()

	auth_certificate = None

	for slot in slots:
		session = pkcs11.openSession(slot)
		token = pkcs11.getTokenInfo( slot )

		if 'CARTAO DE CIDADAO' in token.label:
			session = pkcs11.openSession( slot )
			auth_certificate = session.findObjects( [(CKA_CLASS, CKO_CERTIFICATE), (CKA_LABEL, "CITIZEN AUTHENTICATION CERTIFICATE")])[0]
			certificate_der = session.getAttributeValue( auth_certificate, [CKA_VALUE])[0]

			return certificate_der
		
		# Make sure we close slot session		
		session.closeSession()

def load_info_from_cert_der(raw_der_cert):
	cert = x509.load_der_x509_certificate(raw_der_cert)

### Native data is the whole packet
def validate_request(data, cert, signature):
	# cert = bytes.fromhex(cert)
	cert_chain_check = verify_certificate_chain(cert)

	# Check signature
	signature = bytes.fromhex(signature)

	# data = json.dumps(native_data, sort_keys=True)

	sign_check = verify_signature(cert, data, signature)

	return cert_chain_check and sign_check

