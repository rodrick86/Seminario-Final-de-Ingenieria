# Generated by Django 5.0 on 2024-09-01 00:04

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0029_remove_orden_anio_remove_orden_vehiculo_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='orden',
            name='cliente',
        ),
        migrations.RemoveField(
            model_name='orden',
            name='garantia',
        ),
    ]
