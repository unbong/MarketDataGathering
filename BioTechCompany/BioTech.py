import requests
from bs4 import BeautifulSoup
from pymongo import MongoClient
import urllib3
import pymongo
from pymongo import MongoClient
import datetime
import random
import warnings
import pprint
import datetime

client = MongoClient()
db = client.MainMarketData


def func_httprequest(url, param):
    header_info = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.71 Safari/537.36',
        'Content-type': 'application/json'
    }
    requestres = requests.get(url, params=param)
    # requestres.encoding="utf-8"
    # result=BeautifulSoup(requestres.text,'lxml')
    return requestres


def func_httprequest_bs4(url, encoding="utf-8"):
    header_info = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.71 Safari/537.36',
        'Content-type': 'application/json'
    }
    requestres = requests.get(url)
    # requestres.encoding="utf-8"
    requestres.encoding = encoding
    result = BeautifulSoup(requestres.text, 'lxml')
    return result

def func_bs4_select(bs_object,selector,result_item,index = 0):
    result = False
    selected_item = bs_object.select('#name')
    if len(selected_item)==0 and len(selected_item) < index :
        return result
    result_item = selected_item[0]
    result = True
    return result

today = datetime.datetime.today()

fund_search_path = "http://fundsuggest.eastmoney.com/FundSearch/api/FundSearchPageAPI.ashx"
searchKey = "生物"
param = {'m': 0, 'key': searchKey, 'pagesize': 17}

result = func_httprequest(fund_search_path, param)

for data in result.json()['Datas']['FundList']:
    # print(data['_id'])
    id = data['_id']
    fund_content_url = "http://fund.eastmoney.com/%s.html" % id
    fund_content_result = func_httprequest_bs4(fund_content_url, "gb2312")
    fund_stock_top10_list = fund_content_result.select("#position_shares > div.poptableWrap > table > tr ")

    for stock_data in fund_stock_top10_list:
        func_result=False
        if (stock_data.contents[1].name == "th"):
            continue
        stock_name = stock_data.td.a.text

        stock_url = stock_data.td.a['href']
        stock_url_result = func_httprequest_bs4(stock_url, "gb2312")

        stock_data_db = {}

        stock_data_db['date'] = today

        #stock_data_db['stock_name'] = stock_url_result.select('#name')[0].text
        func_result = func_bs4_select(stock_url_result,'#name', stock_data_db['stock_name'], 0)
        if (func_result == False):
            print('Error')

        stock_infos = stock_url_result.select('div.w578 > div.cwzb > table > tbody > tr > td')

        stock_id =stock_url_result.select('#code')[0].text
        stock_price_request_url = "http://nufm.dfcfw.com/EM_Finance2014NumericApplication/JS.aspx?&type=CT&sty=GB20GFBTC&st=z&js=((x))&token=4f1862fc3b5e77c150a2b985b12db0fd&cmd=%s1" % stock_id
        stock_price_result = func_httprequest(stock_price_request_url, {}).text
        if len(stock_price_result) <= 5:
            print ('stock name' + stock_data_db['stock_name'])
        stock_data_db['price'] =stock_price_result[5]
        print('start ' + stock_data_db['stock_name'] + ' fund id'+id)
        try:
            # 总市值
            stock_data_db['total_mkt_cap'] = stock_infos[1].text
            # 净资产
            stock_data_db['net_asset'] = stock_infos[2].text
            # 净利润
            stock_data_db['net_profit'] = stock_infos[3].text
            # 市盈率
            stock_data_db['PER_shi_ying_lv'] = stock_infos[4].text
            # 市净率
            stock_data_db['PB_shi_jing_lv'] = stock_infos[5].text
            # 	毛利率
            stock_data_db['GB_mao_li_lv'] = stock_infos[6].text
            # 净利率
            stock_data_db['net_profit_lv'] = stock_infos[7].text
            # ROE
            stock_data_db['ROE'] = stock_infos[8].text

            # update insert data
            # res = db.biotech_company.update_one({'stock_name':stock_data_db['stock_name']}, {'$set':stock_data_db}, upsert=True)
            # print(res)
            pprint.pprint(stock_data_db)
        except ValueError:
            message = "stock name :%s, fund name:%s" % stock_data_db['stock_name'] % id
            print(message)

