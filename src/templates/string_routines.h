// string_routines.h

#ifndef STRING_ROUTINES_H
#define STRING_ROUTINES_H

#include <time.h>
#include <vector>
#include <string>
#include <sstream>
#include <iomanip>
#include <unordered_map>


namespace std {
    inline std::string to_string(const char * data) {
        return std::string(data);
    }

    inline std::string to_string(struct tm data) {
        char buffer[27];
        return std::string(asctime_r(&data, buffer));
    }
}

namespace strings {
    template <typename StrType,
              typename CharType,
              typename StreamType>
    std::vector<StrType> base_split(const StrType& s, CharType delim) {
        std::vector<StrType> elems;
        StreamType ss(s);
        StrType item;
        while (std::getline(ss, item, delim)) {
            elems.push_back(item);
        }
        return std::move(elems);
    }

    typedef std::vector<std::string> (*split_t)(const std::string&, char);
    split_t const split = &base_split<std::string, char, std::stringstream>;

    typedef std::vector<std::wstring> (*wsplit_t)(const std::wstring&, wchar_t);
    wsplit_t const wsplit = &base_split<std::wstring, wchar_t, std::wstringstream>;

    std::string trim_spaces(const std::string& s);
    std::string trim_spaces(std::string&& s);

    typedef std::unordered_map<std::string, std::string> keyval_dict;
    keyval_dict str2dict(const std::string s);

    // convert number to string with str_len size
    // (fill with zeros to the left)
    template <typename T>
    std::string numToStr(T number, size_t str_len) {
        std::stringstream ss;
        ss << std::setfill('0') << std::setw(str_len) << number;
        return ss.str();
    }

    std::string makeHexString(int value);

    template<typename ValType, typename... ValTypesRest> 
    std::string makeString(ValType val, ValTypesRest... rest_values) {
        return std::to_string(val) + makeString(rest_values...);
    }

    template<typename ValType> 
    std::string makeString(ValType val) {
        return std::to_string(val);
    }

    inline std::string makeString(std::string val) {
        return val;
    }

}  // strings

#endif // STRING_ROUTINES_H
