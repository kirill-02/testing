from flask import Flask, request
from flask_restful import Api, Resource
from datetime import datetime, timedelta
import uuid

app = Flask(__name__)
api = Api(app)

users = {}
events = {}
notifications = {}


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
        self.events = []
    
    def dict(self):
        d = super().dict()
        d.update({'name': self.name, 'email': self.email, 'events_count': len(self.events)})
        return d


class Event(Base):
    def __init__(self, title, dt, user_id, desc='', remind=30):
        super().__init__()
        self.title = title
        self.desc = desc
        self.dt = dt
        self.user_id = user_id
        self.remind = remind
        self.notified = False
    
    def dict(self):
        d = super().dict()
        d.update({
            'title': self.title,
            'desc': self.desc,
            'dt': self.dt.isoformat(),
            'user_id': self.user_id,
            'remind': self.remind,
            'notified': self.notified
        })
        return d
    
    def need_notify(self):
        if self.notified:
            return False
        now = datetime.now()
        notify_time = self.dt - timedelta(minutes=self.remind)
        return now >= notify_time and now < self.dt


class Notification(Base):
    def __init__(self, user_id, event_id, message):
        super().__init__()
        self.user_id = user_id
        self.event_id = event_id
        self.message = message
        self.is_read = False
    
    def dict(self):
        d = super().dict()
        d.update({
            'user_id': self.user_id,
            'event_id': self.event_id,
            'message': self.message,
            'is_read': self.is_read
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
        if not u: return {'msg': 'User not found'}, 404
        return u.dict(), 200


class Events(Resource):
    def post(self):
        d = request.get_json()
        err = check(d, ['title', 'dt', 'user_id'])
        if err: return err
        
        if d['user_id'] not in users:
            return {'msg': 'User not found'}, 404
        
        try:
            dt = datetime.fromisoformat(d['dt'])
        except:
            return {'msg': 'Invalid date'}, 400
        
        e = Event(
            d['title'],
            dt,
            d['user_id'],
            d.get('desc', ''),
            d.get('remind', 30)
        )
        events[e.id] = e
        users[d['user_id']].events.append(e.id)
        
        return e.dict(), 201
    
    def get(self):
        user_id = request.args.get('user_id')
        upcoming = request.args.get('upcoming', 'false').lower() == 'true'
        
        res = []
        for e in events.values():
            if user_id and e.user_id != user_id:
                continue
            if upcoming and datetime.now() >= e.dt:
                continue
            res.append(e.dict())
        
        return {'events': res, 'total': len(res)}, 200


class EventOne(Resource):
    def get(self, eid):
        e = events.get(eid)
        if not e: return {'msg': 'Event not found'}, 404
        return e.dict(), 200
    
    def put(self, eid):
        e = events.get(eid)
        if not e: return {'msg': 'Event not found'}, 404
        
        d = request.get_json()
        if 'title' in d:
            e.title = d['title']
        if 'desc' in d:
            e.desc = d['desc']
        if 'dt' in d:
            try:
                e.dt = datetime.fromisoformat(d['dt'])
            except:
                return {'msg': 'Invalid date'}, 400
        if 'remind' in d:
            e.remind = d['remind']
        
        e.notified = False  
        return e.dict(), 200
    
    def delete(self, eid):
        e = events.get(eid)
        if not e: return {'msg': 'Event not found'}, 404
        
        if e.user_id in users and eid in users[e.user_id].events:
            users[e.user_id].events.remove(eid)
        
        del events[eid]
        return {'msg': 'Event deleted'}, 200


class Notifications(Resource):
    def get(self):
        user_id = request.args.get('user_id')
        unread = request.args.get('unread', 'false').lower() == 'true'
        
        res = []
        for n in notifications.values():
            if user_id and n.user_id != user_id:
                continue
            if unread and n.is_read:
                continue
            res.append(n.dict())
        
        return {'notifications': res, 'total': len(res)}, 200
    
    def post(self):
        """Проверить и создать уведомления"""
        created = []
        for e in events.values():
            if e.need_notify():
                msg = f"Reminder: '{e.title}' in {e.remind} min"
                n = Notification(e.user_id, e.id, msg)
                notifications[n.id] = n
                e.notified = True
                created.append(n.dict())
        
        return {'created': created, 'count': len(created)}, 200


class NotificationOne(Resource):
    def put(self, nid):
        n = notifications.get(nid)
        if not n: return {'msg': 'Not found'}, 404
        n.is_read = True
        return n.dict(), 200
    
    def delete(self, nid):
        n = notifications.get(nid)
        if not n: return {'msg': 'Not found'}, 404
        del notifications[nid]
        return {'msg': 'Notification deleted'}, 200


api.add_resource(Users, '/api/users')
api.add_resource(UserOne, '/api/users/<string:uid>')
api.add_resource(Events, '/api/events')
api.add_resource(EventOne, '/api/events/<string:eid>')
api.add_resource(Notifications, '/api/notifications')
api.add_resource(NotificationOne, '/api/notifications/<string:nid>')

if __name__ == '__main__':
    app.run(debug=True)