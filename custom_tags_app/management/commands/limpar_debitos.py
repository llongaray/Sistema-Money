from django.core.management.base import BaseCommand
from django.db import transaction
from apps.siape.models import DebitoMargem
from datetime import datetime

class Command(BaseCommand):
    help = 'Limpa todos os registros da tabela DebitoMargem'

    def add_arguments(self, parser):
        # Argumento opcional para backup antes de limpar
        parser.add_argument(
            '--backup',
            action='store_true',
            help='Criar backup dos dados antes de limpar',
        )
        
        # Argumento opcional para confirmar a ação
        parser.add_argument(
            '--force',
            action='store_true',
            help='Força a limpeza sem pedir confirmação',
        )

    def handle(self, *args, **options):
        try:
            # Conta total de registros
            total_registros = DebitoMargem.objects.count()
            
            if not options['force']:
                # Pede confirmação do usuário
                confirmacao = input(f'\nATENÇÃO: Isso irá deletar {total_registros} registros da tabela DebitoMargem.\nTem certeza que deseja continuar? (sim/não): ')
                if confirmacao.lower() not in ['sim', 's', 'yes', 'y']:
                    self.stdout.write(self.style.WARNING('Operação cancelada pelo usuário.'))
                    return

            # Backup opcional
            if options['backup']:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f'backup_debitos_{timestamp}.csv'
                
                self.stdout.write(f'Criando backup em {filename}...')
                
                # Exporta dados para CSV
                import csv
                with open(filename, 'w', newline='') as f:
                    writer = csv.writer(f)
                    # Escreve cabeçalho
                    fields = [field.name for field in DebitoMargem._meta.fields]
                    writer.writerow(fields)
                    
                    # Escreve dados em lotes de 1000
                    queryset = DebitoMargem.objects.all().iterator()
                    batch = []
                    for obj in queryset:
                        row = [getattr(obj, field) for field in fields]
                        writer.writerow(row)
                
                self.stdout.write(self.style.SUCCESS(f'Backup criado com sucesso em {filename}'))

            # Deleta os registros usando transaction
            with transaction.atomic():
                self.stdout.write('Iniciando limpeza da tabela...')
                DebitoMargem.objects.all().delete()
                self.stdout.write(self.style.SUCCESS(f'Tabela limpa com sucesso! {total_registros} registros foram removidos.'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Erro ao limpar tabela: {str(e)}'))
            raise
