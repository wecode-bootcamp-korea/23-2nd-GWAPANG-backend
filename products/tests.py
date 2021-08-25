import json, jwt

from django.test                    import TestCase, Client
from django.core.files.uploadedfile import SimpleUploadedFile
from unittest.mock                  import MagicMock, patch

from reviews.models                 import Review
from products.models                import Origin, Storage, Product, Image, Order
from users.models                   import User
from my_settings                    import SECRET_KEY, ALGORITHM

class SetUpTearDown(TestCase):
    @classmethod
    def setUpTestData(cls):
        User.objects.bulk_create([
            User(
                kakao_account = 'asdf@kakao.com',
                point = 1000000,
                name = '유저1',
                profile_image = 'asdf',
                email = 'asdf@kakao.com'
            ),
            User(
                kakao_account = 'zxcv@kakao.com',
                point = 2000000,
                name = '유저2',
                profile_image = 'zxcv',
                email = 'zxcv@kakao.com'
            )
        ])

        Origin.objects.bulk_create([
            Origin(name = 'DOMESTIC'),
            Origin(name = 'IMPORTED')
        ])

        Storage.objects.bulk_create([
            Storage(name = 'COLD'),
            Storage(name = 'FROZEN'),
            Storage(name = 'DRY')
        ])

        Product.objects.bulk_create([
            Product(
                name = '상품1',
                price = 10000,
                ordered_quantity = 100,
                description = '상품1입니다',
                stock = 1000,
                origin_id = Origin.Type(1).value,
                storage_id = Storage.Type(1).value,
                user_id = User.objects.get(id=1).id
            ),
            Product(
                name = '상품2',
                price = 20000,
                ordered_quantity = 200,
                description = '상품2입니다',
                stock = 2000,
                origin_id = Origin.Type(2).value,
                storage_id = Storage.Type(3).value,
                user_id = User.objects.get(id=2).id
            ),
            Product(
                id = 3,
                name = '상품3',
                price = 30000,
                ordered_quantity = 300,
                description = '상품3입니다',
                stock = 3000,
                origin_id = Origin.Type(1).value,
                storage_id = Storage.Type(2).value,
                user_id = User.objects.get(id=1).id
            )
        ])

        Image.objects.bulk_create([
            Image(
                url = 'aaaa',
                is_thumbnail=True,
                product_id = Product.objects.get(id=1).id
            ),
            Image(
                url = 'ssss',
                is_thumbnail=False,
                product_id = Product.objects.get(id=1).id
            ),
            Image(
                url = 'dddd',
                is_thumbnail=False,
                product_id = Product.objects.get(id=1).id
            ),
            Image(
                url = 'ffff',
                is_thumbnail=True,
                product_id = Product.objects.get(id=2).id
            ),
            Image(
                url = 'gggg',
                is_thumbnail=True,
                product_id = Product.objects.get(id=3).id
            )
        ])

    def tearDown(self):
        User.objects.all().delete()
        Origin.objects.all().delete()
        Storage.objects.all().delete()
        Product.objects.all().delete()
        Image.objects.all().delete()


class SearchTest(SetUpTearDown):
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
                        "profile_image" : "zxcv"
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


class SellerListTest(SetUpTearDown):
    def test_seller_list_get_success(self):
        self.maxDiff = None
        client = Client()
        response = client.get('/products/seller')
        self.assertEqual(response.json(),
                {
                    "seller" : [{
                        "id"            : 1,
                        "kakao_account" : "asdf@kakao.com",
                        "name"          : "유저1",
                        "profile_image" : "asdf",
                        "category"      : ["COLD", "DOMESTIC", "FROZEN"]
                    },
                    {
                        "id"            : 2,
                        "kakao_account" : "zxcv@kakao.com",
                        "name"          : "유저2",
                        "profile_image" : "zxcv",
                        "category"      : ["DRY", "IMPORTED"]
                    }]
                }
        )
        self.assertEqual(response.status_code, 200)

    def test_seller_list_get_category_success(self):
        self.maxDiff = None
        client = Client()
        response = client.get('/products/seller?category=DOMESTIC')
        self.assertEqual(response.json(),
                {
                    "seller" : [{
                        "id"            : 1,
                        "kakao_account" : "asdf@kakao.com",
                        "name"          : "유저1",
                        "profile_image" : "asdf",
                        "category"      : ["COLD", "DOMESTIC", "FROZEN"]
                    }]
                }
        )
        self.assertEqual(response.status_code, 200)


