from flask import Flask, jsonify, render_template, request
from flask_mysqldb import MySQL
from dotenv import load_dotenv
import os

app = Flask(__name__)

load_dotenv()

MYSQL_HOST = os.getenv("MYSQL_HOST")
MYSQL_USER = os.getenv("MYSQL_USER")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD")
MYSQL_DB = os.getenv("MYSQL_DB")

# MySQL configurations
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'root'
app.config['MYSQL_DB'] = 'residence'

mysql = MySQL(app)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/unsold')
def unsold():
    return render_template('unsold.html')

@app.route('/unsold-houses')
def get_unsold_houses():
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT House.house_no,House.address,
        House_info.price,House_info.area,House_info.no_of_rooms,House_info.floor,
        Owner_detail.name,Owner_detail.phone_no,Owner_detail.occupation,Owner_detail.email,Owner_detail.dob
        FROM House
        JOIN House_info ON House.Id = House_info.HId
        JOIN Owner_detail ON House_info.HId = Owner_detail.OId
        WHERE House_info.Availibility = 'unsold'
    """)
    houses = cur.fetchall()
    house_data = []
    for house in houses:
        house_dict = {
            'house_no': house[0], 
            'address': house[1],
            'price': house[2],
            'area': house[3],
            'no_of_rooms': house[4],
            'floor': house[5],
            'owner_name': house[6], 
            'phone_no': house[7],
            'occupation': house[8],
            'email': house[9],
            'dob': house[10].strftime('%Y-%m-%d'),
        }
        house_data.append(house_dict)
    return jsonify(house_data)


@app.route('/sold')
def sold():
    return render_template('sold.html')

@app.route('/search-house', methods=['POST'])
def search_house():
    house_no = request.form['house_no']
    owner_name = request.form['owner_name']
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT House.house_no,House.address, 
        Owner_detail.name,Owner_detail.phone_no,Owner_detail.occupation,Owner_detail.email,Owner_detail.dob, 
        Electricity.Amount AS electricity_consumption, 
        Water.Amount AS water_consumption
        FROM House
        JOIN House_info ON House.Id = House_info.HId
        JOIN Owner_detail ON House_info.HId = Owner_detail.OId
        LEFT JOIN Electricity ON House.Id = Electricity.Eid
        LEFT JOIN Water ON House.Id = Water.Wid
        WHERE House.House_no = %s AND Owner_detail.Name = %s
    """, (house_no, owner_name))
    house_data = cur.fetchone()
    if house_data:
        house_dict = {
                'house_no': house_data[0],
                'address': house_data[1],
                'owner_name': house_data[2],
                'phone_no': house_data[3],
                'occupation': house_data[4],
                'email': house_data[5],
                'dob': house_data[6].strftime('%Y-%m-%d'), 
                'electricity_consumption': float(house_data[7]),
                'water_consumption': float(house_data[8])
        }
        return jsonify(house_dict)
    else:
        return jsonify({'message': 'House not found or owner name does not match'})

if __name__ == '__main__':
    app.run(debug=True)