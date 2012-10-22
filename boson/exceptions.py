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
from boson.openstack.common import log as logging


LOG = logging.getLogger(__name__)


class BosonException(Exception):
    """
    Base class for all Boson exceptions.
    """

    message = _("An unknown exception occurred")

    def __init__(self, **kwargs):
        """
        Initialize a BosonException.
        """

        try:
            msg = self.message % kwargs
        except Exception as exc:
            # Missing a field; use the raw message and log an
            # exception
            msg = self.message
            LOG.exception(_("Exception formatting exception message: "
                            "message %(msg)r, kwargs %(kwargs)r") % locals())

        super(BosonException, self).__init__(msg)


class AmbiguousFieldUpdate(BosonException):
    message = _("Ambiguous update of field %(field)r")
