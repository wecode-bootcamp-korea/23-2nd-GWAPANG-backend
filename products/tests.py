import json, jwt

from django.test                    import TestCase, Client
from django.core.files.uploadedfile import SimpleUploadedFile
from unittest.mock                  import MagicMock, patch


from products.models                import Origin, Storage, Product, Image, Order
from users.models                   import User
from my_settings                    import SECRET_KEY, ALGORITHM



class SearchTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        User.objects.bulk_create([
            User(
                id = 1,
                kakao_account = 'asdf@kakao.com',
                point = 1000000,
                name = '유저1',
                profile_image = 'asdf',
                email = 'asdf@kakao.com'
            ),
            User(
                id = 2,
                kakao_account = 'zxcv@kakao.com',
                point = 2000000,
                name = '유저2',
                profile_image = 'zxcv',
                email = 'zxcv@kakao.com'
            )])

        Origin.objects.bulk_create([
            Origin(id = 1, name = 'DOMESTIC'),
            Origin(id = 2, name = 'IMPORTED')
        ])

        Storage.objects.bulk_create([
            Storage(id = 1, name = 'COLD'),
            Storage(id = 2, name = 'FROZEN'),
            Storage(id = 3, name = 'DRY')
        ])

        Product.objects.bulk_create([
            Product(
                id = 1,
                name = '상품1',
                price = 10000,
                ordered_quantity = 100,
                description = '상품1입니다',
                stock = 1000,
                origin_id = Origin.objects.get(id=1).id,
                storage_id = Storage.objects.get(id=1).id,
                user_id = User.objects.get(id=1).id
            ),
            Product(
                id = 2,
                name = '상품2',
                price = 20000,
                ordered_quantity = 200,
                description = '상품2입니다',
                stock = 2000,
                origin_id = Origin.objects.get(id=2).id,
                storage_id = Storage.objects.get(id=3).id,
                user_id = User.objects.get(id=2).id
            )])

        Image.objects.bulk_create([
            Image(
                id = 1,
                url = 'aaaa',
                is_thumbnail=True,
                product_id = Product.objects.get(id=1).id
            ),
            Image(
                id = 2,
                url = 'ssss',
                is_thumbnail=False,
                product_id = Product.objects.get(id=1).id
            ),
            Image(
                id = 3,
                url = 'dddd',
                is_thumbnail=False,
                product_id = Product.objects.get(id=1).id
            ),
            Image(
                id = 4,
                url = 'ffff',
                is_thumbnail=True,
                product_id = Product.objects.get(id=2).id
            )])

    def tearDown(self):
        User.objects.all().delete()
        Origin.objects.all().delete()
        Storage.objects.all().delete()
        Product.objects.all().delete()
        Image.objects.all().delete()

    def test_search_get_empty_success(self):
        client = Client()
        response = client.get('/products/search')
        self.assertEqual(response.json(),
                {
                    "seller" : [],
                    "item"   : []
                }
        )
        self.assertEqual(response.status_code, 200)

    def test_search_get_success(self):
        self.maxDiff = None
        client = Client()
        response = client.get('/products/search?keyword=2')

        self.assertEqual(response.json(),
                {
                    "seller" : [{
                        "id"            : 2,
                        "kakao_account" : "zxcv@kakao.com",
                        "name"          : "유저2",
                        "profile_image" : "zxcv",
                    }],
                    "item" : [{
                        "id"    : 2,
                        "name"  : "상품2",
                        "price" : "20000.00",
                        "stock" : 2000,
                        "image" : "ffff"
                    }]
                }
        )
        self.assertEqual(response.status_code, 200)


