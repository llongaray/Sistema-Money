from django.db import models
from django.contrib.auth.models import User, Group
from django.core.files.storage import FileSystemStorage
from django.conf import settings
import os

# Definindo o diretório de armazenamento para arquivos de funcionários
fs = FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT, 'files_funcionarios'))

def get_funcionario_upload_path(instance, filename):
    """Define o diretório como 'funcionarios/nome_do_funcionario/foto.png'"""
    return os.path.join('funcionarios', instance.nome.upper(), 'foto.png')

# Modelo de Empresas
class Empresa(models.Model):
    nome = models.CharField(max_length=255)
    cnpj = models.CharField(max_length=18, unique=True)
    endereco = models.CharField(max_length=255)

    def save(self, *args, **kwargs):
        self.nome = self.nome.upper()  # Convertendo o nome para caixa alta
        super(Empresa, self).save(*args, **kwargs)

    def __str__(self):
        return self.nome

    class Meta:
        verbose_name_plural = "Empresas"

class Loja(models.Model):
    nome = models.CharField(max_length=255)
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='lojas')
    logo = models.ImageField(upload_to='lojas/logos/', null=True, blank=True)  # Novo campo

    def save(self, *args, **kwargs):
        self.nome = self.nome.upper()
        super(Loja, self).save(*args, **kwargs)

    def __str__(self):
        return f'{self.nome} - {self.empresa.nome}'

    class Meta:
        verbose_name_plural = "Lojas"

# Modelo de Horários
class Horario(models.Model):
    nome = models.CharField(max_length=255)
    horario_entrada = models.TimeField()
    horario_saida = models.TimeField()

    def __str__(self):
        return f"{self.nome} ({self.horario_entrada} - {self.horario_saida})"

    class Meta:
        verbose_name_plural = "Horários"


# Modelo de Departamentos
class Departamento(models.Model):
    grupo = models.OneToOneField(Group, on_delete=models.CASCADE, related_name='departamento')
    # outros campos, se houver

    def __str__(self):
        return self.grupo.name

    class Meta:
        verbose_name_plural = "Departamentos"


# Modelo de Cargos
class Cargo(models.Model):
    nome = models.CharField(max_length=100)
    nivel = models.CharField(max_length=50)
    grupo = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='cargos', null=True, blank=True)

    class Meta:
        verbose_name_plural = "Cargos"
        unique_together = ('nome', 'nivel')

    def __str__(self):
        return f"{self.nome} (Nível: {self.nivel})"

    def save(self, *args, **kwargs):
        if not self.grupo:
            # Não cria um novo grupo aqui, isso será feito na view
            pass
        super().save(*args, **kwargs)


# Modelo de Funcionários
class Funcionario(models.Model):
    # Informações básicas
    usuario = models.OneToOneField(User, on_delete=models.CASCADE, related_name='funcionario', null=True, blank=True)
    nome = models.CharField(max_length=100)
    sobrenome = models.CharField(max_length=100)
    cpf = models.CharField(max_length=20)
    data_de_nascimento = models.DateField(blank=True, null=True)
    genero = models.CharField(max_length=100, blank=True, null=True)
    estado_civil = models.CharField(max_length=200, blank=True, null=True)

    # Informações de contato
    cep = models.CharField(max_length=9, blank=True, null=True)
    endereco = models.CharField(max_length=255, blank=True, null=True)
    bairro = models.CharField(max_length=100, blank=True, null=True)
    cidade = models.CharField(max_length=100, blank=True, null=True)
    estado = models.CharField(max_length=200, blank=True, null=True)
    celular = models.CharField(max_length=200, blank=True, null=True)
    celular_sms = models.BooleanField(default=False, blank=True, null=True)
    celular_ligacao = models.BooleanField(default=False, blank=True, null=True)
    celular_whatsapp = models.BooleanField(default=False, blank=True, null=True)

    # Informações familiares
    nome_do_pai = models.CharField(max_length=100, blank=True, null=True)
    nome_da_mae = models.CharField(max_length=100, blank=True, null=True)
    nacionalidade = models.CharField(max_length=200, blank=True, null=True)
    naturalidade = models.CharField(max_length=200, blank=True, null=True)

    # Documentos
    rg = models.CharField(max_length=20, blank=True, null=True)
    cnpj = models.CharField(max_length=20, blank=True, null=True)
    pis = models.CharField(max_length=20, blank=True, null=True)
    cnh = models.CharField(max_length=20, blank=True, null=True)
    categoria_cnh = models.CharField(max_length=200, blank=True, null=True)
    ctps = models.CharField(max_length=200, blank=True, null=True)

    # Informações profissionais
    matricula = models.CharField(max_length=20000, blank=True, null=True)
    empresa = models.ForeignKey('Empresa', on_delete=models.SET_NULL, null=True, blank=True)
    loja = models.ForeignKey('Loja', on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=10, default='Ativo')
    data_de_admissao = models.DateField(blank=True, null=True)
    horario = models.ForeignKey('Horario', on_delete=models.SET_NULL, null=True, blank=True)
    departamento = models.ForeignKey('Departamento', on_delete=models.SET_NULL, null=True, blank=True)
    cargo = models.ForeignKey('Cargo', on_delete=models.SET_NULL, null=True, blank=True)
    numero_da_folha = models.CharField(max_length=200, blank=True, null=True)
    superior_direto = models.ForeignKey('self', on_delete=models.SET_NULL, blank=True, null=True, related_name='subordinados')

    # Arquivos
    foto = models.ImageField(upload_to=get_funcionario_upload_path, blank=True, null=True)
    identidade = models.FileField(upload_to=get_funcionario_upload_path, storage=fs, blank=True, null=True)
    carteira_de_trabalho = models.FileField(upload_to=get_funcionario_upload_path, storage=fs, blank=True, null=True)
    comprovante_de_escolaridade = models.FileField(upload_to=get_funcionario_upload_path, storage=fs, blank=True, null=True)
    pdf_contrato = models.FileField(upload_to=get_funcionario_upload_path, storage=fs, blank=True, null=True)
    certidao_de_nascimento = models.FileField(upload_to=get_funcionario_upload_path, storage=fs, blank=True, null=True)

    def save(self, *args, **kwargs):
        """Converte nome e sobrenome para caixa alta antes de salvar"""
        self.nome = self.nome.upper()
        self.sobrenome = self.sobrenome.upper()
        super().save(*args, **kwargs)

    def __str__(self):
        """Retorna uma representação em string do funcionário"""
        if self.loja:
            return f"{self.nome} {self.sobrenome} (Loja ID: {self.loja.id})"
        return f"{self.nome} {self.sobrenome}"

    class Meta:
        verbose_name_plural = "Funcionários"
