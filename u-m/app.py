from detection import detect_vehicles
from flask import Flask, render_template, request,session,redirect,url_for,flash
from ocv import perform_detection
import os
import sqlite3
from geopy import distance
from geopy.geocoders import Nominatim
import geocoder
import json
import base64
from PIL import Image

import folium
import requests
import time


app = Flask(__name__)

app.secret_key="testsession"

DB_NAME = '../database/accounts.db'
if not os.path.exists(DB_NAME):
    conn=sqlite3.connect(DB_NAME)
    c=conn.cursor()
    c.execute('''CREATE TABLE accounts (username TEXT, password TEXT, email TEXT, vtype TEXT)''')
    conn.commit()
    conn.close()
    
g = geocoder.ip('me')

@app.route('/login',methods=['GET','POST'])
def login():
    if request.method == 'POST':
        email=request.form['email']
        password=request.form['password']
        
    # if email=='admin@admin' and password=='admin':
    #     session['admin']=True
    #     return render_template('manager/index.html',admin=True)
        
        conn=sqlite3.connect(DB_NAME)
        c=conn.cursor()
        c.execute("select * from accounts where email=? and password=?",(email,password))
        account=c.fetchone()
        conn.close()
        
        if account is not None and email == account[2] and password == account[1]:
            session['email']=account[2]
            session['username']=account[0]
            print(f"session username={session['username']}\nsession email={session['email']}")
            session['d']=1
            # return render_template('users/home.html',username=session['username'],email=session['email'],active_page='home')
            return redirect(url_for('index'))
        else:
            print("Couldn't find email and password")
            return redirect(url_for('index'))

@app.route('/to-login')
def to_login():
    return render_template('login.html')
         
         
def locate(items): #home-map
    red_marker_coords = (g.lat,g.lng)
    
    # Create a Folium map centered on the red marker location
    map = folium.Map(location=red_marker_coords, zoom_start=30)

    # Add a red marker for the current location
    folium.CircleMarker(
        location=red_marker_coords,
        # Adjust the radius to your desired size
        popup='Your Location',
        radius=100,
        color='red',
        fill=True,
        fill_color='red',
        icon=folium.Icon(color='red')
    ).add_to(map)
    
    green_marker_coords=[]
    for item in items:
        print("dictionary:",item[2])
        json_data = json.loads(item[2])
        latitude = json_data['latitude']
        longitude = json_data['longitude']
        green_marker_coords.append((latitude,longitude))
    
        print("dictionary datas:",green_marker_coords)
    

    for i, coords in enumerate(green_marker_coords):
        folium.Marker(location=coords, popup=f'Destination {i+1}', icon=folium.Icon(color='green',icon="ok-sign")).add_to(map)
      
    map_html = map._repr_html_()
   
    return map_html
 
def locate_parking(latitude,longitude,name): #parking-map
    green_marker = (latitude,longitude)
    
    # Create a Folium map centered on the red marker location
    map2 = folium.Map(location=green_marker, zoom_start=40)


    folium.Marker(
        location=green_marker,

        popup=f"{name}",
        icon=folium.Icon(color="green", icon="ok-sign")
    ).add_to(map2)
          
    parking_map_html = map2._repr_html_()
   
    return parking_map_html   

@app.route('/',methods=['GET','POST'])
def index():
   
    # if session.get('admin'):
    #     return render_template('manager/index.html')
    if session.get('username'):
        
        if request.method == 'POST':
            D=request.form['filter_range']
            session['d']=float(D)
            # print("new d=",d)
        d=session['d']
        
        g = geocoder.ip('me')
        print(g.latlng)        
        
        conn=sqlite3.connect(DB_NAME)
        c=conn.cursor()
        c.execute("select mid,parking_name,parking_loc,slot1,slot2 from managers WHERE approval=1")
        lists=c.fetchall()
        conn.close()
        
        # print(lists)
        items=[]
        for list in lists:
            if list[2] != None:
                jlist=json.loads(list[2])
                jcheck1=json.loads(list[3])
                jcheck2=json.loads(list[4])
                full1=jcheck1.get('motorcycle')+jcheck1.get('car')+jcheck1.get('truck')
                full2=jcheck2.get('motorcycle')+jcheck2.get('car')+jcheck2.get('truck')
                print("full1:",full1)
                print("full2:",full2)
                
                if full1!=jcheck1.get('t1') or full2!=jcheck2.get('t1'):
                    p1=(jlist.get('latitude'),jlist.get('longitude'))
                    p2=(g.lat,g.lng)
                    dist = distance.distance(p1, p2).kilometers
                    dist = round(dist, 3) 
                    list_with_dist = list + (dist,)
                    print(dist)
                    if d == 0:
                        print("runingggggggggggggg")
                        items.append(list_with_dist)
                    if d > 0 and dist <=d:
                        items.append(list_with_dist)
                    m=locate(items)
                    
        print("items:",items)               
        
        return render_template('users/home.html',username=session['username'],items=items,d=d,map=m)

    return render_template('welcome.html')
    
