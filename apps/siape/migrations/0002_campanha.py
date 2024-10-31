# Generated by Django 5.1 on 2024-10-18 19:16

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('siape', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Campanha',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nome', models.CharField(max_length=100, verbose_name='Nome da Campanha')),
                ('data_criacao', models.DateTimeField(default=django.utils.timezone.now, verbose_name='Data de Criação')),
                ('departamento', models.CharField(max_length=100, verbose_name='Departamento')),
                ('status', models.BooleanField(default=True, verbose_name='Status')),
            ],
        ),
    ]