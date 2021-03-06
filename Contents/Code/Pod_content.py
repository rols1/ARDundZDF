# -*- coding: utf-8 -*-
# Pod_content.py	- Aufruf durch __init__.py/PodFavoritenListe 
#
# Die Funktionen dienen der Auswertung von Radio-Podcasts der Regionalsender. Zusätzlich
#	stehen die angezeigten Dateien für Downloads zur Verfügung (einzeln und gesamte Liste)
# Basis ist die Liste podcast-favorits.txt (Default/Muster im Ressourcenverzeichnis), die
# 	Liste enthält weitere  Infos zum Format und zu bereits unterstützten Podcast-Seiten
# 	- siehe nachfolgende Liste Podcast_Scheme_List
#
# Die Kurzform 'Podcast-Suche' deckt auch www.ardmediathek.de/radio ab - diese Funktion
#	macht die Radio-Podcasts aus dem Hauptmenü für Downloads verfügbar. Ein Beispiel
#	ist in der podcast-favorits.txt enthalten (s. Podcast-Suche: Quarks - Wissenschaft und mehr).


Podcast_Scheme_List = [		# Liste vorhandener Auswertungs-Schemata
# fehlendes http / https wird in Auswertungsschemata ersetzt
	'http://www.br-online.de', 'https://www.br.de',  
	'http://www.deutschlandfunk.de', 'http://mediathek.rbb-online.de',
	'//www.ardmediathek.de', 'http://www1.wdr.de/mediathek/podcast',
	'www1.wdr.de/mediathek/audio', 'http://www.ndr.de',
	'www.swr3.de', 'Podcast-Suche:']	

PREFIX 			= '/video/ardundzdf/Pod_content'			

####################################################################################################
@route(PREFIX + '/PodFavoriten')
def PodFavoriten(title, path, offset=0):
	Log('PodFavoriten'); Log(offset)
			
	rec_per_page = 24							# Anzahl pro Seite (www.br.de 24, ndr 10)
	title_org = title
	
	Scheme = ''
	for s in Podcast_Scheme_List:				# Prüfung: Schema für path vorhanden?
		Log(s); Log(path[:80])
		if path.find(s) >= 0:
			Scheme = s
			Log(Scheme)
			break			
	if Scheme == '':			
		msg='Auswertungs-Schema fehlt für Url:\n' +  path
		msg = msg.decode(encoding="utf-8", errors="ignore")
		Log(msg)
		return ObjectContainer(header='Error', message=msg)
		
	# Indices: 	0. Gesamtzahl, 1. Url, 2. Originaltitel, 3. Summary, 4. Datum,
	#			5. Dauer, 6. Größe, 7. Titel (zusammengesetzt), 8. Bild	, 9. Tagline
	#			10. PageControl
	POD_rec = get_pod_content(url=path, rec_per_page=rec_per_page, baseurl=Scheme, offset=offset)
	Log(len(POD_rec))
	if len(POD_rec) == 0:					# z.B. Fehlschlag bei Podcast-Suche 
		msg='Leider kein Treffer.'	
		return ObjectContainer(header='Error', message=msg)
	if 'Seite nicht' in POD_rec:			# error_txt aus get_page, einschl. path
		msg=POD_rec	
		msg = msg.decode(encoding="utf-8", errors="ignore")
		return ObjectContainer(header='Error', message=msg)
	
	rec_cnt = len(POD_rec)							# Anzahl gelesener Sätze
	start_cnt = int(offset) + 1						# Startzahl diese Seite
	end_cnt = int(start_cnt) + int(rec_per_page)-1	# Endzahl diese Seite

	Log(POD_rec[0][0])								# Gesamtzahl (0 bei Seitenkontrolle, außer br-online)
	if POD_rec[0][0] == 0:
		title2 = title
	else:
		title2 = "%s (gesamt: %s Podcasts)"	% (title, POD_rec[0][0])
		
	title2 = title2.decode(encoding="utf-8")
	oc = ObjectContainer(view_group="InfoList", title1='Favoriten', title2=title2, art = ObjectContainer.art)
	oc = home(cont=oc, ID='PODCAST')					# Home-Button
	
	if rec_cnt == 0:			
		msg='Keine Podcast-Daten gefunden. Url:\n' +  path
		msg = msg.decode(encoding="utf-8", errors="ignore")
		return ObjectContainer(header='Error', message=msg)
			
	url_list = []									# url-Liste für Sammel-Downloads (Dict['url_list'])	
	DLMultiple = True
	for rec in POD_rec:
		max_len=rec[0]
		url=rec[1]; summ=rec[3]; tagline=rec[9]; title=rec[7];
		if url == '':								# skip Satz ohne url - kann vorkommen
			continue
		if  url.endswith('.mp3') == False:			# Sammel-Downloads abschalten, falls Mehrfachseiten folgen
			DLMultiple = False
		title = unescape(title)
		url_list.append(url)
		img = R(ICON_NOTE)	
		# Log(title); Log(summ[:40]); Log(url); Log(DLMultiple) # bei Bedarf
		if rec[8]:
			img = rec[8]
		if rec[10]:										# Schemata mit Seitenkontrolle?
			if rec[10] == 'htmlpages':					# Bsp. RBB u.a. - versch. Formate:
				pagepos = url.find('page')				# 	..page-1.html, ..page1.html, ..mcontent=page.1
				page = url[pagepos:]
				pagenr = (page.replace('-', '').replace('.', '').replace('html', '').replace('page', ''))
				
			if 'jsonpages' in rec[10]:					# Bsp. jsonpages|53|3.0|24|1 (total,pages,items,current)
				current = rec[10].split('|')[-1]
				pagenr = current			
			Log('pagenr: %s' % pagenr) 
			oc.add(DirectoryObject(key=Callback(PodFavoriten, title=title, path=url, offset=pagenr), 
				title=title, tagline=path, summary=summ,  thumb=R(ICON_STAR)))
		else:
			# nicht direkt zum TrackObject, sondern zu SingleSendung, um Downloadfunktion zu nutzen
			# oc.add(CreateTrackObject(url=url, title=title, summary=summ, fmt='mp3', thumb=img))
			oc.add(DirectoryObject(key=Callback(SingleSendung, path=url, title=title, thumb=img, 
				duration='leer', tagline=tagline, ID='PODCAST', summary=summ), title=title, tagline=tagline, 
				summary=summ, thumb=img))
		
	# Mehr Seiten anzeigen:					
	if rec[10] == '' and rec[11] == '':		# nur bei Podcasts ohne Seitenkontrolle (rec[11]='skip_more')	
		Log(rec_cnt);Log(offset);Log(max_len)
		if (rec_cnt + int(offset)) < int(max_len): 
			new_offset = rec_cnt + int(offset)
			Log(new_offset); Log(path)
			title=title_org.decode(encoding="utf-8", errors="ignore")
			summ = 'Mehr (insgesamt ' + str(max_len) + ' Podcasts)'
			summ = summ.decode(encoding="utf-8", errors="ignore")
			oc.add(DirectoryObject(key=Callback(PodFavoriten, title=title, path=path, offset=new_offset), 
				title=title, tagline='Favoriten', summary=summ,  thumb=R(ICON_MEHR)))
			
	if DLMultiple == True and len(oc) > 1:			# True z.B. bei "Weiter zu Seite 1"
		# Sammel-Downloads - alle angezeigten Favoriten-Podcasts downloaden?
		#	für "normale" Podcasts erfolgt die Abfrage in SinglePage
		title='Achtung! Alle angezeigten Podcasts ohne Rückfrage speichern?'
		title = title.decode(encoding="utf-8", errors="ignore")
		summ = 'Download von insgesamt %s Podcasts' % len(POD_rec)	
		Dict['url_list'] = url_list			# als Dict - kann zu umfangreich sein als url-Parameter
		Dict['POD_rec'] = POD_rec	
		Dict.Save()
		oc.add(DirectoryObject(key=Callback(DownloadMultiple, key_url_list='url_list', key_POD_rec='POD_rec'), 
			title=title, tagline='', summary=summ,  thumb=R(ICON_DOWNL)))
				 
	return oc

