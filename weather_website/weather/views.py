from django.shortcuts import render,redirect,get_object_or_404
import requests #use for sending http request
from django.conf import settings 
import datetime
from collections import defaultdict
from .models import SearchHistoryModel
from django.contrib.auth import authenticate,login,logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.decorators import login_required


#regisration view
def registration_view(request):
    if request.method=='POST':
        username=request.POST['username']
        email=request.POST['email']
        password=request.POST['password']
        confirm=request.POST['confirm']

        if password!=confirm:
            messages.error('Password is not matching!')
            return redirect('register')
        
        user=User.objects.create_user(username=username,email=email,password=password)
        user.save()
        return redirect('login')
    return render(request,'register.html')

#login view
def login_view(request):
    if request.method=='POST':
        username=request.POST['username']
        password=request.POST['password']

        user=authenticate(request,username=username,password=password)
        if user:
            login(request,user)
            return redirect('home')
        else:
            messages.error(request,'Invalid Username or Password!')
    return render(request,'login.html')

#logout view
def logout_view(request):
    logout(request)
    return redirect('login')

#home view
@login_required
def home_view(request):
    weather_data = {}
    hourly_forecast = []
    daily_forecast = []

    #if user is redirect from search histroy page to see old city weather info
    #used turnry operator
    city = request.GET.get('city') if request.method == 'GET' else request.POST.get('city')

    if city:
        api_key = settings.API_KEY

        #url for get weathrt info 
        weather_url = f'https://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric'
        #storing the response sent by url
        weather_res = requests.get(weather_url)

        #checking that http request is success
        if weather_res.status_code == 200:
            #converting jsom data into dictionry
            data = weather_res.json()

            #adding the data which we went to uses
            weather_data = {
                'city': city,
                'temperature': data['main']['temp'],
                'description': data['weather'][0]['description'],
                'icon': data['weather'][0]['icon'],
                'humidity': data['main']['humidity'],
                'wind_speed': data['wind']['speed'],
            }

            #adding suggestion in dictionry
            weather_data['suggest'] = suggestions(weather_data['temperature'], weather_data['description'])

            #saving search info in database if method is post
            if request.method == 'POST':
                SearchHistoryModel.objects.create(user=request.user, city=city)

            #url for get forecast info
            forecast_url = f'https://api.openweathermap.org/data/2.5/forecast?q={city}&appid={api_key}&units=metric'
            #storing the response sent by forecasr url
            forecast_response = requests.get(forecast_url)

            if forecast_response.status_code == 200:
                forecast_data = forecast_response.json()

                #hourly forecasting data 
                for entry in forecast_data['list'][:8]:
                    time = datetime.datetime.fromtimestamp(entry['dt']).strftime('%I:%M %p')
                    temp = entry['main']['temp']
                    icon = entry['weather'][0]['icon']
                    desc = entry['weather'][0]['description']
                    
                    hourly_forecast.append({
                        'time': time,
                        'temp': temp,
                        'icon': icon,
                        'desc': desc
                    })

                #daily avarage forecasting data
                daily_data = defaultdict(list) #used for creating dictionary without giving key
                for entry in forecast_data['list']:
                    #adding data by date
                    date = datetime.datetime.fromtimestamp(entry['dt']).strftime('%b %d,%Y')
                    daily_data[date].append(entry)

                #storing it in list as dictionary
                for date, entries in list(daily_data.items())[:5]:
                    avg_temp = sum(e['main']['temp'] for e in entries) / len(entries)
                    icon = entries[0]['weather'][0]['icon']
                    desc = entries[0]['weather'][0]['description']

                    daily_forecast.append({
                        'date': date,
                        'temp': round(avg_temp, 1),
                        'icon': icon,
                        'desc': desc
                    })

        #when city is not found
        else:
            weather_data = {'error': 'City not found!'}
    
    return render(request, 'home.html', {'weather': weather_data,'hourly': hourly_forecast,'daily': daily_forecast})


#get all search history by user
@login_required 
def search_history_view(request):
    history = SearchHistoryModel.objects.filter(user=request.user).order_by('-searched_at')
    return render(request, 'search_history.html', {'history': history})

#delete search histroy view
@login_required
def delete_search_entry(request, entry_id):
    entry = get_object_or_404(SearchHistoryModel, id=entry_id, user=request.user)
    entry.delete()
    return redirect('search_history')

#function for return suggestion according to weather condition
def suggestions(temp,description):
    suggest=""

    if 'rain' in description.lower():
        suggest="☔ Rain expected. Carry an umbrella!"
    elif 'snow' in description.lower():
        suggest="❄️ It's snowing! Wear warm clothes and boots."
    elif temp<=5:
        suggest="🧥 It's very cold! Wear a heavy jacket."
    elif temp<=15:
        suggest="🧣 It's chilly. Consider a jacket or sweater."
    elif temp>=30:
        suggest="🥵 It's hot! Stay hydrated and wear light clothes."
    elif 'clear' in description.lower():
        suggest= "😎 Clear skies! Great day for a walk."
    else:
        suggest = "🧍 Stay comfortable and dress appropriately."
    return suggest
