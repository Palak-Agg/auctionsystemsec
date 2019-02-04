import os
from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import padding
import requests, datetime

def load_certificate(cert):
    try:
        certLoaded = x509.load_pem_x509_certificate(cert, default_backend())
    except:
        certLoaded = x509.load_der_x509_certificate(cert, default_backend())
    return certLoaded

def load_crl(cert):
    try:
        certLoaded = x509.load_pem_x509_crl(cert, default_backend())
    except:
        certLoaded = x509.load_der_x509_crl(cert, default_backend())
    return certLoaded

def verify_cert(cert, cert_root):
    try:
        cert_root.public_key().verify(
            cert.signature,
            cert.tbs_certificate_bytes,
            padding.PKCS1v15(),
            cert.signature_hash_algorithm
        )
    except:
        return False
    return True

def get_crl_of_cert(cert):
    for ext in cert.extensions:
        if ext.oid._name == 'cRLDistributionPoints':
            distPoints = ext.value
            for distPoint in distPoints:
                return distPoint.full_name[0].value

def check_certs(cert, certRoot):
    # Check if signed by root
    if (not verify_cert(cert, certRoot)):
        return False

    # Get CRL
    crl_name = get_crl_of_cert(cert)
    r = requests.get(crl_name)
    crltemp = load_crl(r.content)

    #Check CRL signature
    if not crltemp.is_signature_valid(certRoot.public_key()):
        return False

    #Check if certificate in CRL
    if crltemp.get_revoked_certificate_by_serial_number(cert.serial_number):
        return False

    #Check if certificates expired
    if cert.not_valid_after < datetime.datetime.now() \
        or certRoot.not_valid_after < datetime.datetime.now():
        return False

    return True
