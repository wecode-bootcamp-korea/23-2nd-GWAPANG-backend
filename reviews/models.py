from django.db import models

from users.models    import User
from products.models import Product

class Review(models.Model):
    user      = models.ForeignKey(User, on_delete=models.CASCADE)
    product   = models.ForeignKey(Product, on_delete=models.CASCADE)
    image_url = models.URLField(max_length=500, null=True)
    grade     = models.IntegerField(null=True)
    content   = models.TextField()
    comment   = models.ForeignKey("self", on_delete=models.SET_NULL, null=True)
    create_at = models.DateTimeField(auto_now_add=True)
    update_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'reviews'
