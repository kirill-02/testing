from flask import Flask, request
from flask_restful import Api, Resource
from datetime import datetime
import uuid

app = Flask(__name__)
api = Api(app)

users, transactions, categories = {}, {}, {}


class Base:
    def __init__(self):
        self.id = str(uuid.uuid4())
        self.created = datetime.now()
    
    def dict(self):
        return {'id': self.id, 'created': self.created.isoformat()}


class User(Base):
    def __init__(self, name, email):
        super().__init__()
        self.name = name
        self.email = email
        self.transactions = []  
    
    def dict(self):
        d = super().dict()
        d.update({'name': self.name, 'email': self.email, 'transactions': len(self.transactions)})
        return d


class Category(Base):
    def __init__(self, name, user_id, type='expense'):  
        super().__init__()
        self.name = name
        self.user_id = user_id
        self.type = type  
    
    def dict(self):
        d = super().dict()
        d.update({'name': self.name, 'user_id': self.user_id, 'type': self.type})
        return d


class Transaction(Base):
    def __init__(self, amount, type, category_id, user_id, description=''):
        super().__init__()
        self.amount = float(amount)
        self.type = type  
        self.category_id = category_id
        self.user_id = user_id
        self.description = description
        self.date = datetime.now()
    
    def dict(self):
        d = super().dict()
        d.update({
            'amount': self.amount,
            'type': self.type,
            'category_id': self.category_id,
            'user_id': self.user_id,
            'description': self.description,
            'date': self.date.isoformat()
        })
        return d


def check(data, need):
    if not data or not all(f in data for f in need):
        return {'msg': f'Need: {need}'}, 400
    return None


class Users(Resource):
    def post(self):
        d = request.get_json()
        err = check(d, ['name', 'email'])
        if err: return err
        if any(u.email == d['email'] for u in users.values()):
            return {'msg': 'Email exists'}, 400
        u = User(d['name'], d['email'])
        users[u.id] = u
        return u.dict(), 201


class UserOne(Resource):
    def get(self, uid):
        u = users.get(uid)
        if not u: return {'msg': 'No user'}, 404
        return u.dict(), 200
    
    def delete(self, uid):
        u = users.get(uid)
        if not u: return {'msg': 'No user'}, 404
        for tid in u.transactions[:]:
            if tid in transactions:
                del transactions[tid]
        del users[uid]
        return {'msg': 'User deleted'}, 200


class Categories(Resource):
    def post(self):
        d = request.get_json()
        err = check(d, ['name', 'user_id', 'type'])
        if err: return err
        if d['user_id'] not in users:
            return {'msg': 'User not found'}, 404
        if d['type'] not in ['income', 'expense']:
            return {'msg': 'Type must be income or expense'}, 400
        c = Category(d['name'], d['user_id'], d['type'])
        categories[c.id] = c
        return c.dict(), 201
    
    def get(self):
        uid = request.args.get('user_id')
        typ = request.args.get('type')
        res = []
        for c in categories.values():
            if uid and c.user_id != uid: continue
            if typ and c.type != typ: continue
            res.append(c.dict())
        return {'categories': res, 'total': len(res)}, 200


class Transactions(Resource):
    def post(self):
        d = request.get_json()
        err = check(d, ['amount', 'type', 'category_id', 'user_id'])
        if err: return err
        
        if d['user_id'] not in users:
            return {'msg': 'User not found'}, 404
        if d['category_id'] not in categories:
            return {'msg': 'Category not found'}, 404
        if d['type'] not in ['income', 'expense']:
            return {'msg': 'Type must be income or expense'}, 400
        
        cat = categories[d['category_id']]
        if cat.user_id != d['user_id']:
            return {'msg': 'Category does not belong to user'}, 400
        if cat.type != d['type']:
            return {'msg': 'Category type mismatch'}, 400
        
        t = Transaction(
            d['amount'], 
            d['type'], 
            d['category_id'], 
            d['user_id'], 
            d.get('description', '')
        )
        transactions[t.id] = t
        users[d['user_id']].transactions.append(t.id)
        
        return t.dict(), 201
    
    def get(self):
        uid = request.args.get('user_id')
        cat_id = request.args.get('category_id')
        typ = request.args.get('type')
        
        res = []
        for t in transactions.values():
            if uid and t.user_id != uid: continue
            if cat_id and t.category_id != cat_id: continue
            if typ and t.type != typ: continue
            res.append(t.dict())
        
        return {'transactions': res, 'total': len(res)}, 200


class TransactionOne(Resource):
    def get(self, tid):
        t = transactions.get(tid)
        if not t: return {'msg': 'Transaction not found'}, 404
        return t.dict(), 200
    
    def delete(self, tid):
        t = transactions.get(tid)
        if not t: return {'msg': 'Transaction not found'}, 404
        
        if t.user_id in users and tid in users[t.user_id].transactions:
            users[t.user_id].transactions.remove(tid)
        
        del transactions[tid]
        return {'msg': 'Transaction deleted'}, 200


class Stats(Resource):
    def get(self, uid):
        if uid not in users:
            return {'msg': 'User not found'}, 404
        
        total_income = 0.0
        total_expense = 0.0
        by_category = {}
        
        for tid in users[uid].transactions:
            if tid not in transactions: continue
            t = transactions[tid]
            
            if t.type == 'income':
                total_income += t.amount
            else:
                total_expense += t.amount
            
            if t.category_id not in by_category:
                cat = categories.get(t.category_id)
                by_category[t.category_id] = {
                    'category_name': cat.name if cat else 'Unknown',
                    'category_type': cat.type if cat else 'unknown',
                    'total': 0.0,
                    'count': 0
                }
            by_category[t.category_id]['total'] += t.amount
            by_category[t.category_id]['count'] += 1
        
        balance = total_income - total_expense
        
        return {
            'user_id': uid,
            'total_income': round(total_income, 2),
            'total_expense': round(total_expense, 2),
            'balance': round(balance, 2),
            'transactions_count': len(users[uid].transactions),
            'by_category': by_category
        }, 200


api.add_resource(Users, '/api/users')
api.add_resource(UserOne, '/api/users/<string:uid>')
api.add_resource(Categories, '/api/categories')
api.add_resource(Transactions, '/api/transactions')
api.add_resource(TransactionOne, '/api/transactions/<string:tid>')
api.add_resource(Stats, '/api/users/<string:uid>/stats')

if __name__ == '__main__':
    app.run(debug=True)