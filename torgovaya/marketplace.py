from flask import Flask, request
from flask_restful import Api, Resource
from datetime import datetime
import uuid

app = Flask(__name__)
api = Api(app)

users = {}
products = {}
reviews = {}
categories = {}


class Base:
    def __init__(self):
        self.id = str(uuid.uuid4())
        self.created = datetime.now()
    
    def dict(self):
        return {'id': self.id, 'created': self.created.isoformat()}


class User(Base):
    def __init__(self, username, email):
        super().__init__()
        self.username = username
        self.email = email
        self.products = []
        self.reviews = [] 
    
    def dict(self):
        d = super().dict()
        d.update({
            'username': self.username,
            'email': self.email,
            'products_count': len(self.products),
            'reviews_count': len(self.reviews)
        })
        return d


class Category(Base):
    def __init__(self, name):
        super().__init__()
        self.name = name
        self.products = []
    
    def dict(self):
        d = super().dict()
        d.update({'name': self.name, 'products_count': len(self.products)})
        return d


class Product(Base):
    def __init__(self, title, description, price, seller_id, category_id, quantity=1):
        super().__init__()
        self.title = title
        self.description = description
        self.price = float(price)
        self.seller_id = seller_id
        self.category_id = category_id
        self.quantity = quantity
        self.available = quantity
        self.reviews = []
        self.rating_sum = 0
        self.rating_count = 0
        self.views = 0
    
    def dict(self):
        d = super().dict()
        avg_rating = 0
        if self.rating_count > 0:
            avg_rating = round(self.rating_sum / self.rating_count, 1)
        
        d.update({
            'title': self.title,
            'description': self.description,
            'price': self.price,
            'seller_id': self.seller_id,
            'category_id': self.category_id,
            'quantity': self.quantity,
            'available': self.available,
            'reviews_count': len(self.reviews),
            'rating': avg_rating,
            'views': self.views
        })
        return d


class Review(Base):
    def __init__(self, product_id, user_id, rating, comment=''):
        super().__init__()
        self.product_id = product_id
        self.user_id = user_id
        self.rating = rating 
        self.comment = comment
        self.updated_at = None
    
    def dict(self):
        d = super().dict()
        d.update({
            'product_id': self.product_id,
            'user_id': self.user_id,
            'rating': self.rating,
            'comment': self.comment,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        })
        return d


def check(data, need):
    if not data or not all(f in data for f in need):
        return {'msg': f'Need: {need}'}, 400
    return None


class Users(Resource):
    def post(self):
        d = request.get_json()
        err = check(d, ['username', 'email'])
        if err: return err
        if any(u.email == d['email'] for u in users.values()):
            return {'msg': 'Email exists'}, 400
        u = User(d['username'], d['email'])
        users[u.id] = u
        return u.dict(), 201
    
    def get(self):
        return {'users': [u.dict() for u in users.values()], 'total': len(users)}, 200


class UserOne(Resource):
    def get(self, uid):
        u = users.get(uid)
        if not u: return {'msg': 'User not found'}, 404
        return u.dict(), 200


class Categories(Resource):
    def post(self):
        d = request.get_json()
        err = check(d, ['name'])
        if err: return err
        if any(c.name == d['name'] for c in categories.values()):
            return {'msg': 'Category exists'}, 400
        c = Category(d['name'])
        categories[c.id] = c
        return c.dict(), 201
    
    def get(self):
        return {'categories': [c.dict() for c in categories.values()], 'total': len(categories)}, 200


class Products(Resource):
    def post(self):
        d = request.get_json()
        err = check(d, ['title', 'price', 'seller_id', 'category_id'])
        if err: return err
        
        if d['seller_id'] not in users:
            return {'msg': 'Seller not found'}, 404
        if d['category_id'] not in categories:
            return {'msg': 'Category not found'}, 404
        
        p = Product(
            d['title'],
            d.get('description', ''),
            d['price'],
            d['seller_id'],
            d['category_id'],
            d.get('quantity', 1)
        )
        products[p.id] = p
        users[d['seller_id']].products.append(p.id)
        categories[d['category_id']].products.append(p.id)
        
        return p.dict(), 201
    
    def get(self):
        seller = request.args.get('seller_id')
        cat = request.args.get('category_id')
        min_price = request.args.get('min_price', type=float)
        max_price = request.args.get('max_price', type=float)
        
        res = []
        for p in products.values():
            if seller and p.seller_id != seller: continue
            if cat and p.category_id != cat: continue
            if min_price and p.price < min_price: continue
            if max_price and p.price > max_price: continue
            res.append(p.dict())
        
        return {'products': res, 'total': len(res)}, 200


