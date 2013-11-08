#!/usr/bin/env python
# -*- coding: utf-8 -*
"""
predictionio ratings

$Id$
"""
from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

import gevent
import functools
import transaction
import predictionio

from zope import component

from pyramid.security import authenticated_userid
from pyramid.threadlocal import get_current_request

from contentratings.interfaces import IObjectRatedEvent

from nti.dataserver import users
from nti.dataserver import interfaces as nti_interfaces
from nti.dataserver.contenttypes.forums import interfaces as frm_interfaces

from nti.externalization import externalization

from nti.ntiids import ntiids

from . import get_predictionio_app
from . import interfaces as pio_interfaces

LIKE_API = "like"
DISLIKE_API = "dislike"
LIKE_CAT_NAME = "likes"

def _process_like_api(app, username, oid, api):
	# from IPython.core.debugger import Tracer; Tracer()()
	client = predictionio.Client(app.AppKey, app.URL)
	user = users.User.get_user(username)
	modeled = ntiids.find_object_with_ntiid(oid)
	if modeled is not None and user is not None:
		client.create_user(username, params=pio_interfaces.IProperties(user))
		client.create_item(oid, pio_interfaces.ITypes(modeled),
						   pio_interfaces.IProperties(modeled))
		client.identify(username)
		client.record_action_on_item(api, oid)
	client.close()

def record_like(app, username, oid):
	_process_like_api(app, username, oid, LIKE_API)

def record_unlike(app, username, oid):
	_process_like_api(app, username, oid, DISLIKE_API)

def _process_like_event(username, oid, like=True):
	app = get_predictionio_app()
	def _process_event():
		transaction_runner = \
			component.getUtility(nti_interfaces.IDataserverTransactionRunner)
		if like:
			func = functools.partial(record_like, app=app, username=username, oid=oid)
		else:
			func = functools.partial(record_unlike, app=app, username=username, oid=oid)
		transaction_runner(func)
	transaction.get().addAfterCommitHook(
							lambda success: success and gevent.spawn(_process_event))

@component.adapter(nti_interfaces.IModeledContent, IObjectRatedEvent)
def _object_rated(modeled, event):
	request = get_current_request()
	username = authenticated_userid(request) if request else None
	if username and event.category == LIKE_CAT_NAME:
		like = event.rating != 0
		oid = externalization.to_external_ntiid_oid(modeled)
		_process_like_event(username, oid, like)

@component.adapter(frm_interfaces.ITopic, IObjectRatedEvent)
def _topic_rated(topic, event):
	_object_rated(topic, event)
