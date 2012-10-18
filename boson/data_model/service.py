# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012 OpenStack LLC.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from boson.openstack.common.gettextutils import _


class Category(object):
    """
    Represent a category of quotas; that is, for a given resource,
    there may be quota limits imposed on a per-user basis and a
    per-tenant basis.
    """

    def __init__(self, service, name, usage_fields, quota_fieldsets):
        """
        Initialize a Category.

        :param service: The Service object.
        :param name: A descriptive name of the category.
        :param usage_fields: A list of the field names of
                             authentication and authorization data
                             that will be used for looking up an
                             applicable usage.
        :param quota_fieldsets: A list containing, in order from most
                                specific to least specific, lists of
                                field names of authentication and
                                authorization data that will be used
                                for looking up an applicable quota.
        """

        self.service = service
        self.name = name
        self.usage_fields = set(fld for fld in usage_fields
                                if fld in service.auth_fields)
        self.quota_fieldsets = [set(fld for fld in fieldset
                                    if fld in service.auth_fields)
                                for fieldset in quota_fieldsets]


class Service(object):
    """
    Represent a single service.
    """

    def __init__(self, name, auth_fields):
        """
        Initialize a Service.

        :param name: The name of the service, as a string; e.g.,
                     "nova", "glance", etc.
        :param auth_fields: A list of the field names of
                            authentication and authorization data that
                            will be provided by the service.
        """

        self.name = name
        self.auth_fields = set(auth_fields)
        self.categories = {}

    def add_category(self, category):
        """
        Add a category to the service.
        """

        self.categories[category.name] = category


class ServiceUser(object):
    """
    Represent a user on the service.  Bundles together a service and
    the authentication and authorization data relevant to the user.
    """

    def __init__(self, service, auth_data):
        """
        Initialize a ServiceUser.

        :param service: The Service object.
        :param auth_data: The authentication and authorization data
                          relevant to the user.
        """

        self.service = service

        # Filter the authentication/authorization data
        self.auth_data = dict((k, v) for k, v in auth_data.items()
                              if k in service.auth_fields)

        # Make sure we got everything
        missing = service.auth_fields - set(self.auth_data.keys())
        if missing:
            raise ValueError(_("Missing auth data fields: %s") %
                             ', '.join(repr(f) for f in sorted(missing)))
