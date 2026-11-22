from django.shortcuts import render

import silverpoint


def csp(get_response):
    def middleware(request):
        response = get_response(request)
        response["Content-Security-Policy"] = "script-src 'self'; style-src 'self'"
        return response

    return middleware


def index(request):
    rows = [{"team": "A", "wins": 12}, {"team": "B", "wins": 9}, {"team": "C", "wins": 15}]
    chart = silverpoint.bar_chart(rows, x="team", value="wins", title="Wins", orientation="rows")
    return render(request, "index.html", {"chart": chart})