#------------------------	
@route(PREFIX + '/DownloadMultiple')
# Sammeldownload lädt alle angezeigten Podcasts herunter.
# Im Gegensatz zum Einzeldownload wird keine Textdatei zum Podcast angelegt.
# DownloadExtern kann nicht von hier aus verwendet werden, da der wiederholte Einzelaufruf 
# 	von Curl kurz hintereinander auf Linux Prozessleichen hinterlässt: curl (defunct)
# Zum Problem command-line splitting (curl-Aufruf) und shlex-Nutzung siehe:
# 	http://stackoverflow.com/questions/33560364/python-windows-parsing-command-lines-with-shlex
# Das Problem >curl "[Errno 36] File name too long"< betrifft die max. Pfadlänge auf verschiedenen
#	Plattformen (Posix-Standard 4096). Teilweise ist die Pfadlänge manuell konfigurierbar.
#	Die hier gewählte platform-abhängige Variante funktioniert unter Linux + Windows (Argumenten-Länge
#	bis ca. 4 KByte getestet) 
# Rücksprung-Problem: der Button DownloadsTools ruft zwar die Funktion DownloadsTools auf, führt aber vorher
#	noch einmal den Curl-Aufruf aus mit kompl. Download - keine Abhilfe mit no_cache=True im ObjectContainer
#	oder Parameter time=time.time() für dem Callback DownloadsTools.
#
#	01.09.2018: s.a. Doku in LiveRecord. Die Lösungen / Anpassungen für PHT  wurden hier analog umgesetzt. 
#		PHT: bei Plugin-Timeout zeigt PHT zuerst den Callback-Button und sprint anschließend wieder zum 
#			Funktionskopf.
#		
def DownloadMultiple(key_url_list, key_POD_rec):						# Sammeldownloads
	Log('DownloadMultiple'); 
	import shlex											# Parameter-Expansion
	
	url_list = Dict[key_url_list]
	POD_rec = Dict[key_POD_rec]
	
	if Dict['PIDcurlPOD']:								# ungewollten Wiedereintritt abweisen 
		Log('PIDcurlPOD: %s' % Dict['PIDcurlPOD'])
		Log('PIDcurlPOD = %s | Blocking DownloadMultiple' % Dict['PIDcurlPOD'])
		Dict['PIDcurlPOD'] = ''						# löschen für manuellen Aufruf 
		# Für PHT Info erst hier nach autom. Wiedereintritt nach Popen möglich:
		title1 = 'curl/wget: Download erfolgreich gestartet'
		if 'Home Theater' in str(Client.Platform):	# GetDirectory failed nach Info
			return ObjectContainer(header='Info', message=title1)
		return DownloadsTools()

	oc = ObjectContainer(view_group="InfoList", title1='Favoriten', title2='Sammel-Downloads', 
		art = ObjectContainer.art, no_cache=True)
	oc = home(cont=oc, ID='PODCAST')						# Home-Button
	
	rec_len = len(POD_rec)
	AppPath = Prefs['pref_curl_path']
	AppPath = os.path.abspath(AppPath)
	dest_path = Prefs['pref_curl_download_path']
	curl_param_list = '-k '									# schaltet curl's certificate-verification ab

	if os.path.exists(AppPath)	== False:					# Existenz Curl prüfen
		msg='curl nicht gefunden'
		return ObjectContainer(header='Error', message=msg)		
	if os.path.isdir(dest_path)	== False:			
		msg='Downloadverzeichnis nicht gefunden: ' + path	# Downloadverzeichnis prüfen
		return ObjectContainer(header='Error', message=msg)	
	
	i = 0
	for rec in POD_rec:										# Parameter-Liste für Curl erzeugen
		i = i + 1
		#if  i > 2:											# reduz. Testlauf
		#	break
		url = rec[1]; title = rec[7]
		title = unescape(title)								# schon in PodFavoriten, hier erneut nötig 
		if 	Prefs['pref_generate_filenames']:				# Dateiname aus Titel generieren
			dfname = make_filenames(title) + '.mp3'
		else:												# Bsp.: Download_2016-12-18_09-15-00.mp4  oder ...mp3
			now = datetime.datetime.now()
			mydate = now.strftime("%Y-%m-%d_%H-%M-%S")	
			dfname = 'Download_' + mydate + '.mp3'

		# Parameter-Format: -o Zieldatei_kompletter_Pfad Podcast-Url -o Zieldatei_kompletter_Pfad Podcast-Url ..
		curl_fullpath = os.path.join(dest_path, dfname)		 
		curl_fullpath = os.path.abspath(curl_fullpath)		# os-spezischer Pfad
		curl_param_list = curl_param_list + ' -o '  + curl_fullpath + ' ' + url
		
	cmd = AppPath + ' ' + curl_param_list
	Log(len(cmd))
	
	Log(sys.platform)
	if sys.platform == 'win32':								# s. Funktionskopf
		args = cmd
	else:
		args = shlex.split(cmd)								# ValueError: No closing quotation (1 x, Ursache n.b.)
	Log(len(args))											# hier Ende Log-Ausgabe bei Plugin-Timeout, Download
															#	läuft aber weiter.
	try:
		Dict['PIDcurlPOD'] = ''
		sp = subprocess.Popen(args, shell=False)			# shell=True entf. hier nach shlex-Nutzung	
		output,error = sp.communicate()						#  output,error = None falls Aufruf OK
		Log('call = ' + str(sp))	
		if str(sp).find('object at') > 0:  				# Bsp.: <subprocess.Popen object at 0x7fb78361a210>
			Dict['PIDcurlPOD'] = sp.pid					# PID zum Abgleich gegen Wiederholung sichern
			Log('PIDcurlPOD neu: %s' % Dict['PIDcurlPOD'])
			msgH = 'curl: Download erfolgreich gestartet'	# trotzdem Fehlschlag möglich, z.B. ohne Schreibrecht
			Log(msgH)								
			summary = 'Anzahl der Podcast: %s' % rec_len
			tagline = 'zurück zu den Download-Tools'.decode(encoding="utf-8", errors="ignore")
			# PHT springt hier zurück an den Funktionskopf - Info dort. Bei Plugin-Timeout zeigt PHT zuerst
			#	den Callback-Button und sprint anschließend wieder zum Funktionskopf.
			oc.add(DirectoryObject(key = Callback(DownloadsTools), title='Download-Tools', summary=summary, 
				tagline=tagline, thumb=R(ICON_OK)))		
			return oc				
		else:
			raise Exception('Start von curl fehlgeschlagen')			
	except Exception as exception:
		msg = str(exception)
		Log(msg)		
		title1 = "Fehler: %s" % msg
		title1 = title1.decode(encoding="utf-8")
		summ	= 'zur Sender Auswahl'
		tagline='Download fehlgeschlagen'
		# bei Fehlschlag gibt PHT die message aus (im Gegensatz zu oben):
		if 'Home Theater' in str(Client.Platform):	# GetDirectory failed nach Info
			return ObjectContainer(header='Fehler', message=title1)
		oc.add(DirectoryObject(key = Callback(DownloadsTools), title=title1, 
				 thumb=R('icon-error.png'), summary=summ, tagline=tagline))		
		return oc
		
	return oc

