import hashlib
from datetime import datetime
import json


class Blok:
    def __init__(self, index, data, timestamp, hash, previous_hash, nonce, tezavnost):
        self.index = index
        self.data = data
        self.timestamp = timestamp
        self.hash = hash
        self.previous_hash = previous_hash
        self.nonce = nonce
        self.tezavnost = tezavnost

    def __repr__(self) -> json:
        block = {
            "index": self.index,
            "data": self.data,
            "timestamp": self.timestamp,
            "hash": self.hash,
            "previous_hash": self.previous_hash,
            "nonce": self.nonce,
            "tezavnost": self.tezavnost,
        }
        return json.dumps(block, indent=1)


def ustvari_zacetni_blok():
    index = 0
    data = "Zacetni Blok"
    timestamp = datetime.timestamp(datetime.now())
    previous_hash = ""
    nonce = 0
    tezavnost = 0
    hash = hashlib.sha256(
        (str(index) + str(timestamp) + data + previous_hash + str(tezavnost) + str(nonce)).encode()).hexdigest()
    return Blok(index, data, timestamp, hash, previous_hash, nonce, tezavnost)
