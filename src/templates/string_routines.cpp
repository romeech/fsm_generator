// string_routines.cpp

#include <iomanip>
#include <algorithm>

#include "string_routines.h"

namespace strings {
    std::string makeHexString(int value) {
        std::stringstream stringBuilder;
        stringBuilder << std::hex
                << std::setw(2)
                << std::setfill('0')
                << std::uppercase << value;

        return stringBuilder.str();
    }

    std::string trim_spaces(const std::string &s) {
        std::string r(s);
        r.erase( std::remove_if( r.begin(), r.end(), ::isspace ), r.end() );
        return r;
    }

    std::string trim_spaces(std::string&& s) {
        std::string r(std::move(s));
        r.erase( std::remove_if( r.begin(), r.end(), ::isspace ), r.end() );
        return r;
    }

    keyval_dict str2dict(const std::string s) {
        keyval_dict kv;
        for (auto pair_str : strings::split(s, ',')) {
            auto key_val = strings::split(pair_str, '=');
            kv.emplace(trim_spaces(key_val[0]), trim_spaces(key_val[1]));
        }
        return kv;
    }
}
