# Desafio CNPJ — Ingestão e Visualização de Dados

Aplicação Django + PostgreSQL para coletar, armazenar e consultar dados abertos do
CNPJ disponibilizados pela Receita Federal.

## Stack

- Python 3.12
- Django 5
- PostgreSQL
- requests (download dos arquivos)

## Pré-requisitos

- Python 3.10+
- PostgreSQL instalado e rodando localmente
- Git

## Passo a passo para rodar localmente (Ubuntu/Debian)

### 1. Clonar o repositório

```bash
git clone <url-do-repositorio>
cd <pasta-do-projeto>
```

### 2. Criar e ativar o ambiente virtual

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Instalar as dependências

```bash
pip install -r requirements.txt
```

### 4. Configurar o PostgreSQL

Crie o banco e o usuário que a aplicação vai usar:

```bash
sudo -u postgres psql
```

Dentro do console do Postgres:

```sql
CREATE DATABASE cnpj_db;
CREATE USER cnpj_user WITH PASSWORD 'escolha_uma_senha';
ALTER ROLE cnpj_user SET client_encoding TO 'utf8';
GRANT ALL PRIVILEGES ON DATABASE cnpj_db TO cnpj_user;
\c cnpj_db
GRANT ALL ON SCHEMA public TO cnpj_user;
\q
```

### 5. Configurar as variáveis de ambiente

Copie o arquivo de exemplo e preencha com os valores que você definiu acima:

```bash
cp .env.example .env
```

Edite o `.env` com um editor de texto e preencha `DB_PASSWORD` (a senha escolhida no
passo 4) e `SECRET_KEY`. Para gerar uma `SECRET_KEY` nova:

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### 6. Aplicar as migrations

```bash
python manage.py migrate
```

### 7. Baixar os dados do CNPJ

Este comando baixa e descompacta automaticamente os arquivos públicos da Receita
Federal (não é necessário baixar nada manualmente):

```bash
python manage.py download_data
```

Por padrão, o comando baixa as tabelas auxiliares completas (CNAEs, Municípios,
Naturezas Jurídicas, Qualificações, Motivos) e apenas a primeira das 10 partes de
cada tabela grande (Empresas, Estabelecimentos, Sócios), para manter o tempo de
execução e o espaço em disco administráveis. Para processar mais partes, ajuste a
constante `PARTES_A_BAIXAR` em `cnpj/management/commands/download_data.py`.

### 8. Popular o banco de dados

```bash
python manage.py ingest_all
```

Isso executa, na ordem correta, a importação de todas as tabelas
(tabelas auxiliares → Empresas → Estabelecimentos → Sócios).

### 9. (Opcional) Criar um superusuário para o Django Admin

```bash
python manage.py createsuperuser
```

### 10. Rodar o servidor

```bash
python manage.py runserver
```

Acesse `http://127.0.0.1:8000/` no navegador.

## Funcionalidades

- **Página inicial**: estatísticas gerais (totais, distribuição por UF, situação
  cadastral, porte, CNAEs e naturezas jurídicas mais comuns, municípios com mais
  estabelecimentos).
- **Busca** (`/buscar/`): por razão social (busca parcial) ou CNPJ.
- **Detalhe da empresa** (`/empresa/<cnpj_basico>/`): dados cadastrais, lista de
  estabelecimentos vinculados e sócios.
- **Listagem com filtros** (`/listar/`): por UF, município, situação cadastral e
  CNAE principal, com paginação.
- **Django Admin** (`/admin/`): consulta administrativa direta às tabelas.

## Estrutura de dados

O modelo cobre as entidades exigidas pelo desafio: Empresas, Estabelecimentos,
Sócios, CNAEs, Naturezas Jurídicas e Municípios, além das tabelas auxiliares de
Qualificações e Motivos de situação cadastral.

## Observação sobre a amostra de dados

Por padrão, o projeto baixa apenas a primeira das 10 partes de cada arquivo grande
da Receita Federal (Empresas0, Estabelecimentos0, Socios0), para manter o tempo de
ingestão e o espaço em disco compatíveis com um ambiente de desenvolvimento local.
Isso significa que nem toda empresa presente na amostra de `Empresas0` terá
necessariamente estabelecimentos ou sócios correspondentes carregados (já que a
divisão em partes não segue a mesma distribuição entre os três arquivos). O
pipeline de ingestão foi construído para lidar com a base completa caso as demais
partes sejam adicionadas à lista `ARQUIVOS` em `download_data.py`.

## Uso de Inteligência Artificial

Este projeto foi desenvolvido com apoio do Claude (Anthropic) para: modelagem das
entidades no Django, estruturação dos comandos de ingestão e download automatizado,
construção das views e templates da interface web, e depuração de erros durante o
desenvolvimento. Detalhes sobre quais etapas contaram com apoio de IA são
apresentados no vídeo de demonstração.