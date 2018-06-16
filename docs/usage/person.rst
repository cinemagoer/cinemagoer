:orphan:

Persons
=======

It works mostly like the Movie class. :-)

The Movie class defines a ``__contains__()`` method, which is used to check
if a given person has worked in a given movie with the syntax:

.. code-block:: python

   if personObject in movieObject:
       print('%s worked in %s' % (personObject['name'], movieObject['title']))

The Person class defines a ``isSamePerson(otherPersonObject)`` method, which
can be used to compare two person objects. This can be used to check whether
an object has retrieved complete information or not, as in the case of a Person
object returned by a query:

.. code-block:: python

   if personObject.isSamePerson(otherPersonObject):
       print('they are the same person!')

A similar method is defined for the Movie class, and it's called
``isSameTitle(otherMovieObject)``.