class SellerProductsTest(SetUpTearDown):
    def test_seller_products_invalid_user_error(self):
        client = Client()
        response = client.get('/products/seller/s')
        self.assertEqual(response.json(), {"message" : "INVALID_USER"})
        self.assertEqual(response.status_code, 400)

    def test_seller_products_get_success(self):
        self.maxDiff = None
        client = Client()
        response = client.get('/products/seller/1')
        self.assertEqual(response.json(),
                {
                    "item" : [{
                        "id"    : 1,
                        "name"  : "상품1",
                        "price" : "10000.00",
                        "stock" : 1000,
                        "image" : "aaaa",
                        "category" : ["DOMESTIC", "COLD"]
                    },
                    {
                        "id" : 3,
                        "name" : "상품3",
                        "price" : "30000.00",
                        "stock" : 3000,
                        "image" : "gggg",
                        "category" : ["DOMESTIC", "FROZEN"]
                    }]
                }
        )
        self.assertEqual(response.status_code, 200)

    def test_seller_products_get_category_success(self):
        self.maxDiff = None
        client = Client()
        response = client.get('/products/seller/1?category=COLD')

        self.assertEqual(response.json(),
                {
                    "item" : [{
                        "id"    : 1,
                        "name"  : "상품1",
                        "price" : "10000.00",
                        "stock" : 1000,
                        "image" : "aaaa",
                        "category" : ["DOMESTIC", "COLD"]
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


class SellerListTest(TestCase):
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

    def test_seller_list_get_success(self):
        client = Client()
        response = client.get('/products/seller')
        self.assertEqual(response.json(),
                {
                    "seller" : [{
                        "id"            : 1,
                        "kakao_account" : "asdf@kakao.com",
                        "name"          : "유저1",
                        "profile_image" : "asdf",
                        "category"      : ["COLD", "DOMESTIC"]
                    },
                    {
                        "id"            : 2,
                        "kakao_account" : "zxcv@kakao.com",
                        "name"          : "유저2",
                        "profile_image" : "zxcv",
                        "category"      : ["IMPORTED", "DRY"]
                    }]
                }
        )
        self.assertEqual(response.status_code, 200)

    def test_seller_list_get_category_success(self):
        self.maxDiff = None
        client = Client()
        response = client.get('/products/seller?category=DOMESTIC')

        self.assertEqual(response.json(),
                {
                    "seller" : [{
                        "id"            : 1,
                        "kakao_account" : "asdf@kakao.com",
                        "name"          : "유저1",
                        "profile_image" : "asdf",
                        "category"      : ["COLD", "DOMESTIC"]
                    }]
                }
        )
        self.assertEqual(response.status_code, 200)


class DetailPageTest(TestCase):
    @classmethod
    def setUpTestData(cls):  
        origin = Origin.objects.create(
                name  = 'Origin1',
         )

        storage = Storage.objects.create(
                name  = 'Storage1',
         )
        
        user1 = User.objects.create(
            name              = "백선호1", 
            kakao_account     = "123456", 
            profile_image_url ='http://k.kakaocdn.net/dn/dScJVH/btq7DShllEz/3X2kXV9W5anK3nmcitWoWk/img_640x640.jpg',
            email             = 'rhadlfrhq@naver.com',
            point             = 1000000
            )

        user2 = User.objects.create(
            name              = "백선호2", 
            kakao_account     = "1234567", 
            profile_image_url ='http://k.kakaocdn.net/dn/dScJVH/btq7DShllEz/3X2kXV9W5anK3nmcitWoWk/img_640x640.jpg',
            email             = '2rhadlfrhq@naver.com',
            point             = 1000000
            )

        product = Product.objects.create(
                id               = 200,
                name             = "product",
                price            = 10000,
                description      = 'description',
                user_id          = user1.id,
                ordered_quantity = 100,
                stock            = 1000,
                origin_id        = origin.id,
                storage_id       = storage.id,
        )
        product2 = Product.objects.create(
                id               = 201,
                name             = "product",
                price            = 10000,
                description      = 'description',
                user_id          = user1.id,
                ordered_quantity = 100,
                stock            = 1000,
                origin_id        = origin.id,
                storage_id       = storage.id,

        )
        Image.objects.bulk_create(
             [Image(
                title        = f'Title{i+1}',
                url          = f'Url{i+1}',
                image_uuid   = f'UUID{i+1}',
                product_id   = product.id,
                is_thumbnail = True
             ) for i in range(2)]
         )

        review = Review.objects.create(
            user_id    = user2.id,
            product_id = product.id,
            image_url  = 'REVIEW_URL',
            grade      = 3,
            content    = '리뷰',
            comment_id = None,
            create_at  = "2021-08-23"
        )
        
        Review.objects.create(
            user_id    = user2.id,
            product_id = product.id,
            image_url  = None,
            grade      = None,
            content    = '리뷰 댓글',
            comment_id = review.id,
            create_at  = "2021-08-23"
        )
        Review.objects.create(
            user_id    = user2.id,
            product_id = product2.id,
            image_url  = 'REVIEW_URL',
            grade      = 3,
            content    = '리뷰',
            comment_id = None,
            create_at  = "2021-08-23"
        )

        Order.objects.create(
            user_id    = user1.id,
            product_id = 200,
            quantity   = 10
        )
        Order.objects.create(
            user_id    = user2.id,
            product_id = 201,
            quantity   = 10
        )
    def tearDown(self):
        Order.objects.all().delete()
        Review.objects.all().delete()
        Image.objects.all().delete()    
        User.objects.all().delete()
        Storage.objects.all().delete()
        Origin.objects.all().delete()
        Product.objects.all().delete()

    def test_detailpage_view(self):
        client       = Client()
        response     = client.get('/products/200')
        self.assertEqual(response.status_code, 200)

    def test_detailpage_no_item(self):
        client       = Client()
        response     = client.get('/products/400')
        self.assertEqual(response.status_code, 400)

    def test_authorization_review_success(self):
        client       = Client()
        user         = User.objects.get(name="백선호1")
        access_token = jwt.encode({"id" : user.id}, key=SECRET_KEY, algorithm=ALGORITHM)
        header       = {"HTTP_Authorization" : access_token}
        data         = {}
        response  = client.post("/products/200", json.dumps(data) ,content_type="application/json", **header)
        self.assertEqual(response.status_code, 200)

    def test_authorization_user(self):
        client       = Client()
        user         = User.objects.get(name="백선호2")
        access_token = jwt.encode({"id" : user.id}, key=SECRET_KEY, algorithm=ALGORITHM)
        header       = {"HTTP_Authorization" : access_token}
        data         = {}
        response  = client.post("/products/200", json.dumps(data) ,content_type="application/json", **header)
        self.assertEqual(response.status_code, 401)
    
    def est_already_exits_review(self):
        client       = Client()
        user         = User.objects.get(name="백선호2")
        access_token = jwt.encode({"id" : user.id}, key=SECRET_KEY, algorithm=ALGORITHM)
        header       = {"HTTP_Authorization" : access_token}
        data         = {}
        response  = client.post("/products/200", json.dumps(data) ,content_type="application/json", **header)
        self.assertEqual(response.status_code, 402)
