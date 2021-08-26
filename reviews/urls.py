from django.urls import path
from reviews.views import ReviewView, CommentView, RecentReviewView

urlpatterns = [
    path("/<int:product_id>", ReviewView.as_view()),
    path("/<int:product_id>/comment", CommentView.as_view()),
    path('/recent', RecentReviewView.as_view())

]
