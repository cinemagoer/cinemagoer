/*
 * cutils.c module.
 *
 * Miscellaneous functions to speed up the IMDbPY package.
 *
 * Contents:
 * - pyratcliff():
 *   Function that implements the Ratcliff-Obershelp comparison
 *   amongst Python strings.
 *
 * - search_title(), search_name():
 *   Functions used to search for a movie title or a person name
 *   in titles or names ".key" files of an installation of the
 *   IMDb's plain text data files.
 *
 * - get_episodes():
 *   Given the movieID of a tv series, scans the titles.key file
 *   and returns a list of episode titles.
 *
 * - pysoundex():
 *   Return a soundex code string, for the given string.
 *
 * Copyright 2004-2008 Davide Alberani <da@erlug.linux.it>
 * Released under the GPL license.
 *
 * NOTE: The Ratcliff-Obershelp part was heavily based on code from the
 * "simil" Python module.
 * The "simil" module is copyright of Luca Montecchiani <cbm64 _at_ inwind.it>
 * and can be found here: http://spazioinwind.libero.it/montecchiani/
 * It was released under the GPL license; original comments are leaved
 * below.
 *
 */


/*========== Ratcliff-Obershelp ==========*/
/*****************************************************************************
 *
 * Stolen code from :
 *
 * [Python-Dev] Why is soundex marked obsolete?
 * by Eric S. Raymond [4]esr@thyrsus.com
 * on Sun, 14 Jan 2001 14:09:01 -0500
 *
 *****************************************************************************/

/*****************************************************************************
 *
 * Ratcliff-Obershelp common-subpattern similarity.
 *
 * This code first appeared in a letter to the editor in Doctor
 * Dobbs's Journal, 11/1988.  The original article on the algorithm,
 * "Pattern Matching by Gestalt" by John Ratcliff, had appeared in the
 * July 1988 issue (#181) but the algorithm was presented in assembly.
 * The main drawback of the Ratcliff-Obershelp algorithm is the cost
 * of the pairwise comparisons.  It is significantly more expensive
 * than stemming, Hamming distance, soundex, and the like.
 *
 * Running time quadratic in the data size, memory usage constant.
 *
 *****************************************************************************/

#include <Python.h>

#define DONTCOMPARE_NULL    0.0
#define DONTCOMPARE_SAME    1.0
#define COMPARE             2.0
#define STRING_MAXLENDIFFER 0.7

/* As of 05 Mar 2008, the longest title is ~600 chars. */
#define MXLINELEN   1023
#define FSEP        '|'

#define RO_THRESHOLD 0.6

#define MAX(a,b) ((a) > (b) ? (a) : (b))


/* List of articles.
   XXX: see comments about articles in the imdb.utils module. */
#define ART_COUNT    46
char *articles[ART_COUNT] = {"the ", "la ", "a ", "die ", "der ", "le ", "el ",
        "l'", "il ", "das ", "les ", "i ", "o ", "ein ", "un ", "de ", "los ",
        "an ", "una ", "las ", "eine ", "den ", "het ", "gli ", "lo ", "os ",
        "ang ", "oi ", "az ", "een ", "ha-", "det ", "ta ", "al-",
	"mga ", "un'", "uno ", "ett ", "dem ", "egy ", "els ", "eines ", "Ο ",
	"Η ", "Το ", "Οι "};

char *articlesNoSP[ART_COUNT] = {"the", "la", "a", "die", "der", "le", "el",
        "l'", "il", "das", "les", "i", "o", "ein", "un", "de", "los",
        "an", "una", "las", "eine", "den", "het", "gli", "lo", "os",
        "ang", "oi", "az", "een", "ha-", "det", "ta", "al-",
	"mga", "un'", "uno", "ett", "dem", "egy", "els", "eines", "Ο",
	"Η", "Το", "Οι"};


