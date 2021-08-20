import jwt, requests, random

from django.views         import View
from django.http.response import JsonResponse

from my_settings          import SECRET_KEY, ALGORITHM
from users.models         import User


class KakaoLoginView(View):
    def get(self, request):
        try:
            access_token = request.headers['Authorization']
            url          = "https://kapi.kakao.com/v2/user/me"
            header       = {
                'Authorization' : 'Bearer {}'.format(access_token)
            }
            response = requests.get(url, headers = header).json()                

            user, is_user = User.objects.get_or_create(
                kakao_account     = response['id'], 
                email             = response['kakao_account']['email'], 
                name              = response['kakao_account']['profile']['nickname'],
                profile_image_url = response['kakao_account']['profile']['profile_image_url'],
            )
            if is_user:
                token = jwt.encode({'id': user.id}, SECRET_KEY, algorithm=ALGORITHM)
                return JsonResponse({'MESSAGE': 'SUCCESS', 'user_name': user.name, 'TOKEN': token}, status = 200)
            else:
                token = jwt.encode({'id': user.id}, SECRET_KEY, algorithm=ALGORITHM)
                return JsonResponse({'MESSAGE': 'SUCCESS', 'user_name': user.name, 'TOKEN': token}, status = 201)

        except KeyError:
            return JsonResponse({'message': 'KEY_ERROR'}, status=400)
