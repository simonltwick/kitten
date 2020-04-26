# -*- coding: utf-8 -*-
# Generated by Django 1.11.22 on 2020-04-25 20:55
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('kitten', '0013_auto_20200425_2139'),
    ]

    operations = [
        migrations.AlterField(
            model_name='team',
            name='owner',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='teams_owned', to=settings.AUTH_USER_MODEL),
        ),
    ]
