# -*- coding: utf-8 -*-
# code by Avigdor and Nux007 (https://github.com/Nux007/Kodi-plugin.video.playlistLoader)
import urllib, urlparse, sys, xbmcplugin ,xbmcgui, xbmcaddon, xbmc, os, json, hashlib, uuid as random

AddonID = 'plugin.video.playlistLoader'
Addon = xbmcaddon.Addon(AddonID)
AddonName = Addon.getAddonInfo("name")
icon = Addon.getAddonInfo('icon')

addonDir = Addon.getAddonInfo('path').decode("utf-8")
iconsDir = os.path.join(addonDir, "resources", "images")

libDir = os.path.join(addonDir, 'resources', 'lib')
sys.path.insert(0, libDir)
import common

addon_data_dir = xbmc.translatePath(Addon.getAddonInfo("profile")).decode("utf-8")
cacheDir = os.path.join(addon_data_dir, "cache")
if not os.path.exists(cacheDir):
    os.makedirs(cacheDir)
    
playlistsFile = os.path.join(addon_data_dir, "playLists.txt")
vDirectoriesFile = os.path.join(addon_data_dir, "virtual_directoriesLists.txt")
tmpListFile = os.path.join(addon_data_dir, 'tempList.txt')
favoritesFile = os.path.join(addon_data_dir, 'favorites.txt')

if not (os.path.isfile(favoritesFile)):
    common.SaveList(favoritesFile, [])

if not (os.path.isfile(vDirectoriesFile)):
    common.SaveList(vDirectoriesFile, [])
    
    
makeGroups = Addon.getSetting("makeGroups") == "true"
    
    
def getLocaleString(id):
    return Addon.getLocalizedString(id).encode('utf-8')



def AddListItems(chList, addToVdir=True):
        
    cacheList = []
    i = 0

    for item in chList:
        mode = 1 if '.plx' in item["url"] else 2
        name = common.GetEncodeString(item["name"])
        
        image = item.get('image', '')
        uuid4 = item["uuid"]
        
        if image.encode("utf-8") is "" or image is None:
            image = os.path.join(iconsDir, "default-list-image.png")
        
        logos = item.get('logos', '')
        cacheMin = item.get('cache', '0')
        if item["url"].startswith('http'):
            cacheList.append(hashlib.md5(item["url"].encode("utf-8")).hexdigest())
        AddDir("[{0}]".format(name) ,item["url"].encode("utf-8"), mode, image.encode("utf-8"), logos.encode("utf-8"), index=i, uuid=uuid4.encode("utf-8"), cacheMin=cacheMin, addToVdir=addToVdir)
        i += 1

    for the_file in os.listdir(cacheDir):
        file_path = os.path.join(cacheDir, the_file)
        try:
            if os.path.isfile(file_path) and the_file not in cacheList:
                os.unlink(file_path)
        except Exception as ex:
            xbmc.log("{0}".format(ex), 3)


    
def Categories():
                
    '''
    Actions menu items.
    '''
    AddDir("[B]{0}: {1}[/B] - {2} ".format(getLocaleString(30036), getLocaleString(30037) if makeGroups else getLocaleString(30038) , getLocaleString(30039)), "setting" ,50 ,os.path.join(iconsDir, "setting.png"), isFolder=False)
    AddDir("[COLOR white][B][{0}][/B][/COLOR]".format(getLocaleString(30003)), "favorites" ,30 ,os.path.join(iconsDir, "bright_yellow_star.png"))
    AddDir("[COLOR yellow][B]{0}[/B][/COLOR]".format(getLocaleString(30001)), "newList" , 20, os.path.join(iconsDir, "NewList.ico"), isFolder=False)
    AddDir("[COLOR yellow][B]{0}[/B][/COLOR]".format(getLocaleString(30040)), "newDirectory" , 43, os.path.join(iconsDir, "New-folder.png"), isFolder=False)
    
    '''
    Contents
    '''
    # Displaying virtual directories.
    vDirs = common.ReadList(vDirectoriesFile)
    y = 0
    for vDir in vDirs:
        dir_icon = vDir["icon"].encode("utf-8") if not vDir["icon"].encode("utf-8") is "" else os.path.join(iconsDir, "default-folder-image.png")
        AddDir("[COLOR green][B]{0}[/B][/COLOR]".format(vDir["name"].encode("utf8")), "{0}".format(y) , 44 , dir_icon, uuid=vDir["uuid"].encode("utf-8"), isFolder=True)
        y += 1
    
    ignored = []
    for vdir in vDirs:
        if len(vdir["data"]) > 0:
            ignored += vdir["data"]
    
    i = 0
    chList = common.ReadList(playlistsFile) 
    addList = []
    try:	
        for uitem in chList:
            if "uuid" in uitem and not uitem["uuid"].encode("utf-8") in ignored:
                addList.append(chList[i])
            i += 1
    except:
        addList = chList
		
    AddListItems(addList)




