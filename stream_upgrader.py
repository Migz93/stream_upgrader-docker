#!/usr/bin/python3
#-*- coding: utf-8 -*-

"""
The use case of this script is the following:
	When a local stream is started, check if a version of the media exists with a higher resolution.
	This version can exist in the same folder, in a different library or on a different plex server (backup server).
	When one is found, switch the stream to that file.
Requirements (python3 -m pip install [requirement]):
	requests
	PlexAPI
	websocket-client
Setup:
	Fill in the variables below.
	Then run the script. As long as the script is running, it will handle streams correctly.
	Because the script is a constant running script, you should run it in the background (as a service or a cron '@reboot' job for example; depends on the os how to do this so google it).
"""
#Copy config file from /config folder into /app folder
import os
os.system('cp /config/stream_upgrader_config.py /app/stream_upgrader_config.py')  
#Import config from file
import stream_upgrader_config
#Set variables from above file
plex_ip = stream_upgrader_config.plex_ip
plex_port = stream_upgrader_config.plex_port
plex_api_token = stream_upgrader_config.plex_api_token
process_audio = stream_upgrader_config.process_audio
process_video = stream_upgrader_config.process_video
process_priority = stream_upgrader_config.process_priority
backup_plex_ip = stream_upgrader_config.backup_plex_ip
backup_plex_port = stream_upgrader_config.backup_plex_port
backup_plex_api_token = stream_upgrader_config.backup_plex_api_token
in_library_source_ids = stream_upgrader_config.in_library_source_ids
in_library_target_ids = stream_upgrader_config.in_library_target_ids
in_library_remote_target_ids = stream_upgrader_config.in_library_remote_target_ids
in_media_rating_keys = stream_upgrader_config.in_media_rating_keys
in_resolutions = stream_upgrader_config.in_resolutions
in_channels = stream_upgrader_config.in_channels
audio_in_clients = stream_upgrader_config.audio_in_clients
video_in_clients = stream_upgrader_config.video_in_clients
ex_library_source_ids = stream_upgrader_config.ex_library_source_ids
ex_library_target_ids = stream_upgrader_config.ex_library_target_ids
ex_library_remote_target_ids = stream_upgrader_config.ex_library_remote_target_ids
ex_media_rating_keys = stream_upgrader_config.ex_media_rating_keys
ex_resolutions = stream_upgrader_config.ex_resolutions
ex_channels = stream_upgrader_config.ex_channels
audio_ex_clients = stream_upgrader_config.audio_ex_clients
video_ex_clients = stream_upgrader_config.video_ex_clients

import requests, argparse, time, logging, json
from plexapi.server import PlexServer
from plexapi.client import PlexClient

#required for alert listener so checking here
import websocket

def get_resolution(session, formatted=True):
	for media in session['Media']:
		if 'selected' in media.keys() and media['selected'] == True:
			res_number = int(media['videoResolution'].rstrip('k') + '000') if media['videoResolution'].endswith('k') else int(media['videoResolution'].rstrip('p'))
			if formatted == True:
				return res_number
			else:
				return media['videoResolution']
	logging.error('Could not find the current video stream')
	return 'not-found'