@app.route('/filter',methods=['GET'])
def filter():
    if request.method == 'GET':
        D=request.args['filter_range']
        print("D=",D)
        d=D
    return redirect(url_for('index'))

@app.route('/profile')
def profile():
    
    conn=sqlite3.connect(DB_NAME)
    c=conn.cursor()
    c.execute("select email,vtype from accounts where username=?",(session['username'],))
    profile=c.fetchone()
    conn.close()
    
    return render_template('profile.html',username=session['username'],profile=profile, active_page='profile')

@app.route('/map',methods=['GET','POST'])
def map_page():
    items=[]
    if request.method == 'POST':
        mid=request.form['mid']
        pname=request.form['pname']
        print("mid:",mid)
        print("pname:",pname)
        address=request.form['address']
        conn=sqlite3.connect(DB_NAME)
        c=conn.cursor()
        c.execute("SELECT parking_name,parking_loc,slot1,slot2 FROM managers WHERE mid=? AND approval = 1",(mid,))
        lists=c.fetchone()
        # conn.close()
        jmdata = json.loads(lists[1])
        js1data = json.loads(lists[2])
        js2data = json.loads(lists[3])
        print("slot1:",js1data)
        print("slot2:",js2data)
        print(lists[0])
        latitude = jmdata['latitude']
        longitude = jmdata['longitude']
        items=(latitude,longitude)
        direction_link=f"https://www.google.co.in/maps/dir/{g.lat},{g.lng}/{latitude},{longitude}/"
        geolocator = Nominatim(user_agent='http')
        location = geolocator.reverse((latitude,longitude))
        mapl=locate_parking(latitude,longitude,lists[0])
        print(location)
        print(mid)
        c.execute("SELECT s1_predict,s2_predict FROM parking_data WHERE manager_id =?", (mid,))
        images = c.fetchone()
        # print("images",images)
        conn.close()

        decoded_images = []
        if images is not None:
            print("working image")
            if images[0] is not None:
                print("working image0")
                img_data1 = base64.b64encode(images[0]).decode('utf-8')
                decoded_images.append(img_data1)
            else:
                decoded_images.append('')
            
            if images[1] is not None:
                print("working image1")
                img_data2 = base64.b64encode(images[1]).decode('utf-8')
                decoded_images.append(img_data2)
            else:
                decoded_images.append('')
        else:
            decoded_images = ['', '']  # Assign empty values for images when no record is found
            
        
        return render_template('users/map.html', pname=pname,id=mid,address=location,items=items,direction_link=direction_link,mapl=mapl,s1=js1data,s2=js2data,images=decoded_images)
    return redirect(url_for('index'))



@app.route('/logout')
def logout():
    session.pop('username', None)
    flash(f"logout successful")
    # return redirect('/')
    return redirect(url_for('index'))

@app.route('/manager/logout')
def admin_logout():
    session.pop('mid', None)
    session.pop('mname',None)
    flash(f"logout successful")
    # return redirect('/')
    return redirect(url_for('index'))
    
@app.route('/register',methods=['GET','POST'])
def register():
    if request.method == 'POST':
        username=request.form['username']
        password=request.form['password']
        email=request.form['email']
        vtype=request.form['vtype']
        
        conn=sqlite3.connect(DB_NAME)
        c=conn.cursor()
        c.execute("INSERT INTO accounts VALUES (?,?,?,?)",(username,password,email,vtype))
        conn.commit()
        conn.close()
        flash(f"Account creation completed successfully. Please login using user login.")
        # return render_template('success.html')
        return redirect(url_for('index'))
    
    return render_template('register.html')