#------------------------	
def get_pod_content(url, rec_per_page, baseurl, offset):
	Log('get_pod_content'); Log(rec_per_page); Log(baseurl); Log(offset);

	if baseurl.startswith('Podcast-Suche:'):		# Kurzform Podcast-Suche -> Link erzeugen
		query = url.split(':')[1]
		query = query.strip()
		query = query.replace(' ', '+')			# Leer-Trennung = UND-Verknüpfung bei Podcast-Suche 
		query = urllib2.quote(query, "utf-8")
		Log('query: %s' %  query)
		path =  BASE_URL  + POD_SEARCH
		url = path % query
		baseurl = BASE_URL						# 'http://www.ardmediathek.de'
		
	url = unescape(url)							# einige url enthalten html-escapezeichen
	if baseurl == 'https://www.br.de':			# Umlenkung auf API-Seite beim
		if int(offset) == 0:					# 	ersten Aufruf - Erzeugung Seiten-Urls in Scheme_br_online
			ID = url.split('/')[-1]				# ID am Pfadende
			url = baseurl + '/mediathek/podcast/api/podcasts/%s/episodes?items_per_page=24&page=1'	% ID
	
	page, err = get_page(path=url)				# Absicherung gegen Connect-Probleme
	if page == '':
		Log(err)
		return err
	Log(len(page))

	# baseurl aus Podcast_Scheme_List (PodFavoriten)
	if baseurl == 'https://www.br.de':
		return Scheme_br_online(page, rec_per_page, offset, page_href=url)
	if 'www.swr3.de' in baseurl:
		return Scheme_swr3(page, rec_per_page, offset)
	if baseurl == 'http://www.deutschlandfunk.de':
		return Scheme_deutschlandfunk(page, rec_per_page, offset)
	if baseurl == 'http://mediathek.rbb-online.de':
		sender = ''								# mp3-url mittels documentId zusammensetzen
		if url.find('documentId=24906530') > 0:
			sender = 'Fritz'					# mp3-url auf Ziel-url ermitteln
		return Scheme_rbb(page, rec_per_page, offset, sender, baseurl)
		
	if baseurl == 'http://www1.wdr.de/mediathek/podcast' or baseurl == 'www1.wdr.de/mediathek/audio':
		return Scheme_wdr(page, rec_per_page, offset)
	if baseurl == 'http://www.ndr.de':
		return Scheme_ndr(page, rec_per_page, offset)
		
	if '//www.ardmediathek.de' in baseurl:
		return Scheme_ARD(page, rec_per_page, offset, baseurl)
		
#------------------------
def Scheme_br_online(page, rec_per_page, offset, page_href=None):	# Schema www.br-online.de, ab Mai 2018 json-format
# 	Aufruf von get_pod_content - Umsetzung auf API-Call dort
	Log('Scheme_br_online'); Log(offset)
	jsonObject = json.loads(page)
	max_len = jsonObject["result"]["meta"]["episodes"]["total"]
	Log(max_len)
	tagline = ''; pagecontrol= '';img=''
	
	max_len 		= jsonObject["result"]["meta"]["episodes"]["total"]
	page_cnt		= jsonObject["result"]["meta"]["episodes"]["pages"]
	items_per_page 	= jsonObject["result"]["meta"]["episodes"]["items_per_page"]
	current			= jsonObject["result"]["meta"]["episodes"]["current_page"]
	# Bsp. jsonpages|53|3.0|24|1 (total,pages,items,current):
	pagecontrol = 'jsonpages|%s|%s|%s|%s' % (max_len,page_cnt,items_per_page,current)	
	POD_rec = []			# Datensaetze gesamt (1. Dim.)
	
	if int(offset) == 0:							# 1. Durchlauf - Seitenkontrolle 
		pages = int(page_cnt)						# 3.0 -> 3
		Log(pages)	
		pagenr = 1									# Start
		for i in range(1, pages+1):
			single_rec = []							# Datensatz einzeln (2. Dim.)
			Log(page_href); 	
			# max_len = 0							# br_online: Gesamt in title2 in PodFavoriten zeigen
			url = page_href.split('&page=')			# Part mit Seitennr. entfernen
			url = url[0]
			url = url + "&page=%s"	% pagenr
									
			title = 'Weiter zu Seite %s' % pagenr
			dach = jsonObject["result"]["episodes"][0]["podcast"]["title"]	# Titel Sendereihe
			summ = dach; title_org = ''; datum = ''; dauer = ''; groesse = ''; 
			pagenr = pagenr + 1
			
			Log(title); Log(url); 
			title=title.decode(encoding="utf-8", errors="ignore")
			summ=summ.decode(encoding="utf-8", errors="ignore")
			
			# Indices: 	0. Gesamtzahl, 1. Url, 2. Originaltitel, 3. Summary, 4. Datum,
			#			5. Dauer, 6. Größe, 7. Titel (zusammengesetzt), 8. Bild, 9. Tagline
			#			10. PageControl, 11. 'skip_more' oder leer
			single_rec.append(max_len); single_rec.append(url); single_rec.append(title_org); 
			single_rec.append(summ); single_rec.append(datum); single_rec.append(dauer); 
			single_rec.append(groesse); single_rec.append(title); single_rec.append(img);
			single_rec.append(tagline); single_rec.append(pagecontrol);single_rec.append('');
			POD_rec.append(single_rec)
		return POD_rec	
	
	pagecontrol = ''				# überspringt Seitenkontrolle in PodFavoriten
	for i, episodes in enumerate(jsonObject["result"]["episodes"]):
		cnt = int(i) + int(offset)
		# Log(cnt); Log(i)
		if int(cnt) >= max_len:			# Gesamtzahl überschritten?
			break
		if i >= rec_per_page:			# Anzahl pro Seite überschritten?
			break

		single_rec = []		# Datensatz einzeln (2. Dim.)
		title_org = episodes["title"]
		summ = episodes["podcast"]["summary"]
		url = episodes["enclosure"]["url"]
		img =  episodes["image"]
		
		poddatum = episodes["publication_date"]		#Bsp.  "2018-05-09T14:35:00Z"
		datum = datetime.datetime.strptime(poddatum, "%Y-%m-%dT%H:%M:%SZ").strftime("%d.%m.%Y, %H:%M Uhr")			
		dauer = episodes["duration"]
		groesse = episodes["enclosure"]["length"]
		
		title = '%s | %s' % (datum, title_org)
		if groesse:
			groesse = humanbytes(groesse)
			title = '%s | %s' % (title, groesse)
		
		Log(title); Log(summ[:80]); Log(url); Log(pagecontrol); 
		title=title.decode(encoding="utf-8", errors="ignore")
		summ=summ.decode(encoding="utf-8", errors="ignore")
		
		# Indices: 	0. Gesamtzahl, 1. Url, 2. Originaltitel, 3. Summary, 4. Datum,
		#			5. Dauer, 6. Größe, 7. Titel (zusammengesetzt), 8. Bild, 9. Tagline
		#			10. PageControl, 11. 'skip_more' oder leer
		single_rec.append(max_len); single_rec.append(url); single_rec.append(title_org); 
		single_rec.append(summ); single_rec.append(datum); single_rec.append(dauer); 
		single_rec.append(groesse); single_rec.append(title); single_rec.append(img);
		single_rec.append(tagline); single_rec.append(pagecontrol); single_rec.append('skip_more');
		POD_rec.append(single_rec)
		
	Log(len(POD_rec))	
	return POD_rec
	
