import unittest
import json
from chat import app, users, chats, messages, memberships, User, Chat, Message, Membership
from datetime import datetime, timedelta


class TestChatApp(unittest.TestCase):
    
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True
        
        users.clear(); chats.clear(); messages.clear(); memberships.clear()
        
        self.user1 = User("Alice", "alice@mail.com")
        users[self.user1.id] = self.user1
        
        self.user2 = User("Bob", "bob@mail.com")
        users[self.user2.id] = self.user2
        
        self.user3 = User("Charlie", "charlie@mail.com")
        users[self.user3.id] = self.user3
        
        self.chat = Chat("General", self.user1.id)
        chats[self.chat.id] = self.chat
        self.chat.members = [self.user1.id, self.user2.id]
        self.user1.chats.append(self.chat.id)
        self.user2.chats.append(self.chat.id)
        
        self.m1 = Membership(self.user1.id, self.chat.id, 'admin')
        memberships[self.m1.id] = self.m1
        self.m2 = Membership(self.user2.id, self.chat.id, 'member')
        memberships[self.m2.id] = self.m2
        
        self.msg1 = Message(self.chat.id, self.user1.id, "Hello everyone!")
        messages[self.msg1.id] = self.msg1
        self.chat.messages.append(self.msg1.id)
        
        self.msg2 = Message(self.chat.id, self.user2.id, "Hi Alice!")
        messages[self.msg2.id] = self.msg2
        self.chat.messages.append(self.msg2.id)
        self.chat.last_message = self.msg2.created.isoformat()
    
    def tearDown(self):
        users.clear(); chats.clear(); messages.clear(); memberships.clear()
    
    def post(self, url, d):
        return self.app.post(url, data=json.dumps(d), content_type='application/json')
    
    def put(self, url, d):
        return self.app.put(url, data=json.dumps(d), content_type='application/json')
    
    def test_1_create_chat(self):
        """Сценарий 1: Создание нового чата"""
        d = {
            'name': 'Work Chat',
            'creator_id': self.user1.id,
            'is_private': False
        }
        r = self.post('/api/chats', d)
        self.assertEqual(r.status_code, 201)
        data = json.loads(r.data)
        
        self.assertEqual(data['name'], 'Work Chat')
        self.assertEqual(data['creator_id'], self.user1.id)
        self.assertEqual(data['members_count'], 1)
        self.assertEqual(data['messages_count'], 0)
        
        self.assertIn(data['id'], chats)
        self.assertIn(data['id'], users[self.user1.id].chats)
        self.assertIn(self.user1.id, chats[data['id']].members)
    
    def test_2_send_message(self):
        """Сценарий 2: Отправка сообщения в чат"""
        d = {
            'chat_id': self.chat.id,
            'sender_id': self.user1.id,
            'text': 'New message from Alice'
        }
        r = self.post('/api/messages', d)
        self.assertEqual(r.status_code, 201)
        data = json.loads(r.data)
        
        self.assertEqual(data['text'], 'New message from Alice')
        self.assertEqual(data['sender_id'], self.user1.id)
        self.assertEqual(data['chat_id'], self.chat.id)
        self.assertFalse(data['is_read'])
        
        self.assertIn(data['id'], chats[self.chat.id].messages)
        self.assertIsNotNone(chats[self.chat.id].last_message)
    
    def test_3_get_messages(self):
        """Сценарий 3: Получение всех сообщений чата"""
        r = self.app.get(f'/api/messages?chat_id={self.chat.id}')
        self.assertEqual(r.status_code, 200)
        data = json.loads(r.data)
        
        self.assertEqual(data['total'], 2)
        texts = [m['text'] for m in data['messages']]
        self.assertIn('Hello everyone!', texts)
        self.assertIn('Hi Alice!', texts)
    
    def test_4_add_member(self):
        """Сценарий 4: Добавление нового участника в чат"""
        self.assertNotIn(self.user3.id, self.chat.members)
        
        d = {'user_id': self.user3.id, 'role': 'member'}
        r = self.post(f'/api/chats/{self.chat.id}/members', d)
        self.assertEqual(r.status_code, 200)
        
        self.assertIn(self.user3.id, chats[self.chat.id].members)
        self.assertIn(self.chat.id, users[self.user3.id].chats)
        
        membership_exists = False
        for m in memberships.values():
            if m.user_id == self.user3.id and m.chat_id == self.chat.id:
                membership_exists = True
                break
        self.assertTrue(membership_exists)
    
    def test_5_remove_member(self):
        """Сценарий 5: Удаление участника из чата"""
        self.assertIn(self.user2.id, self.chat.members)
        
        d = {'user_id': self.user2.id}
        r = self.app.delete(f'/api/chats/{self.chat.id}/members', 
                           data=json.dumps(d), 
                           content_type='application/json')
        self.assertEqual(r.status_code, 200)
        
        self.assertNotIn(self.user2.id, chats[self.chat.id].members)
        self.assertNotIn(self.chat.id, users[self.user2.id].chats)
        
        for m in memberships.values():
            self.assertFalse(m.user_id == self.user2.id and m.chat_id == self.chat.id)
    
    def test_6_mark_as_read(self):
        """Сценарий 6: Отметка сообщения как прочитанного"""
        msg_id = self.msg1.id
        self.assertFalse(messages[msg_id].is_read)
        self.assertEqual(len(messages[msg_id].read_by), 0)
        
        d = {'user_id': self.user2.id}
        r = self.put(f'/api/messages/{msg_id}', d)
        self.assertEqual(r.status_code, 200)
        data = json.loads(r.data)
        
        self.assertTrue(data['is_read'])
        self.assertIn(self.user2.id, data['read_by'])
        self.assertIn(self.user2.id, messages[msg_id].read_by)
    
    def test_7_delete_message(self):
        """Сценарий 7: Удаление сообщения"""
        msg_id = self.msg1.id
        self.assertIn(msg_id, messages)
        self.assertIn(msg_id, chats[self.chat.id].messages)
        
        r = self.app.delete(f'/api/messages/{msg_id}')
        self.assertEqual(r.status_code, 200)
        
        self.assertNotIn(msg_id, messages)
        self.assertNotIn(msg_id, chats[self.chat.id].messages)
    
    def test_8_delete_chat(self):
        """Сценарий 8: Удаление чата"""
        chat_id = self.chat.id
        self.assertIn(chat_id, chats)
        self.assertEqual(len(messages), 2) 
        self.assertEqual(len(memberships), 2) 
        
        r = self.app.delete(f'/api/chats/{chat_id}')
        self.assertEqual(r.status_code, 200)
        
        self.assertNotIn(chat_id, chats)
        
        self.assertEqual(len(messages), 0)
        
        self.assertEqual(len(memberships), 0)
        
        self.assertNotIn(chat_id, users[self.user1.id].chats)
        self.assertNotIn(chat_id, users[self.user2.id].chats)


if __name__ == '__main__':
    unittest.main()