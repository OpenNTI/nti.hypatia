#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""
from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

import itertools

from zope import component

import zope.intid

from nti.contentsearch.interfaces import ITypeResolver

from nti.dataserver import users
from nti.dataserver.interfaces import IUser

from .interfaces import ISearchCatalog
from .interfaces import ISearchCatalogQueue
from .interfaces import DEFAULT_QUEUE_LIMIT

def search_queue():
	result = component.getUtility(ISearchCatalogQueue)
	return result

def search_catalog():
	result = component.getUtility(ISearchCatalog)
	return result

def get_user(user):
	user = users.User.get_user(str(user)) \
		   if not IUser.providedBy(user) and user else user
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

def process_queue(limit=DEFAULT_QUEUE_LIMIT, sync_queue=True):
	ids = component.getUtility(zope.intid.IIntIds)
	catalog = component.getUtility(ISearchCatalog)

	queue = search_queue()
	if sync_queue and queue.syncQueue():
		logger.debug("Queue synched")
	queue_size = queue_length(queue)

	limit = queue_size if limit == -1 else limit
	to_process = min(limit, queue_size)
	if queue_size > 0:
		logger.info("Taking %s event(s) to process; current queue size %s",
					to_process, queue_size)
		queue.process(ids, (catalog,), to_process)

	return to_process
