# Generated by Django 5.1 on 2025-01-31 04:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('booking', '0004_alter_truck_image'),
    ]

    operations = [
        migrations.AlterField(
            model_name='truck',
            name='image',
            field=models.ImageField(blank=True, default='trucks/service-3.jpg', upload_to='trucks/'),
        ),
    ]
