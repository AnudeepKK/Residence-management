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
MYSQL_PORT = os.getenv("MYSQL_PORT")

# MySQL configurations
app.config['MYSQL_HOST'] = MYSQL_HOST
app.config['MYSQL_USER'] = MYSQL_USER
app.config['MYSQL_PASSWORD'] = MYSQL_PASSWORD
app.config['MYSQL_DB'] = MYSQL_DB
app.config['MYSQL_PORT'] = int(MYSQL_PORT) 


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
    
    
@app.route('/add', methods=['GET', 'POST'])
def add():
    if request.method == 'POST':
        house_no = request.form['house_no']
        address = request.form['address']
        availability = request.form['availability']
        no_of_rooms = request.form['no_of_rooms']
        price = request.form['price']
        floor = request.form['floor']
        area = request.form['area']
        owner_name = request.form['owner_name']
        phone = request.form['phone']
        occupation = request.form['occupation']
        dob = request.form['dob']
        email = request.form['email']

        cur = mysql.connection.cursor()

        try:
            # Start a transaction
            cur.execute("START TRANSACTION")

            # Insert into house table
            cur.execute("INSERT INTO house(House_no, Address) VALUES (%s, %s)", (house_no, address))

            # Get the last inserted house_id (hid)
            cur.execute("SELECT LAST_INSERT_ID()")
            hid = cur.fetchone()[0]

            # Insert into house_info table
            cur.execute("INSERT INTO house_info(HId,availibility, no_of_rooms, Price, Floor,Area) VALUES (%s, %s, %s, %s, %s, %s )", (hid, availability, no_of_rooms, price, floor,area))

            # Insert into electricity table
            electricity_consumption = random.choice([75.00, 200.00, 150.00, 80.00, 300.00, 100.00, 50.00, 180.00, 220.00, 90.00, 130.00, 170.00, 95.00, 110.00, 140.00, 250.00, 180.00, 190.00, 140.00, 102.00])
            cur.execute("INSERT INTO electricity (Eid, Consumption) VALUES (%s, %s)", (hid, electricity_consumption))

            # Insert into water table
            water_consumption = random.choice([5000.00, 12000.00, 20000.00, 7500.00, 22000.00, 10500.00, 3000.00, 18000.00, 25000.00, 9000.00, 13500.00, 17000.00, 9500.00, 11000.00, 14500.00, 25500.00, 18500.00, 19500.00, 14500.00])
            cur.execute("INSERT INTO water (Wid, Consumption) VALUES (%s, %s)", (hid, water_consumption))

            # Insert into owner_detail table
            if availability == 'sold':
                cur.execute("INSERT INTO owner_detail (OId, Name, Phone_no, Occupation, DOB, Email) VALUES (%s, %s, %s, %s, %s, %s)", (hid, owner_name, phone, occupation, dob, email))
            else:
                cur.execute("INSERT INTO owner_detail (OId, Name, Phone_no, Occupation, DOB, Email) VALUES (%s, %s, %s, %s, %s, %s)", (hid, "ColonySpace", "1234568790", "Residence Overseer", "1961-07-22", "ColonySpace@gmail.com"))

            # Commit the transaction
            mysql.connection.commit()

        except Exception as e:
            # Rollback the transaction if an error occurs
            mysql.connection.rollback()
            print("Error occurred:", str(e))
            return "An error occurred while adding the house. Please try again."

        finally:
            cur.close()

        return render_template('add.html')

    return render_template('add.html')


@app.route('/update', methods=['GET', 'POST'])
def update():
    if request.method == 'POST':
        house_id = int(request.form['house_id'])
        house_no = str(request.form['house_no'])
        # Query database to get the house details
        cur = mysql.connection.cursor()
        query = "SELECT * FROM house WHERE Id = " + str(house_id) + " AND House_no = '" + house_no + "';"
        cur.execute(query)
        house = cur.fetchone()  # Fetches a tuple
        cur.close()

        if house:
            # Convert the tuple to a dictionary with appropriate keys
            house_dict = {
                'id': house[0],
                'house_no': house[1],
                'address': house[2]
                # Add other fields as needed
            }
            return render_template('update.html', house=house_dict)
        else:
            return jsonify({'message': 'House not found'})

    # If it's a GET request, simply render the search form
    return render_template('search_form.html')



