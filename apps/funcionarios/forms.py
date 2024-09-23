from django import forms
from django.contrib.auth.models import User
from .models import Funcionario
from django.core.exceptions import ValidationError
from .models import Funcionario, Empresa, Horario, Cargo, Departamento

from django.contrib.auth.models import Group

class FuncionarioForm(forms.ModelForm):
    empresa = forms.ModelChoiceField(queryset=Empresa.objects.all(), label='Empresa')
    horario = forms.ModelChoiceField(queryset=Horario.objects.all(), label='Horário')
    cargo = forms.ModelChoiceField(queryset=Cargo.objects.all(), label='Cargo')
    departamento = forms.ModelChoiceField(queryset=Departamento.objects.all(), label='Departamento')

    class Meta:
        model = Funcionario
        fields = [
            'nome',
            'sobrenome',
            'cpf',
            'cep',
            'endereco',
            'bairro',
            'cidade',
            'estado',
            'empresa',
            'horario',
            'cargo',
            'departamento',
            'foto'
        ]
        widgets = {
            'nome': forms.TextInput(attrs={'placeholder': 'Nome'}),
            'sobrenome': forms.TextInput(attrs={'placeholder': 'Sobrenome'}),
            'cpf': forms.TextInput(attrs={'placeholder': 'CPF'}),
            'cep': forms.TextInput(attrs={'placeholder': 'CEP'}),
            'endereco': forms.TextInput(attrs={'placeholder': 'Endereço'}),
            'bairro': forms.TextInput(attrs={'placeholder': 'Bairro'}),
            'cidade': forms.TextInput(attrs={'placeholder': 'Cidade'}),
            'estado': forms.TextInput(attrs={'placeholder': 'Estado'}),
            'foto': forms.ClearableFileInput(attrs={'class': 'form-control-file', 'placeholder': 'Escolha uma foto'})
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Configura labels e atributos
        for field_name in ['nome', 'sobrenome', 'cpf', 'empresa', 'horario', 'cargo', 'departamento']:
            if field_name in self.fields:
                self.fields[field_name].label = field_name.capitalize()
                self.fields[field_name].widget.attrs.update({'class': 'form-control'})



class UserForm(forms.ModelForm):
    confirma_password = forms.CharField(widget=forms.PasswordInput, label='Confirme a Senha')

    class Meta:
        model = User
        fields = ['username', 'email', 'password']
        widgets = {
            'password': forms.PasswordInput,
        }

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirma_password = cleaned_data.get("confirma_password")

        if password and confirma_password and password != confirma_password:
            raise ValidationError("As senhas não coincidem.")

class UserGroupForm(forms.Form):
    user = forms.ModelChoiceField(queryset=User.objects.all(), label="Usuário")
    groups = forms.ModelMultipleChoiceField(queryset=Group.objects.all(), widget=forms.CheckboxSelectMultiple, label="Grupos")



class FuncionarioFullForm(forms.ModelForm):
    class Meta:
        model = Funcionario
        fields = [
            'nome', 'sobrenome', 'cpf', 'cnpj', 'pis', 'rg', 'data_de_nascimento', 
            'cnh', 'categoria_cnh', 'cep', 'endereco', 'bairro', 'cidade', 
            'estado', 'celular', 'celular_sms', 'celular_ligacao', 
            'celular_whatsapp', 'nome_do_pai', 'nome_da_mae', 'genero', 
            'nacionalidade', 'naturalidade', 'estado_civil', 'matricula', 
            'empresa', 'status', 'data_de_admissao', 'horario', 'departamento', 
            'cargo', 'numero_da_folha', 'ctps', 'superior_direto', 'foto', 
            'identidade', 'carteira_de_trabalho', 'comprovante_de_escolaridade', 
            'pdf_contrato', 'certidao_de_nascimento'
        ]
        widgets = {
            'data_de_nascimento': forms.TextInput(attrs={'type': 'text', 'placeholder': 'dd/mm/aaaa'}),
            'data_de_admissao': forms.TextInput(attrs={'type': 'text', 'placeholder': 'dd/mm/aaaa'}),
            'foto': forms.ClearableFileInput(attrs={'class': 'form-control-file'}),
            # Adicione outros widgets conforme necessário
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Adiciona labels e placeholders personalizados
        for field in self.fields:
            if field != 'foto':
                self.fields[field].label = field.replace('_', ' ').capitalize()
            else:
                self.fields[field].label = 'Foto'
            self.fields[field].widget.attrs.update({
                'placeholder': f'Insira {self.fields[field].label.lower()}'
            })

class CustomUserForm(forms.ModelForm):
    confirma_password = forms.CharField(widget=forms.PasswordInput, label='Confirme a Senha')

    class Meta:
        model = User
        fields = ['username', 'email', 'password']
        widgets = {
            'password': forms.PasswordInput,
        }

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirma_password = cleaned_data.get("confirma_password")

        if password and confirma_password and password != confirma_password:
            raise ValidationError("As senhas não coincidem.")


# -------------------------------------------------------------------------------------

from .models import Empresa, Horario, Departamento, Cargo

# Formulário para Empresa
class EmpresaForm(forms.ModelForm):
    class Meta:
        model = Empresa
        fields = ['nome', 'cnpj', 'endereco']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'cnpj': forms.TextInput(attrs={'class': 'form-control'}),
            'endereco': forms.TextInput(attrs={'class': 'form-control'}),
        }

# Formulário para Horário
class HorarioForm(forms.ModelForm):
    class Meta:
        model = Horario
        fields = ['nome', 'horario_entrada', 'horario_saida']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'horario_entrada': forms.TimeInput(format='%H:%M', attrs={'class': 'form-control', 'placeholder': 'HH:MM'}),
            'horario_saida': forms.TimeInput(format='%H:%M', attrs={'class': 'form-control', 'placeholder': 'HH:MM'}),
        }

# Formulário para Departamento
class DepartamentoForm(forms.ModelForm):
    class Meta:
        model = Departamento
        fields = ['nome']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
        }

# Formulário para Cargo
class CargoForm(forms.ModelForm):
    class Meta:
        model = Cargo
        fields = ['nome', 'nivel']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'nivel': forms.TextInput(attrs={'class': 'form-control'}),
        }
