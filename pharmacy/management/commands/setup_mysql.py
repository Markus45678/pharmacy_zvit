import os
import pymysql
from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.conf import settings


class Command(BaseCommand):
    help = "Ініціалізує та налаштовує базу даних MySQL, запускає міграції та наповнює даними"

    def add_arguments(self, parser):
        parser.add_argument('--password', type=str, default=None, help='Пароль користувача root в MySQL')
        parser.add_argument('--database', type=str, default='pharmacy_db', help='Назва створюваної бази даних')

    def handle(self, *args, **options):
        db_name = options['database']
        db_user = os.getenv('DB_USER', 'root')
        db_host = os.getenv('DB_HOST', '127.0.0.1')
        db_port = int(os.getenv('DB_PORT', '3306'))
        db_pass = options['password'] if options['password'] is not None else os.getenv('DB_PASSWORD', '')

        self.stdout.write(f"Connecting to MySQL server at {db_host}:{db_port} as user '{db_user}'...")

        try:
            conn = pymysql.connect(
                host=db_host,
                port=db_port,
                user=db_user,
                password=db_pass
            )
            with conn.cursor() as cursor:
                cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{db_name}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
                self.stdout.write(self.style.SUCCESS(f"Database `{db_name}` ensured in MySQL!"))
            conn.close()

            if options['password'] is not None:
                env_path = os.path.join(settings.BASE_DIR, '.env')
                lines = []
                if os.path.exists(env_path):
                    with open(env_path, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                
                updated = False
                new_lines = []
                for line in lines:
                    if line.startswith('DB_PASSWORD='):
                        new_lines.append(f"DB_PASSWORD={db_pass}\n")
                        updated = True
                    else:
                        new_lines.append(line)
                if not updated:
                    new_lines.append(f"DB_PASSWORD={db_pass}\n")

                with open(env_path, 'w', encoding='utf-8') as f:
                    f.writelines(new_lines)
                self.stdout.write(self.style.SUCCESS(".env updated with the new DB_PASSWORD."))

            self.stdout.write("Running migrations on MySQL...")
            call_command('migrate')
            self.stdout.write("Seeding data into MySQL...")
            call_command('seed_data')
            self.stdout.write(self.style.SUCCESS("All done! MySQL is completely setup and seeded."))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Failed to setup MySQL: {e}"))
