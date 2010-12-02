# -*- coding: latin-1 -*-

from PMS import *
import re, time

# Plugin parameters
PLUGIN_TITLE		= "TOU.TV"
PLUGIN_PREFIX   	= "/video/TOU.TV"
PLUGIN_URL			= "http://www.tou.tv"
PLUGIN_CONTENT_URL 	= 'http://release.theplatform.com/content.select?pid='

# Plugin resources
PLUGIN_ICON_DEFAULT	= "icon-default.png"
PLUGIN_ARTWORK		= "art-default.jpg"

####################################################################################################

def Start():
	Plugin.AddPrefixHandler(PLUGIN_PREFIX, MainMenu, PLUGIN_TITLE, PLUGIN_ICON_DEFAULT, PLUGIN_ARTWORK)
	Plugin.AddViewGroup("InfoList", viewMode = "InfoList", mediaType = "items")
	
	# Set the default MediaContainer attributes
	MediaContainer.title1    = PLUGIN_TITLE
	MediaContainer.viewGroup = "InfoList"
	MediaContainer.art       = R(PLUGIN_ARTWORK)
	
	# Default icons for DirectoryItem and WebVideoItem in case there isn't an image
	DirectoryItem.thumb = R(PLUGIN_ICON_DEFAULT)
	WebVideoItem.thumb  = R(PLUGIN_ICON_DEFAULT)
	
	# Set the default cache time
	HTTP.SetCacheTime(1800)
	HTTP.SetHeader('User-Agent', 'Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10.6; en-US; rv:1.9.2.12) Gecko/20101026 Firefox/3.6.12')

###################################################################################################

def MainMenu():
	dir = MediaContainer()

	shows = []
	data = XML.ElementFromURL(PLUGIN_URL + "/repertoire", isHTML = True)
	
	for c in data.xpath("//h1/.."):
		show = {}
		show["title"]      = c.find("h1").text
		show["genre"]      = c.xpath("span[@class = 'genre']")[0].text
		show["url"]        = c.get("href")
		
		try:
			show["numseasons"] = int(c.xpath("span[@class = 'nbsaison']")[0].text)
		except:
			show["numseasons"] = 0
		
		shows.append(show)
	
	shows.sort(lambda x, y: cmp(x["title"].lower(), y["title"].lower()))
	
	dir.Append(Function(DirectoryItem(AllShows, title = "Toutes les émissions"), shows = shows))
	dir.Append(Function(DirectoryItem(BrowseByGenre, title = "Parcourir par genre"), shows = shows))
	
	return dir

####################################################################################################

def AllShows(sender, shows):
	dir = MediaContainer(title2 = sender.itemTitle)
	
	for show in shows:
		dir.Append(Function(DirectoryItem(Show, title = show["title"], subtitle = show["genre"]), show = show))
	
	return dir

####################################################################################################

def BrowseByGenre(sender, shows):
	dir = MediaContainer(title2 = sender.itemTitle)
	
	genres = {}
	
	for show in shows:
		if show["genre"] not in genres:
			genres[show["genre"]] = []
		genres[show["genre"]].append(show)
	
	keys = genres.keys()
	keys.sort(lambda x, y: cmp(x.lower(), y.lower()))
	
	for key in keys:
		dir.Append(Function(DirectoryItem(Genre, title = key), genre = genres[key]))
	
	return dir

####################################################################################################

def Genre(sender, genre):
	dir = MediaContainer(title2 = sender.itemTitle)
	
	for show in genre:
		dir.Append(Function(DirectoryItem(Show, title = show["title"], subtitle = show["genre"]), show = show))
	
	return dir

####################################################################################################

