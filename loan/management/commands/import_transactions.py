import csv
from django.core.management.base import BaseCommand
from loan.models.user import User
from loan.models.transaction import Transaction

class Command(BaseCommand):
    help = 'Import transactions from a CSV file.'

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str)

    def handle(self, *args, **kwargs):
        csv_file = kwargs['csv_file']

        with open(csv_file, newline='') as file:
            reader = csv.DictReader(file)
            for row in reader:
                try:
                    user = User.objects.get(aadhar_id=row['user'])
                    transaction = Transaction(
                        user=user,
                        date=row['date'],
                        transaction_type=row['transaction_type'],
                        amount=row['amount']
                    )
                    transaction.save()
                    self.stdout.write(self.style.SUCCESS(f"Transaction for user {user.aadhar_id} saved successfully."))
                except User.DoesNotExist:
                    self.stdout.write(self.style.ERROR(f"User with AADHAR ID {row['user']} does not exist"))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"Failed to save transaction: {e}"))
