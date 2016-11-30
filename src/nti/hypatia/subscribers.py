#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope import component

from zope.lifecycleevent.interfaces import IObjectRemovedEvent

# from nti.contentsearch.discriminators import query_uid

from nti.dataserver.interfaces import SC_SHARED
from nti.dataserver.interfaces import SC_CREATED
from nti.dataserver.interfaces import SC_DELETED
from nti.dataserver.interfaces import SC_MODIFIED

from nti.dataserver.interfaces import IUser
from nti.dataserver.interfaces import IEntity
from nti.dataserver.interfaces import IReadableShared
from nti.dataserver.interfaces import IDeletedObjectPlaceholder
from nti.dataserver.interfaces import ITargetedStreamChangeEvent

from nti.dataserver.users import Entity

from nti.hypatia import is_indexable
from nti.hypatia import search_queue
from nti.hypatia import search_catalog

def add_2_queue(obj):
	iid = None # query_uid(obj)
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
		iid = None # query_uid(obj)
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
		iid = None # query_uid(obj)
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
	username = username.lower()
	catalog = search_catalog()
	# remove from ACL index
	kwIndex = catalog['acl']
	kwIndex.remove_word(username)
	# remove from creator index
	crIndex = catalog['creator']
	try:
		docids = crIndex._fwd_index[username]
		for docid in list(docids or ()):
			crIndex.unindex_doc(docid)
	except KeyError:  # pragma no cover
		pass

@component.adapter(IUser, IObjectRemovedEvent)
def _user_deleted(user, event):
	username = user.username
	delete_userdata(username)

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