def AddNewList():
    listName = GetKeyboardText(getLocaleString(30004)).strip()
    if len(listName) < 1:
        return
    listUrl = GetChoice(30002, 30005, 30006, 30016, 30017, fileType=1, fileMask='.plx|.m3u|.m3u8')
    if len(listUrl) < 1:
        return
    image = GetChoice(30022, 30022, 30022, 30024, 30025, 30021, fileType=2)
    logosUrl = '' if listUrl.endswith('.plx') else GetChoice(30018, 30019, 30020, 30019, 30020, 30021, fileType=0)
    if logosUrl.startswith('http') and not logosUrl.endswith('/'):
        logosUrl += '/'
    cacheInMinutes = GetNumFromUser(getLocaleString(30034), '0') if listUrl.startswith('http') else 0
    if cacheInMinutes is None:
        cacheInMinutes = 0
    chList = common.ReadList(playlistsFile)
    for item in chList:
        if item["url"].lower() == listUrl.lower():
            xbmc.executebuiltin('Notification({0}, "{1}" {2}, 5000, {3})'.format(AddonName, item["name"].encode("utf-8"), getLocaleString(30007), icon))
            return
    chList.append({"name": listName.decode("utf-8"), "url": listUrl, "image": image, "logos": logosUrl, "cache": cacheInMinutes, "uuid":str(random.uuid4())})
    if common.SaveList(playlistsFile, chList):
        xbmc.executebuiltin("XBMC.Container.Refresh()")



    

def GetChoice(choiceTitle, fileTitle, urlTitle, choiceFile, choiceUrl, choiceNone=None, fileType=1, fileMask=None, defaultText=""):
    choice = ''
    choiceList = [getLocaleString(choiceFile), getLocaleString(choiceUrl)]
    if choiceNone is not None:
        choiceList = [getLocaleString(choiceNone)] + choiceList
    method = GetSourceLocation(getLocaleString(choiceTitle), choiceList)    
    if choiceNone is None and method == 0 or choiceNone is not None and method == 1:
        if not defaultText.startswith('http'):
            defaultText = ""
        choice = GetKeyboardText(getLocaleString(fileTitle), defaultText).strip().decode("utf-8")
    elif choiceNone is None and method == 1 or choiceNone is not None and method == 2:
        if defaultText.startswith('http'):
            defaultText = ""
        choice = xbmcgui.Dialog().browse(fileType, getLocaleString(urlTitle), 'files', fileMask, False, False, defaultText).decode("utf-8")
    return choice
    
    
    
def RemoveFromLists(iuuid, listFile):
    # Removin the tv db and the movie db data first to ensure a clean file system.
    '''
    if common.isScannedByTheTvDB(index):
        common.removeTheTvDBData(index)
    
    if common.isScannedByTheMovieDB(index):
        common.removeTheMovieDBData(index)
    '''
    chList = common.ReadList(listFile) 
    vDirsList = common.ReadList(vDirectoriesFile)
    
    i = 0
    for playlist in chList:
        if playlist["uuid"].encode("utf-8") == iuuid.encode("utf-8"):
            del chList[i]
        i += 1
    
    # Removing from vdir lists.
    for vDir in vDirsList:
        i = 0
        for uuid4 in vDir["data"]:
            if iuuid.encode("utf-8") in uuid4.encode("utf-8"):
                del vDir["data"][i]
            i += 1
            
    common.SaveList(listFile, chList)
    common.SaveList(vDirectoriesFile, vDirsList)
    
    xbmc.executebuiltin("XBMC.Container.Refresh()")
    
    
