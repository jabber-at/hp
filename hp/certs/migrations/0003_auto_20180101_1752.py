# Generated by Django 2.0 on 2018-01-01 17:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('certs', '0002_auto_20180101_1211'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='certificate',
            name='tlsa',
        ),
        migrations.AddField(
            model_name='certificate',
            name='md5',
            field=models.CharField(blank=True, max_length=47, verbose_name='MD5'),
        ),
    ]