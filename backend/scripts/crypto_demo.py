import base64
import hashlib
import os
import sys

import requests
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

API = os.environ.get("API", "http://127.0.0.1:8000/api")
EMAIL = os.environ.get("EMAIL", "alice@example.com")
PASSWORD = os.environ.get("PASSWORD", "SuperSecret123")


def derive_key(password, salt_b64, iterations):
    salt = base64.b64decode(salt_b64)
    return hashlib.pbkdf2_hmac("sha256", password.encode(), salt, iterations, dklen=32)


def main():
    source = sys.argv[1] if len(sys.argv) > 1 else __file__
    plaintext = open(source, "rb").read()
    print(f"[*] Source file: {source} ({len(plaintext)} bytes)")

    tokens = requests.post(f"{API}/auth/login/", json={"email": EMAIL, "password": PASSWORD}).json()
    auth = {"Authorization": f"Bearer {tokens['access']}"}

    me = requests.get(f"{API}/auth/me/", headers=auth).json()
    key = derive_key(PASSWORD, me["kdf_salt"], me["kdf_iterations"])
    print(f"[*] Derived AES-256 key (PBKDF2, {me['kdf_iterations']} iters): {key.hex()[:32]}...")

    nonce = os.urandom(12)
    ciphertext = AESGCM(key).encrypt(nonce, plaintext, None)
    print(f"[*] Encrypted -> {len(ciphertext)} bytes ciphertext (incl. 16-byte GCM tag)")
    print(f"    ciphertext preview: {ciphertext[:24].hex()}")

    files = {"blob": ("blob.enc", ciphertext, "application/octet-stream")}
    data = {"name": os.path.basename(source), "nonce": base64.b64encode(nonce).decode()}
    up = requests.post(f"{API}/files/", headers=auth, files=files, data=data).json()
    file_id = up["id"]
    print(f"[*] Uploaded. Server stored file id={file_id}")

    dl = requests.get(f"{API}/files/{file_id}/download/", headers=auth)
    server_blob = dl.content
    server_nonce = base64.b64decode(dl.headers["X-File-Nonce"])
    print(f"[*] Downloaded {len(server_blob)} bytes + nonce from X-File-Nonce header")

    try:
        server_blob.decode("utf-8")
        print("    !! server stored readable text")
    except UnicodeDecodeError:
        print("    -> what the server holds is unreadable ciphertext (zero-knowledge OK)")

    recovered = AESGCM(key).decrypt(server_nonce, server_blob, None)
    assert recovered == plaintext, "decryption mismatch!"
    print(f"[+] Decrypted in 'browser' -> {len(recovered)} bytes, matches original exactly. ✅")


if __name__ == "__main__":
    main()
