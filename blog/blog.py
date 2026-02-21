from flask import Flask, request
from flask_restful import Api, Resource
from datetime import datetime
import uuid

app = Flask(__name__)
api = Api(app)

posts, comments, users = {}, {}, {}


class BaseModel:
    def __init__(self):
        self.id = str(uuid.uuid4())
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
    
    def to_dict(self):
        return {'id': self.id, 'created_at': self.created_at.isoformat(), 
                'updated_at': self.updated_at.isoformat()}


class User(BaseModel):
    def __init__(self, username, email):
        super().__init__()
        self.username = username
        self.email = email
        self.posts_count = self.comments_count = 0
    
    def to_dict(self):
        data = super().to_dict()
        data.update({'username': self.username, 'email': self.email,
                    'posts_count': self.posts_count, 'comments_count': self.comments_count})
        return data


class Post(BaseModel):
    def __init__(self, title, content, author_id):
        super().__init__()
        self.title = title
        self.content = content
        self.author_id = author_id
        self.comments_ids = []
        self.likes = 0
    
    def to_dict(self):
        data = super().to_dict()
        data.update({'title': self.title, 'content': self.content, 'author_id': self.author_id,
                    'comments_count': len(self.comments_ids), 'likes': self.likes})
        return data


class Comment(BaseModel):
    def __init__(self, content, author_id, post_id):
        super().__init__()
        self.content = content
        self.author_id = author_id
        self.post_id = post_id
    
    def to_dict(self):
        data = super().to_dict()
        data.update({'content': self.content, 'author_id': self.author_id, 'post_id': self.post_id})
        return data


def validate_request(data, required_fields):
    """Валидация запроса"""
    if not data or not all(field in data for field in required_fields):
        return {'message': f'Required fields: {", ".join(required_fields)}'}, 400
    return None


class UserListResource(Resource):
    def post(self):
        data = request.get_json()
        
        error = validate_request(data, ['username', 'email'])
        if error: return error
        
        if any(user.email == data['email'] for user in users.values()):
            return {'message': 'Email already exists'}, 400
        
        user = User(data['username'], data['email'])
        users[user.id] = user
        return user.to_dict(), 201


class PostListResource(Resource):
    def get(self):
        return {'posts': [p.to_dict() for p in posts.values()], 'total': len(posts)}, 200
    
    def post(self):
        data = request.get_json()
        
        error = validate_request(data, ['title', 'content', 'author_id'])
        if error: return error
        
        if data['author_id'] not in users:
            return {'message': 'Author not found'}, 404
        
        post = Post(data['title'], data['content'], data['author_id'])
        posts[post.id] = post
        users[data['author_id']].posts_count += 1
        return post.to_dict(), 201


class PostResource(Resource):
    def _get_post(self, post_id):
        post = posts.get(post_id)
        if not post:
            return {'message': 'Post not found'}, 404
        return post
    
    def get(self, post_id):
        post = self._get_post(post_id)
        if isinstance(post, tuple): return post
        
        post_data = post.to_dict()
        post_data['comments'] = [comments[cid].to_dict() for cid in post.comments_ids if cid in comments]
        return post_data, 200
    
    def put(self, post_id):
        post = self._get_post(post_id)
        if isinstance(post, tuple): return post
        
        data = request.get_json()
        if 'title' in data: post.title = data['title']
        if 'content' in data: post.content = data['content']
        post.updated_at = datetime.now()
        return post.to_dict(), 200
    
    def delete(self, post_id):
        post = self._get_post(post_id)
        if isinstance(post, tuple): return post
        
        for cid in post.comments_ids[:]:
            if cid in comments:
                comment = comments.pop(cid)
                if comment.author_id in users:
                    users[comment.author_id].comments_count -= 1
        
        if post.author_id in users:
            users[post.author_id].posts_count -= 1
        
        del posts[post_id]
        return {'message': 'Post deleted'}, 200


class CommentListResource(Resource):
    def post(self):
        data = request.get_json()
        
        error = validate_request(data, ['content', 'author_id', 'post_id'])
        if error: return error
        
        if data['author_id'] not in users:
            return {'message': 'Author not found'}, 404
        if data['post_id'] not in posts:
            return {'message': 'Post not found'}, 404
        
        comment = Comment(data['content'], data['author_id'], data['post_id'])
        comments[comment.id] = comment
        posts[data['post_id']].comments_ids.append(comment.id)
        users[data['author_id']].comments_count += 1
        return comment.to_dict(), 201


class CommentResource(Resource):
    def _get_comment(self, comment_id):
        comment = comments.get(comment_id)
        if not comment:
            return {'message': 'Comment not found'}, 404
        return comment
    
    def get(self, comment_id):
        comment = self._get_comment(comment_id)
        return comment.to_dict(), 200 if not isinstance(comment, tuple) else comment
    
    def put(self, comment_id):
        comment = self._get_comment(comment_id)
        if isinstance(comment, tuple): return comment
        
        data = request.get_json()
        if 'content' in data:
            comment.content = data['content']
            comment.updated_at = datetime.now()
        return comment.to_dict(), 200
    
    def delete(self, comment_id):
        comment = self._get_comment(comment_id)
        if isinstance(comment, tuple): return comment
        
        if comment.post_id in posts:
            post = posts[comment.post_id]
            if comment.id in post.comments_ids:
                post.comments_ids.remove(comment.id)
        
        if comment.author_id in users:
            users[comment.author_id].comments_count -= 1
        
        del comments[comment_id]
        return {'message': 'Comment deleted'}, 200


api.add_resource(UserListResource, '/api/users')
api.add_resource(PostListResource, '/api/posts')
api.add_resource(PostResource, '/api/posts/<string:post_id>')
api.add_resource(CommentListResource, '/api/comments')
api.add_resource(CommentResource, '/api/comments/<string:comment_id>')

if __name__ == '__main__':
    app.run(debug=True)