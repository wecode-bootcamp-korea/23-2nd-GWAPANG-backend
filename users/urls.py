from django.urls import path
from users.views import KakaoLoginView

urlpatterns = [
    path('/login/kakao', KakaoLoginView.as_view())
]