import json, boto3, uuid

from time import timezone

from django.http      import JsonResponse
from django.views     import View
from django.db        import transaction

from core.utils       import query_debugger
from users.utils      import login
from reviews.models   import Review
from products.models  import Product


from my_settings      import ACCESS_KEY_ID, BUCKET_NAME, SECRET_ACESS_KEY, AWS_S3_URL


class ReviewView(View):
    s3_client = boto3.client(
        's3',
        aws_access_key_id     = ACCESS_KEY_ID,
        aws_secret_access_key = SECRET_ACESS_KEY,
    )    
    @login
    def post(self, request, product_id):
        try:
            content    = request.POST.get("content")
            grade      = request.POST.get("grade", None)
            image      = request.FILES.get('image', None)
            
            if not image:
                return JsonResponse({"MESSAGE": "IMAGE_FILES_NONE"}, status=404)


            if not content:
                return JsonResponse({"MESSAGE":"NO_CONTENT"}, status=400)
            
            with transaction.atomic():
                review = Review.objects.create(
                    user_id    = request.user.id,
                    product_id = product_id,
                    image_url  = None,
                    image_uuid = str(uuid.uuid4()),
                    content    = content,
                    grade      = grade
                )
                
                self.s3_client.upload_fileobj(
                    image,
                    BUCKET_NAME,
                    review.image_uuid,
                    ExtraArgs = {
                        'ContentType' : image.content_type
                    }
                )
                image_urls       = f"{AWS_S3_URL}/{review.image_uuid}"
                review.image_url = image_urls
                review.save() 

            return JsonResponse({'MESSAGE': "SUCCESS"}, status=201)
        except KeyError:
            return JsonResponse({"MESSAGE": "KEY_ERROR"}, status=400)


class CommentView(View):
    @login
    def post(self, request, product_id):
        try:
            data = json.loads(request.body)
            
            if not Product.objects.filter(id = product_id ,user_id = request.user.id).exists():
                return JsonResponse({'MESSAGE' : 'INVALID_USER'}, status=400)
            
            if not Review.objects.filter(product_id=product_id, comment_id=None).exists():
                return JsonResponse({"MESSAGE": "NOT_EXIST_REVIEW"}, status=400)

            if Review.objects.filter(user_id = request.user.id, product_id=product_id, grade = None, image_uuid = None).exists():
                return JsonResponse({"MESSAGE": "ALREADY_EXIST_COMMENT"}, status=400)
            
            Review.objects.create(
                                user_id    = request.user.id,
                                product_id = product_id,
                                comment_id = data['review_id'],
                                content    = data['content']
                            )           
            return JsonResponse({'MESSAGE': "SUCCESS"}, status=201)
        
        except KeyError:
            return JsonResponse({"MESSAGE": "KEY_ERROR"}, status=400)

    @query_debugger
    def get(self, request, product_id):
        
        reviews = Review.objects.filter(product_id = product_id, comment_id=None).select_related('user').prefetch_related('review_set')
    
        result  = [{
                    "review_writer" : review.user.name, 
                    "review_image"  : review.image_url,
                    'profile_image' : review.user.profile_image_url,
                    "content"       : review.content,
                    "grade"         : review.grade,
                    "create_at"     : review.create_at,
                    "comment"       : {
                            "comment_writer"    : review.user.name,
                            "comment_content"   : review.content,
                            "comment_create_at" : review.create_at
                            } if review.review_set.exists() else None   
                }
            for review in reviews] if True else None

        return JsonResponse({'RESULT':result}, status=200)
