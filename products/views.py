import json

from django.http  import JsonResponse
from django.views import View
from django.db.models import Case, When

from users.models import User
from products.models import Origin, Storage, Product, Image

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
