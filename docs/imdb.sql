# phpMyAdmin SQL Dump
# version 2.5.4
# http://www.phpmyadmin.net
#
# Host: localhost
# Generation Time: Aug 28, 2005 at 10:43 AM
# Server version: 4.0.16
# PHP Version: 4.1.2
# 
# Database : `imdb`
# 

# --------------------------------------------------------

#
# Table structure for table `akanames`
#
# Creation: Aug 28, 2005 at 10:40 AM
# Last update: Aug 28, 2005 at 10:40 AM
#

CREATE TABLE `akanames` (
  `personid` mediumint(8) unsigned NOT NULL default '0',
  `name` varchar(255) NOT NULL default '',
  `imdbindex` varchar(12) default NULL,
  KEY `personid` (`personid`),
  KEY `name` (`name`(5))
) TYPE=MyISAM COMMENT='AKA names';

#
# Dumping data for table `akanames`
#


# --------------------------------------------------------

#
# Table structure for table `akatitles`
#
# Creation: Aug 28, 2005 at 10:40 AM
# Last update: Aug 28, 2005 at 10:40 AM
#

CREATE TABLE `akatitles` (
  `movieid` mediumint(8) unsigned NOT NULL default '0',
  `title` varchar(255) NOT NULL default '',
  `imdbindex` varchar(12) default NULL,
  `kind` enum('movie','tv series','tv movie','video movie','tv mini series','video game') NOT NULL default 'movie',
  `year` smallint(5) unsigned default NULL,
  `note` varchar(255) default NULL,
  KEY `movieid` (`movieid`),
  KEY `title` (`title`(5))
) TYPE=MyISAM COMMENT='AKA titles';

#
# Dumping data for table `akatitles`
#


# --------------------------------------------------------

#
# Table structure for table `cast`
#
# Creation: Aug 28, 2005 at 10:40 AM
# Last update: Aug 28, 2005 at 10:40 AM
#

CREATE TABLE `cast` (
  `personid` mediumint(8) unsigned NOT NULL default '0',
  `movieid` mediumint(8) unsigned NOT NULL default '0',
  `currentrole` varchar(255) default NULL,
  `note` varchar(255) default NULL,
  `nrorder` tinyint(3) unsigned default NULL,
  `roleid` tinyint(3) unsigned NOT NULL default '0',
  KEY `personid` (`personid`),
  KEY `movieid` (`movieid`),
  KEY `roleid` (`roleid`)
) TYPE=MyISAM COMMENT='Persons who had worked in a movie';

#
# Dumping data for table `cast`
#


# --------------------------------------------------------

#
# Table structure for table `completecast`
#
# Creation: Aug 28, 2005 at 10:40 AM
# Last update: Aug 28, 2005 at 10:40 AM
#

CREATE TABLE `completecast` (
  `movieid` mediumint(8) unsigned NOT NULL default '0',
  `object` enum('cast','crew') NOT NULL default 'cast',
  `status` enum('complete','complete+verified') NOT NULL default 'complete',
  `note` varchar(255) default NULL,
  KEY `movieid` (`movieid`)
) TYPE=MyISAM COMMENT='Movies with complete cast/crew';

#
# Dumping data for table `completecast`
#


# --------------------------------------------------------

#
# Table structure for table `infotypes`
#
# Creation: Aug 25, 2005 at 10:38 AM
# Last update: Aug 26, 2005 at 04:32 PM
# Last check: Aug 26, 2005 at 03:52 PM
#

CREATE TABLE `infotypes` (
  `id` tinyint(3) unsigned NOT NULL auto_increment,
  `info` varchar(32) NOT NULL default '',
  PRIMARY KEY  (`id`),
  UNIQUE KEY `info` (`info`)
) TYPE=MyISAM COMMENT='Information types about movies and persons' AUTO_INCREMENT=130 ;

#
# Dumping data for table `infotypes`
#

