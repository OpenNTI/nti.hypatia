#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

import os
import sys
import time
import signal
import argparse

import zope.exceptions

from zope import component

from ZODB.interfaces import IDatabase

from nti.dataserver.utils import open_all_databases
from nti.dataserver.utils import run_with_dataserver
from nti.dataserver.utils.base_script import create_context
	
from nti.hypatia.reactor import IndexReactor
from nti.hypatia.reactor import MIN_WAIT_TIME
from nti.hypatia.reactor import MAX_WAIT_TIME
from nti.hypatia.reactor import DEFAULT_SLEEP
from nti.hypatia.reactor import DEFAULT_RETRIES
from nti.hypatia.reactor import DEFAULT_INTERVAL

from nti.hypatia.interfaces import DEFAULT_QUEUE_LIMIT

def sigint_handler(*args):
	logger.info("Shutting down %s", os.getpid())
	sys.exit(0)

def handler(*args):
	raise SystemExit()

signal.signal(signal.SIGTERM, handler)
signal.signal(signal.SIGINT, sigint_handler)

def main():
	arg_parser = argparse.ArgumentParser(description="Index processor")
	arg_parser.add_argument('-v', '--verbose', help="Be verbose", action='store_true',
							 dest='verbose')
	arg_parser.add_argument('-r', '--retries',
							 dest='retries',
							 help="Transaction runner retries",
							 type=int,
							 default=DEFAULT_RETRIES)
	arg_parser.add_argument('-s', '--sleep',
							 dest='sleep',
							 help="Transaction runner sleep time (secs)",
							 type=float,
							 default=DEFAULT_SLEEP)
	arg_parser.add_argument('-m', '--mintime',
							 dest='mintime',
							 help="Min poll time interval (secs)",
							 type=int,
							 default=DEFAULT_INTERVAL)
	arg_parser.add_argument('-x', '--maxtime',
							 dest='maxtime',
							 help="Max poll time interval (secs)",
							 type=int,
							 default=DEFAULT_INTERVAL)
	arg_parser.add_argument('-l', '--limit',
							 dest='limit',
							 help="Queue limit",
							 type=int,
							 default=DEFAULT_QUEUE_LIMIT)
	arg_parser.add_argument('--pke', help="Don't ignore POSKeyErrors", 
							 action='store_true',
							 dest='allow_pke')

	args = arg_parser.parse_args()
	env_dir = os.getenv('DATASERVER_DIR')
	if not env_dir or not os.path.exists(env_dir) and not os.path.isdir(env_dir):
		raise IOError("Invalid dataserver environment root directory")

	context = create_context(env_dir)
	conf_packages = ('nti.appserver', 'nti.hypatia')

	run_with_dataserver(environment_dir=env_dir,
						xmlconfig_packages=conf_packages,
						verbose=args.verbose,
						context=context,
						minimal_ds=True,
						use_transaction_runner=False,
						function=lambda: _process_args(args))

def _process_args(args):
	import logging

	mintime = args.mintime
	maxtime = args.maxtime
	assert mintime <= maxtime and mintime > 0

	limit = args.limit
	assert limit > 0
	
	retries = args.retries
	assert retries >= 1 and retries <= 5

	sleep = args.sleep
	assert sleep >= 0 and sleep <= 10

	ignore_pke = not args.allow_pke 
	mintime = min(max(mintime, MIN_WAIT_TIME), MAX_WAIT_TIME)
	maxtime = max(min(maxtime, MAX_WAIT_TIME), MIN_WAIT_TIME)

	ei = '%(asctime)s %(levelname)-5.5s [%(name)s][%(thread)d][%(threadName)s] %(message)s'
	logging.root.handlers[0].setFormatter(zope.exceptions.log.Formatter(ei))
	
	## open connections to all databases
	## so they can be recycled in the connection pool
	db = component.getUtility(IDatabase)
	open_all_databases(db, close_children=False)
	
	target = IndexReactor(min_time=mintime, max_time=maxtime, limit=limit,
						  ignore_pke=ignore_pke, retries=retries, sleep=sleep)
	result = target(time.sleep)
	sys.exit(result)

if __name__ == '__main__':
	main()
