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

import sys

import metatools

from boson.openstack.common.gettextutils import _


def _get_klass(klass):
    """
    Helper function to convert a class name (needed due to forward
    references) to an actual class.
    """

    return getattr(sys.modules[__name__], klass)


class BaseRef(object):
    """
    Base class for references.  References are fields in the model
    classes that correspond to instances of other model classes.  The
    BaseRef subclasses control how to obtain those instances from the
    database API.
    """

    def __init__(self, field, klass):
        """
        Initialize a reference.

        :param field: The name of the field.
        :param klass: The name of the model class.  Note that this is
                      the name, not the class itself; this is to allow
                      for references to model classes that have not
                      yet been declared.
        """

        self.field = field
        self._klass_name = klass
        self._klass = None

    @property
    def klass(self):
        """
        Retrieve the model class.  This is a property to allow for
        references to model classes that were not declared at the time
        the BaseRef was instantiated.
        """

        if self._klass is None:
            self._klass = _get_klass(self._klass_name)
        return self._klass


class Ref(BaseRef):
    """
    A reference to a single instance of another model class.  It is
    assumed that the ID of that instance is given by the field name
    with '_id' appended.
    """

    def __init__(self, field, klass):
        """
        Initialize a reference.

        :param field: The name of the field.
        :param klass: The name of the model class.  Note that this is
                      the name, not the class itself; this is to allow
                      for references to model classes that have not
                      yet been declared.
        """

        super(Ref, self).__init__(field, klass)

        self.base_field = '%s_id' % field

    def __call__(self, model):
        """
        Retrieve an instance of the appropriate model class for this
        reference.

        :param model: The instance of the model class.
        """

        return model._dbapi._lazy_get(model._context, model._base_obj,
                                      self.base_field, model._hints,
                                      self.klass)


class ListRef(BaseRef):
    """
    A reference to a list of instances of another model class.
    """

    def __call__(self, model):
        """
        Retrieve a list of instances of the appropriate model class
        for this reference.

        :param model: The instance of the model class.
        """

        return model._dbapi._lazy_get_list(model._context, model._base_obj,
                                           self.field, model._hints,
                                           self.klass)


class BaseModelMeta(metatools.MetaClass):
    """
    Metaclass for class BaseModel.  Uses the metatools package to
    allow for inheritance of field names, and translates lists of
    references into the dictionary needed by BaseModel.__getattr__().
    """

    def __new__(mcs, name, bases, namespace):
        """
        Create a new BaseModel subclass.
        """

        # Set up _refs as a dictionary
        decl_refs = namespace.get('_refs', [])
        refs = {}
        for ref in decl_refs:
            refs[ref.field] = ref

        # Update the namespace appropriately
        namespace['_refs'] = refs
        namespace.setdefault('_fields', set())

        # Inherit _fields and _refs
        for base in mcs.iter_bases(bases):
            mcs.inherit_set(base, namespace, '_fields')
            mcs.inherit_dict(base, namespace, '_refs')

        return super(BaseModelMeta, mcs).__new__(mcs, name, bases, namespace)


