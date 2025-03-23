# Generated by Django 5.1.7 on 2025-03-22 11:40

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('users', '0001_initial'),
        ('subscriptions', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Payment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('status', models.CharField(choices=[('pending', 'Kutilmoqda'), ('approved', 'Tasdiqlangan'), ('rejected', 'Rad etilgan')], default='pending', max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('subscription_plan', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='subscriptions.subscriptionplan')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='users.user')),
            ],
            options={
                'verbose_name': "To'lov",
                'verbose_name_plural': "To'lovlar",
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='PaymentScreenshot',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', models.ImageField(upload_to='screenshots/')),
                ('uploaded_at', models.DateTimeField(auto_now_add=True)),
                ('payment', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='payments.payment')),
            ],
        ),
    ]
