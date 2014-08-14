#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

# disable: accessing protected members, too many methods
# pylint: disable=W0212,R0904

import uuid

from zope import component
from zope.component.hooks import setHooks

from nti.dataserver import interfaces as nti_interfaces

from nti.hypatia import interfaces as hypatia_interfaces
from nti.hypatia.adapters import _HypatiaUserIndexController

from nti.dataserver.tests.mock_dataserver import WithMockDS
from nti.dataserver.tests.mock_dataserver import mock_db_trans

from nti.app.testing.application_webtest import ApplicationTestLayer

from nti.testing.layers import find_test
from nti.testing.layers import GCLayerMixin
from nti.testing.layers import ZopeComponentLayer
from nti.testing.layers import ConfiguringLayerMixin

from nti.dataserver.tests.mock_dataserver import DSInjectorMixin

import zope.testing.cleanup

zanpakuto_commands = (
    "Shoot To Kill",
    "Bloom, Split and Deviate",
    "Rankle the Seas and the Skies",
    "Lightning Flash Flame Shell",
    "Flower Wind Rage and Flower God Roar, Heavenly Wind Rage and Heavenly Demon Sneer",
    "All Waves, Rise now and Become my Shield, Lightning, Strike now and Become my Blade",
    "Cry, Raise Your Head, Rain Without end",
    "Sting All Enemies To Death",
    "Reduce All Creation to Ash",
    "Sit Upon the Frozen Heavens",
    "Call forth the Twilight",
    "Multiplication and subtraction of fire and ice, show your might")

def register():
    try:
        # temp hack to register adapter while the zcml condition zopyx_index is
        # deprecated
        component.provideAdapter(_HypatiaUserIndexController, (nti_interfaces.IUser,),
                                 hypatia_interfaces.IHypatiaUserIndexController)
    except:
        pass

class SharedConfiguringTestLayer(ZopeComponentLayer,
                                 GCLayerMixin,
                                 ConfiguringLayerMixin,
                                 DSInjectorMixin):

    set_up_packages = ('nti.dataserver', 'nti.hypatia', 'nti.contentsearch')

    @classmethod
    def setUp(cls):
        cls.setUpPackages()
        setHooks()
        register()

    @classmethod
    def tearDown(cls):
        cls.tearDownPackages()
        zope.testing.cleanup.cleanUp()

    @classmethod
    def testSetUp(cls, test=None):
        cls.setUpTestDS(test)
        setHooks()
        
    @classmethod
    def testTearDown(cls):
        pass

class HypatiaApplicationTestLayer(ApplicationTestLayer):

    @classmethod
    def setUp(cls):
        register()
        setHooks()

    @classmethod
    def tearDown(cls):
        pass
