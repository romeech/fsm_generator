import os, os.path
import sys
import string
import re
import shutil

from cStringIO import StringIO
from fsm_utils import capitalize_str
from fsm_utils import list2str
# metadata
#   queues : []
#       queue-i : {}
#           name : str
#           thread : str
#           with_timers : bool
#           bound_fsm : []
#       ...

#   + fsm_list : []
#       + fsm-i : {}
#           + name : str
#           + type : str (multi, single)
#           + state_changed_handler : bool
#           thread : str
#           + acpt_msg : set of str
#           + states: []
#               + state: {}
#                   + name: str
#                   [ begin : str ]
#                   [ end : str ]
#                   + trans : []
#                       + trans-i : {}
#                           + msg : str
#                           type : str ("straight", "conditional")
#                           + dest : {}
#                               + type : str ("state", "changer", "common_changer")
#                               + name : str
#                           + [ comment : str ]
#                           + [ handler : str ]
#                           + [ common_handler : str ]
#                       ...
#               ...
#       ...

#   + messages : set of str
#   threads : set of str


def build_world(metadata, output_dir):
    # todo: add key words validation
    build_messages(metadata, output_dir)
    build_queues(metadata, output_dir)
    build_fsms(metadata, output_dir)

    
def build_messages(metadata, output_dir):
    work_dir = os.path.join(output_dir, "messages") 
    ensure_dir(work_dir)
    file_list = os.listdir(work_dir)

    # put necessary files to work dir
    shutil.copy(os.path.join("src", "templates","message_data.h"),  os.path.join(work_dir, "message_data.h"))

    # creating custom messages
    include_list = []
    msg_factory_cases = []
    msg_list = [m for m in metadata["messages"] if m != "default"]
    for msg in msg_list:
        header_name = os.path.join(work_dir, msg + "_impl.h")
        if not os.path.exists(header_name):
            create_custom_msg_data_header(msg, header_name, metadata)
        # accumulate in a list for including in "messages.h"
        include_list.append(make_include_str(msg + "_impl"))
        # accumulate in a list for MessageFactory building
        msg_factory_cases.append(make_msg_factory_case(msg))

            
    # make messages.h/cpp
    make_messages_h(msg_list, include_list, os.path.join(work_dir, "messages.h"))
    shutil.copy(os.path.join("src", "templates","messages.cpp"), os.path.join(work_dir, "messages.cpp"))

    # make message_factory.h/cpp
    shutil.copy(os.path.join("src", "templates","message_factory.h"), os.path.join(work_dir, "message_factory.h"))
    process_message_factory(msg_factory_cases, os.path.join(work_dir, "message_factory.cpp"))

    # print work dir content
    # print "\n%s contains now:" % work_dir
    # print "\n".join(["- " + f for f in os.listdir(work_dir)])

def make_msg_factory_case(msg):
    return "case %s:\n\t\t\t\tmd = new %s();\n\t\t\t\tbreak;\n" % \
        (msg.upper(), capitalize_str(msg) + "_Impl")

def create_custom_msg_data_header(msg, path, metadata):
    substitutes = [("$INC_GUARD", msg.upper() + "_H"), 
                   ("$CLASS_NAME", capitalize_str(msg) + "_Impl")]
    finalize_line = (lambda l: l.strip())
    process_template(path, "custom_message_data.h", substitutes, finalize_line)

def make_messages_h(msg_list, include_list, path):
    substitutes = [("$INCLUDE_LIST", list2str(include_list, "\n")), 
                   ("$MSG_LIST", list2str(msg_list, ",\n    ", (lambda x: x.upper())))]
    finalize_line = (lambda l: l.rstrip())
    process_template(path, "messages.h", substitutes, finalize_line)

def process_message_factory(msg_factory_cases, path):
    substitutes = [("$MSG_TYPE_CASES", list2str(msg_factory_cases, "\n\t\t\t"))]
    finalize_line = (lambda l: l.rstrip())
    process_template(path, "message_factory.cpp", substitutes, finalize_line)


def build_queues(metadata, output_dir):
    # TODO 3: implement
    pass

