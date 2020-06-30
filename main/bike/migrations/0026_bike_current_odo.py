# Generated by Django 2.2.12 on 2020-06-18 11:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bike', '0025_auto_20200601_1541'),
    ]

    operations = [
        migrations.AddField(
            model_name='bike',
            name='current_odo',
            field=models.FloatField(default=0, help_text='calculated current odometer, in distance units from preferences.'),
        ),
    ]