@app.route('/register/manager',methods=['GET','POST'])
def register_m():
    if request.method == 'POST':
        mname=request.form['username']
        p_name=request.form['parking']
        mpassword=request.form['password']
        memail=request.form['email']
        latitude=g.lat
        longitude=g.lng
        
        loc={"latitude": latitude,"longitude": longitude}
        data = {'t1': 0 ,'tmc' : 0 ,'tc' : 0 , 'tt' : 0 ,'motorcycle' : 0 , 'car' : 0 , 'truck' : 0 }
        
        json_data = json.dumps(loc)
        json_data2 = json.dumps(data)
        
        conn=sqlite3.connect(DB_NAME)
        c=conn.cursor()
        c.execute("INSERT INTO managers (mname, parking_name, memail, mpassword, slot1, slot2, approval,parking_loc) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
          (mname, p_name, memail, mpassword, json_data2, json_data2, 0,json_data))

        conn.commit()
        conn.close()
        flash(f"Account creation completed successfully. Please contact the admin for approval: example@gmail.com")

        return redirect(url_for('index'))
    
    return render_template('/manager/register_m.html')

@app.route('/manager/login',methods=['GET','POST'])
def m_login():
    if request.method == 'POST':
        memail = request.form['email']
        mpassword = request.form['password']
        
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("SELECT * FROM managers WHERE memail=? AND mpassword=?", (memail, mpassword))
        manager = c.fetchone()
        conn.close()
        
        if manager:
            if manager[7] == 0:
                flash("Manager is not approved.")
            else:
                session['mid'] = manager[0]
                session['mname'] = manager[1]
                flash("Login successful.")
                return redirect(url_for('home_m'))
        else:
            flash("Invalid email or password.")
            
    return render_template('/manager/login_m.html')

@app.route('/home')
def home():
    if 'username' in session:
        username = session['username']
        print(username)
        g = geocoder.ip('me')
        print(g)
        return render_template('home.html', username=username,latitude =g.lat , Longitude=g.lng)

    return redirect('/login')

@app.route('/manager/home',methods=['GET','POST'])
def home_m():
    if session.get('mid') is None :
        return render_template('login.html')
    
    
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT * FROM managers WHERE mid=?", (session['mid'],))
    manager = c.fetchone()
    conn.close()
    print(manager[5])
    
    slot1 = json.loads(manager[5])
    slot2 = json.loads(manager[6])
    location = json.loads(manager[8])
    
    map3 = locate_parking(location.get('latitude'), location.get('longitude'), manager[2])
    
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT * FROM parking_data WHERE manager_id =?", (session['mid'],))
    images = c.fetchone()
    conn.close()

    decoded_images = []
    if images is not None:
        if images[2] is not None:
            img_data1 = base64.b64encode(images[2]).decode('utf-8')
            decoded_images.append(img_data1)
        else:
            decoded_images.append('')
        
        if images[3] is not None:
            img_data2 = base64.b64encode(images[3]).decode('utf-8')
            decoded_images.append(img_data2)
        else:
            decoded_images.append('')
    else:
        decoded_images = ['', '']  # Assign empty values for images when no record is found

    return render_template('/manager/home_m.html', id=session['mid'], manager=manager, location=location, slot1=slot1, slot2=slot2, images=decoded_images, map3=map3)

 
@app.route('/manager/update/location',methods=['POST'])       
def update_location_m():
    if request.method == 'POST':

        lat = request.form['lat']
        lng = request.form['lng']
    
        print(lat,lng)
        
        ldata={"latitude": lat, "longitude": lng}
        ljdata = json.dumps(ldata)

        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("UPDATE managers SET parking_loc=? WHERE mid=?", (ljdata, session['mid']))
        conn.commit()
        conn.close()
    return redirect(url_for('home_m')) 
 
    
