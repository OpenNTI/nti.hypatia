#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from datetime import datetime
from collections import Mapping

import pytz
import BTrees

from zope import interface
from zope.container.contained import Contained

from ZODB.interfaces import IBroken
from ZODB.POSException import POSError, POSKeyError

from zc.catalogqueue.queue import CatalogQueue
from zc.catalogqueue.CatalogEventQueue import REMOVED
from zc.catalogqueue.CatalogEventQueue import CatalogEventQueue

from .interfaces import ISearchCatalogQueue
from .interfaces import ISearchCatalogEventQueue

class _ProxyMap(Mapping):
	
	__slots__ = ('_data',)
	
	def __init__(self, data):
		self._data = data
		
	def __getitem__(self, key):
		return self._data[key]
	
	def __len__(self):
		return len(self._data)
	
	def __iter__(self):
		return iter(self._data)

	def items(self):
		for k, v in self._data.items():
			__traceback_info__ = k,v
			yield k,v
		
@interface.implementer(ISearchCatalogEventQueue)
class SearchCatalogEventQueue(Contained, CatalogEventQueue):
	
	def process(self, limit=None):
		result = super(SearchCatalogEventQueue, self).process(limit)
		return _ProxyMap(result)
	
	def keys(self):
		result = list(self._data.keys())
		return result

@interface.implementer(ISearchCatalogQueue)
class SearchCatalogQueue(Contained, CatalogQueue):

	def __init__(self, buckets=1009):
		CatalogQueue.__init__(self, buckets=0)
		self._reset(buckets)

	def _reset(self, buckets=1009):
		self._queues = list()
		self._buckets = buckets
		for i in xrange(buckets):
			queue = SearchCatalogEventQueue()
			queue.__name__ = str(i)
			queue.__parent__ = self
			self._queues.append(queue)
			
	@property
	def buckets(self):
		return self._buckets

	def eventQueueLength(self):
		result = 0
		for queue in self._queues:
			result += len(queue)
		return result
	event_queue_length = eventQueueLength

	def syncQueue(self):
		try:
			length = self._length
		except AttributeError:
			length = self._length = BTrees.Length.Length()
		old = length.value
		new = self.eventQueueLength()
		result = old != new
		if result:  # only set if different
			length.set(new)
		return result
	sync = sync_queue = syncQueue

	changeLength = CatalogQueue._change_length

	def empty(self):
		self._reset(self, buckets=self._buckets)

	def iterkeys(self):
		for queue in self._queues:
			for key in queue.keys():
				yield key
	
	def keys(self):
		return list(self.iterkeys())
	
	def __getitem__(self, idx):
		return self._queues[idx]

	def __iter__(self):
		return iter(self._queues)

	def __str__(self):
		return "%s(%s)" % (self.__class__.__name__, self._buckets)
	__repr__ = __str__
	
	def process(self, ids, catalogs, limit, ignore_pke=True):
		done = 0
		for queue in self._queues:
			for uid, (_, event) in queue.process(limit-done).iteritems():
				try:
					if event is REMOVED:
						for catalog in catalogs:
							catalog.unindex_doc(uid)
					else:
						ob = ids.queryObject(uid)
						if ob is None:
							logger.warn("Couldn't find object for %s", uid)
						elif IBroken.providedBy(ob):
							logger.warn("Ignoring broken object with id %s", uid)
						else:
							for catalog in catalogs:
								catalog.index_doc(uid, ob)
				except (POSKeyError, POSError), e:
					if ignore_pke:
						logger.error("POSError while indexing object with id %s", uid)
					else:
						raise e
				done += 1
				self._change_length(-1)

			if done >= limit:
				break

		self.totalProcessed += done
		self.lastProcessedTime = datetime.now(pytz.UTC)
		return done
