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

import copy
import uuid

from boson.db import api as db_api
from boson.openstack.common.gettextutils import _
from boson.openstack.common import log as logging


LOG = logging.getLogger(__name__)


def generate_request_id():
    """Generate a unique request ID."""

    return 'req-' + str(uuid.uuid4())


class Context(object):
    """
    Security context and request information.

    Represents the user taking a given action within the system.
    """

    @classmethod
    def from_dict(cls, values):
        """Synthesize a Context object from a dictionary."""

        return cls(**values)

    def __init__(self, user, tenant, roles=None, request_id=None,
                 is_admin=None, **kwargs):
        """
        Initialize the context.

        :param user: The ID of the user making the request.
        :param tenant: The tenant ID of the user making the request.
        :param roles: A list of the roles for the user making the
                      request.
        :param request_id: The unique ID for the request.  This is
                           used solely for generating log messages, to
                           allow all phases of a request to be matched
                           up across multiple services.
        :param is_admin: A boolean flag indicating if the context
                         allows administrative access.  This allows
                         for temporary elevation in access privileges.

        All other keyword arguments are ignored
        """

        if kwargs:
            LOG.warning(_('Arguments dropped when creating context: %s') %
                        str(kwargs))

        self.user = user
        self.tenant = tenant
        self.roles = roles or []
        self.request_id = request_id or generate_request_id()
        if is_admin is None:
            is_admin = 'admin' in [r.lower() for r in self.roles]
        self.is_admin = is_admin
        self._session = None

    def to_dict(self):
        """Serialize the context to a dictionary."""

        return {
            'user': self.user,
            'tenant': self.tenant,
            'roles': self.roles,
            'request_id': self.request_id,
            'is_admin': self.is_admin,
        }

    def elevated(self):
        """Return a version of this context with admin privileges."""

        new_ctx = copy.copy(self)
        new_ctx.is_admin = True

        if 'admin' not in [r.lower() for r in new_ctx.roles]:
            new_ctx.roles.append('admin')

        return new_ctx

    @property
    def session(self):
        """Obtain a database API session object."""

        if self._session is None:
            self._session = db_api.get_session()
        return self._session


def get_admin_context():
    """Return a generic administrative context."""

    return Context(user=None,
                   tenant=None,
                   roles=['admin'],
                   is_admin=True)
