# -*- coding: utf-8 -*-
# Generated by Django 1.11.22 on 2020-04-26 06:42
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('kitten', '0020_auto_20200426_0636'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='game',
            name='network',
        ),
        migrations.AddField(
            model_name='game',
            name='level',
            field=models.IntegerField(choices=[(10, 'Basic'), (20, 'Intermediate'), (30, 'Advanced'), (40, 'Expert')], default=10),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='game',
            name='network_name',
            field=models.CharField(default='', max_length=40),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='team',
            name='level',
            field=models.IntegerField(choices=[(10, 'Basic'), (20, 'Intermediate'), (30, 'Advanced'), (40, 'Expert')], default=10),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='game',
            name='name',
            field=models.CharField(blank=True, max_length=40, null=True),
        ),
    ]
