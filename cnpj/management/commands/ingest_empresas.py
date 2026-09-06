import csv
from decimal import Decimal, InvalidOperation
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction

from cnpj.models import Empresa, NaturezaJuridica, Qualificacao

DADOS_DIR = Path(__file__).resolve().parent.parent.parent.parent / "dados"
TAMANHO_LOTE = 20000


def limpar_objeto(obj):
    """Remove caracteres NUL (0x00) de todos os campos de texto do objeto."""
    for campo in obj._meta.get_fields():
        nome_atributo = getattr(campo, "attname", None)
        if nome_atributo is None:
            continue
        valor = getattr(obj, nome_atributo, None)
        if isinstance(valor, str) and "\x00" in valor:
            setattr(obj, nome_atributo, valor.replace("\x00", ""))
    return obj


class Command(BaseCommand):
    help = "Importa a tabela Empresas (DEBUG off, transacao unica, limpeza automatica de NUL)"

    def handle(self, *args, **options):
        settings.DEBUG = False

        naturezas = set(NaturezaJuridica.objects.values_list("codigo", flat=True))
        qualificacoes = set(Qualificacao.objects.values_list("codigo", flat=True))

        arquivos = list(DADOS_DIR.glob("*.EMPRECSV"))
        if not arquivos:
            self.stdout.write(self.style.WARNING("Nenhum arquivo *.EMPRECSV encontrado"))
            return

        total = 0
        for arquivo in arquivos:
            self.stdout.write(f"Lendo {arquivo.name}...")
            linhas_lote = []

            with open(arquivo, encoding="latin-1") as f:
                leitor = csv.reader(f, delimiter=";", quotechar='"')
                for linha in leitor:
                    linhas_lote.append(linha)

                    if len(linhas_lote) >= TAMANHO_LOTE:
                        total += self.processar_lote(linhas_lote, naturezas, qualificacoes)
                        #self.stdout.write(f"  ... {total} processados ate agora") debug para contagem processos
                        linhas_lote = []

                if linhas_lote:
                    total += self.processar_lote(linhas_lote, naturezas, qualificacoes)

        self.stdout.write(self.style.SUCCESS(f"Empresa: {total} registros processados"))

    @transaction.atomic
    def processar_lote(self, linhas, naturezas, qualificacoes):
        objetos = []
        for linha in linhas:
            cnpj_basico, razao_social, nat_juridica, qualif, capital, porte, ente = linha

            try:
                capital_social = Decimal(capital.replace(",", "."))
            except InvalidOperation:
                capital_social = Decimal("0")

            obj = Empresa(
                cnpj_basico=cnpj_basico,
                razao_social=razao_social,
                natureza_juridica_id=nat_juridica if nat_juridica in naturezas else None,
                qualificacao_responsavel_id=qualif if qualif in qualificacoes else None,
                capital_social=capital_social,
                porte_empresa=porte,
                ente_federativo_responsavel=ente,
            )
            objetos.append(limpar_objeto(obj))

        Empresa.objects.bulk_create(objetos, batch_size=TAMANHO_LOTE, ignore_conflicts=True)
        return len(objetos)