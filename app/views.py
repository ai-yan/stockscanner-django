# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.template import loader
from django.http import HttpResponse
from django import template
import pandas as pd
from django.shortcuts import render_to_response
from django.views.decorators.csrf import csrf_exempt
from django.template import Context, RequestContext
from sqlalchemy import create_engine
from datetime import datetime, timedelta
import pytz
from django.http import StreamingHttpResponse
import csv
import xlsx_streaming
from .forms import EditForm
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.forms.utils import ErrorList


result = pd.DataFrame()




class Echo:

    def write(self, value):

        return value

def download(request):
    
    
    current_user = request.user
    current_user_id = current_user.id
    Chicago = pytz.timezone('America/Chicago')
    now = datetime.now(Chicago) - timedelta(days=90)
    dt_string = now.strftime("%m/%d/%Y %H:%M")
    
    signals = pd.read_sql_table('Stock_Signals', 'sqlite:///./db.sqlite3')
    signals['Crossover_Time'] = pd.to_datetime(signals['Crossover_Time'])
    signals = signals.loc[signals['Crossover_Time'] > dt_string]
    alerts = pd.read_sql_table('Users_Alerts', 'sqlite:///./db.sqlite3')
    alerts = alerts[alerts['user'] == current_user_id]
    alerts = alerts[['symbol','first_period','second_period']]
    alerts = alerts.rename(columns={"first_period": "fr_pr", "second_period": "sc_pr"})
    result_nin = pd.merge(alerts,signals,on=['symbol','fr_pr','sc_pr'], how='inner')

    result_nin = result_nin.sort_index(ascending=False)
    result_nin = result_nin[['symbol',"Crossover_Type","Crossover_Time"]]

    #with open('template.xlsx', 'rb') as template:
    result_list = [['symbol','Crossover_Type','Crossover_Time']]
    result_list = result_list + result_nin.values.tolist()

    
    stream = xlsx_streaming.stream_queryset_as_xlsx(result_list)
    if request.GET.get('type') == "excel":
        response = StreamingHttpResponse(
            stream,
            content_type='application/vnd.xlsxformats-officedocument.spreadsheetml.sheet',
        )
        response['Content-Disposition'] = f'attachment; filename="Historical_data_{dt_string}.xlsx"'
    elif request.GET.get('type') == "csv":
        response = StreamingHttpResponse(result_nin.to_csv(index=False),content_type="text/csv")

        response['Content-Disposition'] = f'attachment; filename="Historical_data_{dt_string}.csv"'
    else:
        response = None
    return response

def write_user_alert(user_id, symbol, first_period, second_period):
    engine = create_engine('sqlite:///./db.sqlite3', echo=False)
    df = pd.DataFrame({'user' : [user_id], 'symbol' : [symbol], 'first_period' : [first_period], 'second_period' : [second_period] })
    df.to_sql('Users_Alerts', con=engine, if_exists='append', index=False)
    engine.execute("SELECT * FROM Users_Alerts").fetchall()

def sql_del(user, symbol, first_period, second_period):
    engine = create_engine('sqlite:///./db.sqlite3', echo=False)
    sql_update_query = f"""DELETE from Users_Alerts where user = {user} and symbol = '{symbol}' and first_period ={first_period} and second_period = {second_period}"""
    engine.execute(sql_update_query)


def homepage(request):
    
    context = {}
    

    html_template = loader.get_template( 'homepage.html' )
    return HttpResponse(html_template.render(context, request))

@csrf_exempt


