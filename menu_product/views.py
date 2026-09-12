from django.shortcuts import render
# from django.http import HttpResponse
# from .models import Product

# Create your views here.
def product_list(request):
    return render(request, 'hello.html')
