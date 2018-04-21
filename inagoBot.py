import pybitflyer
import time
import os
import json
import requests
from selenium import webdriver
#from selenium.webdriver.chrome.options import Options
#from bs4 import BeautifulSoup

class InagoBot:

    #メンバ変数の初期化
    midprice = 0
    position_midprice = 0
    pos = 0 #long:+1 short:-1 no position:0
    count = 0
    score = 0 #スコアリングシステム


    def readData(self):
        #設定の読み込み
        f = open('set.json' , 'r', encoding="utf-8")
        config = json.load(f)

        self.code = config['code']
        self.api_key = config['api_key']
        self.api_secret_key = config['api_secret_key']
        self.set_size = config['set_size']
        self.sleep_time = float(config['sleep_time'])
        self.max_count = int(config['max_count'])
        
 
    #イナゴスクレイピングメソッド
    def inagoScraping(self , driver):
        try:
            
            for buyvol in driver.find_elements_by_id("buyVolumePerMeasurementTime"):
                buy_volume = buyvol.text
            for sellvol in driver.find_elements_by_id("sellVolumePerMeasurementTime"):
                sell_volume = sellvol.text
        
            print("BUY_VOLUME: " + buy_volume + " SELL_VOLUME: " +  sell_volume)

            return (sell_volume,buy_volume)
        except:
            print("Scraping Error")
        #try-exceptはここまで
    
    #オーダーメソッド
    def placeOrder(self, api, side):
        api.sendchildorder(product_code = self.code, child_order_type = "MARKET", side = side, size = self.set_size)
        if self.pos == 1:
            log = "種別: " + str(side) + "  枚数: " + str(self.set_size) + "  レート: " + str(self.midprice) + "  利益: " + str(self.set_size * (self.midprice - self.position_midprice))
            self.writeLog(log)
            print(log)
        elif self.pos == -1:
            log = "種別: " + str(side) + "  枚数: " + str(self.set_size) + "  レート: " + str(self.midprice) + "  利益: " + str(self.set_size * (self.position_midprice - self.midprice))
            self.writeLog(log)
            print(log)

    #ログ出力メソッド
    def writeLog(self , log):
        f = open('inago.log', 'w')
        f.writelines(log)
        f.close()
    
    #実行メソッド
    def execute(self):

        print("イナゴbot始動")
        public_api = pybitflyer.API()
        api = pybitflyer.API(api_key=self.api_key , api_secret=self.api_secret_key)

        self.readData()

        #スクレイピングの事前準備
        driver = webdriver.PhantomJS(service_log_path=os.path.devnull) 
        driver.get("https://inagoflyer.appspot.com/btcmac")
        #html = driver.page_source.encode('utf-8')
        #soup = BeautifulSoup(html, "lxml") #lxmlだと爆速らしい

        while True:
            time.sleep(self.sleep_time)
            self.count = self.count + 1

            #VOLUMEの初期化
            sell_volume = 0
            buy_volume = 0

            #イナゴフライヤーをクロール
            volume = self.inagoScraping(driver)
    
            #VOLUMEの算出
            try:
                sell_volume = float(volume[0])
                buy_volume = float(volume[1])
            except:
                print('float値への変換に失敗')
                sell_volume = 0
                buy_volume = 0

            #bitflyerの現在中間価格の更新
            self.midprice = public_api.board(product_code = self.code)["mid_price"]

            health = api.gethealth(product_code="FX_BTC_JPY")
            print(health)

            if health == "SUPER BUSY" or health == "STOP":
                self.score = 0
            elif health == "VERY BUSY":
                self.score = 1
            else:
                self.score = 3
            print(health)

            #クローズ条件
            if self.pos==1 and buy_volume - sell_volume < 0:
                print("Close Long position")
                self.placeOrder(api,'SELL')
                self.pos = 0
                self.count = 0

            if self.pos==-1 and sell_volume - buy_volume < 0:
                print("Close Short position")        
                self.placeOrder(api, 'BUY')
                self.pos = 0
                self.count = 0
    
            #オーダー条件
            #long
            if self.pos==0 and self.score >= 1 and self.count >= 1 and (buy_volume - sell_volume) > 30:
                print("Long Entry")
                self.placeOrder(api ,'BUY')
                self.position_midprice = public_api.board(product_code = self.code)["mid_price"]
                self.pos = 1 #現在のポジションを更新
                self.count = 0
            #short
            if self.pos==0 and self.score >= 1 and self.count >= 1 and (sell_volume - buy_volume) > 30:
                print("Short Entry")
                self.placeOrder(api, 'SELL')
                self.position_midprice = public_api.board(product_code = self.code)["mid_price"]
                self.pos = -1 #現在のポジションを更新
                self.count = 0