//*****************************************
// preliminary check....
//*****************************************
static float
strings_check(char const *s, char const *t)
{
    float threshold;    // lenght difference
    int s_len = strlen(s);    // length of s
    int t_len = strlen(t);    // length of t

    // NULL strings ?
    if ((t_len * s_len) == 0)
        return (DONTCOMPARE_NULL);

    // the same ?
    if (strcmp(s, t) == 0)
        return (DONTCOMPARE_SAME);

    // string lenght difference threshold
    // we don't want to compare too different lenght strings ;)
    if (s_len < t_len)
        threshold = (float) s_len / (float) t_len;
    else
        threshold = (float) t_len / (float) s_len;
    if (threshold < STRING_MAXLENDIFFER)
        return (DONTCOMPARE_NULL);

    // proceed
    return (COMPARE);
}


static int
RatcliffObershelp(char *st1, char *end1, char *st2, char *end2)
{
    register char *a1, *a2;
    char *b1, *b2;
    char *s1 = st1, *s2 = st2;    /* initializations are just to pacify GCC */
    short max, i;

    if (end1 <= st1 || end2 <= st2)
        return (0);
    if (end1 == st1 + 1 && end2 == st2 + 1)
        return (0);

    max = 0;
    b1 = end1;
    b2 = end2;

    for (a1 = st1; a1 < b1; a1++) {
        for (a2 = st2; a2 < b2; a2++) {
            if (*a1 == *a2) {
                /* determine length of common substring */
                for (i = 1; a1[i] && (a1[i] == a2[i]); i++)
                    continue;
                if (i > max) {
                    max = i;
                    s1 = a1;
                    s2 = a2;
                    b1 = end1 - max;
                    b2 = end2 - max;
                }
            }
        }
    }
    if (!max)
        return (0);
    max += RatcliffObershelp(s1 + max, end1, s2 + max, end2);    /* rhs */
    max += RatcliffObershelp(st1, s1, st2, s2);    /* lhs */
    return max;
}


static float
ratcliff(char *s1, char *s2)
/* compute Ratcliff-Obershelp similarity of two strings */
{
    int l1, l2;
    float res;

    // preliminary tests
    res = strings_check(s1, s2);
    if (res != COMPARE)
        return(res);

    l1 = strlen(s1);
    l2 = strlen(s2);

    return 2.0 * RatcliffObershelp(s1, s1 + l1, s2, s2 + l2) / (l1 + l2);
}


/* Change a string to lowercase. */
static void
strtolower(char *s1)
{
    int i;
    for (i=0; i < strlen(s1); i++) s1[i] = tolower(s1[i]);
}


/* Ratcliff-Obershelp for two python strings; returns a python float. */
static PyObject*
pyratcliff(PyObject *self, PyObject *pArgs)
{
    char *s1 = NULL;
    char *s2 = NULL;
    PyObject *discard = NULL;
    char s1copy[MXLINELEN+1];
    char s2copy[MXLINELEN+1];

    /* The optional PyObject parameter is here to be compatible
     * with the pure python implementation, which uses a
     * difflib.SequenceMatcher object. */
    if (!PyArg_ParseTuple(pArgs, "ss|O", &s1, &s2, &discard))
        return NULL;

    strncpy(s1copy, s1, MXLINELEN);
    strncpy(s2copy, s2, MXLINELEN);
    /* Work on copies. */
    strtolower(s1copy);
    strtolower(s2copy);

    return Py_BuildValue("f", ratcliff(s1copy, s2copy));
}


/*========== titles and names searches ==========*/
/* Search for the 'name1', 'name2' and 'name3' name variations
 * in the key file keyFileName, returning at most nrResults results.
 *
 * See also the documentation of the _search_person() method of the
 * parser.sql python module, and the _nameVariations() method of the
 * common.locsql module.
 */
