import csv
from pathlib import Path
from django.core.management.base import BaseCommand
from cnpj.models import Cnae, Municipio, NaturezaJuridica, Qualificacao, Motivo

# Caminho da pasta onde você descompactou os arquivos (ajuste se necessário)
DADOS_DIR = Path(__file__).resolve().parent.parent.parent.parent / "dados"


class Command(BaseCommand):
    help = "Importa as tabelas pequenas (Cnaes, Municipios, Naturezas, Qualificacoes, Motivos)"

    def handle(self, *args, **options):
        self.importar_arquivo("*.CNAECSV", Cnae, "codigo", "descricao")
        self.importar_arquivo("*.MUNICCSV", Municipio, "codigo", "nome")
        self.importar_arquivo("*.NATJUCSV", NaturezaJuridica, "codigo", "descricao")
        self.importar_arquivo("*.QUALSCSV", Qualificacao, "codigo", "descricao")
        self.importar_arquivo("*.MOTICSV", Motivo, "codigo", "descricao")
        self.stdout.write(self.style.SUCCESS("Tabelas pequenas importadas com sucesso!"))

    def importar_arquivo(self, padrao_nome, model, campo_codigo, campo_texto):
        arquivos = list(DADOS_DIR.glob(padrao_nome))
        if not arquivos:
            self.stdout.write(self.style.WARNING(f"Nenhum arquivo encontrado para {padrao_nome}"))
            return

        objetos = []
        for arquivo in arquivos:
            with open(arquivo, encoding="latin-1") as f:
                leitor = csv.reader(f, delimiter=";", quotechar='"')
                for linha in leitor:
                    codigo, texto = linha[0], linha[1]
                    objetos.append(model(**{campo_codigo: codigo, campo_texto: texto}))

        # bulk_create com ignore_conflicts evita erro se você rodar o comando de novo
        model.objects.bulk_create(objetos, batch_size=1000, ignore_conflicts=True)
        self.stdout.write(f"{model.__name__}: {len(objetos)} registros processados")