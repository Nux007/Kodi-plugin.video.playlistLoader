import urllib, urllib2, os, io, xbmc, xbmcaddon, xbmcgui, json, re, chardet, shutil, time, hashlib, gzip, xbmcvfs, requests
from StringIO import StringIO
import requests, shutil
from xbmc import getLocalizedString

AddonID = 'plugin.video.playlistLoader'
Addon = xbmcaddon.Addon(AddonID)
icon = Addon.getAddonInfo('icon')
AddonName = Addon.getAddonInfo("name")
addon_data_dir = xbmc.translatePath(Addon.getAddonInfo("profile")).decode("utf-8")
cacheDir = os.path.join(addon_data_dir, "cache")
tvdb_path = os.path.join(cacheDir, "TVDB")
tmdb_path = os.path.join(cacheDir, "TMDB")
UA = 'Mozilla/5.0 (Windows NT 6.1; rv:11.0) Gecko/20100101 Firefox/11.0'

class SmartRedirectHandler(urllib2.HTTPRedirectHandler):
	def http_error_301(self, req, fp, code, msg, headers):
		result = urllib2.HTTPRedirectHandler.http_error_301(self, req, fp, code, msg, headers)
		return result

	def http_error_302(self, req, fp, code, msg, headers):
		result = urllib2.HTTPRedirectHandler.http_error_302(self, req, fp, code, msg, headers)
		return result

def getFinalUrl(url):
	link = url
	try:
		req = urllib2.Request(url)
		req.add_header('User-Agent', UA)
		opener = urllib2.build_opener(SmartRedirectHandler())
		f = opener.open(req)
		link = f.url
		if link is None or link == '':
			link = url
	except Exception as ex:
		xbmc.log(str(ex), 3)
	return link
		
def OpenURL(url, headers={}, user_data={}, cookieJar=None, justCookie=False):
	if isinstance(url, unicode):
		url = url.encode('utf8')
	#url = urllib.quote(url, ':/')
	cookie_handler = urllib2.HTTPCookieProcessor(cookieJar)
	opener = urllib2.build_opener(cookie_handler, urllib2.HTTPBasicAuthHandler(), urllib2.HTTPHandler())
	if user_data:
		user_data = urllib.urlencode(user_data)
		req = urllib2.Request(url, user_data)
	else:
		req = urllib2.Request(url)
	req.add_header('Accept-encoding', 'gzip')
	for k, v in headers.items():
		req.add_header(k, v)
	if not req.headers.has_key('User-Agent') or req.headers['User-Agent'] == '':
		req.add_header('User-Agent', UA)
	response = opener.open(req)
	if justCookie == True:
		if response.info().has_key("Set-Cookie"):
			data = response.info()['Set-Cookie']
		else:
			data = None
	else:
		if response.info().get('Content-Encoding') == 'gzip':
			buf = StringIO(response.read())
			f = gzip.GzipFile(fileobj=buf)
			data = f.read().replace("\r", "")
		else:
			data = response.read().replace("\r", "")
	response.close()
	return data

def ReadFile(fileName):
	try:
		f = xbmcvfs.File(fileName)
		content = f.read().replace("\n\n", "\n")
		f.close()
	except Exception as ex:
		xbmc.log(str(ex), 3)
		content = ""
	return content

def SaveFile(fileName, text):
	try:
		f = xbmcvfs.File(fileName, 'w')
		f.write(text)
		f.close()
	except:
		return False
	return True
	
def ReadList(fileName):
	try:
		with open(fileName, 'r') as handle:
			content = json.load(handle)
	except Exception as ex:
		xbmc.log(str(ex), 5)
		if os.path.isfile(fileName):
			shutil.copyfile(fileName, "{0}_bak.txt".format(fileName[:fileName.rfind('.')]))
			xbmc.executebuiltin('Notification({0}, Cannot read file: "{1}". \nBackup createad, {2}, {3})'.format(AddonName, os.path.basename(fileName), 5000, icon))
		content=[]

	return content

