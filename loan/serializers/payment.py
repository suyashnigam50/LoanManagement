from rest_framework import serializers
from loan.models.payment import Payment

class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ['loan', 'date', 'amount_paid']