# ------------------------
def Scheme_swr3(page, rec_per_page, offset):	# Schema SWR
	Log('Scheme_swr3')
	sendungen = blockextract('<li id=\"audio-', page)
	max_len = len(sendungen)					# Gesamtzahl gefundener Sätze
	Log(max_len)
	tagline = ''; pagecontrol= '';
	
	POD_rec = []			# Datensaetze gesamt (1. Dim.)
	for i in range(len(sendungen)):
		cnt = int(i) + int(offset)
		# Log(cnt); Log(i)
		if int(cnt) >= max_len:			# Gesamtzahl überschritten?
			break
		if i >= rec_per_page:			# Anzahl pro Seite überschritten?
			break
		s = sendungen[cnt]
		
		single_rec = []		# Datensatz einzeln (2. Dim.)
		title_org = stringextract('data-title="', '\"', s) 
		title = title_org.strip()
		url = stringextract('data-mp3="', '"', s) 
		img =  stringextract('data-src="', '"', s) 						# Index-Bild
		img_alt =  stringextract('alt="', '"', s) 						# Bildbeschr. - nicht verwendet
		
		datum = stringextract('datePublished">', '</time>', s) 			# im Titel ev. bereits vorhanden
		dauer = stringextract('duration" content=', '/div>', s) 		# "P0Y0M0DT0H0M34.000S">0:34</div>
		dauer = stringextract('>', '<', dauer) 
		groesse = stringextract('data-ati-size="', '"', s)
		groesse = float(int(groesse)) / 1000000						# Konvert. nach MB, auf 2 Stellen gerundet
		groesse = '%.2f MB' % groesse
		
		title = ' %s | %s' % (title, datum)
		summ = ' Dauer %s | Größe %s' % (dauer, groesse)
		
		Log(title); Log(summ); Log(url); 
		title=title.decode(encoding="utf-8", errors="ignore")
		summ=summ.decode(encoding="utf-8", errors="ignore")
		
		# Indices: 	0. Gesamtzahl, 1. Url, 2. Originaltitel, 3. Summary, 4. Datum,
		#			5. Dauer, 6. Größe, 7. Titel (zusammengesetzt), 8. Bild, 9. Tagline
		#			10. PageControl, 11. 'skip_more' oder leer
		single_rec.append(max_len); single_rec.append(url); single_rec.append(title_org); 
		single_rec.append(summ); single_rec.append(datum); single_rec.append(dauer); 
		single_rec.append(groesse); single_rec.append(title); single_rec.append(img);
		single_rec.append(tagline); single_rec.append(pagecontrol); single_rec.append('skip_more');
		POD_rec.append(single_rec)
		
	Log(len(POD_rec))	
	return POD_rec
		
# ------------------------
def Scheme_deutschlandfunk(page, rec_per_page, offset):		# Schema www.deutschlandfunk.de, XML-Format
	Log('Scheme_deutschlandfunk')
	sendungen = blockextract('<item>', page)
	max_len = len(sendungen)								# Gesamtzahl gefundener Sätze
	Log(max_len)
	tagline = ''; pagecontrol= '';
	
	POD_rec = []			# Datensaetze gesamt (1. Dim.)
	for i in range(len(sendungen)):
		cnt = int(i) + int(offset)
		# Log(cnt); Log(i)
		if int(cnt) >= max_len:			# Gesamtzahl überschritten?
			break
		if i >= rec_per_page:			# Anzahl pro Seite überschritten?
			break
		s = sendungen[cnt]
		
		single_rec = []		# Datensatz einzeln (2. Dim.)
		title_org = stringextract('<title>', '</title>', s) 
		title = title_org.strip()
		summ = stringextract('vspace="4"/>', '<br', s) 			# direkt nach Bildbeschreibung
		summ = summ.strip()
		url = stringextract('<enclosure url="', '"', s) 
		img =  stringextract('<img src="', '\"', s) 
		img_alt =  stringextract('alt="', '\"', s) 						# 
		
		author = stringextract('itunes:author>', '</itunes:author>', s) 
		datum = stringextract('<pubDate>', '</pubDate>', s)
		datum = datum.replace('+0200', '')	
		dauer = stringextract('duration>', '</itunes', s) 
		groesse = stringextract('length="', '"', s) 
		groesse = float(int(groesse)) / 1000000						# Konvert. nach MB, auf 2 Stellen gerundet
		groesse = '%.2f MB' % groesse
		
		title = ' %s | %s' % (title, datum)
		summ = ' Autor %s | Datum %s | Größe %s' % (author, datum, groesse)
		
		Log(title); Log(summ); Log(url); 
		title=title.decode(encoding="utf-8", errors="ignore")
		summ=summ.decode(encoding="utf-8", errors="ignore")
		
		# Indices: 	0. Gesamtzahl, 1. Url, 2. Originaltitel, 3. Summary, 4. Datum,
		#			5. Dauer, 6. Größe, 7. Titel (zusammengesetzt), 8. Bild, 9. Tagline
		#			10. PageControl, 11. 'skip_more' oder leer
		single_rec.append(max_len); single_rec.append(url); single_rec.append(title_org); 
		single_rec.append(summ); single_rec.append(datum); single_rec.append(dauer); 
		single_rec.append(groesse); single_rec.append(title); single_rec.append(img);
		single_rec.append(tagline); single_rec.append(pagecontrol); single_rec.append('skip_more');
		POD_rec.append(single_rec)
		
	Log(len(POD_rec))	
	return POD_rec
		
