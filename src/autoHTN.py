import pyhop
import json

def check_enough (state, ID, item, num):
	if getattr(state,item)[ID] >= num: return []
	return False

def produce_enough (state, ID, item, num):
	return [('produce', ID, item), ('have_enough', ID, item, num)]

pyhop.declare_methods ('have_enough', check_enough, produce_enough)

def produce (state, ID, item):
	return [('produce_{}'.format(item), ID)]

pyhop.declare_methods ('produce', produce)

def make_method (name, rule):
	def method (state, ID):
		results = []

		for task, value in rule.items():
			if task != 'Produces' and isinstance(value, dict):
				results.extend(map(lambda item: ('have_enough', ID, item[0], item[1]), reversed(value.items())))
		results.append(('op_'+name, ID))
		return results
	method.__name__ = name
	return method

def declare_methods (data):
	recipes = data['Recipes']

	list_info = [('produce_' + list(recipe['Produces'].keys())[0],
        make_method(recipe_task.replace(' ', '_'), recipe),
        recipe['Time'])
        for recipe_task, recipe in recipes.items()]

	list_info.sort(key=lambda item: item[2])

	for product, method, _ in list_info:
		pyhop.declare_methods(product, method)

def make_operator(recipe_data):
    def operator(state, ID):
        for task, items in recipe_data.items():
            if task == 'Produces':
                for item, quantity in items.items():
                    setattr(state, item, {ID: getattr(state, item)[ID] + quantity})
            elif task == 'Consumes':
                for item, quantity in items.items():
                    if getattr(state, item)[ID] >= quantity:
                        setattr(state, item, {ID: getattr(state, item)[ID] - quantity})
                    else:
                        return False
            elif task == 'Time':
                if state.time[ID] >= items:
                    state.time[ID] -= items
                else:
                    return False
        return state

    return operator

def declare_operators(data):
    operators_info = []

    for recipe_name, recipe_data in sorted(data['Recipes'].items(), key=lambda item: item[1]["Time"], reverse=True):
        recipe_name = recipe_name.replace(' ', '_')
        operator_function = make_operator(recipe_data)
        operator_time = recipe_data['Time']
        operator_function.__name__ = 'op_' + recipe_name
        operators_info.append((operator_function, operator_time))

    operators_info.sort(key=lambda info: info[1])

    for operator_function, _ in operators_info:
        pyhop.declare_operators(operator_function)

def add_heuristic (data, ID):
	# prune search branch if heuristic() returns True
	# do not change parameters to heuristic(), but can add more heuristic functions with the same parameters:
	# e.g. def heuristic2(...); pyhop.add_check(heuristic2)
	def heuristic (state, curr_task, tasks, plan, depth, calling_stack):
		# your code here
		return False # if True, prune this branch

	pyhop.add_check(heuristic)


def set_up_state (data, ID, time=0):
	state = pyhop.State('state')
	state.time = {ID: time}

	for item in data['Items']:
		setattr(state, item, {ID: 0})

	for item in data['Tools']:
		setattr(state, item, {ID: 0})

	for item, num in data['Initial'].items():
		setattr(state, item, {ID: num})

	return state

def set_up_goals (data, ID):
	goals = []
	for item, num in data['Goal'].items():
		goals.append(('have_enough', ID, item, num))

	return goals

if __name__ == '__main__':
	rules_filename = 'crafting.json'

	with open(rules_filename) as f:
		data = json.load(f)

	state = set_up_state(data, 'agent', time=239) # allot time here
	goals = set_up_goals(data, 'agent')

	declare_operators(data)
	declare_methods(data)
	add_heuristic(data, 'agent')

	# pyhop.print_operators()
	# pyhop.print_methods()

	# Hint: verbose output can take a long time even if the solution is correct;
	# try verbose=1 if it is taking too long
	pyhop.pyhop(state, goals, verbose=3)
	# pyhop.pyhop(state, [('have_enough', 'agent', 'cart', 1),('have_enough', 'agent', 'rail', 20)], verbose=3)
	# pyhop.pyhop(state, [('have_enough', 'agent', 'stone_pickaxe', 1)], verbose=3)