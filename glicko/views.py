from django.shortcuts import render

# Create your views here.

from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.template import RequestContext
from .models import MatchMaker, RankingCreator, Player
import operator
from collections import OrderedDict
from bokeh.plotting import figure, output_file, show
from bokeh.embed import components

def index(request):
    context = {}
    return render(request, 'glicko/index.html', context)

def results(request):
    # username = request.POST['user_name']
    # api_key = request.POST['user_apikey']
    username = "dummy_challonge"
    api_key = "SL1WRtqcsDoGOiukIwv5NNXzH8OCj7tEsduDvhDC"
    raw_brackets = request.POST['user_bracket-urls']
    with_duplicates_brackets = raw_brackets.splitlines()
    brackets = list(OrderedDict.fromkeys(with_duplicates_brackets))
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
        string += ("%.0f" % t[1])
        rankings.append(string)
    context= {}
    context['rankings'] = rankings

    # Graph X & Y coordinates
    # x = [ 1,2,3,4,5 ]
    # y = [ 1,2,3,4,5 ]
    # B = [ 10,4,3,2,1 ]

    # Set up graph plot for displaying line graph
    plot = figure(title = "Click on Player in Legend to Hide Their Line", x_axis_label = 'Time', y_axis_label = "Rating", plot_width = 800, plot_height = 400)

    # Plot line
    # plot.line(x, y, line_width = 2)
    # plot.line(x, B, line_width = 2)

    # get top 3 players
    # sorted_e.reverse()
    # top_three = []
    # for i in range(3):
    #     player = sorted_e.pop()
    #     top_three.append(player[0])
    # get their y axis
    colors = ['red', 'orange', 'yellow', 'green', 'blue', 'purple', 'black'] * 100
    for i in range(len(sorted_e)):
        player = sorted_e[i][0]
        timestep_to_rating = r.player_to_dict[player]
        timesteps = sorted(list(timestep_to_rating.keys()))
        ratings = []
        for step in timesteps:
            ratings.append(timestep_to_rating[step])
        plot.line(timesteps, ratings, line_color = colors[i], legend=player)

    plot.legend.location = "top_left"
    plot.legend.click_policy = "hide"

    # Store components
    script, div = components(plot)
    context['script'] = script
    context['div'] = div

    return render(request, 'glicko/results.html', context)