static PyObject*
search_name(PyObject *self, PyObject *pArgs, PyObject *pKwds)
{
    char *keyFileName = NULL;
    char *name1 = NULL;
    char *name2 = NULL;
    char *name3 = NULL;
    float ratio;
    FILE *keyFile;
    char line[MXLINELEN+1];
    char origLine[MXLINELEN+1];
    char surname[MXLINELEN+1] = "";
    char namesurname[MXLINELEN+1] = "";
    char *cp;
    char *key;
    short hasNS = 0;
    unsigned int nrResults = 0;
    static char *argnames[] = {"keyFile", "name1", "name2", "name3",
                                "results", "_scan_character", NULL};
    PyObject *scanChar = NULL;
    int isChar = 0;
    PyObject *result = PyList_New(0);

    if (!PyArg_ParseTupleAndKeywords(pArgs, pKwds, "ss|ssiO",
                argnames, &keyFileName, &name1, &name2, &name3, &nrResults,
                &scanChar))
        return NULL;

    if (scanChar != NULL && PyObject_IsTrue(scanChar)) {
        isChar = 1;
    }

    if (strlen(name1) > MXLINELEN)
        return Py_BuildValue("O", result);
    strtolower(name1);

    if (name2 == NULL || strlen(name2) == 0)
        name2 = NULL;
    else
        strtolower(name2);

    if (name3 == NULL || strlen(name3) == 0)
        name3 = NULL;
    else
        strtolower(name3);

    if ((keyFile = fopen(keyFileName, "r")) == NULL) {
        PyErr_SetFromErrno(PyExc_IOError);
        return NULL;
    }

    while (fgets(line, MXLINELEN+1, keyFile) != NULL) {
        /* Split a "origLine|key" line. */
        if ((cp = strrchr(line, FSEP)) != NULL) {
            *cp = '\0';
            key = cp+1;
            strcpy(origLine, line);
        } else { continue; }
        /* Strip the optional imdbIndex.
         * XXX: check for [IVXLC]? */
        if ((cp = strrchr(line, '(')) != NULL)
            *(cp-1) = '\0';

        /* Build versions of this line with just the "surname" and in the
         * "name surname" format. */
        strtolower(line);
        strcpy(surname, line);
        hasNS = 0;
        if (!isChar) {
            if ((cp = strrchr(surname, ',')) != NULL && (cp+1)[0] == ' ') {
                *cp = '\0';
                hasNS = 1;
                strcpy(namesurname, cp+2);
                strcat(namesurname, " ");
                strcat(namesurname, surname);
            }
        } else {
            if ((cp = strrchr(surname, ' ')) != NULL) {
                    hasNS = 1;
                    strcpy(namesurname, surname);
                    strcpy(surname, cp+1);
                    strcat(surname, "\0");
            }
        }

        ratio = ratcliff(name1, line) + 0.05;

        if (hasNS) {
            ratio = MAX(ratio, ratcliff(name1, surname));
            if (!isChar) {
                ratio = MAX(ratio, ratcliff(name1, namesurname));
            }
            if (name2 != NULL) {
                ratio = MAX(ratio, ratcliff(name2, surname));
                if (strcmp(namesurname, "")) {
                    ratio = MAX(ratio, ratcliff(name2, namesurname));
                }
            }
        }

        if (name3 != NULL && strrchr(origLine, ')') != NULL) {
            char origLineLower[MXLINELEN+1];
            strcpy(origLineLower, origLine);
            strtolower(origLineLower);
            ratio = MAX(ratio, ratcliff(name3, origLineLower) + 0.1);
        }

        if (ratio >= RO_THRESHOLD)
            PyList_Append(result, Py_BuildValue("(dis)",
                            ratio, strtol(key, NULL, 16), origLine));
    }

    fclose(keyFile);

    PyObject_CallMethod(result, "sort", NULL);
    PyObject_CallMethod(result, "reverse", NULL);

    if (nrResults > 0)
        PySequence_DelSlice(result, nrResults, PySequence_Size(result));

    return Py_BuildValue("O", result);
}


/* Search for the 'title1', title2' and 'title3' title variations
 * in the key file keyFileName, returning at most nrResults results.
 *
 * See also the documentation of the _search_movie() method of the
 * parser.sql python module, and the _titleVariations() method of the
 * common.locsql module.
 */
