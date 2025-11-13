from django.core.management.base import BaseCommand
from django.utils import timezone

from core.uti_ingesta import (
    sync_listado_preinscriptos,
    sync_listado_ingresantes,
    sync_listado_aspirantes,
)


class Command(BaseCommand):
    help = "Sincroniza listados UTI (preinscriptos, ingresantes, aspirantes) para una fecha."

    def add_arguments(self, parser):
        parser.add_argument(
            "--fecha",
            type=str,
            help="Fecha a sincronizar en formato YYYY-MM-DD (por defecto: hoy).",
        )
        parser.add_argument(
            "--n",
            type=int,
            help="Cantidad de registros simulados (mock).",
        )

    def handle(self, *args, **options):
        # Determinar la fecha
        if options["fecha"]:
            try:
                fecha = timezone.datetime.fromisoformat(options["fecha"]).date()
            except ValueError:
                self.stderr.write(self.style.ERROR("Formato de fecha inválido. Use YYYY-MM-DD."))
                return
        else:
            fecha = timezone.now().date()

        n = options.get("n")

        self.stdout.write(self.style.NOTICE(f"Sincronizando UTI para fecha: {fecha}, n={n}"))

        desde = hasta = fecha

        # Llamamos a la ingesta por tipo
        sync_listado_preinscriptos(desde, hasta, n=n)
        sync_listado_ingresantes(desde, hasta, n=n)
        sync_listado_aspirantes(desde, hasta, n=n)

        self.stdout.write(self.style.SUCCESS("Sincronización UTI finalizada."))

