#!/usr/bin/env python
# -*- coding: utf-8 -*
"""
predictionIO adapters

$Id$
"""
from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

from zope import component
from zope import interface

from nti.dataserver import interfaces as nti_interfaces
from nti.dataserver.users import interfaces as user_interfaces

from . import interfaces as pio_interfaces

@interface.implementer(pio_interfaces.IProperties)
@component.adapter(interface.Interface)
def _GenericPropertyAdpater(item):
	return {}

@interface.implementer(pio_interfaces.IProperties)
@component.adapter(nti_interfaces.IUser)
def _UserPropertyAdpater(user):
	profile = user_interfaces.IFriendlyNamed(user)
	result = {'name':profile.realname, 'alias':profile.alias}
	return result

@interface.implementer(pio_interfaces.IProperties)
@component.adapter(nti_interfaces.INote)
def _NotePropertyAdpater(note):
	result = {'title':note.title}
	return result

@interface.implementer(pio_interfaces.ITypes)
@component.adapter(interface.Interface)
def _GenericTypesAdpater(item):
	return ()

@interface.implementer(pio_interfaces.ITypes)
@component.adapter(nti_interfaces.INote)
def _NoteTypesAdpater(item):
	tags = tuple((t.lower() for  t in item.tags))
	autotags = tuple((t.lower() for t in getattr(item, 'AutoTags', None) or ()))
	result = ('note',) + tags + autotags
	return result
