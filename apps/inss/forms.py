from django import forms
from .models import Agendamento
from apps.funcionarios.models import Funcionario, Loja, Empresa

class AgendamentoForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        funcionarios = kwargs.pop('funcionarios', None)
        lojas = kwargs.pop('lojas', None)
        super().__init__(*args, **kwargs)

        if funcionarios:
            self.fields['atendente_agendou'].choices = [(funcionario.id, funcionario.nome) for funcionario in funcionarios]

        if lojas:
            self.fields['loja_agendada'].choices = [(loja.id, loja.nome) for loja in lojas]

    class Meta:
        model = Agendamento
        fields = [
            'nome_cliente', 
            'cpf_cliente', 
            'numero_cliente', 
            'dia_agendado', 
            'loja_agendada', 
            'atendente_agendou'
        ]
        widgets = {
            'nome_cliente': forms.TextInput(attrs={'required': True, 'maxlength': 255}),
            'cpf_cliente': forms.TextInput(attrs={'required': True, 'maxlength': 14, 'placeholder': '000.000.000-00'}),
            'numero_cliente': forms.TextInput(attrs={'required': True, 'maxlength': 15, 'placeholder': '(00) 00000-0000'}),
            'dia_agendado': forms.DateInput(attrs={'type': 'date'}),
            'loja_agendada': forms.Select(attrs={'required': True}),
            'atendente_agendou': forms.Select(attrs={'required': True}),
        }



class ConfirmacaoAgendamentoForm(forms.Form):
    agendamento_id = forms.IntegerField(widget=forms.HiddenInput())
    status = forms.ChoiceField(choices=[
        ('CONFIRMADO', 'CONFIRMADO'),
        ('REAGENDADO', 'REAGENDADO'),
        ('DESISTENCIA', 'DESISTÊNCIA'),
    ], required=True)
    dia_agendado = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))

class ListaClientesForm(forms.Form):
    cliente_id = forms.IntegerField(widget=forms.HiddenInput())
    status = forms.ChoiceField(choices=[
        ('NÃO QUIS OUVIR', 'NÃO QUIS OUVIR'),
        ('NEGÓCIO FECHADO', 'NEGÓCIO FECHADO'),
        ('NÃO ELEGÍVEL', 'NÃO ELEGÍVEL'),
    ], required=True)
