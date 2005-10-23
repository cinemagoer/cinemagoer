# phpMyAdmin SQL Dump
# version 2.5.4
# http://www.phpmyadmin.net
#
# Host: localhost
# Generation Time: Oct 23, 2005 at 12:37 PM
# Server version: 4.0.16
# PHP Version: 4.1.2
# 
# Database : `imdb`
# 

# --------------------------------------------------------

#
# Table structure for table `akanames`
#
# Creation: Oct 23, 2005 at 12:35 PM
# Last update: Oct 23, 2005 at 12:35 PM
#

DROP TABLE IF EXISTS `akanames`;
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
# Creation: Oct 23, 2005 at 12:35 PM
# Last update: Oct 23, 2005 at 12:35 PM
#

DROP TABLE IF EXISTS `akatitles`;
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
# Creation: Oct 23, 2005 at 12:35 PM
# Last update: Oct 23, 2005 at 12:35 PM
#

DROP TABLE IF EXISTS `cast`;
CREATE TABLE `cast` (
  `personid` mediumint(8) unsigned NOT NULL default '0',
  `movieid` mediumint(8) unsigned NOT NULL default '0',
  `currentrole` varchar(255) default NULL,
  `note` varchar(255) default NULL,
  `nrorder` smallint(5) unsigned default NULL,
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
# Creation: Oct 23, 2005 at 12:35 PM
# Last update: Oct 23, 2005 at 12:35 PM
#

DROP TABLE IF EXISTS `completecast`;
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
# Creation: Oct 08, 2005 at 01:17 PM
# Last update: Oct 08, 2005 at 01:17 PM
#

DROP TABLE IF EXISTS `infotypes`;
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
(12, 'taglines'),
(13, 'keywords'),
(14, 'alternate versions'),
(15, 'crazy credits'),
(16, 'goofs'),
(17, 'soundtrack'),
(18, 'quotes'),
(19, 'release dates'),
(20, 'trivia'),
(21, 'locations'),
(22, 'miscellaneous companies'),
(23, 'mini biography'),
(24, 'birth notes'),
(25, 'birth date'),
(26, 'height'),
(27, 'death date'),
(28, 'spouse'),
(29, 'other works'),
(30, 'birth name'),
(31, 'salary history'),
(32, 'nick names'),
(33, 'books'),
(34, 'agent address'),
(35, 'biographical movies'),
(36, 'portrayed'),
(37, 'where now'),
(38, 'trademarks'),
(39, 'interviews'),
(40, 'articles'),
(41, 'magazine covers'),
(42, 'pictorials'),
(43, 'death notes'),
(44, 'LD disc format'),
(45, 'LD year'),
(46, 'LD digital sound'),
(47, 'LD official retail price'),
(48, 'LD frequency response'),
(49, 'LD pressing plant'),
(50, 'LD length'),
(51, 'LD language'),
(52, 'LD review'),
(53, 'LD spaciality'),
(54, 'LD release date'),
(55, 'LD production country'),
(56, 'LD contrast'),
(57, 'LD color rendition'),
(58, 'LD picture format'),
(59, 'LD video noise'),
(60, 'LD video artifacts'),
(61, 'LD release country'),
(62, 'LD sharpness'),
(63, 'LD dynamic range'),
(64, 'LD audio noise'),
(65, 'LD color information'),
(66, 'LD group (genre)'),
(67, 'LD quality program'),
(68, 'LD close captions/teletext/ld+g'),
(69, 'LD category'),
(70, 'LD analog left'),
(71, 'LD certification'),
(72, 'LD audio quality'),
(73, 'LD video quality'),
(74, 'LD aspect ratio'),
(75, 'LD analog right'),
(76, 'LD additional information'),
(77, 'LD number of chapter stops'),
(78, 'LD dialogue intellegibility'),
(79, 'LD disc size'),
(80, 'LD master format'),
(81, 'LD subtitles'),
(82, 'LD status of availablility'),
(83, 'LD quality of source'),
(84, 'LD number of sides'),
(85, 'LD video standard'),
(86, 'LD supplement'),
(87, 'LD original title'),
(88, 'LD sound encoding'),
(89, 'LD number'),
(90, 'LD label'),
(91, 'LD catalog number'),
(92, 'LD laserdisc title'),
(93, 'screenplay/teleplay'),
(94, 'novel'),
(95, 'adaption'),
(96, 'book'),
(97, 'production process protocol'),
(98, 'printed media reviews'),
(99, 'essays'),
(100, 'other literature'),
(101, 'mpaa'),
(102, 'plot'),
(103, 'votes distribution'),
(104, 'votes'),
(105, 'rating'),
(106, 'production dates'),
(107, 'copyright holder'),
(108, 'filming dates'),
(109, 'budget'),
(110, 'weekend gross'),
(111, 'gross'),
(112, 'opening weekend'),
(113, 'rentals'),
(114, 'admissions'),
(115, 'studios'),
(116, 'top 250 rank'),
(117, 'bottom 10 rank');

# --------------------------------------------------------

#
# Table structure for table `linktypes`
#
# Creation: Oct 08, 2005 at 01:17 PM
# Last update: Oct 08, 2005 at 01:17 PM
#

DROP TABLE IF EXISTS `linktypes`;
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
# Creation: Oct 23, 2005 at 12:35 PM
# Last update: Oct 23, 2005 at 12:35 PM
#

DROP TABLE IF EXISTS `movielinks`;
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
# Creation: Oct 23, 2005 at 12:35 PM
# Last update: Oct 23, 2005 at 12:35 PM
#

DROP TABLE IF EXISTS `moviesinfo`;
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
# Creation: Oct 23, 2005 at 12:35 PM
# Last update: Oct 23, 2005 at 12:35 PM
#

DROP TABLE IF EXISTS `names`;
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
# Creation: Oct 23, 2005 at 12:35 PM
# Last update: Oct 23, 2005 at 12:35 PM
#

DROP TABLE IF EXISTS `personsinfo`;
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
# Creation: Oct 08, 2005 at 01:17 PM
# Last update: Oct 23, 2005 at 12:30 PM
#

DROP TABLE IF EXISTS `roletypes`;
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
(10, 'miscellaneous crew'),
(11, 'production designer'),
(12, 'guest');

# --------------------------------------------------------

#
# Table structure for table `titles`
#
# Creation: Oct 23, 2005 at 12:35 PM
# Last update: Oct 23, 2005 at 12:35 PM
#

DROP TABLE IF EXISTS `titles`;
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

