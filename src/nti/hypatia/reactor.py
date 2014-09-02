#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""
from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from nti.monkey import relstorage_patch_all_except_gevent_on_import
relstorage_patch_all_except_gevent_on_import.patch()

import os
import time
import gevent
import random
import functools

from zope import component
from zope import interface
from zope.component import ComponentLookupError

from ZODB import loglevels
from ZODB.POSException import POSKeyError
from ZODB.POSException import ConflictError

from redis.connection import ConnectionError

from nti.dataserver.interfaces import IRedisClient
from nti.dataserver.interfaces import IDataserverTransactionRunner

from nti.zodb.interfaces import UnableToAcquireCommitLock

from . import LOCK_NAME
from . import process_queue

from .interfaces import IIndexReactor
from .interfaces import DEFAULT_QUEUE_LIMIT

MIN_INTERVAL = 5
MAX_INTERVAL = 60
MIN_BATCH_SIZE = 10

DEFAULT_SLEEP = 1
DEFAULT_RETRIES = 2
DEFAULT_INTERVAL = 30

POS_KEY_ERROR_RT = -2
CONFLICT_ERROR_RT = -1

class _MockLockingClient(object):

	singleton = None
	
	def __new__(cls, *args, **kwargs):
		if not cls.singleton:
			cls.singleton = super(_MockLockingClient, cls).__new__(cls)
		return cls.singleton
	
	def lock(self, *args, **kwargs):
		return self

	def acquire(self, *args, **kwargs):
		return True

	def release(self, *args, **kwargs):
		pass

def process_index_msgs(limit=DEFAULT_QUEUE_LIMIT, 
					   retries=DEFAULT_RETRIES,
					   sleep=DEFAULT_SLEEP,
					   lock_client=None, 
					   lock_name=LOCK_NAME):

	lock_client = lock_client if lock_client is not None else _MockLockingClient()
	try:
		lock = lock_client.lock(lock_name, MAX_INTERVAL)
		aquired = lock.acquire(blocking=False)
	except TypeError:
		lock = lock_client.lock(lock_name)
		aquired = lock.acquire()

	result = 0
	try:
		if aquired:
			try:
				runner = functools.partial(process_queue, limit=limit)
				transaction_runner = component.getUtility(IDataserverTransactionRunner)
				result = transaction_runner(runner, retries=retries, sleep=sleep)
			except POSKeyError:
				logger.exception("Cannot index object(s)")
				result = POS_KEY_ERROR_RT
			except (UnableToAcquireCommitLock, ConflictError) as e:
				logger.error(e)
				result = CONFLICT_ERROR_RT
			except (TypeError, StandardError): # Cache errors?
				logger.exception('Cannot process index messages')
				raise
	finally:
		if aquired:
			lock.release()
	return result

@interface.implementer(IIndexReactor)
class IndexReactor(object):

	# transaction runner
	sleep = DEFAULT_SLEEP
	retries = DEFAULT_RETRIES
	# wait time
	min_wait_time = 10
	max_wait_time = 30
	# batch size
	limit = DEFAULT_QUEUE_LIMIT
	
	stop = False
	start_time = 0
	processor = pid = None

	def __init__(self, min_time=None, max_time=None, limit=None, 
				 retries=None, sleep=None, use_redis=False):
		
		if min_time:
			self.min_wait_time = min_time
		
		if max_time:
			self.max_wait_time = max_time
			
		if limit and limit != DEFAULT_QUEUE_LIMIT:
			self.limit = limit
		
		if sleep:
			self.sleep = sleep
			
		if retries:
			self.retries = retries
			
		if not use_redis:
			self.lock_client = _MockLockingClient()
		else:
			self.lock_client = component.getUtility(IRedisClient) 

	def __repr__(self):
		return "%s" % (self.__class__.__name__.lower())

	def halt(self):
		self.stop = True

	def start(self):
		if self.processor is None:
			self.processor = self._spawn_index_processor()
		return self
	
	def run(self, sleep=gevent.sleep):
		result = 0
		self.stop = False
		self.pid = os.getpid()
		generator = random.Random()
		self.start_time = time.time()
		try:
			batch_size = self.limit
			logger.info("Index reactor started")
			while not self.stop:
				start = time.time()
				try:
					if not self.stop:
						result = process_index_msgs(batch_size,
												 	sleep=self.sleep,
												 	retries=self.retries,
													lock_client=self.lock_client)
						duration = time.time() - start
						if result == 0: # no work
							batch_size = self.limit  # reset to default
							secs = generator.randint(self.min_wait_time, 
													 self.max_wait_time)
							duration = secs
						elif result < 0:  # conflict error/exception
							factor = 0.33 if result == CONFLICT_ERROR_RT else 0.2
							batch_size = max(MIN_BATCH_SIZE, int(batch_size * factor))
							duration = min(duration * 2.0, MAX_INTERVAL * 3.0)
						elif duration < MAX_INTERVAL:
							batch_size = int(batch_size * 1.5)
							half = int(duration / 2.0)
							secs = generator.randint(self.min_wait_time,
												  	 max(self.min_wait_time, half))
							duration = secs
						else:
							half = batch_size * .5
							batch_size = max(MIN_BATCH_SIZE, int(half / duration))
							secs = generator.randint(self.min_wait_time, 
													 self.max_wait_time)
							duration = secs
							
						logger.log(loglevels.TRACE, "Sleeping %s(secs). Batch size %s",
								   duration, batch_size)
						sleep(duration)
				except ComponentLookupError:
					result = 99
					logger.error("process could not get component", self.pid)
					break
				except KeyboardInterrupt:
					break
				except ConnectionError:
					result = 66
					logger.exception("%s could not connect to redis", self.pid)
					break
				except (TypeError, StandardError):
					result = 77 # Cache errors?
					break
				except:
					logger.exception("Unhandled exception")
					raise
		finally:
			self.processor = None
		return result

	__call__ = run

	def _spawn_index_processor(self):
		result = gevent.spawn(self.run)
		return result
