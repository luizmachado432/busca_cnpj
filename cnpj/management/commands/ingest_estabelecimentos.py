import csv
from datetime import date
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction

from cnpj.models import Estabelecimento, Empresa, Municipio, Cnae, Motivo

DADOS_DIR = Path(__file__).resolve().parent.parent.parent.parent / "dados"
TAMANHO_LOTE = 20000


def parse_data(valor):
    if not valor or valor == "00000000":
        return None
    try:
        return date(int(valor[0:4]), int(valor[4:6]), int(valor[6:8]))
    except (ValueError, IndexError):
        return None


def limpar_objeto(obj):
    """
    Remove caracteres NUL (0x00) de TODOS os campos de texto do objeto,
    automaticamente, em vez de depender de limpar campo por campo manualmente
    (evita esquecer algum campo que tambem possa vir com esse problema).
    """
    for campo in obj._meta.get_fields():
        nome_atributo = getattr(campo, "attname", None)
        if nome_atributo is None:
            continue
        valor = getattr(obj, nome_atributo, None)
        if isinstance(valor, str) and "\x00" in valor:
            setattr(obj, nome_atributo, valor.replace("\x00", ""))
    return obj


class Command(BaseCommand):
    help = "Importa a tabela Estabelecimentos (limpeza automatica de NUL, transacao unica, lotes grandes)"

    def handle(self, *args, **options):
        settings.DEBUG = False  # evita acumulo de log de queries em memoria durante a carga

        municipios = set(Municipio.objects.values_list("codigo", flat=True))
        cnaes = set(Cnae.objects.values_list("codigo", flat=True))
        motivos = set(Motivo.objects.values_list("codigo", flat=True))

        arquivos = list(DADOS_DIR.glob("*.ESTABELE"))
        if not arquivos:
            self.stdout.write(self.style.WARNING("Nenhum arquivo *.ESTABELE encontrado"))
            return

        total = 0
        total_pulados = 0
        for arquivo in arquivos:
            self.stdout.write(f"Lendo {arquivo.name}...")
            linhas_lote = []

            with open(arquivo, encoding="latin-1") as f:
                leitor = csv.reader(f, delimiter=";", quotechar='"')
                for linha in leitor:
                    linhas_lote.append(linha)

                    if len(linhas_lote) >= TAMANHO_LOTE:
                        processados, pulados = self.processar_lote(linhas_lote, municipios, cnaes, motivos)
                        total += processados
                        total_pulados += pulados
                        #self.stdout.write(f"  ... {total} processados ate agora") apenas debug 
                        linhas_lote = []

                if linhas_lote:
                    processados, pulados = self.processar_lote(linhas_lote, municipios, cnaes, motivos)
                    total += processados
                    total_pulados += pulados

        self.stdout.write(self.style.SUCCESS(
            f"Estabelecimento: {total} registros processados ({total_pulados} pulados - empresa nao encontrada)"
        ))

    @transaction.atomic
    def processar_lote(self, linhas, municipios, cnaes, motivos):
        cnpjs_do_lote = {linha[0] for linha in linhas}
        empresas_existentes = set(
            Empresa.objects.filter(cnpj_basico__in=cnpjs_do_lote).values_list("cnpj_basico", flat=True)
        )

        objetos = []
        pulados = 0
        for linha in linhas:
            (cnpj_basico, cnpj_ordem, cnpj_dv, matriz_filial, nome_fantasia,
             situacao_cadastral, data_situacao, motivo, cidade_exterior, pais,
             data_inicio, cnae_principal, cnae_secundaria, tipo_logradouro,
             logradouro, numero, complemento, bairro, cep, uf, municipio,
             ddd1, tel1, ddd2, tel2, ddd_fax, fax, email,
             situacao_especial, data_situacao_especial) = linha

            if cnpj_basico not in empresas_existentes:
                pulados += 1
                continue

            obj = Estabelecimento(
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
            )
            objetos.append(limpar_objeto(obj))

        if objetos:
            Estabelecimento.objects.bulk_create(objetos, batch_size=TAMANHO_LOTE, ignore_conflicts=True)

        return len(objetos), pulados