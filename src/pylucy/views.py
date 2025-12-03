from django.shortcuts import render

def index(request):
    """Vista principal de la landing page de Lucy AMS"""
    return render(request, 'index.html')