def SaveList(filname, chList):
	try:
		with io.open(filname, 'w', encoding='utf-8') as handle:
			handle.write(unicode(json.dumps(chList, indent=4, ensure_ascii=False)))
		success = True
	except Exception as ex:
		xbmc.log(str(ex), 3)
		success = False
	return success

def OKmsg(title, line1, line2 = None, line3 = None):
	dlg = xbmcgui.Dialog()
	dlg.ok(title, line1, line2, line3)
	
def isFileNew(file, deltaInSec):
	lastUpdate = 0 if not os.path.isfile(file) else int(os.path.getmtime(file))
	now = int(time.time())
	return False if (now - lastUpdate) > deltaInSec else True 
	
def GetList(address, cache=0):
	if address.startswith('http'):
		fileLocation = os.path.join(cacheDir, hashlib.md5(address.encode('utf8')).hexdigest())
		fromCache = isFileNew(fileLocation, cache*60)
		if fromCache:
			response = ReadFile(fileLocation)
		else:
			response = OpenURL(address)
			if cache > 0:
				SaveFile(fileLocation, response)
	else:
		response = ReadFile(address.decode('utf-8'))
	return response
		
def plx2list(url, cache):
	response = GetList(url, cache)
	matches = re.compile("^background=(.*?)$",re.I+re.M+re.U+re.S).findall(response)
	background = None if len(matches) < 1 else matches[0]
	chList = [{"background": background}]
	matches = re.compile('^type(.*?)#$',re.I+re.M+re.U+re.S).findall(response)
	for match in matches:
		item=re.compile('^(.*?)=(.*?)$',re.I+re.M+re.U+re.S).findall("type{0}".format(match))
		item_data = {}
		for field, value in item:
			item_data[field.strip().lower()] = value.strip()
		item_data['group'] = 'Main'
		chList.append(item_data)
	return chList


def m3u2list(url, cache):
	response = GetList(url, cache)	
	matches=re.compile('^#EXTINF:-?[0-9]*(.*?),([^\"]*?)\n(.*?)$', re.M).findall(response)
	li = []
	for params, display_name, url in matches:
		item_data = {"params": params, "display_name": display_name.strip(), "url": url.strip()}
		li.append(item_data)
	chList = []
	for channel in li:
		item_data = {"display_name": (channel["display_name"].decode("utf-8", "ignore")), "url": channel["url"]}
		matches=re.compile(' (.*?)="(.*?)"').findall(channel["params"])
		for field, value in matches:
			item_data[field.strip().lower().replace('-', '_')] = value.strip()
		chList.append(item_data)
	return chList
	
	
	
def GetEncodeString(str):
	try:
		str = str.decode(chardet.detect(str)["encoding"]).encode("utf-8")
	except:
		try:
			str = str.encode("utf-8")
		except:
			pass
	return str

def DelFile(filname):
	try:
		if os.path.isfile(filname):
			os.unlink(filname)
	except Exception as ex:
		xbmc.log(str(ex), 3)
		

"""
Search for a movie / tvshow detail with The movie DB
"""		
def searchTMDB(item_name):
	api_key = Addon.getSetting("themoviedb_api_key")
	response = requests.get("https://api.themoviedb.org/3/search/movie?api_key=%s&query=%s" % (api_key, item_name))
	return response.json()



"""
Search for a movie / tvshow detail with The TV DB
"""		
def getTheTvDbToken():
	username = Addon.getSetting("thetvdb_username")
	user_key = Addon.getSetting("thetvdb_user_key")
	api_key =  Addon.getSetting("thetvdb_api_key")
	
	credentials={"apikey": api_key, "userkey": user_key,"username": username}
	r = requests.post('https://api.thetvdb.com/login', json=credentials)
	if r.status_code != 200:
		return  False
	
	response = r.json()
	return response["token"]



