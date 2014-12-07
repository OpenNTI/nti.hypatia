#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

import time
import itertools

from zope import component

import zope.intid

from nti.contentsearch.interfaces import ITypeResolver

from nti.dataserver.users import User
from nti.dataserver.interfaces import IUser

from .interfaces import ISearchCatalog
from .interfaces import ISearchCatalogQueue
from .interfaces import DEFAULT_QUEUE_LIMIT
from .interfaces import ISearchCatalogQueueFactory

def search_queue():
	factory = component.getUtility(ISearchCatalogQueueFactory)
	result = factory.get_queue()
	return result

def search_catalog():
	result = component.getUtility(ISearchCatalog)
	return result

def get_user(user):
	user = User.get_user(str(user)) if user and not IUser.providedBy(user) else user
	return user

def get_usernames_of_dynamic_memberships(user):
	user = get_user(user)
	dynamic_memberships = getattr(user, 'usernames_of_dynamic_memberships', ())
	usernames = itertools.chain((user.username,), dynamic_memberships)
	result = {x.lower() for x in usernames}
	return result

def is_indexable(x):
	return ITypeResolver(x, None) is not None

def queue_length(queue=None):
	queue = queue if queue is not None else search_queue()
	try:
		result = len(queue)
	except ValueError:
		result = 0
		logger.error("Could not compute queue length")
	return result

def process_queue(queue=None, limit=DEFAULT_QUEUE_LIMIT, sync_queue=True, 
				  ignore_pke=True):
	ids = component.getUtility(zope.intid.IIntIds)
	catalog = component.getUtility(ISearchCatalog)

	queue = search_queue() if queue is None else queue
	if sync_queue and queue.syncQueue():
		logger.debug("Queue synched")
	queue_size = queue_length(queue)

	limit = queue_size if limit == -1 else limit
	to_process = min(limit, queue_size)
	if queue_size > 0:
		now = time.time()
		done = queue.process(ids, (catalog,), to_process, ignore_pke=ignore_pke)
		queue_size = max(0, queue_size-done)
		logger.info("%s event(s) processed in %s(s).Queue size %s", done, 
					time.time()-now, queue_size)
	return to_process
