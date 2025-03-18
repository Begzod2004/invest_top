# Generated by Django 5.1.7 on 2025-03-18 21:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0002_alter_broadcastmessage_options_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='broadcastmessage',
            name='status',
            field=models.CharField(choices=[('pending', 'Kutilmoqda'), ('sent', 'Yuborildi'), ('failed', 'Xatolik')], default='pending', max_length=20),
        ),
        migrations.AddField(
            model_name='broadcastmessage',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AlterField(
            model_name='broadcastmessage',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True),
        ),
        migrations.AlterField(
            model_name='broadcastmessage',
            name='recipient_type',
            field=models.CharField(choices=[('all', 'Barcha foydalanuvchilarga'), ('subscribed', 'Faqat obunachilarga'), ('active', 'Faol foydalanuvchilarga')], max_length=20),
        ),
    ]
