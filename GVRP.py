from flask import Flask, render_template, url_for, request, redirect, jsonify
import pymysql.cursors
from SA_FCVRP import *
app = Flask(__name__)


@app.route('/', methods=['GET', 'POST'])
def home():
	formdata = ''
	if request.method == "POST":
		formdata = request.form['formdata']
		ntype = request.form['NodeType']
		lat = float(request.form['Latitude'])
		lon = float(request.form['Longitude'])
		dem = float(request.form['Demand'])
		connection = pymysql.connect(host='localhost',
							 user='root',
							 password='',
							 db='gvrp_db',
							 charset='utf8mb4',
							 cursorclass=pymysql.cursors.DictCursor)
		with connection.cursor() as cursor:
		# Create a new record
			cursor.execute("INSERT INTO input_table (NodeType, Latitude, Longitude, Demand) VALUES  (%s, %s, %s,%s)", (ntype, lat, lon, dem))

		connection.commit()
		connection.close()
		if formdata:
			formdata =  formdata+','+str(lat)+','+str(lon)+','+str(dem)+','+str(ntype)
		else:
			formdata =  str(lat)+','+str(lon)+','+str(dem)+','+str(ntype)
		return render_template("main.html", formdata = formdata)

	return render_template("main.html", formdata = formdata)


@app.route("/emptydb")
def emptydb():
	connection = pymysql.connect(host='localhost',
						 user='root',
						 password='',
						 db='gvrp_db',
						 charset='utf8mb4',
						 cursorclass=pymysql.cursors.DictCursor)
	with connection.cursor() as cursor:

		cursor.execute("TRUNCATE TABLE input_table")
	connection.close()

	return redirect(url_for('home'))



@app.route("/result" , methods=['POST'])
def map():
	if request.method == "POST":
		iname = request.form["Instance name"]
		vehCap = request.form["Vehicle capacity"]
		latlonlist, pathlatlon, demlist, cost = SA(float(vehCap))


	return render_template('result.html', latlonlist = latlonlist, pathlatlon= pathlatlon, demlist = demlist, cost = cost)
if __name__ == "__main__":
  app.run(debug=True, host= '10.21.58.202')