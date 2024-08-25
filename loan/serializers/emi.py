from rest_framework import serializers
from loan.models.emi import EMI

class EMISerializer(serializers.ModelSerializer):
    class Meta:
        model = EMI
        fields = '__all__'
