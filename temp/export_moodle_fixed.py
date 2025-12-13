"""
Management command para exportar datos desde Moodle a archivos NDJSON
"""
from django.core.management.base import BaseCommand
from django.conf import settings
import mysql.connector
from mysql.connector import Error
import json

# Definiciones de tablas
TABLE_DEFINITIONS = {
    'courses': {
        'query': """
            SELECT c.id, c.shortname, c.fullname, c.category, 
                   c.startdate, c.enddate, c.visible
            FROM {prefix}course c 
            WHERE c.id > 1 
            ORDER BY c.id
        """,
        'paged': False,
        'pk': 'id'
    },
    'categories': {
        'query': """
            SELECT id, name, parent, path, visible
            FROM {prefix}course_categories
            ORDER BY id
        """,
        'paged': False,
        'pk': 'id'
    },
    'enrol': {
        'query': """
            SELECT e.id, e.courseid, e.enrol, e.status
            FROM {prefix}enrol e
            ORDER BY e.id
        """,
        'paged': False,
        'pk': 'id'
    },
    'user_enrolments': {
        'query': """
            SELECT ue.id, ue.userid, ue.enrolid, 
                   ue.timestart, ue.timeend, ue.status
            FROM {prefix}user_enrolments ue
            WHERE ue.id > %(last_id)s
            ORDER BY ue.id ASC
            LIMIT %(page_size)s
        """,
        'paged': True,
        'pk': 'id'
    },
    'users': {
        'query': """
            SELECT u.id, u.username, u.firstname, u.lastname, 
                   u.email, u.city, u.country, u.suspended, u.deleted
            FROM {prefix}user u
            WHERE u.deleted = 0 AND u.id > %(last_id)s
            ORDER BY u.id ASC
            LIMIT %(page_size)s
        """,
        'paged': True,
        'pk': 'id'
    },
    'groups': {
        'query': """
            SELECT g.id, g.courseid, g.name, g.idnumber
            FROM {prefix}groups g
            ORDER BY g.id
        """,
        'paged': False,
        'pk': 'id'
    },
    'groups_members': {
        'query': """
            SELECT gm.id, gm.groupid, gm.userid
            FROM {prefix}groups_members gm
            WHERE gm.id > %(last_id)s
            ORDER BY gm.id ASC
            LIMIT %(page_size)s
        """,
        'paged': True,
        'pk': 'id'
    },
    'user_lastaccess': {
        'query': """
            SELECT ula.id, ula.userid, ula.courseid, ula.timeaccess
            FROM {prefix}user_lastaccess ula
            WHERE ula.id > %(last_id)s
            ORDER BY ula.id ASC
            LIMIT %(page_size)s
        """,
        'paged': True,
        'pk': 'id'
    },
    'role_assignments': {
        'query': """
            SELECT ra.id, ra.roleid, ra.contextid, ra.userid,
                   ra.timemodified, ra.modifierid
            FROM {prefix}role_assignments ra
            WHERE ra.id > %(last_id)s
            ORDER BY ra.id ASC
            LIMIT %(page_size)s
        """,
        'paged': True,
        'pk': 'id'
    },
    'context': {
        'query': """
            SELECT c.id, c.contextlevel, c.instanceid, c.path, c.depth
            FROM {prefix}context c
            WHERE c.id > %(last_id)s
            ORDER BY c.id ASC
            LIMIT %(page_size)s
        """,
        'paged': True,
        'pk': 'id'
    }
}


class Command(BaseCommand):
    help = 'Exporta datos desde Moodle a archivos NDJSON'

    def add_arguments(self, parser):
        parser.add_argument(
            '--tables',
            type=str,
            default='all',
            help='Tablas a exportar (separadas por coma), o "all" para todas'
        )

    def handle(self, *args, **options):
        tables = options.get('tables', 'all')
        
        # Determinar qué tablas exportar
        if tables == 'all':
            tables_to_export = list(TABLE_DEFINITIONS.keys())
        else:
            tables_to_export = [t.strip() for t in tables.split(',')]
        
        self.stdout.write(f"Exportando {len(tables_to_export)} tabla(s)...")
        
        try:
            # Conectar a Moodle DB
            connection = mysql.connector.connect(
                host=settings.MOODLE_DB_CONFIG['host'],
                port=settings.MOODLE_DB_CONFIG['port'],
                database=settings.MOODLE_DB_CONFIG['database'],
                user=settings.MOODLE_DB_CONFIG['user'],
                password=settings.MOODLE_DB_CONFIG['password'],
                charset='utf8mb4',
                use_unicode=True
            )
            
            self.stdout.write(self.style.SUCCESS('✓ Conectado a Moodle DB'))
            
            total_records = 0
            
            # Asegurar que existe el directorio
            settings.EXPORT_DIR.mkdir(parents=True, exist_ok=True)
            
            # Exportar cada tabla
            for table_name in tables_to_export:
                if table_name not in TABLE_DEFINITIONS:
                    self.stdout.write(self.style.WARNING(f"⚠ Tabla '{table_name}' no definida"))
                    continue
                
                definition = TABLE_DEFINITIONS[table_name]
                
                if definition['paged']:
                    count = self._export_paged(connection, table_name, definition)
                else:
                    count = self._export_full(connection, table_name, definition)
                
                total_records += count
                self.stdout.write(self.style.SUCCESS(f"✓ {table_name}: {count} registros"))
            
            connection.close()
            
            self.stdout.write(self.style.SUCCESS(f"\n✓ Exportación completada: {total_records} registros totales"))
            
        except Error as e:
            error_msg = f"Error de base de datos: {e}"
            self.stdout.write(self.style.ERROR(error_msg))
            raise
        except Exception as e:
            error_msg = f"Error: {e}"
            self.stdout.write(self.style.ERROR(error_msg))
            raise

    def _export_full(self, connection, table_name, definition):
        """Exporta tabla completa"""
        query = definition['query'].replace(
            '{prefix}', 
            settings.MOODLE_DB_CONFIG['prefix']
        )
        output_file = settings.EXPORT_DIR / f'{table_name}.ndjson'
        
        cursor = connection.cursor(dictionary=True, buffered=False)
        count = 0
        
        try:
            cursor.execute(query)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                for row in cursor:
                    f.write(json.dumps(row, ensure_ascii=False, default=str) + '\n')
                    count += 1
                    
                    if count % 1000 == 0:
                        self.stdout.write(f"  {table_name}: {count} registros...")
        finally:
            cursor.close()
        
        return count

    def _export_paged(self, connection, table_name, definition):
        """Exporta tabla con paginación"""
        query_template = definition['query'].replace(
            '{prefix}', 
            settings.MOODLE_DB_CONFIG['prefix']
        )
        pk = definition['pk']
        output_file = settings.EXPORT_DIR / f'{table_name}.ndjson'
        
        cursor = connection.cursor(dictionary=True, buffered=False)
        total_count = 0
        last_id = 0
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                while True:
                    cursor.execute(query_template, {
                        'last_id': last_id,
                        'page_size': settings.EXPORT_PAGE_SIZE
                    })
                    
                    count = 0
                    for row in cursor:
                        last_id = row[pk]
                        f.write(json.dumps(row, ensure_ascii=False, default=str) + '\n')
                        count += 1
                    
                    if count == 0:
                        break
                    
                    total_count += count
                    
                    if total_count % 1000 == 0:
                        self.stdout.write(f"  {table_name}: {total_count} registros...")
                    
                    if count < settings.EXPORT_PAGE_SIZE:
                        break
        finally:
            cursor.close()
        
        return total_count
