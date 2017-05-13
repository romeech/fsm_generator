#include "message_factory.h"

#include <unordered_map>
#include <stdexcept>
#include <locale>

#include "string_routines.h"

class OnFlyMessageFactory : public MessageFactory {
public:
	Message make(MessageType mt) {
		MessageData* md;
		switch(mt) {
			$MSG_TYPE_CASES			
			default:
				md = nullptr;
		}

		Message res(mt);
		res.data.reset(md);
		return res;
	}
};

class CachedMessageFactory : public MessageFactory {
public:
	Message make(MessageType mt) {
		// Not implemented
		return Message(mt);
	}
};



static MessageFactory* MessageFactory::create(const std::string param_str) {
	strings::keyval_dict dict = strings::str2dict(param_str);
	auto type = dict.find("type");
	if (type == dict.end()) {
		throw std::logic_error("MessageFactory creation failure: parameter 'type' is not set");
	}

	auto type_val = std::tolower(type.second);
	if (type_val.compare("onfly") == 0) {
		// Here one can pass specific params to .ctor
		return new OnFlyMessageFactory();

	} else if (type_val.compare("cached") == 0) {
		// Here one can pass specific params to .ctor
		return new CachedMessageFactory();

	} else {
		throw std::logic_error("MessageFactory creation failure: unknown type");
	}
}
