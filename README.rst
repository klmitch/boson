===============================
Boson Distributed Quota Manager
===============================

Introduction
============

This page provides an initial proposal for the Boson distributed quota
manager, for use with Nova and other OpenStack projects (although it
should also be general enough for use with any other project). It is
necessary primarily because Nova can potentially be deployed in a
multi-cell manner, but quotas should be enforced across the entire
deployment rather than per cell. Its generality means that it can also
be used to track quotas for other projects (e.g., Glance, Quantum,
etc.). If Boson is used for tracking quotas in multiple projects in
this manner, that in turn means that it becomes a single point of
contact for users to evaluate their current quotas and usages, as well
as for administrators to manage quotas.

Boson Description
=================

Boson is defined as a REST API, accessible via HTTP rather than
RPC. This means that it can be used by any project without having to
pull in Nova's RPC mechanism. This also means that users can access it
directly, to inquire as to their current usages. On the down side, it
means that Boson must apply authorization checks to ensure that users
cannot modify their own quotas while administrators can.

Boson tracks quotas and usages for services. Each service being
tracked may potentially provide different authentication information
for checking quotas; for instance, Nova may provide a user's quota
class, while no other service currently uses this information. (In
fact, Nova does not currently originate quota class data; it instead
assumes that the authentication middleware will set the quota class if
one is available. It should be noted, however, that there are efforts
underway to incorporate quota classes directly into Nova.) Each
service is named with a simple string, which will form part of the
URI.

For each service, a set of *resources* is registered. Resources are
named using hierarchical simple strings, which will form another part
of the URI for accessing Boson. For each resource, a set of required
parameters are declared, for differentiating usages per resource. (To
further explain resource parameters, consider Nova's *security group
rules*: there is a quota for how many security group rules may be
associated with a given *security group*, but a given user may have
more than one security group. The resource parameters are used to
indicate that a usage or reservation is associated with a given
security group.) Resources can be described as *abstract* or
*concrete*, based on these parameters: if all required parameters are
provided, then the resource is concrete, but if one or more required
parameters are not provided, then the resource is abstract.

Quota Tracking
==============

There are three basic objects that are tracked to provide quota
enforcement; they are:

**Quotas**
    Bind an abstract resource with a numerical limit on the usage of
    that resource. To provide support for default quotas, per-class
    quotas, per-tenant quotas, etc., the Quota object may also have
    one piece of authentication data. The registration of the service
    will indicate quota priorities based on the authentication data,
    so that, e.g., a default quota is overridden by a per-class quota,
    which in turn is overridden by a per-tenant quota. None of the
    resource parameters are relevant for a quota, as a Quota object
    merely binds a limit with a resource.

**Usages**
    Bind a concrete resource (a resource with all required parameters)
    with the current in-use count of that resource. (For purposes of
    synchronization, different instances of the services will have
    their usage tracked individually, but for the purposes of quota
    enforcement and reporting, only the aggregate usage is reported.)
    The Usage object also keeps track of resources that are reserved;
    the sum of the in-use count and the current reservation count are
    used when evaluating new reservations.

**Reservations**
    Bind a concrete resource (a resource with all required parameters)
    with a delta. Reservations are key to the quota management and
    enforcement infrastructure; quotas are checked by requesting
    reservations, and successfully created reservations are then later
    either committed or rolled back. The delta of a Reservation object
    is either positive or negative. Reservation objects additionally
    have two ID fields, one being optional and provided by the caller,
    and the other being generated and returned by Boson. (Origination
    data is also stored with the Reservation, to ensure that
    Reservations can only be committed or rolled back by the proper
    caller.) Certain reservations can also be committed immediately
    upon being approved; this would typically be used when
    decrementing a resource, for instance, when destroying a Nova
    instance.

Dynamic Operation
=================

Boson should provide a dynamic quota management system. To achieve
this, certain idempotent operations are defined, such as defining
services and resources (and default quotas for those resources). By
defining these operations as part of the REST API, we enable new
services to be tracked by Boson with minimal work required by the
administrator. By defining these operations to be idempotent, we can
allow the services to register themselves each time they start up,
which also affords the opportunity to automatically register new
resources that have been added to the code base for a given
service. (We can even track the last time we saw a given resource
declared, which will make it easier to identify deprecated resources
and purge them from Boson's database later on.)

Data Storage
============

Boson requires two primary things from its data storage backend:
atomicity and document storage/retrieval. The atomicity requirement is
simple to understand: by allowing data to be manipulated in an atomic
manner, we allow the administrator to stand up multiple instances of
Boson for HA configuration. (This requirement extends to atomic update
of multiple database objects.) The document storage/retrieval
requirement is more difficult to explain. Because concrete resources
can have associated parameters, Boson needs the ability to remember
both the key and the value of those parameters in the Usage and
Reservation objects. It is also necessary to be able to search for a
given Usage or Reservation based on some or all of the key/value
pairs, so that usage information may be obtained and easily displayed
to the user. This latter requirement may indicate that a NoSQL
solution is the best for Boson's backend.

Usage Synchronization
=====================

Boson depends on having access to the current utilization of a given
resource. There are a couple of ways of getting this information into
Boson. The simplest is to simply have the services regularly send the
updated usage information to Boson, but that might be prohibitively
expensive for the services. Instead, Boson will keep freshness
information on the usage data; should it determine that the usage
information it has is not fresh enough, it will reject reservation
creation requests with a special response code, which tells the
service to send fresh usage information for certain resources along
with resending the reservation creation requests. (This can be
supported by a client library, to make this extra round trip invisible
to the service.) This will amortize the cost of keeping the usage
information fresh across all reservation requests.

"Absolute" Quotas
=================

Some quotas are much simpler than Boson is designed to accommodate. As
an example, consider Nova, which has a quota for the number of
injected files allowed when creating a new instance. There is no usage
information that should be tracked by Boson; the limit applies to each
instance only at its creation time. To accommodate this, resources
will consist of two different types: absolute resources and reservable
resources, with the example limit of the number of injected files
being an absolute resource. Only reservable resources can have
reservations, but the reservation creation interface will provide
support for either checking an absolute number against the quota of a
resource, or for returning the limit to the caller, for its own
processing.

What's in a Name?
=================

A "boatswain" is a petty officer on a merchant ship who controls the
work of other seamen. One could envision such a crew member also being
responsible for rationing scarce resources, such as food or
water. Alternate spellings of "boatswain" are "bosun" and "boson"; the
latter was chosen because the author is inherently a physics geek (as
evidenced by the third-person reference!).
