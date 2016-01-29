#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
generation 7.

.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

generation = 7

from zope import component

from zope.component.hooks import site
from zope.component.hooks import setHooks

from zope.intid.interfaces import IIntIds

from ZODB.POSException import POSKeyError

from nti.contentsearch.constants import type_

from nti.dataserver.contenttypes.forums.interfaces import ICommentPost

from nti.hypatia.interfaces import ISearchCatalog

def do_evolve(context):
	setHooks()
	conn = context.connection
	root = conn.root()
	ds_folder = root['nti.dataserver']

	lsm = ds_folder.getSiteManager()
	logger.info('Hypatia evolution %s started', generation)

	with site(ds_folder):
		assert	component.getSiteManager() == ds_folder.getSiteManager(), \
				"Hooks not installed?"

		intids = lsm.getUtility(IIntIds)

		obj = None
		count = 0
		catalog = lsm.getUtility(provided=ISearchCatalog)
		type_index = catalog[type_]
		for uid in list(type_index.indexed()):
			try:
				obj = intids.queryObject(uid)
				if obj is None:
					catalog.unindex_doc(uid)
					logger.warn("Unindexing missing object %s", uid)
				elif ICommentPost.providedBy(obj):
					type_index.unindex_doc(uid)
					type_index.index_doc(uid, obj)
					count += 1
			except POSKeyError:
				logger.exception("Ignoring broken object %s,%r", uid, obj)

		logger.info('%s comment object(s) reindexed', count)
		logger.info('Hypatia evolution %s done', generation)

def evolve(context):
	"""
	Evolve to generation 7 by changing type for comments
	"""
	do_evolve(context)
