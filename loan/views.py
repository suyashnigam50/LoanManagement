from rest_framework import generics, status
from rest_framework.response import Response
from loan.models.user import User
from loan.models.loan import Loan
from loan.models.payment import Payment
from django.utils.dateparse import parse_date
import math
from decimal import Decimal, getcontext
from datetime import timedelta, date

from loan.serializers import UserSerializer, LoanSerializer, PaymentSerializer
from loan.tasks import calculate_credit_score
from loan.utils import calculate_emis
from loan.models.emi import EMI
from loan.serializers.emi import EMISerializer
from django.utils.dateparse import parse_date
getcontext().prec = 28



class RegisterUserView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def perform_create(self, serializer):
        user = serializer.save()
        calculate_credit_score.delay(user.aadhar_id)  # Trigger async credit score calculation task

import logging

logger = logging.getLogger(__name__)

class ApplyLoanView(generics.CreateAPIView):
    queryset = Loan.objects.all()
    serializer_class = LoanSerializer

    def create(self, request, *args, **kwargs):
        try:
            logger.debug(f"Request data: {request.data}")

            aadhar_id = request.data.get('aadhar_id')
            if not aadhar_id:
                return Response({'error': 'aadhar_id is required.'}, status=status.HTTP_400_BAD_REQUEST)

            # Fetch the user by aadhar_id
            try:
                user = User.objects.get(aadhar_id=aadhar_id)
            except User.DoesNotExist:
                return Response({'error': 'User does not exist.'}, status=status.HTTP_400_BAD_REQUEST)

            if user.credit_score < 0 or user.annual_income < 150000:
                logger.info(f"User {user.aadhar_id} has a credit score of {user.credit_score}.")
                return Response({'error': 'Loan cannot be approved. Credit score or income does not meet requirements.'}, status=status.HTTP_400_BAD_REQUEST)

            loan_type = request.data['loan_type']
            loan_amount = (request.data['loan_amount'])  

            max_loan_amounts = {
                'Car': 750000,
                'Home': 8500000,
                'Education': 5000000,
                'Personal': 1000000
            }

            if loan_amount > max_loan_amounts.get(loan_type, 0):
                return Response({'error': f'Loan amount exceeds limit for {loan_type} loan.'}, status=status.HTTP_400_BAD_REQUEST)

            term_period = int(request.data['term_period'])
            interest_rate = Decimal(request.data['interest_rate']) 
            disbursement_date = parse_date(request.data['disbursement_date'])

            # Simple EMI calculation
            monthly_interest_rate = Decimal(interest_rate) / Decimal(100) / Decimal(12)

            # Use Decimal's power method instead of math.pow
            one_plus_rate = Decimal(1) + monthly_interest_rate
            emi_amount = loan_amount * monthly_interest_rate * one_plus_rate ** Decimal(term_period) / (one_plus_rate ** Decimal(term_period) - Decimal(1))

            # EMI amount must be at-most 60% of the monthly income of the User
            monthly_income = Decimal(user.annual_income) / Decimal(12)

            # Calculate 60% of the monthly income
            max_emi_amount = monthly_income * Decimal(0.6)

            # Compare the calculated EMI amount with the 60% threshold
            if emi_amount > max_emi_amount:
                return Response({'error': 'EMI amount exceeds 60% of user\'s monthly income.'}, status=status.HTTP_400_BAD_REQUEST)

            # Calculate EMI details
            emis = []
            for i in range(1, term_period + 1):
                emi_date = disbursement_date + timedelta(days=i * 30)
                emis.append({
                    "due_date": emi_date,
                    "amount_due": emi_amount if i != term_period else (emi_amount + loan_amount * monthly_interest_rate * Decimal(term_period - i + 1))
                })

            loan = Loan.objects.create(
                user=user,
                loan_type=loan_type,
                loan_amount=loan_amount,
                interest_rate=interest_rate,
                term_period=term_period,
                disbursement_date=disbursement_date
            )

            emi_objects = [EMI(loan=loan, due_date=emi['due_date'], amount_due=emi['amount_due']) for emi in emis]
            EMI.objects.bulk_create(emi_objects)

            emi_serializer = EMISerializer(emi_objects, many=True)
            return Response({
                'Loan_id': loan.loan_id,
                'Due_dates': emi_serializer.data
            }, status=status.HTTP_201_CREATED)

        except KeyError as e:
            logger.error(f"KeyError: {str(e)}")
            return Response({'error': f'Missing key: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            return Response({'error': 'An unexpected error occurred. Please try again later.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class MakePaymentView(generics.CreateAPIView):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer

    def create(self, request, *args, **kwargs):
        try:
            loan_id = request.data.get('loan_id')
            payment_date = parse_date(request.data.get('payment_date'))
            amount = Decimal(request.data.get('amount'))

            # Fetch the loan and the next due EMI
            loan = Loan.objects.get(loan_id=loan_id)
            emi = EMI.objects.filter(loan=loan, amount_paid__isnull=True).order_by('due_date').first()

            # Reject if payment is already made for that date
            if emi and emi.due_date == payment_date:
                if emi.amount_paid is not None:
                    return Response({'error': 'Payment is already made for this date.'}, status=status.HTTP_400_BAD_REQUEST)

            # Reject if previous EMIs are due
            if EMI.objects.filter(loan=loan, amount_paid__isnull=True, due_date__lt=emi.due_date).exists():
                return Response({'error': 'Previous EMIs are due. Please clear those before making this payment.'}, status=status.HTTP_400_BAD_REQUEST)

            # If the amount paid is less/more than the due amount, adjust the EMI
            if amount < emi.amount_due:
                remaining_amount = emi.amount_due - amount
                emi.amount_paid = amount
                emi.save()

                # Create a new EMI for the remaining amount
                new_emi = EMI.objects.create(
                    loan=loan,
                    due_date=emi.due_date + timedelta(days=30),
                    amount_due=remaining_amount,
                    amount_paid=None
                )
            elif amount > emi.amount_due:
                extra_payment = amount - emi.amount_due
                emi.amount_paid = emi.amount_due
                emi.save()

                # Apply the extra payment to the next EMI or principal
                next_emi = EMI.objects.filter(loan=loan, amount_paid__isnull=True).order_by('due_date').first()
                if next_emi:
                    next_emi.amount_due -= extra_payment
                    if next_emi.amount_due <= 0:
                        next_emi.amount_paid = -next_emi.amount_due
                    next_emi.save()
                else:
                    loan.loan_amount -= extra_payment
                    loan.save()
            else:
                emi.amount_paid = amount
                emi.save()

            return Response({'message': 'Payment processed successfully.'}, status=status.HTTP_200_OK)

        except Loan.DoesNotExist:
            return Response({'error': 'Loan does not exist.'}, status=status.HTTP_400_BAD_REQUEST)

        except EMI.DoesNotExist:
            return Response({'error': 'No EMIs due for this loan.'}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
class GetStatementView(generics.RetrieveAPIView):
    queryset = Loan.objects.all()
    serializer_class = LoanSerializer
    lookup_field = 'loan_id'

    def retrieve(self, request, *args, **kwargs):
        try:
            loan = self.get_object()

            past_transactions = EMI.objects.filter(loan=loan, amount_paid__isnull=False).order_by('due_date')
            past_transactions_serializer = EMISerializer(past_transactions, many=True)

            upcoming_transactions = EMI.objects.filter(loan=loan, amount_paid__isnull=True).order_by('due_date')
            upcoming_transactions_serializer = EMISerializer(upcoming_transactions, many=True)

            return Response({
                'Loan_id': loan.loan_id,
                'Past_transactions': past_transactions_serializer.data,
                'Upcoming_transactions': upcoming_transactions_serializer.data
            }, status=status.HTTP_200_OK)

        except Loan.DoesNotExist:
            return Response({'error': 'Loan does not exist.'}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ListUsersView(generics.ListAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer

