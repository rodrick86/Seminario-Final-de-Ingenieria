# Generated by Django 5.0 on 2024-09-08 21:43

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0038_remove_orden_intervencion'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='orden',
            name='descripcion',
        ),
    ]
