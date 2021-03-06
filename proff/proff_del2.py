import time; start = time.perf_counter() #Since it also takes time to Import libs, I allways start the timer asap. 
import requests
from bs4 import BeautifulSoup
from fake_headers import Headers
import pandas as pd
import pprint
import re 
from industry_list import industries
import json
import concurrent.futures
import numpy as np
from tqdm import tqdm



BASE_URL = 'https://www.proff.no'

print("=" * 91)
print("|											  |")
print("|				STARTING PROFF.NO DATA SCRAPER 				  |")
print("|											  |")
print("=" * 91)
print(f" Amount of industries scraping: {len(industries)}")
print()
print()


def getLinks():
	# links = pd.read_csv('links.csv')
	links = pd.read_csv('../_input_data/links.csv')
	return links.to_numpy()

def pullRequest(url):
	try:
		r = requests.get(url, timeout=10)
		soup = BeautifulSoup(r.content, "html.parser")
		r.raise_for_status()
	except (requests.exceptions.RequestException, ValueError) as e:
		print("="*91)
		print("|											  |")
		print("|				WARNING: ERROR CAUGHT! 				  |")
		print("|											  |")
		print("="*91)
		print(f'					{print(e)}')
		soup = ""
	return soup


def getPage(url):
	df = pd.DataFrame(		 index = [ 'bedrift',
										'avdeling',
										'telefon',
										'bransje',
										'org num', ] ).T
	soup = pullRequest(url)
	try:
		content = soup.findAll('div', {"class":"search-block"})
		content = [i for i in content]
		with concurrent.futures.ThreadPoolExecutor() as executor:
			results = executor.map(pageWorker, content) 
			for data_list in results:
				row = pd.DataFrame(data_list, index = [ 'bedrift',
														'avdeling',
														'telefon',
														'bransje',
														'org num', ] ).T
				df = pd.concat([df, row], axis = 0)
	except AttributeError:
		pass
	df = df.reset_index(drop = True)
	return df


def pageWorker(cont):
	data_list = []

	# ___ NAME ___________
	try:
		name = [element.text for element in cont.find('a','addax addax-cs_hl_hit_company_name_click')]
		data_list.append(name)
	except TypeError:
		name = ""
		data_list.append(name)	

	# ___ BRANCH ___________
	try:
		company_data = [item['data-company'] for item in cont.find_all('a', attrs = {'data-company' : True})]
		branch = [json.loads(company_data[0])['location']['county']]
	except:
		branch = ""
	data_list.append(branch)
	
	# ___ TELEPHONE ___________
	try: 
		tlf = [element.text for element in cont.find('a','addax addax-cs_hl_hit_phone_click')]
		data_list.append(tlf)
	except TypeError:
		tlf = ""
		data_list.append(tlf)
	
	# ___ INDUSTRY ___________
	try:
		industry = [[element.text for element in cont.find('a','addax addax-cs_hl_hit_industry_click')]]
		data_list.append(industry)
	except TypeError:
		industry = ""
		data_list.append(industry)	

	# ___ ORG_NUM ___________
	org_num = [item['data-id'] for item in cont.find_all('div', attrs = {'data-id' : True})]
	data_list.append(org_num)

	return data_list



def makeDataframe():
	return pd.DataFrame( index = [  'bedrift',
									'avdeling',
									'telefon',
									'bransje',
									'org num', ] ).T


def scarper(url):
	df_new = getPage(url[0])
	df_old = makeDataframe()
	# df_old = pd.DataFrame( index = [  'bedrift',
	# 								 	'avdeling',
	# 								 	'telefon',
	# 								 	'bransje',
	# 								 	'org num', ] ).T
	df_final = pd.concat([df_old, df_new], axis = 0)
	return df_final


def proffDataDownloader():
	urls = getLinks()
	index = 0

	print('	loading, please wait..')
	print()
	df_final = makeDataframe()
	# df_final = pd.DataFrame( index = [ 	'bedrift',
	# 									'avdeling',
	# 									'telefon',
	# 									'bransje',
	# 									'org num', ] ).T
	with tqdm(total = len(urls)) as pbar:
			with concurrent.futures.ThreadPoolExecutor() as executor:
				results = executor.map(scarper, urls)
				for result in results:
					pbar.update(1)
					df_final = pd.concat([df_final, result], axis = 0)
	# df_final.to_csv('proff_data.csv', index = False)
	df_final.to_csv('../output_data/proff_data.csv', index = False)
	print(f"|				   Finished in {round(time.perf_counter() - start, 2)} second(s)				  |")
	print("Displaying results:")
	print()
	print(df_final)


if __name__ == '__main__':
	proffDataDownloader()



'''
Next runs
'''

'''
___ Id?? _____________________

	1. Regn ut total_amount p?? forh??nd.
	2. Sett v som en standard mengde med threads.
	3. Integrer getLenResults() inn i getNextPages() og getFirstPage() => num_of_pages
	4. I scraper() regner du ut en ny total_amount [vil trolig vokse fra start til finish]
	5. I scraper() legg til funksjonen:
		if new_total_amount > old_total_amount:
			spawn additional threads
	6. oppdatere old_total_amount = new_total_amount s?? lagre det nye grunntallet. 

	Note: 
		m?? splitte opp threadingen i to deler. 
		del 1 threader main per ind in industries. 
		del 2 m?? regne ut total_amount per bransje, s?? threade hver side. 

	Alts??: 
		N?? vil den ikke sjekke tallet p?? forh??nd som sparer meg 1 min. 
		Den vil spawne X antall threads til ?? begynne med, fra et grunntall,
		s?? etterhvert som den jobber vil total_amount bli oppdatert og den 
		vil spawne nye threads etterhvert som proff f??r flere virksomheter.
		Til slutt vil den nye_total_amount bli lagret over old_total_amount i en egen fil (eller databasen) 

'''

'''
___ NY Id?? _____________________
	
	Alternativ til tidligere l??sninger iht threading.
	grunnet mangel p?? sidetall kan man ikke threade sider pga man m?? innom side 1 for ?? hente linken til side 2. 
	1. 

	alts??:
		Alle sidene best??r av en liste, og det kan vi iterate igjennom. 
		S?? da kan vi derimot threade hvert liste item; at hver worker har sin designerte arbeidsplass p?? listen:
			worker 1:	skal bare hente list[0]
			worker 2:	skal bare hente list[1]
			...
			worker n-1:	skal bare hente list[n]
			worker n:	henter neste link til neste side (trenger strengt tatt ikke ?? v??re en worker)
		S?? istedenfor ?? ha ??n worker for X antall sider, har vi 28 workers for hver side. (for hver bransje)

'''
