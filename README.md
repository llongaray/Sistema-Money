# Projeto Django com Virtualenv

Este documento descreve os passos para configurar um ambiente virtual e instalar as dependências de um projeto Django.

## Configuração do Ambiente Virtual

### 1. Instale o Virtualenv:  

``` pip install virtualenv ```

### 2. Crie o Ambiente Virtual:  

**Windows:**  
``` virtualenv .venv ```

**Linux:**  
``` virtualenv venv ```

### 3. Ative o Ambiente Virtual:  

**Windows:**  
``` .venv\Scripts\activate ```

**Linux:**  
``` source venv/bin/activate ```

### 4. Instale o Django e Outras Dependências:

``` pip install django ```  
``` pip install python-dotenv ```

Outras bibliotecas que você precisar podem ser instaladas usando:

``` pip install nome_da_biblioteca ```

## Iniciando o Projeto Django

Após configurar o ambiente virtual e instalar o Django, você pode iniciar um novo projeto:

1. Crie o projeto Django:

``` django-admin startproject nome_do_projeto . ```

2. Navegue até a pasta do projeto e inicie o servidor:

``` python manage.py runserver ```

## Importância do .env e do .gitignore

### .env

O arquivo `.env` é usado para armazenar variáveis de ambiente, como chaves secretas, credenciais de banco de dados e outras informações sensíveis que não devem ser expostas no código-fonte. É crucial para a segurança e facilita a configuração em diferentes ambientes (desenvolvimento, produção etc.).

### .gitignore

O arquivo `.gitignore` serve para especificar quais arquivos ou diretórios não devem ser incluídos no controle de versão (Git). Nele, você deve adicionar o `.env`, o diretório `venv`, e outros arquivos que não precisam ser compartilhados com o repositório. Exemplo:

```venv/  .env  __pycache__/ *.pyc```

Esses passos ajudam a garantir a segurança e organização do projeto.
