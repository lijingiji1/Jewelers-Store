# Generated by Django 5.0.3 on 2024-05-15 07:06

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0004_auto_20210529_1741'),
    ]

    operations = [
        migrations.AddField(
            model_name='address',
            name='address',
            field=models.CharField(max_length=150, null=True, verbose_name='Address Line '),
        ),
        migrations.AddField(
            model_name='address',
            name='email',
            field=models.EmailField(max_length=254, null=True, verbose_name='Email Address'),
        ),
        migrations.AddField(
            model_name='address',
            name='firstname',
            field=models.CharField(max_length=150, null=True, verbose_name='First Name'),
        ),
        migrations.AddField(
            model_name='address',
            name='lastname',
            field=models.CharField(max_length=150, null=True, verbose_name='Last Name'),
        ),
        migrations.AddField(
            model_name='address',
            name='phone',
            field=models.CharField(max_length=150, null=True, verbose_name='Phone Number'),
        ),
        migrations.AlterField(
            model_name='order',
            name='status',
            field=models.CharField(choices=[('Pending', 'Pending'), ('Accepted', 'Accepted'), ('Packed', 'Packed'), ('On The Way', 'On The Way'), ('Delivered', 'Delivered'), ('Cancelled', 'Cancelled')], default='Pending', max_length=50),
        ),
        migrations.AlterField(
            model_name='product',
            name='category',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='store.category', verbose_name='Product Category'),
        ),
    ]