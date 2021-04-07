import requests
from flask import Flask, json,request,make_response,jsonify
import os


requests.packages.urllib3.util.ssl_.DEFAULT_CIPHERS += "HIGH:!DH:!aNULL"
app = Flask(__name__)
basePath = os.path.dirname(__file__)




#OAuth認証(ベアラートークン取得→)
@app.route("/")
def OAuth():
    #リダイレクトでベアラートークンをもらう
    code = request.args.get('code', default = None, type = str)
    
    if code is None:
        return "NONE"

    data = {
        'client_id': 776864066370404363,
        'client_secret': "u6Vrf2Lem8tyS5XLS8_DEdYv1pZweTMb",
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': "https://api.noko1024.net",
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
    print(userGuild)

    #トークン破棄用
    headers_token = {
        'Content-Type':'application/x-www-form-urlencoded',
        "Authorization": "Bearer %s" % userAccessToken["access_token"]
    }
    data = {
        'client_id': 776864066370404363,
        'client_secret': "fv24yLGLxX93CjtLpnfYZTJUwXT7s7iv",
        'token': userAccessToken["access_token"]
    }
    
    #トークンを無効化
    requests.post("https://discord.com/api/oauth2/token/revoke", headers=headers_token, data=data)

    #プロ研に属していなかったら
    if not [x for x in userGuild if x["id"] == "565666930493489184"]:
        return "NOTPROKEN"

    return userInfo


if __name__ == "__main__":
	app.run()
