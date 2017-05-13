import os, sys
import string
import re

from fsm_utils import split_vals
from fsm_utils import str2dict
from fsm_utils import list2str
from fsm_utils import findDictByAttr

def findSection(sec_name, line, metadata):
	return metadata["regexp"][sec_name].match(line)

def appendThread(metadata, thread_name, actor_name=""):
	if not metadata.has_key("threads"):
		metadata["threads"] = set()
	result_name = thread_name
	if result_name == "separated":
		result_name = actor_name + "_thread"
	metadata["threads"].add(result_name)

def parse(file_name, metadata) :
	try:
		infile = open(file_name, "rb", 0)
		try:
			infile.seek(0)
			init_regexp(metadata)
			proc_fn = parseSection("", metadata)
			for line in infile:
				# Skip empty lines and block comments ( # )
				if len(line.strip()) == 0 or findSection("block_comment", line, metadata):
					continue
				proc_fn = proc_fn(line, metadata)
				#print "new state: %s" % proc_fn
			# printParseResults(metadata)
		finally:
			infile.close()
	except IOError:
		print "Failed to read file \"" + file_name + "\""

def init_regexp(metadata):
	regexp_dict = {}
	
	regexp_dict["messages"] = re.compile(r"\s*messages\s*:")
	regexp_dict["queues"] = re.compile(r"\s*queues\s*:")
	regexp_dict["queue"] = re.compile(r"(\tqueue\s*\{)([^}]*)(\}\s*:)")
	regexp_dict["bound_fsm"] = re.compile(r"\t\tbound fsm\s*:")
	regexp_dict["bound_fsm_content"] = re.compile(r"(\s*\{?\s*)([^}]*)(\}?)")
	regexp_dict["fsm_list"] = re.compile(r"\s*fsms\s*:")
	regexp_dict["fsm"] = re.compile(r"(\tfsm\s*\{)([^}]*)(\})")
	regexp_dict["state"] = re.compile(r"(\t\tstate\s*\{)([^}]*)(\})")
	regexp_dict["trans"] = re.compile(r"(\t\t\tmsg\s*)(\S*)(\s*=>\s)(.*)")
	regexp_dict["trans_rhs"] = re.compile(r"([^;]*)(\;\s*)(.*)")
	regexp_dict["block_comment"] = re.compile(r"\s*\#+.*")

	metadata["regexp"] = regexp_dict


def parseSection(line, metadata):
	# I haven't decided yet what to do with the section "messages"
	# It can be useful in case of describing message attributes
	# if findSection("messages", line, metadata):
	# 	if string.find(line, "{") >= 0:
	# 		# Open brace is on the same line
	# 		return parseMessages_Continue
	# 	else:
	# 		return parseMessages

	if findSection("queues", line, metadata):
		return parseQueueList

	elif findSection("fsm_list", line, metadata):
		return parseFsmList

	else:
		return parseSection


# def parseMessages(line, metadata):
# 	result = None
# 	m = re.match(r"(\s*\{{1,1}\s*)([^}]*)(\s*\}?\s*)", line)
# 	if m != None:
# 		metadata["messages"] = split_vals(m.group(2), ",", True)
	
# 		if string.find(line, "}") >= 0:
# 			result = parseSection
# 		else:
# 			result = parseMessages_Continue
# 	else:
# 		raise Exception("Wrong format for the content section \"messages\".\nCheck it matches the next pattern: { msg1 [, msg2 ...] }")
		
# 	return result

# def parseMessages_Continue(line, metadata):
# 	result = None

# 	if findSection("queues", line, metadata) or findSection("fsm_list", line, metadata):
# 		raise Exception("Closing brace \"}\" for the section \"messages\" was not found")

# 	m = re.match(r"([^}]*)(\s*\}?\s*)", line)
# 	if m != None:
# 		add_list = split_vals(m.group(1), ",", True)
# 		if "messages" in metadata:
# 			metadata["messages"].extend(add_list)
# 		else:
# 			metadata["messages"] = add_list

# 		if string.find(line, "}") >= 0:
# 			result = parseSection
# 		else:
# 			result = parseMessages_Continue

# 	return result


def parseQueueList(line, metadata):
	m = findSection("queue", line, metadata)
	if m == None:
		raise Exception("Expected \"<TAB>queue {...} \", got: %s" % line)
	else:
		return parseQueue(line, metadata)	

def parseQueue(line, metadata):
	m = findSection("queue", line, metadata)
	if m == None:
		# parseSection must know what to do with that stuff
		return parseSection(line, metadata)
	else:
		queue_dict = str2dict(m.group(2))
		if "queues" in metadata:
			metadata["queues"].append(queue_dict)
		else:
			metadata["queues"] = [queue_dict]
		#appendThread(metadata, queue_dict["thread"], queue_dict["name"])
		metadata["curr_queue"] = queue_dict["name"]
		return parseBoundFsm

def parseBoundFsm(line, metadata):
	# Possible Patterns: 
	#   case #1 \t\tbound fsm: { fsm1, fsm2}
	#   case #2 \t\tbound fsm: { fsm1,
    #   case #3 \t\tbound fsm: {
    #   case #4 \t\tbound fsm:
	m = findSection("bound_fsm", line, metadata)
	if m == None:
		return parseQueue(line, metadata)
	else:
		chunk = line
		if line.find("{") >= 0:
			# Trim "\t\tbound fsm: "
			chunk = re.search(r"\t\tbound fsm:(.*)", line).group(1)
			return parseBoundFsm_Content(chunk, metadata)
		else:
			# Case #4, no need to trim, just go to a next line
			return parseBoundFsm_Content

