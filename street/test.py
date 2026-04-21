import unittest
import uuid
from datetime import datetime


class NameManager:
    def __init__(self):
        self.names = {}
        self.add("Удмуртская")
        self.add("Ленина")

    def add(self, names):
        if not names or any(s['name'] == names for s in self.names.values()):
            return False
        id = uuid.uuid4().hex
        self.names[id] = {
            'id': id,
            'name': names,
            'created_at': datetime.now(),
            'updated_at': datetime.now()
        }
        return True

    def update(self, id, names):
        if id not in self.names or not names:
            return False
        self.names[id]['name'] = names
        self.names[id]['updated_at'] = datetime.now()
        return True

    def delete(self, id):
        if id not in self.names:
            return False
        del self.names[id]
        return True

    def get_all(self):
        return list(self.names.values())


class TestNames(unittest.TestCase):
    def setUp(self):
        self.m = NameManager()

    def test_add(self):
        self.assertTrue(self.m.add('Пушкинская'))
        self.assertEqual(3, len(self.m.get_all()))

    def test_add_duplicate(self):
        self.assertFalse(self.m.add('Удмуртская'))

    def test_update(self):
        names = self.m.get_all()
        self.assertTrue(self.m.update(names[0]['id'], 'Удмуртская улица'))
        self.assertEqual('Удмуртская улица', self.m.get_all()[0]['name'])

    def test_update_nonexistent(self):
        self.assertFalse(self.m.update('ххх', 'Тест'))

    def test_delete(self):
        names = self.m.get_all()
        self.assertTrue(self.m.delete(names[1]['id']))
        self.assertEqual(1, len(self.m.get_all()))

    def test_delete_nonexistent(self):
        self.assertFalse(self.m.delete('ххх'))

    def test_get_all(self):
        names = self.m.get_all()
        self.assertEqual(2, len(names))
        names = [s['name'] for s in names]
        self.assertIn('Удмуртская', names)
        self.assertIn('Ленина', names)


if __name__ == '__main__':
    unittest.main()
