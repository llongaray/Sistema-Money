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

--------------------------------------------------

# Sistema Money

## Atualização de Versão - v4.0

Este documento destaca as principais atualizações, erros corrigidos e tentativas de implementação realizadas durante o desenvolvimento da versão mais recente do **Sistema Money**.

### Atualizações Gerais

- **Digitalização de Processos e Integrações**: Nesta versão, houve melhorias significativas na digitalização e automação dos processos internos. O foco foi na eficiência e na modernização dos procedimentos que, anteriormente, eram realizados de forma manual.

- **Autenticação por QR Code**: Implementamos um sistema onde, após o primeiro login com usuário e senha fornecidos, os funcionários devem utilizar um QR Code com aplicativos de autenticação como Google Authenticator para registrar ações subsequentes. Esta medida aumenta a segurança e facilita o controle de acesso.

- **Verificação de Dados**: Foram implementados mecanismos de validação e verificação para garantir a consistência dos dados e evitar duplicidade em determinadas ações.

### Tentativas Mal-Sucedidas

- **Problemas com Arquivos Grandes no GitHub**: Durante o desenvolvimento, houve diversas tentativas de fazer _push_ de arquivos grandes, resultando em erros. O arquivo `db_antigo.sqlite3`, que ultrapassava o limite de 100 MB imposto pelo GitHub, causou vários conflitos. Como resultado, optou-se por remover o arquivo do controle de versão e configurar o `.gitignore` para evitar futuros conflitos.

- **GitHub LFS (Large File Storage)**: Consideramos brevemente a implementação do Git LFS para gerenciar arquivos grandes, mas, após análise, a equipe decidiu seguir sem essa tecnologia, mantendo o foco no desenvolvimento da aplicação.

### Correções de Erros

- **Erros no Commit e Push Iniciais**: Ao iniciar o repositório, ocorreram erros durante os _commits_ e _pushes_ devido à falta de adição dos arquivos ao _stage_ e à tentativa de enviar arquivos grandes. Esses problemas foram solucionados com a remoção dos arquivos grandes e a adoção de boas práticas de versionamento com o Git.

- **Branch Principal**: Foi necessário ajustar o branch padrão para `main` e corrigir erros relacionados ao envio das alterações para o repositório remoto.
