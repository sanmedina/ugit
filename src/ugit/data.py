import hashlib
import os

GIT_DIR = ".ugit"


def init() -> None:
    os.makedirs(GIT_DIR)
    os.makedirs(f"{GIT_DIR}/objects")


def hash_object(data: bytes, type_="blob") -> str:
    obj = type_.encode() + b"\x00" + data
    oid = hashlib.sha1(obj).hexdigest()
    with open(f"{GIT_DIR}/objects/{oid}", "wb") as out:
        out.write(obj)
    return oid


def get_object(oid: str, exptected="blob") -> bytes:
    with open(f"{GIT_DIR}/objects/{oid}", "rb") as f:
        obj = f.read()

    type_, _, content = obj.partition(b"\x00")
    type_ = type_.decode()

    if exptected is not None:
        assert type_ == exptected, f"Expected {exptected}, got {type_}"
    return content
