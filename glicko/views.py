from django.shortcuts import render

# Create your views here.

from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.template import RequestContext
from .models import MatchMaker, RankingCreator, Player
import operator

def index(request):
    context = {}
    return render(request, 'glicko/index.html', context)

def results(request):
    # username = request.POST['user_name']
    # api_key = request.POST['user_apikey']
    username = "dummy_challonge"
    api_key = "SL1WRtqcsDoGOiukIwv5NNXzH8OCj7tEsduDvhDC"
    raw_brackets = request.POST['user_bracket-urls']
    brackets = raw_brackets.splitlines()
    m = MatchMaker()
    match_pairs = m.get_matches(username, api_key, brackets)
    r = RankingCreator()
    d = r.create_ratings(match_pairs)
    e = {}
    for key in d:
        e[key] = d[key].rating
    sorted_e = sorted(e.items(), key = operator.itemgetter(1)) # this is a list
    sorted_e.reverse()
    rankings = []
    for t in sorted_e:
        string = t[0]
        string += ", "
        string += str(t[1])
        rankings.append(string)
    context= {}
    context['rankings'] = rankings
    return render(request, 'glicko/results.html', context)