"""
Scan a given playlist index with the tv db
"""
def startTheTvDbScan(index, playlistsFile, token):

	search_series = "https://api.thetvdb.com/search/series?%s"
	search_poster = "https://api.thetvdb.com/series/%s/images/query?keyType=poster"
	search_fanarts = "https://api.thetvdb.com/series/%s/images/query?keyType=fanart"
	images_route = "https://www.thetvdb.com/banners/%s"
	
	# Checking base tvdb directory.
	if not os.path.exists(tvdb_path):
		os.mkdir(tvdb_path)
	
	tvdb_playlist_path = os.path.join(tvdb_path, str(index))

	# Remove all previous scans.
	if os.path.exists(tvdb_playlist_path):
		shutil.rmtree(tvdb_playlist_path)
	
	os.mkdir(tvdb_playlist_path)
	
	chList = ReadList(playlistsFile)
	item = chList[index]
	url = item["url"]
	content = m3u2list(url, cache=0)
	
	groups = []
	groups_infos = {}
	groups_404 = []
	headers = { "Accept": "application/json", "Accept-Language" : "%s" % Addon.getSetting("language_1").lower(), 'Authorization' : 'Bearer '+token, "User-agent": UA  }
	
	# Preparing progress bar.
	progress = xbmcgui.DialogProgress()
	progress.create(Addon.getLocalizedString(32028))
	step = 1
	not_found = 0
	
	for movie_item in content:
		
		# Handling "Cancel" action.
		if progress.iscanceled():
			break
		
		if not movie_item["group_title"] in groups:
			percent = (step * 100) / len(content)
			progress.update(int(percent), Addon.getLocalizedString(32029) + movie_item["group_title"], "", "")
			
			params = {"name" : movie_item["group_title"]}
			params = urllib.urlencode(params)
			res = requests.get(search_series % params, headers=headers)
			
			if not res.status_code == 200:
				# Then fallback language.
				headers["Accept-Language"] = "en"
				res = requests.get(search_series % params, headers=headers)
				
			res = res.json()
			try:
				aired = res["data"][0]["firstAired"] if ("firstAired" in res["data"][0] and len(res["data"][0]["firstAired"]) > 0) else "1800-01-01"
				idx = -1
			except KeyError:
				# Nothing found.
				
				if not movie_item["group_title"] in groups_404:
					not_found += 1
					progress.update(int(percent), "", "", Addon.getLocalizedString(32030) + str(not_found))
				groups_404.append(movie_item["group_title"])
				continue
				
			for data in res["data"]:
				cmp = data["firstAired"] if ("firstAired" in data and len(data["firstAired"]) > 0) else "1800-01-01"
				dtcmp = strptime2(cmp, "%Y-%m-%d")
				if strptime2(aired, "%Y-%M-%d").date() <= dtcmp.date():
					aired = cmp
					idx+=1
				
			# Getting poster and fanarts.
			progress.update(int(percent), Addon.getLocalizedString(32029) + movie_item["group_title"] + " - " + Addon.getLocalizedString(32031), "", "")
			poster = requests.get(search_poster % str(res["data"][idx]["id"]), headers=headers)
			fanarts = requests.get(search_fanarts % str(res["data"][idx]["id"]), headers=headers)
			
			if not poster.status_code == 200:
				# Fallback language for posters ... most of posters are availables in english.
				headers["Accept-Language"] = "en"
				poster = requests.get(search_poster % str(res["data"][idx]["id"]), headers=headers)
			
			poster = poster.json()
			try:
				poster = images_route % poster["data"][0]["thumbnail"]
			except KeyError:
				poster = ""
			
			if not fanarts.status_code == 200:
				fanarts = requests.get(search_fanarts % str(res["data"][idx]["id"]), headers=headers)
			
			fanarts = fanarts.json()
			try:
				fanarts = [images_route % fanarts["data"][i]["fileName"] for i in range(len(fanarts["data"]))]
			except KeyError:
				fanarts = []
			
			
			# Reset to the default language.
			headers["Accept-Language"] = Addon.getSetting("language_1").lower()
				
			# Registering values into an array.
			groups_infos[movie_item["group_title"]] = {"overview": res["data"][idx]["overview"], 
											           "firstAired": aired , 
											           "poster": poster, 
											           "fanarts": fanarts,
											           "tvdb_id": res["data"][idx]["id"] }
				
			groups.append(movie_item["group_title"])
		
		progress.update(int(percent), "", Addon.getLocalizedString(32032) + movie_item["group_title"], "")
		step += 1
			
	progress.close()
	
	# Savin this list to json
	with open(os.path.join(tvdb_playlist_path, "groups.json"), 'w') as outfile:
		json.dump(groups_infos, outfile)
		
	with open(os.path.join(tvdb_playlist_path, "groups.json"), 'w') as outfile:
		json.dump(groups_infos, outfile) 
		
		# item["name"]	
	"""
	# UNCOMMENT FOR DEBUG ONLY !!! 			
	for info in groups_infos:
		xbmc.log("\n\n----------------------------------------------------------------------------", xbmc.LOGERROR)
		xbmc.log("---- Key : %s" % groups_infos[info]["poster"], xbmc.LOGERROR)
		xbmc.log("First Aired : %s" % groups_infos[info]["firstAired"], xbmc.LOGERROR)
		xbmc.log("tvdb_id : %s" % groups_infos[info]["tvdb_id"], xbmc.LOGERROR)
		xbmc.log("overview : %s" % groups_infos[info]["overview"], xbmc.LOGERROR)
		xbmc.log("----------------------------------------------------------------------------", xbmc.LOGERROR)
	"""
	

