# Generated by Django 5.1 on 2024-09-04 20:31

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('funcionarios', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Agendamento',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nome_cliente', models.CharField(max_length=255)),
                ('cpf_cliente', models.CharField(max_length=14)),
                ('data_inicio', models.DateField()),
                ('data_fim', models.DateField()),
                ('loja_agendada', models.CharField(choices=[('Porto Alegre', 'Porto Alegre'), ('São Leopoldo', 'São Leopoldo'), ('Santa Maria', 'Santa Maria')], max_length=50)),
                ('funcionario', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='funcionarios.funcionario')),
            ],
        ),
    ]
