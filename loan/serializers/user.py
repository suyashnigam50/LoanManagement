from rest_framework import serializers
from loan.models.user import User
from loan.serializers.transaction import TransactionSerializer  # Import TransactionSerializer

class UserSerializer(serializers.ModelSerializer):
    transactions = TransactionSerializer(many=True, read_only=True)

    class Meta:
        model = User
        fields = ['id', 'name', 'email_id', 'aadhar_id', 'annual_income', 'transactions']  # Include 'transactions' here
