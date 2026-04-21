import unittest
import uuid
from datetime import datetime


class StreetManager:
    def __init__(self):
        self.streets = {}
        self.add("Удмуртская")
        self.add("Ленина")

    def add(self, name):
        if not name or any(s['name'] == name for s in self.streets.values()):
            return False
        id = uuid.uuid4().hex
        self.streets[id] = {
            'id': id,
            'name': name,
            'created_at': datetime.now(),
            'updated_at': datetime.now()
        }
        return True

    def update(self, id, name):
        if id not in self.streets or not name:
            return False
        self.streets[id]['name'] = name
        self.streets[id]['updated_at'] = datetime.now()
        return True

    def delete(self, id):
        if id not in self.streets:
            return False
        del self.streets[id]
        return True

    def get_all(self):
        return list(self.streets.values())


class TestStreets(unittest.TestCase):
    def setUp(self):
        self.m = StreetManager()

    def test_add(self):
        self.assertTrue(self.m.add('Пушкинская'))
        self.assertEqual(3, len(self.m.get_all()))

    def test_add_duplicate(self):
        self.assertFalse(self.m.add('Удмуртская'))

    def test_update(self):
        streets = self.m.get_all()
        self.assertTrue(self.m.update(streets[0]['id'], 'Удмуртская улица'))
        self.assertEqual('Удмуртская улица', self.m.get_all()[0]['name'])

    def test_update_nonexistent(self):
        self.assertFalse(self.m.update('ххх', 'Тест'))

    def test_delete(self):
        streets = self.m.get_all()
        self.assertTrue(self.m.delete(streets[1]['id']))
        self.assertEqual(1, len(self.m.get_all()))

    def test_delete_nonexistent(self):
        self.assertFalse(self.m.delete('ххх'))


    def test_get_all(self):
        streets = self.m.get_all()
        self.assertEqual(2, len(streets))
        names = [s['name'] for s in streets]
        self.assertIn('Удмуртская', names)
        self.assertIn('Ленина', names)


if __name__ == '__main__':
    unittest.main()