def build_fsms(metadata, output_dir):
    work_dir = os.path.join(output_dir, "fsm")
    ensure_dir(work_dir)
    file_list = os.listdir(work_dir)

    for fsm in metadata["fsm_list"]:
        fsm_name_lc = fsm["name"].lower()
        fsm_name_uc = fsm["name"].upper()
        fsm_class_name = get_fsm_class_name(fsm)
        fsm_h = fsm_name_lc + "_auto.h"
        fsm_impl_h = fsm_name_lc + "_impl.h"
        fsm_impl_h_path = os.path.join(work_dir, fsm_impl_h)
        trim_right_fn = (lambda l: l.rstrip())
        # make custom fsm.h
        (state_decls, state_changers, state_handlers) = get_fsm_declarations(fsm)
        on_state_changed_handler = "\tvoid onStateChanged(fptr old_state, fptr new_state);" \
            if fsm["state_changed_handler"] == "true" else ""

        substitutes = [ ("$INC_GUARD", fsm_name_uc), 
                        ("$FSM_IMPL_INC", "#include \"%s\"" % fsm_impl_h),
                        ("$FSM_CLASS_NAME", fsm_class_name),
                        ("$FSM_PROTOTYPE", get_fsm_prototype(fsm)),
                        ("$ON_STATE_CHANGED_HANDLER", on_state_changed_handler),
                        ("$STATE_DECLS", state_decls),
                        ("$STATE_CHANGERS_DECLS", state_changers),
                        ("$STATE_HANDLERS_DECLS", state_handlers) ]
        process_template(os.path.join(work_dir, fsm_h), "custom_fsm.h", substitutes, trim_right_fn)
        
        inc_fsm_h = "#include \"%s\"" % fsm_h
        # make custom fsm.cpp
        (state_aliases, state_definitions, states_desc_cont, acpt_msg_list) = get_fsm_definitions(fsm)
        substitutes = [ ("$FSM_HDR_INC", inc_fsm_h), 
                        ("$STATE_ALIASES", state_aliases),
                        ("$FSM_CLASS_NAME", fsm_class_name),
                        ("$STATE_DEFINITIONS", state_definitions),
                        ("$STATE_DESC_MAP_CONTENT", states_desc_cont),
                        ("$ACPTD_MSG_LIST", acpt_msg_list) ]
        process_template(os.path.join(work_dir, fsm_name_lc + "_auto.cpp"), "custom_fsm.cpp", substitutes, trim_right_fn)
        
        # check custom fsm_handlers.cpp
        (changers, handlers) = get_fsm_handlers(fsm)
        fsm_handlers_cpp = os.path.join(work_dir, fsm_name_lc + "_handlers.cpp")
        if os.path.exists(fsm_handlers_cpp):
            update_fsm_handlers_cpp(fsm, fsm_handlers_cpp, changers, handlers)
        else:
            changers_definitions = "\n".join(changers.values())
            handlers_definitions = "\n".join(handlers.values())
            substitutes = [ ("$FSM_HDR_INC", inc_fsm_h),
                            ("$ON_STATE_CHANGED", get_on_state_changed_def(fsm)),
                            ("$STATE_CHANGERS_DEFINITIONS", changers_definitions),
                            ("$STATE_HANDLERS_DEFINITIONS", handlers_definitions) ]
            process_template(fsm_handlers_cpp, "custom_fsm_handlers.cpp", substitutes, trim_right_fn)

        # check custom fsm_impl.h
        if not os.path.exists(fsm_impl_h_path):
            substitutes = [ ("$INC_GUARD", fsm_name_uc + "_IMPL"), ("$FSM_CLASS_NAME", fsm_class_name) ]
            process_template(fsm_impl_h_path, "custom_fsm_impl.h", substitutes, trim_right_fn)

        # check custom fsm_impl.cpp
        fsm_impl_cpp_path = os.path.join(work_dir, fsm_name_lc + "_impl.cpp")
        if not os.path.exists(fsm_impl_cpp_path):
            substitutes = [ ("$INC_FSM_IMPL_H", "#include \"%s\"" % fsm_impl_h),
                            ("$FSM_CLASS_NAME", fsm_class_name) ]
            process_template(fsm_impl_cpp_path, "custom_fsm_impl.cpp", substitutes, trim_right_fn)


