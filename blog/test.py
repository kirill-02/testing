import unittest
import json
from blog import app, users, posts, comments, User, Post, Comment


class BlogAPITestCase(unittest.TestCase):
    
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True
        
        users.clear()
        posts.clear()
        comments.clear()
        
        self.test_user = User("testuser", "test@example.com")
        users[self.test_user.id] = self.test_user
        
        self.test_post = Post("Test Post", "Test Content", self.test_user.id)
        posts[self.test_post.id] = self.test_post
        self.test_user.posts_count = 1
        
        self.test_comment = Comment("Test Comment", self.test_user.id, self.test_post.id)
        comments[self.test_comment.id] = self.test_comment
        self.test_post.comments_ids.append(self.test_comment.id)
        self.test_user.comments_count = 1
    
    def tearDown(self):
        users.clear()
        posts.clear()
        comments.clear()
    
    def _post_json(self, url, data):
        return self.app.post(url, data=json.dumps(data), content_type='application/json')
    
    def _put_json(self, url, data):
        return self.app.put(url, data=json.dumps(data), content_type='application/json')
    
    def test_1_create_post(self):
        new_user = User("creator", "creator@example.com")
        users[new_user.id] = new_user
        
        post_data = {
            'title': 'New Test Post',
            'content': 'This is a test post content',
            'author_id': new_user.id
        }
        
        response = self._post_json('/api/posts', post_data)
        self.assertEqual(response.status_code, 201)
        
        data = json.loads(response.data)
        self.assertEqual(data['title'], post_data['title'])
        self.assertEqual(data['content'], post_data['content'])
        self.assertIn(data['id'], posts)
        self.assertEqual(users[new_user.id].posts_count, 1)
    
    def test_2_edit_post(self):
        update_data = {'title': 'Updated Title', 'content': 'Updated Content'}
        response = self._put_json(f'/api/posts/{self.test_post.id}', update_data)
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['title'], update_data['title'])
        self.assertEqual(data['content'], update_data['content'])
        self.assertNotEqual(data['updated_at'], data['created_at'])
    
    def test_3_delete_post_with_comments(self):
        self.assertIn(self.test_post.id, posts)
        self.assertIn(self.test_comment.id, comments)
        
        response = self.app.delete(f'/api/posts/{self.test_post.id}')
        self.assertEqual(response.status_code, 200)
        
        self.assertNotIn(self.test_post.id, posts)
        self.assertNotIn(self.test_comment.id, comments)
        self.assertEqual(users[self.test_user.id].posts_count, 0)
        self.assertEqual(users[self.test_user.id].comments_count, 0)
    
    def test_4_create_comment(self):
        commenter = User("commenter", "commenter@example.com")
        users[commenter.id] = commenter
        
        comment_data = {
            'content': 'New comment',
            'author_id': commenter.id,
            'post_id': self.test_post.id
        }
        
        response = self._post_json('/api/comments', comment_data)
        self.assertEqual(response.status_code, 201)
        
        data = json.loads(response.data)
        self.assertEqual(data['content'], comment_data['content'])
        self.assertIn(data['id'], comments)
        self.assertIn(data['id'], posts[self.test_post.id].comments_ids)
        self.assertEqual(users[commenter.id].comments_count, 1)
    
    def test_5_edit_comment(self):
        update_data = {'content': 'Updated comment'}
        response = self._put_json(f'/api/comments/{self.test_comment.id}', update_data)
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['content'], update_data['content'])
        self.assertNotEqual(data['updated_at'], data['created_at'])
    
    def test_6_delete_comment(self):
        self.assertIn(self.test_comment.id, comments)
        self.assertIn(self.test_comment.id, posts[self.test_post.id].comments_ids)
        
        response = self.app.delete(f'/api/comments/{self.test_comment.id}')
        self.assertEqual(response.status_code, 200)
        
        self.assertNotIn(self.test_comment.id, comments)
        self.assertNotIn(self.test_comment.id, posts[self.test_post.id].comments_ids)
        self.assertEqual(users[self.test_user.id].comments_count, 0)
    
    def test_7_get_post_with_comments(self):
        another = Comment("Another", self.test_user.id, self.test_post.id)
        comments[another.id] = another
        self.test_post.comments_ids.append(another.id)
        
        response = self.app.get(f'/api/posts/{self.test_post.id}')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertEqual(len(data['comments']), 2)
        self.assertIn(self.test_comment.content, [c['content'] for c in data['comments']])
    
    def test_8_error_handling(self):
        response = self.app.get('/api/posts/nonexistent')
        self.assertEqual(response.status_code, 404)
        
        response = self._post_json('/api/posts', {'title': 'Only Title'})
        self.assertEqual(response.status_code, 400)


if __name__ == '__main__':
    unittest.main()