# Generated by Django 5.0 on 2023-12-31 20:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0011_presupuesto_usuario'),
    ]

    operations = [
        migrations.AlterField(
            model_name='orden',
            name='anio',
            field=models.IntegerField(blank=True, null=True),
        ),
    ]
