from flask import Flask, request
from flask_restful import Api, Resource
from datetime import datetime
import uuid

app = Flask(__name__)
api = Api(app)

users = {}
chats = {}        
messages = {}     
memberships = {}  


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
        self.chats = []  
    
    def dict(self):
        d = super().dict()
        d.update({'username': self.username, 'email': self.email, 'chats_count': len(self.chats)})
        return d


class Chat(Base):
    def __init__(self, name, creator_id, is_private=False):
        super().__init__()
        self.name = name
        self.creator_id = creator_id
        self.is_private = is_private
        self.members = [] 
        self.messages = [] 
        self.last_message = None
    
    def dict(self):
        d = super().dict()
        d.update({
            'name': self.name,
            'creator_id': self.creator_id,
            'is_private': self.is_private,
            'members_count': len(self.members),
            'messages_count': len(self.messages),
            'last_message': self.last_message
        })
        return d


class Message(Base):
    def __init__(self, chat_id, sender_id, text):
        super().__init__()
        self.chat_id = chat_id
        self.sender_id = sender_id
        self.text = text
        self.is_read = False
        self.read_by = []  
    
    def dict(self):
        d = super().dict()
        d.update({
            'chat_id': self.chat_id,
            'sender_id': self.sender_id,
            'text': self.text,
            'is_read': self.is_read,
            'read_by': self.read_by
        })
        return d


