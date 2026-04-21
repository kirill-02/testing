import unittest
import uuid
from datetime import datetime


class StreetManager:
    def __init__(self):
        self.streets = {}
        self.add('Удмуртская')
        self.add('Ленина')

    def add(self, name):
        if not name or any(s['name'] == name for s in self.streets.values()):
            return False
        id = uuid.uuid4().hex

