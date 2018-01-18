from __future__ import division
from copy import copy
import math
import numpy
import random
from graph import *
import pprint
pp = pprint.PrettyPrinter(indent=4)
from utils import *
import time

def optimize(printer,graph):
	# get graph input
	variables = graph.variables
	path_weights = graph.path_weights
	capacity_vector = graph.capacity_vector
	switch_index = graph.switch_index
	switches_to_nullify = graph.switches_to_nullify

	start = time.time()

	# initialization #
	variables = variables*100
	number_of_switches = len(variables)
	number_of_paths = len(path_weights)

	all_traffic_weight = 0
	for path in range(0,number_of_paths):
		all_traffic_weight += path_weights[path]

	original_normalized_traspose = numpy.ones((number_of_switches, number_of_paths)).transpose()

	path_capacity = numpy.ones((number_of_switches, number_of_paths))*1000000

	original = copy(variables)
	# end of initialization #



	# start with a viable solutions
	original_normalized_traspose = normalize(variables, path_weights).transpose()
	variables = equalizer(variables,all_traffic_weight)
	variables = normalize(variables, path_weights)
	

	for f in range(0,100):
		path_capacity = generate_path_capacities(variables, path_capacity,capacity_vector)
		variables = prohibit(variables, path_capacity)
		variables = nullify_switches(variables,switch_index,switches_to_nullify)
		variables = normalize(variables, path_weights)

	max_iteration = 2000
	i = 0
	loss = 10
	obj_new = 11

	# start optimization
	while loss>0.00000001:
		obj_old = evaluate_obj_function(variables)
		
		i = i+1
		# stop if takes too long
		if i>max_iteration:
			variables = rectify(variables,original,capacity_vector)
			variables_normalized = normalize(variables, path_weights)
			break
		

		# calculate gradient
		grad = evaluate_grad(variables)
		variables_viable = copy(variables)
		k = 0
		s = 2
		while (True):
			variables = copy(variables_viable)
			s = s*2
			k = k + 1
			if s>100000000000:
				# redeem
				variables = copy(variables_viable)
				if printer:
					print "Couldn't backtrack! reached at " + str(obj_new) + " i = " + str(i) + " k " + str(k) 
				break

			must_backtrack = False
			
			# descend
			for row in range(0,number_of_switches):
				if must_backtrack:
					break

				for column in range(0,number_of_paths):
					# no need to descend
					if variables[row][column] ==0:
						continue
					variables[row][column] = variables_viable[row][column]- grad[row]/s
					if variables[row][column]<0:
						must_backtrack = True
						break
			if must_backtrack:
				continue

			# assert attained path weights are not zero
			path_weights_temp = evaluate_current_path_weights(variables)
			for path_weight in path_weights_temp:
				if path_weight == 0:
					must_backtrack = True
					break
			# avoid deviding by zero
			if must_backtrack:
				continue

			# handle constraints
			pre_normalized = copy(variables)
			variables = project_n(variables, path_weights,original_normalized_traspose)
			variables = rectify(variables,original,capacity_vector)
			variables = normalize(variables, path_weights)
			variables = equalizer(variables,all_traffic_weight)
			variables = normalize(variables, path_weights)
			for f in range(0,100):
				path_capacity = generate_path_capacities(variables, path_capacity,capacity_vector)
				variables = prohibit(variables, path_capacity)
				variables = nullify_switches(variables,switch_index, switches_to_nullify)
				variables = normalize(variables, path_weights)

			# calculate new obj function value in line search
			obj_sub_new = evaluate_obj_function(variables)

			# ensure positive loss in line search
			loss_sub = obj_old - obj_sub_new
			if (obj_sub_new is not None and obj_old-obj_sub_new<=-0.0000000000001):
				if printer:
					print "Going up! backtracking reached at new=" + str(obj_sub_new) + " old=" + str(obj_old) + " i = " + str(i)	+ " k=" + str(k) +  "	 backtracking"
				continue
			break

		# calculate attained new obj function value
		obj_new = evaluate_obj_function(variables)
		
		# evaluate loss
		loss = obj_old - obj_new

	if printer:
		print variables
	done = time.time()
	elapsed = done - start

	print "Time Elapsed for optimization: " + str(elapsed)
	

	return variables









def evaluate_obj_function(variables):
	""" evaluates value of objective function
	"""
	column_length = len(variables[0])
	ones = numpy.ones((column_length, 1))
	sum_mat = variables.dot(ones)
	sum_squared_mat = sum_mat.transpose().dot(sum_mat)
	return sum_squared_mat