def get_fsm_prototype(fsm):
    fsm_type = fsm["type"].lower()
    if fsm_type == "multi":
        return "MultiStateFsa"
    elif fsm_type == "single":
        return "FSA"
    else:
        raise Exception("Unknown FSM type = %s" % fsm["type"] )

def get_fsm_declarations(fsm):
    def concat_method_list(out_buffer, method_dict, signature):
        for (state_name, method_set) in method_dict.items():
            out_buffer.write("\t// %s:\n" % state_name.upper())
            preffix = capitalize_str(state_name, camel=1) + "_" if state_name != "common" else ""
            for m in method_set:
                out_buffer.write(signature % str(preffix + m))

    state_decls = StringIO()
    state_change_signature = "\tstd::pair<fptr, bool> %s(const Message& msg);\n"

    state_changer_dict = {}
    state_handler_dict = {}
    for state in fsm["states"]:
        state_decls.write(state_change_signature % capitalize_str(state["name"], camel=1));
        state_changer_dict.update( get_state_changers(state) )
        state_handler_dict.update( get_state_handlers(state) )
    
    changers = StringIO()
    concat_method_list(changers, state_changer_dict, state_change_signature)

    handlers = StringIO()
    concat_method_list(handlers, state_handler_dict, "\tvoid %s(const Message& msg);\n")

    return ( state_decls.getvalue(), changers.getvalue(), handlers.getvalue() )

def get_fsm_state_decls(state):
    # STATES DECL ELEM: std::pair<fptr, bool> stateName(const Message& msg);
    output = StringIO()
    for state in fsm["states"]:
        output.write("\tstd::pair<fptr, bool> %s(const Message& msg);\n" % capitalize_str(state["name"], camel=1))
    return output.getvalue()

def get_state_changers(state):
    out_dict = {}
    for trn in state["trans"]:
        curr_dest = trn["dest"]
        curr_dest_type = curr_dest["type"].lower()
        if curr_dest_type != "state":
            if curr_dest_type == "changer":
                key = state["name"]
                value = curr_dest["name"]
            elif curr_dest_type == "common_changer":
                key = "common"
                value = curr_dest["name"]
            else:
                raise Exception("Unknown destination type \"%s\" of state \"%s\" transition by msg \"%s\"" % \
                                (curr_dest["type"], state["name"], trn["msg"]) )
            if not out_dict.has_key(key):
                out_dict[key] = set()
            out_dict[key].add(value)

    return out_dict

def get_state_handlers(state):
    out_dict = {}
    for trn in state["trans"]:
        if trn.has_key("handler"):
            key = state["name"]
            value = trn["handler"]
        elif trn.has_key("common_handler"):
            key = "common"
            value = trn["common_handler"]
        else:
            continue
        if not out_dict.has_key(key):
            out_dict[key] = set()
        out_dict[key].add(value)

    return out_dict


def get_fsm_definitions(fsm):
    alias_list = []
    state_definitions = []
    state_desc_map_cont = []
    acpt_msg_set = set()
    for state in fsm["states"]:
        # STATE_ALIASES 
        alias_list.append("const state_method %s = (state_method)&%s::%s;" % \
                            (state["name"].upper(), get_fsm_class_name(fsm), get_state_fn_name(state)) )
        # STATE_DEFINITIONS
        state_definitions.append( make_state_definition(fsm, state))
        # STATE_DESC_MAP_CONTENT
        state_desc_map_cont.append( make_state_desc(state) )
        # ACPTD_MSG_LIST
        acpt_msg_set.update( extract_state_messages(state) )
    return ("\n\t".join(alias_list), "\n".join(state_definitions), "\n\t".join(state_desc_map_cont), ",\n\t\t".join(acpt_msg_set))

