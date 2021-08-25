from django.urls    import path
from products.views import ProductView, SearchView, SellerListView

urlpatterns = [
    path('/search', SearchView.as_view()),
    path('/seller', SellerListView.as_view()),
    path("", ProductView.as_view()),
]
