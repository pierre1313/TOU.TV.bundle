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
  Plugin.AddViewGroup("List", viewMode="List", mediaType="items")
  Plugin.AddViewGroup("InfoList", viewMode="InfoList", mediaType="items")

  # Set the default MediaContainer attributes
  MediaContainer.title1    = PLUGIN_TITLE
  MediaContainer.viewGroup = "List"
  MediaContainer.art       = R(PLUGIN_ARTWORK)

  # Default icons for DirectoryItem and WebVideoItem in case there isn't an image
  DirectoryItem.thumb      = R(PLUGIN_ICON_DEFAULT)
  WebVideoItem.thumb       = R(PLUGIN_ICON_DEFAULT)

  # Set the default cache time
  HTTP.SetCacheTime(1800)
  HTTP.SetHeader('User-Agent', 'Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10.6; en-US; rv:1.9.2.12) Gecko/20101026 Firefox/3.6.12')

###################################################################################################

def MainMenu():
	dir  = MediaContainer()
	data = XML.ElementFromURL(PLUGIN_URL + "/repertoire", isHTML=True)

	shows = []
	for c in data.xpath("//h1/.."):
		show = {}
		show["name"] = c.find("h1").text
		show["url"]  = c.get("href")
		shows.append(show)

	for show in shows:
		dir.Append(Function(DirectoryItem(Show, title=show["name"]), show = show))

	return dir

####################################################################################################

def Show(sender, show):
	dir  = MediaContainer(title2=sender.itemTitle)
	data = XML.ElementFromURL(PLUGIN_URL + show["url"], isHTML=True)

	seasons = {}

	try:
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
	except:
		pass

	keys = seasons.keys()
	keys.sort(lambda x, y: cmp(x.lower(), y.lower()))

	for key in keys:
		dir.Append(Function(DirectoryItem(Season, title=key), show_name = show["name"], season_name = key, season = seasons[key])) 

	if len(dir) == 0:
		dir.header = "Empty directory"
		dir.message = "This programme doesn't have any content."

	return dir

####################################################################################################

def Season(sender, show_name, season_name, season):
	dir = MediaContainer(viewGroup="InfoList", title1=show_name, title2=season_name)

	season.sort(lambda x, y: cmp(x["url"], y["url"]))

	for episode in season:
		dir.Append(Function(VideoItem(Episode, title = episode["name"], subtitle = episode["date"], thumb = episode["thumb"], summary = episode["summary"]), episode_url = episode["url"]))

	if len(dir) == 0:
		dir.header = "Empty directory"
		dir.message = "This season doesn't have any content."

	return dir

####################################################################################################

def Episode(sender, episode_url):
	episode_data = HTTP.Request(PLUGIN_URL + episode_url)
	episode_data = HTTP.Request(PLUGIN_CONTENT_URL + re.compile("toutv.releaseUrl='(.+?)'").findall(episode_data)[0] + '&format=SMIL')

	try:
		player_url       = "rtmp:" + re.compile('<meta base="rtmp:(.+?)"').findall(episode_data)[0]
		clip_url         = "mp4:" + re.compile('<ref src="mp4:(.+?)"').findall(episode_data)[0]
	except:
		try:
			# You are not in a geographic region that has access to this content.
			player_url   = "http:" + re.compile('<meta base="http:(.+?)"').findall(episode_data)[0]
			clip_url     = re.compile('<ref src="(.+?)"').findall(episode_data)[0]
		except:
			player_url   = None
			clip_url     = None

	return Redirect(RTMPVideoItem(player_url, clip = clip_url))
