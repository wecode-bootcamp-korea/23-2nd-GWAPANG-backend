from django.urls    import path
from products.views import ProductView, SearchView, SellerListView, SellerProductsView, DetailPageView

urlpatterns = [
    path('/search', SearchView.as_view()),
    path('/seller', SellerListView.as_view()),
    path('/seller/<user_id>', SellerProductsView.as_view()),
    path("", ProductView.as_view()),
    path("/<int:product_id>", DetailPageView.as_view())
]
