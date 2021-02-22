import main
from main import scheduled
symbols_to_check = ["AAPL","GOOGL","MSFT","AMZN"] #these are the symbols
period_first_avg = 5 #this is the period of first average
period_second_avg = 15 #this is the period of second average
time_refresh = 60 #seconds this is the time of each refresh
interval = "1min"
scheduled(symbols_to_check,period_first_avg,period_second_avg,time_refresh,interval)


from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError

my_conn = create_engine('sqlite:///./db.sqlite3', echo=False)


q="SELECT DISTINCT first_period, second_period FROM Users_Alerts"
try:
  r_set=my_conn.execute(q)
  data=r_set.fetchall()
  for row in data:
    print(row[0], row[1])
except SQLAlchemyError as e:
  error=str(e.__dict__['orig'])
  print(error)
else:
  print("No of records displayed : ",len(data))
