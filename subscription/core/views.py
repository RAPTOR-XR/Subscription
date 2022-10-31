from django.shortcuts import render, redirect
from django.contrib.auth.hashers import make_password
from django.http import JsonResponse
from django.contrib import auth
from django.http import HttpResponseRedirect
from django.conf import settings
from datetime import timedelta
from datetime import datetime as dt
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from . models import *
from . serializers import RegisterSerializer

import requests
import json


'''
For assigning and validation of the number, first the generated numbers will be stored in a table of the database.
The random numbers will be generated in a loop and will check if the number is already in the database or not.
'''


def index(request):
    return render(request, 'index.html')

def check_mail_ajax(request):
    if request.is_ajax():
        email = request.GET.get('email', None)
        check_email = User.objects.filter(email=email).exists()
        if check_email:
            response = {'error': 'Email already exists'}
            return JsonResponse(response)
        else:
            response = {'success': 'Email available'}
            return JsonResponse(response)
    else:
        return JsonResponse({'error': 'Invalid request'})

'''
check if number is valid and unique
'''

def check_phone_ajax(request):
	if request.is_ajax():
		phone = request.GET.get('phone', None)
		check_phone = User.objects.filter(phone=phone).exists()
		if check_phone:
			response = {'error': 'Phone number already exists'}
			return JsonResponse(response)
		else:
			response = {'success': 'Phone number available'}
			return JsonResponse(response)
	else:
		return JsonResponse({'error': 'Invalid request'})

def signin(request):
	return render(request, 'login.html')


class Register(APIView):
	def post(self, request):
		serializer = RegisterSerializer(data=request.data)
		if serializer.is_valid():
			serializer.save()
			obj = serializer.save()
			password = make_password(serializer.data['password'])
			User.objects.filter(email=serializer.data['email']).update(password=password)
			get_membership = SubscriptionChoices.objects.get(subscription_type='Globalnet Bronze')
			instance = UserSubscription.objects.create(user=obj, membership=get_membership)
			return Response({'success': 'Registration successful.'})
		else:
			return Response({'error': 'Error. Try again'})


class Login(APIView):
	def post(self, request):
		email = request.data.get('email')
		password = request.data.get('password')

		# Let us check if the user exists or not...
		check_email = User.objects.filter(email=email).exists()
		if check_email == False:
			return Response({'error': 'No account with such email'})
		# We need to check if the user password is correct
		user = User.objects.get(email=email)
		if user.check_password(password) == False:
			return Response({'error': 'Password is not correct. Try again'})
		# Now let us log the user in
		log_user = auth.authenticate(email=email, password=password)
		if user is not None:
			auth.login(request, log_user)
			return Response({'success': 'Login successful'})
		else:
			return Response({'error': 'Invalid email/password. Try again later.'})


def subscription(request):
	return render(request, 'subscription.html')

def end_sub(request):
	return render(request, 'sub.html')

def subscribe(request):
	plan = request.GET.get('sub_plan')
	fetch_membership = SubscriptionChoices.objects.filter(subscription_type=plan).exists()
	if fetch_membership == False:
		return redirect('subscribe')
	membership = SubscriptionChoices.objects.get(subscription_type=plan)
	price = float(membership.price)
	price = int(price)

	def init_payment(request):
		url = 'https://checkout.stripe.com/checkout.js'
		headers = {
			'Authorization': 'Bearer '+settings.STRIPE_SECRET_KEY,
			'Content-Type' : 'application/json',
			'Accept': 'application/json',
			}
		datum = {
			"email": request.user.email,
			"amount": price
			}
		x = requests.post(url, data=json.dumps(datum), headers=headers)
		if x.status_code != 200:
			return str(x.status_code)
		
		results = x.json()
		return results
	initialized = init_payment(request)
	print(initialized['data']['authorization_url'])
	amount = price/100
	instance = UserPaymentHistory.objects.create(amount=amount, payment_for=membership, user=request.user, stripe_charge_id=initialized['data']['reference'], stripe_access_code=initialized['data']['access_code'])
	UserSubscription.objects.filter(user=instance.user).update(reference_code=initialized['data']['reference'])
	link = initialized['data']['authorization_url']
	return HttpResponseRedirect(link)
	return render(request, 'subscribe.html')

def call_back_url(request):
	reference = request.GET.get('reference')
	# We need to fetch the reference from PAYMENT
	check_pay = UserPaymentHistory.objects.filter(stripe_charge_id=reference).exists()
	if check_pay == False:
		# This means payment was not made error should be thrown here...
		print("Error")
	else:
		payment = UserPaymentHistory.objects.get(stripe_charge_id=reference)
		# We need to fetch this to verify if the payment was successful.
		def verify_payment(request):
			url = 'https://checkout.stripe.com/checkout.js'+reference
			headers = {
				'Authorization': 'Bearer '+settings.STRIPE_SECRET_KEY,
				'Content-Type' : 'application/json',
				'Accept': 'application/json',
				}
			datum = {
				"reference": payment.stripe_charge_id
				}
			x = requests.get(url, data=json.dumps(datum), headers=headers)
			if x.status_code != 200:
				return str(x.status_code)
			
			results = x.json()
			return results
	initialized = verify_payment(request)
	if initialized['data']['status'] == 'success':
		UserPaymentHistory.objects.filter(stripe_charge_id=initialized['data']['reference']).update(paid=True)
		new_payment = UserPaymentHistory.objects.get(stripe_charge_id=initialized['data']['reference'])
		instance = SubscriptionChoices.objects.get(id=new_payment.payment_for.id)
		sub = UserSubscription.objects.filter(reference_code=initialized['data']['reference']).update(membership=instance)
		user_membership = UserSubscription.objects.get(reference_code=initialized['data']['reference'])
		Subscription.objects.create(user_membership=user_membership, expires_in=dt.now().date() + timedelta(days=user_membership.membership.duration))
		return redirect('subscribed')
	return render(request, 'payment.html')


def subscribed(request):
	return render(request, 'subscribed.html')