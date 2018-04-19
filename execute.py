import json
import inagoBot

if __name__ == '__main__':

    inagoBot = inagoBot.InagoBot()

    #Jsonファイルの読み込み
    inagoBot.readData()
    #実行
    inagoBot.execute()

