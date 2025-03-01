# Generated by Django 5.1 on 2025-01-30 10:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('subscriptions', '0002_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Feature',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, unique=True)),
            ],
        ),
        migrations.RemoveField(
            model_name='subscriptionplan',
            name='features',
        ),
        migrations.AddField(
            model_name='subscriptionplan',
            name='features',
            field=models.ManyToManyField(related_name='subscription_plans', to='subscriptions.feature'),
        ),
    ]
