# Generated by Django 5.0 on 2024-09-08 23:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0039_remove_orden_descripcion'),
    ]

    operations = [
        migrations.AddField(
            model_name='orden',
            name='intervencion',
            field=models.TextField(blank=True, null=True),
        ),
    ]
