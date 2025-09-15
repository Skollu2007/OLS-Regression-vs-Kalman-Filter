import pandas as pd
import json
import requests
from io import StringIO

def get_stocks():
   url = 'https://stockanalysis.com/list/sp-500-stocks/'

    # fetch HTML with User-Agent
   html = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}).text

    # wrap HTML in StringIO to satisfy future pandas versions
   df = pd.read_html(StringIO(html))[0]

   tickers = df['Symbol'].astype(str).tolist()[0:50]
   return(tickers)