# ------------------------
def Scheme_rbb(page, rec_per_page, offset,sender, baseurl):		# Schema mediathek.rbb-online.de
# 	Besonderheit: offset = Seitennummer
# 	1. Aufruf kommt mit ..&mcontent=page.1
	Log('Scheme_rbb'); Log(offset); Log(sender)

	POD_rec = []			# Datensaetze gesamt (1. Dim.)
	pages = blockextract('entry" data-ctrl-contentLoader-source', page)		# Seiten-Urls
	max_len = len(pages)
	Log(max_len)
	page_href = baseurl + stringextract('href="', '">', pages[0])
	page_href = page_href.split('mcontent=')[0]		# Basis-url ohne Seitennummer
	tagline = ''; pagecontrol= '';
	
	if offset == '0':								# 1. Durchlauf - Seitenkontrolle 
		pagenr = 1
		for p in pages:
			single_rec = []							# Datensatz einzeln (2. Dim.)
			max_len = 0								# -> POD_rec[0][0] 	-> title2 in PodFavoriten
			url = page_href + 'mcontent=page.' + str(pagenr)	 # url mit Seitennr, ergänzen
			title = 'Weiter zu Seite %s' % pagenr
			img = '';					
			pagecontrol= 'htmlpages';			# 'PageControl' steuert 
			summ = ''; title_org = ''; datum = ''; dauer = ''; groesse = ''; 
			pagenr = pagenr + 1
			
			Log(title); Log(url); 
			title=title.decode(encoding="utf-8", errors="ignore")
			summ=summ.decode(encoding="utf-8", errors="ignore")
			
			# Indices: 	0. Gesamtzahl, 1. Url, 2. Originaltitel, 3. Summary, 4. Datum,
			#			5. Dauer, 6. Größe, 7. Titel (zusammengesetzt), 8. Bild, 9. Tagline
			#			10. PageControl, 11. 'skip_more' oder leer
			single_rec.append(max_len); single_rec.append(url); single_rec.append(title_org); 
			single_rec.append(summ); single_rec.append(datum); single_rec.append(dauer); 
			single_rec.append(groesse); single_rec.append(title); single_rec.append(img);
			single_rec.append(tagline); single_rec.append(pagecontrol); single_rec.append('');
			POD_rec.append(single_rec)
		return POD_rec
	
	sendungen = blockextract('class="teaser"', page)  # Struktur wie ARD-Mediathek
	del sendungen[0]; del sendungen[1]			# Sätze 1 + 2 keine Podcasts
	max_len = len(sendungen)					# Gesamtzahl gefundener Sätze dieser Seite
	Log(max_len)
	
	for i in range(len(sendungen)):
		cnt = int(i) 		# + int(offset) Offset entfällt (pro Seite Ausgabe aller Sätze)
		# Log(cnt); Log(i)
		#if int(cnt) >= max_len:		# Gesamtzahl überschritten? - entf. hier
		s = sendungen[cnt]
		
		single_rec = []		# Datensatz einzeln (2. Dim.)
		title_org = stringextract('dachzeile">', '</p>', s) 
		summ = stringextract('subtitle">', '<', s) 		# Bsp.: Do 13.04.17 00:00 | 03:28 min	
		headline = stringextract('headline">', '</h4>', s)  # häufig mehr Beschreibung als Headline
		
		url_local = stringextract('<a href="', '"', s) 		# Homepage der Sendung
		url_local = baseurl + url_local
		url_local = decode_url(url_local)					# f%C3%BCr -> für, 	&amp; -> &
		Log(url_local)
		try:												# mp3-url auf Ziel-url ermitteln
			url_local = unescape(url_local)
			page, err = get_page(path=url_local)			# Absicherung gegen Connect-Probleme
			url = stringextract('<div data-ctrl-ta-source', 'target="_blank"', page)
			url = stringextract('a href="', '"', url)
			Log(url)		
		except:	
			url=''											

		if url.endswith('.mp3') == False:					# mp3-url mittels documentId zusammensetzen
			documentId =  re.findall("documentId=(\d+)", url_local)[0]
			url = baseurl + '/play/media/%s?devicetype=pc&features=hls' % documentId
			Log('hlsurl: ' + url)
			try:
				url_content, err = get_page(path=url)				# Textdatei, Format ähnlich parseLinks_Mp4_Rtmp
				url = stringextract('stream":"', '"}', url_content) # geändert 24.01-2018	
			except:
				url=''
		Log(url)
			
		text = stringextract('urlScheme', '/noscript', s)
		img, img_alt = img_urlScheme(text, 320, ID='PODCAST') # img_alt nicht verwendet
		
		author = ''	  										# fehlt
		groesse = ''	  										# fehlt
		datum = summ.split('|')[0]
		dauer = summ.split('|')[1]
				
		title = ' %s | %s  | %s' % (title_org, datum, dauer)
		summ = headline
		summ = unescape(summ)
		
		Log(title); Log(summ); Log(url); 
		title=title.decode(encoding="utf-8", errors="ignore")
		summ=summ.decode(encoding="utf-8", errors="ignore")
		
		# Indices: 	0. Gesamtzahl, 1. Url, 2. Originaltitel, 3. Summary, 4. Datum,
		#			5. Dauer, 6. Größe, 7. Titel (zusammengesetzt), 8. Bild, 9. Tagline
		#			10. PageControl, 11. 'skip_more' oder leer
		single_rec.append(max_len); single_rec.append(url); single_rec.append(title_org); 
		single_rec.append(summ); single_rec.append(datum); single_rec.append(dauer); 
		single_rec.append(groesse); single_rec.append(title); single_rec.append(img);
		single_rec.append(tagline);  single_rec.append(pagecontrol); single_rec.append('skip_more');
		POD_rec.append(single_rec)
		
	Log(len(POD_rec))	
	return POD_rec
		