@app.route('/manager/update/slot-1',methods=['POST'])       
def update_slot_1():
    if request.method == 'POST':

        tc = request.form['tc']
        tt = request.form['tt']
        tm = request.form['tm']
        print(tc,tt,tm)
        
        data={'t1': int(tc)+int(tt)+int(tm), 'tmc': int(tm), 'tc': int(tc), 'tt': int(tt), 'motorcycle': 0, 'car': 0, 'truck': 0}
        jdata = json.dumps(data)

        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("UPDATE managers SET slot1=? WHERE mid=?", (jdata, session['mid']))
        conn.commit()

        c.execute("SELECT * FROM managers WHERE mid=?", (session['mid'],))
        manager = c.fetchone()
        print("managers:", manager)

        conn.close()
    return redirect(url_for('home_m'))
        
@app.route('/manager/update/slot-2',methods=['POST'])       
def update_slot_2():
    if request.method == 'POST':
            
        tc2 = request.form['tc2']
        tt2 = request.form['tt2']
        tm2 = request.form['tm2']
        print(tc2,tt2,tm2)
        truck2=int(tt2) 
        data={'t1': int(tc2)+int(tt2)+int(tm2), 'tmc': int(tm2), 'tc': int(tc2), 'tt': truck2, 'motorcycle': 0, 'car': 0, 'truck': 0}
        
        
        jdata = json.dumps(data)

        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("UPDATE managers SET slot2=? WHERE mid=?", (jdata, session['mid']))
        conn.commit()

        c.execute("SELECT * FROM managers WHERE mid=?", (session['mid'],))
        manager = c.fetchone()
        print("managers:", manager)

        conn.close()
    return redirect(url_for('home_m'))
    
@app.route('/manager/update/upload-1', methods=['POST'])
def upload_image_1():
    if request.method == 'POST':
        image = request.files['image']
        if image:
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute("SELECT * FROM parking_data WHERE manager_id=?", (session['mid'],))
            images = c.fetchone()
            if images is None:
                c.execute("INSERT INTO parking_data (manager_id, s1photo) VALUES (?, ?)", (session['mid'], image.read()))
            else:
                c.execute("UPDATE parking_data SET s1photo = ? WHERE manager_id = ?", (image.read(), session['mid']))
            conn.commit()
            conn.close()
        else:
            print("No image uploaded")
    return redirect(url_for('home_m'))

@app.route('/manager/update/upload-2', methods=[ 'POST'])
def upload_image_2():
    if request.method == 'POST':
        image2 = request.files['image2']
        if image2:
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute("UPDATE parking_data SET s2photo=? WHERE manager_id=?", (image2.read(),session['mid'],))
            conn.commit()
            conn.close()
        else:
            print("error")

   
    return redirect(url_for('home_m'))



def convert_data(data, file_name):
    with open(file_name, 'wb') as file:
        file.write(data)
    img = Image.open(file_name)
    print(img)
 
@app.route('/manager/detect',methods=['GET'])
def detect():
    slot= request.args.get('slot')
    detection=(0,0,0)
    print("passed:",slot)
    if not os.path.exists('Static/Images/') :
        print("not")
        try: 
            os.makedirs('Static/Images/slot1')
            os.makedirs('Static/Images/predict1')
            os.makedirs('Static/Images/slot2')
            os.makedirs('Static/Images/predict2')
            
        except OSError as error: 
            print(error)

    try:
        con = sqlite3.connect(DB_NAME)
        cursor = con.cursor()
        cursor.execute("SELECT s1photo,s2photo FROM parking_data WHERE manager_id=?",(session['mid'],))
        photos = cursor.fetchone()
        
        if slot == 'slot1' :
            convert_data(photos[0], 'Static/Images/slot1/image1.jpg')
            imgpath= 'Static/Images/slot1/image1.jpg'
            predictpath= 'Static/Images/predict1/'
            pimg='predict1.jpg'
            detection=detect_vehicles(imgpath,predictpath,pimg,slot)
        elif slot == 'slot2' :
            convert_data(photos[1], 'Static/Images/slot2/image2.jpg')
            imgpath= 'Static/Images/slot2/image2.jpg'
            predictpath= 'Static/Images/predict2/'
            pimg='predict2.jpg'
            detection=detect_vehicles(imgpath,predictpath,pimg,slot)
        
    except Exception as e:
        print(e)
        
    finally:
        con.close()
        
    return render_template('manager/detect.html',value=detection,slot=slot)