def RemoveFromFavourites(index):
    
    favList = common.ReadList(favoritesFile) 
    if index < 0 or index >= len(favList):
        return
    del favList[index]
    common.SaveList(favoritesFile, favList)
    xbmc.executebuiltin("XBMC.Container.Refresh()")


            
def PlxCategory(url, cache):
    tmpList = []
    chList = common.plx2list(url, cache)
    background = chList[0]["background"]
    for channel in chList[1:]:
        iconimage = "" if not channel.has_key("thumb") else common.GetEncodeString(channel["thumb"])
        name = common.GetEncodeString(channel["name"])
        if channel["type"] == 'playlist':
            AddDir("[{0}]".format(name) ,channel["url"].encode("utf-8"), 1, iconimage, background=background.encode("utf-8"))
        else:
            AddDir(name, channel["url"].encode("utf-8"), 3, iconimage, isFolder=False, IsPlayable=True, background=background)
            tmpList.append({"url": channel["url"], "image": iconimage.decode("utf-8"), "name": name.decode("utf-8")})
            
    common.SaveList(tmpListFile, tmpList)
    
    
            
def m3uCategory(url, logos, cache, gListIndex=-1): 
      
    meta = None
    '''
    meta_id = common.searchMetaTVDBId(url, playlistsFile)
    if not meta_id is None:
        if common.isScannedByTheTvDB(meta_id):
            meta = common.loadDataFromTheTvDB(meta_id)

    elif common.isScannedByTheMovieDB(gListIndex):
        meta = common.loadDataFromTheMovieDB(gListIndex)
    '''
    tmpList = []
    chList = common.m3u2list(url, cache)
    groupChannels = []
    
    for channel in chList:
        if makeGroups:
            matches = [groupChannels.index(x) for x in groupChannels if len(x) > 0 and x[0].get("group_title", x[0]["display_name"]) == channel.get("group_title", channel["display_name"])]
        
        if makeGroups and len(matches) == 1:
            groupChannels[matches[0]].append(channel)
        else:
            groupChannels.append([channel])
    
    
    for channels in groupChannels:
        idx = groupChannels.index(channels)
        if gListIndex > -1 and gListIndex != idx:
            continue
        isGroupChannel = gListIndex < 0 and len(channels) > 1
        chs = [channels[0]] if isGroupChannel else channels
        
        for channel in chs:
            name = common.GetEncodeString(channel["display_name"]) if not isGroupChannel else common.GetEncodeString(channel.get("group_title", channel["display_name"]))
            plot = "" if meta is None else meta[channel["group_title"]]["overview"] if channel["group_title"] in meta else ""
            fanart = "" if meta is None else meta[channel["group_title"]]["fanarts"][0] if (channel["group_title"] in meta and len(meta[channel["group_title"]]["fanarts"]) > 0) else ""

            if isGroupChannel:
                name = '{0}'.format(name)
                chUrl = url
                try:
                    image = channel['tvg_logo'] if meta is None else meta[channel["group_title"]]["poster"] if channel["group_title"] in meta else channel['tvg_logo']
                except KeyError:
                    image = "DefaultTVShows.png"
                AddDir(name ,url, 10, index=idx, iconimage=image, plot=plot, fanart=fanart)
            else:
                chUrl = common.GetEncodeString(channel["url"])
                image = channel.get("tvg_logo", channel.get("logo", ""))
                if logos is not None and logos != ''  and image != "" and not image.startswith('http'):
                    image = logos + image
                AddDir(name, chUrl, 3, image, index=-1, isFolder=False, IsPlayable=True, plot=plot, fanart=fanart)
            tmpList.append({"url": chUrl.decode("utf-8"), "image": image.decode("utf-8"), "name": name.decode("utf-8")})
    
    common.SaveList(tmpListFile, tmpList)
        
        
        
        
def PlayUrl(name, url, iconimage=None):
    if url.startswith('acestream://'):
        url = 'plugin://program.plexus/?mode=1&url={0}&name={1}&iconimage={2}'.format(url, name, iconimage)
    else:
        url = common.getFinalUrl(url)
    xbmc.log('--- Playing "{0}". {1}'.format(name, url), 2)
    listitem = xbmcgui.ListItem(path=url)
    listitem.setInfo(type="Video", infoLabels={"mediatype": "movie", "Title": name })
        
    if iconimage is not None:
        try:
            listitem.setArt({'thumb' : iconimage})
        except:
            listitem.setThumbnailImage(iconimage)
    xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, listitem)



