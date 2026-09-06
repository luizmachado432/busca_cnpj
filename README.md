# Desafio CNPJ — Ingestão e Visualização de Dados

Aplicaçao Django + PostgreSQL para coletar, armazenar e consultar dados abertos do
CNPJ disponibilizados pela Receita Federal.


## Pré-requisitos

- Python 3.10+
- PostgreSQL

# 1. Criar e ativar o ambiente virtual

```bash
python3 -m venv venv
source venv/bin/activate
```

# 2. Instalar as dependências

```bash
pip install -r requirements.txt
```

# 3. Configurar o PostgreSQL

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

# 4. Configurar as variáveis de ambiente

Copie e renomeie o arquivo de exemplo e preencha com os valores que você definiu acima:


Edite o `.env` com um editor de texto e preencha `DB_PASSWORD` (a senha escolhida no
passo 4) e `SECRET_KEY`. Para gerar uma `SECRET_KEY` nova:

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

# 5. Aplicar as migrations

```bash
python manage.py migrate
```

# 6. Baixar os dados do CNPJ

Este comando baixa e descompacta automaticamente os arquivos das empresas:

```bash
python manage.py download_data
```

Por padrão, o comando baixa as tabelas auxiliares completas (CNAEs, Municípios,
Naturezas Jurídicas, Qualificações, Motivos) e uma das 10 partes de
cada tabela grande (empresas, estabelecimentos, socios), pois esses arquivos possuem varios gbs e para testes é desnecessario a instalaçao de todos. Para processar mais partes ajuste a
constante `PARTES_A_BAIXAR` em `cnpj/management/commands/download_data.py` ela é uma lista que instala todos a partir do numero no final de cada arquivo.

# 7. Popular o banco de dados

```bash
python manage.py ingest_all
```

Isso executa na ordem correta, a importação de todas as tabelas na ordem para atender todas dependencias entre elas.
(tabelas auxiliares → Empresas → Estabelecimentos → Sócios).
### 9. Rodar o servidor

```bash
python manage.py runserver
```

Acesse `http://127.0.0.1:8000/` no navegador.

## Funcionalidades

- **home**: estatisticas gerais (totais, distribuição por UF, situação
  cadastral, porte, CNAEs e naturezas jurídicas mais comuns, munici**pios com mais
  estabelecimentos).
- **Busca** (`/buscar/`): por razão social (busca parcial) ou CNPJ.
- **Detalhe da empresa** (`/empresa/<cnpj_basico>/`): dados cadastrais, lista de
  estabelecimentos vinculados e sócios.
- **Listagem com filtros** (`/listar/`): por UF, município, situação cadastral e
  CNAE principal, com paginação.

## Observação sobre a amostra de dados

Por padrão, o projeto baixa apenas a segunda das 10 partes de cada arquivo grande
da Receita Federal (Empresas1, Estabelecimentos1, Socios1) , para manter o tempo de
ingestão e o espaço em disco compatíveis com um ambiente de desenvolvimento local.
Isso significa que nem toda empresa presente na amostra de `Empresas1` terá
necessariamente estabelecimentos ou socios correspondentes carregados (já que a
divisão em partes não segue a mesma distribuição entre os tres arquivos). O
pipeline de ingestao foi construido para lidar com a base completa caso as demais
partes sejam adicionadas à lista `ARQUIVOS` em `download_data.py`.

## Observação sobre segurança

Neste projeto, não tive como prioridade o tratamento de questões de segurança de forma aprofundada. Algumas medidas foram deixadas de lado por se tratar de uma aplicação simples, local e desenvolvida com o propósito de teste e avaliação técnica. Isso não representa necessariamente um problema para o contexto deste projeto, mas achei importante deixar claras as minhas escolhas e intenções em relação à segurança, principalmente para não dar a entender que esses aspectos foram ignorados por desconhecimento ou falta de consideração.

