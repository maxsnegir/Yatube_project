from django.core.cache import cache
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse

from posts.models import Post, Group

User = get_user_model()


class StaticUrlTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='StasBasov')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        cls.unauthorized_client = Client()

        cls.group = Group.objects.create(title='group', slug='group',
                                         description='group')
        cls.new_post = Post.objects.create(text='text', author=cls.user,
                                           group=cls.group)

        cls.edit_url = reverse('post_edit',
                               args=[cls.user, cls.new_post.id])

    def test_homepage(self):
        response = self.unauthorized_client.get('/')
        self.assertEqual(response.status_code, 200)

    def test_force_login(self):
        response = self.authorized_client.get('/new/')
        self.assertEqual(response.status_code, 200)

    def test_new_post(self):
        current_posts_count = Post.objects.count()
        response = self.authorized_client.post('/new/',
                                               {'text': 'text'},
                                               follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Post.objects.count(), current_posts_count + 1)

    def test_unauthorized_user_newpage(self):
        response = self.unauthorized_client.get('/new/')
        self.assertRedirects(response, '/auth/login/?next=/new/',
                             status_code=302, target_status_code=200)

