import unittest
import json
from calendar import app, users, events, notifications, User, Event, Notification
from datetime import datetime, timedelta


class TestCalendar(unittest.TestCase):
    
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True
        
        users.clear(); events.clear(); notifications.clear()
        
        self.user = User("Test User", "test@mail.com")
        users[self.user.id] = self.user
        
        future = datetime.now() + timedelta(hours=2)
        self.event = Event("Test Event", future, self.user.id, "Description", 30)
        events[self.event.id] = self.event
        self.user.events.append(self.event.id)
    
    def tearDown(self):
        users.clear(); events.clear(); notifications.clear()
    
    def post(self, url, d):
        return self.app.post(url, data=json.dumps(d), content_type='application/json')
    
    def put(self, url, d):
        return self.app.put(url, data=json.dumps(d), content_type='application/json')
    
    def test_1_create_event(self):
        future = (datetime.now() + timedelta(days=1)).isoformat()
        d = {
            'title': 'Meeting',
            'desc': 'Project discussion',
            'dt': future,
            'user_id': self.user.id,
            'remind': 15
        }
        r = self.post('/api/events', d)
        self.assertEqual(r.status_code, 201)
        data = json.loads(r.data)
        
        self.assertEqual(data['title'], 'Meeting')
        self.assertEqual(data['desc'], 'Project discussion')
        self.assertEqual(data['remind'], 15)
        self.assertFalse(data['notified'])
        
        self.assertIn(data['id'], events)
        self.assertIn(data['id'], users[self.user.id].events)
    
    def test_2_get_event(self):
        r = self.app.get(f'/api/events/{self.event.id}')
        self.assertEqual(r.status_code, 200)
        data = json.loads(r.data)
        
        self.assertEqual(data['title'], 'Test Event')
        self.assertEqual(data['desc'], 'Description')
        self.assertEqual(data['remind'], 30)
    
    def test_3_edit_event(self):
        new_time = (datetime.now() + timedelta(days=2)).isoformat()
        d = {
            'title': 'Updated Event',
            'remind': 45,
            'dt': new_time
        }
        r = self.put(f'/api/events/{self.event.id}', d)
        self.assertEqual(r.status_code, 200)
        data = json.loads(r.data)
        
        self.assertEqual(data['title'], 'Updated Event')
        self.assertEqual(data['remind'], 45)
        self.assertFalse(data['notified']) 
    
    def test_4_delete_event(self):
        self.assertIn(self.event.id, events)
        self.assertIn(self.event.id, users[self.user.id].events)
        
        r = self.app.delete(f'/api/events/{self.event.id}')
        self.assertEqual(r.status_code, 200)
        data = json.loads(r.data)
        self.assertEqual(data['msg'], 'Event deleted')
        
        self.assertNotIn(self.event.id, events)
        self.assertNotIn(self.event.id, users[self.user.id].events)
    
    def test_5_upcoming_events(self):
        past = datetime.now() - timedelta(days=1)
        past_event = Event("Past Event", past, self.user.id)
        events[past_event.id] = past_event
        self.user.events.append(past_event.id)
        
        future = datetime.now() + timedelta(days=1)
        future_event = Event("Future Event", future, self.user.id)
        events[future_event.id] = future_event
        self.user.events.append(future_event.id)
        
        r = self.app.get(f'/api/events?user_id={self.user.id}&upcoming=true')
        data = json.loads(r.data)
        
        self.assertEqual(data['total'], 2) 
        titles = [e['title'] for e in data['events']]
        self.assertIn('Future Event', titles)
        self.assertIn('Test Event', titles)
        self.assertNotIn('Past Event', titles)
    
def test_6_notification_logic(self):
    events.clear()
    self.user.events.clear()
    
    past_time = datetime.now() - timedelta(minutes=10)
    event1 = Event(
        "Past Event", 
        past_time, 
        self.user.id, 
        remind=5  
    )
    events[event1.id] = event1
    self.user.events.append(event1.id)
    
    now_time = datetime.now() + timedelta(seconds=1)
    event2 = Event(
        "Now Event", 
        now_time, 
        self.user.id, 
        remind=0  
    )
    events[event2.id] = event2
    self.user.events.append(event2.id)
    
    self.assertTrue(event1.need_notify(), "Event1 should need notification")
    self.assertTrue(event2.need_notify(), "Event2 should need notification")
    
    r = self.post('/api/notifications', {})
    self.assertEqual(r.status_code, 200)
    data = json.loads(r.data)
    
    self.assertEqual(data['count'], 2)
    self.assertEqual(len(notifications), 2)
    
    self.assertTrue(events[event1.id].notified)
    self.assertTrue(events[event2.id].notified)
    
    r2 = self.post('/api/notifications', {})
    data2 = json.loads(r2.data)
    self.assertEqual(data2['count'], 0)

    def test_7_get_user_notifications(self):
        """Сценарий 7: Получение уведомлений пользователя"""
        n1 = Notification(self.user.id, self.event.id, "Reminder 1")
        n2 = Notification(self.user.id, self.event.id, "Reminder 2")
        notifications[n1.id] = n1
        notifications[n2.id] = n2
        
        r = self.app.get(f'/api/notifications?user_id={self.user.id}')
        data = json.loads(r.data)
        self.assertEqual(data['total'], 2)
        
        n2.is_read = True
        
        r2 = self.app.get(f'/api/notifications?user_id={self.user.id}&unread=true')
        data2 = json.loads(r2.data)
        self.assertEqual(data2['total'], 1)
    
    def test_8_mark_notification_read(self):
        """Сценарий 8: Отметка уведомления как прочитанного"""
        n = Notification(self.user.id, self.event.id, "Test")
        notifications[n.id] = n
        self.assertFalse(n.is_read)
        
        r = self.put(f'/api/notifications/{n.id}', {})
        self.assertEqual(r.status_code, 200)
        data = json.loads(r.data)
        
        self.assertTrue(data['is_read'])
        self.assertTrue(notifications[n.id].is_read)


if __name__ == '__main__':
    unittest.main()