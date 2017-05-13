from cStringIO import StringIO


def split_vals(csv_str, sep, skip_nulls=False):
	if skip_nulls:
		return [ s for s in [s.strip() for s in csv_str.split(sep)] if len(s) > 0]
	else:
		return [s.strip() for s in csv_str.split(sep)]

def str2dict(s):
	""" Converts a string "key1=val1, key2=val2, ..." to 
		a dictionary "{"key1" : "val1", "key2" : "val2", ... }"  """

	pair_list = split_vals(s, ",")
	pair_set = [ (pair[0], pair[1]) for pair in [x.split('=') for x in pair_list] ]
	result = {}
	result.update(pair_set)
	return result

def list2str(elems, sep, proc_fn=(lambda x: x)):
	return sep.join([proc_fn(s) for s in elems])

def findDictByAttr(dict_list, attr_name, val):
	result = None
	# Look for current queue ref in metadata
	for q in dict_list:
		if q[attr_name] == val:
			result = q
			break
	return result

def capitalizeStr(src, trim_underscores=True, camel=False):
	words = split_vals(src, "_")
	result = ""
	if camel:
		result += words[0][0].lower() + words[0][1:]
		words = words[1:]
	if len(words) > 0:
		concat_fn = trim_underscores and (lambda x,y: x+y) or (lambda x,y: "%s_%s" % (x, y))
		result += reduce(concat_fn, [word.capitalize() for word in words])

	return result