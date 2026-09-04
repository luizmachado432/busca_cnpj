import zipfile
from pathlib import Path

import requests
from django.core.management.base import BaseCommand

SHARE_TOKEN = "YggdBLfdninEJX9"
ANO_MES = "2026-08"  # ajuste conforme a pasta mais recente disponivel no portal
BASE_URL = f"https://arquivos.receitafederal.gov.br/public.php/dav/files/{SHARE_TOKEN}/{ANO_MES}"
AUTH = (SHARE_TOKEN, "")  # HTTP Basic Auth: token como usuario, senha vazia

DADOS_DIR = Path(__file__).resolve().parent.parent.parent.parent / "dados"

# Tabelas pequenas: sempre baixamos por completo (sao poucos KB/MB cada).
ARQUIVOS_PEQUENOS = [
    "Cnaes.zip",
    "Naturezas.zip",
    "Municipios.zip",
    "Qualificacoes.zip",
    "Motivos.zip",
]

# Tabelas grandes: a Receita divide cada uma em 10 partes (0 a 9).
# A base completa soma dezenas de GB, entao para fins deste desafio
# limitamos quantas partes baixar via PARTES_A_BAIXAR, mas o codigo
# ja contempla a existencia das 10 partes de cada tabela.
TABELAS_GRANDES = ["Empresas", "Estabelecimentos", "Socios"]
TOTAL_PARTES = 10  # partes 0 a 9 que a Receita disponibiliza por tabela
PARTES_A_BAIXAR = 1  # <-- ajuste aqui para processar mais partes (ate 10)


def montar_lista_arquivos_grandes():
    arquivos = []
    for tabela in TABELAS_GRANDES:
        for parte in range(TOTAL_PARTES):
            nome = f"{tabela}{parte}.zip"
            if parte < PARTES_A_BAIXAR:
                arquivos.append(nome)
            # partes nao incluidas (parte >= PARTES_A_BAIXAR) sao
            # conhecidas mas deliberadamente nao baixadas nesta execucao
    return arquivos


ARQUIVOS = ARQUIVOS_PEQUENOS + montar_lista_arquivos_grandes()


class Command(BaseCommand):
    help = "Baixa e descompacta os arquivos de dados abertos do CNPJ via WebDAV"

    def handle(self, *args, **options):
        DADOS_DIR.mkdir(exist_ok=True)

        self.stdout.write(
            f"Baixando {len(ARQUIVOS)} arquivo(s): {PARTES_A_BAIXAR} de {TOTAL_PARTES} "
            f"partes de cada tabela grande ({', '.join(TABELAS_GRANDES)})."
        )

        for nome_arquivo in ARQUIVOS:
            destino = DADOS_DIR / nome_arquivo

            if destino.exists():
                self.stdout.write(f"{nome_arquivo} ja existe, pulando download.")
            else:
                self.stdout.write(f"Baixando {nome_arquivo}...")
                url = f"{BASE_URL}/{nome_arquivo}"
                sucesso = self.baixar_arquivo(url, destino)
                if not sucesso:
                    continue

            self.stdout.write(f"Descompactando {nome_arquivo}...")
            self.descompactar(destino)

        self.stdout.write(self.style.SUCCESS("Download e extracao concluidos!"))

    def baixar_arquivo(self, url, destino):
        try:
            with requests.get(url, auth=AUTH, stream=True, timeout=120) as resposta:
                resposta.raise_for_status()
                with open(destino, "wb") as f:
                    for pedaco in resposta.iter_content(chunk_size=8192):
                        f.write(pedaco)
            return True
        except requests.exceptions.RequestException as e:
            self.stdout.write(self.style.ERROR(f"Falha ao baixar {url}: {e}"))
            return False

    def descompactar(self, caminho_zip):
        try:
            with zipfile.ZipFile(caminho_zip) as z:
                z.extractall(DADOS_DIR)
        except zipfile.BadZipFile:
            self.stdout.write(self.style.ERROR(
                f"{caminho_zip.name} nao e um zip valido - o download provavelmente falhou "
                f"(a resposta pode ter sido uma pagina de erro em vez do arquivo)"
            ))