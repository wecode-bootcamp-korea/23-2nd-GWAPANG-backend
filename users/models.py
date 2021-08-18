from django.db import models

class User(models.Model):
    kakao_account = models.CharField(max_length=100)
    point         = models.IntegerField()
    name          = models.CharField(max_length=100)
    profile_image = models.URLField(max_length=500, null=True)

    class Meta:
        db_table = 'users'