def evaluate_grad(variables):
	""" evaluates gradient of objective function
	"""
	column_length = len(variables[0])
	ones = numpy.ones((column_length, 1))
	sum_mat = variables.dot(ones)
	for val in range(0,len(sum_mat)):
		sum_mat[val] = math.pow(sum_mat[val],1)
	return sum_mat

def evaluate_current_path_weights(variables):
	""" evaluates currently attained path weights from the variables
	"""
	path_weights_vector = []
	number_of_switches = len(variables)
	v_t = variables.transpose()
	ones = numpy.ones((number_of_switches,1))
	path_weights = v_t.dot(ones)
	return path_weights
def normalize(variables,path_weights):
	""" normalize values in variables
	"""
	number_of_switches = len(variables)
	number_of_paths = len(variables[0])

	varibales_normalized = copy(variables)

	current_path_weights = evaluate_current_path_weights(variables)
	for row in range(0,number_of_switches):
		for column in range(0,number_of_paths):
			varibales_normalized[row][column] = variables[row][column]*path_weights[column]/current_path_weights[column]

	return varibales_normalized

def equalizer(variables,all_traffic_weight):
	""" fix ratio of variables per switch according to switch aggregate
	"""
	number_of_switches = len(variables)
	number_of_paths = len(variables[0])

	for row in range(0,number_of_switches):
		switch_aggregate = 0
		for column in range(0,number_of_paths):
			switch_aggregate += variables[row][column]

		for column in range(0,number_of_paths):
			variables[row][column] = variables[row][column]*all_traffic_weight/switch_aggregate
	return variables


def project_n(variables,path_weights,original_normalized_traspose):
	""" project variables on the path constraints
	"""
	number_of_switches = len(variables)
	number_of_paths = len(variables[0])

	variables_transposed = numpy.transpose(variables)
	ones = numpy.ones((number_of_switches,1))
	varibales_normalized = copy(variables_transposed)
	current_path_weights = evaluate_current_path_weights(variables)
	for row in range(0,number_of_paths):
		minus = variables_transposed[row] - original_normalized_traspose[row]
		
		varibales_normalized[row] = variables_transposed[row] - minus.dot(ones/(math.sqrt(number_of_switches)))*(1/(math.sqrt(number_of_switches)))

	varibales_normalized = numpy.transpose(varibales_normalized)

	return varibales_normalized
def rectify(variables, original,capacity_vector):
	""" assert variables[i][j] is zero for path:j that does not pass through switch:i
	"""
	number_of_switches = len(variables)
	number_of_paths = len(variables[0])

	for row in range(0,number_of_switches):
		for column in range(0,number_of_paths):
			if original[row][column] == 0:
				variables[row][column] = 0

	return variables


def generate_path_capacities(variables, path_capacity,capacity_vector):
	""" generates capacity limit on each variable according to its ratio per switch
	"""
	number_of_switches = len(variables)
	number_of_paths = len(variables[0])

	path_capacity = copy(variables)
	for row in range(0,number_of_switches):
		switch_aggregate = 0
		for column in range(0,number_of_paths):
			switch_aggregate += path_capacity[row][column]

		for column in range(0,number_of_paths):
			path_capacity[row][column] = path_capacity[row][column]*capacity_vector[row]/switch_aggregate
	return path_capacity

def prohibit(variables, path_capacity):
	""" assert variables don't exceed their capacities
	"""
	number_of_switches = len(variables)
	number_of_paths = len(variables[0])

	for row in range(0,number_of_switches):
		for column in range(0,number_of_paths):
			if variables[row][column] > path_capacity[row][column]:
				variables[row][column] = path_capacity[row][column]

	return variables



def nullify_switches(variables,switch_index, switches_to_nullify):
	""" set variables corresponding to a switch to zero if a switch is to be excluded from optimization
		TODO: augment function to able to nullify switches per path, instead of total nullification
	"""
	#{'s9': 2, 's8': 11, 's3': 7, 's2': 4, 's11': 3, 's10': 9, 's7': 8, 's6': 5, 's5': 1, 's4': 10, 's12': 6, 's1': 0}
	switches_to_nullify = switches_to_nullify
	if switches_to_nullify is None:
		return variables
	number_of_switches = len(variables)
	number_of_paths = len(variables[0])
	for switch_name in switches_to_nullify:
		if switch_index.get(switch_name) is not None:
			index = switch_index.get(switch_name)
			for row in range(0,number_of_switches):
				if row == index:
					for column in range(0,number_of_paths):
						variables[row][column] = 0

	return variables