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

from zope.intid import IIntIds

from nti.dataserver.interfaces import IUser

from nti.dataserver.users import User

from nti.hypatia.interfaces import DEFAULT_QUEUE_LIMIT

from nti.hypatia.interfaces import ISearchCatalog
from nti.hypatia.interfaces import ISearchCatalogQueue
from nti.hypatia.interfaces import ISearchCatalogQueueFactory

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
	try:
		from nti.contentsearch.interfaces import ITypeResolver
		return ITypeResolver(x, None) is not None
	except ImportError:
		return False

def queue_length(queue=None):
	queue = queue if queue is not None else search_queue()
	try:
		result = len(queue)
	except ValueError:
		result = 0
		logger.error("Could not compute queue length")
	return result

def process_queue(queue=None, limit=DEFAULT_QUEUE_LIMIT, sync_queue=True, ignore_pke=True):
	ids = component.getUtility(IIntIds)
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
		queue_size = max(0, queue_size - done)
		logger.info("%s event(s) processed in %s(s). Queue size %s", done,
					time.time() - now, queue_size)
	return to_process
