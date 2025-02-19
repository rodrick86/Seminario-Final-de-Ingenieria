# Generated by Django 5.0 on 2024-08-28 03:46

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0020_alter_orden_tiempo_total'),
    ]

    operations = [
        migrations.RenameField(
            model_name='orden',
            old_name='modifacado',
            new_name='modificado',
        ),
        migrations.RemoveField(
            model_name='orden',
            name='descripcion',
        ),
        migrations.CreateModel(
            name='ItemSolicitado',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('descripcion', models.CharField(max_length=255)),
                ('terminado', models.BooleanField(default=False)),
                ('orden', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='items', to='base.orden')),
            ],
        ),
    ]
