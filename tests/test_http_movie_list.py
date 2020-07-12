listId = "ls058726648"

def test_list_movies_entries_should_have_rank(ia):
    movies = ia.get_movie_list(list_=listId)
    for rank, movie in enumerate(movies):
        assert movie['rank'] == rank + 1

def test_list_movies_entries_should_have_movie_id(ia):
    movies = ia.get_movie_list(list_=listId)
    for movie in movies:
        assert movie.movieID.isdigit()

def test_list_movies_entries_should_have_title(ia):
    movies = ia.get_movie_list(list_=listId)
    for movie in movies:
        assert 'title' in movie

def test_list_entries_should_be_movies(ia):
    movies = ia.get_movie_list(list_=listId)
    for movie in movies:
        assert movie['kind'] == 'movie'
