from django.shortcuts import render
from django.http import HttpResponse

# Create your views here.
def order_list(request):
    return HttpResponse("Halaman List Order")

def order_detail(request, pk):
    return HttpResponse("Halaman Detail Order")