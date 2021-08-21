import jwt 

from django.http.response   import JsonResponse
from users.models           import User
from my_settings            import SECRET_KEY, ALGORITHM
from django.core.exceptions import ObjectDoesNotExist     



def login(func):
    def wrapper(self, request, *args, **kwargs):
        try:
            token        = request.headers.get('Authorization', None)
            payload      = jwt.decode(token, SECRET_KEY, algorithms=ALGORITHM)
            user         = User.objects.get(id=payload['id'])
            request.user = user
        
        except jwt.exceptions.DecodeError:
            return JsonResponse({'MESSAGE' : 'INVALID_TOKEN' }, status=400)

        except User.DoesNotExist:
            return JsonResponse({'MESSAGE' : 'INVALID_USER'}, status=400)

        return func(self, request, *args, **kwargs)

    return wrapper

            

