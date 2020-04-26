# -*- coding: utf-8 -*-
# Generated by Django 1.11.22 on 2020-04-25 20:39
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('kitten', '0012_auto_20200425_2133'),
    ]

    operations = [
        migrations.RenameField(
            model_name='gamelineparameters',
            old_name='reputation',
            new_name='line_reputation',
        ),
        migrations.RemoveField(
            model_name='gamelineparameters',
            name='name',
        ),
        migrations.RemoveField(
            model_name='gamelineparameters',
            name='network',
        ),
        migrations.AlterField(
            model_name='gamelineparameters',
            name='game',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='kitten.Game'),
        ),
    ]