def Show(sender, show):
	dir = MediaContainer(title2 = sender.itemTitle)
	
	try:
		data     = XML.ElementFromURL(PLUGIN_URL + show["url"], isHTML = True)
		raw_data = HTTP.Request(PLUGIN_URL + show["url"])
		
		if show["numseasons"] == 0:
			movie_title   = data.xpath("//h1[@class = 'emission']")[0].text
			movie_date    = data.xpath("//div[@class = 'specs']/p[@id = 'MainContent_ctl00_PDateEpisode']/strong")[0].text
			movie_summary = re.compile('"Description":"(.+?)"').findall(raw_data)[0]

			try:
				movie_thumb = re.compile('<meta property="og:image" content="(.+?)"').findall(raw_data)[0]
			except:
				movie_thumb = None
				
			dir.Append(Function(WebVideoItem(Video, title = movie_title, subtitle = movie_date, summary = movie_summary, thumb = Function(Thumb, url = movie_thumb)), video_url = show["url"]))
		else:
			season_summary = data.xpath("//div[@id = 'detailsemission']/p")[0].text
			
			try:
				season_thumb = re.compile('<meta property="og:image" content="(.+?)"').findall(raw_data)[0]
			except:
				season_thumb = None
				pass
			
			show["seasons"] = {}
			
			for c in data.xpath("//div[@class = 'blocepisodeemission']"):
				floatimg      = c.xpath("div[@class = 'floatimg']")[0]
				floatinfos    = c.xpath("div[@class = 'floatinfos']")[0]
				
				season_name = floatinfos.xpath("p")[0].text
				if season_name not in show["seasons"]:
					show["seasons"][season_name] = []
				
				episode = {}
				episode["name"]     = floatimg.find("a").find("img").get("alt")
				episode["url"]      = floatimg.find("a").get("href")
				episode["thumb"]    = floatimg.find("a").find("img").get("src")
				episode["date"]     = floatinfos.find("div").find("strong").text
				episode["summary"]  = floatinfos.xpath("p")[1].text
				show["seasons"][season_name].append(episode)
			
			season_names = show["seasons"].keys()
			season_names.sort(lambda x, y: cmp(x.lower(), y.lower()))
			
			for season_name in season_names:
				dir.Append(Function(DirectoryItem(Season, title = season_name, summary = season_summary, thumb = Function(Thumb, url = season_thumb)), show_title = show["title"], season = show["seasons"][season_name])) 
	except:
		dir.header  = "Emission vide"
		dir.message = "Cette émission n'a aucun contenu."
		
	return dir

####################################################################################################

def Season(sender, show_title, season):
	dir = MediaContainer(title1 = show_title, title2 = sender.itemTitle)
	
	season.sort(lambda x, y: cmp(x["url"], y["url"]))
	
	for episode in season:
		dir.Append(Function(WebVideoItem(Video, title = episode["name"], subtitle = episode["date"], thumb = Function(Thumb, url = episode["thumb"]), summary = episode["summary"]), video_url = episode["url"]))
	
	if len(dir) == 0:
		dir.header  = "Saison vide"
		dir.message = "Cette saison n'a aucun contenu."
	
	return dir

####################################################################################################

def Video(sender, video_url):
	video_data = HTTP.Request(PLUGIN_URL + video_url)
	video_data = HTTP.Request(PLUGIN_CONTENT_URL + re.compile("toutv.releaseUrl='(.+?)'").findall(video_data)[0] + '&format=SMIL')
	
	try:
		player_url = "rtmp:" + re.compile('<meta base="rtmp:(.+?)"').findall(video_data)[0]
		clip_url   = "mp4:" + re.compile('<ref src="mp4:(.+?)"').findall(video_data)[0]
	except:
		try:
			# You are not in a geographic region that has access to this content.
			player_url = "http:" + re.compile('<meta base="http:(.+?)"').findall(video_data)[0]
			clip_url   = re.compile('<ref src="(.+?)"').findall(video_data)[0]
		except:
			player_url = None
			clip_url   = None
	
	return Redirect(RTMPVideoItem(player_url, clip = clip_url))

####################################################################################################

def Thumb(url):
	if url != None:
		try:
			image = HTTP.Request(url, cacheTime=CACHE_1MONTH)
			return DataObject(image, 'image/jpeg')
		except:
			pass

	return Redirect(R(PLUGIN_ICON_DEFAULT))
