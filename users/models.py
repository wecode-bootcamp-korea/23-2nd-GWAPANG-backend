from django.db import models

class User(models.Model):
    kakao_account = models.CharField(max_length=100)
    point         = models.IntegerField(default=100000)
    name          = models.CharField(max_length=100)
    profile_image = models.URLField(max_length=500)
    email         = models.CharField(max_length=200, null=True)
    image_url     = models.URLField(max_length=500, null=True)

    class Meta:
        db_table = 'users'