INSERT INTO `infotypes` (`id`, `info`) VALUES (1, 'runtimes'),
(2, 'color info'),
(3, 'genres'),
(4, 'distributors'),
(5, 'languages'),
(6, 'certificates'),
(7, 'special effects companies'),
(8, 'sound mix'),
(9, 'tech info'),
(10, 'production companies'),
(11, 'countries'),
(12, 'episodes'),
(13, 'taglines'),
(14, 'keywords'),
(15, 'alternate versions'),
(16, 'crazy credits'),
(17, 'goofs'),
(18, 'soundtrack'),
(19, 'quotes'),
(20, 'release dates'),
(21, 'trivia'),
(22, 'locations'),
(23, 'connections'),
(24, 'business'),
(25, 'literature'),
(26, 'laserdisc'),
(27, 'miscellaneous companies'),
(28, 'mini biography'),
(29, 'birth notes'),
(30, 'birth date'),
(31, 'height'),
(32, 'death date'),
(34, 'spouse'),
(36, 'other works'),
(37, 'birth name'),
(38, 'salary history'),
(39, 'nick names'),
(40, 'books'),
(41, 'agent address'),
(42, 'biographical movies'),
(43, 'portrayed'),
(44, 'notable tv guest appearances'),
(45, 'where now'),
(46, 'trademarks'),
(47, 'interviews'),
(48, 'articles'),
(49, 'magazine covers'),
(50, 'pictorials'),
(51, 'death notes'),
(52, 'LD disc format'),
(53, 'LD year'),
(54, 'LD digital sound'),
(55, 'LD official retail price'),
(56, 'LD frequency response'),
(57, 'LD pressing plant'),
(58, 'LD length'),
(59, 'LD language'),
(60, 'LD review'),
(61, 'LD spaciality'),
(62, 'LD release date'),
(63, 'LD production country'),
(64, 'LD contrast'),
(65, 'LD color rendition'),
(66, 'LD picture format'),
(67, 'LD video noise'),
(68, 'LD video artifacts'),
(69, 'LD release country'),
(70, 'LD sharpness'),
(71, 'LD dynamic range'),
(72, 'LD audio noise'),
(73, 'LD color information'),
(74, 'LD group (genre)'),
(75, 'LD quality program'),
(76, 'LD close captions/teletext/ld+g'),
(77, 'LD category'),
(78, 'LD analog left'),
(79, 'LD certification'),
(80, 'LD audio quality'),
(81, 'LD video quality'),
(82, 'LD aspect ratio'),
(83, 'LD analog right'),
(84, 'LD additional information'),
(85, 'LD number of chapter stops'),
(86, 'LD dialogue intellegibility'),
(87, 'LD disc size'),
(88, 'LD master format'),
(89, 'LD subtitles'),
(90, 'LD status of availablility'),
(91, 'LD quality of source'),
(92, 'LD number of sides'),
(93, 'LD video standard'),
(94, 'LD supplement'),
(95, 'LD original title'),
(96, 'LD sound encoding'),
(97, 'LD number'),
(98, 'LD label'),
(99, 'LD catalog number'),
(100, 'LD laserdisc title'),
(101, 'screenplay/teleplay'),
(102, 'novel'),
(103, 'adaption'),
(104, 'book'),
(105, 'production process protocol'),
(107, 'printed media reviews'),
(108, 'essays'),
(109, 'other literature'),
(110, 'mpaa'),
(111, 'plot'),
(112, 'votes distribution'),
(113, 'votes'),
(114, 'rating'),
(116, 'production dates'),
(117, 'copyright holder'),
(118, 'filming dates'),
(119, 'budget'),
(120, 'weekend gross'),
(121, 'gross'),
(122, 'opening weekend'),
(123, 'rentals'),
(124, 'admissions'),
(126, 'studios'),
(128, 'top 250 rank'),
(129, 'bottom 10 rank');

# --------------------------------------------------------

#
# Table structure for table `linktypes`
#
# Creation: Aug 25, 2005 at 10:49 AM
# Last update: Aug 25, 2005 at 10:49 AM
#

CREATE TABLE `linktypes` (
  `id` tinyint(3) unsigned NOT NULL auto_increment,
  `type` varchar(32) NOT NULL default '',
  PRIMARY KEY  (`id`),
  UNIQUE KEY `type` (`type`)
) TYPE=MyISAM COMMENT='Kinds of connections between movies' AUTO_INCREMENT=19 ;

#
# Dumping data for table `linktypes`
#

INSERT INTO `linktypes` (`id`, `type`) VALUES (1, 'follows'),
(2, 'followed by'),
(3, 'remake of'),
(4, 'remade as'),
(5, 'references'),
(6, 'referenced in'),
(7, 'spoofs'),
(8, 'spoofed in'),
(9, 'features'),
(10, 'featured in'),
(11, 'spin off from'),
(12, 'spin off'),
(13, 'version of'),
(14, 'similar to'),
(15, 'edited into'),
(16, 'edited from'),
(17, 'alternate language version of'),
(18, 'unknown link');

# --------------------------------------------------------

