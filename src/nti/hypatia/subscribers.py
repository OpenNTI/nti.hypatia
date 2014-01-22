#!/usr/bin/env python
# -*- coding: utf-8 -*
"""
subscribers functionality

$Id$
"""
from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope import component
from zope.lifecycleevent import interfaces as lce_interfaces

from zope.intid.interfaces import IIntIdRemovedEvent, IIntIdAddedEvent

from nti.contentsearch import discriminators

from nti.dataserver import interfaces as nti_interfaces

from . import is_indexable
from . import search_queue

def add_2_queue(obj):
	iid = discriminators.query_uid(obj)
	if iid is not None:
		__traceback_info__ = iid
		search_queue().add(iid)
		return True
	return False

def queue_added(obj):
	if is_indexable(obj):
		try:
			add_2_queue(obj)
		except TypeError, e:
			logger.exception(e)

def queue_modified(obj):
	if is_indexable(obj):
		iid = discriminators.query_uid(obj)
		if iid is not None:
			__traceback_info__ = iid
			try:
				search_queue().update(iid)
			except TypeError, e:
				logger.exception(e)
		else:
			logger.debug("Could not find iid for %r", obj)

def queue_remove(obj):
	if is_indexable(obj):
		iid = discriminators.query_uid(obj)
		if iid is not None:
			__traceback_info__ = iid
			search_queue().remove(iid)

@component.adapter(nti_interfaces.IModeledContent, IIntIdRemovedEvent)
def _modeled_removed(modeled, event):
	queue_remove(modeled)

@component.adapter(nti_interfaces.IModeledContent, IIntIdAddedEvent)
def _modeled_added(modeled, event):
	queue_added(modeled)

@component.adapter(nti_interfaces.IModeledContent, lce_interfaces.IObjectModifiedEvent)
def _modeled_modified(modeled, event):
	if nti_interfaces.IDeletedObjectPlaceholder.providedBy(modeled):
		queue_remove(modeled)
	else:
		queue_modified(modeled)

