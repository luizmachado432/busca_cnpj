import csv
from decimal import Decimal, InvalidOperation
from pathlib import Path
from django.core.management.base import BaseCommand
from cnpj.models import Empresa, NaturezaJuridica, Qualificacao

DADOS_DIR = Path(__file__).resolve().parent.parent.parent.parent / "dados"


class Command(BaseCommand):
    help = "Importa a tabela Empresas"

    def handle(self, *args, **options):
        # Carrega as FKs em memória primeiro, pra não bater no banco em cada linha
        naturezas = set(NaturezaJuridica.objects.values_list("codigo", flat=True))
        qualificacoes = set(Qualificacao.objects.values_list("codigo", flat=True))

        arquivos = list(DADOS_DIR.glob("*.EMPRECSV"))
        if not arquivos:
            self.stdout.write(self.style.WARNING("Nenhum arquivo *.EMPRECSV encontrado"))
            return

        total = 0
        for arquivo in arquivos:
            self.stdout.write(f"Lendo {arquivo.name}...")
            objetos = []
            with open(arquivo, encoding="latin-1") as f:
                leitor = csv.reader(f, delimiter=";", quotechar='"')
                for linha in leitor:
                    cnpj_basico, razao_social, nat_juridica, qualif, capital, porte, ente = linha

                    try:
                        capital_social = Decimal(capital.replace(",", "."))
                    except InvalidOperation:
                        capital_social = Decimal("0")

                    objetos.append(Empresa(
                        cnpj_basico=cnpj_basico,
                        razao_social=razao_social,
                        natureza_juridica_id=nat_juridica if nat_juridica in naturezas else None,
                        qualificacao_responsavel_id=qualif if qualif in qualificacoes else None,
                        capital_social=capital_social,
                        porte_empresa=porte,
                        ente_federativo_responsavel=ente,
                    ))

                    # Insere em lotes de 5000 pra não estourar memória com arquivo grande
                    if len(objetos) >= 5000:
                        Empresa.objects.bulk_create(objetos, batch_size=5000, ignore_conflicts=True)
                        total += len(objetos)
                        objetos = []

            if objetos:
                Empresa.objects.bulk_create(objetos, batch_size=5000, ignore_conflicts=True)
                total += len(objetos)

        self.stdout.write(self.style.SUCCESS(f"Empresa: {total} registros processados"))