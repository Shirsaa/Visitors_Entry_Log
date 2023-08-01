from flask import Flask
from flask_mysqldb import MySQL
from flask import render_template, request, url_for, redirect, session
import mysql
from random import randint
from flask_session import Session
import datetime, time
from flask import jsonify,after_this_request, json
from werkzeug.utils import secure_filename
import os
from pathlib import Path

UPLOAD_FOLDER = "static/uploaded_images"

app = Flask(__name__)
app.debug = True

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'visitors_log'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

mysql = MySQL(app)

app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

@app.route('/add_profile', methods=['GET', 'POST'])
def profile():
    if request.method=="POST":
        name = request.form['your_name']
        gender = request.form['gender']
        age = request.form['age']
        purpose = request.form['purpose']
        person_of_interest = request.form['person_of_interest']
        organization = request.form['organization']
        address = request.form['address']
        contact = request.form['contact_number']

        cur = mysql.connection.cursor()

        query_find = "SELECT * FROM visitors WHERE Name = '{name}'".format(name=name)
        cur.execute(query_find)
        name_exists_check = cur.fetchall()

        if len(name_exists_check) == 0:

            with open('static/unique_id.txt','r') as f:
                unique_id = f.read()
            with open('static/unique_id.txt','w') as f:
                f.write(str(int(unique_id)+1))

            profile_pic = request.files['file_upload']
            filename = secure_filename(profile_pic.filename)
            profile_pic.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
            path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            print(path)


            info = (unique_id, name, gender, age, purpose, person_of_interest, organization, address, contact, path)

            query_insert = "INSERT INTO visitors (Unique_ID, Name, Gender, Age, Purpose, Person_of_Interest, Organization, Address, Contact_number, profile_pic) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"

            cur.execute(query_insert, info)

            mysql.connection.commit()
            cur.close()
            
            return render_template('add_profile.html') 
                                   
        else:
            return "profile created: go to login page"
    
    else:
        return render_template('add_profile.html')


@app.route('/profile_created', methods=['GET', 'POST'])
def view():
    if request.method=="POST":

        cur = mysql.connection.cursor()
        name_arr = request.get_json()
        print(name_arr)
        name = name_arr['name']

        query_find = "SELECT Unique_ID, Name, Gender, Age, Purpose, Person_of_Interest, Organization, Address, Contact_number, profile_pic FROM visitors WHERE Name = '{name}'".format(name = name)
        cur.execute(query_find)
        info = cur.fetchall()
        print(info)

        mysql.connection.commit()
        cur.close()

        return jsonify(info)

    return render_template('profile_created.html')




@app.route('/login', methods=['GET', 'POST'])
def retreiving_id():
    if request.method=="POST":
        cur = mysql.connection.cursor()
        name = request.form.get('name')

        query_find = "SELECT Unique_ID FROM visitors WHERE Name = '{name}'".format(name = name) 
        cur.execute(query_find)
        id = cur.fetchall()

        if len(id) != 0:
            query_still_checked_in = "SELECT Unique_ID FROM entry WHERE Check_out IS NULL AND Unique_ID = '{id}'".format(id=id[0][0])
            cur.execute(query_still_checked_in)
            checked_in = cur.fetchall()
            print(checked_in)

            inside = False
            if id == checked_in:
                inside = True

            mysql.connection.commit()
            cur.close()

            if inside == False:
                id = id[0][0]
                return render_template('login.html', show=True, id=id, name=name)
            else:
                return 'already logged in'
        else:
            return 'this name is not registered'
        
    else:
        return render_template("login.html")
        


@app.route("/login/<id>", methods=['GET', 'POST'])
def login(id):
    if request.method=="POST":
        cur = mysql.connection.cursor()
        purpose = request.form['purpose']
        person_of_interest = request.form['person_of_interest']
        organization = request.form['organization']

        query_extract = "SELECT Name FROM visitors WHERE Unique_ID = '{id}'".format(id = id)
        cur.execute(query_extract)
        past_info = cur.fetchall()
        
        name = past_info[0][0]
        current_date_time = datetime.datetime.now()
        current_time = current_date_time.strftime("%H:%M:%S")
        print(current_time)
        
        entry_data = (id, name, purpose, person_of_interest, organization, current_time)
        query_insert = "INSERT INTO entry (Unique_ID, Name, Purpose, Person_of_Interest, Organization, Check_in) VALUES (%s,%s,%s,%s,%s,%s)"
        cur.execute(query_insert, entry_data)

        mysql.connection.commit()
        cur.close()

    return render_template('login.html')
    


@app.route("/", methods=['POST', 'GET'])
def index():

    current_date = datetime.date.today()
    current_date = current_date.strftime("%Y-%m-%d")
    
    cur = mysql.connection.cursor()
    query_retreive_info = "SELECT Unique_ID, Name, Purpose, Person_of_Interest, Organization, Check_in FROM entry WHERE Date = '{current_date}'".format(current_date=current_date)
    cur.execute(query_retreive_info)
    info = cur.fetchall()
    len1 = len(info)
    try:
        len2 = len(info[0])
    except:
        len2 = 0

    current_datetime = datetime.datetime.now()
    current_time = current_datetime.strftime("%H:%M:%S")
    if request.is_json:
        req_id = request.get_json()
        # print(req_id)
        id = req_id['id']
        checkin_time = req_id['Checkin_time']
        # print(checkin_time)

        query_checkout = "UPDATE entry SET Check_out = %s WHERE Unique_ID = %s AND Date = %s AND Check_in = %s"
        data = (current_time, id, current_date, checkin_time)
        cur.execute(query_checkout, data)
    else:
        pass
    
    query_checkout_data = "SELECT Unique_ID FROM entry WHERE Check_out IS NOT NULL AND Date = '{current_date}'".format(current_date=current_date)
    cur.execute(query_checkout_data)
    checked_out= cur.fetchall()
    
    query_checkout_data_time = "SELECT Unique_ID,Check_in, Check_out FROM entry WHERE Check_out IS NOT NULL AND Date = '{current_date}'".format(current_date=current_date)
    cur.execute(query_checkout_data_time)
    checked_out_data_time= cur.fetchall()
    print(checked_out_data_time)
    
    query_checkedin = "SELECT Unique_ID FROM entry WHERE Check_out IS NULL AND Date = '{current_date}'".format(current_date=current_date)
    cur.execute(query_checkedin)
    checkedin_data = cur.fetchall()
    print(checkedin_data)

    query_checkintime = "SELECT Check_in FROM entry WHERE Check_out IS NULL AND Date = '{current_date}'".format(current_date=current_date)
    cur.execute(query_checkintime)
    checkintime = cur.fetchall()
    print(checkintime)

    mysql.connection.commit()
    cur.close()

    return render_template('index.html', info=info, len1 = len1, len2=len2, checked_out=checked_out, checkout_time = checked_out_data_time, checkedin_data = checkedin_data, checkintime=checkintime)


if __name__ == '__main__':
    app.run()