import SunRiseSunSetPerDayDictionaries as C
import datetime
import os
import linecache
import sys
import time
from gpiozero import LED as LEDClass, LEDBarGraph #Need this line eventually
import RPi.GPIO as GPIO
import math
import requests
import random

SWITCH_IP = '10.0.0.180'
SWITCH_2_IP = '10.0.0.8'
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:126.0) Gecko/20100101 Firefox/126.0',
    'Accept': '*/*',
    'Accept-Language': 'en-US,en;q=0.5',
    # 'Accept-Encoding': 'gzip, deflate',
    'DNT': '1',
    'Connection': 'keep-alive',
    'Referer': f'http://{SWITCH_IP}/',#TODO Change IP Address Here
    'Priority': 'u=1',
}
HEADERS_2 = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:126.0) Gecko/20100101 Firefox/126.0',
    'Accept': '*/*',
    'Accept-Language': 'en-US,en;q=0.5',
    # 'Accept-Encoding': 'gzip, deflate',
    'DNT': '1',
    'Connection': 'keep-alive',
    'Referer': f'http://{SWITCH_2_IP}/',#TODO Change IP Address Here
    'Priority': 'u=1',
}
PARAMS_ON = {
    'cmnd': 'Power ON',
}
PARAMS_OFF = {
    'cmnd': 'Power OFF',
}
GPIO.setwarnings(False)
LED1 = LEDClass(18) #DST
LED2 = LEDClass(23) #Exception occurred
LED_PINS : list[int] = [4,17,27,22,5,6,13,19,26,21]
BAR_GRAPH = LEDBarGraph(*LED_PINS, active_high=False)
LED_PINS2 : list[int] = [20,16,12,1,7,8,25,24,15,14]
BAR_GRAPH2 = LEDBarGraph(*LED_PINS2, active_high=False)

switch = False
all_dates = C.CreateTheYear()
today_date : datetime
today_dict : dict #initialize today just to save value inside of loops
rate_of_change = 0

def TurnOnSwitch():
    sendThisRequest = requests.get(f'http://{SWITCH_IP}/cm', params=PARAMS_ON, headers=HEADERS)
    sendThisRequest = requests.get(f'http://{SWITCH_2_IP}/cm', params=PARAMS_ON, headers=HEADERS)

def TurnOFFSwitch():
    sendThisRequest = requests.get(f'http://{SWITCH_IP}/cm', params=PARAMS_OFF, headers=HEADERS)
    sendThisRequest = requests.get(f'http://{SWITCH_2_IP}/cm', params=PARAMS_OFF, headers=HEADERS)

def MilitaryToMinutes(military_in_thousands):
    hours = math.floor(military_in_thousands/100)
    minutes_without_hour_minutes = military_in_thousands - (hours*100)
    total_minutes = (hours*60) + minutes_without_hour_minutes
    return total_minutes

def WhatIsToday():
    global today_date
    today_date = datetime.datetime.now()

def loop():
    global today_date, today_dict, switch, TOGGLE_SWITCH
    day_change_rate = 0
    day_length = 0
    iteration = 0
    while True: #loop forever
        WhatIsToday()
        today_month = int(today_date.strftime("%m")) #retrieve today's month
        today_month_name = (today_date.strftime("%B"))
        today_day = int(today_date.strftime("%d")) #retrieve today's day
        today_time = int(today_date.strftime("%H%M")) #retrieve the time as military, 4 digit integer
        day_change_rate = 0
        day_length = 0
        
        time.sleep(1)
        
        os.system('clear') #Clear the console
        
        if (today_time == 1) or (iteration == 0): #this needs changed so the program will calculate upon startup as well
            (day_change_rate, day_length) = HowQuicklyAreTheDaysChanging(today_month, today_day)
            if IsItDaylightSavingsTime(): #Check if it is daylight savings time
                print("Daylight Savings Time\n")
        
        iteration += 1
        #Would prefer to only calculate this once daily to save processing power
        SetBarGraphForDayRateChange(day_change_rate)
        
        
        
        for j in range(1, 13): #for each month in a year
            if today_month == j: #if the month in the year is the same as the current month
                month = tuple(x for x in all_dates if x.get("month") == j) #current month is the tuple of dictionaries of all days in that month
                
                for day in month: #for each day in the current month
                    test_day = day.get('day') # day int from dictionary
                    
                    if test_day == today_day: #if the day is today
                        today_dict = dict(tuple(y for y in month if y.get("day") == today_day)[0])
                        j=13 #BREAK BOTH FOR LOOPS
                        break
        
        rise = today_dict.get('rise')#Get the sunrise time
        set = today_dict.get('set')#Get the sunset time
        
        
            
        if (today_time >= rise) and (today_time < set) and (not switch): #AND THE SWITCH IS CURRENTLY OFF:
            #turn the switch on
            switch = not switch
            TurnOnSwitch()
        elif ((today_time < rise) or (today_time >= set)) and (switch): #AND THE SWITCH IS CURRENTLY ON:
            #This means the switch is on or that it is not time yet.
            #turn off the switch
            switch = not switch
            TurnOFFSwitch()      
        
        iteration += 1
        time.sleep(300)
          
        