def video(session, part_id, media_output=None):
	set_stream_source = ''
	set_stream_count = 0
	res = get_resolution(session)
	if res == 'not-found':
		return
	logging.debug(f'Current resolution is {res}')
	if media_output == None:
		media_output = ssn.get(baseurl + session['key']).json()
	#check if there's a better version in a different file in the folder
	index = -1
	for media in media_output['MediaContainer']['Metadata'][0]['Media']:
		index += 1
		res_number = int(media['videoResolution'].rstrip('k') + '000') if media['videoResolution'].endswith('k') else int(media['videoResolution'].rstrip('p'))
		if ((set_stream_count > 0 and res_number > set_stream_count) or (set_stream_count == 0 and res_number > res)):
			set_stream_source = 'version'
			set_stream_count = res_number
			media_index = index

	#check if there's a better version in a different library
	lib_id = int(session['librarySectionID'])
	media_type = session['type']
	for search_result in ssn.get(f'http://{plex_ip}:{plex_port}/search', params={'query': session['title']}).json()['MediaContainer']['Metadata']:
		if search_result['librarySectionID'] != lib_id and search_result['type'] == media_type and search_result['title'] == session['title']:
			search_output = ssn.get(f'http://{plex_ip}:{plex_port}{search_result["key"]}').json()
			index = -1
			for media in search_output['MediaContainer']['Metadata'][0]['Media']:
				index += 1
				res_number = int(media['videoResolution'].rstrip('k') + '000') if media['videoResolution'].endswith('k') else int(media['videoResolution'].rstrip('p'))
				if ((set_stream_count > 0 and res_number > set_stream_count) or (set_stream_count == 0 and res_number > res)):
					set_stream_source = 'library'
					set_stream_count = res_number
					media_index = index
					media_key = search_result['key']

	#check if there's a better version inside a different file on a backup server (if setup)
	if backup == True:
		for search_result in backup_ssn.get(f'http://{backup_plex_ip}:{backup_plex_port}/search', params={'query': session['title']}).json()['MediaContainer']['Metadata']:
			if search_result['type'] == media_type and search_result['title'] ==  session['title']:
				search_output = backup_ssn.get(f'http://{backup_plex_ip}:{backup_plex_port}{search_result["key"]}').json()
				index = -1
				for media in search_output['MediaContainer']['Metadata'][0]['Media']:
					index += 1
					res_number = int(media['videoResolution'].rstrip('k') + '000') if media['videoResolution'].endswith('k') else int(media['videoResolution'].rstrip('p'))
					if ((set_stream_count > 0 and res_number > set_stream_count) or (set_stream_count == 0 and res_number > res)):
						set_stream_source = 'backup'
						set_stream_count = res_number
						media_index = index
						media_key = search_result['key']

	#change the stream if needed
	if set_stream_source and set_stream_count:
		#better stream found so change it
		if session['Player']['title'] == "Bedroom SHIELD":
			client_url="http://192.168.11.22:32500"
			client = PlexClient(server=plex, baseurl=client_url, token=plex_api_token)
		elif session['Player']['title'] == "Lounge SHIELD":
			client_url="http://192.168.11.21:32500"
			client = PlexClient(server=plex, baseurl=client_url, token=plex_api_token)
		else:
			client = plex.client(session['Player']['title'])
		view_offset = session['viewOffset']
		if set_stream_source == '':
			logging.info('No better video version was found')
		elif set_stream_source == 'version':
			logging.info(f'A better video stream has been found inside a different version of the file with the resolution of {set_stream_count}')
			key = session['key']
			media = plex.fetchItem(key)
			client.stop(mtype='video')
			client.playMedia(media, offset=view_offset, key=key, mediaIndex=media_index)
		elif set_stream_source == 'library':
			logging.info(f'A better video stream has been found inside a file in a different library with the resolution of {set_stream_count}')
			media = plex.fetchItem(media_key)
			client.stop(mtype='video')
			client.playMedia(media, offset=view_offset, key=media_key, mediaIndex=media_index)
		elif set_stream_source == 'backup':
			logging.info(f'A better video stream has been found inside a file on the backup server with the resolution of {set_stream_count}')
			media = backup_plex.fetchItem(media_key)
			client.stop(mtype='video')
			backup_client = backup_plex.client(session['Player']['title'])
			backup_client.playMedia(media, offset=view_offset, key=media_key, mediaIndex=media_index)