@login_required(login_url="/login/")
def stock_alerts(request):
    symbols =request.GET.get('symbol')

    if symbols != None:
        symbols = symbols.replace(" ","")
        symbols = symbols.upper()
        symbol = symbols.split(",")

    else:
        symbol = []
    current_user = request.user
    current_user_id = current_user.id
    max_num = ""
    try:
        row_id=int(request.GET.get('row_id'))
    except:
        row_id = None

    if  row_id != None:
        alerts_del = pd.read_sql_table('Users_Alerts', 'sqlite:///./db.sqlite3')
        alerts2_del = alerts_del[alerts_del['user'] == current_user_id]
        alerts2_del = alerts2_del.sort_index(ascending=False)
        row_to_del = alerts2_del.loc[row_id,:]

        sql_del(row_to_del.at['user'],row_to_del.at['symbol'],row_to_del.at['first_period'],row_to_del.at['second_period'])


    if len(symbol) > 0:
        first_period=int(request.GET.get('first_period'))
        second_period=int(request.GET.get('second_period'))

        check_ = pd.read_sql_table('Users_Alerts', 'sqlite:///./db.sqlite3')
        check = check_[check_['user'] == current_user_id]
        index = check.index
        number_of_rows = len(index)
        

        if (number_of_rows + len(symbol)) <= 50:
            for k in symbol:
                exist = check[(check['symbol'] == k) & (check['first_period'] == first_period) & (check['second_period'] == second_period)]

                if (exist.empty):
                    write_user_alert(current_user_id, k, first_period, second_period)

        else:
            mx = 50 - number_of_rows
            max_num = f"Maximum number of 50 symbols are reached. You can add other {mx} symbols. Please try again"
    
    alerts = pd.read_sql_table('Users_Alerts', 'sqlite:///./db.sqlite3')
    alerts2 = alerts[alerts['user'] == current_user_id]
    alerts2 = alerts2.sort_index(ascending=False)
    alerts_ = alerts2.iterrows()
    context=({'alerts' : alerts_, 'max_num' : max_num})
    
    
    try:
        
        load_template      = request.path.split('/')[-1]
        context['segment'] = load_template

        html_template = loader.get_template( load_template )
        return HttpResponse(html_template.render(context, request))
        
    except template.TemplateDoesNotExist:

        html_template = loader.get_template( 'page-404.html' )
        return HttpResponse(html_template.render(context, request))

    except:
    
        html_template = loader.get_template( 'page-500.html' )
        return HttpResponse(html_template.render(context, request))



@login_required(login_url="/login/")
def tables(request):
    global result
    context = {}
    current_user = request.user
    current_user_id = current_user.id
    Chicago = pytz.timezone('America/Chicago')
    now = datetime.now(Chicago) - timedelta(hours=24)
    dt_string = now.strftime("%m/%d/%Y %H:%M")
    #print(dt_string)
    

    if result.empty:
        last_row = 0
        
    else:
        last_row = len(result.index)
        
    
    signals = pd.read_sql_table('Stock_Signals', 'sqlite:///./db.sqlite3')
    signals['Crossover_Time'] = pd.to_datetime(signals['Crossover_Time'])
    signals = signals.loc[signals['Crossover_Time'] > dt_string]
    
    #print(signals)
    alerts = pd.read_sql_table('Users_Alerts', 'sqlite:///./db.sqlite3')
    alerts = alerts[alerts['user'] == current_user_id]
    alerts = alerts[['symbol','first_period','second_period']]
    #print(alerts)
    alerts = alerts.rename(columns={"first_period": "fr_pr", "second_period": "sc_pr"})
    result = pd.merge(alerts,signals,on=['symbol','fr_pr','sc_pr'], how='inner')
    #print("---------------------------------------------------")
    #print(result)
       
    result = result.sort_index(ascending=False)
    result_ = result.iterrows()
   
    context={'data' : result_}

    try:
        
        load_template      = request.path.split('/')[-1]
        context['segment'] = load_template

        html_template = loader.get_template( load_template )
        return HttpResponse(html_template.render(context, request))
        
    except template.TemplateDoesNotExist:

        html_template = loader.get_template( 'page-404.html' )
        return HttpResponse(html_template.render(context, request))

    except:
    
        html_template = loader.get_template( 'page-500.html' )
        return HttpResponse(html_template.render(context, request))


@login_required(login_url="/login/")
def pages(request):
    context = {}
    try:
        
        load_template      = request.path.split('/')[-1]
        context['segment'] = load_template

        html_template = loader.get_template( load_template )
        return HttpResponse(html_template.render(context, request))
        
    except template.TemplateDoesNotExist:

        html_template = loader.get_template( 'page-404.html' )
        return HttpResponse(html_template.render(context, request))

    except:
    
        html_template = loader.get_template( 'page-500.html' )
        return HttpResponse(html_template.render(context, request))


@csrf_exempt
def edit_profile(request):
    # if request.method == "POST":
    #     form = EditForm(request.POST, instance=request.user)
    #     if form.is_valid():
    #         form.save()
    #         return redirect("page-user.html")
   
    # else:
    #     form = EditForm(instance=request.user)
    #     args = {'form': form}
    #     return render(request, "page-user.html", args)

    context = {}
    if request.method == "POST":
        form = EditForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect("page-user.html")
   
    else:
        form = EditForm(instance=request.user)
        
        context = {'form': form}

    try:
        
        load_template      = request.path.split('/')[-1]
        context['segment'] = load_template

        html_template = loader.get_template( load_template )
        return HttpResponse(html_template.render(context, request))
        
    except template.TemplateDoesNotExist:

        html_template = loader.get_template( 'page-404.html' )
        return HttpResponse(html_template.render(context, request))

    except:
    
        html_template = loader.get_template( 'page-500.html' )
        return HttpResponse(html_template.render(context, request))
