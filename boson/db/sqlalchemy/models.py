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

from sqlalchemy import Column, Integer, BigInteger, String
from sqlalchemy import ForeignKey, DateTime, Text
from sqlalchemy.exc.declarative import declarative_base
from sqlalchemy.orm import relationship, backref

from boson.openstack.common import timeutils
from boson import utils


BASE = declarative_base()


class ModelBase(object):
    __table_args__ = {'mysql_engine': 'InnoDB'}
    __table_initialized__ = False
    created_at = Column(DateTime, default=timeutils.utcnow)
    updated_at = Column(DateTime, onupdate=timeutils.utcnow)


class Service(BASE, ModelBase):
    """Represents a declared service."""

    __tablename__ = 'services'

    id = Column(String(36), primary_key=True, default=utils.generate_uuid)
    name = Column(String(64))
    auth_fields = Column(Text)


class Category(BASE, ModelBase):
    """Represents a category of quotas for a given service."""

    __tablename__ = 'categories'

    id = Column(String(36), primary_key=True, default=utils.generate_uuid)
    service_id = Column(String(36), ForeignKey('services.id'),
                        nullable=False)
    name = Column(String(64))
    usage_fset = Column(Text)
    quota_fsets = Column(Text)

    service = relationship(Service, backref=backref('categories'))


class Resource(BASE, ModelBase):
    """Represents an abstract resource for a given service."""

    __tablename__ = 'resources'

    id = Column(String(36), primary_key=True, default=utils.generate_uuid)
    service_id = Column(String(36), ForeignKey('services.id'),
                        nullable=False)
    category_id = Column(String(36), ForeignKey('categories.id'),
                         nullable=False)
    name = Column(String(64))
    parameters = Column(Text)

    service = relationship(Service, backref=backref('resources'))
    category = relationship(Category, backref=backref('resources'))


class Usage(BASE, ModelBase):
    """Represents a resource usage."""

    __tablename__ = 'usages'

    id = Column(String(36), primary_key=True, default=utils.generate_uuid)
    resource_id = Column(String(36), ForeignKey('resources.id'),
                         nullable=False)
    parameter_data = Column(Text)
    auth_data = Column(Text)
    used = Column(BigInteger)
    reserved = Column(BigInteger)
    until_refresh = Column(Integer)

    resource = relationship(Resource, backref=backref('usages'))


class Quota(BASE, ModelBase):
    """Represents a quota."""

    __tablename__ = 'quotas'

    id = Column(String(36), primary_key=True, default=utils.generate_uuid)
    resource_id = Column(String(36), ForeignKey('resources.id'),
                         nullable=False)
    auth_data = Column(Text)
    limit = Column(BigInteger)

    resource = relationship(Resource, backref=backref('quotas'))


class Reservation(BASE, ModelBase):
    """Represents a reservation of a selection of resources."""

    __tablename__ = 'reservations'

    id = Column(String(36), primary_key=True, default=utils.generate_uuid)
    expire = Column(DateTime, nullable=False)


class ReservedItem(BASE, ModelBase):
    """Represents a reservation of a single resource."""

    __tablename__ = 'reserved_items'

    id = Column(String(36), primary_key=True, default=utils.generate_uuid)
    reservation_id = Column(String(36), ForeignKey('reservations.id'),
                            nullable=False)
    resource_id = Column(String(36), ForeignKey('resources.id'),
                         nullable=False)
    usage_id = Column(String(36), ForeignKey('usages.id'),
                      nullable=False)
    delta = Column(BigInteger)

    reservation = relationship(Reservation, backref=backref('reserved_items'))
    resource = relationship(Resource, backref=backref('reserved_items'))
    usage = relationship(Usage, backref=backref('reserved_items'))
