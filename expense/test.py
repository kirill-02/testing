import unittest
import json
from expense import app, users, transactions, categories, User, Category, Transaction
from datetime import datetime, timedelta


class TestExpenseTracker(unittest.TestCase):
    
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True
        
        users.clear(); transactions.clear(); categories.clear()
        
        self.user = User("Test User", "test@mail.com")
        users[self.user.id] = self.user
        
        self.cat_food = Category("Food", self.user.id, 'expense')
        categories[self.cat_food.id] = self.cat_food
        
        self.cat_salary = Category("Salary", self.user.id, 'income')
        categories[self.cat_salary.id] = self.cat_salary
        
        self.t1 = Transaction(1000, 'income', self.cat_salary.id, self.user.id, "Зарплата")
        transactions[self.t1.id] = self.t1
        self.user.transactions.append(self.t1.id)
        
        self.t2 = Transaction(500, 'expense', self.cat_food.id, self.user.id, "Продукты")
        transactions[self.t2.id] = self.t2
        self.user.transactions.append(self.t2.id)
    
    def tearDown(self):
        users.clear(); transactions.clear(); categories.clear()
    
    def post(self, url, d):
        return self.app.post(url, data=json.dumps(d), content_type='application/json')
    
    def put(self, url, d):
        return self.app.put(url, data=json.dumps(d), content_type='application/json')
    
    def test_1_add_income(self):
        """Сценарий 1: Добавление дохода"""
        d = {
            'amount': 5000,
            'type': 'income',
            'category_id': self.cat_salary.id,
            'user_id': self.user.id,
            'description': 'Бонус'
        }
        r = self.post('/api/transactions', d)
        self.assertEqual(r.status_code, 201)
        data = json.loads(r.data)
        
        self.assertEqual(data['amount'], 5000)
        self.assertEqual(data['type'], 'income')
        self.assertEqual(data['description'], 'Бонус')
        self.assertIn(data['id'], transactions)
        self.assertIn(data['id'], users[self.user.id].transactions)
    
    def test_2_add_expense(self):
        """Сценарий 2: Добавление расхода"""
        d = {
            'amount': 1500,
            'type': 'expense',
            'category_id': self.cat_food.id,
            'user_id': self.user.id,
            'description': 'Ресторан'
        }
        r = self.post('/api/transactions', d)
        self.assertEqual(r.status_code, 201)
        data = json.loads(r.data)
        
        self.assertEqual(data['amount'], 1500)
        self.assertEqual(data['type'], 'expense')
        self.assertEqual(data['description'], 'Ресторан')
        self.assertIn(data['id'], transactions)
    
    def test_3_delete_transaction(self):
        """Сценарий 3: Удаление транзакции"""
        self.assertIn(self.t1.id, transactions)
        self.assertIn(self.t1.id, users[self.user.id].transactions)
        
        r = self.app.delete(f'/api/transactions/{self.t1.id}')
        self.assertEqual(r.status_code, 200)
        
        self.assertNotIn(self.t1.id, transactions)
        self.assertNotIn(self.t1.id, users[self.user.id].transactions)
    
    def test_4_stats(self):
        """Сценарий 4: Получение статистики"""
        t3 = Transaction(300, 'expense', self.cat_food.id, self.user.id, "Кофе")
        transactions[t3.id] = t3
        self.user.transactions.append(t3.id)
        
        t4 = Transaction(2000, 'income', self.cat_salary.id, self.user.id, "Премия")
        transactions[t4.id] = t4
        self.user.transactions.append(t4.id)
        
        r = self.app.get(f'/api/users/{self.user.id}/stats')
        self.assertEqual(r.status_code, 200)
        data = json.loads(r.data)
        
        self.assertEqual(data['total_income'], 3000)
        self.assertEqual(data['total_expense'], 800)
        self.assertEqual(data['balance'], 2200)
        self.assertEqual(data['transactions_count'], 4)
    
    def test_5_filter_by_type(self):
        """Сценарий 5: Фильтрация транзакций по типу"""
        t3 = Transaction(100, 'expense', self.cat_food.id, self.user.id)
        transactions[t3.id] = t3
        self.user.transactions.append(t3.id)
        
        t4 = Transaction(50, 'expense', self.cat_food.id, self.user.id)
        transactions[t4.id] = t4
        self.user.transactions.append(t4.id)
        
        r = self.app.get(f'/api/transactions?user_id={self.user.id}&type=expense')
        self.assertEqual(r.status_code, 200)
        data = json.loads(r.data)
        
        for t in data['transactions']:
            self.assertEqual(t['type'], 'expense')
    
    def test_6_category_type_mismatch(self):
        """Сценарий 6: Ошибка при несоответствии типа категории"""
        d = {
            'amount': 1000,
            'type': 'income',
            'category_id': self.cat_food.id, 
            'user_id': self.user.id
        }
        r = self.post('/api/transactions', d)
        self.assertEqual(r.status_code, 400)
        data = json.loads(r.data)
        self.assertEqual(data['msg'], 'Category type mismatch')
    
    def test_7_category_stats(self):
        """Сценарий 7: Статистика по категориям"""
        cat_transport = Category("Transport", self.user.id, 'expense')
        categories[cat_transport.id] = cat_transport
        
        t3 = Transaction(200, 'expense', cat_transport.id, self.user.id, "Такси")
        transactions[t3.id] = t3
        self.user.transactions.append(t3.id)
        
        t4 = Transaction(300, 'expense', cat_transport.id, self.user.id, "Метро")
        transactions[t4.id] = t4
        self.user.transactions.append(t4.id)
        
        t5 = Transaction(150, 'expense', self.cat_food.id, self.user.id, "Обед")
        transactions[t5.id] = t5
        self.user.transactions.append(t5.id)
        
        r = self.app.get(f'/api/users/{self.user.id}/stats')
        self.assertEqual(r.status_code, 200)
        data = json.loads(r.data)
        
        by_cat = data['by_category']
        
        self.assertIn(self.cat_food.id, by_cat)
        self.assertIn(cat_transport.id, by_cat)
        
        self.assertEqual(by_cat[self.cat_food.id]['total'], 650)
        self.assertEqual(by_cat[cat_transport.id]['total'], 500)
    
    def test_8_delete_user(self):
        """Сценарий 8: Удаление пользователя"""
        self.assertIn(self.user.id, users)
        self.assertEqual(len(transactions), 2)
        
        r = self.app.delete(f'/api/users/{self.user.id}')
        self.assertEqual(r.status_code, 200)
        
        self.assertNotIn(self.user.id, users)
        self.assertEqual(len(transactions), 0) 


if __name__ == '__main__':
    unittest.main()