@app.route('/manager/detect/submit', methods=['POST'])
def detect_submit():
    print("testing detect")
    if request.method == 'POST':
        car = request.form.get('car', 0)
        truck = request.form.get('truck', 0)
        motorcycle = request.form.get('motorcycle', 0)
        slot = request.form.get('slot')

        try:
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            if slot == 'slot1':
                cursor.execute("SELECT slot1 FROM managers WHERE mid=?", (session['mid'],))
                slot_data = cursor.fetchone()
                jslots = json.loads(slot_data[0])
                jslots['motorcycle'] = int(motorcycle)
                jslots['car'] = int(car)
                jslots['truck'] = int(truck)
                new_slot_data = json.dumps(jslots)
                image_path = os.path.join(app.static_folder, 'images', 'predict1', 'predict1.jpg')
                with open(image_path, 'rb') as image_file:
                    image_data = image_file.read()
                cursor.execute("UPDATE parking_data SET s1_predict=? WHERE manager_id=?", (image_data, session['mid']))
                conn.commit()

                cursor.execute("UPDATE managers SET slot1=? WHERE mid=?", (new_slot_data, session['mid']))
                conn.commit()
                
                
            elif slot == 'slot2':
                cursor.execute("SELECT slot2 FROM managers WHERE mid=?", (session['mid'],))
                slot_data = cursor.fetchone()
                jslots = json.loads(slot_data[0])
                jslots['motorcycle'] = int(motorcycle)
                jslots['car'] = int(car)
                jslots['truck'] = int(truck)
                new_slot_data = json.dumps(jslots)
                image_path = os.path.join(app.static_folder, 'images', 'predict2', 'predict2.jpg')
                with open(image_path, 'rb') as image_file:
                    image_data = image_file.read()
                cursor.execute("UPDATE parking_data SET s2_predict=? WHERE manager_id=?", (image_data, session['mid']))
                conn.commit()
                
                cursor.execute("UPDATE managers SET slot2=? WHERE mid=?", (new_slot_data, session['mid']))
                conn.commit()
                
                
            flash("Slot data updated successfully.")
        except Exception as e:
            print(e)
            flash("Error occurred while updating slot data.")
        finally:
            conn.close()

    return redirect(url_for('home_m'))


@app.route('/manager/delete_account',methods=['GET','POST'])       
def delete_account_m():
    if request.method == 'POST':

        passw = request.form['pass']
        repassw = request.form['repass']
    
        print(passw,repassw)
        
        if passw == repassw:
            time.sleep(5)
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM managers WHERE mid = ?", (session['mid'],))
            conn.commit()
            conn.close()
            session.pop('mid', None)
            session.pop('mname',None)
            return render_template('success.html') 
    return render_template('manager/delete.html')


@app.route('/users/delete_account',methods=['GET','POST'])       
def delete_account():
    if request.method == 'POST':

        passw = request.form['pass']
        repassw = request.form['repass']
    
        print(passw,repassw)
        
        if passw == repassw:
            time.sleep(5)
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM accounts WHERE username = ?", (session['username'],))
            conn.commit()
            conn.close()
            session.pop('username', None)
            return render_template('success.html') 
    return render_template('users/delete.html')

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'mp4', 'avi', 'mov'}

UPLOAD_FOLDER = 'Static/Video'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/manager/video', methods=['GET', 'POST'])
def video_detection():
    if request.method == 'POST':
        if 'video' not in request.files:
            return render_template('manager/video.html',username=session['mid'], message='No file selected.',pd='',filename='')
        file = request.files['video']
        if file.filename == '':
            return render_template('manager/video.html',username=session['mid'], message='No file selected.',pd='',filename='')
        if not allowed_file(file.filename):
            return render_template('manager/video.html',username=session['mid'], message='Invalid file type.',pd='',filename='')

        file.save(os.path.join(app.config['UPLOAD_FOLDER'], file.filename))
        print("filename:",file.filename)

        return render_template('manager/video.html',username=session['mid'], message='File uploaded successfully.',filename=file.filename,pd='')

    return render_template('manager/video.html',username=session['mid'],message='0',pd='',filename=None)