static PyObject*
search_title(PyObject *self, PyObject *pArgs, PyObject *pKwds)
{
    char *keyFileName = NULL;
    char *title1 = NULL;
    char *title2 = NULL;
    char *title3 = NULL;
    float ratio;
    FILE *keyFile;
    char line[MXLINELEN+1];
    char origLine[MXLINELEN+1];
    char *cp;
    char *key;
    unsigned short hasArt = 0;
    unsigned short matchHasArt = 0;
    unsigned int nrResults = 0;
    unsigned short artlen = 0;
    unsigned short linelen = 0;
    unsigned short searchingEpisode = 0;
    unsigned int count = 0;
    char noArt[MXLINELEN+1] = "";
    static char *argnames[] = {"keyFile", "title1", "title2", "title3",
                                "results", NULL};
    PyObject *result = PyList_New(0);

    if (!PyArg_ParseTupleAndKeywords(pArgs, pKwds, "ss|ssi",
            argnames, &keyFileName, &title1, &title2, &title3, &nrResults))
        return NULL;

    if (strlen(title1) > MXLINELEN)
        return Py_BuildValue("O", result);

    strtolower(title1);
    if (title2 == NULL || strlen(title2) == 0)
        title2 = NULL;
    else
        strtolower(title2);

    if (title3 == NULL || strlen(title3) == 0) {
        title3 = NULL;
    } else {
        strtolower(title3);
        /* Is this a tv series episode? */
        if (title3[strlen(title3)-1] == '}')
            searchingEpisode = 1;
    }

    if ((keyFile = fopen(keyFileName, "r")) == NULL) {
        PyErr_SetFromErrno(PyExc_IOError);
        return NULL;
    }

    linelen = strlen(title1);
    for (count = 0; count < ART_COUNT; count++) {
        artlen = strlen(articlesNoSP[count]);
        if (linelen >= artlen+2 &&
                !strncmp(articlesNoSP[count],
                &(title1[linelen-artlen]), artlen) &&
                !strncmp(&(title1[linelen-artlen-2]), ", ", 2)) {
            /* title1 contains an article. */
            hasArt = 1;
            break;
        }
    }

    while (fgets(line, MXLINELEN+1, keyFile) != NULL) {
        /* Split a "origLine|key" line */
        if ((cp = strrchr(line, FSEP)) != NULL) {
            *cp = '\0';
            key = cp+1;
            strcpy(origLine, line);
        } else { continue; }

        /* We're searching a tv series episode, and this is not one. */
        if (searchingEpisode) {
            if (line[strlen(line)-1] != '}')
                continue;
        } else {
            if (line[strlen(line)-1] == '}')
                continue;
        }

        /* Check against title1 and title2 if and only if we're not
         * searching for a tv series episode. */
        if (!searchingEpisode) {
            /* Strip the (year[/imdbIndex]) */
            while ((cp = strrchr(line, '(')) != NULL) {
                *(cp-1) = '\0';
                if ((cp+1)[0] == '1' || (cp+1)[0] == '2' || (cp+1)[0] == '?')
                    break;
            }
            /* Strip the quotes around the TV series titles. */
            if (line[0] == '"') {
                strcpy(line, &(line[1]));
                linelen = strlen(line);
                if (linelen > 2 && line[linelen-1] == '"')
                    line[linelen-1] = '\0';
            }
            strtolower(line);

            /* If the current line has an article, strip it and put the new
             * line in noArt. */
            matchHasArt = 0;
            if (strrchr(line, ',') != NULL) {
                /* Strip the article. */
                linelen = strlen(line);
                for (count = 0; count < ART_COUNT; count++) {
                    artlen = strlen(articlesNoSP[count]);
                    if (linelen >= artlen+2 &&
                            !strncmp(articlesNoSP[count],
                            &(line[linelen-artlen]), artlen) &&
                            !strncmp(&(line[linelen-artlen-2]), ", ", 2)) {
                        strcpy(noArt, line);
                        noArt[linelen-artlen-2] = '\0';
                        matchHasArt = 1;
                        break;
                    }
                }
            }

            ratio = ratcliff(title1, line) + 0.05;

            if (matchHasArt && !hasArt)
                ratio = MAX(ratio, ratcliff(title1, noArt));
            else if (hasArt && !matchHasArt && title2 != NULL)
                ratio = MAX(ratio, ratcliff(title2, line));
        } else {
            ratio = 0.0;
        }

        if (title3 != NULL) {
            char origLineLower[MXLINELEN+1];
            strcpy(origLineLower, origLine);
            strtolower(origLineLower);
            ratio = MAX(ratio, ratcliff(title3, origLineLower) + 0.1);
        }

        if (ratio >= RO_THRESHOLD)
            PyList_Append(result, Py_BuildValue("(dis)",
                            ratio, strtol(key, NULL, 16), origLine));
    }

    fclose(keyFile);

    PyObject_CallMethod(result, "sort", NULL);
    PyObject_CallMethod(result, "reverse", NULL);
    if (nrResults > 0)
        PySequence_DelSlice(result, nrResults, PySequence_Size(result));

    return Py_BuildValue("O", result);
}


