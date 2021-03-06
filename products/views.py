import json, boto3, uuid

from datetime           import date


from django.http        import JsonResponse
from django.views       import View
from django.db.models   import Case, When, Q, Prefetch, Sum, F
from django.db          import transaction


from users.models       import User
from products.models    import Origin, Storage, Product, Image, Order
from reviews.models     import Review
from users.utils        import login
from my_settings        import ACCESS_KEY_ID, BUCKET_NAME, SECRET_ACESS_KEY, AWS_S3_URL


class SearchView(View):
    def get(self, request):
        keyword  = request.GET.get("keyword", "")

        if not keyword:
            return JsonResponse({"seller": [], "item": []}, status=200)

        users    = User.objects.filter(name__icontains=keyword)
        products = Product.objects.filter(name__icontains=keyword).annotate(thumbnail=Case(When(image__is_thumbnail=True, then='image__url'))).exclude(thumbnail=None)

        seller = [{
            "id"            : user.id,
            "kakao_account" : user.kakao_account,
            "name"          : user.name,
            "profile_image" : user.profile_image,
            } for user in users]

        item = [{
            "id"       : product.id,
            "name"     : product.name,
            "price"    : product.price,
            "stock"    : product.stock,
            "image"    : product.thumbnail
        } for product in products]

        return JsonResponse({"seller": seller, "item": item}, status=200)


class ProductView(View):
    s3_client = boto3.client(
        's3',
        aws_access_key_id     = ACCESS_KEY_ID,
        aws_secret_access_key = SECRET_ACESS_KEY,
    )

    @login
    def post(self, request):
        name         = request.POST.get('name')
        price        = request.POST.get('price')
        description  = request.POST.get('description')
        stock        = request.POST.get('stock')
        origin       = request.POST.get('origin')
        storage      = request.POST.get('storage')
        images       = request.FILES.getlist('images')
        product_id   = request.GET.get('product_id', None)

        if not images:
            return JsonResponse({"MESSAGE": "IMAGE_FILES_NONE"}, status=404)

        if Product.objects.filter(user_id=request.user.id, create_at=date.today()).count() > 3:
            return JsonResponse({"MESSAGE": "YOU_CANT_UPLOAD"}, status=400)

        with transaction.atomic():
            product= Product.objects.create(
                user_id     = request.user.id,
                name        = name,
                price       = price,
                description = description,
                stock       = stock,
                origin_id   = origin,
                storage_id  = storage
            )           

            Image.objects.bulk_create(
                [Image( 
                product_id   = product.id,
                url          = None,
                is_thumbnail = True if i ==0 else False
                )for i in range(len(images))]                
            )

            for i, image in enumerate(images):
                my_uuid = str(uuid.uuid4())
                upload  = Image.objects.filter(product_id = product.id)[i]
                self.s3_client.upload_fileobj(
                    image,
                    BUCKET_NAME,
                    my_uuid,
                    ExtraArgs = {
                        'ContentType' : image.content_type
                    }
                )

                image_urls   = f"{AWS_S3_URL}/{my_uuid}"
                upload.image_uuid = my_uuid
                upload.url   = image_urls
                upload.title = image.name
                upload.save()
            
            if product_id:
                for i in range(len(Image.objects.filter(product_id=product_id))):
                    self.s3_client.delete_object(Bucket=BUCKET_NAME, Key=Image.objects.filter(product_id=product_id)[i].image_uuid)
                
                Product.objects.filter(id=product_id).delete()

                return JsonResponse({"PRODUCT_ID" : product.id, 'MESSAGE' : "SUCCESS1"}, status=202)
            else:
                return JsonResponse({"PRODUCT_ID" : product.id, 'MESSAGE' : "SUCCESS"}, status=201)

    @login
    def delete(self, request):
        product_id = request.GET.get('product_id')

        if not Product.objects.filter(user_id = request.user.id, id=product_id).exists():
            return JsonResponse({"MESSAGE": "INAVILD_PRODUCT"}, status=404)
        
        with transaction.atomic():

            for i in range(len(Image.objects.filter(product_id=product_id))):
                self.s3_client.delete_object(Bucket=BUCKET_NAME, Key=Image.objects.filter(product_id=product_id)[i].image_uuid)
            
            Product.objects.get(id=product_id).delete()

        return JsonResponse({"MESSAGE" : "NO_CONTENT"}, status=204)


    @login
    def get(self, request):
        product_id = request.GET.get('product_id')

        if not Product.objects.filter(id=product_id).exists():
            return JsonResponse({"MESSAGE":"NO_PRODUCT"}, status=400)        

        product = Product.objects.prefetch_related("image_set").get(id=product_id)

        result = {
            "name"        : product.name,
            "price"       : product.price,
            "stock"       : product.stock,
            "origin"      : product.origin_id,
            "storage"     : product.storage_id,
            "description" : product.description,
            "images"      : [image.url for image in product.image_set.all()],
        }

        return JsonResponse({'RESULT':result}, status=200)
 

