from django.test   import Client, TestCase
from unittest.mock import patch, MagicMock

from users.models  import User



class KakaoSignInTest(TestCase):

    def setUp(self):
        User.objects.create(
            name="지선", 
            kakao_account=1855324271, 
            profile_image_url='http://k.kakaocdn.net/dn/dScJVH/btq7DShllEz/3X2kXV9W5anK3nmcitWoWk/img_640x640.jpg',
            email='rhadlfrhq@naver.com'
            )

    def tearDown(self):
        User.objects.all().delete() 

    @patch('users.views.requests')
    def test_kakao_sign_in(self, mocked_request):
        class FakeResponse:
            def json(self):
                return {
    'id': 1855324271, 'connected_at': '2021-08-19T07:55:45Z', 
'    properties': {
        '        nickname': '지선',
                'profile_image': 'http://k.kakaocdn.net/dn/dScJVH/btq7DShllEz/3X2kXV9W5anK3nmcitWoWk/img_640x640.jpg',
                'thumbnail_image': 'http://k.kakaocdn.net/dn/dScJVH/btq7DShllEz/3X2kXV9W5anK3nmcitWoWk/img_110x110.jpg'
                }, 
                'kakao_account': {
                    'profile_nickname_needs_agreement': False,
                    'profile_image_needs_agreement': False, 
                    'profile' : {
                        'nickname': '지선',
                        'thumbnail_image_url': 'http://k.kakaocdn.net/dn/dScJVH/btq7DShllEz/3X2kXV9W5anK3nmcitWoWk/img_110x110.jpg',
                        'profile_image_url': 'http://k.kakaocdn.net/dn/dScJVH/btq7DShllEz/3X2kXV9W5anK3nmcitWoWk/img_640x640.jpg',
                        'is_default_image': False}, 
                            'has_email': True,
                            'email_needs_agreement': False,
                            'is_email_valid': True,
                            'is_email_verified': True,
                            'email': 'rhadlfrhq@naver.com'}
}      

        mocked_request.get = MagicMock(return_value = FakeResponse())
        c = Client()
        header   = {'HTTP_Authorization':'fake_token.1234'}
        response = c.get('/users/login/kakao', content_type='applications/json', **header)
        self.assertEqual(response.status_code, 200)