class UploadTest(TestCase):
    def setUp(self):
        
        user1 =User.objects.create(
            name              = "백선호1", 
            kakao_account     = "123456", 
            profile_image_url ='http://k.kakaocdn.net/dn/dScJVH/btq7DShllEz/3X2kXV9W5anK3nmcitWoWk/img_640x640.jpg',
            email             = 'rhadlfrhq@naver.com',
            point             = 1000000
            )

        user2 =User.objects.create(
            name              = "백선호2", 
            kakao_account     = "123456", 
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
     
        Product.objects.create(
                id               = 200,
                name             = "product",
                price            = 10000,
                description      = 'description',
                user_id          = user1.id,
                ordered_quantity = 100,
                stock            = 1000,
                origin_id        = origin1.id,
                storage_id       = storage1.id,
        )

        Product.objects.bulk_create(
            [Product(
                id               = 300+i,
                name             = "product",
                price            = 10000,
                description      = 'description',
                user_id          = user2.id,
                ordered_quantity = 100,
                stock            = 1000,
                origin_id        = origin1.id,
                storage_id       = storage1.id,
            ) for i in range(4)]
        )

    def tearDown(self):
        Origin.objects.all().delete()
        Storage.objects.all().delete()
        User.objects.all().delete()
        Product.objects.all().delete()
    
    @patch('products.views.boto3.client')
    def test_upload_success(self, mocked_s3_client):
        client            = Client()
        user              = User.objects.get(name="백선호1")
        access_token      = jwt.encode({"id" : user.id}, key=SECRET_KEY, algorithm=ALGORITHM)

        class MockedResponse:
            def upload(self):
                return None
        
        image_file = SimpleUploadedFile(
            'file.jpg',
            b'file_content',
            content_type='image/jpg'
        )
        
        headers = {'HTTP_AUTHORIZATION': access_token, 'format': 'multipart'}
        origin=Origin.objects.get(name="DOMESTIC")
        storage=Storage.objects.get(name="COLD")
        
        body = {
            'images'      : image_file,
            "name"        : "망고",
            "price"       : 12000,
            "description" : "안녕하세요",
            "stock"       : 50,
            "origin"      : origin.id,
            "storage"     : storage.id
            }
        
        mocked_s3_client.upload = MagicMock(return_value=MockedResponse())
        response = client.post("/products/upload", body, **headers)
        self.assertEqual(response.status_code, 201)
    
    @patch('products.views.boto3.client')
    def test_empty_image(self, mocked_s3_client):
        client            = Client()
        user              = User.objects.get(name="백선호1")
        access_token      = jwt.encode({"id" : user.id}, key=SECRET_KEY, algorithm=ALGORITHM)

        class MockedResponse:
            def upload(self):
                return None
        
        image_file = SimpleUploadedFile(
            'file.jpg',
            b'file_content',
            content_type='image/jpg'
        )
        
        headers = {'HTTP_AUTHORIZATION': access_token, 'format': 'multipart'}
        origin=Origin.objects.get(name="DOMESTIC")
        storage=Storage.objects.get(name="COLD")
        
        body = {
            'images'      : '',
            "name"        : "망고",
            "price"       : 12000,
            "description" : "안녕하세요",
            "stock"       : 50,
            "origin"      : origin.id,
            "storage"     : storage.id
            }
        
        mocked_s3_client.upload = MagicMock(return_value=MockedResponse())
        response = client.post("/products/upload", body, **headers)
        self.assertEqual(response.status_code, 404)

    @patch('products.views.boto3.client')
    def test_upload_full(self, mocked_s3_client):
        client            = Client()
        user              = User.objects.get(name="백선호2")
        access_token      = jwt.encode({"id" : user.id}, key=SECRET_KEY, algorithm=ALGORITHM)

        class MockedResponse:
            def upload(self):
                return None
        
        image_file = SimpleUploadedFile(
            'file.jpg',
            b'file_content',
            content_type='image/jpg'
        )
        
        headers = {'HTTP_AUTHORIZATION': access_token, 'format': 'multipart'}
        origin=Origin.objects.get(name="DOMESTIC")
        storage=Storage.objects.get(name="COLD")
        
        body = {
            'images'      : image_file,
            "name"        : "망고",
            "price"       : 12000,
            "description" : "안녕하세요",
            "stock"       : 50,
            "origin"      : origin.id,
            "storage"     : storage.id
            }
        
        mocked_s3_client.upload = MagicMock(return_value=MockedResponse())
        response = client.post("/products/upload", body, **headers)
        self.assertEqual(response.status_code, 400)

    @patch('products.views.boto3.client')
    def test_product_delete(self, mocked_s3_client):
        client            = Client()
        user              = User.objects.get(name="백선호1")
        access_token      = jwt.encode({"id" : user.id}, key=SECRET_KEY, algorithm=ALGORITHM)

        class MockedResponse:
            def upload(self):
                return None
        
        image_file = SimpleUploadedFile(
            'file.jpg',
            b'file_content',
            content_type='image/jpg'
        )
        
        headers = {'HTTP_AUTHORIZATION': access_token, 'format': 'multipart'}
        
        mocked_s3_client.upload = MagicMock(return_value=MockedResponse())
        response = client.delete("/products/upload?product_id=200", **headers)
        self.assertEqual(response.status_code, 204)


class ProductUpdateTest(TestCase):
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
            name              = "백선호2", 
            kakao_account     = "123456", 
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
     
        Product.objects.create(
                id               = 200,
                name             = "product",
                price            = 10000,
                description      = 'description',
                user_id          = user1.id,
                ordered_quantity = 100,
                stock            = 1000,
                origin_id        = origin1.id,
                storage_id       = storage1.id,
        )

        Product.objects.bulk_create(
            [Product(
                id               = 300+i,
                name             = "product",
                price            = 10000,
                description      = 'description',
                user_id          = user2.id,
                ordered_quantity = 100,
                stock            = 1000,
                origin_id        = origin1.id,
                storage_id       = storage1.id,
            ) for i in range(4)]
        )

    def tearDown(self):
        Origin.objects.all().delete()
        Storage.objects.all().delete()
        User.objects.all().delete()
        Product.objects.all().delete()
    
    @patch('products.views.boto3.client')
    def test_update_success(self, mocked_s3_client):
        client            = Client()
        user              = User.objects.get(name="백선호1")
        access_token      = jwt.encode({"id" : user.id}, key=SECRET_KEY, algorithm=ALGORITHM)

        class MockedResponse:
            def upload(self):
                return None
        
        image_file = SimpleUploadedFile(
            'file.jpg',
            b'file_content',
            content_type='image/jpg'
        )
        
        headers = {'HTTP_AUTHORIZATION': access_token, 'format': 'multipart'}
        origin=Origin.objects.get(name="DOMESTIC")
        storage=Storage.objects.get(name="COLD")
        
        body = {
            'images'      : image_file,
            "name"        : "망고",
            "price"       : 12000,
            "description" : "안녕하세요",
            "stock"       : 50,
            "origin"      : origin.id,
            "storage"     : storage.id
            }
        
        mocked_s3_client.upload = MagicMock(return_value=MockedResponse())
        response = client.post("/products/200/update", body, **headers)
        self.assertEqual(response.status_code, 201)

    @patch('products.views.boto3.client')
    def test_empty_image(self, mocked_s3_client):
        client            = Client()
        user              = User.objects.get(name="백선호1")
        access_token      = jwt.encode({"id" : user.id}, key=SECRET_KEY, algorithm=ALGORITHM)

        class MockedResponse:
            def upload(self):
                return None
        
        image_file = SimpleUploadedFile(
            'file.jpg',
            b'file_content',
            content_type='image/jpg'
        )
        
        headers = {'HTTP_AUTHORIZATION': access_token, 'format': 'multipart'}
        origin=Origin.objects.get(name="DOMESTIC")
        storage=Storage.objects.get(name="COLD")
        
        body = {
            'images'      : '',
            "name"        : "망고",
            "price"       : 12000,
            "description" : "안녕하세요",
            "stock"       : 50,
            "origin"      : origin.id,
            "storage"     : storage.id
            }
        
        mocked_s3_client.upload = MagicMock(return_value=MockedResponse())
        response = client.post("/products/200/update", body, **headers)
        self.assertEqual(response.status_code, 404)

    def test_product_get_success(self):
        client       = Client()
        user         = User.objects.get(name="백선호1")
        access_token = jwt.encode({"id" : user.id}, key=SECRET_KEY, algorithm=ALGORITHM)
        headers      = {'HTTP_AUTHORIZATION': access_token}
        response     = client.get("/products/200/update", content_type="application/json", **headers)
        self.assertEqual(response.status_code, 200)

    def test_product_no_product(self):
        client       = Client()
        user         = User.objects.get(name="백선호1")
        access_token = jwt.encode({"id" : user.id}, key=SECRET_KEY, algorithm=ALGORITHM)
        headers      = {'HTTP_AUTHORIZATION': access_token}
        response     = client.get("/products/333/update", content_type="application/json", **headers)
        self.assertEqual(response.status_code, 400)