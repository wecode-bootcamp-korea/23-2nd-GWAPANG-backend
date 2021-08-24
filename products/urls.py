from django.urls    import path

from products.views import UploadProductView, SearchView, SellerProductsView

urlpatterns = [
    path('/search', SearchView.as_view()),
    path('/seller/<user_id>', SellerProductsView.as_view())
    path("/upload", UploadProductView.as_view()),
]