def parseBoundFsm_Content(line, metadata):
	m = findSection("bound_fsm_content", line, metadata)
	if m == None:
		raise Exception("Expected \"<TAB><TAB>bound fsm: { [<ENTER>]fsm1, [<ENTER>]fsm2, ... }\", got: %s" % line)
	else:
		result = None
		if line.find("}") >= 0:
			result = parseQueue
		else:
			result = parseBoundFsm_Content
		# Look for current queue ref in metadata
		curr_queue = findDictByAttr(metadata["queues"], "name", metadata["curr_queue"])
		if curr_queue == None:
			raise Exception("Integrity violation: couldn't find queue for \"curr_queue\"=%s" % metadata["curr_queue"])

		fsm_list = split_vals(m.group(2), ",", True)
		if curr_queue.has_key("bound_fsm"):
			curr_queue["bound_fsm"].extend(fsm_list)
		else:	
			curr_queue["bound_fsm"] = fsm_list
	return result


def parseFsmList(line, metadata):
	m = findSection("fsm", line, metadata)
	if m == None:
		raise Exception("Expected \"<TAB>fsm {...}\", got %s" % line)
	else:
		return parseFsm(line, metadata)
	return parseSection

def parseFsm(line, metadata):
	m = findSection("fsm", line, metadata)
	if m == None:
		# parseSection must know what to do with that stuff
		return parseSection
	else:
		fsm_dict = str2dict(m.group(2))
		if not metadata.has_key("fsm_list"):
			metadata["fsm_list"] = []
		metadata["fsm_list"].append(fsm_dict)
		metadata["curr_fsm"] = fsm_dict["name"]
		#appendThread(metadata, fsm_dict["thread"], fsm_dict["name"])
		return parseState

def parseState(line, metadata):
	m = findSection("state", line, metadata)
	if m == None:
		if findSection("fsm", line, metadata):
			# go to a next FSM
			return parseFsm(line, metadata)
		else:
			# FSM definitions has been ended 
			return parseSection(line, metadata)
	else:
		curr_fsm = findDictByAttr(metadata["fsm_list"], "name", metadata["curr_fsm"])
		state = str2dict(m.group(2))
		if not curr_fsm.has_key("states"):
			curr_fsm["states"] = []
		curr_fsm["states"].append(state)
		# remember current state of current fsm
		metadata["curr_state"] = state["name"]
		return parseTransition

def parseTransition(line, metadata):
	m = findSection("trans", line, metadata)
	if m == None:
		# go to a next state
		return parseState(line, metadata)
	else:
		curr_fsm = findDictByAttr(metadata["fsm_list"], "name", metadata["curr_fsm"])
		msg = m.group(2)
		if not curr_fsm.has_key("acpt_msg"):
			curr_fsm["acpt_msg"] = set() 
		curr_fsm["acpt_msg"].add(msg)

		if not metadata.has_key("messages"):
			metadata["messages"] = set()
		metadata["messages"].add(msg)

		transition = {}
		transition["msg"] = msg
		# parse right-hand-side of a current transition statement
		rhs_m = findSection("trans_rhs", m.group(4), metadata)
		if rhs_m == None:
			# only destination declared, no additional attributes
			_parseTransDest(m.group(4), transition)
		else:
			# destination ; additional attributes (like "handler", "comment")
			_parseTransDest(rhs_m.group(1), transition)
			transition.update(str2dict(rhs_m.group(3)).items())

		curr_state = findDictByAttr(curr_fsm["states"], "name", metadata["curr_state"])
		if curr_state.has_key("trans"):
			curr_state["trans"].append(transition)
		else:
			curr_state["trans"] = [transition]
		return parseTransition

def _parseTransDest(chunk, transition):
	pair = split_vals(chunk, "=")
	if len(pair) == 1:
		transition["type"] = "straight"
		transition["dest"] = {"type" : "state", "name" : pair[0]}
	elif len(pair) == 2:
		transition["type"] = "conditional"
		transition["dest"] = {"type" : pair[0], "name" : pair[1]}
	else:
		raise Exception("Wrong state transition format on the right side of \"=>\":%s" % chunk)

def printParseResults(metadata):
	print "parse results:"
	print "messages: " 
	print "\t" + list2str(metadata["messages"], "\n\t") 
	#print "threads: %s" % metadata["threads"]
	print "queues = %s" % metadata["queues"]
	#print "fsm = %s" % metadata["fsm_list"]
	for fsm in metadata["fsm_list"]:
		print "\nfsm %s:" % fsm["name"]
		print "------------------------------------------------------------------------------------------"
		print "\t" + "\n\t".join( ["%s = %s" % (k, v) for k, v in fsm.items() if k != "states"])
		print "\tstates:"
		for state in fsm["states"]:
			print "\tstate %s" % state["name"]
			print "\t\t" + "\n\t\t".join(["%s = %s" % (k, v) for k, v in state.items() if k != "trans"]) 
			print "\t\ttransitions:"
			i = 1
			for trans in state["trans"]:
				print "\t\ttrans %d:" % i
				i += 1
				print "\t\t\t" + "\n\t\t\t".join(["%s = %s" % (k, v) for k, v in trans.items()]) 
		print "------------------------------------------------------------------------------------------"
	print "curr_queue is %s" % metadata["curr_queue"]
	print "curr_fsm is %s" % metadata["curr_fsm"]
	print "curr_state is %s" % metadata["curr_state"]


