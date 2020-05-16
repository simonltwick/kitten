# -*- coding: utf-8 -*-
# Generated by Django 1.11.22 on 2020-05-03 11:21
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('kitten', '0029_auto_20200503_1220'),
    ]

    operations = [
        migrations.AlterField(
            model_name='teaminvitation',
            name='team',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='invitations', to='kitten.Team'),
        ),
    ]
