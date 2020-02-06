#!/usr/bin/env python3

import pandas as pd
from types import SimpleNamespace
import numpy as np
import math
import networkx as nx
import matplotlib.pyplot as plt

import os
import csv
import random

import argparse

from sklearn import preprocessing

def distance(p0, p1):
    return math.hypot(p1[0] - p0[0], p1[1] - p0[1])

def generate_problem_file(filepath, services, locations, points, service_range_factor = 1.0, do_draw = False):
    """
    Generates an MSCFLP-problem from the given parameters and writes it to a file at location <filepath>.
    This is done by randomly placing service locations in a square area with side L.
    The range of services (max distance to service a demand point) is inversely proportional to the cube root
    of the number of locations. It can be scaled using the service_range_factor parameter.

    Demand points are sampled randomly such that they can always be serviced by at least one service location.

    The points parameter determines the total number of demand points.
    Each demand point requires only one service, so there must be at least `services` demand points
    since every service should have at least one demand point that requests it.
    """
    if services > points:
        print("Error: more services than demand points requested. Exiting.")
        exit()
        
    # Create an initial graph. Give some slack with demand points so we can remove enough later.
    # Points are generated inside the unit square using the Poisson disk method.
    total_nodes = locations + points
    service_range = service_range_factor / (locations ** (1.0 / 3.0))
    minimum_distance = 0.1 * service_range
    coords = {}
    node_idx = 0
    while node_idx < total_nodes:
       new_coord = (np.random.random(), np.random.random())
       too_close = False
       for c in coords.values():
         if distance(c, new_coord) < minimum_distance:
           too_close = True
           break;
       if too_close:
          continue
       coords[node_idx] = new_coord
       node_idx += 1

    G = nx.random_geometric_graph(total_nodes, service_range, pos=coords)

    for loc_idx in range(locations):
        for loc_jdx in range(locations):
            if G.has_edge(loc_idx, loc_jdx):
                G.remove_edge(loc_idx, loc_jdx)
    # Remove edges between every two demand points
    for dem_idx in range(locations, total_nodes):
        for dem_jdx in range(locations, total_nodes):
            if G.has_edge(dem_idx, dem_jdx):
                G.remove_edge(dem_idx, dem_jdx)
    # Move isolated demand points so they can be serviced by at least one service location
    for dem_idx in range(locations, total_nodes):
        node = G.node[dem_idx]
        while len(G[dem_idx]) == 0:
            # change the node position
            too_close = True
            new_coord = None
            while too_close:
               new_coord = (np.random.random(), np.random.random())
               too_close = False
               for c in coords.values():
                 if distance(c, new_coord) < minimum_distance:
                   too_close = True
                   break;
            coords[dem_idx] = new_coord
            node['pos'] = new_coord
            # update neighbors
            for loc_idx in range(locations):
                dstc = distance(G.node[loc_idx]['pos'], new_coord)
                if dstc <= service_range:
                    G.add_edge(loc_idx, dem_idx)
    for loc_idx in range(locations):
        node = G.node[loc_idx]
        while len(G[loc_idx]) == 0:
            # change the node position
            too_close = True
            new_coord = None
            while too_close:
               new_coord = (np.random.random(), np.random.random())
               too_close = False
               for c in coords.values():
                 if distance(c, new_coord) < minimum_distance:
                   too_close = True
                   break;
            coords[loc_idx] = new_coord
            node['pos'] = new_coord
            # update neighbors
            for dem_idx in range(locations, total_nodes):
                dstc = distance(G.node[dem_idx]['pos'], new_coord)
                if dstc <= service_range:
                    G.add_edge(loc_idx, dem_idx)
    degree_centralities = nx.degree_centrality(G)
    max_centrality = 0.0
    for loc_idx in range(locations):
        if degree_centralities[loc_idx] > max_centrality:
            max_centrality = degree_centralities[loc_idx]
    # Centrality = fraction of all nodes (including service points) to which a service point is connected
    print("Highest centrality: " + str(max_centrality))
    if max_centrality > 0.5:
        print("Warning: single location can service more than half of all nodes (" + str(math.floor(100 * max_centrality)) + " percent).")
    if max_centrality < 2.0 / locations:
        print("Warning: location with most demand points can service only " + str(math.floor(100 * max_centrality)) + " percent of demand points.")

    if do_draw == True:
        plt.figure(figsize=(6, 6))
        nx.draw_networkx_nodes(G, coords, nodelist = [idx for idx in range(locations)], node_size = 30, node_color = 'r')
        nx.draw_networkx_nodes(G, coords, nodelist = [idx for idx in range(locations, total_nodes)], node_size = 15, node_color = 'b')
        nx.draw_networkx_edges(G, coords)
        plt.show()

    """
    Create service, location and point lists to convert into excel files
    At this point all the location - demand point rows are known, we just have
    to assign each demand point a random service, ensuring that each service is
    requested at least once. We thus iterate over the demand points and sort at the end.
    """
    services_list = []
    locations_list = []
    points_list = []
    service_requested = 0
    all_services_requested = False
    # first `locations` indices are service locations
    # iterate over demand point indices only
    for dem_idx in range(locations, total_nodes):
        locs = G[dem_idx].keys() # locations connected to current demand point
        for loc in locs:
            # append triplet
            services_list.append(service_requested)
            locations_list.append(loc)
            points_list.append(dem_idx - locations)
        if not all_services_requested:
            if service_requested == services - 1:
                all_services_requested = True
            else:
                service_requested += 1
        else:
            service_requested = np.random.randint(services)

    data = pd.DataFrame()
    data['service'] = services_list
    data['location'] = locations_list
    data['point'] = points_list
    sorted_data = data.sort_values(by=['service', 'location', 'point']).reset_index(drop=True)

    # opening cost range
    ocr = [4000, 5000]
    opening_costs_list = (ocr[0] + (ocr[1] - ocr[0]) * np.random.random_sample(locations)).astype(int)
    # equipping cost range
    ecr = [200, 500]
    equip_costs_list = (ecr[0] + (ecr[1] - ecr[0]) * np.random.random_sample(services)).astype(int)
    data_equip = pd.DataFrame()
    data_equip['equip_costs'] = equip_costs_list
    data_open = pd.DataFrame()
    data_open['opening_costs'] = opening_costs_list
    final_data = pd.concat([sorted_data, data_open, data_equip], axis = 1)
    
    print(filepath)
    final_data.to_excel(filepath, sheet_name='problem', index=False)

if __name__ == '__main__':
    parser = argparse.ArgumentParser( \
        description='This script generates a service allocation problem and its solution.')
    parser.add_argument('services', type=int)
    parser.add_argument('locations', type=int)
    parser.add_argument('points', type=int)
    parser.add_argument('service_range_factor', type=float, default=1.0, nargs='?')
    parser.add_argument('--draw', default=False)
    parser.add_argument('--dir', default='.')
    parser.add_argument('--filename', default='')
    args = parser.parse_args()

    filename = args.filename
    if len(filename) == 0:
        filename = "testproblem_geometric_F" + str(args.services) + "L" + str(args.locations) + "U" + str(args.points) + ".xlsx"

    filepath = args.dir + '/' + filename
    if os.path.isfile(filepath):
        print("File already exists!")
    generate_problem_file(filepath, args.services, args.locations, args.points, args.service_range_factor, args.draw)