def AddDir(name, url, mode, iconimage='', logos='', index=-1, move=0, uuid='0', isFolder=True, IsPlayable=False, background=None, cacheMin='0', plot="", fanart="", addToVdir=True):
    urlParams = {'name': name, 'url': url, 'mode': mode, 'iconimage': iconimage, 'logos': logos, 'cache': cacheMin, 'uuid': uuid}
    
    liz = xbmcgui.ListItem(name, iconImage=iconimage, thumbnailImage=iconimage)
    liz.setInfo(type="Video", infoLabels={ "Title": name, "plot": plot, "plotoutline": plot, "tagline": plot})
    liz.setProperty("fanart_image", fanart)
    items = []
    
    listMode = 21 # Lists
    if IsPlayable:
        liz.setProperty('IsPlayable', 'true')
    if background != None:
        liz.setProperty('fanart_image', background)
    
    
    if mode == 1 or mode == 2:
        items = [
            (getLocaleString(30008), 'XBMC.RunPlugin({0}?index={1}&mode=22&uuid={2})'.format(sys.argv[0], index, uuid)),
            (getLocaleString(30026), 'XBMC.RunPlugin({0}?index={1}&mode=23&uuid={2})'.format(sys.argv[0], index, uuid)),
            (getLocaleString(30027), 'XBMC.RunPlugin({0}?index={1}&mode=24&uuid={2})'.format(sys.argv[0], index, uuid)),
            (getLocaleString(30028), 'XBMC.RunPlugin({0}?index={1}&mode=25&uuid={2})'.format(sys.argv[0], index, uuid))
        ]
        
        if mode == 2 and not url.endswith('.plx'):
            items.append((getLocaleString(30029), 'XBMC.RunPlugin({0}?index={1}&mode=26&uuid={2})'.format(sys.argv[0], index, uuid)))
        if url.startswith('http'):
            items.append((getLocaleString(30035), 'XBMC.RunPlugin({0}?index={1}&mode=28&uuid={2})'.format(sys.argv[0], index, uuid)))
                    
    elif mode == 3:
        items = [
            (getLocaleString(30009), 'XBMC.RunPlugin({0}?url={1}&mode=31&iconimage={2}&name={3}&uuid={4})'.format(sys.argv[0], urllib.quote_plus(url), iconimage, name, uuid))
        ]
    
    elif mode == 32:
        items = [
            (getLocaleString(30010), 'XBMC.RunPlugin({0}?index={1}&mode=33)'.format(sys.argv[0], index)),
            (getLocaleString(30026), 'XBMC.RunPlugin({0}?index={1}&mode=35)'.format(sys.argv[0], index)),
            (getLocaleString(30027), 'XBMC.RunPlugin({0}?index={1}&mode=36)'.format(sys.argv[0], index)),
            (getLocaleString(30028), 'XBMC.RunPlugin({0}?index={1}&mode=37)'.format(sys.argv[0], index))
        ]
        listMode = 38 # Favourits
    
    
    elif mode == 44:
        items = [
            (getLocaleString(30043), 'XBMC.RunPlugin({0}?index={1}&mode=46&uuid={2})'.format(sys.argv[0], index, uuid)),
            (getLocaleString(30044), 'XBMC.RunPlugin({0}?index={1}&mode=47&uuid={2})'.format(sys.argv[0], index, uuid))
        ]
        
    '''
    if common.isScannedByTheTvDB(index):
        tvdb_item = (getLocaleString(32033), 'XBMC.RunPlugin({0}?index={1}&mode=42&move=0)'.format(sys.argv[0], index))
    else:
        tvdb_item = (getLocaleString(30041), 'XBMC.RunPlugin({0}?index={1}&mode=41&move=0)'.format(sys.argv[0], index))
    '''
    
    if mode == 1 or mode == 2 or mode == 32:
        items += [
            # Moviedb temporary comment ! (getLocaleString(30040), 'XBMC.RunPlugin({0}?index={1}&mode=40&move=0)'.format(sys.argv[0], index)),
            #tvdb_item,
            (getLocaleString(30030), 'XBMC.RunPlugin({0}?index={1}&mode={2}&move=-1&uuid={3})'.format(sys.argv[0], index, listMode, uuid)),
            (getLocaleString(30031), 'XBMC.RunPlugin({0}?index={1}&mode={2}&move=1&uuid={3})'.format(sys.argv[0], index, listMode, uuid)),
            (getLocaleString(30032), 'XBMC.RunPlugin({0}?index={1}&mode={2}&move=0&uuid={3})'.format(sys.argv[0], index, listMode, uuid))
        ]
        
        if addToVdir:
            items += [
                (getLocaleString(30041), 'XBMC.RunPlugin({0}?index={1}&mode=45&move=-1&uuid={2})'.format(sys.argv[0], index, uuid)),
        ]
    
    if mode == 10:
        urlParams['index'] = index
    
        
    liz.addContextMenuItems(items)
        
    u = '{0}?{1}'.format(sys.argv[0], urllib.urlencode(urlParams))
    xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz, isFolder=isFolder)
    



