from django.shortcuts import render
import time

def index(request):
    """Vista principal de la landing page de Lucy AMS"""
    return render(request, 'index.html', {'timestamp': int(time.time())})

def test_css(request):
    """Vista de prueba para verificar CSS"""
    return render(request, 'test-css.html', {'timestamp': int(time.time())})
