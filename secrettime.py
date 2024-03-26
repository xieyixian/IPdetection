
from time import time

from Cryptodome.Cipher import AES, DES, PKCS1_OAEP, DES3
from Cryptodome.Hash import SHA256
from Cryptodome.Protocol.SecretSharing import Shamir
from Cryptodome.PublicKey import RSA, ECC
from Cryptodome.Random import get_random_bytes
from Cryptodome.Signature import DSS


def aes_encryption():
    key = get_random_bytes(16)  # AES key size can be 16, 24, or 32 bytes long
    cipher = AES.new(key, AES.MODE_EAX)
    data = b'This is the data to encrypt' * 1000
    start_time = time()
    ciphertext, tag = cipher.encrypt_and_digest(data)
    end_time = time()
    print(f"AES Encryption took {end_time - start_time} seconds")

    # Decryption
    nonce = cipher.nonce
    cipher = AES.new(key, AES.MODE_EAX, nonce=nonce)
    start_time = time()
    decrypted_data = cipher.decrypt_and_verify(ciphertext, tag)
    end_time = time()
    print(f"AES Decryption took {end_time - start_time} seconds")

def des_encryption():
    key = get_random_bytes(8)  # DES key size is 8 bytes long
    cipher = DES.new(key, DES.MODE_EAX)
    data = b'This is the data to encrypt' * 1000
    start_time = time()
    ciphertext, tag = cipher.encrypt_and_digest(data)
    end_time = time()
    print(f"DES Encryption took {end_time - start_time} seconds")

    # Decryption
    nonce = cipher.nonce
    cipher = DES.new(key, DES.MODE_EAX, nonce=nonce)
    start_time = time()
    decrypted_data = cipher.decrypt_and_verify(ciphertext, tag)
    end_time = time()
    print(f"DES Decryption took {end_time - start_time} seconds")


def rsa_encryption():
    key = RSA.generate(2048)
    cipher = PKCS1_OAEP.new(key.publickey())
    data = b'This is the data to encrypt' * 100
    start_time = time()

    # 分段进行 RSA 加密
    max_length = key.size_in_bytes() - 2 * 20 - 2
    ciphertext = b""
    for i in range(0, len(data), max_length):
        chunk = data[i:i + max_length]
        ciphertext += cipher.encrypt(chunk)
    end_time = time()
    print(f"RSA Encryption took {end_time - start_time} seconds")

    # 解密
    cipher = PKCS1_OAEP.new(key)
    start_time = time()
    # 分段进行 RSA 解密
    decrypted_data = b""
    for i in range(0, len(ciphertext), key.size_in_bytes()):
        chunk = ciphertext[i:i + key.size_in_bytes()]
        decrypted_data += cipher.decrypt(chunk)
    end_time = time()
    print(f"RSA Decryption took {end_time - start_time} seconds")

def triple_des_encryption():
    key = DES3.adjust_key_parity(get_random_bytes(24))  # 3DES key size is 24 bytes long
    cipher = DES3.new(key, DES3.MODE_EAX)
    data = b'This is the data to encrypt' * 1000
    start_time = time()
    ciphertext, tag = cipher.encrypt_and_digest(data)
    end_time = time()
    print(f"3DES Encryption took {end_time - start_time} seconds")

    # Decryption
    nonce = cipher.nonce
    cipher = DES3.new(key, DES3.MODE_EAX, nonce=nonce)
    start_time = time()
    decrypted_data = cipher.decrypt_and_verify(ciphertext, tag)
    end_time = time()
    print(f"3DES Decryption took {end_time - start_time} seconds")

def ecc_signature():
    key = ECC.generate(curve='P-256')
    signer = DSS.new(key, 'fips-186-3')
    message = b'This is the message to sign'
    hash_obj = SHA256.new(message)
    start_time = time()
    signature = signer.sign(hash_obj)
    end_time = time()
    print(f"ECC Signature took {end_time - start_time} seconds")

    # Verification
    verifier = DSS.new(key.public_key(), 'fips-186-3')
    start_time = time()
    verifier.verify(hash_obj, signature)
    end_time = time()
    print(f"ECC Verification took {end_time - start_time} seconds")

def diffie_hellman_key_exchange():
    secret = get_random_bytes(16)
    start_time = time()
    shares = Shamir.split(2, 5, secret)  # 2 out of 5 shares are needed to reconstruct
    reconstructed_secret = Shamir.combine(shares[:2])
    end_time = time()
    print(f"Diffie-Hellman Key Exchange took {end_time - start_time} seconds")

if __name__ == "__main__":
    aes_encryption()
    des_encryption()
    triple_des_encryption()
    rsa_encryption()
    ecc_signature()
    diffie_hellman_key_exchange()