class ProductOne(Resource):
    def get(self, pid):
        p = products.get(pid)
        if not p: return {'msg': 'Product not found'}, 404
        p.views += 1 
        
        data = p.dict()
        product_reviews = []
        for rid in p.reviews:
            if rid in reviews:
                r = reviews[rid].dict()
                if r['user_id'] in users:
                    r['username'] = users[r['user_id']].username
                product_reviews.append(r)
        data['reviews'] = product_reviews
        
        return data, 200
    
    def put(self, pid):
        p = products.get(pid)
        if not p: return {'msg': 'Product not found'}, 404
        
        d = request.get_json()
        if 'title' in d: p.title = d['title']
        if 'description' in d: p.description = d['description']
        if 'price' in d: p.price = float(d['price'])
        if 'quantity' in d: 
            diff = d['quantity'] - p.quantity
            p.quantity = d['quantity']
            p.available += diff
        
        return p.dict(), 200
    
    def delete(self, pid):
        p = products.get(pid)
        if not p: return {'msg': 'Product not found'}, 404
        
        for rid in p.reviews[:]:
            if rid in reviews:
                r = reviews[rid]
                if r.user_id in users and rid in users[r.user_id].reviews:
                    users[r.user_id].reviews.remove(rid)
                del reviews[rid]
        
        if p.seller_id in users and pid in users[p.seller_id].products:
            users[p.seller_id].products.remove(pid)
        
        if p.category_id in categories and pid in categories[p.category_id].products:
            categories[p.category_id].products.remove(pid)
        
        del products[pid]
        return {'msg': 'Product deleted'}, 200


class Reviews(Resource):
    def post(self):
        d = request.get_json()
        err = check(d, ['product_id', 'user_id', 'rating'])
        if err: return err
        
        if d['product_id'] not in products:
            return {'msg': 'Product not found'}, 404
        if d['user_id'] not in users:
            return {'msg': 'User not found'}, 404
        
        for rid in products[d['product_id']].reviews:
            if rid in reviews and reviews[rid].user_id == d['user_id']:
                return {'msg': 'Already reviewed'}, 400
        
        if d['rating'] < 1 or d['rating'] > 5:
            return {'msg': 'Rating must be 1-5'}, 400
        
        r = Review(d['product_id'], d['user_id'], d['rating'], d.get('comment', ''))
        reviews[r.id] = r
        
        products[d['product_id']].reviews.append(r.id)
        products[d['product_id']].rating_sum += d['rating']
        products[d['product_id']].rating_count += 1
        
        users[d['user_id']].reviews.append(r.id)
        
        return r.dict(), 201
    
    def get(self):
        pid = request.args.get('product_id')
        uid = request.args.get('user_id')
        
        res = []
        for r in reviews.values():
            if pid and r.product_id != pid: continue
            if uid and r.user_id != uid: continue
            review_data = r.dict()
            if r.user_id in users:
                review_data['username'] = users[r.user_id].username
            if r.product_id in products:
                review_data['product_title'] = products[r.product_id].title
            res.append(review_data)
        
        return {'reviews': res, 'total': len(res)}, 200


class ReviewOne(Resource):
    def get(self, rid):
        r = reviews.get(rid)
        if not r: return {'msg': 'Review not found'}, 404
        return r.dict(), 200
    
    def put(self, rid):
        r = reviews.get(rid)
        if not r: return {'msg': 'Review not found'}, 404
        
        d = request.get_json()
        old_rating = r.rating
        
        if 'rating' in d:
            if d['rating'] < 1 or d['rating'] > 5:
                return {'msg': 'Rating must be 1-5'}, 400
            r.rating = d['rating']
        if 'comment' in d:
            r.comment = d['comment']
        
        r.updated_at = datetime.now()
        
        if r.product_id in products:
            p = products[r.product_id]
            p.rating_sum = p.rating_sum - old_rating + r.rating
        
        return r.dict(), 200
    
    def delete(self, rid):
        r = reviews.get(rid)
        if not r: return {'msg': 'Review not found'}, 404
        
        if r.product_id in products:
            p = products[r.product_id]
            if rid in p.reviews:
                p.reviews.remove(rid)
                p.rating_sum -= r.rating
                p.rating_count -= 1
        
        if r.user_id in users and rid in users[r.user_id].reviews:
            users[r.user_id].reviews.remove(rid)
        
        del reviews[rid]
        return {'msg': 'Review deleted'}, 200


api.add_resource(Users, '/api/users')
api.add_resource(UserOne, '/api/users/<string:uid>')
api.add_resource(Categories, '/api/categories')
api.add_resource(Products, '/api/products')
api.add_resource(ProductOne, '/api/products/<string:pid>')
api.add_resource(Reviews, '/api/reviews')
api.add_resource(ReviewOne, '/api/reviews/<string:rid>')

if __name__ == '__main__':
    app.run(debug=True)