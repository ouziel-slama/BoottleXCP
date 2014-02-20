#! /usr/bin/env python3

import time, sys

while True:
	sys.stdout.write("stdout\n")
	sys.stderr.write("stderr\n")
	time.sleep(2)