import random, pylab, time, math, sys, random, itertools
from functions_FCVRP import *
import numpy as np
import pandas as pd
import pymysql.cursors
#-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
def compute_distance_matrix(nodes_x, nodes_y):
    nb_nodes = len(nodes_x)-1
    x0 = nodes_x[0]
    x = nodes_x[:]
    y = nodes_y[:]
    y0 = nodes_y[0]
    x.remove(x[0])
    y.remove(y[0])
    d=np.zeros((nb_nodes,nb_nodes))
    d0=np.zeros(nb_nodes)
    for i in range(nb_nodes):
        for i2 in range(i+1, nb_nodes):
            d[i][i2]=math.sqrt(math.pow(x[i]-x[i2], 2) + math.pow(y[i]-y[i2], 2))
            d[i2][i]=d[i][i2]
        
        d0[i]=math.sqrt(math.pow(x[i]-x0, 2) + math.pow(y[i]-y0, 2))

    return (d, d0)
#-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
'''
Reading input data from database
'''

def SA(truck_capacity):
	connection = pymysql.connect(host='localhost',
								 user='root',
								 password='',
								 db='gvrp_db',
								 charset='utf8mb4',
								 cursorclass=pymysql.cursors.DictCursor)
	with connection.cursor() as cursor:
	# Create a new record
		cursor.execute("SELECT * FROM `input_table`")
		Cust_records = cursor.fetchall()
		connection.commit()
		connection.close()	
	nodes_x = []
	nodes_y = []
	demand = []
	nb_customers = 0
	for row in Cust_records:
		# print(row["NodeType"])
		if row["NodeType"] == "customer":
			demand.append(row["Demand"])
			nodes_x.append(row["Latitude"])
			nodes_y.append(row["Longitude"])
			nb_customers += 1
		else:
			nodes_x.insert(0,row["Latitude"])
			nodes_y.insert(0,row["Longitude"])


	nb_trucks = nb_customers
	# truck_capacity = 200
	(distance_matrix, distance_origin) = compute_distance_matrix(nodes_x, nodes_y)
	dc_data = pd.read_excel("/home/surendra/Dropbox/django/dc_data.xlsx")
	acc = list(dc_data['Acceleration']) # instantaneous acceleration in m/s^2
	speed = list(dc_data['Speed']) # speed in m/s


	#-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
	start = time.process_time()
	''' reading input data '''
	vehicle = {}
	model = {}
	vehicle['vm'], vehicle['cd'], vehicle['ad'], vehicle['fa'], vehicle['rr'], vehicle['dte'], vehicle['ftar'], vehicle['k'], vehicle['V'], vehicle['rhode'] = 600, 0.8, 1.2041, 2.25, 0.04, 0.4, 0.0667, 0.2, 2.77, 0.9
	(model['nb_trucks'] ,model['nb_customers'], model['truck_capacity'], model['dmatrix'], model['dmatrix0'], model['demands'], model['speed'], model['acc'], nodes_x, nodes_y) = nb_trucks, nb_customers, truck_capacity, distance_matrix, distance_origin, demand, speed, acc, nodes_x, nodes_y

	#-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
	'''
	SA Parameters
	'''
	#-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

	MaxIter = 30
	MaxIter_inner = 120
	initial_temp = 100
	alpha = 0.99


	#-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
	'''
	Initialization
	'''
	#-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
	# create initial solution
	x , dummy_data = {}, {}
	dummy_data['fuel'] = [0]*model['nb_trucks']
	dummy_data['node_list'] = [0]*model['nb_trucks']
	dummy_data['route_quantity'] = [0]*model['nb_trucks']
	x['position'] = CreateRandomSolution(model)
	(x['distcost'], x['fuelcost'], x['sol']) = CostFunction(x['position'], model, vehicle, dummy_data)
	# Update Best solution ever found
	BestSol = x

	# Array to hold Best cost Values
	BestDistCost = np.zeros((MaxIter, 1))
	BestFuelCost = np.zeros((MaxIter, 1))

	# set initial Temperature

	T = initial_temp

	#-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
	'''
	SA Main Loop
	'''
	#-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
	oldstop = start
	for it in range(MaxIter):
		for it2 in range(MaxIter_inner):
			xnew ={}
			# create neighbour
			xnew['position'] = CreateNeighbour(x['position'])
			(xnew['distcost'], xnew['fuelcost'], xnew['sol']) = CostFunction(xnew['position'], model, vehicle, BestSol['sol'])

			if xnew['fuelcost'] <= x['fuelcost']:
				# xnew is better, so it is accepted
				x = xnew

			else:
				delta = xnew['fuelcost']-x['fuelcost']
				p = math.exp(-delta/T)

				if random.random() <= p:
					x = xnew

		# Update best solution based on distance
		# if x['cost'] <= BestSol['cost']:
		# 	BestSol = x
		# Update best solution based on fuel
		if x['fuelcost'] <= BestSol['fuelcost']:
			BestSol = x

		# store Best cost
		BestDistCost[it] = BestSol['distcost']/1000
		BestFuelCost[it] = BestSol['fuelcost']/850

		sol = BestSol['sol']
		L = sol['node_list']
		stop = time.process_time()

		# print('Iteration:', it, 'Total distance (km) = ', BestDistCost[it], 'Total fuel consumed (Lit)= ', BestFuelCost[it], 'processing time:', stop-oldstop, 'Node List = ', L)
		oldstop = stop
		# Reduce Temperature
		T = alpha*T

	stop = time.process_time()
	# print('processing time:', stop-start)
	routelatlon = [[0, 0, nodes_x[0], nodes_y[0]]]
	pathlatlon = []
	demandout ={}
	vcount = 1
	for valid, val in enumerate(BestSol['sol']['route_quantity']):
		if val:
			demandout.update({vcount:val})
			latlon = [[nodes_x[0], nodes_y[0]]]
			for cu in BestSol['sol']['node_list'][valid]:
				routelatlon.append([vcount, cu+1, nodes_x[cu+1], nodes_y[cu+1]])
				latlon.append([nodes_x[cu+1], nodes_y[cu+1]])
			latlon.append([nodes_x[0], nodes_y[0]])
			pathlatlon.append(latlon)
			vcount += 1
	return (routelatlon, pathlatlon, demandout, BestSol['fuelcost'])
