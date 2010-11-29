import re, time
from PMS import *

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
	Plugin.AddPrefixHandler(PLUGIN_PREFIX, MainMenu, PLUGIN_TITLE, PLUGIN_ICON_DEFAULT, R(PLUGIN_ARTWORK))
	Plugin.AddViewGroup("Details", "InfoList")

	# Set the default cache time and user-agent
	HTTP.SetCacheTime(1800)
	HTTP.SetHeader("User-Agent", "Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10.6; en-US; rv:1.9.2.12) Gecko/20101026 Firefox/3.6.12")

####################################################################################################

def MainMenu():
	dir  = MediaContainer(R(PLUGIN_ARTWORK), "Details", PLUGIN_TITLE)
	data = XML.ElementFromURL(PLUGIN_URL + "/repertoire", True)
	
	shows = []
	for c in data.xpath("//h1/.."):
		show = {}
		show["name"] = c.find("h1").text
		show["url"]  = c.get("href")
		shows.append(show)
	
	for show in shows:
		dir.Append(Function(DirectoryItem(Show, show["name"]), show = show))
	
	return dir

####################################################################################################

def Show(sender, show):
	dir  = MediaContainer(R(PLUGIN_ARTWORK), "Details", PLUGIN_TITLE, show["name"])
	data = XML.ElementFromURL(PLUGIN_URL + show["url"], True)
	
	seasons = {}
	for c in data.xpath("//div[@class = 'blocepisodeemission']"):
		floatimg      = c.xpath("div[@class = 'floatimg']")[0]
		floatinfos    = c.xpath("div[@class = 'floatinfos']")[0]
		
		season_name = floatinfos.xpath("p")[0].text
		if season_name not in seasons:
			seasons[season_name] = []
		
		episode = {}
		episode["name"]     = floatimg.find("a").find("img").get("alt")
		episode["url"]      = floatimg.find("a").get("href")
		episode["thumb"]    = floatimg.find("a").find("img").get("src")
		episode["date"]     = floatinfos.find("div").find("strong").text
		episode["summary"]  = floatinfos.xpath("p")[1].text
		seasons[season_name].append(episode)
	
	keys = seasons.keys()
	keys.sort(lambda x, y: cmp(x.lower(), y.lower()))
	
	for key in keys:
		dir.Append(Function(DirectoryItem(Season, key), show_name = show["name"], season_name = key, season = seasons[key])) 
	
	return dir

####################################################################################################

def Season(sender, show_name, season_name, season):
	dir = MediaContainer(R(PLUGIN_ARTWORK), "Details", show_name, season_name)
	
	season.sort(lambda x, y: cmp(x["url"], y["url"]))
	
	for episode in season:
		dir.Append(Function(RTMPVideoItem(Episode, title = episode["name"], subtitle = episode["date"], thumb = episode["thumb"], summary = episode["summary"]), episode_url = episode["url"]))
	
	return dir

####################################################################################################

def Episode(sender, episode_url):
	episode_data = HTTP.Request(PLUGIN_URL + episode_url)
	episode_data = HTTP.Request(PLUGIN_CONTENT_URL + re.compile("toutv.releaseUrl='(.+?)'").findall(episode_data)[0] + '&format=SMIL')
	player_url   = "rtmp:" + re.compile('<meta base="rtmp:(.+?)"').findall(episode_data)[0]
	clip_url     = "mp4:" + re.compile('<ref src="mp4:(.+?)"').findall(episode_data)[0]
	return Redirect(RTMPVideoItem(player_url, clip = clip_url))