def GetKeyboardText(title = "", defaultText = ""):
    keyboard = xbmc.Keyboard(defaultText, title)
    keyboard.doModal()
    text = "" if not keyboard.isConfirmed() else keyboard.getText()
    return text



def GetSourceLocation(title, chList):
    dialog = xbmcgui.Dialog()
    answer = dialog.select(title, chList)
    return answer
    
    
    
def AddFavorites(url, iconimage, name):
    #Checking if url already in list.
    favList = common.ReadList(favoritesFile)
    for item in favList:
        if item["url"].lower() == url.decode("utf-8").lower():
            xbmc.executebuiltin("Notification({0}, '{1}' {2}, 5000, {3})".format(AddonName, name, getLocaleString(30011), icon))
            return
    
    chList = common.ReadList(tmpListFile)    
    for channel in chList:
        if channel["name"].lower() == name.decode("utf-8").lower():
            url = channel["url"].encode("utf-8")
            iconimage = channel["image"].encode("utf-8")
            break
    if not iconimage:
        iconimage = ""
        
    data = {"url": url.decode("utf-8"), "image": iconimage.decode("utf-8"), "name": name.decode("utf-8")}
    favList.append(data)
    common.SaveList(favoritesFile, favList)
    xbmc.executebuiltin("Notification({0}, '{1}' {2}, 5000, {3})".format(AddonName, name, getLocaleString(30012), icon))



def AddNewDirectory():
    dir_name = GetKeyboardText(getLocaleString(30040), "My new directory name").decode("utf-8")
    dir_icon = xbmcgui.Dialog().browse(1, getLocaleString(30042), 'files').decode("utf-8")
    
    if dir_name != "":
        vDirs = common.ReadList(vDirectoriesFile)
        vDirs.append({"name" : dir_name, "data" : [], "icon" : dir_icon, "uuid": str(random.uuid4())})
        
        common.SaveList(vDirectoriesFile, vDirs)
        xbmc.executebuiltin("XBMC.Container.Refresh()")



def AddToDirectory(playlist_uuid):
    # if vdir is none, ask to choose one
    vdirs = common.ReadList(vDirectoriesFile)
        
    dialog = xbmcgui.Dialog()
    svdir = dialog.select("Choose the directory were to attach this playlist", [item["name"] for item in vdirs])
    vdirs[svdir]["data"].append(playlist_uuid)
    common.SaveList(vDirectoriesFile, vdirs)
    xbmc.executebuiltin("XBMC.Container.Refresh()")



def DeleteDirectory(iuuid, with_contents=False):
    vDirs = common.ReadList(vDirectoriesFile)
    y = 0
    for vdir in vDirs:
        if vdir["uuid"].encode("utf-8") == iuuid:
            if with_contents:
                contents = common.ReadList(playlistsFile)
                i = 0
                uuids = vdir["data"]
                uuids = [uuid4.encode("utf-8") for uuid4 in uuids]
                for content in contents:
                    if content["uuid"].encode("utf-8") in uuids:
                        del contents[i]
                    i += 1
                common.SaveList(playlistsFile, contents)
            del vDirs[y]
            common.SaveList(vDirectoriesFile, vDirs)
            xbmc.executebuiltin("XBMC.Container.Refresh()")
        y += 1
   
    
    
