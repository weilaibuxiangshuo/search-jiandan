# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2019-08-09 15:40
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('major', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='record',
            name='tel',
            field=models.CharField(db_index=True, max_length=15, verbose_name='电话号码'),
        ),
    ]
