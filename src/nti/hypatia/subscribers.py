#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""
from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

import gevent
import functools
import transaction

from zope import component
from zope.lifecycleevent.interfaces import IObjectRemovedEvent

from nti.contentsearch.constants import acl_
from nti.contentsearch.discriminators import query_uid

from nti.dataserver.users import Entity
from nti.dataserver.interfaces import IUser
from nti.dataserver.interfaces import IEntity
from nti.dataserver.interfaces import IReadableShared
from nti.dataserver.interfaces import IDeletedObjectPlaceholder
from nti.dataserver.interfaces import ITargetedStreamChangeEvent
from nti.dataserver.interfaces import IDataserverTransactionRunner
from nti.dataserver.interfaces import SC_CREATED, SC_SHARED, SC_MODIFIED, SC_DELETED

from . import is_indexable
from . import search_queue
from . import search_catalog

def add_2_queue(obj):
	iid = query_uid(obj)
	if iid is not None:
		__traceback_info__ = iid
		search_queue().add(iid)
		return True
	return False

def queue_added(obj):
	if is_indexable(obj):
		try:
			return add_2_queue(obj)
		except TypeError:
			pass
	return False

def queue_modified(obj):
	if is_indexable(obj):
		iid = query_uid(obj)
		if iid is not None:
			__traceback_info__ = iid
			try:
				search_queue().update(iid)
				return True
			except TypeError:
				pass
	return False

def queue_remove(obj):
	if is_indexable(obj):
		iid = query_uid(obj)
		if iid is not None:
			__traceback_info__ = iid
			search_queue().remove(iid)

# IIntIdRemovedEvent
def _object_removed(modeled, event):
	queue_remove(modeled)

# IIntIdAddedEvent
def _object_added(modeled, event):
	queue_added(modeled)

# IObjectModifiedEvent
def _object_modified(modeled, event):
	if IDeletedObjectPlaceholder.providedBy(modeled):
		queue_remove(modeled)
	else:
		queue_modified(modeled)

def delete_userdata(username):
	logger.info("Removing hypatia search data for user %s", username)
	catalog = search_catalog()
	kwIndex = catalog[acl_]
	docids = kwIndex.remove_word(username)
	for docid in docids or ():
		search_queue().remove(docid)
	return len(docids)

@component.adapter(IUser, IObjectRemovedEvent)
def _user_deleted(user, event):
	username = user.username
	def _process_event():
		transaction_runner = \
			component.getUtility(IDataserverTransactionRunner)
		func = functools.partial(delete_userdata, username=username)
		transaction_runner(func)
		return True

	transaction.get().addAfterCommitHook(
					lambda success: success and gevent.spawn(_process_event))

# on change listener

_changeType_events = (SC_CREATED, SC_SHARED, SC_MODIFIED)

@component.adapter(ITargetedStreamChangeEvent)
def onChange(event):
	change = event.object
	target = event.target
	changeType, changeObject = change.type, change.object
	entity = Entity.get_entity(str(target)) \
			 if not IEntity.providedBy(target) else target

	should_process = IUser.providedBy(entity)
	if should_process:
		if 	changeType in _changeType_events and \
			IReadableShared.providedBy(changeObject):
			should_process = changeObject.isSharedDirectlyWith(entity)

	if should_process:
		if changeType != SC_DELETED:
			queue_added(changeObject)

	return should_process
