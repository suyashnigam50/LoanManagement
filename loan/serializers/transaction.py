from rest_framework import serializers
from loan.models.transaction import Transaction

class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = ['date', 'amount', 'transaction_type']
