from rest_framework import serializers
from loan.models.user import User
from loan.models.loan import Loan


class LoanSerializer(serializers.ModelSerializer):
    aadhar_id = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())

    class Meta:
        model = Loan
        fields = ['aadhar_id', 'loan_type', 'loan_amount', 'interest_rate', 'term_period', 'disbursement_date']
