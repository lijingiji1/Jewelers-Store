import django
from django.contrib.auth.models import User
from store.models import Address, Cart, Category, Order, Product
from django.shortcuts import redirect, render, get_object_or_404
from .forms import RegistrationForm, AddressForm
from django.contrib import messages
from django.views import View
import decimal
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator # for Class Based Views
from .models import Creditcard as CC

from .forms import CreditcardForm
import paypalrestsdk
from django.conf import settings
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views import View
from django.shortcuts import render
import razorpay
from django.conf import settings  
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponseBadRequest
from django.views import View
import http.client



# Create your views here.

def home(request):
    categories = Category.objects.filter(is_active=True, is_featured=True)[:3]
    products = Product.objects.filter(is_active=True, is_featured=True)[:8]
    context = {
        'categories': categories,
        'products': products,
    }
    return render(request, 'store/index.html', context)


def detail(request, slug):
    product = get_object_or_404(Product, slug=slug)
    related_products = Product.objects.exclude(id=product.id).filter(is_active=True, category=product.category)
    context = {
        'product': product,
        'related_products': related_products,

    }
    return render(request, 'store/detail.html', context)


def all_categories(request):
    categories = Category.objects.filter(is_active=True)
    return render(request, 'store/categories.html', {'categories':categories})


def category_products(request, slug):
    category = get_object_or_404(Category, slug=slug)
    products = Product.objects.filter(is_active=True, category=category)
    categories = Category.objects.filter(is_active=True)
    context = {
        'category': category,
        'products': products,
        'categories': categories,
    }
    return render(request, 'store/category_products.html', context)


# Authentication Starts Here

class RegistrationView(View):
    def get(self, request):
        form = RegistrationForm()
        return render(request, 'account/register.html', {'form': form})
    
    def post(self, request):
        form = RegistrationForm(request.POST)
        if form.is_valid():
            messages.success(request, "Congratulations! Registration Successful!")
            form.save()
        return render(request, 'account/register.html', {'form': form})
        

@login_required
def profile(request):
    addresses = Address.objects.filter(user=request.user)
    orders = Order.objects.filter(user=request.user)
    return render(request, 'account/profile.html', {'addresses':addresses, 'orders':orders})


@method_decorator(login_required, name='dispatch')
class AddressView(View):
    def get(self, request):
        form = AddressForm()
        return render(request, 'account/add_address.html', {'form': form})

    def post(self, request):
        form = AddressForm(request.POST)
        if form.is_valid():
            user=request.user
            locality = form.cleaned_data['locality']
            city = form.cleaned_data['city']
            state = form.cleaned_data['state']
            reg = Address(user=user, locality=locality, city=city, state=state)
            reg.save()
            messages.success(request, "New Address Added Successfully.")
        return redirect('store:profile')


@login_required
def remove_address(request, id):
    a = get_object_or_404(Address, user=request.user, id=id)
    a.delete()
    messages.success(request, "Address removed.")
    return redirect('store:profile')

@login_required
def add_to_cart(request):
    user = request.user
    product_id = request.GET.get('prod_id')
    product = get_object_or_404(Product, id=product_id)

    # Check whether the Product is alread in Cart or Not
    item_already_in_cart = Cart.objects.filter(product=product_id, user=user)
    if item_already_in_cart:
        cp = get_object_or_404(Cart, product=product_id, user=user)
        cp.quantity += 1
        cp.save()
    else:
        Cart(user=user, product=product).save()
    
    return redirect('store:cart')


@login_required
def cart(request):
    user = request.user
    cart_products = Cart.objects.filter(user=user)

    # Display Total on Cart Page
    amount = decimal.Decimal(0)
    shipping_amount = decimal.Decimal(10)
    # using list comprehension to calculate total amount based on quantity and shipping
    cp = [p for p in Cart.objects.all() if p.user==user]
    if cp:
        for p in cp:
            temp_amount = (p.quantity * p.product.price)
            amount += temp_amount

    # Customer Addresses
    addresses = Address.objects.filter(user=user)

    context = {
        'cart_products': cart_products,
        'amount': amount,
        'shipping_amount': shipping_amount,
        'total_amount': amount + shipping_amount,
        'addresses': addresses,
    }
    return render(request, 'store/cart.html', context)


@login_required
def remove_cart(request, cart_id):
    if request.method == 'GET':
        c = get_object_or_404(Cart, id=cart_id)
        c.delete()
        messages.success(request, "Product removed from Cart.")
    return redirect('store:cart')


@login_required
def plus_cart(request, cart_id):
    if request.method == 'GET':
        cp = get_object_or_404(Cart, id=cart_id)
        cp.quantity += 1
        cp.save()
    return redirect('store:cart')


@login_required
def minus_cart(request, cart_id):
    if request.method == 'GET':
        cp = get_object_or_404(Cart, id=cart_id)
        # Remove the Product if the quantity is already 1
        if cp.quantity == 1:
            cp.delete()
        else:
            cp.quantity -= 1
            cp.save()
    return redirect('store:cart')


@login_required
def checkout(request):
    user = request.user
    address = Address.objects.filter(user=user)
    # Get all the products of User in Cart
    cart = Cart.objects.filter(user=user)
    if request.method=="POST":
        id=request.POST.get('address')
        address=get_object_or_404(Address,id=id)
        for c in cart:
            # Saving all the products from Cart to Order
            Order(user=user,address=address,product=c.product, quantity=c.quantity).save()
            # And Deleting from Cart
            c.delete()
        return redirect('store:payment')
    return render(request,"store/checkout.html",{'address':address})

