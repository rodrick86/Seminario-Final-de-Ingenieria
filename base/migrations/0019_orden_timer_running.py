# Generated by Django 5.0 on 2024-08-28 01:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0018_orden_hora_final_orden_tiempo_total'),
    ]

    operations = [
        migrations.AddField(
            model_name='orden',
            name='timer_running',
            field=models.BooleanField(default=False),
        ),
    ]