def ShowDirectoryContents(directory_uuid):
    vDirs = common.ReadList(vDirectoriesFile)
    dirFiles = lsDir(directory_uuid)
    
    if dirFiles is None:
        return
    
    chList = common.ReadList(playlistsFile)
    lPlaylists = []
    
    for pUuid in dirFiles:
        for playlist in chList:
            if pUuid.encode("utf-8") == playlist["uuid"].encode("utf-8"):
                lPlaylists.append(playlist) 
        
    AddListItems(lPlaylists, addToVdir=False)
    


def ListFavorites():
    AddDir("[COLOR yellow][B]{0}[/B][/COLOR]".format(getLocaleString(30013)), "favorites" ,34 ,os.path.join(iconsDir, "bright_yellow_star.png"), isFolder=False)
    chList = common.ReadList(favoritesFile)
    i = 0
    for channel in chList:
        AddDir(channel["name"].encode("utf-8"), channel["url"].encode("utf-8"), 32, channel["image"].encode("utf-8"), index=i, isFolder=False, IsPlayable=True)
        i += 1
    
        
def AddNewFavorite():
    chName = GetKeyboardText(getLocaleString(30014))
    if len(chName) < 1:
        return
    chUrl = GetKeyboardText(getLocaleString(30015))
    if len(chUrl) < 1:
        return
    image = GetChoice(30023, 30023, 30023, 30024, 30025, 30021, fileType=2)
        
    favList = common.ReadList(favoritesFile)
    for item in favList:
        if item["url"].lower() == chUrl.decode("utf-8").lower():
            xbmc.executebuiltin("Notification({0}, '{1}' {2}, 5000, {3})".format(AddonName, chName, getLocaleString(30011), icon))
            return
            
    data = {"url": chUrl.decode("utf-8"), "image": image, "name": chName.decode("utf-8")}
    
    favList.append(data)
    if common.SaveList(favoritesFile, favList):
        xbmc.executebuiltin("XBMC.Container.Refresh()")



def GetPlaylistIndex(iuuid, listFile):
    chList = common.ReadList(listFile)
    
    i = 0
    for playlist in chList:
        if playlist["uuid"].encode("utf-8") == iuuid.encode("utf-8"):
            return i
        i += 1
        
        
def lsDir(iuuid):
    chDirs = common.ReadList(vDirectoriesFile)
    for vdir in chDirs:
        if vdir["uuid"].encode("utf-8") == iuuid.encode("utf-8"):
            return vdir["data"]
    return None



def ChangeKey(iuuid, listFile, key, title, favourites=False):
    chList = common.ReadList(listFile)
    index = GetPlaylistIndex(iuuid, listFile) if not favourites else iuuid
    
    str = GetKeyboardText(getLocaleString(title), chList[index][key].encode("utf-8"))
    if len(str) < 1:
        return
        
    chList[index][key] = str.decode("utf-8")
    if common.SaveList(listFile, chList):
        xbmc.executebuiltin("XBMC.Container.Refresh()")
        
    
        
def ChangeChoice(iuuid, listFile, key, choiceTitle, fileTitle, urlTitle, choiceFile, choiceUrl, choiceNone=None, fileType=1, fileMask=None, favourites=False):
    index = GetPlaylistIndex(iuuid, listFile) if not favourites else iuuid
    chList = common.ReadList(listFile)
    defaultText = chList[index].get(key, "")
    str = GetChoice(choiceTitle, fileTitle, urlTitle, choiceFile, choiceUrl, choiceNone, fileType, fileMask, defaultText.encode("utf-8"))
    if key == "url" and len(str) < 1:
        return
    elif key == "logos" and str.startswith('http') and not str.endswith('/'):
        str += '/'
    chList[index][key] = str.decode("utf-8")
    if common.SaveList(listFile, chList):
        xbmc.executebuiltin("XBMC.Container.Refresh()")
    


def MoveInFavourites(index, step):
    
    theList = common.ReadList(favoritesFile)
    	
    if index + step >= len(theList) or index + step < 0:
        return
    if step == 0:
        step = GetIndexFromUser(len(theList), index)
    
    if step < 0:
        tempList = theList[0:index + step] + [theList[index]] + theList[index + step:index] + theList[index + 1:]
    elif step > 0:
        tempList = theList[0:index] + theList[index +  1:index + 1 + step] + [theList[index]] + theList[index + 1 + step:]
    else:
        return
    common.SaveList(favoritesFile, tempList)
    xbmc.executebuiltin("XBMC.Container.Refresh()")
      
    

