:orphan:

Movies
======

Below is a list of each main key, the type of its value, and a short
description or an example:

title (string)
  The "usual" title of the movie, like "The Untouchables".

long imdb title (string)
  "Uncommon Valor (1983/II) (TV)"

canonical title (string)
  The title in canonical format, like "Untouchables, The".

long imdb canonical title (string)
  "Patriot, The (2000)"

year (string)
  The release year, or '????' if unknown.

kind (string)
  One of: 'movie', 'tv series', 'tv mini series', 'video game', 'video movie',
  'tv movie', 'episode'

imdbIndex (string)
  The roman numeral for movies with the same title/year.

director (Person list)
  A list of directors' names, e.g.: ['Brian De Palma'].

cast (Person list)
  A list of actors/actresses, with the currentRole instance variable
  set to a Character object which describe his role.

cover url (string)
  The link to the image of the poster.

writer (Person list)
  A list of writers, e.g.: ['Oscar Fraley (novel)'].

plot (list)
  A list of plot summaries and their authors.

rating (string)
  User rating on IMDb from 1 to 10, e.g. '7.8'.

votes (string)
  Number of votes, e.g. '24,101'.

runtimes (string list)
  List of runtimes in minutes ['119'], or something like ['USA:118', 'UK:116'].

number of episodes (int)
  Number or episodes for a TV series.

color info (string list)
  ["Color (Technicolor)"]

countries (string list)
  Production's country, e.g. ['USA', 'Italy'].

genres (string list)
  One or more of: Action, Adventure, Adult, Animation, Comedy, Crime,
  Documentary, Drama, Family, Fantasy, Film-Noir, Horror, Musical, Mystery,
  Romance, Sci-Fi, Short, Thriller, War, Western, and other genres
  defined by IMDb.

akas (string list)
  List of alternative titles.

languages (string list)
  A list of languages.

certificates (string list)
  ['UK:15', 'USA:R']

mpaa (string)
  The MPAA rating.

episodes (series only) (dictionary of dictionaries)
  One key for every season, one key for every episode in the season.

number of episodes (series only) (int)
  Total number of episodes.

number of seasons (series only) (int)
  Total number of seasons.

series years (series only) (string)
  Range of years when the series was produced.

episode of (episodes only) (Movie object)
  The series to which the episode belongs.

season (episodes only) (int)
  The season number.

episode (episodes only) (int)
  The number of the episode in the season.

long imdb episode title (episodes only) (string)
  Episode and series title.

series title (string)
  The title of the series to which the episode belongs.

canonical series title (string)
  The canonical title of the series to which the episode belongs.


Other keys that contain a list of Person objects are: costume designer,
sound crew, crewmembers, editor, production manager, visual effects,
assistant director, art department, composer, art director, cinematographer,
make up, stunt performer, producer, set decorator, production designer.

Other keys that contain list of companies are: production companies, special
effects, sound mix, special effects companies, miscellaneous companies,
distributors.

Converting a title to its "Title, The" canonical format, IMDbPY makes
some assumptions about what is an article and what isn't, and this could
lead to some wrong canonical titles. For more information on this subject,
see the "ARTICLES IN TITLES" section of the README.locale file.