class BaseModel(object):
    """
    Base class for all model classes.

    All model classes should have _fields and _refs class attributes.
    The _fields class attribute should be a set, the members of which
    are the names of the simple fields.  The _refs class attribute
    should be a list of Ref() or ListRef() instances.

    Note that, once constructed, the _refs class attribute of the
    newly created class will actually be a dictionary.  Also note that
    both _fields and _refs are subject to inheritance behavior; that
    is, BaseModel declares the 'created_at' and 'updated_at' fields,
    which will automatically be declared for all subclasses.
    """

    __metaclass__ = BaseModelMeta

    _fields = set(['created_at', 'updated_at', 'id'])
    _refs = []

    def __init__(self, context, dbapi, base_obj, hints=None):
        """
        Initialize a Model object.

        :param context: The current context for accessing the
                        database.
        :param dbapi: A handle for the underlying database API.
        :param base_obj: The object returned from the underlying
                         database API.  It is assumed that all
                         declared fields (listed in the _fields class
                         attribute) will be accessible as attributes
                         of this object.
        :param hints: An object constructed by the underlying database
                      API that can be used by that API to remember
                      information about what database objects have
                      been eager-loaded.  This is used when resolving
                      references.
        """

        self._context = context
        self._dbapi = dbapi
        self._base_obj = base_obj
        self._values = dict((fld, getattr(base_obj, fld))
                            for fld in self._fields)
        self._cache = {}
        self._hints = hints

    def __getitem__(self, name):
        """
        Retrieve the value of a given field (item syntax).
        """

        # For simple values, return the value
        if name in self._fields:
            return self._values[name]

        # For reference values, return the referenced object
        elif name in self._refs:
            if name not in self._cache:
                self._cache[name] = self._refs[name](self)
            return self._cache[name]

        # OK, don't know that name
        raise KeyError(name)

    def __getattr__(self, name):
        """
        Retrieve the value of a given field (attribute syntax).
        """

        try:
            return self.__getitem__(name)
        except KeyError:
            # OK, don't know that attribute
            raise AttributeError(_('cannot get %r attribute') % name)

    def __setitem__(self, name, value):
        """
        Set the value of a given field.
        """

        # For simple values, update the value in the base object and
        # call the dbapi to save it
        if name in self._fields:
            setattr(self._base_obj, name, value)
            self._dbapi._save(self._context, self._base_obj)
            self._values[name] = value

            # If there's a corresponding reference, invalidate the
            # corresponding cache entry
            if name[-3:] == '_id':
                self._cache.pop(name[:-3], None)

            return

        # For reference values, update the corresponding field in the
        # base object and call the dbapi to save it
        elif name in self._refs:
            ref = self._refs[name]

            # If it's a simple reference, update it
            if isinstance(ref, Ref):
                setattr(self._base_obj, ref.base_field, value.id)
                self._dbapi._save(self._context, self._base_obj)
                self._values[ref.base_field] = value.id
                self._cache[name] = value
                return

        # Can't set that field
        raise KeyError(name)

    def __setattr__(self, name, value):
        """
        Set the value of a given field.
        """

        # Delegate internal attributes to regular setting
        if name[0] == '_':
            return super(BaseModel, self).__setattr__(name, value)

        try:
            return self.__setitem__(name, value)
        except KeyError:
            # Don't know that attribute
            raise AttributeError(_('cannot set %r attribute') % name)

    def __delitem__(self, name):
        """
        Prohibit deletion of fields.
        """

        raise KeyError(name)

    def __delattr__(self, name):
        """
        Prohibit deletion of fields.
        """

        raise AttributeError(_('cannot delete %r attribute') % name)

    def update(self, **kwargs):
        """
        Update multiple fields simultaneously.  Specify field values
        as keyword arguments.  If a field is unknown or unsettable
        (e.g., a reference field returning a list), a KeyError will be
        raised, and no other changes will be applied.
        """

        values = {}
        cache = {}
        invalidate = set()

        for name, value in kwargs.items():
            # For simple values, save an update for the value
            if name in self._fields:
                # Make sure we didn't have a duplicate
                if name in values:
                    raise AmbiguousFieldUpdate(field=name)

                # Save the value we're going to set
                values[name] = value

                # Mark the cache for invalidation
                if name[-3:] == '_id':
                    invalidate.add(name[:-3])

                continue

            # For reference values, sanity-check the value and save an
            # update for it
            elif name in self._refs:
                ref = self._refs[name]

                # If it's a simple reference, we can handle it
                if isinstance(ref, Ref):
                    # Make sure we didn't have a duplicate
                    if ref.base_field in values:
                        raise AmbiguousFieldUpdate(field=ref.base_field)

                    # Save the value we're going to set
                    values[name] = value.id  # sanity-checks the value, too

                    # Mark the cache for update
                    cache[name] = value

                    continue

            # Couldn't handle that field; raise a KeyError
            raise KeyError(name)

        # We have now validated the whole change request; install the
        # changes to the base object...
        for key, value in values.items():
            setattr(self._base_obj, key, value)

        # Save it...
        self._dbapi._save(self._context, self._base_obj)

        # Install the changes to the values and the cache
        self._values.update(values)
        self._cache.update(cache)

        # Handle cache invalidations
        for name in invalidate:
            self._cache.pop(name, None)

    def delete(self):
        """
        Delete the model object from the database.  Note that this may
        fail if other records refer to this object.
        """

        # Just call the dbapi delete method
        self._dbapi._delete(self._context, self._base_obj)


