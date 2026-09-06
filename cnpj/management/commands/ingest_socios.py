import csv
from datetime import date
from pathlib import Path
from django.core.management.base import BaseCommand
from cnpj.models import Socio, Empresa, Qualificacao

DADOS_DIR = Path(__file__).resolve().parent.parent.parent.parent / "dados"


def parse_data(valor):
    if not valor or valor == "00000000":
        return None
    try:
        return date(int(valor[0:4]), int(valor[4:6]), int(valor[6:8]))
    except (ValueError, IndexError):
        return None


class Command(BaseCommand):
    help = "Importa a tabela Socios"

    def handle(self, *args, **options):
        empresas = set(Empresa.objects.values_list("cnpj_basico", flat=True))
        qualificacoes = set(Qualificacao.objects.values_list("codigo", flat=True))

        arquivos = list(DADOS_DIR.glob("*.SOCIOCSV"))
        if not arquivos:
            self.stdout.write(self.style.WARNING("Nenhum arquivo *.SOCIOCSV encontrado"))
            return

        total = 0
        for arquivo in arquivos:
            self.stdout.write(f"Lendo {arquivo.name}...")
            objetos = []
            with open(arquivo, encoding="latin-1") as f:
                leitor = csv.reader(f, delimiter=";", quotechar='"')
                for linha in leitor:
                    (cnpj_basico, identificador, nome_socio, cpf_cnpj, qualificacao,
                     data_entrada, pais, representante, nome_representante,
                     qualificacao_representante, faixa_etaria) = linha

                    if cnpj_basico not in empresas:
                        continue

                    objetos.append(Socio(
                        empresa_id=cnpj_basico,
                        identificador_socio=identificador,
                        nome_socio=nome_socio,
                        cpf_cnpj_socio=cpf_cnpj,
                        qualificacao_socio_id=qualificacao if qualificacao in qualificacoes else None,
                        data_entrada_sociedade=parse_data(data_entrada),
                        pais=pais,
                        representante_legal=representante,
                        nome_representante=nome_representante,
                        qualificacao_representante_id=qualificacao_representante if qualificacao_representante in qualificacoes else None,
                        faixa_etaria=faixa_etaria,
                    ))

                    if len(objetos) >= 4000:
                        Socio.objects.bulk_create(objetos, batch_size=5000, ignore_conflicts=True)
                        total += len(objetos)
                        objetos = []

            if objetos:
                Socio.objects.bulk_create(objetos, batch_size=5000, ignore_conflicts=True)
                total += len(objetos)

        self.stdout.write(self.style.SUCCESS(f"Socio: {total} registros processados"))