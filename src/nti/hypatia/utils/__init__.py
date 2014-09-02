#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
hypatia utils

.. $Id$
"""
from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

import zope.intid
from zope import component
from zope.catalog.interfaces import ICatalog

from ZODB.POSException import POSKeyError

from nti.contentsearch.interfaces import IContentResolver

from nti.dataserver.interfaces import IDeletedObjectPlaceholder
from nti.dataserver.metadata_index import CATALOG_NAME as METADATA_CATALOG_NAME

from nti.externalization.oids import to_external_oid

from nti.hypatia import is_indexable

def _is_indexable_and_valid_object(obj, usernames=()):
	# get the object creator to try to trigger a POSKeyError 
	# if the object is invalid
	creator = getattr(obj, 'creator', None) or u''
	username = getattr(creator, 'username', creator).lower()
	result =  is_indexable(obj) and not IDeletedObjectPlaceholder.providedBy(obj) and \
			  (not usernames or username in usernames) 
	if result:
		# resolve the content to try trigger POSKeyError if the object is invalid
		resolver = IContentResolver(obj, None)
		getattr(resolver, 'content', None)
	return result
		
def all_indexable_objects_iids(users=()):
	obj = None
	intids = component.getUtility(zope.intid.IIntIds)
	usernames = {getattr(user, 'username', user).lower() for user in users or ()}
	for uid in intids:
		try:
			obj = intids.getObject(uid)
			if _is_indexable_and_valid_object(obj, usernames):
				yield uid, obj
		except (POSKeyError, TypeError) as e:
			logger.error("Ignoring %s(%s); %s", type(obj), uid, e)

def all_cataloged_objects(users=()):
	obj = None
	intids = component.getUtility(zope.intid.IIntIds)
	catalog = component.getUtility(ICatalog, METADATA_CATALOG_NAME)
	usernames = {getattr(user, 'username', user).lower() for user in users or ()}
	if usernames:
		intids_created_by = catalog['creator'].apply({'any_of': usernames})
	else:
		intids_created_by = catalog['creator'].ids()

	for uid in intids_created_by:
		try:
			obj = intids.getObject(uid)
			if 	_is_indexable_and_valid_object(obj):
				yield uid, obj
		except (POSKeyError, TypeError) as e:
			logger.error("Ignoring %s(%s); %s", type(obj), uid, e)
