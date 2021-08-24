import json, boto3, uuid

from datetime           import date


from django.http        import JsonResponse
from django.views       import View
from django.db.models   import Case, When, Q
from django.db          import transaction


from users.models       import User
from products.models    import Origin, Storage, Product, Image
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


class UploadProductView(View):
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
                upload.url   = image_urls
                upload.title = image.name
                upload.save()

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
            "category" : [Origin.Type(product.origin_id).name, Storage.Type(product.storage_id).name]
        } for product in products]

        return JsonResponse({"item": item}, status=200)
