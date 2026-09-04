from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Roda toda a ingestao de dados do CNPJ, na ordem correta"

    def handle(self, *args, **options):
        self.stdout.write("Iniciando ingestao completa...")
        call_command("ingest_small")
        call_command("ingest_empresas")
        call_command("ingest_estabelecimentos")
        call_command("ingest_socios")
        self.stdout.write(self.style.SUCCESS("Ingestao completa finalizada!"))