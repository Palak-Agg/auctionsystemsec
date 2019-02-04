import sys
sys.path.append("auction")

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

lib = '/usr/lib/libpteidpkcs11.so'
pkcs11 = PyKCS11.PyKCS11Lib()
pkcs11.load(lib)

slots = pkcs11.getSlotList()	

def sign_data(data):
	for slot in slots:
		if 'CARTAO DE CIDADAO' in pkcs11.getTokenInfo( slot ).label:
			session = pkcs11.openSession( slot )

			privKey = session.findObjects([(CKA_CLASS, CKO_PRIVATE_KEY),
											(CKA_LABEL, 'CITIZEN AUTHENTICATION KEY')])[0]

			signature = bytes(session.sign(privKey, bytes(data, 'utf-8'), Mechanism(CKM_SHA1_RSA_PKCS)))
			
			session.closeSession()

			return signature


def verify_signature(certificate, data, signature):
	target_cert = x509.load_der_x509_certificate(bytes(certificate), default_backend())
	# try:
	target_cert.public_key().verify(signature, bytes(data, 'utf-8'), padding.PKCS1v15(), hashes.SHA1())
	print( 'SUCCESS')

	# except:
		# print ( 'VERIFICATION FAILED' )



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
			print ("{} is self-signed, stopping!".format(subject_name))
			break

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

			# print ("EXTENSIONS --------")
			# for ext in target_cert.extensions:
			# 	print (ext)


			try:
				root_cert.public_key().verify(
							target_cert.signature,
							target_cert.tbs_certificate_bytes,
							padding.PKCS1v15(),
							target_cert.signature_hash_algorithm)
				print ("{} WAS VERIFIED BY => {}".format(subject_name, issuer_name))

				# Go 1 level up the chain
				target_cert = root_cert

			except:
				print ("Verification failed!")
				return False

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

c = extract_auth_certificate()
data = "hehehehehe"
sign = sign_data(data)
verify_signature(c, data, sign)
# verify_certificate_chain(c)



'''
1 - Extract all certificates from card
2 - Iteratively verify them until
'''