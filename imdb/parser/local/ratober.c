/*
 * Scan IMDb titles or names ".key" files, searching for a movie title
 * or a person name.
 *
 * Copyright 2004, 2005 Davide Alberani <da@erlug.linux.it>
 * Released under the GPL license.
 * 
 * Heavily based on code from the "simil" Python module.
 * The "simil" module is copyright of Luca Montecchiani <cbm64 _at_ inwind.it>
 * and can be found here: http://spazioinwind.libero.it/montecchiani/
 * It was released under the GPL license; original comments are leaved
 * below.
 * 
 */

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
#define STRING_MAXLENDIFFER 0.75

#define MXLINELEN   700
#define FSEP        '|'

#define RO_THRESHOLD 0.6


/* List of articles.
   XXX: are "agapi mou" and  "liebling" articles? */
#define ART_COUNT    45
char *articles[ART_COUNT] = {"the ", "la ", "a ", "die ", "der ", "le ", "el ",
            "l'", "il ", "das ", "les ", "i ", "o ", "ein ", "un ", "los ",
            "de ", "an ", "una ", "eine ", "las ", "den ", "gli ", "het ",
            "lo ", "os ", "az ", "ha-", "een ", "det ",
            "oi ", "ang ", "ta ", "al-", "dem ",
            "uno ", "un'", "ett ", "mga ", "Ο ", "Η ",
            "eines ", "els ", "Το ", "Οι "};

char *articlesNoSP[ART_COUNT] = {"the", "la", "a", "die", "der", "le", "el",
           "l'", "il", "das", "les", "i", "o", "ein", "un", "los",
           "de", "an", "una", "eine", "las", "den", "gli", "het",
           "lo", "os", "az", "ha-", "een", "det",
           "oi", "ang", "ta", "al-", "dem",
           "uno", "un'", "ett", "mga", "Ο", "Η",
           "eines", "els", "Το", "Οι"};


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
    if (strcasecmp(s, t) == 0)
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


/* Search for the searchText2 name in the key file keyFileName,
 * returning at most nrResults results. */
static PyObject*
search_name(PyObject *self, PyObject *pArgs, PyObject *pKwds)
{
    char *searchText2, *keyFileName;
    char searchText1[MXLINELEN] = "";
    FILE *keyFile;
    float res;
    char line[MXLINELEN];
    char origLine[MXLINELEN];
    char *cp;
    char *key;
    short doSecTest = 1;
    short doThirdTest = 0;
    unsigned int nrResults = 0;
    static char *argnames[] = {"name", "keyFile", "results", NULL};
    PyObject *result = PyList_New(0);

    if (!PyArg_ParseTupleAndKeywords(pArgs, pKwds, "ss|i",
                argnames, &searchText2, &keyFileName, &nrResults))
        return NULL;

    if (strlen(searchText2) > MXLINELEN - 1) {
        return Py_BuildValue("O", result);
    }

    if ((keyFile = fopen(keyFileName, "r")) == NULL) {
        PyErr_SetFromErrno(PyExc_IOError);
        return NULL;
    }

    if (strstr(searchText2, ", ") == NULL) {
        if ((cp = strrchr(searchText2, ' ')) != NULL) {
            /* build a "Surname, Name" search pattern.
             * XXX: what about search patterns with multiple spaces? */
            strncpy(searchText1, cp+1, strlen(cp));
            strncat(searchText1, ", ", 2);
            strncat(searchText1, searchText2, strlen(searchText2) - strlen(cp));
        } else {
            /* Only a surname? */
            doSecTest = 0;
            doThirdTest = 1;
        }
    } else {
        /* Contains a ", ", so we can assume that the search pattern
         * is already in the "Surname, Name" format. */
        strcpy(searchText1, searchText2);
        doSecTest = 0;
    }

    while (fgets(line, MXLINELEN, keyFile) != NULL) {
        if ((cp = strrchr(line, FSEP)) != NULL) {
            *cp = '\0';
            key = cp+1;
            strcpy(origLine, line);
        } else { continue; }
        if ((cp = strstr(line, " (")) != NULL)
            *cp = '\0';
        res = ratcliff(searchText1, line);
        if (res >= RO_THRESHOLD) {
            PyList_Append(result, Py_BuildValue("(dis)",
                            res, strtol(key, NULL, 16), origLine));
            continue;
        }
        if (doSecTest) {
            res = ratcliff(searchText2, line);
            if (res >= RO_THRESHOLD) {
                PyList_Append(result, Py_BuildValue("(dis)",
                            res, strtol(key, NULL, 16), origLine));
                continue;
            }
        }

        if (doThirdTest) {
            if ((cp = strstr(line, ", ")) != NULL) {
                *cp = '\0';
            }
            res = ratcliff(searchText2, line) - 0.1;
            if (res >= RO_THRESHOLD) {
                PyList_Append(result, Py_BuildValue("(dis)",
                                res, strtol(key, NULL, 16), origLine));
                continue;
            }
        }
    }

    fclose(keyFile);

    PyObject_CallMethod(result, "sort", NULL);
    PyObject_CallMethod(result, "reverse", NULL);
    if (nrResults > 0)
        PySequence_DelSlice(result, nrResults, PySequence_Size(result));

    return Py_BuildValue("O", result);
}


