# Generated by Django 2.2.12 on 2020-06-01 14:41

import bike.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bike', '0024_auto_20200530_1158'),
    ]

    operations = [
        migrations.AlterField(
            model_name='componentchange',
            name='distance_units',
            field=models.PositiveSmallIntegerField(choices=[(10, 'miles'), (20, 'kilometres')], default=bike.models.DistanceUnits(10)),
        ),
        migrations.AlterField(
            model_name='maintenanceaction',
            name='distance_units',
            field=models.PositiveSmallIntegerField(choices=[(10, 'miles'), (20, 'kilometres')], default=bike.models.DistanceUnits(10)),
        ),
        migrations.AlterField(
            model_name='odometer',
            name='distance_units',
            field=models.PositiveSmallIntegerField(choices=[(10, 'miles'), (20, 'kilometres')], default=bike.models.DistanceUnits(10)),
        ),
        migrations.AlterField(
            model_name='preferences',
            name='distance_units',
            field=models.PositiveSmallIntegerField(choices=[(10, 'miles'), (20, 'kilometres')], default=bike.models.DistanceUnits(10)),
        ),
        migrations.AlterField(
            model_name='ride',
            name='distance_units',
            field=models.PositiveSmallIntegerField(choices=[(10, 'miles'), (20, 'kilometres')], default=bike.models.DistanceUnits(10)),
        ),
    ]
