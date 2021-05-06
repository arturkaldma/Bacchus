from flask import Flask, render_template, request, redirect, url_for
import requests
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
from datetime import datetime, timedelta

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://cjnaglylwdcgyi:bfd5c6972a45975ae28985d950e886c6dffae0bc29fe2d9841529a74c2839e48@ec2-52-209-134-160.eu-west-1.compute.amazonaws.com:5432/dbt5fnncj7i0ua?sslmode=require'

db = SQLAlchemy(app)

def get_info():
    resp = requests.get('http://uptime-auction-api.azurewebsites.net/api/Auction/')
    updated_json = resp.json()
    for entry in updated_json:
        datetime_str = entry["biddingEndDate"]
        datetime_object = datetime.strptime(datetime_str, '%Y-%m-%dT%H:%M:%SZ')
        hours = 3
        hours_added = timedelta(hours = hours)
        real_time = (datetime_object + hours_added)
        calculate_time = (real_time - datetime.now())
        calculate_time2 = datetime.strptime(str(calculate_time), "%H:%M:%S.%f")
        time_left_base = calculate_time2.strftime("%H:%M:%S")
        formula = sum(x * int(t) for x, t in zip([3600, 60, 1], str(time_left_base).split(":")))
        if formula > 3600:
            entry["biddingEndDate"] = (calculate_time2.strftime("%H hours %M minutes %S seconds"))
        elif formula > 60:
            entry["biddingEndDate"] = (calculate_time2.strftime("%M min %Ss"))
        else:
            entry["biddingEndDate"] = (calculate_time2.strftime("%Ss"))
    return updated_json

def removeduplicate(it):
    seen = []
    for i in range(len(it)):
        try:
            if it[i]["productCategory"] not in it and it[i]["productCategory"] not in seen:
                seen.append(it[i]["productCategory"])
        except IndexError:
            pass
    return seen



class Data(db.Model):
    __tablename__ = "data"
    id = db.Column(db.Integer, primary_key=True)
    productId_ = db.Column(db.String)
    customerId_ = db.Column(db.String(120))
    bid_ = db.Column(db.FLOAT)

    def __init__(self, productId_, customerId_, bid_):
        self.productId_ = productId_
        self.customerId_ = customerId_
        self.bid_ = bid_


@app.route('/', methods=["POST","GET"])
def index():
    if request.method == 'POST':
        productId = request.form["productId"]
        customerId = (request.form["customer_name"]).replace(" ", "") + datetime.now().strftime("%d%m%y-%H:%M")
        bid = request.form["bid"]
        data = Data(productId, customerId, bid)
        db.session.add(data)
        db.session.commit()
        return render_template("index.html", updated_json=get_info(), b=removeduplicate(get_info()))
    return render_template("index.html", updated_json=get_info(), b=removeduplicate(get_info()))

@app.route("/getcat/", methods=["POST","GET"])
def getcat():
    if request.method == 'POST':
        category = request.form["category"]
        print(category)
        return redirect(url_for('category', category = category))

@app.route("/<category>")
def category(category):
    return render_template("index.html", updated_json=get_info(), b=removeduplicate(get_info()), category=category)

@app.route('/admin', methods=["POST","GET"])
def admin():
    if request.method == 'POST':
        uname = request.form["username"]
        pword = request.form["password"]
        if uname == "qwe" and pword == "123":
            a = Data.query.all()
            results = [
                {
                    "product": i.productId_,
                    "customer": i.customerId_,
                    "bid": i.bid_
                } for i in a ]
            return render_template("admin.html", ok=results)
    if request.method == 'GET':
        return render_template("admin.html")

if __name__ == '__main__':
    app.run()
