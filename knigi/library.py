from flask import Flask, request
from flask_restful import Api, Resource
from datetime import datetime, timedelta
import uuid

app = Flask(__name__)
api = Api(app)

books, readers, loans = {}, {}, {}


class BaseModel:
    def __init__(self):
        self.id = str(uuid.uuid4())
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
    
    def to_dict(self):
        return {'id': self.id, 'created_at': self.created_at.isoformat()}


class Book(BaseModel):
    def __init__(self, title, author, isbn, year, quantity=1):
        super().__init__()
        self.title = title
        self.author = author
        self.isbn = isbn
        self.year = year
        self.quantity = quantity
        self.available = quantity
        self.loaned = 0
    
    def to_dict(self):
        d = super().to_dict()
        d.update({'title': self.title, 'author': self.author, 'isbn': self.isbn,
                 'year': self.year, 'quantity': self.quantity, 'available': self.available})
        return d


class Reader(BaseModel):
    def __init__(self, name, email, phone):
        super().__init__()
        self.name = name
        self.email = email
        self.phone = phone
        self.active = []  
        self.history = []  
    
    def to_dict(self):
        d = super().to_dict()
        d.update({'name': self.name, 'email': self.email, 'phone': self.phone,
                 'active': len(self.active), 'total': len(self.history)})
        return d


class Loan(BaseModel):
    def __init__(self, book_id, reader_id, days=14):
        super().__init__()
        self.book_id = book_id
        self.reader_id = reader_id
        self.loan_date = datetime.now()
        self.due_date = self.loan_date + timedelta(days=days)
        self.return_date = None
        self.status = 'active'
    
    def to_dict(self):
        d = super().to_dict()
        d.update({'book_id': self.book_id, 'reader_id': self.reader_id,
                 'loan_date': self.loan_date.isoformat(), 'due_date': self.due_date.isoformat(),
                 'return_date': self.return_date.isoformat() if self.return_date else None,
                 'status': self.status})
        return d


def validate(data, fields):
    if not data or not all(f in data for f in fields):
        return {'message': f'Required: {fields}'}, 400
    return None


class BookList(Resource):
    def get(self):
        return {'books': [b.to_dict() for b in books.values()], 'total': len(books)}, 200
    
    def post(self):
        data = request.get_json()
        err = validate(data, ['title', 'author', 'isbn', 'year'])
        if err: return err
        
        if any(b.isbn == data['isbn'] for b in books.values()):
            return {'message': 'ISBN exists'}, 400
        
        b = Book(data['title'], data['author'], data['isbn'], data['year'], data.get('quantity', 1))
        books[b.id] = b
        return b.to_dict(), 201


class BookRes(Resource):
    def get(self, bid):
        b = books.get(bid)
        if not b: return {'message': 'Not found'}, 404
        return b.to_dict(), 200
    
    def delete(self, bid):
        b = books.get(bid)
        if not b: return {'message': 'Not found'}, 404
        
        if any(l.book_id == bid and l.status == 'active' for l in loans.values()):
            return {'message': 'Has active loans'}, 400
        
        del books[bid]
        return {'message': 'Deleted'}, 200


class ReaderList(Resource):
    def post(self):
        data = request.get_json()
        err = validate(data, ['name', 'email', 'phone'])
        if err: return err
        
        if any(r.email == data['email'] for r in readers.values()):
            return {'message': 'Email exists'}, 400
        
        r = Reader(data['name'], data['email'], data['phone'])
        readers[r.id] = r
        return r.to_dict(), 201


class ReaderRes(Resource):
    def get(self, rid):
        r = readers.get(rid)
        if not r: return {'message': 'Not found'}, 404
        
        d = r.to_dict()
        d['active_loans'] = [loans[l].to_dict() for l in r.active if l in loans]
        d['history'] = [loans[l].to_dict() for l in r.history if l in loans and l not in r.active]
        return d, 200
    
    def delete(self, rid):
        r = readers.get(rid)
        if not r: return {'message': 'Not found'}, 404
        if r.active: return {'message': 'Has active loans'}, 400
        del readers[rid]
        return {'message': 'Deleted'}, 200


class LoanList(Resource):
    def post(self):
        data = request.get_json()
        err = validate(data, ['book_id', 'reader_id'])
        if err: return err
        
        if data['book_id'] not in books: return {'message': 'Book not found'}, 404
        if data['reader_id'] not in readers: return {'message': 'Reader not found'}, 404
        
        book = books[data['book_id']]
        if book.available <= 0: return {'message': 'No copies'}, 400
        
        loan = Loan(data['book_id'], data['reader_id'], data.get('loan_days', 14))
        loans[loan.id] = loan
        
        book.available -= 1
        book.loaned += 1
        
        reader = readers[data['reader_id']]
        reader.active.append(loan.id)
        reader.history.append(loan.id)
        
        return loan.to_dict(), 201


class LoanRes(Resource):
    def put(self, lid):
        loan = loans.get(lid)
        if not loan: return {'message': 'Not found'}, 404
        if loan.status == 'returned': return {'message': 'Already returned'}, 400
        
        loan.return_date = datetime.now()
        loan.status = 'returned'
        
        if loan.book_id in books:
            books[loan.book_id].available += 1
        
        if loan.reader_id in readers and loan.id in readers[loan.reader_id].active:
            readers[loan.reader_id].active.remove(loan.id)
        
        return loan.to_dict(), 200
    
    def get(self, lid):
        loan = loans.get(lid)
        if not loan: return {'message': 'Not found'}, 404
        return loan.to_dict(), 200


api.add_resource(BookList, '/api/books')
api.add_resource(BookRes, '/api/books/<string:bid>')
api.add_resource(ReaderList, '/api/readers')
api.add_resource(ReaderRes, '/api/readers/<string:rid>')
api.add_resource(LoanList, '/api/loans')
api.add_resource(LoanRes, '/api/loans/<string:lid>')

if __name__ == '__main__':
    app.run(debug=True)