def PrintException(): #prints an exception that occured, useful in except: blocks
    global LED2
    exc_type, exc_obj, tb = sys.exc_info()
    f = tb.tb_frame
    lineno = tb.tb_lineno
    filename = f.f_code.co_filename
    linecache.checkcache(filename)
    line = linecache.getline(filename, lineno, f.f_globals)
    print (f'EXCEPTION IN ({filename}, LINE {lineno} "{line.strip()}"): {exc_obj}')
    LED2.on()
        
def IsItDaylightSavingsTime():
    global LED1, today_date
    todays_month = int(today_date.strftime("%m")) #retrieve today's month
    todays_day = int(today_date.strftime("%d")) #retrieve today's day
    todays_year = int(today_date.strftime("%Y")) #retrieve today's year
    counter = 0 #initialize to save value
    DST = False #initialize at it is not daylight savings time
    
    if(todays_month >= 3 and todays_month <= 11): #if the months line up
        if(todays_month == 3): #if it is march
            for i in range(1,15): #go through the first 14 days of march (2 full weeks)
                if datetime.datetime(todays_year, todays_month, i).strftime("%a").casefold() == 'sun': #check for sundays
                    counter += 1 #increase counter for sundays
                    if counter == 2 and (todays_day >= i): #Once we reach the second sunday in March, is the day in march during/after that?
                        DST = True #Then it is DST
                        break
                    
        elif(todays_month == 11): #If it is november
            for day in range(1,8): #Iterate through the first week
                if datetime.datetime(todays_year, todays_month, day).strftime("%a").casefold() == 'sun': #count the sundays
                    counter += 1
                    if counter == 1 and (todays_day >= day): #if it is the first sunday in november and today is during or after that, then it is not DST
                        DST = False
                        break
                    
        elif todays_month in range(4,11): #If today's month is april to october, it is DST
            DST = True
            
    if DST: #Turn on or turn off the LED accordingly
       LED1.on()
    else: 
        LED1.off()   
    
    return DST
 
def IsItALeapYear():
    global today_date
    
    today_year = int(today_date.strftime("%Y"))
    
    return (today_year % 4 == 0)
          
def FindMonthDayTotal(month, day):
    month_string = ('jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec')
    the_31_day_months = (month_string[0], month_string[2], month_string[4], month_string[6], month_string[7], month_string[9], month_string[11])
    the_30_day_months = (month_string[3], month_string[5], month_string[8], month_string[10])
    the_29_day_months = month_string[1]
    counter = 0
    
    for which_month in month_string[:int(month)-1]:
                
        if which_month in the_31_day_months:
            counter += 31
        if which_month in the_30_day_months:
            counter += 30
        if which_month in the_29_day_months:
            if IsItALeapYear():
                counter += 29
            else:
                counter += 28
                
    counter += day
    
    return(counter-1) #to account for indices being one before the day count
           
def HowLongIsTodayBarGraph2Setting(index):
    global BAR_GRAPH2
    minutes = MilitaryToMinutes(all_dates[index].get("set")) - MilitaryToMinutes(all_dates[index].get("rise"))
    
    steps = (0, 593, 628, 663, 698, 733, 767, 802, 837, 872)
    for i in range (0, len(steps)):
        if minutes > steps[i]:
            for bar in BAR_GRAPH2:
                bar.off()
            for bar in BAR_GRAPH2[:i+1]:
                bar.on()
    
    return minutes
                  