# ------------------------
def Scheme_wdr(page, rec_per_page, offset):		# Schema WDR, XML-Format
	Log('Scheme_wdr')
	sendungen = blockextract('<item>', page)
	max_len = len(sendungen)									# Gesamtzahl gefundener Sätze
	Log(max_len)
	title_channel = stringextract('<title>', '</title>', page)	# Channel-Titel
	tagline = ''; pagecontrol= '';
	
	POD_rec = []			# Datensaetze gesamt (1. Dim.)
	for i in range(len(sendungen)):
		cnt = int(i) + int(offset)
		# Log(cnt); Log(i)
		if int(cnt) >= max_len:			# Gesamtzahl überschritten?
			break
		if i >= rec_per_page:			# Anzahl pro Seite überschritten?
			break
		s = sendungen[cnt]
		
		single_rec = []		# Datensatz einzeln (2. Dim.)
		title_org = stringextract('<title>', '</title>', s) 
		title = title_org.strip()
		summ = stringextract('<description>', '</description>', s) 			
		summ = summ.strip()
		summ = unescape(summ)
		url = stringextract('<enclosure url="', '"', s) 
		img =  stringextract('<img src="', '\"', s) 
		img_alt =  stringextract('alt="', '\"', s) 						# 
		
		author = stringextract('itunes:author>', '</itunes:author>', s) 
		datum = stringextract('<pubDate>', '</pubDate>', s)
		datum = datum.replace('GMT', '')	
		dauer = stringextract('duration>', '</itunes', s) 
		groesse = stringextract('length="', '"', s) 					# fehlt
		#groesse = float(int(groesse)) / 1000000						# Konvert. nach MB, auf 2 Stellen gerundet
		#groesse = '%.2f MB' % groesse
		
		title = ' %s | %s'			% (title, datum)
		summ = ' Autor %s | %s' 	% (author, summ)
		
		Log(title); Log(summ); Log(url); 
		title=title.decode(encoding="utf-8", errors="ignore")
		summ=summ.decode(encoding="utf-8", errors="ignore")
		
		# Indices: 	0. Gesamtzahl, 1. Url, 2. Originaltitel, 3. Summary, 4. Datum,
		#			5. Dauer, 6. Größe, 7. Titel (zusammengesetzt), 8. Bild, 9. Tagline
		#			10. PageControl, 11. 'skip_more' oder leer
		single_rec.append(max_len); single_rec.append(url); single_rec.append(title_org); 
		single_rec.append(summ); single_rec.append(datum); single_rec.append(dauer); 
		single_rec.append(groesse); single_rec.append(title); single_rec.append(img);
		single_rec.append(tagline); single_rec.append(pagecontrol); single_rec.append('');
		POD_rec.append(single_rec)
		
	Log(len(POD_rec))	
	return POD_rec
		
# ------------------------
def Scheme_ndr(page, rec_per_page, offset):		# Schema NDR - ab 05.2018 Verwendung der xml-Seiten
	Log('Scheme_ndr'); Log(offset);Log(len(page))

	baseurl = 'http://www.ndr.de'
	POD_rec = []			# Datensaetze gesamt (1. Dim.)	
	tagline = ''; pagecontrol= '';	

	pages = stringextract('<div class="pagination">', 'googleoff:', page)	# Seiten-Urls für Seitenkontrolle
	if len(pages) > 0:							# Seite ohne Seitenkontrolle möglich
		page_href = baseurl + stringextract('href="', '-', pages)				# zum Ergänzen mit 1.html, 2.html usw.
		# Log(page_href)	
		entry_type = '_page-'
		pages = pages.split(entry_type)				# .. href="/ndr2/programm/podcast2958_page-6.html" title="Zeige Seite 6">			
		# Log(pages[1])
		page_nr = []
		for line in pages:	
			nr = re.search('(\d+)', line).group(1) # Bsp. 6.html
			page_nr.append(nr)	
		page_nr.sort()
		Log(page_nr)
		page_nr = repl_dop(page_nr)					# Doppler entfernen (zurück-Seite, nächste-Seite)
		last_page = page_nr[-1]						# letzte Seite
		Log(last_page)
		
		if offset == '0':							# 1. Durchlauf - Seitenkontrolle:
			pagenr = 0
			# Log(last_page)
			for i in range(int(last_page)):
				title_org=''; 
				# max_len = last_page
				max_len = 0							# -> POD_rec[0][0] 	-> title2 in PodFavoriten
				single_rec = []						# Datensatz einzeln (2. Dim.)
				pagenr = i + 1
				if pagenr >= last_page:
					break
				url = page_href + '-' + str(pagenr) + '.html' 	# url mit Seitennr. ergänzen
				title = 'Weiter zu Seite %s' % pagenr
				img = '';						
				pagecontrol= 'htmlpages';					# 'PageControl' steuert in PodFavoriten
				summ = ''; title_org = ''; datum = ''; dauer = ''; groesse = ''; 
				
				Log(title); Log(url); Log(pagenr); Log(last_page)
				title=title.decode(encoding="utf-8", errors="ignore")
				summ=summ.decode(encoding="utf-8", errors="ignore")
				
				# Indices: 	0. Gesamtzahl, 1. Url, 2. Originaltitel, 3. Summary, 4. Datum,
				#			5. Dauer, 6. Größe, 7. Titel (zusammengesetzt), 8. Bild, 9. Tagline
				#			10. PageControl, 11. 'skip_more' oder leer
				single_rec.append(max_len); single_rec.append(url); single_rec.append(title_org); 
				single_rec.append(summ); single_rec.append(datum); single_rec.append(dauer); 
				single_rec.append(groesse); single_rec.append(title); single_rec.append(img);
				single_rec.append(tagline); single_rec.append(pagecontrol); single_rec.append('')
				POD_rec.append(single_rec)
			return POD_rec							# Rückkehr aus Seitenkontrolle
		
												# 2. Durchlauf - Inhalte der einzelnen Seiten:
	sendungen = blockextract('class="module list w100">', page) 
	if len(sendungen) > 1:
		if sendungen[2].find('urlScheme') >= 0:								# 2 = Episodendach
			text = stringextract('urlScheme', '/noscript', sendungen[2])
			img_src_header, img_alt_header = img_urlScheme(text, 320, ID='PODCAST') 
			teasertext = stringextract('class="teasertext">', '</p>', sendungen[2])
			Log(img_src_header);Log(img_alt_header);Log(teasertext);
	
	
	max_len = len(sendungen)					# Gesamtzahl gefundener Sätze dieser Seite
	Log(max_len)
	
	for i in range(len(sendungen)):
		# cnt = int(i) 		# + int(offset) Offset entfällt (pro Seite Ausgabe aller Sätze)
		# Log(cnt); Log(i)
		# if int(cnt) >= max_len:		# Gesamtzahl überschritten? - entf. hier
		# s = sendungen[cnt]
		s = sendungen[i]
		# Log(s)
		
		single_rec = []		# Datensatz einzeln (2. Dim.)
		title_org = stringextract('title="Zum Audiobeitrag: ', '"', s) 
		subtitle =  stringextract('subline">', '<', s)			# Bsp.: 06.04.2017 06:50 Uhr
		if subtitle == '':
			subtitle =  stringextract('subline date">', '<', s)	# Bsp.: date">18.05.2017 06:50 Uhr
		summ = stringextract('<p>', '<a title', s) 			
		dachzeile = ''										# fehlt		
		headline = ''										# fehlt	
		
		pod = stringextract('podcastbuttons">', 'class="button"', s)
		pod = pod.strip()
		Log(pod[40:])
		url = stringextract('href=\"', '\"', pod)		# kompl. Pfad
		if url == '':									# kein verwertbarer Satz 
			continue			
			
		img = ''											# fehlt	
		author = ''	  										# fehlt
		groesse = ''	  									# fehlt
		datum = subtitle
		dauer = stringextract('class="cta " >', '</a>', s) 
		
		title = '%s | %s' % (subtitle, title_org)
		tagline = '%s | %s' % (subtitle, dauer)
						
		Log(title); Log(summ); Log(url); 
		title=title.decode(encoding="utf-8", errors="ignore")
		summ=summ.decode(encoding="utf-8", errors="ignore")
		tagline=tagline.decode(encoding="utf-8", errors="ignore")
		
		# Indices: 	0. Gesamtzahl, 1. Url, 2. Originaltitel, 3. Summary, 4. Datum,
		#			5. Dauer, 6. Größe, 7. Titel (zusammengesetzt), 8. Bild, 9. Tagline
		#			10. PageControl, 11. 'skip_more' oder leer
		single_rec.append(max_len); single_rec.append(url); single_rec.append(title_org); 
		single_rec.append(summ); single_rec.append(datum); single_rec.append(dauer); 
		single_rec.append(groesse); single_rec.append(title); single_rec.append(img);
		single_rec.append(tagline); single_rec.append(pagecontrol); single_rec.append('skip_more')
		POD_rec.append(single_rec)
		
	Log(len(POD_rec))	
	return POD_rec	
		
