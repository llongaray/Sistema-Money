from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from apps.funcionarios.models import Funcionario, Loja

class Equipe(models.Model):
    """
    Modelo que representa uma equipe na gincana.
    """
    nome = models.CharField(max_length=100, verbose_name="Nome da Equipe")
    descricao = models.TextField(verbose_name="Descrição", blank=True, null=True)
    logo = models.ImageField(
        upload_to='equipes/logos/', 
        verbose_name="Logo da Equipe",
        blank=True, 
        null=True
    )
    lider = models.ForeignKey(
        Funcionario,
        on_delete=models.SET_NULL,
        related_name='equipes_lideradas',
        verbose_name="Líder da Equipe",
        null=True
    )
    data_criacao = models.DateTimeField(
        default=timezone.now,
        verbose_name="Data de Criação"
    )
    status = models.BooleanField(
        default=True,
        verbose_name="Equipe Ativa"
    )

    def __str__(self):
        return f"{self.nome} - {'Ativa' if self.status else 'Inativa'}"

    class Meta:
        verbose_name = "Equipe"
        verbose_name_plural = "Equipes"
        ordering = ['nome']

class MembroEquipe(models.Model):
    """
    Modelo que representa a associação entre funcionários e equipes.
    """
    funcionario = models.ForeignKey(
        Funcionario,
        on_delete=models.CASCADE,
        related_name='membros_equipe',
        verbose_name="Funcionário"
    )
    equipe = models.ForeignKey(
        Equipe,
        on_delete=models.CASCADE,
        related_name='membros',
        verbose_name="Equipe"
    )
    data_entrada = models.DateTimeField(
        default=timezone.now,
        verbose_name="Data de Entrada"
    )
    ativo = models.BooleanField(
        default=True,
        verbose_name="Membro Ativo"
    )

    def __str__(self):
        return f"{self.funcionario.nome} - {self.equipe.nome}"

    class Meta:
        verbose_name = "Membro de Equipe"
        verbose_name_plural = "Membros de Equipe"
        unique_together = ['funcionario', 'equipe']  # Evita duplicatas

class ProvaGincana(models.Model):
    """
    Modelo que representa uma prova ou atividade da gincana.
    """
    nome = models.CharField(max_length=100, verbose_name="Nome da Prova")
    descricao = models.TextField(verbose_name="Descrição da Prova")
    pontos_possiveis = models.PositiveIntegerField(
        verbose_name="Pontos Possíveis",
        validators=[MinValueValidator(1)]
    )
    data_inicio = models.DateTimeField(verbose_name="Data de Início")
    data_fim = models.DateTimeField(verbose_name="Data de Término")
    icone = models.CharField(
        max_length=50,
        default="fa-star",
        verbose_name="Ícone FontAwesome"
    )
    participantes = models.ManyToManyField(
        Funcionario,
        through='ParticipacaoProva',
        related_name='provas_participadas',
        verbose_name="Participantes"
    )
    status = models.BooleanField(default=True, verbose_name="Prova Ativa")

    def __str__(self):
        return f"{self.nome} - {self.pontos_possiveis} pontos"

    class Meta:
        verbose_name = "Prova da Gincana"
        verbose_name_plural = "Provas da Gincana"
        ordering = ['-data_inicio']

class ParticipacaoProva(models.Model):
    """
    Modelo que registra a participação de funcionários em provas.
    """
    funcionario = models.ForeignKey(
        Funcionario,
        on_delete=models.CASCADE,
        verbose_name="Funcionário"
    )
    prova = models.ForeignKey(
        ProvaGincana,
        on_delete=models.CASCADE,
        verbose_name="Prova"
    )
    data_participacao = models.DateTimeField(
        default=timezone.now,
        verbose_name="Data de Participação"
    )
    pontos_obtidos = models.PositiveIntegerField(
        verbose_name="Pontos Obtidos",
        validators=[MinValueValidator(0)]
    )

    def __str__(self):
        return f"{self.funcionario.nome} - {self.prova.nome} - {self.pontos_obtidos} pontos"

    class Meta:
        verbose_name = "Participação em Prova"
        verbose_name_plural = "Participações em Provas"

class Pontuacao(models.Model):
    """
    Modelo que registra as pontuações gerais dos funcionários.
    """
    funcionario = models.ForeignKey(
        Funcionario,
        on_delete=models.CASCADE,
        related_name='pontuacoes',
        verbose_name="Funcionário"
    )
    equipe = models.ForeignKey(
        Equipe,
        on_delete=models.CASCADE,
        related_name='pontuacoes',
        verbose_name="Equipe"
    )
    pontos = models.PositiveIntegerField(
        verbose_name="Pontos",
        validators=[MinValueValidator(0)]
    )
    motivo = models.TextField(
        verbose_name="Motivo da Pontuação",
        blank=True,
        null=True
    )
    data_registro = models.DateTimeField(
        default=timezone.now,
        verbose_name="Data do Registro"
    )

    def __str__(self):
        return f"{self.funcionario.nome} - {self.pontos} pontos - {self.data_registro.date()}"

    class Meta:
        verbose_name = "Pontuação"
        verbose_name_plural = "Pontuações"
        ordering = ['-data_registro']
