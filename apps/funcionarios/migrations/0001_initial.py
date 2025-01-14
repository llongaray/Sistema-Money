# Generated by Django 5.1 on 2024-08-28 20:26

import django.core.files.storage
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Funcionario',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nome', models.CharField(max_length=100)),
                ('sobrenome', models.CharField(max_length=100)),
                ('cpf', models.CharField(max_length=14)),
                ('cnpj', models.CharField(blank=True, max_length=18, null=True)),
                ('pis', models.CharField(max_length=11)),
                ('rg', models.CharField(max_length=12)),
                ('data_de_nascimento', models.DateField()),
                ('cnh', models.CharField(blank=True, max_length=20, null=True)),
                ('categoria_cnh', models.CharField(blank=True, max_length=10, null=True)),
                ('cep', models.CharField(max_length=9)),
                ('endereco', models.CharField(max_length=255)),
                ('bairro', models.CharField(max_length=100)),
                ('cidade', models.CharField(max_length=100)),
                ('estado', models.CharField(max_length=2)),
                ('celular', models.CharField(max_length=15)),
                ('celular_sms', models.BooleanField(default=False)),
                ('celular_ligacao', models.BooleanField(default=False)),
                ('celular_whatsapp', models.BooleanField(default=False)),
                ('nome_do_pai', models.CharField(blank=True, max_length=100, null=True)),
                ('nome_da_mae', models.CharField(blank=True, max_length=100, null=True)),
                ('genero', models.CharField(max_length=10)),
                ('nacionalidade', models.CharField(max_length=30)),
                ('naturalidade', models.CharField(max_length=30)),
                ('estado_civil', models.CharField(blank=True, max_length=20, null=True)),
                ('matricula', models.CharField(blank=True, max_length=20, null=True)),
                ('empresa', models.CharField(max_length=50)),
                ('status', models.CharField(default='Ativo', max_length=10)),
                ('data_de_admissao', models.DateField()),
                ('horario', models.CharField(blank=True, max_length=20, null=True)),
                ('departamento', models.CharField(max_length=50)),
                ('cargo', models.CharField(max_length=50)),
                ('numero_da_folha', models.CharField(blank=True, max_length=20, null=True)),
                ('ctps', models.CharField(blank=True, max_length=20, null=True)),
                ('foto', models.ImageField(blank=True, null=True, storage=django.core.files.storage.FileSystemStorage(location='media/files_funcionarios/'), upload_to='files_funcionarios/%Y/%m/%d/foto/')),
                ('identidade', models.FileField(blank=True, null=True, storage=django.core.files.storage.FileSystemStorage(location='media/files_funcionarios/'), upload_to='files_funcionarios/%Y/%m/%d/identidade/')),
                ('carteira_de_trabalho', models.FileField(blank=True, null=True, storage=django.core.files.storage.FileSystemStorage(location='media/files_funcionarios/'), upload_to='files_funcionarios/%Y/%m/%d/carteira_de_trabalho/')),
                ('comprovante_de_escolaridade', models.FileField(blank=True, null=True, storage=django.core.files.storage.FileSystemStorage(location='media/files_funcionarios/'), upload_to='files_funcionarios/%Y/%m/%d/comprovante_de_escolaridade/')),
                ('pdf_contrato', models.FileField(blank=True, null=True, storage=django.core.files.storage.FileSystemStorage(location='media/files_funcionarios/'), upload_to='files_funcionarios/%Y/%m/%d/pdf_contrato/')),
                ('certidao_de_nascimento', models.FileField(blank=True, null=True, storage=django.core.files.storage.FileSystemStorage(location='media/files_funcionarios/'), upload_to='files_funcionarios/%Y/%m/%d/certidao_de_nascimento/')),
                ('superior_direto', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='subordinados', to='funcionarios.funcionario')),
                ('usuario', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='funcionario', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
