from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse

from posts.models import Post, Group, Follow

User = get_user_model()


class StaticViewTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='StasBasov')
        cls.user2 = User.objects.create_user(username='Stas')

        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)

        cls.authorized_client2 = Client()
        cls.authorized_client2.force_login(cls.user2)

        cls.unauthorized_client = Client()
        cls.group = Group.objects.create(title='group', slug='group',
                                         description='group')
        cls.new_post = Post.objects.create(text='text', author=cls.user,
                                           group=cls.group)

        cls.new_post_url = reverse('new_post')
        cls.edit_url = reverse('post_edit',
                               args=[cls.user, cls.new_post.id])
        cls.redirect_url = f"{reverse('login')}?next="
        cls.follow_url = reverse('profile_follow', args=[cls.user2])
        cls.unfollow_url = reverse('profile_unfollow', args=[cls.user2])
        cls.follow_index_url = reverse('follow_index')
        cls.add_comment_url = reverse('add_comment',
                                      args=[cls.user, cls.new_post.id])

    def contains_check(self, client=None, text=None, id=None):
        group_url = reverse('group_posts', args=[self.group])
        index_url = reverse('index')
        profile_url = reverse('profile', args=[self.user])
        post_url = reverse('post', args=[self.user, id])
        links = [index_url, profile_url, post_url, group_url]

        for link in links:
            response = client.get(link)
            self.assertContains(response, text)

    def test_post_check(self):
        cache.clear()
        new_post_url = reverse('new_post')
        self.authorized_client.post(new_post_url, {'text': 'text1',
                                                   'group': 1})

        self.contains_check(client=self.authorized_client, text='text1',
                            id=2)
        self.contains_check(client=self.unauthorized_client,
                            text='text1', id=2)

    def test_post_edit(self):
        cache.clear()
        self.authorized_client.post(self.edit_url, {'text': 'new_text',
                                                    'group': 1})

        self.contains_check(client=self.authorized_client,
                            text='new_text', id=1)
        self.contains_check(client=self.unauthorized_client,
                            text='new_text', id=1)

    def test_profile_check(self):
        profile_url = reverse('profile', args=[self.user])
        response_auth = self.authorized_client.get(profile_url)
        response_unauth = self.unauthorized_client.get(profile_url)
        self.assertEqual(response_auth.status_code, 200)
        self.assertEqual(response_unauth.status_code, 200)

    def test_post_edit_unauthorized(self):
        response_edit = self.unauthorized_client.post(self.edit_url, {
            'text': 'text'})

        self.assertRedirects(response_edit,
                             self.redirect_url + self.edit_url,
                             status_code=302, target_status_code=200)

    def test_post_create_unauthorized(self):
        response_new = self.unauthorized_client.post(self.new_post_url,
                                                     {'text': 'text'})
        self.assertRedirects(response_new,
                             self.redirect_url + self.new_post_url,
                             status_code=302, target_status_code=200)

    def image_contains(self, client, contains):
        index_url = reverse('index')
        group_url = reverse('group_posts', args=[self.group])
        profile_url = reverse('profile', args=[self.user])
        post_url = reverse('post', args=[self.user, self.new_post.id])
        urls = [index_url, group_url, profile_url, post_url]

        for url in urls:
            response = client.get(url)
            if contains:
                self.assertContains(response, '<img')
            else:
                self.assertNotContains(response, '<img')

    def test_img(self):
        cache.clear()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x00\x00\x00\x21'
            b'\xf9\x04\x01\x0a\x00\x01\x00\x2c\x00\x00\x00\x00\x01\x00'
            b'\x01\x00\x00\x02\x02\x4c\x01\x00\x3b'
        )
        image = SimpleUploadedFile('small.gif', small_gif,
                                   content_type='image/gif')
        self.authorized_client.post(self.edit_url,
                                    {'author': self.user,
                                     'text': 'post with image',
                                     'image': image,
                                     'group': 1})

        self.image_contains(client=self.authorized_client,
                            contains=True)
        self.image_contains(client=self.unauthorized_client,
                            contains=True)

    def test_image_error(self):
        cache.clear()
        error_message = 'Загрузите правильное изображение. ' \
                        'Файл, который вы загрузили, поврежден или ' \
                        'не является изображением.'
        with open('requirements.txt', ) as txt:
            response = self.authorized_client.post(self.edit_url,
                                                   {'author': self.user,
                                                    'text': 'text',
                                                    'image': txt,
                                                    'group': 1})
            self.assertFormError(response, 'form', 'image',
                                 error_message)

    def test_cache_index(self):
        new = reverse('new_post')
        index = reverse('index')
        self.authorized_client.get(index)
        self.authorized_client.post(new,
                                    {'author': self.user,
                                     'text': 'cache text', },
                                    )
        second_response = self.authorized_client.get(index)
        self.assertNotContains(second_response, 'cache text')
        cache.clear()
        third_response = self.authorized_client.get(index)
        self.assertContains(third_response, 'cache text')

    def test_follow(self):
        followers = self.user2.following.count()
        self.authorized_client.get(self.follow_url)
        self.assertEqual(followers + 1, self.user2.following.count())

    def test_unfollow(self):
        Follow.objects.create(user=self.user, author=self.user2)
        followers = self.user2.following.count()
        self.authorized_client.get(self.unfollow_url)
        self.assertEqual(followers - 1, self.user2.following.count())

    def test_feed_for_followers(self):
        self.authorized_client.get(self.follow_url)
        self.authorized_client2.post(self.new_post_url,
                                     {'text': 'text for followers'})
        response = self.authorized_client.get(self.follow_index_url)
        self.assertContains(response, 'text for followers')

    def test_feed_not_for_followers(self):
        self.authorized_client.post(self.new_post_url,
                                    {'text': 'text not for followers'})
        response = self.authorized_client2.get(self.follow_index_url)
        self.assertNotContains(response, 'text not for followers')

    def test_comment_create_unauthorized(self):
        response = self.unauthorized_client.post(self.add_comment_url,
                                                 {'text': 'text'})
        self.assertRedirects(response,
                             self.redirect_url + self.add_comment_url,
                             status_code=302, target_status_code=200)

    def test_comment_create_authorized(self):
        self.authorized_client.post(self.add_comment_url,
                                    {'text': 'comment for post'})
        post_url = reverse('post', args=[self.user, self.new_post.id])
        response = self.authorized_client.get(post_url)
        self.assertContains(response, 'comment for post')
