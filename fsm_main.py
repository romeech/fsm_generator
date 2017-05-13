import os, sys
import fsm_parser
import fsm_builder

if __name__ == "__main__":
	metadata = {}
	fsm_parser.parse(sys.argv[1], metadata)
	fsm_builder.buildWorld(metadata, sys.argv[2])