/* Search for the searchText2 title in the key file keyFileName,
 * returning at most nrResults results. */
static PyObject*
search_title(PyObject *self, PyObject *pArgs, PyObject *pKwds)
{
    char *searchText2, *keyFileName;
    char searchText1[MXLINELEN] = "";
    FILE *keyFile;
    float res;
    char line[MXLINELEN];
    char origLine[MXLINELEN];
    char *cp;
    char *key;
    short doSecTest = 0;
    unsigned int nrResults = 0;
    unsigned short artlen = 0;
    unsigned short linelen = 0;
    unsigned int count = 0;
    static char *argnames[] = {"title", "keyFile", "results", NULL};
    PyObject *result = PyList_New(0);

    if (!PyArg_ParseTupleAndKeywords(pArgs, pKwds, "ss|i",
                argnames, &searchText2, &keyFileName, &nrResults))
        return NULL;

    if (strlen(searchText2) > MXLINELEN - 1) {
        return Py_BuildValue("O", result);
    }

    if ((keyFile = fopen(keyFileName, "r")) == NULL) {
        PyErr_SetFromErrno(PyExc_IOError);
        return NULL;
    }

    for (count = 0; count < ART_COUNT; count++) {
        artlen = strlen(articles[count]);
        if (!strncasecmp(searchText2, articles[count], artlen)) {
            strcpy(searchText1, &searchText2[artlen]);
            strcat(searchText1, ", ");
            strcat(searchText1, articles[count]);
            if (searchText1[strlen(searchText1)-1] == ' ')
                searchText1[strlen(searchText1)-1] = '\0';
            doSecTest = 1;
            break;
        }
    }
    if (!doSecTest)
        strcpy(searchText1, searchText2);

    /* for (count = 0; count < ART_COUNT; count++) {
        artlen = strlen(articles[count]);
        if (articles[count][artlen-1] == ' ')
            articles[count][artlen-1] = '\0';
    } */

    while (fgets(line, MXLINELEN, keyFile) != NULL) {
        if ((cp = strrchr(line, FSEP)) != NULL) {
            *cp = '\0';
            key = cp+1;
            strcpy(origLine, line);
        } else { continue; }
        if ((cp = strstr(line, " (")) != NULL)
            *cp = '\0';
        if (line[0] == '"')
            *line = line[1];
        if (line[(linelen = strlen(line))-1] == '"')
            line[linelen] = '\0';
        res = ratcliff(searchText1, line);
        if (res >= RO_THRESHOLD) {
            PyList_Append(result, Py_BuildValue("(dis)",
                            res, strtol(key, NULL, 16), origLine));
            continue;
        }
        if (doSecTest) {
            res = ratcliff(searchText2, line);
            if (res >= RO_THRESHOLD) {
                PyList_Append(result, Py_BuildValue("(dis)",
                                res, strtol(key, NULL, 16), origLine));
                continue;
            }
        } else if (strstr(line, ", ") != NULL) {
            /* Strip the article. */
            linelen = strlen(line);
            for (count = 0; count < ART_COUNT; count++) {
                artlen = strlen(articlesNoSP[count]);
                if (linelen >= artlen+2 &&
                        !strncasecmp(articlesNoSP[count],
                        &(line[linelen-artlen]), artlen) &&
                        !strncmp(&(line[linelen-artlen-2]), ", ", 2)) {
                    line[linelen-artlen-2] = '\0';
                    res = ratcliff(searchText2, line) - 0.1;
                    if (res >= RO_THRESHOLD) {
                        PyList_Append(result, Py_BuildValue("(dis)",
                                        res, strtol(key, NULL, 16), origLine));
                    }
                    break;
                }
            }
        }
    }

    fclose(keyFile);

    PyObject_CallMethod(result, "sort", NULL);
    PyObject_CallMethod(result, "reverse", NULL);
    if (nrResults > 0)
        PySequence_DelSlice(result, nrResults, PySequence_Size(result));

    return Py_BuildValue("O", result);
}


static PyMethodDef ratober_methods[] = {
    {"search_name", (PyCFunction) search_name,
        METH_KEYWORDS, "search for a person name"},
    {"search_title", (PyCFunction) search_title,
        METH_KEYWORDS, "search for a movie title"},
    {NULL}
};


void
initratober(void)
{
    Py_InitModule("ratober", ratober_methods);
}


