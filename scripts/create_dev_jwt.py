#!/usr/bin/env python3

import jwt
import datetime

# Define a secret key for signing the token
# In production, store this securely (e.g. environment variable)
SECRET_KEY = "this-is-my-super-secret-development-key"  # nosec

payload = {
    "https://samboyd.dev/role": "authenticated",
    "sud":"8ef90f89-4d5c-4e1b-8c73-5db544249f1e", 
    "exp": datetime.datetime.now(datetime.UTC) + datetime.timedelta(days=1),
}

encoded_jwt = jwt.encode(payload, SECRET_KEY, algorithm="HS256")

print(f"\nEncoded JWT:\n\n{encoded_jwt}\n")

try:
    decoded_payload = jwt.decode(encoded_jwt, SECRET_KEY, algorithms=["HS256"])
    print("Decoded Payload:", decoded_payload)
except jwt.ExpiredSignatureError:
    print("Token has expired.")
except jwt.InvalidTokenError:
    print("Invalid token.")
