from django.urls    import path

from products.views import UploadProductView, SearchView

from products.views import SearchView

urlpatterns = [
    path('/search', SearchView.as_view()),
    path("/upload", UploadProductView.as_view()),
]
