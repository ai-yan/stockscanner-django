import requests
import sched, time
import pandas as pd
from datetime import datetime




df = pd.DataFrame()
result = pd.DataFrame()

def signal():
    #print(result)
    min_empty = result[result["old_status"] != ""]
    new_signal = min_empty[min_empty["old_status"] != min_empty["new_status"]]
    #new_signal = result[result["old_status"] != result["new_status"]]
    if new_signal.empty:
        print("No signal at the moment")
        
    else:
        print(new_signal)

    # for index, row in result.iterrows():
    #     if row['old_status'] == "Error" | row['new_status'] == "Error":
    #         print("something went wrong...")
    #     elif row['old_status'] != row['new_status']:
    #         print(f"{row['new_status']} for {index} symbol.")

    #     print(index, row['old_status'], row['new_status'])


def Average(list,n_mov): 
    lst=list[:n_mov]
    return sum(lst) / len(lst)



def get_stocks(symbol, second_avg, interval):
    global df
    params = {
    'access_key': 'b97ec7bc8b5e0f368b7db0a58cdebf55',
    'symbols' : symbol,
    'interval' : interval,
    'limit' : second_avg,
    'exchange' : 'XNAS'

    #https://api.marketstack.com/v1/intraday?access_key=b97ec7bc8b5e0f368b7db0a58cdebf55&symbols=AAPL&interval=1min&limit=15
    }

    api_result = requests.get('https://api.marketstack.com/v1/intraday', params)

    data = api_result.json()
    data = data['data']



    dfi = pd.DataFrame([[x['symbol'], x['last'], x['date']] for x in data],
                    columns=['symbol', 'value', 'date'])

    df = df.append(dfi, ignore_index = True)
    # print(df)


def main(symbol,first_avg,second_avg, interval):
    #symbol=["AAPL","GOOGL"]
    #first_avg = 5
    #second_avg = 15
    global result

    if first_avg < second_avg:
    
        for s in symbol:
            get_stocks(s,second_avg, interval)
            

        for s in symbol:
            df3=df.loc[df['symbol'] == s, 'value']
            #print(df3)
            fifteen_avg = round(Average(df3,first_avg),3)
            five_avg = round(Average(df3,second_avg),3)
            
            # print(five_avg)
            # print(fifteen_avg)

            if five_avg == fifteen_avg:
                new_status = "Five average is equal to fifteen average"
                
            elif five_avg > fifteen_avg:
                new_status = "Five average is greater than fifteen average"
                
            elif five_avg < fifteen_avg:
                new_status = "Fifteen average is greater than five average"
                
            else:
                new_status = "Error"
            
            now = datetime.now()
            
            dt_string = now.strftime("%m/%d/%Y %H:%M")
            try:
                result.at[s, 'old_status'] = result.at[s, 'new_status']
                result.at[s, 'new_status'] = new_status
                result.at[s, 'date'] = dt_string
            except:
                old_status=""
                dfs = pd.DataFrame([[old_status,new_status,dt_string]],
                        index=[s],
                        columns=['old_status', 'new_status','date'])
                result = result.append(dfs)
            

            
        #print(result)
        signal()
        
    
    else:
        pass #inserire qui cosa succede nel caso in cui il primo periodo è >= al secondo

# main()

def scheduled(symbol,first_avg,second_avg,refresh_seconds, interval):
    s = sched.scheduler(time.time, time.sleep)
    def do_something(sc): 
        main(symbol, first_avg, second_avg, interval)
        s.enter(refresh_seconds, 1, do_something, (sc,))

    main(symbol,first_avg,second_avg, interval)
    s.enter(refresh_seconds, 1, do_something, (s,))
    s.run()

# #main(["AAPL","GOOGL","MSFT","AMZN"],5,15)
# symbols=["AAPL","GOOGL","MSFT","AMZN"]
# scheduled(symbols,5,10,60)

