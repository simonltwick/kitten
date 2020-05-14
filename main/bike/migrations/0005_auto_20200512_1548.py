# Generated by Django 2.2.12 on 2020-05-12 14:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bike', '0004_auto_20200512_1543'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ride',
            name='ascent_units',
            field=models.PositiveSmallIntegerField(choices=[(1, 'm'), (2, 'Ft')], default=1),
        ),
    ]
