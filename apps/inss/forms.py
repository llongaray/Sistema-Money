from django import forms
from .models import Agendamento

class AgendamentoForm(forms.ModelForm):
    class Meta:
        model = Agendamento
        fields = ['nome_cliente', 'cpf_cliente', 'numero_celular', 'data', 'loja_agendada']

class ConfirmacaoForm(forms.Form):
    agendamento_id = forms.IntegerField(widget=forms.HiddenInput())
    confirmacao_agem = forms.BooleanField(required=False)
    comparecimento = forms.BooleanField(required=False)
    negocio_fechado = forms.BooleanField(required=False)

class ReliseClienteForm(forms.ModelForm):
    class Meta:
        model = Agendamento
        fields = ['nome_cliente', 'cpf_cliente', 'numero_celular', 'loja_agendada']
