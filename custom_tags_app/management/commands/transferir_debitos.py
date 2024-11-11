from django.core.management.base import BaseCommand
from django.db import connections, transaction
from apps.siape.models import DebitoMargem, Cliente, Campanha
import sqlite3
from datetime import datetime
import os

class Command(BaseCommand):
    help = 'Transfere registros de DebitoMargem de um banco SQLite para outro'

    def add_arguments(self, parser):
        parser.add_argument(
            '--origem',
            type=str,
            required=True,
            help='Caminho para o arquivo SQLite de origem'
        )
        parser.add_argument(
            '--destino',
            type=str,
            required=True,
            help='Caminho para o arquivo SQLite de destino'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Força a transferência sem pedir confirmação'
        )
        parser.add_argument(
            '--log',
            action='store_true',
            help='Gera arquivo de log da transferência'
        )

    def handle(self, *args, **options):
        origem_path = options['origem']
        destino_path = options['destino']
        
        # Verifica se os arquivos existem
        if not os.path.exists(origem_path):
            self.stdout.write(self.style.ERROR(f'Arquivo de origem não encontrado: {origem_path}'))
            return
        if not os.path.exists(destino_path):
            self.stdout.write(self.style.ERROR(f'Arquivo de destino não encontrado: {destino_path}'))
            return

        # Prepara arquivo de log se necessário
        log_file = None
        if options['log']:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            log_file = open(f'transferencia_debitos_{timestamp}.log', 'w')
            self.log(log_file, f'Iniciando transferência em {datetime.now()}')

        try:
            # Conecta aos bancos
            origem_conn = sqlite3.connect(origem_path)
            origem_cursor = origem_conn.cursor()

            # Conta registros na origem
            origem_cursor.execute('SELECT COUNT(*) FROM siape_debitomargem')
            total_registros = origem_cursor.fetchone()[0]

            if not options['force']:
                confirmacao = input(f'\nSerão transferidos {total_registros} registros.\nDeseja continuar? (sim/não): ')
                if confirmacao.lower() not in ['sim', 's', 'yes', 'y']:
                    self.stdout.write(self.style.WARNING('Operação cancelada pelo usuário.'))
                    return

            self.stdout.write(f'Iniciando transferência de {total_registros} registros...')

            # Obtém todos os registros da origem
            origem_cursor.execute('''
                SELECT 
                    dm.id, dm.banco, dm.orgao, dm.matricula, dm.upag, dm.pmt, 
                    dm.prazo, dm.contrato, dm.saldo_5, dm.beneficio_5, 
                    dm.benef_util_5, dm.benef_saldo_5, dm.bruta_35, dm.util_35,
                    dm.saldo_35, dm.bruta_70, dm.saldo_70, dm.rend_bruto,
                    dm.data_envio, c.cpf, camp.id
                FROM siape_debitomargem dm
                LEFT JOIN siape_cliente c ON dm.cliente_id = c.id
                LEFT JOIN siape_campanha camp ON dm.campanha_id = camp.id
            ''')

            registros = origem_cursor.fetchall()
            transferidos = 0
            erros = 0

            # Processa em lotes
            BATCH_SIZE = 1000
            with transaction.atomic():
                for i in range(0, len(registros), BATCH_SIZE):
                    batch = registros[i:i + BATCH_SIZE]
                    for registro in batch:
                        try:
                            # Encontra ou cria o cliente no destino
                            cpf = registro[19]  # índice do CPF na query
                            cliente = Cliente.objects.get(cpf=cpf)
                            
                            # Encontra a campanha no destino
                            campanha_id = registro[20]  # índice do campanha_id na query
                            campanha = Campanha.objects.get(id=campanha_id)

                            # Cria o novo registro de débito
                            debito = DebitoMargem(
                                cliente=cliente,
                                campanha=campanha,
                                banco=registro[1],
                                orgao=registro[2],
                                matricula=registro[3],
                                upag=registro[4],
                                pmt=registro[5],
                                prazo=registro[6],
                                contrato=registro[7],
                                saldo_5=registro[8],
                                beneficio_5=registro[9],
                                benef_util_5=registro[10],
                                benef_saldo_5=registro[11],
                                bruta_35=registro[12],
                                util_35=registro[13],
                                saldo_35=registro[14],
                                bruta_70=registro[15],
                                saldo_70=registro[16],
                                rend_bruto=registro[17],
                                data_envio=registro[18]
                            )
                            debito.save()
                            transferidos += 1

                            if log_file:
                                self.log(log_file, f'Registro transferido: Cliente {cpf}, Contrato {registro[7]}')

                        except Exception as e:
                            erros += 1
                            if log_file:
                                self.log(log_file, f'ERRO: Cliente {cpf}, Contrato {registro[7]}: {str(e)}')
                            continue

                    self.stdout.write(f'Processados {i + len(batch)} de {total_registros} registros...')

            # Resultado final
            self.stdout.write(self.style.SUCCESS(
                f'\nTransferência concluída!\n'
                f'Total de registros: {total_registros}\n'
                f'Transferidos com sucesso: {transferidos}\n'
                f'Erros: {erros}'
            ))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Erro durante a transferência: {str(e)}'))
            if log_file:
                self.log(log_file, f'ERRO FATAL: {str(e)}')
        
        finally:
            origem_conn.close()
            if log_file:
                log_file.close()

    def log(self, file, message):
        """Função auxiliar para escrever no arquivo de log"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        file.write(f'[{timestamp}] {message}\n')
        file.flush()