@app.route('/manager/video/detection',methods = ['GET','POST'])
def ocv_detection():
    
    if request.method == 'POST':
        fm = request.form['filename']
        print("filename passed:",fm)
        video_file = "Static/Video/"+fm
        data_file = "Data/coordinates.yml"
        start_frame = 10
        pd = perform_detection(video_file, data_file, start_frame)
        predict_image="Video/Video_predict/detection_image.jpg"
        return render_template('manager/video.html',username=session['mid'],message='0',pd=pd,predict_image=predict_image)



def read_image_file(file_path):
    with open(file_path, 'rb') as f:
        image_data = f.read()
    return image_data

def insert_image_to_db(db_file, image_data):
    try:
        connection = sqlite3.connect(db_file)
        cursor = connection.cursor()

        # Insert the image into the database table
        cursor.execute("UPDATE parking_data SET s1photo=? WHERE manager_id=?", (image_data, session['mid']))
        connection.commit()

        print("Image uploaded to database successfully!")

    except sqlite3.Error as e:
        print(f"Error uploading image: {e}")

    finally:
        if connection:
            connection.close()

@app.route('/manager/video/detection/submit',methods = ['GET','POST'])
def ocv_submit():
    if request.method == 'POST':
        op = request.form['Occupied']
        ept = request.form['Empty']
        print(f'op={op},ept={ept}')
        
        data={'t1': int(op)+int(ept), 'tmc': 0, 'tc': int(op)+int(ept), 'tt': 0, 'motorcycle': 0, 'car': int(op), 'truck': 0}
        jdata = json.dumps(data)
        data2={'t1':0, 'tmc':0, 'tc':0, 'tt':0, 'motorcycle':0, 'car':0, 'truck':0}
        jdata2 = json.dumps(data2)
        
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("UPDATE managers SET slot1=?,slot2=? WHERE mid=?", (jdata,jdata2, session['mid']))
        conn.commit()
        
        predict_image="Static/Video/Video_predict/detection_image.jpg"
        image_data = read_image_file(predict_image)
        insert_image_to_db(DB_NAME, image_data)

        return redirect(url_for('home_m'))
    
@app.route('/manager/reset/section1',methods = ['GET','POST'])
def reset_section1():

    conn = sqlite3.connect(DB_NAME)
    c=conn.cursor()
    data1={'t1':0, 'tmc':0, 'tc':0, 'tt':0, 'motorcycle':0, 'car':0, 'truck':0}
    jdata1 = json.dumps(data1)
    c.execute("UPDATE managers SET slot1=? WHERE mid=?",(jdata1,session['mid']))
    conn.commit()
    print("manager update working")
    c.execute("UPDATE parking_data SET s1photo=NULL WHERE manager_id=?",(session['mid'],))
    print("parkingdata photo update working")
    conn.commit()
    c.execute("UPDATE parking_data SET s1_predict=NULL WHERE manager_id=?",(session['mid'],))
    print("parkingdata predict update working")
    conn.commit()

    conn.close()
    return redirect(url_for('home_m'))
      
@app.route('/manager/reset/section2',methods = ['GET','POST'])
def reset_section2():

    conn = sqlite3.connect(DB_NAME)
    c=conn.cursor()
    data1={'t1':0, 'tmc':0, 'tc':0, 'tt':0, 'motorcycle':0, 'car':0, 'truck':0}
    jdata1 = json.dumps(data1)
    c.execute("UPDATE managers SET slot2=? WHERE mid=?",(jdata1,session['mid']))
    conn.commit()
    print("manager update working")
    c.execute("UPDATE parking_data SET s2photo=NULL WHERE manager_id=?",(session['mid'],))
    print("parkingdata photo update working")
    conn.commit()
    c.execute("UPDATE parking_data SET s2_predict=NULL WHERE manager_id=?",(session['mid'],))
    print("parkingdata predict update working")
    conn.commit()

    conn.close()
    return redirect(url_for('home_m'))  
       
if __name__ == '__main__':
    app.run(debug=True,port=8080)