"""
Return true if this m3u was scanned with the tv db function.
"""
def isScannedByTheTvDB(index):
	return os.path.exists(os.path.join(tvdb_path, str(index)))


"""
Remove the tv db data for given playlist index.
"""
def removeTheTvDBData(index):
	shutil.rmtree(os.path.join(tvdb_path, str(index)), ignore_errors=True)
	return True if not os.path.exists(os.path.join(tvdb_path, str(index))) else False

"""
Return true if this m3u was scanned with the movie db function.
"""
def isScannedByTheMovieDB(index):
	return os.path.exists(os.path.join(tmdb_path, str(index)))


"""
Remove the movie db data for given playlist index.
"""
def removeTheMovieDBData(index):
	shutil.rmtree(os.path.join(tmdb_path, str(index)), ignore_errors=True)
	return True if not os.path.exists(os.path.join(tmdb_path, str(index))) else False


"""
Load data from regisered the tv db nidex file
"""
def loadDataFromTheTvDB(index):
	jfile = os.path.join(tvdb_path, str(index))
	jfile = os.path.join(jfile, "groups.json")
	json_data=open(jfile).read()
	data = json.loads(json_data)
	return data


"""
Same than above for the movie db
"""
def loadDataFromTheMovieDB(index):
	jfile = os.path.join(tmdb_path, str(index))
	jfile = os.path.join(jfile, "groups.json")
	json_data=open(jfile).read()
	data = json.loads(json_data)
	return data


"""
Search for the right meta id.
"""
def searchMetaTVDBId(url, playlistsFile):
	json_playlists = open(playlistsFile).read()
	data = json.loads(json_playlists)
	i=0
	for playlist in data:
		if playlist["url"] == url:
			return i
		i += 1
	return None
	
"""
Compat for datetime.
"""
def strptime2(string_date, sformat):
	from datetime import datetime as dt
	try:
		res = dt.strptime(string_date, sformat)
	except TypeError:
		res = dt(*(time.strptime(string_date, sformat)[0:6]))
	return res
