import csv
from datetime import date
from pathlib import Path
from django.core.management.base import BaseCommand
from cnpj.models import Estabelecimento, Empresa, Municipio, Cnae, Motivo

DADOS_DIR = Path(__file__).resolve().parent.parent.parent.parent / "dados"


def parse_data(valor):
    """Converte 'AAAAMMDD' para date, ou None se vazio/invalido."""
    if not valor or valor == "00000000":
        return None
    try:
        return date(int(valor[0:4]), int(valor[4:6]), int(valor[6:8]))
    except (ValueError, IndexError):
        return None


class Command(BaseCommand):
    help = "Importa a tabela Estabelecimentos"

    def handle(self, *args, **options):
        empresas = set(Empresa.objects.values_list("cnpj_basico", flat=True))
        municipios = set(Municipio.objects.values_list("codigo", flat=True))
        cnaes = set(Cnae.objects.values_list("codigo", flat=True))
        motivos = set(Motivo.objects.values_list("codigo", flat=True))

        arquivos = list(DADOS_DIR.glob("*.ESTABELE"))
        if not arquivos:
            self.stdout.write(self.style.WARNING("Nenhum arquivo *.ESTABELE encontrado"))
            return

        total = 0
        for arquivo in arquivos:
            self.stdout.write(f"Lendo {arquivo.name}...")
            objetos = []
            with open(arquivo, encoding="latin-1") as f:
                leitor = csv.reader(f, delimiter=";", quotechar='"')
                for linha in leitor:
                    (cnpj_basico, cnpj_ordem, cnpj_dv, matriz_filial, nome_fantasia,
                     situacao_cadastral, data_situacao, motivo, cidade_exterior, pais,
                     data_inicio, cnae_principal, cnae_secundaria, tipo_logradouro,
                     logradouro, numero, complemento, bairro, cep, uf, municipio,
                     ddd1, tel1, ddd2, tel2, ddd_fax, fax, email,
                     situacao_especial, data_situacao_especial) = linha

                    if cnpj_basico not in empresas:
                        continue  # pula estabelecimento orfao (empresa nao importada ainda)

                    objetos.append(Estabelecimento(
                        empresa_id=cnpj_basico,
                        cnpj_ordem=cnpj_ordem,
                        cnpj_dv=cnpj_dv,
                        identificador_matriz_filial=matriz_filial,
                        nome_fantasia=nome_fantasia,
                        situacao_cadastral=situacao_cadastral,
                        data_situacao_cadastral=parse_data(data_situacao),
                        motivo_situacao_cadastral_id=motivo if motivo in motivos else None,
                        data_inicio_atividade=parse_data(data_inicio),
                        cnae_principal_id=cnae_principal if cnae_principal in cnaes else None,
                        cnae_secundaria=cnae_secundaria,
                        tipo_logradouro=tipo_logradouro,
                        logradouro=logradouro,
                        numero=numero,
                        complemento=complemento,
                        bairro=bairro,
                        cep=cep,
                        uf=uf,
                        municipio_id=municipio if municipio in municipios else None,
                        email=email,
                    ))

                    if len(objetos) >= 5000:
                        Estabelecimento.objects.bulk_create(objetos, batch_size=5000, ignore_conflicts=True)
                        total += len(objetos)
                        objetos = []

            if objetos:
                Estabelecimento.objects.bulk_create(objetos, batch_size=5000, ignore_conflicts=True)
                total += len(objetos)

        self.stdout.write(self.style.SUCCESS(f"Estabelecimento: {total} registros processados"))