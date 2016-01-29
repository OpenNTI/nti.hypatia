#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
generation 4.

.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

generation = 4

from zope import component

from zope.component.hooks import site
from zope.component.hooks import setHooks

from zope.intid.interfaces import IIntIds

from ZODB.POSException import POSKeyError

from nti.contentsearch.constants import type_

from nti.hypatia.catalog import SearchCatalog

from nti.hypatia.interfaces import ISearchCatalog
from nti.hypatia.interfaces import ISearchCatalogQueue

from nti.hypatia.utils import all_indexable_objects_iids

def do_evolve(context):
	setHooks()
	conn = context.connection
	root = conn.root()
	ds_folder = root['nti.dataserver']

	lsm = ds_folder.getSiteManager()
	intids = lsm.getUtility(IIntIds)

	with site(ds_folder):
		assert	component.getSiteManager() == ds_folder.getSiteManager(), \
				"Hooks not installed?"

		# unregister
		old_catalog = lsm.getUtility(provided=ISearchCatalog)
		intids.unregister(old_catalog)
		lsm.unregisterUtility(old_catalog, provided=ISearchCatalog)
		old_catalog.__parent__ = None

		# recreate
		new_catalog = SearchCatalog()
		new_catalog.__parent__ = ds_folder
		new_catalog.__name__ = '++etc++hypatia++catalog'
		intids.register(new_catalog)
		lsm.registerUtility(new_catalog, provided=ISearchCatalog)

		# reset indices
		for k, v in old_catalog.items():
			new_catalog[k] = v

		# search anything that has not been indexed
		total = 0
		type_index = new_catalog[type_]
		search_queue = lsm.getUtility(provided=ISearchCatalogQueue)
		for iid, _ in all_indexable_objects_iids():
			try:
				if not type_index.has_doc(iid):
					search_queue.add(iid)
					total += 1
			except (POSKeyError, TypeError):
				pass
		logger.info('Hypatia evolution gen 4 done; %s missing object(s) indexed', total)
		return total

def evolve(context):
	"""
	Evolve to generation 4 by recreating the catalog
	"""
	do_evolve(context)