#
# Table structure for table `movielinks`
#
# Creation: Aug 28, 2005 at 10:41 AM
# Last update: Aug 28, 2005 at 10:41 AM
#

CREATE TABLE `movielinks` (
  `movieid` mediumint(8) unsigned NOT NULL default '0',
  `movietoid` mediumint(8) unsigned NOT NULL default '0',
  `linktypeid` tinyint(3) unsigned NOT NULL default '0',
  `note` varchar(255) default NULL,
  KEY `movieid` (`movieid`)
) TYPE=MyISAM;

#
# Dumping data for table `movielinks`
#


# --------------------------------------------------------

#
# Table structure for table `moviesinfo`
#
# Creation: Aug 28, 2005 at 10:41 AM
# Last update: Aug 28, 2005 at 10:41 AM
#

CREATE TABLE `moviesinfo` (
  `movieid` mediumint(8) unsigned NOT NULL default '0',
  `infoid` tinyint(3) unsigned NOT NULL default '0',
  `info` text NOT NULL,
  `note` varchar(255) default NULL,
  KEY `movieid` (`movieid`),
  KEY `infoid` (`infoid`)
) TYPE=MyISAM COMMENT='Information about a movie';

#
# Dumping data for table `moviesinfo`
#


# --------------------------------------------------------

#
# Table structure for table `names`
#
# Creation: Aug 28, 2005 at 10:41 AM
# Last update: Aug 28, 2005 at 10:41 AM
#

CREATE TABLE `names` (
  `personid` mediumint(8) unsigned NOT NULL auto_increment,
  `name` varchar(255) NOT NULL default '',
  `imdbindex` varchar(12) default NULL,
  `imdbid` mediumint(8) unsigned default NULL,
  PRIMARY KEY  (`personid`),
  KEY `name` (`name`(5),`imdbindex`)
) TYPE=MyISAM COMMENT='People' AUTO_INCREMENT=1 ;

#
# Dumping data for table `names`
#


# --------------------------------------------------------

#
# Table structure for table `personsinfo`
#
# Creation: Aug 28, 2005 at 10:41 AM
# Last update: Aug 28, 2005 at 10:41 AM
#

CREATE TABLE `personsinfo` (
  `personid` mediumint(9) NOT NULL default '0',
  `infoid` tinyint(3) unsigned NOT NULL default '0',
  `info` text NOT NULL,
  `note` varchar(255) default NULL,
  KEY `personid` (`personid`),
  KEY `infoid` (`infoid`)
) TYPE=MyISAM COMMENT='Information about a person';

#
# Dumping data for table `personsinfo`
#


# --------------------------------------------------------

#
# Table structure for table `roletypes`
#
# Creation: Aug 25, 2005 at 10:54 AM
# Last update: Aug 26, 2005 at 03:20 PM
#

CREATE TABLE `roletypes` (
  `id` tinyint(3) unsigned NOT NULL auto_increment,
  `role` varchar(32) NOT NULL default '',
  PRIMARY KEY  (`id`),
  UNIQUE KEY `role` (`role`)
) TYPE=MyISAM COMMENT='Kinds of roles/duties' AUTO_INCREMENT=13 ;

#
# Dumping data for table `roletypes`
#

INSERT INTO `roletypes` (`id`, `role`) VALUES (1, 'actor'),
(2, 'actress'),
(3, 'producer'),
(4, 'writer'),
(5, 'cinematographer'),
(6, 'composer'),
(7, 'costume designer'),
(8, 'director'),
(9, 'editor'),
(10, 'crewmembers'),
(11, 'production designer');

# --------------------------------------------------------

#
# Table structure for table `titles`
#
# Creation: Aug 28, 2005 at 10:41 AM
# Last update: Aug 28, 2005 at 10:41 AM
#

CREATE TABLE `titles` (
  `movieid` mediumint(9) NOT NULL auto_increment,
  `title` varchar(255) NOT NULL default '',
  `imdbindex` varchar(12) default NULL,
  `kind` enum('movie','tv series','tv movie','video movie','tv mini series','video game') NOT NULL default 'movie',
  `year` mediumint(8) unsigned default NULL,
  `imdbid` mediumint(8) unsigned default NULL,
  PRIMARY KEY  (`movieid`),
  KEY `title` (`title`(5),`kind`,`year`,`imdbindex`)
) TYPE=MyISAM COMMENT='Movies' AUTO_INCREMENT=1 ;

#
# Dumping data for table `titles`
#

