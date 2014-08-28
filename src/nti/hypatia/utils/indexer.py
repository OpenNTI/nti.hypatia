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
import zope.browserpage

from zope.container.contained import Contained
from zope.configuration import xmlconfig, config
from zope.dottedname import resolve as dottedname

from z3c.autoinclude.zcml import includePluginsDirective

from nti.dataserver.utils import run_with_dataserver

from nti.hypatia.reactor import IndexReactor
from nti.hypatia.reactor import MIN_INTERVAL
from nti.hypatia.reactor import MAX_INTERVAL
from nti.hypatia.reactor import DEFAULT_SLEEP
from nti.hypatia.reactor import DEFAULT_RETRIES
from nti.hypatia.reactor import DEFAULT_INTERVAL
from nti.hypatia.interfaces import DEFAULT_QUEUE_LIMIT

def sigint_handler(*args):
	logger.info("Shutting down %s", os.getpid())
	sys.exit(0)

def handler(*args):
	raise SystemExit()

signal.signal(signal.SIGINT, sigint_handler)
signal.signal(signal.SIGTERM, handler)

# package loader info

class PluginPoint(Contained):

	def __init__(self, name):
		self.__name__ = name

PP_APP = PluginPoint('nti.app')
PP_APP_SITES = PluginPoint('nti.app.sites')
PP_APP_PRODUCTS = PluginPoint('nti.app.products')

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
	arg_parser.add_argument('--redis', help="Use redis lock", action='store_true',
							 dest='redis')

	args = arg_parser.parse_args()
	env_dir = os.getenv('DATASERVER_DIR')
	if not env_dir or not os.path.exists(env_dir) and not os.path.isdir(env_dir):
		raise IOError("Invalid dataserver environment root directory")

	context = _create_context(env_dir)
	conf_packages = ('nti.appserver', 'nti.hypatia')

	run_with_dataserver(environment_dir=env_dir,
						xmlconfig_packages=conf_packages,
						verbose=args.verbose,
						context=context,
						minimal_ds=True,
						use_transaction_runner=False,
						function=lambda: _process_args(args))

def _create_context(env_dir, devmode=False):
	etc = os.getenv('DATASERVER_ETC_DIR') or os.path.join(env_dir, 'etc')
	etc = os.path.expanduser(etc)

	context = config.ConfigurationMachine()
	xmlconfig.registerCommonDirectives(context)

	if devmode:
		context.provideFeature("devmode")
		
	slugs = os.path.join(etc, 'package-includes')
	if os.path.exists(slugs) and os.path.isdir(slugs):
		package = dottedname.resolve('nti.dataserver')
		context = xmlconfig.file('configure.zcml', package=package, context=context)
		xmlconfig.include(context, files=os.path.join(slugs, '*.zcml'),
						  package='nti.appserver')

	# Include zope.browserpage.meta.zcm for tales:expressiontype
	# before including the products
	xmlconfig.include(context, file="meta.zcml", package=zope.browserpage)

	# include plugins
	includePluginsDirective(context, PP_APP)
	includePluginsDirective(context, PP_APP_SITES)
	includePluginsDirective(context, PP_APP_PRODUCTS)
	
	return context

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
	
	mintime = max(min(mintime, MAX_INTERVAL), MIN_INTERVAL)
	maxtime = max(min(maxtime, MAX_INTERVAL), MIN_INTERVAL)

	ei = '%(asctime)s %(levelname)-5.5s [%(name)s][%(thread)d][%(threadName)s] %(message)s'
	logging.root.handlers[0].setFormatter(zope.exceptions.log.Formatter(ei))

	target = IndexReactor(min_time=mintime, max_time=maxtime, limit=limit,
						  retries=retries, sleep=sleep, use_redis=args.redis)
	result = target(time.sleep)
	sys.exit(result)

if __name__ == '__main__':
	main()
