from django.shortcuts import render

# Create your views here.

from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.template import RequestContext

def index(request):
    context = {}
    return render(request, 'glicko/index.html', context)

def results(request):
    username = request.POST['user_name']
    context= {}
    context['username'] = username
    return render(request, 'glicko/results.html', context)