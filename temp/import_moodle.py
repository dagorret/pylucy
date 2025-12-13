"""
Management command para importar datos desde archivos NDJSON a Django DB
"""
from django.core.management.base import BaseCommand
from django.conf import settings
from moodledata.models import TABLE_MODEL_MAP
import json
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Importa datos desde archivos NDJSON a la base de datos de Django'

    def add_arguments(self, parser):
        parser.add_argument(
            '--tables',
            type=str,
            default='all',
            help='Tablas a importar (separadas por coma), o "all" para todas'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Limpiar datos existentes antes de importar'
        )

    def handle(self, *args, **options):
        tables = options.get('tables', 'all')
        clear = options.get('clear', False)
        
        # Determinar qué tablas importar
        if tables == 'all':
            tables_to_import = list(TABLE_MODEL_MAP.keys())
        else:
            tables_to_import = [t.strip() for t in tables.split(',')]
        
        self.stdout.write(f"Importando {len(tables_to_import)} tabla(s)...")
        
        try:
            total_records = 0
            
            for table_name in tables_to_import:
                if table_name not in TABLE_MODEL_MAP:
                    self.stdout.write(self.style.WARNING(f"⚠ Tabla '{table_name}' no mapeada"))
                    continue
                
                model = TABLE_MODEL_MAP[table_name]
                input_file = settings.EXPORT_DIR / f'{table_name}.ndjson'
                
                if not input_file.exists():
                    self.stdout.write(self.style.WARNING(f"⚠ Archivo no encontrado: {input_file}"))
                    continue
                
                # Limpiar si se solicita
                if clear:
                    deleted_count = model.objects.all().delete()[0]
                    if deleted_count > 0:
                        self.stdout.write(f"  Eliminados {deleted_count} registros de {table_name}")
                
                # Importar registros
                count = self._import_table(model, input_file, table_name)
                total_records += count
                
                self.stdout.write(self.style.SUCCESS(f"✓ {table_name}: {count} registros importados"))
            
            self.stdout.write(self.style.SUCCESS(f"\n✓ Importación completada: {total_records} registros totales"))
            
        except Exception as e:
            error_msg = f"Error: {e}"
            self.stdout.write(self.style.ERROR(error_msg))
            raise

    def _import_table(self, model, input_file, table_name):
        """Importa registros desde archivo NDJSON"""
        count = 0
        batch = []
        batch_size = 1000
        
        try:
            with open(input_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if not line.strip():
                        continue
                    
                    data = json.loads(line)
                    
                    # Mapear campos de Moodle a campos de Django
                    obj_data = self._map_fields(table_name, data)
                    
                    batch.append(model(**obj_data))
                    count += 1
                    
                    # Insertar en lotes
                    if len(batch) >= batch_size:
                        model.objects.bulk_create(batch, ignore_conflicts=True)
                        batch = []
                        
                        if count % 5000 == 0:
                            self.stdout.write(f"  {table_name}: {count} registros...")
                
                # Insertar registros restantes
                if batch:
                    model.objects.bulk_create(batch, ignore_conflicts=True)
        
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error importando {table_name}: {e}"))
            raise
        
        return count

    def _map_fields(self, table_name, data):
        """Mapea campos del NDJSON a campos del modelo Django"""
        # Mapeo común para todas las tablas
        field_map = {
            'id': 'moodle_id',
        }
        
        result = {}
        for key, value in data.items():
            # Aplicar mapeo si existe, sino usar el mismo nombre
            django_field = field_map.get(key, key)
            result[django_field] = value
        
        return result