# ------------------------
def Scheme_ARD(page, rec_per_page, offset,baseurl):		# Schema ARD = www.ardmediathek.de
# 	Schema für die Podcastangebote der ARD-Mediathek
# 	1. Aufruf kommt mit ..&mcontents=page.1 (nicht ..content=..)
	Log('Scheme_ARD'); Log(offset);

	POD_rec = []			# Datensaetze gesamt (1. Dim.)
	
	# Bsp. ['"/suche?searchText=quarks+wissenschaft&amp;sort=date&amp;pod&amp;source=radio&amp;mresults']:
	pages =  re.findall(r'<a href=(.*?)=page.', page)
	max_len = len(pages)								# max_len=letzte Seitennr.							
	Log(len(pages))
	if pages:	
		page_href = pages[0].replace('"', '')			# Pfad aus 1. Pagelink ermitteln
		page_href = page_href.replace('+', '%2B')		# ARD-Fehler in Links: %2B (Leerz.) wird durch + ersetzt
		Log(page_href)

	if baseurl.startswith('http') == False:				# https ergänzen (http bei ard obsolet)
		baseurl = 'https:' + baseurl
		
	tagline = ''; pagecontrol= '';
	# für Seiten mit offset=0 aber ohne Seitenkontrolle direkt weiter bei sendungen
	if offset == '0' and pages:							# 1. Durchlauf - Seitenkontrolle
		pagenr = 1
		for p in pages:
			single_rec = []								# Datensatz einzeln (2. Dim.)
			max_len = 0									# -> POD_rec[0][0] 	-> title2 in PodFavoriten
			url = baseurl + page_href + "=page.%d" % pagenr	 # url mit Seitennr. ergänzen
			url = unescape(url)
			url = url.replace('+', '%2B')				# ARD-Fehler in Links: %2B (Leerz.) wird durch + ersetzt
			title = 'Weiter zu Seite %s' % pagenr
			img = '';						
			pagecontrol= 'htmlpages';				# 'PageControl' steuert 
			summ = ''; title_org = ''; datum = ''; dauer = ''; groesse = ''; 
			pagenr = pagenr + 1
			
			Log(title); Log('url: %s' % url); 
			title=title.decode(encoding="utf-8", errors="ignore")
			summ=summ.decode(encoding="utf-8", errors="ignore")
			
			# Indices: 	0. Gesamtzahl, 1. Url, 2. Originaltitel, 3. Summary, 4. Datum,
			#			5. Dauer, 6. Größe, 7. Titel (zusammengesetzt), 8. Bild, 9. Tagline
			#			10. PageControl, 11. 'skip_more' oder leer
			single_rec.append(max_len); single_rec.append(url); single_rec.append(title_org); 
			single_rec.append(summ); single_rec.append(datum); single_rec.append(dauer); 
			single_rec.append(groesse); single_rec.append(title); single_rec.append(img);
			single_rec.append(tagline); single_rec.append(pagecontrol); single_rec.append('');
			POD_rec.append(single_rec)
		return POD_rec							# Rückkehr aus Seitenkontrolle
		
												# 2. Durchlauf - bzw. ohne Seitenkontrolle direkt -
												# Inhalte der einzelnen Seiten:	
	sendungen = blockextract('class="teaser"', page)  # Struktur für Podcasts + Videos ähnlich
	img_src_header=''; img_alt_header=''; teasertext=''
	max_len = len(sendungen)					# Gesamtzahl gefundener Sätze dieser Seite
	#Log('sendungen[0]: ' + sendungen[0])		# bei Bedarf
	if sendungen[0].find('urlScheme') >= 0:								# [0] = Episodendach
		text = stringextract('urlScheme', '/noscript', sendungen[0])
		img_src_header, img_alt_header = img_urlScheme(text, 320, ID='PODCAST') 
		teasertext = stringextract('class="teasertext">', '</p>', sendungen[0])
		max_len = str(max_len - 1)				# sonst klappt's nicht mit 'Mehr'-Anzeige
		Log(img_src_header);Log(img_alt_header);Log(teasertext);
	
	Log('max_len: ' + str(max_len))
	
	for i in range(len(sendungen)):
		s = sendungen[i]
		Log(len(s));    # Log(s)
		
		single_rec = []		# Datensatz einzeln (2. Dim.)
		title_org = stringextract('dachzeile">', '</p>', s) 
		subtitle =  stringextract('subtitle">', '<', s)		# Bsp.: 06.02.2017 | 1 Min.
		summ = stringextract('teasertext">', '<', s) 			
		dachzeile = stringextract('dachzeile">', '</p>', s)  # Sendereihe		
		headline = stringextract('headline">', '</h4>', s)  # Titel der einzelnen Sendung
		
		url_local = stringextract('<a href="', '"', s) 		# Homepage der Sendung
		if url_local == '' or url_local.find('documentId=') == -1:	# kein verwertbarer Satz 
			continue
		url_local = baseurl + url_local
		Log('url_local: ' + url_local)
		documentId =  re.findall("documentId=(\d+)", url_local)[0]
		url = baseurl + '/play/media/%s?devicetype=pc&features=hls' % documentId 	# Quelldatei Podcast
		url_content, err = get_page(path=url)			# Textdatei, Format ähnlich parseLinks_Mp4_Rtmp
		Log('url_content: ' + url_content[:60])
		if url_content == '':
			Log('url_content leer')
			return err
		url = stringextract('stream":"', '"', url_content) # manchmal 2 identische url
		Log('mp3-url: ' + url)	
			
		text = stringextract('urlScheme', '/noscript', s)
		img, img_alt = img_urlScheme(text, 320, ID='PODCAST') # img_alt nicht verwendet
		if img == '':										# Episodenbild 
			img =img_src_header 
		
		author = '';  groesse = ''  						# fehlen hier
		datum = '';  dauer = '';			
		if subtitle.find('|') > 0:
			datum = subtitle.split('|')[0]
			dauer = subtitle.split('|')[1]
		
		if dachzeile:
			title = ' %s | %s ' % (dachzeile, headline)
			summ =  ' %s | %s' % (datum, dauer)
		else:
			title = ' %s | %s | %s' % (headline, datum, dauer)
			if teasertext:
				summ = teasertext
		title = title.replace('|  |', '')						# Datum + Dauer können fehlen
				
		tagline = teasertext									# aus Episodendach, falls vorh.
		tagline = unescape(tagline)
		summ = unescape(summ)
		
		Log(title); Log(summ); Log(url); 
		title=title.decode(encoding="utf-8", errors="ignore")
		summ=summ.decode(encoding="utf-8", errors="ignore")
		tagline=tagline.decode(encoding="utf-8", errors="ignore")
		
		# Indices: 	0. Gesamtzahl, 1. Url, 2. Originaltitel, 3. Summary, 4. Datum,
		#			5. Dauer, 6. Größe, 7. Titel (zusammengesetzt), 8. Bild, 9. Tagline
		#			10. PageControl, 11. 'skip_more' oder leer
		single_rec.append(max_len); single_rec.append(url); single_rec.append(title_org); 
		single_rec.append(summ); single_rec.append(datum); single_rec.append(dauer); 
		single_rec.append(groesse); single_rec.append(title); single_rec.append(img);
		single_rec.append(tagline); single_rec.append(pagecontrol); single_rec.append('skip_more');
		POD_rec.append(single_rec)
		
	Log(len(POD_rec))
	return POD_rec	
		
