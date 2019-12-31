import math, sys, random, itertools
import numpy as np
import pandas as pd
#-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
""" Reading_input_file  """ 
#-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
def read_elem(filename):
    with open(filename) as f:
        return [str(elem) for elem in f.read().split()]

#-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
def read_input_cvrp(filename):
    file_it = iter(read_elem(filename))
    nb_trucks = get_nb_trucks(filename)

    nb_nodes = 0
    while(1):
        token = file_it.__next__()
        if token == "DIMENSION":
            file_it.__next__() # Removes the ":"
            nb_nodes = int(file_it.__next__())
            nb_customers = nb_nodes - 1
        elif token == "CAPACITY":
            file_it.__next__() # Removes the ":"
            truck_capacity = int(file_it.__next__())
        elif token == "EDGE_WEIGHT_TYPE":
            file_it.__next__() # Removes the ":"
            token = file_it.__next__()
            if token != "EUC_2D":
                print ("Edge Weight Type " + token + " is not supported (only EUD_2D)")
                sys.exit(1)
        elif token == "NODE_COORD_SECTION":
            break;


    nodes_x = [None]*nb_nodes
    nodes_y = [None]*nb_nodes
    for n in range(nb_nodes):
        node_id = int(file_it.__next__())
        if node_id != n+1:
            print(node_id, n+1)
            print ("Unexpected index in input file nodes section")
            sys.exit(1)
        nodes_x[n] = float(file_it.__next__())
        nodes_y[n] = float(file_it.__next__())

    # Compute distance matrix
    (distance_matrix, distance_origin) = compute_distance_matrix(nodes_x, nodes_y)
    dc_data = pd.read_excel("D:\OneDrive\Research_work\python_workspace\VRP\SA\CVRP\FCVRP\dc_data.xlsx",sheetname=0, header=0, skiprows=None, skip_footer=0)
    acc = list(dc_data['Acceleration']) # instantaneous acceleration in m/s^2
    speed = list(dc_data['Speed']) # speed in m/s

    token = file_it.__next__()
    if token != "DEMAND_SECTION":
        print ("Expected token DEMAND_SECTION")
        sys.exit(1)

    demands = [None]*nb_nodes
    for n in range(nb_nodes):
        node_id = int(file_it.__next__())
        if node_id != n+1:
            print ("Unexpected index")
            sys.exit(1)
        demands[n] = int(file_it.__next__())

    token = file_it.__next__()
    if token != "DEPOT_SECTION":
        print ("Expected token DEPOT_SECTION")
        sys.exit(1)

    warehouse_id = int(file_it.__next__())
    if warehouse_id != 1:
        print ("Warehouse id is supposed to be 1")
        sys.exit(1)

    end_of_depot_section = int(file_it.__next__())
    if end_of_depot_section != -1:
        print ("Expecting only one warehouse, more than one found")
        sys.exit(1)

    if demands[0] != 0:
        print ("Warehouse demand is supposed to be 0")
        sys.exit(1)

    demands.pop(0)
    # emission_factors = emission_factor(vtype)
    title = get_title(filename)
    return (nb_trucks, nb_customers, truck_capacity, distance_matrix, distance_origin, demands, speed, acc, nodes_x, nodes_y, title)#, emission_factors)
#-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
def get_title(filename):
    begin = filename.rfind("-n")
    end = filename.find(".", begin)
    title = filename[begin-1:end]
    return title

def get_nb_trucks(filename):
    begin = filename.rfind("-k")
    if begin != -1:
        begin += 2
        end = filename.find(".", begin)
        return int(filename[begin:end])
    print ("Error: nb_trucks could not be read from the file name. Enter it from the command line")
    sys.exit(1)

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

def emission_factor(vtype):
    ef ={}
    if vtype == 3:
        ef['eco'] = 5.69
        ef['enox'] = 7.29
        ef['ethc'] = 0.2
        ef['epm'] = 0.6
    elif vtype == 2:
        ef['eco'] = 2.1
        ef['enox'] = 5.29
        ef['ethc'] = 0.24
        ef['epm'] = 0.3
    else:
        ef['eco'] = 1.73
        ef['enox'] = 5.53
        ef['ethc'] = 0.32
        ef['epm'] = 0.14
    return ef
#-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------