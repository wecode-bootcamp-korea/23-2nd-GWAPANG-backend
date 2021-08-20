from django.db import models

from users.models import User

class Origin(models.Model):
    class Type(models.IntegerChoices):
        DOMESTIC = 1
        IMPORTED = 2

    name = models.CharField(max_length=20, choices=Type.choices)

    class Meta:
        db_table = 'origins'

class Storage(models.Model):
    class Type(models.IntegerChoices):
        COLD   = 1
        FROZEN = 2
        DRY    = 3

    name = models.CharField(max_length=20, choices=Type.choices)

    class Meta:
        db_table = 'storages'

class Product(models.Model):
    origin           = models.ForeignKey("Origin", on_delete=models.CASCADE)
    storage          = models.ForeignKey("Storage", on_delete=models.CASCADE)
    user             = models.ForeignKey(User, on_delete=models.CASCADE)
    name             = models.CharField(max_length=50)
    price            = models.DecimalField(max_digits=18, decimal_places=2)
    ordered_quantity = models.IntegerField(default=0)
    description      = models.TextField()
    stock            = models.IntegerField()

    class Meta:
        db_table = 'products'

class Image(models.Model):
    product      = models.ForeignKey("Product", on_delete=models.CASCADE)
    url          = models.URLField(max_length=500)
    is_thumbnail = models.BooleanField(null=True, default=False)

    class Meta:
        db_table = 'images'

class Order(models.Model):
    user     = models.ForeignKey(User, on_delete=models.CASCADE)
    product  = models.ForeignKey("Product", on_delete=models.CASCADE)
    quantity = models.IntegerField()

    class Meta:
        db_table = 'orders'
