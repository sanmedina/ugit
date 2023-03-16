import hashlib
import os

GIT_DIR = ".ugit"


def init() -> None:
    os.makedirs(GIT_DIR)
    os.makedirs(f"{GIT_DIR}/objects")


def hash_object(data: bytes) -> str:
    oid = hashlib.sha1(data).hexdigest()
    with open(f"{GIT_DIR}/objects/{oid}", "wb") as out:
        out.write(data)
    return oid


def get_object(oid: str) -> bytes:
    with open(f"{GIT_DIR}/objects/{oid}", "rb") as f:
        return f.read()
