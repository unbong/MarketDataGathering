import requests
from bs4 import BeautifulSoup
import pymongo
from pymongo import MongoClient
import datetime
import warnings

client=MongoClient()
db=client.MainMarketData


def func_httprequest(url):
    header_info = {
    'User-Agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.71 Safari/537.36',
    'Content-type': 'application/json'
    }
    requestres=requests.get(url, verify=False,headers = header_info )
    requestres.encoding="utf-8"
    result=BeautifulSoup(requestres.text,'lxml')
    return result

def func_isnumber(str):
    try:
        float(str)
        return True
    except ValueError:
       print("can't convert")
    return False

def func_calculateAveRPS(stocks, isALL=False):
    averageRPS=0.0
    sumOfRps=0.0
    if not isALL:
        for stock in stocks.find({"iscalculated":"Y"}):
            sumOfRps+= float(stock["stockRPS"])
        averageRPS=sumOfRps/stocks.find({"iscalculated":"Y"}).count()
    else:
        s=0
    return averageRPS


def func_AddMarket(stockList, marketName):
    index=0
    for stock in stockList:
        try:
            stockInfo={}
            stockInfo['DateTime'] = datetime.datetime.utcnow()
            address=stock.contents[1]
            href="https://hk.investing.com" + address.a.get('href')
            # 各个股票的子地址
            subBsrs=func_httprequest(href)
            # 市盈率 ID 每股收益
            stockRps=subBsrs.select("#leftColumn > div.clear.overviewDataTable > div")
            # ID
            tmpstock=subBsrs.select("#quotes_summary_current_data > div.right > div")

            if len(tmpstock) < 3:
                stockInfo['stockId']=subBsrs.select("#leftColumn > div.instrumentHead > h1")[0].text
            else:
                stockInfo['stockId'] = tmpstock[2].contents[3].get("title")
            stockName=subBsrs.select("#leftColumn > div.instrumentHead > h1")
            # 名称 RPS EPS
            stockInfo['stockName'] = stockName[0].text
            stockInfo['stockRPS'] = stockRps[10].contents[1].text
            stockInfo['stockEPS'] = stockRps[5].contents[1].text
            # 价格
            stockInfo['stockPrice'] = stockRps[0].contents[1].text
            # 有无市盈率
            stockInfo['iscalculated'] = "Y"
            # 市场名
            stockInfo['marketName'] = marketName

            if not func_isnumber(stockInfo['stockRPS']):
                print(stockInfo['stockName'])
                stockInfo['iscalculated'] = "N"
            stock_id=stocks.find({'stockId':stockInfo['stockId']}).sort("DateTime", pymongo.DESCENDING)

            if stock_id.count() == 0:
                stock_id=stocks.update({'stockId':stockInfo['stockId'], 'DateTime': datetime.datetime.utcnow()}, {'$set':stockInfo},upsert=True)
            else:
                tmpDate1=stock_id[0]["DateTime"]
                tmpDate2=datetime.datetime.utcnow()
                if (tmpDate1.year == tmpDate2.year):
                    if (tmpDate2.month - tmpDate1.month) >=0 :
                        if(tmpDate2.day != tmpDate1.day):
                            stock_id=stocks.update({'stockId':stockInfo['stockId'], 'DateTime': datetime.datetime.utcnow()}, {'$set':stockInfo},upsert=True)
                else:
                    stock_id=stocks.update({'stockId':stockInfo['stockId'], 'DateTime': datetime.datetime.utcnow()}, {'$set':stockInfo},upsert=True)
            print(stockInfo["marketName"]+" - "+stockInfo["stockName"]+" Index: " + str(index))
            index = index +1
        except:
            print("Unexpected error:")
    return True

httpAllofMarketUrl="https://hk.investing.com/indices/major-indices"
bs=func_httprequest(httpAllofMarketUrl)
marketList=bs.select("#cr_12 > tbody > tr")

warnings.simplefilter("ignore")
stocks=db.stockData

for market in marketList:
    marketName=market.contents[1].a.text
    httpurl="https://hk.investing.com"+ str(market.contents[1].a['href'])+"-components"
    #
    bs=func_httprequest(httpurl)
    if marketName == "道琼斯指数" or  marketName == "标普500指数"\
        or marketName == "纳斯达克综合指数" or marketName == "欧洲斯托克50" \
        or marketName == "日经225" :
        stockList=bs.select("#cr1 > tbody > tr")
        # from IPython.core.debugger import Pdb; Pdb().set_trace()
        func_AddMarket(stockList,marketName)
