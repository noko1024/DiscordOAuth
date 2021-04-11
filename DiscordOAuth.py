import requests
from flask import Flask, json,request,make_response,jsonify,redirect,render_template
#apacheパイセンがよしなになってくれそう
#from flask_sslify import SSLify
import os
import sqlite3
import qrcode
import random
import string
import base64
from io import BytesIO

from requests import status_codes

#SSL関係はあぱっちパイセンに任せてるのでローカル環境ではcode 400 Bad Request

#---config.json読み込み---
configPath = os.path.join(os.path.split(os.path.realpath(__file__))[0],"config")

#with open(os.path.join(configPath,"HealthCheck-Config.json"))as d:
#    f = d.read()
#    data = json.loads(f)

ClientID = 678694209057980467
ClientSecret = "JL5nbj6qCyO3j77R-eox7IHeXNly6msU"
botToken = "Njc4Njk0MjA5MDU3OTgwNDY3.XkmhPA.hiCytsZowRx3sm59Al2AazYR4MM"
guildID = "830565829895782440"
roleID = "830566515392249857"
redirectURL = "https://discord.com/api/oauth2/authorize?client_id=678694209057980467&redirect_uri=https%3A%2F%2Fapi.noko1024.net%2FOAuth&response_type=code&scope=identify%20guilds"

oneTimeURL = []

requests.packages.urllib3.util.ssl_.DEFAULT_CIPHERS += "HIGH:!DH:!aNULL"
app = Flask(__name__)

#sslify = SSLify(app)

basePath = os.path.dirname(__file__)

@app.route("/gen")
def OneTimeURLGenerate():
    global oneTimeURL
    onetime = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
    accessURL = "https://api.noko1024.net/want?param="+onetime
    oneTimeURL.append(onetime)
    img = qrcode.make(accessURL)

    # 画像書き込み用バッファを確保して画像データをそこに書き込む
    buf = BytesIO()
    img.save(buf,format="png")
    # バイナリデータをbase64でエンコードし、それをさらにutf-8でデコードしておく 
    qr_b64str = base64.b64encode(buf.getvalue()).decode("utf-8")
    # image要素のsrc属性に埋め込めこむために、適切に付帯情報を付与する
    qr_b64data = "data:image/png;base64,{}".format(qr_b64str)
    print("GEN-ONETIMEURL")
    print(oneTimeURL)
    return render_template("QR.html",qr_b64data=qr_b64data)





@app.route("/want")
def AuthWait():
    global oneTimeURL
    accessOpt = request.args.get('param', default = None, type = str)
    print("Want-Access")
    print(accessOpt)
    print("Want-onetimeurl")
    print(oneTimeURL)
    if accessOpt in oneTimeURL:
        oneTimeURL.remove(accessOpt)
        return redirect(redirectURL)
    else:
        return "404"

#OAuth認証(ベアラートークン取得→アクセストークン取得→データ照会)
@app.route("/OAuth")
def OAuth():
    #リダイレクトでベアラートークンをもらう
    code = request.args.get('code', default = None, type = str)
    
    if code is None:
        return "NONE"

    data = {
        'client_id': ClientID,
        'client_secret': ClientSecret,
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': "https://api.noko1024.net/OAuth",
        'scope': 'identify guilds'
    }
    headers_token = {
        'Content-Type':'application/x-www-form-urlencoded'
    }
    
    #アクセストークンを取得(dict)
    userAccessToken = requests.post('https://discord.com/api/v8/oauth2/token', data=data, headers=headers_token).json()

    #ユーザーデータ取得用
    headers = {
        "Authorization": "Bearer %s" % userAccessToken["access_token"]
    }
    
    #ユーザー情報を取得(dict)
    userInfo = requests.get("https://discord.com/api/users/@me", headers=headers).json()

    #所属サーバー一覧を取得(List内部にdict)
    userGuild :json = requests.get("https://discord.com/api/users/@me/guilds", headers=headers).json()
    #print(userGuild)

    #トークン破棄用
    headers_token = {
        'Content-Type':'application/x-www-form-urlencoded',
        "Authorization": "Bearer %s" % userAccessToken["access_token"]
    }
    data = {
        'client_id': ClientID,
        'client_secret': ClientSecret,
        'token': userAccessToken["access_token"]
    }
    
    #トークンを無効化
    requests.post("https://discord.com/api/oauth2/token/revoke", headers=headers_token, data=data)

    #プロ研に属していなかったら
    if not [x for x in userGuild if x["id"] == "565666930493489184"]:
        return "NOTPROKEN"

    #HTTPS使えない説　削除成功しているか？
    status = requests.delete("https://discord.com/api/guilds/"+guildID+"/members/"+userInfo["id"]+"/roles/"+roleID,headers=headers).status_code
    if status == 204:
        return "成功しました。"

    return status

if __name__ == "__main__":
	app.run(debug=True)