class Service(BaseModel):
    """
    Represent a single service.

    Available Fields
    ----------------

    *id*
        The ID of the service (UUID).

    *name*
        The name of the service.

    *auth_fields*
        A set of authentication fields that the service will provide
        when making reservations on behalf of a given user.

    *categories*
        A list of Category objects representing the recognized
        resource categories.

    *resources*
        A list of Resource objects representing the recognized
        resources.
    """

    _fields = set(['name', 'auth_fields'])
    _refs = [
        ListRef('categories', 'Category'),
        ListRef('resources', 'Resource')
    ]


class Category(BaseModel):
    """
    Represent a category of resources.  Each resource is in a single
    category.  Categories include rules for determining the
    corresponding usage record and for locating the most specific
    applicable quota for a given user.

    Available Fields
    ----------------

    *id*
        The ID of the category (UUID).

    *service_id*
        The ID of the service the category is associated with.

    *service*
        The Service object corresponding to *service_id*.

    *name*
        The name of the category.

    *usage_fset*
        A set of authentication data field names, used for looking up
        the appropriate usage record for a given resource.

    *quota_fsets*
        A list containing sets of authentication data field names.
        These sets are used for looking up the appropriate quota
        record for a given resource, and are ordered from most
        specific to least specific.  The list will always contain an
        empty set, for looking up a default quota value.

    *resources*
        A list of Resource objects representing the associated
        resources.
    """

    _fields = set(['service_id', 'name', 'usage_fset', 'quota_fsets'])
    _refs = [
        Ref('service', 'Service'),
        ListRef('resources', 'Resource'),
    ]


class Resource(BaseModel):
    """
    Represent a resource.

    Available Fields
    ----------------

    *id*
        The ID of the resource (UUID).

    *service_id*
        The ID of the service the resource is associated with.

    *service*
        The Service object corresponding to *service_id*.

    *category_id*
        The ID of the category the resource is associated with.

    *category*
        The Category object corresponding to *category_id*.

    *name*
        The name of the resource.

    *parameters*
        A set of resource parameter data field names, used for looking
        up the appropriate usage record for a given resource.  This
        can be used to allow for limits on the number of one resource
        contained within another resource.  (Note: it is not possible
        to set different limits based on the container.)

    *absolute*
        A boolean, set to ``True`` if the resource is an absolute
        resource.  Absolute resources do not have a usage record and
        cannot be reserved; they serve as simple numerical
        comparisons, and are intended to allow for limiting ephemeral
        resources, such as the number of files that can be injected
        into an instance.

    *usages*
        A list of Usage objects representing the current usage of this
        resource.

    *quotas*
        A list of Quota objects representing the configured limits on
        the use of this resource.

    *reserved_items*
        A list of ReservedItem objects representing the currently
        reserved items of this resource.
    """

    _fields = set(['service_id', 'category_id', 'name', 'parameters',
                   'absolute'])
    _refs = [
        Ref('service', 'Service'),
        Ref('category', 'Category'),
        ListRef('usages', 'Usage'),
        ListRef('quotas', 'Quota'),
        ListRef('reserved_items', 'ReservedItem'),
    ]


