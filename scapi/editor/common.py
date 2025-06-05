
import random
import string

ID_CHARS = string.ascii_letters + string.digits + string.punctuation

def create_new_id() -> str:
    return ''.join(random.choices(ID_CHARS, k=20))