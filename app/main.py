import requests
import sched, time
import pandas as pd
from datetime import datetime
from sqlalchemy import create_engine
import pytz
import dateutil.parser


#df = pd.DataFrame()
result = pd.DataFrame()


def write_sql(dfw):
    engine = create_engine('sqlite:///./db.sqlite3', echo=False)
    #df = pd.DataFrame({'name' : ['User 1', 'User 2', 'User 3']})
    dfw.to_sql('Avg_Status', con=engine, if_exists='append', index_label='symbol')
    engine.execute("SELECT * FROM Avg_Status").fetchall()

def write_signal(dfw):
    engine = create_engine('sqlite:///./db.sqlite3', echo=False)
    #df = pd.DataFrame({'name' : ['User 1', 'User 2', 'User 3']})
    dfw.to_sql('Stock_Signals', con=engine, if_exists='append', index_label='symbol')
    engine.execute("SELECT * FROM Stock_Signals").fetchall()


def signal(symbol_,first_p,second_p):
    #print(result)
    result = pd.read_sql_table('Avg_Status', 'sqlite:///./db.sqlite3',index_col='symbol')
    result = result[result.index == symbol_]
    result = result[(result['fr_pr'] == first_p) & (result['sc_pr'] == second_p)]
    result = result.tail(1)
    min_empty = result[result["old_status"] != ""]
    new_signal = min_empty[min_empty["old_status"] != min_empty["new_status"]][['new_status','date','fr_pr','sc_pr']]
    new_signal = new_signal.rename(columns={"new_status": "Crossover_Type", "date": "Crossover_Time"})
    new_signal["perc_cross"] = ""
    ITA = pytz.timezone('Europe/Rome')
    #new_signal = new_signal_
    #print(new_signal)
    #dfi = pd.DataFrame([[x['symbol'], x['last'], x['date']] for x in data],
    #                columns=['symbol', 'value', 'date'])

    #df = df.append(dfi, ignore_index = True)
    #new_signal = result[result["old_status"] != result["new_status"]]
    if new_signal.empty:
        now = datetime.now(ITA)    
        dt_string_ = now.strftime("%m/%d/%Y %H:%M")
        print(f"{dt_string_} - {symbol_} - {first_p} - {second_p} - No signal at the moment") #da commentare
        #print(result)
        
    else:
        print(f"New signal!\n{new_signal}") #da commentare
        write_signal(new_signal)



    # for index, row in result.iterrows():
    #     if row['old_status'] == "Error" | row['new_status'] == "Error":
    #         print("something went wrong...")
    #     elif row['old_status'] != row['new_status']:
    #         print(f"{row['new_status']} for {index} symbol.")

    #     print(index, row['old_status'], row['new_status'])


def Average(list,n_mov): 
    lst=list[:n_mov]
    if len(lst) > 0:
        avg = sum(lst) / len(lst)
    else:
        avg = 0
    return avg



def get_stocks(symbol, second_p, interval_):
    
    #global df
    
    params = {
    'access_key': 'b97ec7bc8b5e0f368b7db0a58cdebf55',
    'symbols' : symbol,
    'interval' : interval_,
    'limit' : second_p,
    'exchange' : 'XNAS'

    #https://api.marketstack.com/v1/intraday?access_key=b97ec7bc8b5e0f368b7db0a58cdebf55&symbols=AAPL&interval=1min&limit=15
    }
    
    api_result = requests.get('https://api.marketstack.com/v1/intraday', params)
    try:
        data = api_result.json()
        data = data['data']
    except:
        data = []
        print(f"{symbol} - {second_p} - Error on get request")



    dfi = pd.DataFrame([[x['symbol'], x['last'], x['date']] for x in data],
                    columns=['symbol', 'value', 'date'])

    #df = df.append(dfi, ignore_index = True)
    # print(df)
    return dfi

def main(symbol,first_p,second_p, interval):
    
    global result
    #Chicago = pytz.timezone('America/Chicago')
    if first_p < second_p:
    
        
        
        dfi = get_stocks(symbol,second_p, interval)

        if dfi.empty:
            print(f"{symbol} empty request")
        else:
                

            #for s in symbol: #removed when changed from list to single symbol
            s = symbol #added when changed from list to single symbol
            #print(dfi)
            df3=dfi.loc[dfi['symbol'] == s, 'value']
            time_ = dfi.loc[dfi['symbol'] == s, 'date']
            
            time_ = dateutil.parser.parse(time_.iloc[0]).strftime("%m/%d/%Y %H:%M")
            
            
            s_avg = round(Average(df3,first_p),3)
            f_avg = round(Average(df3,second_p),3)
            
            # print(f_avg)
            # print(s_avg)

            if f_avg == s_avg:
                new_status = f"{first_p} periods average is equal to {second_p} periods average"
                
            elif f_avg > s_avg:
                new_status = f"{first_p} periods average is greater than {second_p} periods average"
                
            elif f_avg < s_avg:
                new_status = f"{second_p} periods average is greater than {first_p} periods average"
                
            else:
                new_status = "Error"
            
            #now = datetime.now(Chicago)

            result = pd.read_sql_table('Avg_Status', 'sqlite:///./db.sqlite3',index_col='symbol')
            result = result[(result['fr_pr'] == first_p) & (result['sc_pr'] == second_p)]
            if new_status != "Error":
                try:
                    dfss = result.at[s, 'new_status']
                    old_status = dfss.tail(1).iloc[0]
                    new_status = new_status
                    
                    dfs = pd.DataFrame([[old_status,new_status,time_,first_p,second_p]],
                        index=[s],
                        columns=['old_status', 'new_status','date','fr_pr','sc_pr'])
                    write_sql(dfs)
                except:
                    old_status=""
                    dfs = pd.DataFrame([[old_status,new_status,time_,first_p,second_p]],
                            index=[s],
                            columns=['old_status', 'new_status','date','fr_pr','sc_pr'])
                    write_sql(dfs)
                
            signal(s,first_p,second_p)
        
    
    else:
        pass #inserire qui cosa succede nel caso in cui il primo periodo è >= al secondo


def select_parameters():
    all_data = pd.read_sql_table('Users_Alerts', 'sqlite:///./db.sqlite3',index_col='symbol')
    distinct_period = all_data.drop_duplicates(subset=['first_period', 'second_period'])
    #print(distinct_period)
    interval = "10min"
    
    for index, row in distinct_period.iterrows():
        fr_pd = row[1]
        sc_pr = row[2]

        symbols= all_data[(all_data['first_period'] == fr_pd) & (all_data['second_period'] == sc_pr)].index

        for symbol in symbols:
            
            main(symbol, fr_pd, sc_pr, interval)
    


def scheduled():
    refresh_seconds = 600
    s = sched.scheduler(time.time, time.sleep)
    def do_something(sc): 
        select_parameters()
        s.enter(refresh_seconds, 1, do_something, (sc,))

    select_parameters()
    s.enter(refresh_seconds, 1, do_something, (s,))
    s.run()



#select_parameters()

if __name__ == "__main__":
    scheduled()