@app.route('/update/<int:house_id>', methods=['GET', 'POST'])
def update_house(house_id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM house WHERE Id = %s", (house_id,))
    house = cur.fetchone()  # Fetches a tuple
    cur.close()

    # Convert the tuple to a dictionary with appropriate keys
    house_dict = {
        'id': house[0],
        'house_no': house[1],
        'address': house[2]
        # Add other fields as needed
    }

    if request.method == 'POST':
        house_no = request.form['house_no']
        address = request.form['address']
        availability = request.form['availability']
        no_of_rooms = request.form['no_of_rooms']
        price = request.form['price']
        floor = request.form['floor']
        area = request.form['area']
        owner_name = request.form['owner_name']
        phone = request.form['phone']
        occupation = request.form['occupation']
        dob = request.form['dob']
        email = request.form['email']

        cur = mysql.connection.cursor()
        cur.execute("""
            UPDATE house
            SET House_no = %s, Address = %s
            WHERE Id = %s
        """, (house_no, address, house_id))

        cur.execute("""
            UPDATE house_info
            SET availibility = %s, no_of_rooms = %s, Price = %s, Floor = %s, Area = %s
            WHERE HId = %s
        """, (availability, no_of_rooms, price, floor, area, house_id))

        if availability == 'sold':
            cur.execute("""
                UPDATE owner_detail
                SET Name = %s, Phone_no = %s, Occupation = %s, DOB = %s, Email = %s
                WHERE OId = %s
            """, (owner_name, phone, occupation, dob, email, house_id))
        else:
            # Remove owner details if the house is not sold
            cur.execute("DELETE FROM owner_detail WHERE OId = %s", (house_id,))

        mysql.connection.commit()
        cur.close()
        return redirect(url_for('index'))

    return render_template('update.html', house=house_dict)



@app.route('/delete', methods=['GET', 'POST'])
def delete():
    house_id = None  # Initialize house_id as None
    if request.method == 'POST':
        house_id = int(request.form['house_id'])
        house_no = str(request.form['house_no'])
        # Query database to get the house details
        cur = mysql.connection.cursor()
        query = "SELECT * FROM house WHERE Id = " + str(house_id) + " AND House_no = '" + house_no + "';"
        cur.execute(query)

        house = cur.fetchone()  # Fetches a tuple
        cur.close()

        if house:
            # Convert the tuple to a dictionary with appropriate keys
            house_dict = {
                'id': house[0],
                'house_no': house[1],
                'address': house[2]
                # Add other fields as needed
            }
            return render_template('delete.html', house=house_dict, house_id=house_id)  # Pass house_id to the template
        else:
            return jsonify({'message': 'House not found'})

    # If it's a GET request, simply render the search form
    return render_template('search_delete.html')


@app.route('/delete/<int:house_id>', methods=['GET', 'POST'])
def delete_house(house_id):

    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM house WHERE Id = %s", (house_id,))
    house = cur.fetchone()  # Fetches a tuple
    cur.close()

    # Convert the tuple to a dictionary with appropriate keys
    house_dict = {
        'id': house[0],
        'house_no': house[1],
        'address': house[2]
        # Add other fields as needed
    }


    if request.method == 'POST':
        cur = mysql.connection.cursor()

        # Delete record from house_info table
        cur.execute("DELETE FROM house_info WHERE HId = %s", (house_id,))

        # Delete records from electricity and water tables
        cur.execute("DELETE FROM electricity WHERE Eid = %s", (house_id,))
        cur.execute("DELETE FROM water WHERE Wid = %s", (house_id,))

        # Delete record from owner_detail table
        cur.execute("DELETE FROM owner_detail WHERE OId = %s", (house_id,))

        # Delete record from house table
        cur.execute("DELETE FROM house WHERE Id = %s", (house_id,))

        mysql.connection.commit()
        cur.close()

        return redirect(url_for('index'))
    else:
        return render_template('delete.html', house=house_dict)


if __name__ == '__main__':
    app.run(host='0.0.0.0',debug=True)
