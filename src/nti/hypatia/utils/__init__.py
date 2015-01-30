#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

import six

import zope.intid

from zope import component
from zope.catalog.interfaces import ICatalog

from ZODB.POSException import POSError

from nti.contentsearch.interfaces import IContentResolver

from nti.dataserver.interfaces import IDeletedObjectPlaceholder

from nti.dataserver.metadata_index import IX_CREATOR
from nti.dataserver.metadata_index import IX_SHAREDWITH
from nti.dataserver.metadata_index import CATALOG_NAME as METADATA_CATALOG_NAME

from nti.externalization.oids import to_external_oid

from nti.hypatia import is_indexable

def _is_indexable_and_valid_object(obj, usernames=(), resolve=True):
	if IDeletedObjectPlaceholder.providedBy(obj):
		return False

	if not is_indexable(obj):
		return False
	
	if usernames:
		# get the object creator to try to trigger a POSError if the object is invalid
		creator = getattr(obj, 'creator', None) or u''
		username = getattr(creator, 'username', creator)
		if  not isinstance(username, six.string_types) or \
			username.lower() not in usernames:
			return False
	
	if resolve:
		# resolve the content to try trigger POSError if the object is invalid
		IContentResolver(obj).content
	return True
		
def all_indexable_objects_iids(users=(), resolve=True):
	obj = None
	intids = component.getUtility(zope.intid.IIntIds)
	usernames = {getattr(user, 'username', user).lower() for user in users or ()}
	for uid in intids:
		try:
			obj = intids.getObject(uid)
			if _is_indexable_and_valid_object(obj, usernames, resolve=resolve):
				yield uid, obj
		except (POSError, TypeError, AttributeError) as e:
			logger.error("Ignoring %s(%s); %s", type(obj), uid, e)

def all_cataloged_objects(users=(), sharedWith=False, resolve=True):
	intids = component.getUtility(zope.intid.IIntIds)
	catalog = component.getUtility(ICatalog, METADATA_CATALOG_NAME)
	usernames = {getattr(user, 'username', user).lower() for user in users or ()}
	if usernames:
		intids_created_by = catalog[IX_CREATOR].apply({'any_of': usernames})
	else:
		intids_created_by = catalog[IX_CREATOR].ids()

	def _validate(uid):
		try:
			obj = intids.getObject(uid)
			if 	_is_indexable_and_valid_object(obj, resolve=resolve):
				return obj
		except (POSError, TypeError, AttributeError) as e:
			logger.error("Ignoring %s(%s); %s", type(obj), uid, e)
		return None
			
	for uid in intids_created_by:
		obj = _validate(uid)
		if obj is not None:
			yield uid, obj
				
	if usernames and sharedWith:
		intids_sharedWith = catalog[IX_SHAREDWITH].apply({'any_of': usernames})
	else:
		intids_sharedWith = ()

	for uid in intids_sharedWith:
		obj = _validate(uid)
		if obj is not None:
			yield uid, obj