def HowQuicklyAreTheDaysChanging(month, day):
    global today_date
    
    today_month = month
    today_day = day
        
    current_date_index = FindMonthDayTotal(today_month, today_day)
    day_length= HowLongIsTodayBarGraph2Setting(current_date_index)
    
    future_length = 0
    past_length = 0
    
    if(current_date_index < 362):
        for i in range(0, 5):
            future_length += MilitaryToMinutes(all_dates[current_date_index+i].get("set")) - MilitaryToMinutes(all_dates[current_date_index+i].get("rise"))
            past_length += MilitaryToMinutes(all_dates[current_date_index-1-i].get("set")) - MilitaryToMinutes(all_dates[current_date_index-1-i].get("rise"))
    else:
        for i in range(0, 5):
            past_length += MilitaryToMinutes(all_dates[current_date_index-1-i].get("set")) - MilitaryToMinutes(all_dates[current_date_index-1-i].get("rise"))
        match(current_date_index):#this could be written using a stacked for loop so it is not written 5 times
            case 362:
                #future: 362, 363, 364, 365, 0
                for i in range (0,4):
                    future_length += MilitaryToMinutes(all_dates[current_date_index + i].get("set")) - MilitaryToMinutes(all_dates[current_date_index + i].get("rise"))
                future_length += MilitaryToMinutes(all_dates[0].get("set")) - MilitaryToMinutes(all_dates[0].get("rise"))
                
            case 363:
                #future: 363, 364, 365, 0, 1
                for i in range (0,3):
                    future_length += MilitaryToMinutes(all_dates[current_date_index + i].get("set")) - MilitaryToMinutes(all_dates[current_date_index + i].get("rise"))
                for i in range(0, 2):
                    future_length += MilitaryToMinutes(all_dates[i].get("set")) - MilitaryToMinutes(all_dates[i].get("rise"))

            case 364:
                #future: 364, 365, 0, 1, 2
                for i in range (0,2):
                    future_length += MilitaryToMinutes(all_dates[current_date_index + i].get("set")) - MilitaryToMinutes(all_dates[current_date_index + i].get("rise"))
                for i in range(0, 3):
                    future_length += MilitaryToMinutes(all_dates[i].get("set")) - MilitaryToMinutes(all_dates[i].get("rise"))
               
            case 365:
                #future: 365, 0, 1, 2, 3
                for i in range (0,1):
                    future_length += MilitaryToMinutes(all_dates[current_date_index + i].get("set")) - MilitaryToMinutes(all_dates[current_date_index + i].get("rise"))
                for i in range(0, 4):
                    future_length += MilitaryToMinutes(all_dates[i].get("set")) - MilitaryToMinutes(all_dates[i].get("rise"))
    
    day_length_rate_of_change = (future_length - past_length) / past_length
    return (abs(day_length_rate_of_change), day_length)
    
def SetBarGraphForDayRateChange(change_in_length):
    global BAR_GRAPH
    steps = (0.001, .013, .015, .017, .018, .02, .021, .022, .024, .025)
    for i in range (0, len(steps)):
        if change_in_length > steps[i]:
            for bar in BAR_GRAPH:
                bar.off()
            for bar in BAR_GRAPH[:i+1]:
                bar.on()
            
def destroy():
    global LED1, LED2, BAR_GRAPH, BAR_GRAPH2
    for i in range(0,BAR_GRAPH):
        BAR_GRAPH[i].close()
        BAR_GRAPH2[i].close()
    LED1.close()
    LED2.close()

def OneFootInTheRaveOneFootInTheGrave():
    PianoKeys()
    FunStuff()
    Randomizer()
    
def Randomizer():
    global LED1, LED2, BAR_GRAPH, BAR_GRAPH2
    for i in range(0,30):
        x = random.randrange(0,20)
        if x in range(0,10):
            BAR_GRAPH[x].on()
            time.sleep(0.01+(i/1000))
            BAR_GRAPH[x].off()
            time.sleep(0.01)
        else:
            BAR_GRAPH2[x-10].on()
            time.sleep(0.01+(i/1000))
            BAR_GRAPH2[x-10].off()
            time.sleep(0.01)   

def PianoKeys():
    global LED1, LED2, BAR_GRAPH, BAR_GRAPH2
    
    for i in range(0,10):
            BAR_GRAPH[i].on()
            time.sleep(0.01)
            BAR_GRAPH[i].off()
            time.sleep(0.01)
            
    LED1.on()
    time.sleep(0.02)
    LED1.off()
    time.sleep(0.01)
    LED2.on()
    time.sleep(0.02)
    LED2.off()
    time.sleep(0.01)
    
    for i in range(0,10):
        BAR_GRAPH2[i].on()
        time.sleep(0.01)
        BAR_GRAPH2[i].off()
        time.sleep(0.01)
        
def FunStuff():
    global LED1, LED2, BAR_GRAPH, BAR_GRAPH2
    for i in range(0, len(BAR_GRAPH)):
            BAR_GRAPH[i].on()
            BAR_GRAPH2[i].off()
            LED1.on()
            LED2.off()
            time.sleep(.01)
            BAR_GRAPH[i].off()
            BAR_GRAPH2[i].on()
            LED1.off()
            LED2.on()
            time.sleep(.01)
    time.sleep(.05)
    for i in range(0,2):
        for i in range(0, 5):
            BAR_GRAPH[i].on()
            BAR_GRAPH2[i].off()
            BAR_GRAPH[-i-1].on()
            BAR_GRAPH2[-i-1].off()
            for j in range(0,2):
                LED1.on()
                LED2.on()
                time.sleep(.02)
                LED1.off()
                LED2.off()
                time.sleep(.02)
        for i in range(0, 5):
            BAR_GRAPH[i].off()
            BAR_GRAPH2[i].on()
            BAR_GRAPH[-i-1].off()
            BAR_GRAPH2[-i-1].on()
            for j in range(0,2):
                LED1.on()
                LED2.on()
                time.sleep(.02)
                LED1.off()
                LED2.off()
                time.sleep(.02)

if __name__ == '__main__':    
    x = ''
    OneFootInTheRaveOneFootInTheGrave()
    TurnOFFSwitch()
    while x.casefold() != 'quit':
        try:
            LED2.off()
            loop()
        except Exception:
            #If an exception occurred, notify the user
            PrintException()
            x = input("\nContinue?")
            
    destroy()