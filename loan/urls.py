from django.urls import path
from .views import ApplyLoanView, MakePaymentView, GetStatementView, RegisterUserView , ListUsersView

urlpatterns = [
    path('register-user/', RegisterUserView.as_view(), name='register-user'),
    path('apply-loan/', ApplyLoanView.as_view(), name='apply-loan'),
    path('make-payment/', MakePaymentView.as_view(), name='make-payment'),
    path('get-statement/<str:loan_id>/', GetStatementView.as_view(), name='get-statement'),
    path('users/', ListUsersView.as_view(), name='list-users'),

]
