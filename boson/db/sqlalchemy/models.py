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

import cPickle

from sqlalchemy import BigInteger, Boolean, Column, DateTime
from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.exc.declarative import declarative_base
from sqlalchemy.orm import backref, relationship
from sqlalchemy.types import TypeDecorator

from boson.openstack.common import timeutils
from boson import utils


BASE = declarative_base()


class DictSerialized(TypeDecorator):
    """
    Special SQLAlchemy type to support serializing dictionaries into
    and out of the special serialization format implemented by
    boson.utils.dict_{,de}serialize().  This serialization format is a
    repeatable format (dictionary keys are ordered), which makes it
    possible to search for table rows matching a desired dictionary.
    """

    impl = Text

    def process_bind_param(self, value, dialect):
        """Marshal the value into its serialized format."""

        if value is not None:
            value = utils.dict_serialize(value)

        return value

    def process_result_value(self, value, dialect):
        """Marshal the value out of its serialized format."""

        if value is not None:
            value = utils.dict_deserializer(value)

        return value


class PickledString(TypeDecorator):
    """
    Special SQLAlchemy type to support serializing Python objects into
    and out of the database, using the cPickle module.  This enables
    field sets to be stored in the database as sets, etc.
    """

    impl = Text

    def process_bind_param(self, value, dialect):
        """Marshal the value into its serialized format."""

        if value is not None:
            value = cPickle.dumps(value)

        return value

    def process_result_value(self, value, dialect):
        """Marshal the value out of its serialized format."""

        if value is not None:
            value = cPickle.loads(value)

        return value


class ModelBase(object):
    """Base class for model classes."""

    __table_initialized__ = False
    created_at = Column(DateTime, default=timeutils.utcnow)
    updated_at = Column(DateTime, onupdate=timeutils.utcnow)
    id = Column(String(36), primary_key=True, default=utils.generate_uuid)


class Service(BASE, ModelBase):
    """Represents a declared service."""

    __tablename__ = 'services'

    name = Column(String(64), nullable=False)
    auth_fields = Column(PickledString)


class Category(BASE, ModelBase):
    """Represents a category of quotas for a given service."""

    __tablename__ = 'categories'

    service_id = Column(String(36), ForeignKey('services.id'),
                        nullable=False)
    name = Column(String(64), nullable=False)
    usage_fset = Column(PickledString)
    quota_fsets = Column(PickledString)

    service = relationship(Service, backref=backref('categories'))


class Resource(BASE, ModelBase):
    """Represents an abstract resource for a given service."""

    __tablename__ = 'resources'

    service_id = Column(String(36), ForeignKey('services.id'),
                        nullable=False)
    category_id = Column(String(36), ForeignKey('categories.id'),
                         nullable=False)
    name = Column(String(64), nullable=False)
    parameters = Column(PickledString)
    absolute = Column(Boolean, nullable=False)

    service = relationship(Service, backref=backref('resources'))
    category = relationship(Category, backref=backref('resources'))


class Usage(BASE, ModelBase):
    """Represents a resource usage."""

    __tablename__ = 'usages'

    resource_id = Column(String(36), ForeignKey('resources.id'),
                         nullable=False)
    parameter_data = Column(DictSerialized)
    auth_data = Column(DictSerialized)
    used = Column(BigInteger, nullable=False)
    reserved = Column(BigInteger, nullable=False)
    until_refresh = Column(Integer)
    refresh_id = Column(String(36))

    resource = relationship(Resource, backref=backref('usages'))


class Quota(BASE, ModelBase):
    """Represents a quota."""

    __tablename__ = 'quotas'

    resource_id = Column(String(36), ForeignKey('resources.id'),
                         nullable=False)
    auth_data = Column(DictSerialized)
    limit = Column(BigInteger)

    resource = relationship(Resource, backref=backref('quotas'))


class Reservation(BASE, ModelBase):
    """Represents a reservation of a selection of resources."""

    __tablename__ = 'reservations'

    expire = Column(DateTime, nullable=False)


class ReservedItem(BASE, ModelBase):
    """Represents a reservation of a single resource."""

    __tablename__ = 'reserved_items'

    reservation_id = Column(String(36), ForeignKey('reservations.id'),
                            nullable=False)
    resource_id = Column(String(36), ForeignKey('resources.id'),
                         nullable=False)
    usage_id = Column(String(36), ForeignKey('usages.id'),
                      nullable=False)
    delta = Column(BigInteger, nullable=False)

    reservation = relationship(Reservation, backref=backref('reserved_items'))
    resource = relationship(Resource, backref=backref('reserved_items'))
    usage = relationship(Usage, backref=backref('reserved_items'))
