from inspect import GEN_CREATED
import jwt, json

from django.db.transaction          import clean_savepoints 
from django.test                    import TestCase, Client
from django.core.files.uploadedfile import SimpleUploadedFile
from unittest.mock                  import MagicMock, patch

from django.test                    import TestCase, Client
from django.core.files.uploadedfile import SimpleUploadedFile
from unittest.mock                  import MagicMock, patch

from users.models    import User


from reviews.models  import Review
from my_settings     import SECRET_KEY, ALGORITHM
from products.models import Product, Image, Origin, Storage, Order



class PostReviewCommentTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        user1 =User.objects.create(
            name              = "백선호1", 
            kakao_account     = "123456", 
            profile_image_url ='http://k.kakaocdn.net/dn/dScJVH/btq7DShllEz/3X2kXV9W5anK3nmcitWoWk/img_640x640.jpg',
            email             = 'rhadlfrhq@naver.com',
            point             = 1000000
            )

        user2 =User.objects.create(
            id                = 200,
            name              = "백선호2", 
            kakao_account     = "1234567", 
            profile_image_url ='http://k.kakaocdn.net/dn/dScJVH/btq7DShllEz/3X2kXV9W5anK3nmcitWoWk/img_640x640.jpg',
            email             = 'rhadlfrhq@naver.com',
            point             = 1000000
            )

        origin1=Origin.objects.create(
            name = "DOMESTIC"
        )

        storage1=Storage.objects.create(
            name = "COLD"
        )   

        product1=Product.objects.create(
                id               = 200,
                name             = "product",
                price            = 10000,
                description      = 'description',
                user_id          = user2.id,
                ordered_quantity = 100,
                stock            = 1000,
                origin_id        = origin1.id,
                storage_id       = storage1.id,
        )

        product2=Product.objects.create(
                id               = 201,
                name             = "product1",
                price            = 100001,
                description      = 'description1',
                user_id          = user2.id,
                ordered_quantity = 100,
                stock            = 1000,
                origin_id        = origin1.id,
                storage_id       = storage1.id,
        )

        Order.objects.create(
            user_id    = user1.id,
            product_id = product1.id,
            quantity   = 20, 
        )

        review=Review.objects.create(
            id          = 100,
            user_id     = user2.id,
            image_url   = "image_url",
            grade       = 4,
            content     = "쓰레기장",
            product_id  = product1.id
        )

        Review.objects.create(
            user_id     = user1.id,
            content     = "쓰레기장",
            product_id  = product1.id,
            comment_id  = review.id
        )

    def tearDown(self):
        Order.objects.all().delete()
        Review.objects.all().delete()
        Origin.objects.all().delete()
        Storage.objects.all().delete()
        User.objects.all().delete()
        Product.objects.all().delete()

    @patch('products.views.boto3.client')
    def test_post_review_success(self, mocked_s3_client):
        client = Client()
        user   = User.objects.get(name='백선호1')
        token1 = jwt.encode({'id': user.id}, SECRET_KEY, algorithm=ALGORITHM)
        class MockedResponse:
            def upload(self):
                return None

        image_file = SimpleUploadedFile(
            'file.jpg',
            b'file_content',
            content_type='image/jpg'
        )

        headers = {'HTTP_AUTHORIZATION': token1, 'format': 'multipart'}
        body = {
            'image'   : image_file,
            "content" : "쏘날두",
            "grade"   : 4
            }
        
        mocked_s3_client.upload = MagicMock(return_value=MockedResponse())
        response = client.post("/reviews/200", body, **headers)
        self.assertEqual(response.status_code, 201)

    @patch('products.views.boto3.client')
    def test_post_review_key_error(self, mocked_s3_client):
        client = Client()
        user   = User.objects.get(name='백선호1')
        token1 = jwt.encode({'id': user.id}, SECRET_KEY, algorithm=ALGORITHM)
        class MockedResponse:
            def upload(self):
                return None

        image_file = SimpleUploadedFile(
            'file.jpg',
            b'file_content',
            content_type='image/jpg'
        )

        headers = {'HTTP_AUTHORIZATION': token1, 'format': 'multipart'}
        body = {
            'image'   : image_file,
            "content1" : "쏘날두",
            "grade"   : 4
            }
        
        mocked_s3_client.upload = MagicMock(return_value=MockedResponse())
        response = client.post("/reviews/200", body, **headers)
        self.assertEqual(response.status_code, 400)

    def test_post_comment_success(self):
        client = Client()
        user   = User.objects.get(name='백선호2')
        token2 = jwt.encode({'id': user.id}, SECRET_KEY, algorithm=ALGORITHM)
        header       = {"HTTP_Authorization" : token2}
        comment      = {
            'content'    : "쏘날도",
            'review_id' : 100 
        }
        response  = client.post("/reviews/200/comment", json.dumps(comment) ,content_type="application/json", **header)
        self.assertEqual(response.json(),{'MESSAGE':'SUCCESS'})
        self.assertEqual(response.status_code, 201)

    def test_post_comment_inavalid_user(self):
        client = Client()
        user   = User.objects.get(name='백선호1')
        token1 = jwt.encode({'id': user.id}, SECRET_KEY, algorithm=ALGORITHM)
        header       = {"HTTP_Authorization" : token1}
        comment      = {
            'content'    : "쏘날도",
            'review_id' : 100 
        }
        response  = client.post("/reviews/200/comment", json.dumps(comment) ,content_type="application/json", **header)
        self.assertEqual(response.json(),{'MESSAGE' : 'INVALID_USER'})
        self.assertEqual(response.status_code, 400)
    
    def test_post_comment_not_exist_review(self):
        client = Client()
        user   = User.objects.get(name='백선호2')
        token2 = jwt.encode({'id': user.id}, SECRET_KEY, algorithm=ALGORITHM)
        header       = {"HTTP_Authorization" : token2}
        comment      = {
            'content'   : "쏘날도",
            'review_id' : 100 
        }
        response  = client.post("/reviews/201/comment", json.dumps(comment) ,content_type="application/json", **header)
        self.assertEqual(response.json(),{'MESSAGE' : "NOT_EXIST_REVIEW"})
        self.assertEqual(response.status_code, 400)

    def test_post_comment_already_exist_comment(self):
        client = Client()
        user   = User.objects.get(name='백선호2')
        token2 = jwt.encode({'id': user.id}, SECRET_KEY, algorithm=ALGORITHM)
        header       = {"HTTP_Authorization" : token2}
        comment      = {
            'content'   : "쏘날도",
            'review_id' : 100 
        }
        response  = client.post("/reviews/1000/comment", json.dumps(comment) ,content_type="application/json", **header)
        self.assertEqual(response.status_code, 400)

    def test_get_review_comment_success(self):
        client = Client()
        response  = client.get("/reviews/200/comment", content_type="application/json")
        self.assertEqual(response.status_code, 200)
