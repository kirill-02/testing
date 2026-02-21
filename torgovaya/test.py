import unittest
import json
from marketplace import app, users, products, reviews, categories, User, Category, Product, Review
from datetime import datetime, timedelta


class TestMarketplace(unittest.TestCase):
    
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True
        
        users.clear(); products.clear(); reviews.clear(); categories.clear()
        
        self.seller = User("Seller", "seller@mail.com")
        users[self.seller.id] = self.seller
        
        self.buyer = User("Buyer", "buyer@mail.com")
        users[self.buyer.id] = self.buyer
        
        self.category = Category("Electronics")
        categories[self.category.id] = self.category
        
        self.product = Product(
            "iPhone", 
            "Smartphone", 
            999.99, 
            self.seller.id, 
            self.category.id, 
            5
        )
        products[self.product.id] = self.product
        self.seller.products.append(self.product.id)
        self.category.products.append(self.product.id)
        
        self.review = Review(self.product.id, self.buyer.id, 5, "Great phone!")
        reviews[self.review.id] = self.review
        self.product.reviews.append(self.review.id)
        self.product.rating_sum = 5
        self.product.rating_count = 1
        self.buyer.reviews.append(self.review.id)
    
    def tearDown(self):
        users.clear(); products.clear(); reviews.clear(); categories.clear()
    
    def post(self, url, d):
        return self.app.post(url, data=json.dumps(d), content_type='application/json')
    
    def put(self, url, d):
        return self.app.put(url, data=json.dumps(d), content_type='application/json')
    
    def test_1_create_product(self):
        """Сценарий 1: Создание нового объявления о продаже"""
        d = {
            'title': 'MacBook Pro',
            'description': 'Laptop 16"',
            'price': 1999.99,
            'seller_id': self.seller.id,
            'category_id': self.category.id,
            'quantity': 3
        }
        r = self.post('/api/products', d)
        self.assertEqual(r.status_code, 201)
        data = json.loads(r.data)
        
        self.assertEqual(data['title'], 'MacBook Pro')
        self.assertEqual(data['price'], 1999.99)
        self.assertEqual(data['quantity'], 3)
        self.assertEqual(data['available'], 3)
        self.assertEqual(data['reviews_count'], 0)
        self.assertEqual(data['rating'], 0)
        
        self.assertIn(data['id'], products)
        self.assertIn(data['id'], users[self.seller.id].products)
        self.assertIn(data['id'], categories[self.category.id].products)
    
    def test_2_get_product_with_reviews(self):
        """Сценарий 2: Просмотр товара с отзывами"""
        r = self.app.get(f'/api/products/{self.product.id}')
        self.assertEqual(r.status_code, 200)
        data = json.loads(r.data)
        
        self.assertEqual(data['title'], 'iPhone')
        self.assertEqual(data['price'], 999.99)
        self.assertEqual(data['views'], 1)  
        self.assertEqual(data['reviews_count'], 1)
        self.assertEqual(data['rating'], 5.0)
        
        self.assertIn('reviews', data)
        self.assertEqual(len(data['reviews']), 1)
        self.assertEqual(data['reviews'][0]['comment'], 'Great phone!')
        self.assertEqual(data['reviews'][0]['rating'], 5)
    
    def test_3_update_product(self):
        """Сценарий 3: Редактирование товара"""
        d = {
            'title': 'iPhone 15',
            'price': 1099.99,
            'quantity': 10
        }
        r = self.put(f'/api/products/{self.product.id}', d)
        self.assertEqual(r.status_code, 200)
        data = json.loads(r.data)
        
        self.assertEqual(data['title'], 'iPhone 15')
        self.assertEqual(data['price'], 1099.99)
        self.assertEqual(data['quantity'], 10)
        self.assertEqual(data['available'], 10) 
        
        self.assertEqual(products[self.product.id].title, 'iPhone 15')
    
    def test_4_delete_product_with_reviews(self):
        """Сценарий 4: Удаление товара вместе с отзывами"""
        self.assertIn(self.product.id, products)
        self.assertIn(self.review.id, reviews)
        self.assertEqual(len(products), 1)
        self.assertEqual(len(reviews), 1)
        
        r = self.app.delete(f'/api/products/{self.product.id}')
        self.assertEqual(r.status_code, 200)
        data = json.loads(r.data)
        self.assertEqual(data['msg'], 'Product deleted')
        
        self.assertNotIn(self.product.id, products)
        
        self.assertEqual(len(reviews), 0)
        
        self.assertNotIn(self.product.id, users[self.seller.id].products)
        self.assertNotIn(self.product.id, categories[self.category.id].products)
        self.assertNotIn(self.review.id, users[self.buyer.id].reviews)
    
    def test_5_add_review(self):
        """Сценарий 5: Добавление отзыва к товару"""
        user3 = User("Charlie", "charlie@mail.com")
        users[user3.id] = user3
        
        d = {
            'product_id': self.product.id,
            'user_id': user3.id,
            'rating': 4,
            'comment': 'Good product'
        }
        r = self.post('/api/reviews', d)
        self.assertEqual(r.status_code, 201)
        data = json.loads(r.data)
        
        self.assertEqual(data['rating'], 4)
        self.assertEqual(data['comment'], 'Good product')
        
        p = products[self.product.id]
        self.assertEqual(p.rating_sum, 9) 
        self.assertEqual(p.rating_count, 2)
        self.assertEqual(len(p.reviews), 2)
        
        self.assertIn(data['id'], users[user3.id].reviews)
    
    def test_6_edit_review(self):
        """Сценарий 6: Редактирование отзыва"""
        self.assertEqual(self.product.rating_sum, 5)
        
        d = {
            'rating': 3,
            'comment': 'Updated review'
        }
        r = self.put(f'/api/reviews/{self.review.id}', d)
        self.assertEqual(r.status_code, 200)
        data = json.loads(r.data)
        
        self.assertEqual(data['rating'], 3)
        self.assertEqual(data['comment'], 'Updated review')
        self.assertIsNotNone(data['updated_at'])
        
        self.assertEqual(products[self.product.id].rating_sum, 3) 
        self.assertEqual(products[self.product.id].rating_count, 1)
    
    def test_7_delete_review(self):
        """Сценарий 7: Удаление отзыва"""
        self.assertIn(self.review.id, reviews)
        self.assertIn(self.review.id, products[self.product.id].reviews)
        self.assertIn(self.review.id, users[self.buyer.id].reviews)
        
        r = self.app.delete(f'/api/reviews/{self.review.id}')
        self.assertEqual(r.status_code, 200)
        data = json.loads(r.data)
        self.assertEqual(data['msg'], 'Review deleted')
        
        self.assertNotIn(self.review.id, reviews)
        self.assertNotIn(self.review.id, products[self.product.id].reviews)
        self.assertNotIn(self.review.id, users[self.buyer.id].reviews)
        
        self.assertEqual(products[self.product.id].rating_sum, 0)
        self.assertEqual(products[self.product.id].rating_count, 0)
    
    def test_8_filter_products(self):
        """Сценарий 8: Фильтрация товаров по параметрам"""
        cat2 = Category("Books")
        categories[cat2.id] = cat2
        
        p2 = Product("Python Book", "Learn Python", 49.99, self.seller.id, cat2.id, 10)
        products[p2.id] = p2
        self.seller.products.append(p2.id)
        cat2.products.append(p2.id)
        
        p3 = Product("Java Book", "Learn Java", 59.99, self.seller.id, cat2.id, 5)
        products[p3.id] = p3
        self.seller.products.append(p3.id)
        cat2.products.append(p3.id)
        
        r = self.app.get(f'/api/products?category_id={cat2.id}')
        data = json.loads(r.data)
        self.assertEqual(data['total'], 2)
        
        r = self.app.get('/api/products?min_price=50&max_price=60')
        data = json.loads(r.data)
        self.assertEqual(data['total'], 1) 
        
        r = self.app.get(f'/api/products?seller_id={self.seller.id}')
        data = json.loads(r.data)
        self.assertEqual(data['total'], 3)


if __name__ == '__main__':
    unittest.main()