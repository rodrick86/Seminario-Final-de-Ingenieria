# Generated by Django 5.0 on 2024-09-08 21:41

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0037_presupuesto_mano_de_obra_presupuesto'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='orden',
            name='intervencion',
        ),
    ]
