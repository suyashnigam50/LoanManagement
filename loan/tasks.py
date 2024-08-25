from celery import shared_task
from .models.user import User
from .models.transaction import Transaction

@shared_task
def calculate_credit_score(aadhar_id):
    user = User.objects.get(aadhar_id=aadhar_id)
    transactions = Transaction.objects.filter(user=user)

    balance = sum([t.amount if t.transaction_type == 'CREDIT' else -t.amount for t in transactions])
    
    if balance >= 1000000:
        user.credit_score = 900
    elif balance <= 100000:
        user.credit_score = 300
    else:
        user.credit_score = 300 + ((balance - 100000) // 15000) * 10
    
    user.save()
