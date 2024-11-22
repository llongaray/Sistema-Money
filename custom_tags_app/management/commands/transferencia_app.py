from django.core.management.base import BaseCommand
from django.apps import apps
from django.db import connections
import sqlite3
import logging
import os
from datetime import datetime
from InquirerPy import inquirer
from InquirerPy.base.control import Choice
from InquirerPy.separator import Separator

class Command(BaseCommand):
    help = 'Transfere dados das tabelas de um app entre bancos de dados SQLite'

    def add_arguments(self, parser):
        parser.add_argument('--backup', action='store_true', 
                          help='Cria backup do banco de destino antes da transferência')
        parser.add_argument('--log', action='store_true',
                          help='Gera arquivo de log da operação')
        parser.add_argument('--force', action='store_true',
                          help='Força a transferência sem confirmação')
        parser.add_argument('--limpar', action='store_true',
                          help='Limpa as tabelas de destino antes da transferência')
        parser.add_argument('--limpar_rest_sequenci', action='store_true',
                          help='Reseta as sequências das tabelas após limpeza')
        parser.add_argument('--origem', type=str, help='Caminho do banco de dados de origem')
        parser.add_argument('--destino', type=str, help='Caminho do banco de dados de destino')

    def setup_logging(self):
        if not os.path.exists('logs'):
            os.makedirs('logs')
        
        log_file = f'logs/transferencia_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
        logging.basicConfig(
            filename=log_file,
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )

    def get_apps_with_tables(self):
        """Retorna apenas os apps que possuem tabelas no banco de origem"""
        cursor = self.source_conn.cursor()
        
        # Obtém todas as tabelas do banco
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
        all_tables = [table[0] for table in cursor.fetchall()]
        
        # Agrupa as tabelas por app (considerando o prefixo antes do '_')
        apps_with_tables = {}
        for table in all_tables:
            if '_' in table:
                app_name = table.split('_')[0]
                if app_name not in apps_with_tables:
                    apps_with_tables[app_name] = []
                apps_with_tables[app_name].append(table)
        
        return apps_with_tables

    def handle(self, *args, **options):
        if options['log']:
            self.setup_logging()

        # Solicita os caminhos dos bancos se não fornecidos como argumentos
        db_origem = options.get('origem') or input("Digite o caminho do banco de dados de origem (db.sqlite3): ")
        db_destino = options.get('destino') or input("Digite o caminho do banco de dados de destino (db.sqlite3): ")

        # Valida se os arquivos existem
        if not os.path.exists(db_origem):
            self.stdout.write(self.style.ERROR(f'Banco de dados de origem não encontrado: {db_origem}'))
            return
        if not os.path.exists(db_destino):
            self.stdout.write(self.style.ERROR(f'Banco de dados de destino não encontrado: {db_destino}'))
            return

        # Configura as conexões dinamicamente
        self.source_conn = sqlite3.connect(db_origem)
        self.dest_conn = sqlite3.connect(db_destino)

        # Lista apenas os apps que têm tabelas no banco
        apps_with_tables = self.get_apps_with_tables()
        
        if not apps_with_tables:
            self.stdout.write(self.style.ERROR('Nenhum app com tabelas encontrado no banco de origem'))
            return

        # Prepara as escolhas para o InquirerPy
        choices = []
        for app_name, tables in apps_with_tables.items():
            choices.append(Choice(app_name, name=f"{app_name} ({len(tables)} tabelas)"))
            choices.append(Separator("   Tabelas:"))
            for table in tables:
                choices.append(Separator(f"      - {table}"))
            choices.append(Separator())

        # Solicita escolha do app usando InquirerPy
        selected_app = inquirer.select(
            message="Selecione o app para transferência:",
            choices=choices,
            default=None,
            qmark="🔄",
            amark="✓"
        ).execute()

        app_tables = apps_with_tables[selected_app]

        # Nova lógica para escolher entre transferir todas as tabelas ou selecionar uma
        modo_transferencia = inquirer.select(
            message="Como deseja realizar a transferência?",
            choices=[
                Choice("todas", name="1. Transferir todas as tabelas do app"),
                Choice("uma", name="2. Selecionar apenas uma tabela")
            ],
            default="todas",
            qmark="📋",
            amark="✓"
        ).execute()

        if modo_transferencia == "uma":
            # Prepara as escolhas apenas com as tabelas do app selecionado
            table_choices = [Choice(table, name=table) for table in app_tables]
            selected_table = inquirer.select(
                message="Selecione a tabela para transferência:",
                choices=table_choices,
                qmark="📋",
                amark="✓"
            ).execute()
            app_tables = [selected_table]

        # Backup do banco de destino se solicitado
        if options['backup']:
            self.criar_backup()

        if not options['force']:
            confirm = input(f"\nTransferir dados das tabelas: {', '.join(app_tables)}? (s/N): ")
            if confirm.lower() != 's':
                self.stdout.write(self.style.WARNING('Operação cancelada'))
                return

        # Transferência dos dados
        for table in app_tables:
            try:
                # Verifica se a tabela existe no destino
                dest_cursor = self.dest_conn.cursor()
                dest_cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
                tabela_existe = dest_cursor.fetchone() is not None

                if tabela_existe:
                    # Limpa e reseta a tabela
                    registros_removidos = self.limpar_tabela(table)
                    self.stdout.write(f"Tabela {table}: {registros_removidos} registros removidos")
                
                # Transfere os dados
                registros_transferidos = self.transferir_dados(table)
                
                self.stdout.write(self.style.SUCCESS(
                    f'Tabela {table}: {registros_transferidos} registros transferidos com sucesso'
                ))
                
                if options['log']:
                    logging.info(
                        f'Tabela {table}: {registros_removidos if tabela_existe else 0} registros removidos, '
                        f'{registros_transferidos} registros transferidos'
                    )
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Erro ao transferir tabela {table}: {str(e)}'))
                if options['log']:
                    logging.error(f'Erro ao transferir tabela {table}: {str(e)}')

    def criar_backup(self):
        """Cria backup do banco de destino"""
        dest_db_path = self.dest_conn.cursor().execute("PRAGMA database_list").fetchall()[0][1]
        backup_path = f"{dest_db_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        with open(dest_db_path, 'rb') as src, open(backup_path, 'wb') as dst:
            dst.write(src.read())

    def limpar_tabela(self, table_name):
        """Limpa a tabela e reseta a sequência, retornando o número de registros removidos"""
        cursor = self.dest_conn.cursor()
        
        # Conta registros antes de limpar
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        registros_removidos = cursor.fetchone()[0]
        
        # Limpa a tabela
        cursor.execute(f"DELETE FROM {table_name}")
        
        # Reseta a sequência
        cursor.execute(f"DELETE FROM sqlite_sequence WHERE name='{table_name}'")
        
        self.dest_conn.commit()
        return registros_removidos

    def get_column_info(self, connection, table_name):
        """Retorna informações detalhadas das colunas de uma tabela"""
        cursor = connection.cursor()
        cursor.execute(f"PRAGMA table_info({table_name})")
        return {info[1]: {'type': info[2], 'notnull': info[3], 'dflt_value': info[4]} 
                for info in cursor.fetchall()}

    def add_missing_columns(self, table_name, missing_columns):
        """Adiciona colunas faltantes na tabela de destino"""
        cursor = self.dest_conn.cursor()
        source_columns = self.get_column_info(self.source_conn, table_name)
        
        for column in missing_columns:
            col_info = source_columns[column]
            sql = f"ALTER TABLE {table_name} ADD COLUMN {column} {col_info['type']}"
            
            # Adiciona constraints se necessário
            if col_info['notnull']:
                if col_info['dflt_value'] is not None:
                    sql += f" NOT NULL DEFAULT {col_info['dflt_value']}"
                else:
                    sql += f" NOT NULL DEFAULT ''"
            
            cursor.execute(sql)
        self.dest_conn.commit()

    def transferir_dados(self, table_name):
        """Transfere dados da tabela entre os bancos"""
        source_cursor = self.source_conn.cursor()
        dest_cursor = self.dest_conn.cursor()

        # Obtém informações das colunas de ambas as tabelas
        source_columns = set(self.get_column_info(self.source_conn, table_name).keys())
        dest_columns = set(self.get_column_info(self.dest_conn, table_name).keys())
        
        # Identifica colunas faltantes no destino
        missing_in_dest = source_columns - dest_columns
        
        # Adiciona colunas faltantes no destino
        if missing_in_dest:
            self.stdout.write(self.style.WARNING(
                f"Adicionando colunas faltantes no destino: {', '.join(missing_in_dest)}"
            ))
            self.add_missing_columns(table_name, missing_in_dest)
            dest_columns.update(missing_in_dest)
        
        # Identifica colunas que existem apenas no destino
        only_in_dest = dest_columns - source_columns
        if only_in_dest:
            self.stdout.write(self.style.WARNING(
                f"Colunas ignoradas (existem apenas no destino): {', '.join(only_in_dest)}"
            ))

        # Usa todas as colunas do origem para transferência
        columns = list(source_columns)
        columns_str = ','.join(columns)
        
        # Obtém dados da tabela fonte
        source_cursor.execute(f"SELECT {columns_str} FROM {table_name}")
        rows = source_cursor.fetchall()

        registros_transferidos = 0
        if rows:
            # Prepara a query de inserção
            placeholders = ','.join(['?' for _ in columns])
            
            # Insere dados na tabela de destino
            dest_cursor.executemany(
                f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders})",
                rows
            )
            self.dest_conn.commit()
            registros_transferidos = len(rows)

        return registros_transferidos

    def __del__(self):
        """Fecha as conexões quando o objeto é destruído"""
        if hasattr(self, 'source_conn'):
            self.source_conn.close()
        if hasattr(self, 'dest_conn'):
            self.dest_conn.close()
