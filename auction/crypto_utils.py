from cryptography.fernet import Fernet
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import (padding, rsa, utils)
from cryptography.hazmat.primitives import hashes

def generate_key():
	key = Fernet.generate_key()
	return key

def encrypt_data_sym(data, key):
	f = Fernet(key)
	token = f.encrypt(data)
	return token

def decrypt_data_sym(data, key):
	f = Fernet(key)
	return f.decrypt(data)

def encrypt_data_asym(data, key):
	cipher_text = key.encrypt(
		data,
		padding.OAEP(
			mgf=padding.MGF1(algorithm=hashes.SHA256()),
			algorithm=hashes.SHA256(),
			label=None
			)
		)

	return cipher_text

def decrypt_data_asym(data, key):
	plain_text = key.decrypt(
		data,
		padding.OAEP(
			mgf=padding.MGF1(algorithm=hashes.SHA256()),
			algorithm=hashes.SHA256(),
			label=None
			)
		)

	return plain_text

def load_rsa_public_key(filepath):
	pub_key = None
	
	with open(filepath, "rb") as key_file:
		pub_key = serialization.load_pem_public_key(
		key_file.read(),
		backend=default_backend()
	)

	return pub_key

def load_rsa_private_key(filepath):
	private_key = None

	with open(filepath, "rb") as key_file:
		private_key = serialization.load_pem_private_key(
		key_file.read(),
		password=None,
		backend=default_backend()
	)

	return private_key

def hash_sha_str(data):
	digest = hashes.Hash(hashes.SHA256(), backend=default_backend())
	digest.update(bytes(data))
	return digest.finalize()

def IsInt(s):
    try: 
        int(s)
        return True
    except ValueError:
        return False