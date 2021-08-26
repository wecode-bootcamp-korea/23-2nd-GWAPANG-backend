# Generated by Django 3.2.6 on 2021-08-26 10:20

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('products', '0001_initial'),
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Review',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image_url', models.CharField(default='', max_length=200, null=True)),
                ('image_uuid', models.CharField(max_length=100, null=True)),
                ('grade', models.CharField(max_length=10, null=True)),
                ('content', models.TextField()),
                ('create_at', models.DateTimeField(auto_now_add=True)),
                ('comment', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='reviews.review')),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='products.product')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='users.user')),
            ],
            options={
                'db_table': 'reviews',
            },
        ),
    ]
