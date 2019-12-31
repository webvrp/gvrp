import math, random, copy, time
import numpy as np


def CostFunction(q, model, vehicle, oldsol):
	sol = ParseSolution(q, model, vehicle, oldsol)
	beta = 100000000
	dc = round(sol['t_dist']*(1+beta*sol['mean_var']),2)
	fc = round(sol['t_fuel']*(1+beta*sol['mean_var']),2)

	return (dc, fc, sol)
#------------------------------------------------------------------------------------------------------------------------
def CreateRandomSolution(model):
	nb_customers = model['nb_customers']
	nb_trucks = model['nb_trucks']

	q = np.random.permutation(nb_customers+nb_trucks-1)

	return q
#------------------------------------------------------------------------------------------------------------------------
def Swap(q):
	n = q.size
	i = [ q[i] for i in sorted(random.sample(range(n), 2)) ]
	i1 = i[0]
	i2 = i[1]

	qnew = copy.deepcopy(q)
	qnew[i1], qnew[i2] = q[i2], q[i1]

	return qnew
#------------------------------------------------------------------------------------------------------------------------

def Reversion(q):
	n = q.size
	i = [ q[i] for i in sorted(random.sample(range(n), 2)) ]
	i1 = i[0]
	i2 = i[1]

	qnew = copy.deepcopy(q)
	qnew[i1+1:i2+1] = q[i2:i1:-1]

	return qnew
#------------------------------------------------------------------------------------------------------------------------

def Insertion(q):
	n = q.size
	i = [ q[i] for i in sorted(random.sample(range(n), 2)) ]
	i1 = i[0]
	i2 = i[1]

	if i1 < i2:
		qnew = np.r_[q[0:i1], q[i1+1:i2], q[i1], q[i2:]]
	else:
		qnew = np.r_[q[0:i2], q[i1], q[i2:i1], q[i1+1:]]

	return qnew
#------------------------------------------------------------------------------------------------------------------------

def CreateNeighbour(q):
	m = random.randint(0,2)
	if m == 0:
		qnew = Swap(q)
	elif m == 1:
		qnew = Reversion(q)
	elif m == 2:
		qnew = Insertion(q)

	# qnew = Insertion(qnew)

	return qnew
#------------------------------------------------------------------------------------------------------------------------

def ParseSolution(q, model, vehicle, oldsol):
	nb_customers = model['nb_customers']
	nb_trucks = model['nb_trucks']
	dmatrix = np.array(model['dmatrix'])
	dmatrix0 = np.array(model['dmatrix0'])
	demands = model['demands']
	truck_capacity = model['truck_capacity']

	sol = {}

	DelPos=np.array(np.where(q > nb_customers-1))
	DelPos = DelPos.tolist()
	DelPos = sum(DelPos, [])

	From = [i+1 for i in DelPos]
	From.insert(0,0)
	To= DelPos
	To.append(nb_customers+nb_trucks)

	node_list = [0 for i in range(nb_trucks)]
	distance = [0 for i in range(nb_trucks)]
	fuel = [0 for i in range(nb_trucks)]
	route_quantity = [0 for i in range(nb_trucks)]

	for j in range(nb_trucks):
		q_temp = np.array(q[From[j]:To[j]])
		q_temp = q_temp.tolist()
		node_list[j] = q_temp
		######################################################
		''' use previous memory to make it faster
		'''
		###############################################@######
		if node_list[j]:	
			if node_list[j] in oldsol['node_list']:
				index = oldsol['node_list'].index(node_list[j])
				route_quantity[j] = oldsol['route_quantity'][index]
				distance[j] = oldsol['dist'][index]
				fuel[j] = oldsol['fuel'][index]
					
			else:
				for i in node_list[j]:
					route_quantity[j]=route_quantity[j]+demands[i]

				distance[j]=dmatrix0[node_list[j][0]]
				fuel[j] = fuel_consumed(model, dmatrix0[node_list[j][0]], route_quantity[j], vehicle)

				for k in range(len(node_list[j])-1):
					distance[j]=distance[j]+dmatrix[node_list[j][k]][node_list[j][k+1]]
					fuel[j] += fuel_consumed(model, dmatrix[node_list[j][k]][node_list[j][k+1]], (route_quantity[j]-demands[node_list[j][k]]), vehicle)

				distance[j]=distance[j]+dmatrix0[node_list[j][-1]]
				fuel[j] += fuel_consumed(model, dmatrix0[node_list[j][-1]], 0, vehicle)


	var=[max((i/truck_capacity)-1,0) for i in route_quantity]
	mean_var=np.mean(var)
	sol['node_list'] = node_list
	sol['route_quantity'] =route_quantity
	sol['dist'] = distance
	sol['fuel'] = fuel
	sol['t_fuel'] = sum(fuel)
	sol['max_dist'] = max(distance)
	sol['t_dist'] = sum(distance)
	sol['mean_var'] = mean_var
	
	return sol
#------------------------------------------------------------------------------------------------------------------------

def fuel_consumed(model, distance, demand, vehicle):
	vm, cd, ad, fa, rr, dte, ftar, k, V, rhode = vehicle['vm'], vehicle['cd'], vehicle['ad'], vehicle['fa'], vehicle['rr'], vehicle['dte'], vehicle['ftar'], vehicle['k'], vehicle['V'], vehicle['rhode']
	v = model['speed']
	a = model['acc']
	min_speed = min(v)
	max_speed = max(v)
	fc = 0
	dc_dist = 0
	tdist = sum(v)
	load = vm + float(demand)
	ga = 0 # grade angle
	for idx, val in enumerate(v):
		#fc += ftar(k*N*V+p/rhode)/44
		# N = 16+math.ceil((48-16)/(max_speed-min_speed)*(val-min_speed)), p = (load*math.fabs(a[idx])+load*g*math.sin(ga)+0.5*cd*ad*fa*(val**2)+load*g*rr*math.cos(ga)*val)*val/(1000*dte)
		fc += ftar*(k*(16+math.ceil((48-16)/(max_speed-min_speed)*(val-min_speed)))*V+((load*math.fabs(a[idx])+load*9.81*math.sin(ga)+0.5*cd*ad*fa*(val**2)+load*9.81*rr*math.cos(ga)*val)*val/(1000*dte))/rhode)/44
		dc_dist += v[idx]
		if dc_dist >= distance:
			break
	if distance/tdist >1:
		fc = fc*(math.floor(distance/tdist))
		dc_dist = tdist*math.floor(distance/tdist)
		for idx, val in enumerate(v):
			fc += ftar*(k*(16+math.ceil((48-16)/(max_speed-min_speed)*(val-min_speed)))*V+((load*math.fabs(a[idx])+load*9.81*math.sin(ga)+0.5*cd*ad*fa*(val**2)+load*9.81*rr*math.cos(ga)*val)*val/(1000*dte))/rhode)/44
			dc_dist += v[idx]
			if dc_dist >= distance:
				break
	return fc
#------------------------------------------------------------------------------------------------------------------------