def make_state_definition(fsm, state):
    output = StringIO()
    output.write("std::pair<fptr, bool> %s::%s(const Message& msg) {\n" % (get_fsm_class_name(fsm), get_state_fn_name(state)))
    output.write("\tswitch(msg.type) {\n")
    for trn in state["trans"]:
        if trn["msg"] == "default":
            output.write("\t\tdefault:\n")
        else:
            output.write("\t\tcase %s:\n" % trn["msg"].upper())

        if trn.has_key("comment"):
            output.write("\t\t\t// %s\n" % trn["comment"])

        if trn.has_key("handler"):
            output.write("\t\t\t%s_%s(msg);\n" % (get_state_fn_name(state), trn["handler"]))

        if trn.has_key("common_handler"):
            output.write("\t\t\t%s(msg);\n" % trn["common_handler"])

        dest = trn["dest"]
        dest_type = dest["type"].lower()
        if dest_type == "state":
            if dest["name"] == "remains":
                output.write("\t\t\treturn remains(true);\n")
            else:
                output.write("\t\t\treturn became(%s);\n" % dest["name"].upper())
        elif dest_type == "changer":
            output.write("\t\t\treturn %s_%s(msg);\n" % (get_state_fn_name(state), dest["name"]))
        elif dest_type == "common_changer":
            output.write("\t\t\treturn %s(msg);\n" % dest["name"])
        else:
            raise Exception("Unknown destination type \"%s\"" % dest_type)
        
        output.write("\n") # separator

    output.write("\t}\n")  # closing switch
    output.write("}\n")  # closing method
    return output.getvalue()

def make_state_desc(state):
    # state_desc_map.emplace(STATE_NAME, "state_name");
    state_name = state["name"]
    return "state_desc_map.emplace(%s, \"%s\")" % (state_name.upper(), state_name.lower()) 


def get_fsm_handlers(fsm):
    changers = {} 
    common_changers = {}
    handlers = {}
    fsm_class_name = get_fsm_class_name(fsm)
    for state in fsm["states"]:
        state_fn_name = get_state_fn_name(state)
        for trn in state["trans"]:
            if trn.has_key("handler"):
                key = "%s::%s_%s" % (fsm_class_name, state_fn_name, trn["handler"])
                value = get_handler_definition(fsm_class_name, trn["handler"], state_fn_name)
                handlers[key] = value
            if trn.has_key("common_handler"):
                key = "%s::%s" % (fsm_class_name, trn["common_handler"])
                value = get_handler_definition(fsm_class_name, trn["common_handler"])
                handlers[key] = value
            dest = trn["dest"]
            dest_type = dest["type"].lower()
            key = ""
            value = ""
            if dest_type == "state":
                continue
            elif dest_type == "changer":
                key = "%s::%s_%s" % (fsm_class_name, state_fn_name, dest["name"])
                value = get_changer_definition(fsm_class_name, dest["name"], state_fn_name)
            elif dest_type == "common_changer":
                key = "%s::%s" % (fsm_class_name, dest["name"])
                value = get_changer_definition(fsm_class_name, dest["name"])
            else:
                raise Exception("Unknown destination type \"%s\"" % dest["type"])
            changers[key] = value

    return (changers, handlers)

def get_handler_definition(fsm_class_name, handler_name, state_name = ""):
    # void <FsmClassName>::<stateName>_<handlerName>(const Message & msg) { 
    #     // put your code here
    # }

    # void <FsmClassName>::<handlerName>(const Message & msg) { 
    #     // put your code here
    # }
    output = StringIO()
    if state_name != "":
        output.write("void %s::%s_%s(const Message& msg) { \n" % (fsm_class_name, state_name, handler_name))
    else:
        output.write("void %s::%s(const Message& msg) { \n" % (fsm_class_name, handler_name))
    output.write("\t// put your code here\n")
    output.write("}\n")
    return output.getvalue()

def get_changer_definition(fsm_class_name, changer_name, state_name = ""):
    # std::pair<fptr, bool> <FsmClassName>::<stateName>_<changerName>(const Message & msg) { 
    #     // put your code here
    #     return remains(false);
    # }

    # std::pair<fptr, bool> <FsmClassName>::<changerName>(const Message & msg) { 
    #     // put your code here
    #     return remains(false);
    # }
    output = StringIO()
    if state_name != "":
        output.write("std::pair<fptr, bool> %s::%s_%s(const Message& msg) { \n" % (fsm_class_name, state_name, changer_name))
    else:
        output.write("std::pair<fptr, bool> %s::%s(const Message& msg) { \n" % (fsm_class_name, changer_name))
    output.write("\t// put your code here\n")
    output.write("\treturn remains(false);\n")
    output.write("}\n")
    return output.getvalue()