/* Search for the 'name1' in the key file keyFileName, returning at
 * most nrResults results.
 */
static PyObject*
search_company_name(PyObject *self, PyObject *pArgs, PyObject *pKwds)
{
    char *keyFileName = NULL;
    char *name1 = NULL;
    float ratio;
    FILE *keyFile;
    char line[MXLINELEN+1];
    char origLine[MXLINELEN+1];
    char *cp;
    char *key;
    short withoutCountry = 1;
    unsigned int nrResults = 0;
    static char *argnames[] = {"keyFile", "name1", "results", NULL};
    float var = 0.0;
    PyObject *result = PyList_New(0);

    if (!PyArg_ParseTupleAndKeywords(pArgs, pKwds, "ss|i",
                argnames, &keyFileName, &name1, &nrResults))
        return NULL;

    if (strlen(name1) > MXLINELEN)
        return Py_BuildValue("O", result);
    strtolower(name1);

    if ((keyFile = fopen(keyFileName, "r")) == NULL) {
        PyErr_SetFromErrno(PyExc_IOError);
        return NULL;
    }

    if (line[strlen(line)-1] == ']')
	    withoutCountry = 0;

    while (fgets(line, MXLINELEN+1, keyFile) != NULL) {
        /* Split a "origLine|key" line. */
        if ((cp = strrchr(line, FSEP)) != NULL) {
            *cp = '\0';
            key = cp+1;
            strcpy(origLine, line);
        } else { continue; }
	var = 0.0;
        /* Strip the optional countryCode, if required. */
        if (withoutCountry && (cp = strrchr(line, '[')) != NULL) {
            *(cp-1) = '\0';
	    var = -0.05;
	}

	strtolower(line);

        ratio = ratcliff(name1, line) + var;

        if (ratio >= RO_THRESHOLD)
            PyList_Append(result, Py_BuildValue("(dis)",
                            ratio, strtol(key, NULL, 16), origLine));
    }

    fclose(keyFile);

    PyObject_CallMethod(result, "sort", NULL);
    PyObject_CallMethod(result, "reverse", NULL);

    if (nrResults > 0)
        PySequence_DelSlice(result, nrResults, PySequence_Size(result));

    return Py_BuildValue("O", result);
}


/*========== tv series episodes ==========*/
/* Return a list of pairs (movieID, "long imdb episode title") with
 * every episode of the given series. */
