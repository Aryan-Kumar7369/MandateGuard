import jwt
import uuid
from datetime import datetime, timezone
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization

class CryptoService:
    @staticmethod
    def generate_key_pair() -> tuple[str, str]:
        private_key = ed25519.Ed25519PrivateKey.generate()
        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        ).decode("utf-8")

        public_key = private_key.public_key()
        public_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode("utf-8")

        return private_pem, public_pem

    @staticmethod
    def sign_mandate(payload: dict, private_key_pem: str) -> str:
        private_key = serialization.load_pem_private_key(
            private_key_pem.encode("utf-8"),
            password=None
        )
        claims = {
            **payload,
            "jti": str(uuid.uuid4()),
            "iat": datetime.now(timezone.utc),
            "aud": "mandateguard-preflight"
        }
        return jwt.encode(claims, private_key, algorithm="EdDSA")

    @staticmethod
    def verify_signature(token: str, public_key_pem: str) -> dict:
        public_key = serialization.load_pem_public_key(
            public_key_pem.encode("utf-8")
        )
        return jwt.decode(token, public_key, algorithms=["EdDSA"], audience="mandateguard-preflight")