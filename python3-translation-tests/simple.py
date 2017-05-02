from imdb import IMDb
ia = IMDb()

# print the director(s) of a movie
the_matrix = ia.get_movie('0133093')
print(the_matrix['director'])

# search for a person
for person in ia.search_person('Mel Gibson'):
    print(person.personID, person['name'])

