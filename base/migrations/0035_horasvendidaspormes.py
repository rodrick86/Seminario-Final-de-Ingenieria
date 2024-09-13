# Generated by Django 5.0 on 2024-09-05 04:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0034_alter_orden_mano_de_obra'),
    ]

    operations = [
        migrations.CreateModel(
            name='HorasVendidasPorMes',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('año', models.IntegerField()),
                ('mes', models.IntegerField()),
                ('horas_totales', models.DecimalField(decimal_places=2, default=0.0, max_digits=10)),
            ],
            options={
                'verbose_name': 'Horas Vendidas por Mes',
                'verbose_name_plural': 'Horas Vendidas por Mes',
                'unique_together': {('año', 'mes')},
            },
        ),
    ]
