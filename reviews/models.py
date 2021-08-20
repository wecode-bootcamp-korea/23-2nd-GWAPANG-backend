from django.db import models


class Review(models.Model):
    user       = models.ForeignKey('users.User', on_delete=models.CASCADE)
    product    = models.ForeignKey('products.Product', on_delete=models.CASCADE)
    image_url  = models.CharField(max_length=200, default='', null=True)
    image_uuid = models.CharField(max_length=100, null=True)
    grade      = models.CharField(max_length=10,null=True)
    content    = models.TextField()
    comment    = models.ForeignKey("self", on_delete=models.SET_NULL, null=True)
    create_at  = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'reviews'



