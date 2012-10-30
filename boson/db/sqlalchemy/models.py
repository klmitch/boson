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

import sqlalchemy as sa
from sqlalchemy.exc import declarative as sa_dec
from sqlalchemy import orm
from sqlalchemy import types as sa_types

from boson.openstack.common import timeutils
from boson import utils


BASE = sa_dec.declarative_base()


class DictSerialized(sa_types.TypeDecorator):
    """
    Special SQLAlchemy type to support serializing dictionaries into
    and out of the special serialization format implemented by
    boson.utils.dict_{,de}serialize().  This serialization format is a
    repeatable format (dictionary keys are ordered), which makes it
    possible to search for table rows matching a desired dictionary.
    """

    impl = sa.Text

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


class PickledString(sa_types.TypeDecorator):
    """
    Special SQLAlchemy type to support serializing Python objects into
    and out of the database, using the cPickle module.  This enables
    field sets to be stored in the database as sets, etc.
    """

    impl = sa.Text

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
    created_at = sa.Column(sa.DateTime, default=timeutils.utcnow)
    updated_at = sa.Column(sa.DateTime, onupdate=timeutils.utcnow)
    id = sa.Column(sa.String(36), primary_key=True,
                   default=utils.generate_uuid)


class Service(BASE, ModelBase):
    """Represents a declared service."""

    __tablename__ = 'services'

    name = sa.Column(sa.String(64), nullable=False)
    auth_fields = sa.Column(PickledString)


class Category(BASE, ModelBase):
    """Represents a category of quotas for a given service."""

    __tablename__ = 'categories'

    service_id = sa.Column(sa.String(36), sa.ForeignKey('services.id'),
                           nullable=False)
    name = sa.Column(sa.String(64), nullable=False)
    usage_fset = sa.Column(PickledString)
    quota_fsets = sa.Column(PickledString)

    service = orm.relationship(Service, backref=orm.backref('categories'))


class Resource(BASE, ModelBase):
    """Represents an abstract resource for a given service."""

    __tablename__ = 'resources'

    service_id = sa.Column(sa.String(36), sa.ForeignKey('services.id'),
                           nullable=False)
    category_id = sa.Column(sa.String(36), sa.ForeignKey('categories.id'),
                            nullable=False)
    name = sa.Column(sa.String(64), nullable=False)
    parameters = sa.Column(PickledString)
    absolute = sa.Column(sa.Boolean, nullable=False)

    service = orm.relationship(Service, backref=orm.backref('resources'))
    category = orm.relationship(Category, backref=orm.backref('resources'))


class Usage(BASE, ModelBase):
    """Represents a resource usage."""

    __tablename__ = 'usages'

    resource_id = sa.Column(sa.String(36), sa.ForeignKey('resources.id'),
                         nullable=False)
    parameter_data = sa.Column(DictSerialized)
    auth_data = sa.Column(DictSerialized)
    used = sa.Column(sa.BigInteger, nullable=False)
    reserved = sa.Column(sa.BigInteger, nullable=False)
    until_refresh = sa.Column(sa.Integer)
    refresh_id = sa.Column(sa.String(36))

    resource = orm.relationship(Resource, backref=orm.backref('usages'))


class Quota(BASE, ModelBase):
    """Represents a quota."""

    __tablename__ = 'quotas'

    resource_id = sa.Column(sa.String(36), sa.ForeignKey('resources.id'),
                            nullable=False)
    auth_data = sa.Column(DictSerialized)
    limit = sa.Column(sa.BigInteger)

    resource = orm.relationship(Resource, backref=orm.backref('quotas'))


class Reservation(BASE, ModelBase):
    """Represents a reservation of a selection of resources."""

    __tablename__ = 'reservations'

    expire = sa.Column(sa.DateTime, nullable=False)


class ReservedItem(BASE, ModelBase):
    """Represents a reservation of a single resource."""

    __tablename__ = 'reserved_items'

    reservation_id = sa.Column(sa.String(36), sa.ForeignKey('reservations.id'),
                               nullable=False)
    resource_id = sa.Column(sa.String(36), sa.ForeignKey('resources.id'),
                            nullable=False)
    usage_id = sa.Column(sa.String(36), sa.ForeignKey('usages.id'),
                         nullable=False)
    delta = sa.Column(sa.BigInteger, nullable=False)

    reservation = orm.relationship(Reservation,
                                   backref=orm.backref('reserved_items'))
    resource = orm.relationship(Resource,
                                backref=orm.backref('reserved_items'))
    usage = orm.relationship(Usage, backref=orm.backref('reserved_items'))
