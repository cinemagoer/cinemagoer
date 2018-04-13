:orphan:

Characters
==========

It works mostly like the Person class. :-)

For more information about the "currentRole" attribute, see the
README.currentRole file.


Character associated to a person who starred in a movie, and its notes:

.. code-block:: python

    person_in_cast = movie['cast'][0]
    notes = person_in_cast.notes
    character = person_in_cast.currentRole

Check whether a person worked in a given movie or not:

.. code-block:: python

    person in movie
    movie in person