def MoveInList(iuuid, step, listFile):
    
    def moveOnPlaylist(index, step, tList):
        tempList = None
        if index + step >= len(tList) or index + step < 0:
            return None
        
        if step == 0:
            step = GetIndexFromUser(len(tList), index)
    
        if step < 0:
            tempList = tList[0:index + step] + [tList[index]] + tList[index + step:index] + tList[index + 1:]
    
        elif step > 0:
            tempList = tList[0:index] + tList[index +  1:index + 1 + step] + [tList[index]] + tList[index + 1 + step:]
        
        else:
            return None
        
        return tempList
    
    
    theList = common.ReadList(listFile)
    
    # Checking that playlist is not in a directpry.
    dir = False
    vdirs = common.ReadList(vDirectoriesFile)
    for vdir in vdirs:
    	uuids4 = [uuid4.encode("utf-8") for uuid4 in vdir["data"]]
    	if iuuid.encode("utf-8") in uuids4:
    		dir = vdir
    
    if not dir is False:
        # Moving two sides, directories and global list ( in case of directory removal )
        dirFiles = lsDir(dir["uuid"])
        
        ffiles = [tfile for tfile in theList if tfile["uuid"].encode("utf-8") in dirFiles]
        rfiles = [tfile for tfile in theList if tfile["uuid"].encode("utf-8") not in dirFiles]
        
        ffiles = moveOnPlaylist(dirFiles.index(iuuid.encode("utf-8")), step, ffiles)
        
        if not ffiles is None:
            common.SaveList(listFile, rfiles + ffiles)
        
        # Movin it directory side.
        idx = vdirs.index(vdir)
        vdir["data"] = [item["uuid"].encode("utf-8") for item in ffiles]
        vdirs[idx] = vdir
        common.SaveList(vDirectoriesFile, vdirs)
            
    else:
        dirFiles = [item for data in vdirs for item in lsDir(data["uuid"])]
        dirItems    = [playlist for playlist in common.ReadList(listFile) if playlist["uuid"].encode("utf-8") in dirFiles]
        notDirFiles = [playlist for playlist in common.ReadList(listFile) if not playlist["uuid"].encode("utf-8") in dirFiles]
        
        idx = 0
        for playlist in notDirFiles:
            if playlist["uuid"].encode("utf-8") == iuuid:
                break
            idx += 1
        
        ffiles = moveOnPlaylist(idx, step, notDirFiles)
    
        if not ffiles is None:
            common.SaveList(listFile, dirItems + ffiles)
        
    xbmc.executebuiltin("XBMC.Container.Refresh()")
    
    '''
    # Moving themoviedb and thetvdb data if any.
    if common.isScannedByTheTvDB(index):
        common.removeTheTvDBData(index)
        common.OKmsg("The TV Db", getLocaleString(32036))
    
    if common.isScannedByTheMovieDB(index):
        common.removeTheMovieDBData(index)
        common.OKmsg("The TV Db", getLocaleString(32037))
    '''



def GetNumFromUser(title, defaultt=''):
    dialog = xbmcgui.Dialog()
    choice = dialog.input(title, defaultt=defaultt, type=xbmcgui.INPUT_NUMERIC)
    return None if choice == '' else int(choice)


def GetIndexFromUser(listLen, index):
    dialog = xbmcgui.Dialog()
    location = GetNumFromUser('{0} (1-{1})'.format(getLocaleString(30033), listLen))
    return 0 if location is None or location > listLen or location <= 0 else location - 1 - index


def ChangeCache(iuuid, listFile):
    index = GetPlaylistIndex(iuuid, listFile)
    chList = common.ReadList(listFile)
    defaultText = chList[index].get('cache', 0)
    cacheInMinutes = GetNumFromUser(getLocaleString(30034), str(defaultText)) if chList[index].get('url', '0').startswith('http') else 0
    if cacheInMinutes is None:
        return
    chList[index]['cache'] = cacheInMinutes
    if common.SaveList(listFile, chList):
        xbmc.executebuiltin("XBMC.Container.Refresh()")