class Membership(Base):
    def __init__(self, user_id, chat_id, role='member'):  
        super().__init__()
        self.user_id = user_id
        self.chat_id = chat_id
        self.role = role
        self.joined_at = datetime.now()
        self.last_read = None
    
    def dict(self):
        d = super().dict()
        d.update({
            'user_id': self.user_id,
            'chat_id': self.chat_id,
            'role': self.role,
            'joined_at': self.joined_at.isoformat(),
            'last_read': self.last_read.isoformat() if self.last_read else None
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
    
    def delete(self, uid):
        u = users.get(uid)
        if not u: return {'msg': 'User not found'}, 404
        
        for mid in list(memberships.keys()):
            if memberships[mid].user_id == uid:
                del memberships[mid]
        
        for cid in u.chats[:]:
            if cid in chats:
                chat = chats[cid]
                if uid in chat.members:
                    chat.members.remove(uid)
        
        del users[uid]
        return {'msg': 'User deleted'}, 200


class Chats(Resource):
    def post(self):
        d = request.get_json()
        err = check(d, ['name', 'creator_id'])
        if err: return err
        
        if d['creator_id'] not in users:
            return {'msg': 'Creator not found'}, 404
        
        c = Chat(d['name'], d['creator_id'], d.get('is_private', False))
        chats[c.id] = c
        
        c.members.append(d['creator_id'])
        users[d['creator_id']].chats.append(c.id)
        
        m = Membership(d['creator_id'], c.id, 'admin')
        memberships[m.id] = m
        
        return c.dict(), 201
    
    def get(self):
        uid = request.args.get('user_id')
        res = []
        for c in chats.values():
            if uid and uid not in c.members:
                continue
            res.append(c.dict())
        return {'chats': res, 'total': len(res)}, 200


class ChatOne(Resource):
    def get(self, cid):
        c = chats.get(cid)
        if not c: return {'msg': 'Chat not found'}, 404
        return c.dict(), 200
    
    def delete(self, cid):
        c = chats.get(cid)
        if not c: return {'msg': 'Chat not found'}, 404
        
        for mid in list(messages.keys()):
            if messages[mid].chat_id == cid:
                del messages[mid]
        
        for mid in list(memberships.keys()):
            if memberships[mid].chat_id == cid:
                del memberships[mid]
        
        for uid in c.members[:]:
            if uid in users and cid in users[uid].chats:
                users[uid].chats.remove(cid)
        
        del chats[cid]
        return {'msg': 'Chat deleted'}, 200
    
    def put(self, cid):
        c = chats.get(cid)
        if not c: return {'msg': 'Chat not found'}, 404
        
        d = request.get_json()
        if 'name' in d:
            c.name = d['name']
        return c.dict(), 200


class Messages(Resource):
    def post(self):
        d = request.get_json()
        err = check(d, ['chat_id', 'sender_id', 'text'])
        if err: return err
        
        if d['chat_id'] not in chats:
            return {'msg': 'Chat not found'}, 404
        if d['sender_id'] not in users:
            return {'msg': 'Sender not found'}, 404
        if d['sender_id'] not in chats[d['chat_id']].members:
            return {'msg': 'User not in chat'}, 400
        
        m = Message(d['chat_id'], d['sender_id'], d['text'])
        messages[m.id] = m
        
        chats[d['chat_id']].messages.append(m.id)
        chats[d['chat_id']].last_message = m.created.isoformat()
        
        return m.dict(), 201
    
    def get(self):
        chat_id = request.args.get('chat_id')
        if not chat_id:
            return {'msg': 'chat_id required'}, 400
        if chat_id not in chats:
            return {'msg': 'Chat not found'}, 404
        
        res = []
        for mid in chats[chat_id].messages:
            if mid in messages:
                res.append(messages[mid].dict())
        
        return {'messages': res, 'total': len(res)}, 200


class MessageOne(Resource):
    def get(self, mid):
        m = messages.get(mid)
        if not m: return {'msg': 'Message not found'}, 404
        return m.dict(), 200
    
    def delete(self, mid):
        m = messages.get(mid)
        if not m: return {'msg': 'Message not found'}, 404
        
        if m.chat_id in chats and mid in chats[m.chat_id].messages:
            chats[m.chat_id].messages.remove(mid)
        
        del messages[mid]
        return {'msg': 'Message deleted'}, 200
    
    def put(self, mid):
        """Отметить сообщение как прочитанное"""
        m = messages.get(mid)
        if not m: return {'msg': 'Message not found'}, 404
        
        d = request.get_json()
        user_id = d.get('user_id')
        
        if user_id and user_id not in m.read_by:
            m.read_by.append(user_id)
            m.is_read = True
        
        return m.dict(), 200


class ChatMembers(Resource):
    def post(self, cid):
        """Добавить участника в чат"""
        if cid not in chats:
            return {'msg': 'Chat not found'}, 404
        
        d = request.get_json()
        user_id = d.get('user_id')
        if not user_id:
            return {'msg': 'user_id required'}, 400
        if user_id not in users:
            return {'msg': 'User not found'}, 404
        
        chat = chats[cid]
        if user_id in chat.members:
            return {'msg': 'User already in chat'}, 400
        
        chat.members.append(user_id)
        users[user_id].chats.append(cid)
        
        m = Membership(user_id, cid, d.get('role', 'member'))
        memberships[m.id] = m
        
        return {'msg': 'User added', 'user_id': user_id}, 200
    
    def delete(self, cid):
        """Удалить участника из чата"""
        if cid not in chats:
            return {'msg': 'Chat not found'}, 404
        
        d = request.get_json()
        user_id = d.get('user_id')
        if not user_id:
            return {'msg': 'user_id required'}, 400
        
        chat = chats[cid]
        if user_id not in chat.members:
            return {'msg': 'User not in chat'}, 404
        
        chat.members.remove(user_id)
        if user_id in users and cid in users[user_id].chats:
            users[user_id].chats.remove(cid)
        
        for mid in list(memberships.keys()):
            if memberships[mid].user_id == user_id and memberships[mid].chat_id == cid:
                del memberships[mid]
        
        return {'msg': 'User removed'}, 200


api.add_resource(Users, '/api/users')
api.add_resource(UserOne, '/api/users/<string:uid>')
api.add_resource(Chats, '/api/chats')
api.add_resource(ChatOne, '/api/chats/<string:cid>')
api.add_resource(ChatMembers, '/api/chats/<string:cid>/members')
api.add_resource(Messages, '/api/messages')
api.add_resource(MessageOne, '/api/messages/<string:mid>')

if __name__ == '__main__':
    app.run(debug=True)