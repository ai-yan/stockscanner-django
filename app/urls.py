# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from django.urls import path, re_path
from app import views

urlpatterns = [

    # The home page
    path('', views.homepage, name='homepage'),
    path('ui-tables.html', views.tables, name='tables'),
    path('get_more_tables.html', views.tables, name='tables'),
    path('stock_alerts.html', views.stock_alerts, name='stock_alerts'),
    path('download', views.download, name='download'),
    path('page-user.html', views.edit_profile, name="page-user"),

    # Matches any html file
    re_path(r'^.*\.*', views.pages, name='pages'),

    
    

    
]