def process(data):
	# logging.debug(json.dumps(data, indent=4))
	if data['type'] == 'playing' and data['PlaySessionStateNotification'][0]['viewOffset'] < 500:
		#stream has started
		logging.debug(json.dumps(data, indent=4))
		data = data['PlaySessionStateNotification'][0]
		session_key = data['sessionKey']
		sessions = ssn.get(baseurl + '/status/sessions').json()
		for session in sessions['MediaContainer']['Metadata']:
			if session['sessionKey'] == session_key:
				if session['Session']['location'] != 'lan':
					logging.info('Detected session but it isn\'t streamed locally so ignoring')
					return
				logging.info('Detected local session so handling it')
				logging.debug(json.dumps(session, indent=4))
				#session is found, starting and local; check if it is allowed to be processed
				if (in_library_source_ids and not session['librarySectionID'] in in_library_source_ids) \
				or (in_media_rating_keys and not session['ratingKey'] in in_media_rating_keys) \
				or (in_resolutions and not get_resolution(session, formatted=False) in in_resolutions) \
				or (video_in_clients and not session['Player']['title'] in video_in_clients) \
				or (get_resolution(session, formatted=False) in ex_resolutions) \
				or (session['librarySectionID'] in ex_library_source_ids) \
				or (session['ratingKey'] in ex_media_rating_keys)
				else:
					process_audio = True
				if session['Player']['title'] in video_ex_clients:
					logging.info('Detected session falls under exclusion rules for video; ignoring video upgrade')
					process_video = False
				else:
					process_video = True
				if process_audio == False and process_video == False:
					return
				#process session if the script comes here
				media_output = ssn.get(baseurl + session['key']).json()
				part_id = ''
				for media in session['Media']:
					if 'selected' in media.keys() and media['selected'] == True:
						for part in media['Part']:
							if 'selected' in part.keys() and part['selected'] == True:
								part_id = part['id']
				if not part_id:
					logging.error('Failed to get part id')
					return
				logging.debug(json.dumps(media_output, indent=4))
				try:
					if process_audio == True and process_video == True:
						if process_priority == 'video':
							video(session, part_id, media_output=media_output)
						elif process_priority == 'audio':
							video(session, part_id, media_output=media_output)
						else:
							logging.error('Unknown process priority')
							exit(1)
					elif process_video == True:
						video(session, part_id, media_output=media_output)
				except Exception as e:
					logging.exception('Something went wrong: ')
				break
		else:
			logging.error('Detected session but couldn\'t find it in plex')
			return

if __name__  == '__main__':
	logging_level = logging.INFO
	logging.basicConfig(level=logging_level, format='[%(asctime)s][%(levelname)s] %(message)s', datefmt='%H:%M:%S %d-%m-20%y')
	logging.info('Upgrading streams when needed...')

	backup = True if backup_plex_ip and backup_plex_port and backup_plex_api_token else False
	ssn = requests.Session()
	ssn.headers.update({'Accept':'application/json'})
	ssn.params.update({'X-Plex-Token': plex_api_token})
	baseurl = f'http://{plex_ip}:{plex_port}'
	plex = PlexServer(baseurl, plex_api_token)
	logging.debug(f'baseurl = {baseurl}')
	if backup == True:
		backup_ssn = requests.Session()
		backup_ssn.headers.update({'Accept':'application/json'})
		backup_ssn.params.update({'X-Plex-Token': backup_plex_api_token})
		backup_baseurl = f'http://{backup_plex_ip}:{backup_plex_port}'
		backup_plex = PlexServer(backup_baseurl, backup_plex_api_token)
		logging.debug(f'backup baseurl = {backup_baseurl}')
	if in_library_source_ids: ex_library_source_ids = []
	if in_library_target_ids: ex_library_target_ids = []
	if in_library_remote_target_ids: ex_library_remote_target_ids = []
	if in_media_rating_keys: ex_media_rating_keys = []
	if in_resolutions: ex_resolutions = []
	if in_channels: ex_channels = []
	if audio_in_clients: audio_ex_clients = []
	if video_in_clients: video_ex_clients = []

	logging.debug(f'process_priority = {process_priority}')
	try:
		listener = plex.startAlertListener(callback=process)
		while True:
			time.sleep(1)
	except KeyboardInterrupt:
		listener.stop()