class Usage(BaseModel):
    """
    Represent a resource usage.  Binds a specific resource and a user
    with the current usage by the user of that resource.  The usage
    will include positive reservations.  (Negative reservations are
    not included, to prevent quota overages resulting from failed
    resource deallocations.)

    Available Fields
    ----------------

    *id*
        The ID of the usage (UUID).

    *resource_id*
        The ID of the resource the usage is associated with.

    *resource*
        The Resource object corresponding to *resource_id*.

    *parameter_data*
        A dictionary of resource parameter data, used for looking up
        the appropriate usage record for a given resource.  See the
        description of the *parameters* field for the Resource object.

    *auth_data*
        A dictionary of authentication data, used for looking up the
        appropriate usage record for a given resource category.  See
        the description of the *usage_fset* field for the Category
        object.

    *used*
        The amount of this resource that is currently in use.

    *reserved*
        The amount of this resource that is currently reserved.

    *until_refresh*
        Used to track when the usage must be refreshed from the
        service data.

    *refresh_id*
        A UUID corresponding to the refresh request issued by Boson to
        the service.  This is used to ensure that a usage record is
        only refreshed once, and also to mark a usage record as
        currently being refreshed.

    *reserved_items*
        A list of ReservedItem objects representing the currently
        reserved items counted by this usage.  (Note that reserved
        items with negative deltas will not be reflected in the
        *reserved* field, to prevent quota overages resulting from
        failed resource deallocations.)
    """

    _fields = set(['resource_id', 'parameter_data', 'auth_data', 'used',
                   'reserved', 'until_refresh', 'refresh_id'])
    _refs = [
        Ref('resource', 'Resource'),
        ListRef('reserved_items', 'ReservedItem'),
    ]


class Quota(BaseModel):
    """
    Represent a quota.  Binds a resource and a user with the limit on
    the user's use of that resource.

    Available Fields
    ----------------

    *id*
        The ID of the quota (UUID).

    *resource_id*
        The ID of the resource the quota is associated with.

    *resource*
        The Resource object corresponding to *resource_id*.

    *auth_data*
        A dictionary of authentication data, used for looking up the
        appropriate quota record for a given resource category.  See
        the description of the *quota_fsets* field for the Category
        object.

    *limit*
        The quota limit on allocations of the associated resource.
    """

    _fields = set(['resource_id', 'auth_data', 'limit'])
    _refs = [Ref('resource', 'Resource')]


class Reservation(BaseModel):
    """
    Represent a reservation and its expiration time.  Note
    reservations of multiple resources may be tracked under a single
    reservation record; see the ReservedItem model class.

    Available Fields
    ----------------

    *id*
        The ID of the reservation (UUID).

    *expire*
        The time at which the reservation will be expired.  This is
        used to ensure that service errors do not leave reserved items
        around indefinitely.

    *reserved_items*
        A list of ReservedItem objects representing the actual
        resource reservations.
    """

    _fields = set(['expire'])
    _refs = [ListRef('reserved_items', 'ReservedItem')]


class ReservedItem(BaseModel):
    """
    Represent a single resource reservation.  Links to the applicable
    usage record, to facilitate processing reservation commits and
    rollbacks.  (Note only positive resource reservations are included
    in the usage record, to prevent quota overages resulting from
    failed resource deallocations.)

    Available Fields
    ----------------

    *id*
        The ID of the item reservation (UUID).

    *reservation_id*
        The ID of the reservation the reserved item is associated
        with.

    *reservation*
        The Reservation object corresponding to *reservation_id*.

    *resource_id*
        The ID of the resource the reserved item is associated with.

    *resource*
        The Resource object corresponding to *resource_id*.

    *usage_id*
        The ID of the usage the reserved item is associated with.

    *usage*
        The Usage object corresponding to *usage_id*.

    *delta*
        The delta of the reservation.  May be negative to represent
        resource deallocation.
    """

    _fields = set(['reservation_id', 'resource_id', 'usage_id', 'delta'])
    _refs = [
        Ref('reservation', 'Reservation'),
        Ref('resource', 'Resource'),
        Ref('usage', 'Usage'),
    ]
