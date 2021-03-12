import gzip
import csv
from collections import defaultdict
import datetime as dt
from calendar import monthrange
from datetime import timedelta

from datetime import datetime
startTime = datetime.now()

####### Shanghai
# monthly_trades = ["SHH201409", "SHH201410", "SHH201411", "SHH201412", "SHH201501"]

# continuous_period = {
#     "morning": {
#         "open": "09:30",
#         "close": "11:30"
#     },
#     "afternoon": {
#         "open": "13:00",
#         "close": "14:57"
#     }
# }

####### Hong Kong
monthly_trades = ["HKG201409","HKG201410","HKG201411","HKG201412","HKG201501"]
continuous_period = {
    "morning": {
        "open": "09:30",
        "close": "12:00"
    },
    "afternoon": {
        "open": "13:00",
        "close": "16:00"
    }
}


for monthly_trade in monthly_trades:

    file = gzip.open("/ext/data/FinAnalytics/Assignment/"+monthly_trade+".csv.gz",'rt')
    data = csv.DictReader(file)

    # Create headers
    header = ["stock", "date", "quote_count","trade_volume","trade_value","trade_count","quote2trade","tradeSize"]
    
    year, month = int(monthly_trade[3:7]), int(monthly_trade[7:9])
    num_days_in_month = monthrange(year, month)[1]
    dates = [str(year) + '-' + str(month).zfill(2) + '-' + str(day).zfill(2) for day in range(1, num_days_in_month + 1)]

    
    with open("../output/"+ monthly_trade +".csv", "w") as f:
        w = csv.DictWriter(f, header)
        w.writeheader()

        stock_daily_metrics = defaultdict(float)
        
        market_open = False
        prev_day = None
        prev_security = None
        yesterday = None
        
        for transaction in data:
            security = transaction['#RIC']
            gmt = int(transaction['GMT Offset'])

            curr_datetime = dt.datetime.strptime(transaction['Date-Time'][:-4], '%Y-%m-%dT%H:%M:%S.%f')
            curr_datetime = curr_datetime + timedelta(hours=gmt)
            curr_day = curr_datetime.day
            today = transaction['Date-Time'][:10]
            
            if prev_day != None and prev_day != curr_day:
                market_open = False
                print("{} {} Market Closes. Quote: {} Trade: {}".format(prev_security, yesterday, stock_daily_metrics["quote_count"], stock_daily_metrics["trade_count"]))

                row = {'stock': prev_security, "date": yesterday}
                row.update(stock_daily_metrics)
                print(row)
                w.writerow(row)
                stock_daily_metrics = defaultdict(float)
            
            if (curr_datetime.time() >= dt.datetime.strptime(continuous_period["morning"]["open"],'%H:%M').time() \
                and curr_datetime.time() <= dt.datetime.strptime(continuous_period["morning"]["close"],'%H:%M').time()) or \
                (curr_datetime.time() >= dt.datetime.strptime(continuous_period["afternoon"]["open"],'%H:%M').time() \
                and curr_datetime.time() <= dt.datetime.strptime(continuous_period["afternoon"]["close"],'%H:%M').time()):
                
                if market_open == False:
                    print(security, today, "Market Opens")
                
                # Market Opens
                market_open = True
                
                # Update quote volume, trade volume
                if market_open and transaction['Type'] == 'Quote':
                    stock_daily_metrics["quote_count"] += 1
                elif market_open and transaction['Type'] == 'Trade':
                    stock_daily_metrics["trade_count"] += 1
                    
                    try:
                        stock_daily_metrics["trade_volume"] += int(transaction["Volume"])
                        stock_daily_metrics["trade_value"] += int(transaction["Volume"]) * float(transaction["Price"])
                    except ValueError:
                        stock_daily_metrics["trade_volume"] += 0
                        stock_daily_metrics["trade_value"] += 0

                # Update quote2trade, tradeSize
                try:
                    stock_daily_metrics["quote2trade"] = stock_daily_metrics["quote_count"] / stock_daily_metrics["trade_count"]
                    stock_daily_metrics["tradeSize"] = stock_daily_metrics["trade_volume"] / stock_daily_metrics["trade_count"]
                except ZeroDivisionError:
                    stock_daily_metrics["quote2trade"] = 0
                    stock_daily_metrics["tradeSize"] = 0
                
            elif market_open and curr_datetime.time() > dt.datetime.strptime(continuous_period["morning"]["close"],'%H:%M').time() \
                 and curr_datetime.time() < dt.datetime.strptime(continuous_period["afternoon"]["open"],'%H:%M').time():
                
                market_open = False

            prev_day = curr_day
            prev_security = security
            yesterday = today
            
            
            
print(datetime.now() - startTime)