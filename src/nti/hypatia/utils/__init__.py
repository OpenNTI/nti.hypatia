#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

import six

from zope import component

from zope.catalog.interfaces import ICatalog

from zope.intid.interfaces import IIntIds

from nti.dataserver.interfaces import IDeletedObjectPlaceholder

from nti.dataserver.metadata_index import IX_CREATOR
from nti.dataserver.metadata_index import IX_SHAREDWITH
from nti.dataserver.metadata_index import CATALOG_NAME as METADATA_CATALOG_NAME

from nti.externalization.oids import to_external_oid

from nti.hypatia import is_indexable

from nti.zodb import isBroken

def _is_indexable_and_valid_object(obj, usernames=(), *args, **kwargs):
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
	return True

def all_indexable_objects_iids(users=(), *args, **kwargs):
	obj = None
	intids = component.getUtility(IIntIds)
	usernames = {getattr(user, 'username', user).lower() for user in users or ()}
	for uid in intids:
		try:
			obj = intids.queryObject(uid)
			if not isBroken(obj, uid) and _is_indexable_and_valid_object(obj, usernames):
				yield uid, obj
		except AttributeError as e:
			logger.error("Ignoring %s(%s); %s", type(obj), uid, e)

def all_cataloged_objects(users=(), sharedWith=False, *args, **kwargs):
	intids = component.getUtility(IIntIds)
	catalog = component.getUtility(ICatalog, METADATA_CATALOG_NAME)
	usernames = {getattr(user, 'username', user).lower() for user in users or ()}
	if usernames:
		intids_created_by = catalog[IX_CREATOR].apply({'any_of': usernames})
	else:
		intids_created_by = catalog[IX_CREATOR].ids()

	def _validate(uid):
		try:
			obj = intids.queryObject(uid)
			if not isBroken(obj, uid) and _is_indexable_and_valid_object(obj):
				return obj
		except AttributeError as e:
			logger.error("Ignoring %s(%s); %s", type(obj), uid, e)
		return None

	for uid in intids_created_by:
		obj = intids.queryObject(uid)
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
