from flask.helpers import get_flashed_messages, url_for
from flask.wrappers import Response
import requests
from flask import Flask, json,request,make_response,jsonify,redirect,render_template,session
#apacheパイセンがよしなになってくれそう
#from flask_sslify import SSLify
import os
import qrcode
import random
import string
import base64
from io import BytesIO
import socket

from datetime import timedelta


#SSL関係はあぱっちパイセンに任せてるのでローカル環境ではcode 400 Bad Request

#---config.json読み込み---
configPath = os.path.join(os.path.split(os.path.realpath(__file__))[0],"config")

with open(os.path.join(configPath,"HealthCheck-Config.json"))as d:
    f = d.read()
    data = json.loads(f)

ClientID = data["CLIENT_ID"]
ClientSecret = data["CLIENT_SECRET"]
botToken = data["BOT_TOKEN"]
guildID = data["GUILD_ID"]
roleID = data["ROLE_ID"]
redirectURL = data["REDIRECT_URL"]
adminRedirectURL = data["ADMIN_REDIRECT_URL"]

requests.packages.urllib3.util.ssl_.DEFAULT_CIPHERS += "HIGH:!DH:!aNULL"
app = Flask(__name__)

app.config['SECRET_KEY'] = os.urandom(24)
#sslify = SSLify(app)

basePath = os.path.dirname(__file__)


@app.errorhandler(404)
def Notfound(error):
    return render_template("418.html"),418

#@app.errorhandler(500)
#def InternalServerError(error):
#    print(error)
    #return render_template("500.html"),500
#    return error
#sessionに保存→認証
@app.route("/gen")
def OneTimeURLGenerate():
    session.permanent = True
    app.permanent_session_lifetime = timedelta(minutes=10)

    try:
        adminToken = session["token"]
    except KeyError:
        adminToken = None

    code = request.args.get("code",default = None,type = str)


    #OAuthリダイレクトのとき
    if adminToken != None and code != None or code != None:
        data = {
            'client_id': ClientID,
            'client_secret': ClientSecret,
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': "https://api.noko1024.net/gen",
            'scope': 'identify'
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

        soc = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        soc.connect(("127.0.0.1",51994))

        userID = userInfo["id"]
        soc.send(bytes("ADMINGEN-"+userID,"utf-8"))
        recv = soc.recv(4096).decode().split(",")
        soc.close()
        
        if recv[0] == "True":
            session["token"] = recv[1]
            return redirect(url_for("OneTimeURLGenerate"))

        else:
            return redirect(adminRedirectURL)

        
    #Token発行済の場合
    elif adminToken != None:
        soc = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        soc.connect(("127.0.0.1",51994))
        soc.send(bytes("ADMINAUTH-"+adminToken,"utf-8"))
        recv = soc.recv(4096).decode()
        if recv == "False":
            return render_template("404.html"),404

    
    else:
        return redirect(adminRedirectURL)

    oneTime = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
    accessURL = "http://api.noko1024.net/want?param="+oneTime
    
    soc = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    soc.connect(("127.0.0.1",51994))
    soc.send(bytes(("GEN-"+oneTime),'utf-8'))
    soc.close()
        

    img = qrcode.make(accessURL)
    # 画像書き込み用バッファを確保して画像データをそこに書き込む
    buf = BytesIO()
    img.save(buf,format="png")
    # バイナリデータをbase64でエンコードし、それをさらにutf-8でデコードしておく 
    qr_b64str = base64.b64encode(buf.getvalue()).decode("utf-8")
    # image要素のsrc属性に埋め込めこむために、適切に付帯情報を付与する
    qr_b64data = "data:image/png;base64,{}".format(qr_b64str)

    return render_template("QR.html",qr_b64data=qr_b64data)


@app.route("/want")
def AuthWait():
    session.permanent = True
    oneTime = request.args.get('param', default = None, type = str)

    if oneTime == None:
        return render_template("404.html"),404

    soc = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    soc.connect(("127.0.0.1",51994))
    soc.send(bytes(("AUTH-"+oneTime),'utf8'))
    recv = soc.recv(4096).decode()
    soc.close()

    if recv == "True":
        response = redirect(redirectURL)
        max_age = 60 * 60 * 24 * 1 # 1 days
        response.set_cookie('oneTime', value=oneTime,path="/",max_age=max_age, secure=True)
        return response

    elif recv == "False":
        return render_template("404.html"),404


#OAuth認証(ベアラートークン取得→アクセストークン取得→データ照会)
@app.route("/OAuth")
def OAuth():
    #リダイレクトでベアラートークンをもらう

    session.permanent = True
    app.permanent_session_lifetime = timedelta(minutes=10)
    
    code = request.args.get('code', default = None, type = str)
    oneTime = request.cookies.get('oneTime')


    if code == None or oneTime == None:
        return render_template("404.html"),404
    
    soc = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    soc.connect(("127.0.0.1",51994))
    soc.send(bytes(("AUTH-"+oneTime),'utf8'))
    recv = soc.recv(4096).decode()
    soc.close()

    if recv != "True":
        return render_template("404.html"),404

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
        return render_template("403.html"),403

    headers = {
        "Authorization": "Bot %s" % botToken
    }

    #削除成功しているか？
    status = requests.delete("https://discord.com/api/guilds/"+guildID+"/members/"+userInfo["id"]+"/roles/"+roleID,headers=headers).status_code
    
    if status == 204:
        soc = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        soc.connect(("127.0.0.1",51994))
        soc.send(bytes(("DEL-"+oneTime),'utf8'))
        recv = soc.recv(4096).decode()
        soc.close()
        if recv == "True":
            return render_template("200.html"),200
        else:
            print(recv)
            return render_template("500.html"),500
    else:
        print(status)
        return render_template("500.html"),500

if __name__ == "__main__":
	app.run(debug=True)