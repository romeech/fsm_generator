/*
	Declarations of all messages in the system. Use it for including in own modules
	This file is automatically generated. Don't edit it, all changes will be lost afer next generating
*/

#ifndef MESSAGES_H
#define MESSAGES_H

#include <memory>
#include "message_data.h"
$INCLUDE_LIST

enum MessageType {
	$MSG_LIST
};

struct Message {
	MessageType type;
	std::shared_ptr<MessageData> data;

    size_t buffer_sz = 0;
    // std::shared_ptr control block is thread safe itself, but underling object isn't
    std::shared_ptr<const unsigned char> buffer;
    std::shared_ptr<const TravelDocument> document1;
    std::shared_ptr<const TravelDocument> document2;

    explicit Message(MessageType mt)
        : type(mt), buffer_sz(0), buffer(nullptr) {}

    void set_docs(const TravelDocument * doc1, const TravelDocument * doc2);


    const TravelDocument * doc1() const { 
        return document1.get();
    }

    const TravelDocument * doc2() const { 
        return document2.get();
    }

    void set_buffer(const unsigned char* ptr, size_t data_size, bool copy=false);
};

namespace std {
    std::string to_string(MessageType mt);
    std::string to_string(const Message & message);
}

inline std::ostream & operator<<(std::ostream & os, const Message & msg) {
    return os << std::to_string(msg);
}

inline std::ostream & operator<<(std::ostream & os, const MessageType & msgtp) {
    return os << std::to_string(msgtp);
}


extern void send_message(const Message &);

#endif  // MESSAGES_H