def get_on_state_changed_def(fsm):
    output = StringIO()
    output.write("void %s::onStateChanged(fptr old_state, fptr new_state) {\n" % get_fsm_class_name(fsm))
    output.write("\t// Put your code here\n")
    output.write("\t(void)old_state; // UNUSED\n")
    output.write("\t(void)new_state; // UNUSED\n")
    output.write("}\n")
    return output.getvalue()

def update_fsm_handlers_cpp(fsm, fsm_handlers_cpp, changers, handlers):
    onstatechanged_matcher = re.compile(r"\s*void\s*.*::onStateChanged\(fptr\s*old_state,\s*fptr\s*new_state\)\s*\{")
    changer_matcher = re.compile(r"(\s*std::pair<fptr, bool>\s*)(.*::.*_[^_(]*)(\(const Message& msg\)\s*\{)")
    common_changer_matcher = re.compile(r"(\s*std::pair<fptr, bool>\s*)(.*::[^_(]*)(\(const Message\s*&\s*.*\)\s*\{)")
    handler_matcher = re.compile(r"(\s*void\s*)(.*::.*_[^(]*)(\(const Message& msg\)\s*\{)")
    common_handler_matcher = re.compile(r"(\s*void\s*)(.*::[^_(]*)(\(const Message& msg\)\s*\{)")
    
    try:
        infile = open(fsm_handlers_cpp, "rb", 0)
        try:
            has_onstatechanged = False
            existing_changers = []
            existing_handlers = []

            infile.seek(0)
            for line in infile:
                m = onstatechanged_matcher.match(line) 
                if m != None:
                    has_onstatechanged = True
                    continue
                m = changer_matcher.match(line) 
                if m != None:
                    existing_changers.append(m.group(2))
                    continue
                m = common_changer_matcher.match(line)
                if m != None:
                    existing_changers.append(m.group(2))
                    continue
                m = handler_matcher.match(line)
                if m != None:
                    existing_handlers.append(m.group(2))
                    continue
                m = common_handler_matcher.match(line)
                if m != None:
                    existing_handlers.append(m.group(2))
                    continue
        finally:
            infile.close()

        output = StringIO()
        need_write = False
        # check OnStateChanged-handler
        on_state_changed_def = get_on_state_changed_def(fsm)
        if on_state_changed_def != "" and not has_onstatechanged:
            output.write(on_state_changed_def)
            need_write = True
        # check changers
        for (k, v) in changers.items():
            if k not in existing_changers:
                output.write(v)
                need_write = True
        # check handlers
        for (k, v) in handlers.items():
            if k not in existing_handlers:
                output.write(v)
                need_write = True
        if need_write:
            outfile = open(fsm_handlers_cpp, "a+", 0)
            try:
                outfile.write(output.getvalue())
            finally:
                outfile.close()
    except IOError:
        raise Exception("Failed to update file \"%s\"" % fsm_handlers_cpp)

def extract_state_messages(state):
    result = set()
    for trn in state["trans"]:
        msg = trn["msg"]
        if msg != "default":
            result.add(msg)
    return result


def get_state_fn_name(state):
    return capitalize_str(state["name"], camel=1)

def get_fsm_class_name(fsm):
    return capitalize_str(fsm["name"])


def process_template(dest_path, template_name, substitutes, finalize_line_fn=(lambda x: x)):
    try:
        output = StringIO()
        infile_name = os.path.join("src", "templates", template_name)
        infile = open(infile_name, "rb", 0)
        try:
            infile.seek(0)
            for line in infile:
                for sub in substitutes:
                    line = line.replace(sub[0], sub[1])
                output.write(finalize_line_fn(line))
                output.write("\n")
        finally:
            infile.close()

        print dest_path
        outfile = open(dest_path, "w+", 0)
        try:
            outfile.write(output.getvalue())
        finally:
            outfile.close()
    except IOError:
        print "Failed to convert file \"%s\" to file \"%s\"" % (infile_name, dest_path)


def ensure_dir(dir_path):
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)

def make_include_str(file_name):
    return "#include \"%s.h\"" % file_name

def check_key_word(value, key_words, attr_name):
    if value.lower() == "common":
        raise Exception("\"%s\" cannot be used as %s! It is reserved key word" % (value, attr_name))


