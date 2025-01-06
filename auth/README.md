# Generate an RSA private key, of size 2048
openssl genrsa -out jwt-private.pem 2048

# Generate the public key from the key pair, with can used in a certificate
openssl rsa -in jwt-private.pem -pubout -out jwt-public.pem