def ToggleGroups():
    notMakeGroups = "false" if makeGroups else "true"
    Addon.setSetting("makeGroups", notMakeGroups)
    xbmc.executebuiltin("XBMC.Container.Refresh()")


params = dict(urlparse.parse_qsl(sys.argv[2].replace('?','')))
url = params.get('url')
logos = params.get('logos', '')
name = params.get('name')
iconimage = params.get('iconimage')
cache = int(params.get('cache', '0'))
index = int(params.get('index', '-1'))
move = int(params.get('move', '0'))
mode = int(params.get('mode', '0'))
uuid = params.get('uuid', '0')


if mode == 0:
    Categories()

elif mode == 1:
    PlxCategory(url, cache)
    
elif mode == 2 or mode == 10:
    m3uCategory(url, logos, cache, index)

elif mode == 3 or mode == 32:
    PlayUrl(name, url, iconimage)

elif mode == 20:
    AddNewList()
    
elif mode == 21:
	MoveInList(uuid, move, playlistsFile)

elif mode == 22:
    RemoveFromLists(uuid, playlistsFile)

elif mode == 23:
    ChangeKey(uuid, playlistsFile, "name", 30004)
    
elif mode == 24:
    ChangeChoice(uuid, playlistsFile, "url", 30002, 30005, 30006, 30016, 30017, None, 1, '.plx|.m3u|.m3u8')
    
elif mode == 25:
    ChangeChoice(uuid, playlistsFile, "image", 30022, 30022, 30022, 30024, 30025, 30021, 2)
    
elif mode == 26:
    ChangeChoice(uuid, playlistsFile, "logos", 30018, 30019, 30020, 30019, 30020, 30021, 0)
    
elif mode == 27:
    common.DelFile(playlistsFile)
    sys.exit()

elif mode == 28:
    ChangeCache(uuid, playlistsFile)

elif mode == 30:
    ListFavorites() 

elif mode == 31: 
    AddFavorites(url, iconimage, name)

elif mode == 33:
    RemoveFromFavourites(index)
    
elif mode == 34:
    AddNewFavorite()
    
elif mode == 35:
    ChangeKey(index, favoritesFile, "name", 30014, favourites=True)
    
elif mode == 36:
    ChangeKey(index, favoritesFile, "url", 30015, favourites=True)  

elif mode == 37:
    ChangeChoice(index, favoritesFile, "image", 30023, 30023, 30023, 30024, 30025, 30021, 2, favourites=True)

elif mode == 38:
    MoveInFavourites(index, move)
     
elif mode == 39:
    common.DelFile(favoritesFile)
    sys.exit()      
        
elif mode == 43:
    AddNewDirectory()

elif mode == 44:
    ShowDirectoryContents(uuid)

elif mode == 45:
    AddToDirectory(uuid)

elif mode == 46:
    DeleteDirectory(uuid, with_contents=True)

elif mode == 47:
    DeleteDirectory(uuid)
    

elif mode == 40:
    common.OKmsg("Playlist Loader", "Comming soon !!")
    """
    xbmc.log("The movie db scan request", xbmc.LOGERROR)
    # First make sure no the tv db data was here.
    if common.isScannedByTheTvDB(index):
        common.removeTheTvDBData(index)
    """    
elif mode == 41:
    if makeGroups:
        # First make sur no scan from the movie db was here.
        if common.isScannedByTheMovieDB(index):
            common.removeTheMovieDBData(index)
        
        token = common.getTheTvDbToken()
        if token is False:
            common.OKmsg("The TV Db 1", getLocaleString(30042))
        else:
            common.startTheTvDbScan(index, playlistsFile, token)
            xbmc.executebuiltin("XBMC.Container.Refresh()")
    else:
        common.OKmsg("The TV Db 2", getLocaleString(30043))

elif mode == 42:
    ok = common.removeTheTvDBData(index)
    if ok:
        common.OKmsg("The TV Db 3", getLocaleString(32034))
        xbmc.executebuiltin("XBMC.Container.Refresh()")
    else:
        common.OKmsg("The TV Db 4", getLocaleString(32035))

        
elif mode == 50:
    ToggleGroups()

xbmcplugin.endOfDirectory(int(sys.argv[1]))