class SellerListView(View):
    def get(self, request):
        category = request.GET.get("category", "")
        order_by = request.GET.get("order_by", "")

        user_q    = Q()
        product_q = Q()

        if category in Origin.Type.names:
            origin_type = Origin.Type.names.index(category)+1
            user_q      = Q(product__origin_id=origin_type) 
            product_q   = Q(origin_id=origin_type)
        elif category in Storage.Type.names:
            storage_type = Storage.Type.names.index(category)+1
            user_q       = Q(product__storage_id=storage_type)
            product_q    = Q(storage_id=storage_type)

        if order_by and order_by not in ["order", "id"]:
            return JsonResponse({"message": "INVALID_ORDER_BY"}, status=400)

        if order_by == "id":
            order_by = '-' + order_by
        elif order_by == "order":
            order_by = '-total_' + order_by

        users = []
        if order_by:
            users = User.objects.annotate(total_order=Sum('product__ordered_quantity')).order_by(order_by)[:10]
        else:
            users = User.objects.filter(user_q).prefetch_related(
                        Prefetch('product_set', queryset=Product.objects.filter(product_q), to_attr='category')
            ).order_by('id').distinct()

        seller = [{
            "id"            : user.id,
            "name"          : user.name,
            "profile_image" : user.profile_image,
        } for user in users]

        return JsonResponse({"seller": seller}, status=200)


class SellerProductsView(View):
    def get(self, request, user_id):
        category = request.GET.get("category", "")
 
        if not user_id.isdigit():
            return JsonResponse({"message": "INVALID_USER"}, status=400)

        q = Q(user=user_id)

        if category in Origin.Type.names:
            q &= Q(origin_id=Origin.Type.names.index(category)+1)
        elif category in Storage.Type.names:
            q &= Q(storage_id=Storage.Type.names.index(category)+1)

        products = Product.objects.filter(q).annotate(thumbnail=Case(When(image__is_thumbnail=True, then='image__url'))).exclude(thumbnail=None)
 
        item = [{
            "id"       : product.id,
            "name"     : product.name,
            "price"    : product.price,
            "stock"    : product.stock,
            "image"    : product.thumbnail,
        } for product in products]

        return JsonResponse({"item": item}, status=200)


class ProductListView(View):
    def get(self, request):
        category  = request.GET.get("category", "")
        order_by = request.GET.get("order_by", "")

        q = Q()
        if category in Origin.Type.names:
            q = Q(origin_id=Origin.Type.names.index(category)+1)
        elif category in Storage.Type.names:
            q = Q(storage_id=Storage.Type.names.index(category)+1)

        if order_by and order_by not in ["order", "stock"]:
            return JsonResponse({"message": "INVALID_ORDER_BY"}, status=400)

        if order_by == "order":
            order_by = '-' + order_by + 'ed_quantity'
        else:
            order_by = '-id'

        products = Product.objects.filter(q).annotate(thumbnail=Case(When(image__is_thumbnail=True, then='image__url'))).exclude(thumbnail=None).order_by(order_by)[:10]

        item = [{
            "id"               : product.id,
            "name"             : product.name,
            "price"            : product.price,
            "ordered_quantity" : product.ordered_quantity,
            "stock"            : product.stock,
            "image"            : product.thumbnail
        } for product in products]

        return JsonResponse({"item": item}, status=200)


class DetailPageView(View):
    def get(self, request, product_id):        
        if not Product.objects.filter(id=product_id).exists():
            return JsonResponse({"MESSAGE":"NO_ITEM"}, status=400)
    
        product = Product.objects.prefetch_related("image_set", "review_set").select_related("user").get(id=product_id)
        reviews = product.review_set.filter(product=product.id, comment=None)
        result = [{
            "product_name"        : product.name,
            "seller_name"         : product.user.name,
            "seller_image"        : product.user.profile_image,
            "product_price"       : product.price,
            "product_stock"       : product.stock,
            "product_description" : product.description,
            "product_origin"      : Origin.Type(product.origin_id).name,
            "product_storage"     : Storage.Type(product.storage_id).name,
            "product_image"       : [image.url for image in product.image_set.all()],
            "product_review"      :[
                {
                    "review_writer" : review.user.name, 
                    "review_image"  : review.image_url,
                    'profile_image' : review.user.profile_image,
                    "content"       : review.content,
                    "grade"         : review.grade,
                    "create_at"     : review.create_at,
                    "comment"       : {
                            "comment_writer"    : review.review_set.get(grade=None).user.name,
                            "comment_content"   : review.review_set.get(grade=None).content,
                            "comment_create_at" : review.review_set.get(grade=None).create_at                
                    } if review.review_set.filter(grade=None).exists() else None
                }
            for review in reviews] if reviews.exists() else None
        }]

        return JsonResponse({'RESULT':result}, status=200)
    
    @login
    def post(self, request, product_id):
        if not Order.objects.filter(user_id = request.user.id, product_id = product_id).exists():
            return JsonResponse({"MESSAGE": "UNATHORIZED_REVIEW"}, status=401)

        if Review.objects.filter(user_id = request.user.id, product_id = product_id, comment_id=None).exists():
            return JsonResponse({"MESSAGE": "ALREADY_EXIST_REVIEW"}, status=402)
        
        return JsonResponse({'MESSAGE': "SUCCESS"}, status=200)


class PurchaseView(View):
    @login
    def post(self, request, product_id):
        try:
            data   = json.loads(request.body)
            with transaction.atomic():
                product = Product.objects.select_related("user").get(id=product_id)
                
                if product.user.point < data['total_price']:
                    return JsonResponse({"MESSAGE":"INSUFFICIENT_POINTS"}, status=400)

                product.user.point = F('point') - data['total_price']
                product.user.save()            
                
                product.ordered_quantity = F("ordered_quantity") + data['quantity']
                product.stock            = F("stock") - data['quantity'] 
                product.save()
                
                Order.objects.create(
                    user_id  = request.user.id,
                    product_id  = product_id,
                    quantity = data['quantity']
                )
                
            
            return JsonResponse({'MESSAGE': "SUCCESS"}, status=201)
        
        except KeyError:
            return JsonResponse({"MESSAGE": "KEY_ERROR"}, status=400)
