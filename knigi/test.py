import unittest
import json
from library import app, books, readers, loans, Book, Reader, Loan

class TestLibrary(unittest.TestCase):
    
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True
        
        books.clear(); readers.clear(); loans.clear()
        
        self.book = Book("Test Book", "Author", "123", 2024, 3)
        books[self.book.id] = self.book
        
        self.reader = Reader("Test Reader", "r@t.com", "+123")
        readers[self.reader.id] = self.reader
        
        self.loan = Loan(self.book.id, self.reader.id)
        loans[self.loan.id] = self.loan
        self.book.available = 2
        self.book.loaned = 1
        self.reader.active.append(self.loan.id)
        self.reader.history.append(self.loan.id)
    
    def tearDown(self):
        books.clear(); readers.clear(); loans.clear()
    
    def post(self, url, data):
        return self.app.post(url, data=json.dumps(data), content_type='application/json')
    
    def put(self, url, data):
        return self.app.put(url, data=json.dumps(data), content_type='application/json')
    
    def test_1_add_book(self):
        data = {'title': 'New', 'author': 'Ivanov', 'isbn': '978-5', 'year': 2025, 'quantity': 5}
        r = self.post('/api/books', data)
        self.assertEqual(r.status_code, 201)
        d = json.loads(r.data)
        self.assertEqual(d['title'], 'New')
        self.assertEqual(d['quantity'], 5)
        self.assertEqual(d['available'], 5)
        self.assertIn(d['id'], books)
    
    def test_2_delete_book(self):
        b = Book("Del", "A", "999", 2024)
        books[b.id] = b
        r = self.app.delete(f'/api/books/{b.id}')
        self.assertEqual(r.status_code, 200)
        self.assertNotIn(b.id, books)
    
    def test_3_cant_delete_with_loans(self):
        r = self.app.delete(f'/api/books/{self.book.id}')
        self.assertEqual(r.status_code, 400)
        self.assertIn(self.book.id, books)
    
    def test_4_register_reader(self):
        data = {'name': 'Petr', 'email': 'p@mail.com', 'phone': '+7999'}
        r = self.post('/api/readers', data)
        self.assertEqual(r.status_code, 201)
        d = json.loads(r.data)
        self.assertEqual(d['name'], 'Petr')
        self.assertEqual(d['active'], 0)
        self.assertIn(d['id'], readers)


    def test_5_loan_book(self):
        b = Book("Loan", "A", "111", 2024, 2)
        books[b.id] = b
        rdr = Reader("R", "r@r.com", "+1")
        readers[rdr.id] = rdr
        
        data = {'book_id': b.id, 'reader_id': rdr.id}
        r = self.post('/api/loans', data)
        self.assertEqual(r.status_code, 201)
        
        self.assertEqual(books[b.id].available, 1)
        self.assertEqual(books[b.id].loaned, 1)
        self.assertEqual(len(readers[rdr.id].active), 1)
        self.assertEqual(len(readers[rdr.id].history), 1)
    
    def test_6_return_book(self):
        self.assertEqual(books[self.book.id].available, 2)
        self.assertIn(self.loan.id, readers[self.reader.id].active)
        
        r = self.put(f'/api/loans/{self.loan.id}', {})
        self.assertEqual(r.status_code, 200)
        
        self.assertEqual(books[self.book.id].available, 3)
        self.assertNotIn(self.loan.id, readers[self.reader.id].active)
        self.assertEqual(loans[self.loan.id].status, 'returned')
    
    def test_7_cant_loan_unavailable(self):
        b = Book("Rare", "A", "555", 2024, 1)
        books[b.id] = b
        r1 = Reader("R1", "r1@t.com", "+1")
        r2 = Reader("R2", "r2@t.com", "+2")
        readers[r1.id] = r1
        readers[r2.id] = r2
        
        r = self.post('/api/loans', {'book_id': b.id, 'reader_id': r1.id})
        self.assertEqual(r.status_code, 201)
        
        r = self.post('/api/loans', {'book_id': b.id, 'reader_id': r2.id})
        self.assertEqual(r.status_code, 400)
    
    def test_8_reader_history(self):
        b2 = Book("Book2", "A2", "222", 2024, 1)
        books[b2.id] = b2
        l2 = Loan(b2.id, self.reader.id)
        loans[l2.id] = l2
        self.reader.active.append(l2.id)
        self.reader.history.append(l2.id)
        b2.available = 0
        
        self.put(f'/api/loans/{l2.id}', {})
        
        r = self.app.get(f'/api/readers/{self.reader.id}')
        d = json.loads(r.data)
        self.assertEqual(len(d['active_loans']), 1)
        self.assertEqual(len(d['history']), 1)  


if __name__ == '__main__':
    unittest.main()