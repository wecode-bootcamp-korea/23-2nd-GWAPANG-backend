from django.urls    import path

from products.views import UploadProductView, SearchView, SellerListView

urlpatterns = [
    path('/search', SearchView.as_view()),
    path('/seller', SellerListView.as_view()),
    path("/upload", UploadProductView.as_view()),
]