#----------------------------------------------------------------  

####################################################################################################
#									Hilfsfunktionen
####################################################################################################
#def stringextract(mFirstChar, mSecondChar, mString):  	# extrahiert Zeichenkette zwischen 1. + 2. Zeichenkette
	pos1 = mString.find(mFirstChar)						# return '' bei Fehlschlag
	ind = len(mFirstChar)
	#pos2 = mString.find(mSecondChar, pos1 + ind+1)		
	pos2 = mString.find(mSecondChar, pos1 + ind)		# ind+1 beginnt bei Leerstring um 1 Pos. zu weit
	rString = ''

	if pos1 >= 0 and pos2 >= 0:
		rString = mString[pos1+ind:pos2]	# extrahieren 
		
	#Log(mString); Log(mFirstChar); Log(mSecondChar); 	# bei Bedarf
	#Log(pos1); Log(ind); Log(pos2);  Log(rString); 
	return rString
#----------------------------------------------------------------  
def teilstring(zeile, startmarker, endmarker):  		# rfind: endmarker=letzte Fundstelle, return '' bei Fehlschlag
  # die übergebenen Marker bleiben Bestandteile der Rückgabe (werden nicht abgeschnitten)
  pos2 = zeile.find(endmarker, 0)
  pos1 = zeile.rfind(startmarker, 0, pos2)
  if pos1 & pos2:
    teils = zeile[pos1:pos2+len(endmarker)]	# 
  else:
    teils = ''
  #Log(pos1) Log(pos2) 
  return teils 
#----------------------------------------------------------------  
def blockextract(blockmark, mString):  	# extrahiert Blöcke begrenzt durch blockmark aus mString
	#	blockmark bleibt Bestandteil der Rückgabe
	#	Rückgabe in Liste. Letzter Block reicht bis Ende mString (undefinierte Länge),
	#		Variante mit definierter Länge siehe Plex-Plugin-TagesschauXL (extra Parameter blockendmark)
	#	Verwendung, wenn xpath nicht funktioniert (Bsp. Tabelle EPG-Daten www.dw.com/de/media-center/live-tv/s-100817)
	rlist = []				
	if 	blockmark == '' or 	mString == '':
		Log('blockextract: blockmark or mString leer')
		return rlist
	
	pos = mString.find(blockmark)
	if 	mString.find(blockmark) == -1:
		Log('blockextract: blockmark nicht in mString enthalten')
		# Log(pos); Log(blockmark);Log(len(mString));Log(len(blockmark));
		return rlist
	pos2 = 1
	while pos2 > 0:
		pos1 = mString.find(blockmark)						
		ind = len(blockmark)
		pos2 = mString.find(blockmark, pos1 + ind)		
	
		block = mString[pos1:pos2]	# extrahieren einschl.  1. blockmark
		rlist.append(block)
		# reststring bilden:
		mString = mString[pos2:]	# Rest von mString, Block entfernt	
	return rlist  
#----------------------------------------------------------------  
def unescape(line):	# HTML-Escapezeichen in Text entfernen, bei Bedarf erweitern. ARD auch &#039; statt richtig &#39;
#					# s.a.  ../Framework/api/utilkit.py
	line_ret = (line.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
		.replace("&#39;", "'").replace("&#039;", "'").replace("&quot;", '"').replace("&#x27;", "'")
		.replace("&ouml;", "ö").replace("&auml;", "ä").replace("&uuml;", "ü").replace("&szlig;", "ß")
		.replace("&Ouml;", "Ö").replace("&Auml;", "Ä").replace("&Uuml;", "Ü").replace("&apos;", "'")
		.replace("&#xD;", " ").replace("&shy;", ""))
		
	# Log(line_ret)		# bei Bedarf
	return line_ret	
#----------------------------------------------------------------  	
def decode_url(line):	# in URL kodierte Umlaute und & wandeln, Bsp. f%C3%BCr -> für, 	&amp; -> &
	urllib.unquote(line)
	line = line.replace('&amp;', '&')
	return line
#----------------------------------------------------------------  	
def mystrip(line):	# eigene strip-Funktion, die auch Zeilenumbrüche innerhalb des Strings entfernt
	line_ret = line	
	line_ret = line.replace('\t', '').replace('\n', '').replace('\r', '')
	line_ret = line_ret.strip()	
	# Log(line_ret)		# bei Bedarf
	return line_ret
#----------------------------------------------------------------  
def humanbytes(B):
	'Return the given bytes as a human friendly KB, MB, GB, or TB string'
	# aus https://stackoverflow.com/questions/12523586/python-format-size-application-converting-b-to-kb-mb-gb-tb/37423778
	B = float(B)
	KB = float(1024)
	MB = float(KB ** 2) # 1,048,576
	GB = float(KB ** 3) # 1,073,741,824
	TB = float(KB ** 4) # 1,099,511,627,776

	if B < KB:
	  return '{0} {1}'.format(B,'Bytes' if 0 == B > 1 else 'Byte')
	elif KB <= B < MB:
	  return '{0:.2f} KB'.format(B/KB)
	elif MB <= B < GB:
	  return '{0:.2f} MB'.format(B/MB)
	elif GB <= B < TB:
	  return '{0:.2f} GB'.format(B/GB)
	elif TB <= B:
	  return '{0:.2f} TB'.format(B/TB)
#----------------------------------------------------------------  	
