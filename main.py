# generate_hash.py
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
plain = "1234"
h = pwd_context.hash(plain)
print(h)
