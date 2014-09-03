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

import zope.intid

from zope import component
from zope.component.hooks import site, setHooks

from ZODB.POSException import POSKeyError

from nti.contentsearch.constants import type_

from nti.dataserver.contenttypes.forums.interfaces import ICommentPost

from ..interfaces import ISearchCatalog

def do_evolve(context):
	setHooks()
	conn = context.connection
	root = conn.root()
	ds_folder = root['nti.dataserver']

	lsm = ds_folder.getSiteManager()

	with site(ds_folder):
		assert	component.getSiteManager() == ds_folder.getSiteManager(), \
				"Hooks not installed?"

		intids = lsm.getUtility(zope.intid.IIntIds)
			
		obj = None
		catalog = lsm.getUtility(provided=ISearchCatalog)
		type_index = catalog[type_]
		for uid in list(type_index.indexed()):
			try:
				obj = intids.getObject(uid)
				if ICommentPost.providedBy(obj):
					type_index.unindex_doc(uid)
					type_index.index_doc(uid, obj)
			except POSKeyError:
				logger.exception("Ignoring broken object %s,%r", uid, obj)
		
		logger.info('Hypatia evolution %s done', generation)

def evolve(context):
	"""
	Evolve to generation 7 by changing type for comments
	"""
	do_evolve(context)
