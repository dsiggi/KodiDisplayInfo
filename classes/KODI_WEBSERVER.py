import urllib.request, urllib.error, urllib.parse, warnings
import json
from socket import timeout

warnings.filterwarnings("ignore", category=UserWarning, module='urllib')
import string


class KODI_WEBSERVER:
    ip_port = ""

    def __init__(self, helper, _ConfigDefault, draw_default):
        self.helper = helper
        self._ConfigDefault = _ConfigDefault
        self.draw_default = draw_default

        self.server = 'http://' + self.ip_port + self._ConfigDefault['KODI.webserver.host'] + ':' + self._ConfigDefault[
            'KODI.webserver.port']
        self.ip_port = self.server + '/jsonrpc'

        if self._ConfigDefault['KODI.webserver.user'] != "" and self._ConfigDefault['KODI.webserver.pass'] != "":
            self.passman = urllib.request.HTTPPasswordMgrWithDefaultRealm()
            self.passman.add_password(None, self.ip_port, self._ConfigDefault['KODI.webserver.user'],
                                      self._ConfigDefault['KODI.webserver.pass'])
            urllib.request.install_opener(
                urllib.request.build_opener(urllib.request.HTTPBasicAuthHandler(self.passman)))

    def getJSON(self, jsondata, get_parameter='?request='):
        self.draw_default.setInfoText("", self._ConfigDefault['color.white'])
        try:
            headers = {'content-type': 'application/json'}
            json_data = json.dumps(json.loads(jsondata))
            post_data = json_data.encode('utf-8')
            request = urllib.request.Request(self.ip_port + get_parameter, post_data, headers)

            result = urllib.request.urlopen(request, timeout=3).read()
            return json.loads(result.decode("utf-8"))
        except IOError:
            self.draw_default.setInfoText("NO KODI ACCESS!", self._ConfigDefault['color.red'])
            return json.loads('{"id":1,"jsonrpc":"2.0","result":[]}')
        except timeout:
            self.draw_default.setInfoText("NO KODI ACCESS!", self._ConfigDefault['color.red'])
            return json.loads('{"id":1,"jsonrpc":"2.0","result":[]}')

    def KODI_GetActivePlayers(self):
        try:
            parsed_json = self.getJSON('{"jsonrpc": "2.0", "method": "Player.GetActivePlayers", "id": 1}')
            try:
                return parsed_json['result'][0]['playerid'], parsed_json['result'][0]['type']
            except KeyError:
                return 0, ""
            except IndexError:
                return 0, ""
        except ValueError:
            self.helper.printout("[warning]    ", self._ConfigDefault['mesg.red'])
            print('Decoding JSON has failed')
            return ""

    # Artist, Album und Titel
    def KODI_GetItem(self, playerid, playertype):
        try:
            if playertype == "video":
                player_params_id = "VideoGetItem"
            elif playertype == "audio":
                player_params_id = "AudioGetItem"
            else:
                return ""

            parsed_json = self.getJSON(
                '{"jsonrpc": "2.0", "method": "Player.GetItem", "params": { "properties": ["artist", "album", "title"], "playerid": ' + str(
                    playerid) + ' }, "id": "' + str(player_params_id) + '"}')
            try:
                artist = parsed_json['result']['item']['artist']
                album = parsed_json['result']['item']['album']
                title = parsed_json['result']['item']['title']

                # Wandle artist von "Liste" zu "String"
                artist = str(artist)
                # Wenn der Künstlername ein ' enthält wird der Name wie folgt dargestellt ["Name' Name"]
                # Enthält der Name kein ' wird er wie folgt dargestllt ['Name']
                # Das heißt, der Name muss noch zurecht geschnitten werden
                artist = artist.replace("[\"", "")
                artist = artist.replace("\"]", "")
                artist = artist.replace("['", "")
                artist = artist.replace("']", "")

                if album == "":
                    album = parsed_json['result']['item']['label']

                if title == "":
                    title = parsed_json['result']['item']['label']

                return artist, album, title

            except KeyError as e:
                print("KeyError: " + str(e))
                return "" "" ""
            except IndexError as e:
                print("IndexError: " + str(e))
                return "" "" ""
        except ValueError:
            self.helper.printout("[warning]    ", self._ConfigDefault['mesg.red'])
            print('Decoding JSON has failed')
            return "" "" ""

    def KODI_GetProperties(self, playerid):
        try:
            parsed_json = self.getJSON(
                '{"jsonrpc": "2.0", "method": "Player.GetProperties", "params": { "playerid": ' + str(
                    playerid) + ', "properties": ["speed","time","totaltime"] }, "id": 1}')
            try:
                speed = parsed_json['result']['speed']
                media_time = [int(parsed_json['result']['time']['hours']),
                              int(parsed_json['result']['time']['minutes']),
                              int(parsed_json['result']['time']['seconds'])]
                media_timetotal = [int(parsed_json['result']['totaltime']['hours']),
                                   int(parsed_json['result']['totaltime']['minutes']),
                                   int(parsed_json['result']['totaltime']['seconds'])]
                return speed, media_time, media_timetotal
            except KeyError as e:
                print("KeyError: " + str(e))
                return 0, [0, 0, 0], [0, 0, 0]
            except IndexError as e:
                print("IndexError: " + str(e))
                return 0, [0, 0, 0], [0, 0, 0]

        except ValueError:
            self.helper.printout("[warning]    ", self._ConfigDefault['mesg.red'])
            print('Decoding JSON has failed')
            return 0, [0, 0, 0], [0, 0, 0]

    def KODI_GetCoverURL(self, playerid):
        try:
            parsed_json = self.getJSON('{"jsonrpc": "2.0", "method": "Player.GetItem", "params": { "playerid": ' + str(
                playerid) + ', "properties": ["thumbnail"] }, "id": 1}')
        except ValueError:
            self.helper.printout("[warning]    ", self._ConfigDefault['mesg.red'])
            print('Decoding JSON has failed')
            return ""

        url = parsed_json['result']['item']['thumbnail'][8:-1]
        return url

    def KODI_DownloadCover(self, url):
        if url == "":
            return ""
        else:
            if self._ConfigDefault['KODI.webserver.user'] != "" and self._ConfigDefault['KODI.webserver.pass'] != "":
                self.passman = urllib.request.HTTPPasswordMgrWithDefaultRealm()
                self.passman.add_password(None, self.server, self._ConfigDefault['KODI.webserver.user'],
                                          self._ConfigDefault['KODI.webserver.pass'])
                urllib.request.install_opener(
                    urllib.request.build_opener(urllib.request.HTTPBasicAuthHandler(self.passman)))

                # print(self.server + '/image/' + url)

                try:
                    cover = urllib.request.urlopen(self.server + '/image/' + url).read()
                except urllib.error.HTTPError as err:
                    cover = ""
                    self.helper.printout("[warning]    ", self._ConfigDefault['mesg.red'])
                    print(err.code)

                return cover