@login_required
def orders(request):
    all_orders = Order.objects.filter(user=request.user).order_by('-ordered_date')
    return render(request, 'store/orders.html', {'orders': all_orders})





def shop(request):
    return render(request, 'store/shop.html')





def test(request):
    return render(request, 'store/test.html')
def payment(request):
    if request.POST:
       
        paymethod = request.POST.get('pay')
       
        if paymethod == 'Cash on Delivary':
            return redirect('store:orders')
        elif paymethod == 'RazorPay':
            return redirect('store:razorpay')
        elif paymethod == 'Paypal':
            return redirect('store:create_payment')
        elif paymethod == 'CreditCard':
            return redirect('store:creditcard')
        return redirect('store:orders')
    return render(request, 'store/payment.html')



   
           

def CreditCard(request):
    if request.method == 'POST': 
        form = CreditcardForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            number = cd['cc_number']
            expiry = cd['cc_expiry']
            code = cd['cc_code']
            card = CC(cc_number=number, cc_expiry=expiry, cc_code=code)
            card.save()
            
            return redirect('store:orders')
    else:
        form = CreditcardForm()
    return render(request, 'store/creditcard.html', {'form': form})


paypalrestsdk.configure({
    "mode": "sandbox",  # Change to "live" for production
    "client_id": settings.PAYPAL_CLIENT_ID,
    "client_secret": settings.PAYPAL_SECRET,
})

def create_payment(request):
    payment = paypalrestsdk.Payment({
        "intent": "sale",
        "payer": {
            "payment_method": "paypal",
        },
        "redirect_urls": {
            "return_url": request.build_absolute_uri(reverse('store:execute_payment')),
            "cancel_url": request.build_absolute_uri(reverse('store:payment_failed')),
        },
        "transactions": [
            {
                "amount": {
                    "total": "10.00",  # Total amount in USD
                    "currency": "USD",
                },
                "description": "Payment for Product/Service",
            }
        ],
    })

    if payment.create():
        return redirect(payment.links[1].href)  # Redirect to PayPal for payment
    else:
        return render(request, 'payment_failed.html')

def execute_payment(request):
    payment_id = request.GET.get('paymentId')
    payer_id = request.GET.get('PayerID')

    payment = paypalrestsdk.Payment.find(payment_id)

    if payment.execute({"payer_id": payer_id}):
        return render(request, 'payment_success.html')
    else:
        return render(request, 'payment_failed.html')

def payment_checkout(request):
    return render(request, 'checkout.html')

def payment_failed(request):
    return render(request, 'payment_failed.html')


# authorize razorpay client with API Keys.
"""
Initializes a Razorpay client with the provided API key ID and API key secret.

The Razorpay client is used to interact with the Razorpay payment gateway API,
which allows you to accept online payments on your website or application.

Args:
    settings.RAZOR_KEY_ID (str): The API key ID provided by Razorpay.
    settings.RAZOR_KEY_SECRET (str): The API key secret provided by Razorpay.

Returns:
    razorpay.Client: A Razorpay client instance that can be used to make API calls.
"""
razorpay_client = razorpay.Client(auth=(settings.RAZOR_KEY_ID, settings.RAZOR_KEY_SECRET))


class Razorpay(View):
	def get(self, request):
		currency = 'INR'
		amount = 100 # Rs. 1

		# Create a Razorpay Order
		razorpay_order = razorpay_client.order.create(dict(amount=amount,
														currency=currency,
														payment_capture='0'))

		# order id of newly created order.
		razorpay_order_id = razorpay_order['id']
		callback_url = 'paymenthandler/'

		# we need to pass these details to frontend.
		context = {}
		context['razorpay_order_id'] = razorpay_order_id
		context['razorpay_merchant_key'] = settings.RAZOR_KEY_ID
		context['razorpay_amount'] = amount
		context['currency'] = currency
		context['callback_url'] = callback_url

		return render(request, 'razorpay.html', context=context)


	# we need to csrf_exempt this url as
	# POST request will be made by Razorpay
	# and it won't have the csrf token.
@csrf_exempt
def paymenthandler(request):

	# only accept POST request.
	if request.method == "POST":
		try:
		
			# get the required parameters from post request.
			payment_id = request.POST.get('razorpay_payment_id', '')
			razorpay_order_id = request.POST.get('razorpay_order_id', '')
			signature = request.POST.get('razorpay_signature', '')
			params_dict = {
				'razorpay_order_id': razorpay_order_id,
				'razorpay_payment_id': payment_id,
				'razorpay_signature': signature
			}

			# verify the payment signature.
			result = razorpay_client.utility.verify_payment_signature(
				params_dict)
			if result is not None:
				amount = 100 # Rs. 1
				try:

					# capture the payemt
					razorpay_client.payment.capture(payment_id, amount)

					# render success page on successful caputre of payment
					return render(request, 'paymentsuccess.html')
				except:

					# if there is an error while capturing payment.
					return render(request, 'paymentfail.html')
			else:

				# if signature verification fails.
				return render(request, 'paymentfail.html')
		except:

			# if we don't find the required parameters in POST data
			return HttpResponseBadRequest()
	else:
	# if other than POST request is made.
		return HttpResponseBadRequest()

