#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
generation 5.

.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

generation = 5

from zope import component

from zope.component.hooks import site
from zope.component.hooks import setHooks

from zope.intid.interfaces import IIntIds

from nti.hypatia.interfaces import ISearchCatalogQueue

from nti.hypatia.queue import SearchCatalogQueue

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
		old_catalog_queue = lsm.getUtility(provided=ISearchCatalogQueue)
		intids.unregister(old_catalog_queue)
		lsm.unregisterUtility(old_catalog_queue, provided=ISearchCatalogQueue)
		old_catalog_queue.__parent__ = None

		# recreate
		new_catalog_queue = SearchCatalogQueue(old_catalog_queue._buckets)
		new_catalog_queue.__parent__ = ds_folder
		new_catalog_queue.__name__ = '++etc++hypatia++catalogqueue'
		intids.register(new_catalog_queue)
		lsm.registerUtility(new_catalog_queue, provided=ISearchCatalogQueue)

		# update new event queues
		for idx, old_event_queue in enumerate(old_catalog_queue._queues):
			new_event_queue = new_catalog_queue[idx]
			new_event_queue._data.update(old_event_queue._data)
			new_event_queue._conflict_policy = old_event_queue._conflict_policy

		# sync
		new_catalog_queue.syncQueue()

		logger.info('Hypatia evolution gen 5 done')

def evolve(context):
	"""
	Evolve to generation 5 by recreating the search catalog queue
	"""
	do_evolve(context)
