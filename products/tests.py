import json

from django.test import TestCase, Client

from products.models import Origin, Storage, Product, Image, Order
from users.models    import User

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

