# Generated by Django 5.0 on 2023-12-25 00:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0008_presupuesto_fecha_creacion'),
    ]

    operations = [
        migrations.AddField(
            model_name='presupuesto',
            name='token',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
