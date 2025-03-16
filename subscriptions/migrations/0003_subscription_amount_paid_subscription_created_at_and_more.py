# Generated by Django 5.1.7 on 2025-03-13 03:09

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('subscriptions', '0002_remove_subscription_created_admin_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='subscription',
            name='amount_paid',
            field=models.DecimalField(decimal_places=2, default=1, max_digits=10),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='subscription',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='subscription',
            name='payment_screenshot',
            field=models.ImageField(blank=True, null=True, upload_to='screenshots/'),
        ),
        migrations.AlterField(
            model_name='subscription',
            name='end_date',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='subscription',
            name='start_date',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='subscription',
            name='status',
            field=models.CharField(choices=[('pending', 'Pending Payment'), ('waiting_admin', 'Waiting for Admin'), ('active', 'Active'), ('expired', 'Expired'), ('rejected', 'Rejected')], default='pending', max_length=15),
        ),
    ]
