/* 
	This file is supposed to contained custom data members 
	and methods of $FSM_CLASS_NAME 
	It isn't overridden by next generatings
*/
#ifndef $INC_GUARD_H
#define $INC_GUARD_H

#include "fsa.h"
#include "fsa_impl.h"

class $FSM_CLASS_NAME_Impl : public FsmImpl {
public:
	std::pair<fptr, bool> getInitialState(const FsmSettings* msg); // do not change the signature!
	const char* fsm_full_name() const { return "$FSM_CLASS_NAME"; } // do not change the signature!
};

#endif  // $INC_GUARD_H