static PyObject*
get_episodes(PyObject *self, PyObject *pArgs)
{
    long movieID = 0L;
    FILE *indexFile;
    char *indexFileName = NULL;
    FILE *keyFile;
    char *keyFileName = NULL;
    long kfIndex = 0L;
    int i = 0;
    int read_char;
    char line[MXLINELEN+1];
    char series[MXLINELEN+1];
    int seriesLen = 0;
    char *cp;
    char *key;

    PyObject *result = PyList_New(0);

    if (!PyArg_ParseTuple(pArgs, "lss", &movieID, &indexFileName, &keyFileName))
        return NULL;

    if (movieID < 0) {
        PyErr_SetString(PyExc_ValueError, "movieID must be positive.");
        return NULL;
    }

    if ((indexFile = fopen(indexFileName, "r")) == NULL) {
        PyErr_SetFromErrno(PyExc_IOError);
        return NULL;
    }

    fseek(indexFile, 4L*movieID, 0);
    for (i = 0; i < 4; i++) {
        if ((read_char = fgetc(indexFile)) == EOF) {
            PyErr_SetString(PyExc_IOError,
                            "unable to read indexFile; movieID too high?");
            return NULL;
        }
        kfIndex |= read_char << i*8L;
    }
    fclose(indexFile);

    if ((keyFile = fopen(keyFileName, "r")) == NULL) {
        PyErr_SetFromErrno(PyExc_IOError);
        return NULL;
    }

    fseek(keyFile, kfIndex, 0);
    fgets(series, MXLINELEN+1, keyFile);
    if ((cp = strrchr(series, FSEP)) != NULL) {
        *cp = '\0';
    }
    seriesLen = strlen(series);

    if (series[0] != '"' || series[seriesLen-1] != ')')
        return Py_BuildValue("O", result);

    while (fgets(line, MXLINELEN+1, keyFile) != NULL) {
        if (strncmp(line, series, seriesLen))
            break;

        if ((cp = strrchr(line, FSEP)) != NULL) {
            *cp = '\0';
            key = cp+1;
        } else {
            continue;
        }

        if (line[seriesLen+1] != '{' || line[strlen(line)-1] != '}')
            break;

        PyList_Append(result, Py_BuildValue("(is)",
                        strtol(key, NULL, 16), line));
    }
    fclose(keyFile);

    return Py_BuildValue("O", result);
}


/*========== soundex ==========*/
/* Max length of the soundex code to output (an uppercase char and
 * _at most_ 4 digits). */
#define SOUNDEX_LEN 5

/* Group Number Lookup Table  */
static char soundTable[26] =
{ 0 /* A */, '1' /* B */, '2' /* C */, '3' /* D */, 0 /* E */, '1' /* F */,
 '2' /* G */, 0 /* H */, 0 /* I */, '2' /* J */, '2' /* K */, '4' /* L */,
 '5' /* M */, '5' /* N */, 0 /* O */, '1' /* P */, '2' /* Q */, '6' /* R */,
 '2' /* S */, '3' /* T */, 0 /* U */, '1' /* V */, 0 /* W */, '2' /* X */,
  0 /* Y */, '2' /* Z */};

static PyObject*
pysoundex(PyObject *self, PyObject *pArgs)
{
    int i, j, n;
    char *s = NULL;
    char word[MXLINELEN+1];
    char soundCode[SOUNDEX_LEN+1];
    char c;

    if (!PyArg_ParseTuple(pArgs, "s", &s))
        return NULL;

    j = 0;
    n = strlen(s);

    /* Convert to uppercase and exclude non-ascii chars. */
    for (i = 0; i < n; i++) {
        c = toupper(s[i]);
        if (c < 91 && c > 64) {
            word[j] = c;
            j++;
        }
    }
    word[j] = '\0';

    n = strlen(word);
    if (n == 0) {
        /* If the string is empty, returns None. */
        return Py_BuildValue("");
    }
    soundCode[0] = word[0];

    /* Build the soundCode string. */
    j = 1;
    for (i = 1; j < SOUNDEX_LEN && i < n; i++) {
        c = soundTable[(word[i]-65)];
        /* Compact zeroes and equal consecutive digits ("12234112"->"123412") */
        if (c != 0 && c != soundCode[j-1]) {
                soundCode[j++] = c;
        }
    }
    soundCode[j] = '\0';

    return Py_BuildValue("s", soundCode);
}


static PyMethodDef cutils_methods[] = {
    {"ratcliff", pyratcliff,
        METH_VARARGS, "Ratcliff-Obershelp similarity."},
    {"search_name", (PyCFunction) search_name,
        METH_KEYWORDS, "Search for a person name."},
    {"search_title", (PyCFunction) search_title,
        METH_KEYWORDS, "Search for a movie title."},
    {"search_company_name", (PyCFunction) search_company_name,
        METH_KEYWORDS, "Search for a company name."},
    {"get_episodes", get_episodes,
        METH_VARARGS, "Return a list of episodes of the given series."},
    {"soundex", pysoundex,
        METH_VARARGS, "Soundex code for strings."},
    {NULL}
};


void
initcutils(void)
{
    Py_InitModule("cutils", cutils_methods);
}


