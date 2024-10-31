from django import forms
from django.contrib.auth.models import User
from .models import Funcionario
from django.core.exceptions import ValidationError
from .models import Funcionario, Empresa, Horario, Cargo, Departamento

from django.contrib.auth.models import Group

from django import forms
from .models import Funcionario, Empresa, Horario, Cargo, Departamento, Loja  # Importa o modelo Loja

class FuncionarioForm(forms.ModelForm):
    empresa = forms.ModelChoiceField(queryset=Empresa.objects.all(), label='Empresa')
    horario = forms.ModelChoiceField(queryset=Horario.objects.all(), label='Horário')
    cargo = forms.ModelChoiceField(queryset=Cargo.objects.all(), label='Cargo')
    departamento = forms.ModelChoiceField(queryset=Departamento.objects.all(), label='Departamento')
    loja = forms.ModelChoiceField(queryset=Loja.objects.all(), label='Loja')  # Adiciona o campo Loja

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
            'loja',  # Inclui o campo loja nos fields
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
        for field_name in ['nome', 'sobrenome', 'cpf', 'empresa', 'horario', 'cargo', 'departamento', 'loja']:  # Adiciona 'loja' à lista
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
    user = forms.ModelChoiceField(queryset=User.objects.all(), required=True)
    groups = forms.ModelMultipleChoiceField(queryset=Group.objects.all(), required=True)




class FuncionarioFullForm(forms.ModelForm):
    STATUS_CHOICES = [
        ('Ativo', 'Ativo'),
        ('Inativo', 'Inativo'),
    ]

    status = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'mobileToggle',
            'id': 'toggle_status'
        })
    )

    departamento = forms.ModelChoiceField(
        queryset=Departamento.objects.filter(grupo__isnull=False),
        label='Departamento',
        widget=forms.Select(attrs={'class': 'form-control'}),
        empty_label="Selecione um departamento"
    )
    cargo = forms.ModelChoiceField(
        queryset=Cargo.objects.filter(grupo__isnull=False),
        label='Cargo',
        widget=forms.Select(attrs={'class': 'form-control'}),
        empty_label="Selecione um cargo"
    )

    loja = forms.ModelChoiceField(
        queryset=Loja.objects.all(),
        label='Loja',
        widget=forms.Select(attrs={'class': 'form-control'}),
        empty_label="Selecione uma loja",
        required=False
    )

    class Meta:
        model = Funcionario
        fields = [
            'nome', 'sobrenome', 'cpf', 'cnpj', 'pis', 'rg', 'data_de_nascimento', 
            'cnh', 'categoria_cnh', 'cep', 'endereco', 'bairro', 'cidade', 
            'estado', 'celular', 'celular_sms', 'celular_ligacao', 
            'celular_whatsapp', 'nome_do_pai', 'nome_da_mae', 'genero', 
            'nacionalidade', 'naturalidade', 'estado_civil', 'matricula', 
            'empresa', 'loja', 'status', 'data_de_admissao', 'horario', 'departamento', 
            'cargo', 'numero_da_folha', 'ctps', 'superior_direto', 'foto', 
            'identidade', 'carteira_de_trabalho', 'comprovante_de_escolaridade', 
            'pdf_contrato', 'certidao_de_nascimento'
        ]
        widgets = {
            'data_de_nascimento': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'data_de_admissao': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'foto': forms.FileInput(attrs={'class': 'form-control-file'}),
            'empresa': forms.Select(attrs={'class': 'form-control'}),
            'horario': forms.Select(attrs={'class': 'form-control'}),
            'genero': forms.Select(attrs={'class': 'form-control'}),
            'estado_civil': forms.Select(attrs={'class': 'form-control'}),
            'loja': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Adiciona labels e placeholders personalizados
        for field in self.fields:
            if field != 'foto' and field != 'status':
                self.fields[field].label = field.replace('_', ' ').capitalize()
            elif field == 'foto':
                self.fields[field].label = 'Atualizar foto'
            
            if isinstance(self.fields[field].widget, forms.TextInput) or isinstance(self.fields[field].widget, forms.NumberInput):
                self.fields[field].widget.attrs.update({
                    'class': 'form-control',
                    'placeholder': f'Insira {self.fields[field].label.lower()}'
                })
            elif isinstance(self.fields[field].widget, forms.CheckboxInput):
                self.fields[field].widget.attrs.update({'class': 'form-check-input'})
        
        # Atualiza os querysets para departamento e cargo
        self.fields['departamento'].queryset = Departamento.objects.filter(grupo__isnull=False)
        self.fields['cargo'].queryset = Cargo.objects.filter(grupo__isnull=False)

        # Adiciona opções de exibição personalizadas para departamento e cargo
        self.fields['departamento'].label_from_instance = lambda obj: f"{obj.grupo.name}"
        self.fields['cargo'].label_from_instance = lambda obj: f"{obj.nome} (Nível: {obj.nivel})"

        # Adiciona opção de exibição personalizada para loja
        self.fields['loja'].label_from_instance = lambda obj: f"{obj.nome}"

        # Filtra as lojas baseado na empresa selecionada (se houver)
        if self.instance and self.instance.empresa:
            self.fields['loja'].queryset = Loja.objects.filter(empresa=self.instance.empresa)
        else:
            self.fields['loja'].queryset = Loja.objects.none()

    def clean_status(self):
        status = self.cleaned_data.get('status')
        return 'Ativo' if status else 'Inativo'

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
    nome = forms.CharField(max_length=255)  # Campo para o nome do grupo

    class Meta:
        model = Departamento
        fields = []  # Não incluímos nenhum campo do modelo Departamento

    def save(self, commit=True):
        nome = self.cleaned_data.get('nome')
        grupo = Group.objects.create(name=f"Departamento - {nome}")
        departamento = super().save(commit=False)
        departamento.grupo = grupo
        if commit:
            departamento.save()
        return departamento

# Formulário para Cargo
class CargoForm(forms.ModelForm):
    nome = forms.CharField(max_length=255)  # Campo para o nome do grupo
    nivel = forms.CharField(max_length=50)  # Campo para o nível do cargo

    class Meta:
        model = Cargo
        fields = []  # Não incluímos nenhum campo do modelo Cargo

    def save(self, commit=True):
        nome = self.cleaned_data.get('nome')
        nivel = self.cleaned_data.get('nivel')
        grupo = Group.objects.create(name=f"Cargo - {nome}")
        cargo = super().save(commit=False)
        cargo.grupo = grupo
        cargo.nivel = nivel
        if commit:
            cargo.save()
        return cargo
