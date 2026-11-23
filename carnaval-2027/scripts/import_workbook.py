"""Importador ROTA27. Python 3.10+ e openpyxl. Não publica a planilha nem caminhos locais.
Uso: python scripts/import_workbook.py ARQUIVO.xlsx --research-dir DIRETORIO --out data
"""
import argparse,datetime as dt,hashlib,json,re,unicodedata,warnings
from pathlib import Path
from urllib.parse import urlsplit,urlunsplit,parse_qsl,urlencode
import openpyxl
warnings.filterwarnings('ignore',module='openpyxl')
DEST=[('rio','Rio de Janeiro','Brasil','RIO'),('arraial','Arraial do Cabo','Brasil','CFB'),('aracaju','Aracaju','Brasil','AJU'),('maceio','Maceió','Brasil','MCZ'),('natal','Natal','Brasil','NAT'),('jeri','Jericoacoara','Brasil','JJD'),('salvador','Salvador','Brasil','SSA'),('bh','Belo Horizonte','Brasil','CNF'),('recife','Olinda/Recife','Brasil','REC'),('lima','Lima','Peru','LIM'),('santiago','Santiago','Chile','SCL'),('buenos','Buenos Aires','Argentina','BUE')]
def uid(prefix,*parts):return prefix+'_'+hashlib.sha256('|'.join(str(p) for p in parts).encode()).hexdigest()[:16]
def norm(s):return ''.join(c for c in unicodedata.normalize('NFKD',str(s or '')).lower() if not unicodedata.combining(c))
def dest(s):
 n=norm(s)
 for k,name,country,airport in DEST:
  if norm(name) in n or (k=='recife' and ('olinda' in n or 'recife' in n)) or (country!='Brasil' and norm(country) in n):return k
 return None
def clean(x):
 if isinstance(x,(dt.datetime,dt.date,dt.time)):return x.isoformat()
 if isinstance(x,str):
  x=re.sub(r'(?i)[A-Z]:[\\/][^\n;]+','[caminho local omitido]',x)
  x=re.sub(r'(?i)\b(andré|andre|julya|júlia|julia)\b','grupo',x)
  x=re.sub(r'[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}','[e-mail omitido]',x)
  return x.strip()
 return x
def url(x):
 try:
  p=urlsplit(str(x or ''))
  if p.scheme!='https' or p.username or p.password:return None
  return urlunsplit((p.scheme,p.netloc,p.path,urlencode([(k,v) for k,v in parse_qsl(p.query) if k not in ['aid','label','salesChannel']]),''))
 except ValueError:return None
def canonical(x):
 p=urlsplit(url(x) or '');return urlunsplit((p.scheme,p.netloc,p.path,'',''))
def num(x):return x if isinstance(x,(int,float)) and not isinstance(x,bool) else None
def date(x):
 if isinstance(x,(dt.datetime,dt.date)):return x.strftime('%Y-%m-%d')
 s=str(x or '');m=re.search(r'(\d{4}-\d{2}-\d{2})',s)
 if m:return m[1]
 m=re.search(r'(\d{2})/(\d{2})/(\d{4})',s);return f'{m[3]}-{m[2]}-{m[1]}' if m else None
def payload(v):
 r=v.get('result',{});return r.get('structuredContent') or (json.loads(r['content'][0]['text']) if r.get('content') and r['content'][0]['text'].startswith('{') else r)
def load(p):return json.loads(p.read_text(encoding='utf-8-sig')) if p.exists() else {}
def main():
 ap=argparse.ArgumentParser();ap.add_argument('workbook',type=Path);ap.add_argument('--research-dir',type=Path,default=Path('.'));ap.add_argument('--out',type=Path,default=Path(__file__).resolve().parents[1]/'data');ap.add_argument('--preserve-existing-two',action='store_true');a=ap.parse_args()
 w=openpyxl.load_workbook(a.workbook,data_only=True);out={};meta={'schemaVersion':1,'generatedAt':dt.datetime.now(dt.timezone.utc).isoformat(),'lastResearch':'2026-11-23','origin':'Curitiba (CWB)','sourceFile':a.workbook.name,'sourceSha256':hashlib.sha256(a.workbook.read_bytes()).hexdigest(),'period':{'checkin':'2027-02-05','checkout':'2027-02-10'},'groups':[2,3,5,6]}
 def rows(name):
  s=w[name];headers=[clean(c.value) or f'col{i}' for i,c in enumerate(s[6])]
  for rr in s.iter_rows(min_row=7):
   if rr[0].value is None:continue
   vals=[clean(c.value) for c in rr];links={i:url(c.hyperlink.target) for i,c in enumerate(rr) if c.hyperlink and url(c.hyperlink.target)}
   yield vals,links,dict(zip(headers,[links.get(i,v) for i,v in enumerate(vals)]))
 properties={};lodgings=[];transport=[];sources=[];routes=[];transfers=[];history=[];events=[];research=[];combos=[]
 original={};orig_t={}
 for v,l,raw in rows('Hospedagens'):
  link=l.get(35) or url(v[35]);p=uid('property',canonical(link) or v[3],v[1]);properties.setdefault(p,{'id':p,'destinationId':dest(v[1]),'name':v[3],'country':v[2],'platform':'Airbnb' if 'airbnb' in (link or '') else 'Booking' if 'booking' in (link or '') else 'Referência','type':v[5] or v[4],'address':v[26],'area':v[27],'review':num(v[24]),'reviewScale':10,'reviewCount':num(v[25]),'url':link})
  q={'id':v[0],'propertyId':p,'destinationId':dest(v[1]),'guests':num(v[39]) or num(v[6]),'units':num(v[40]) or num(v[7]),'checkin':date(v[8]),'checkout':date(v[9]),'amount':num(v[16]),'additionalFees':num(v[17]),'currency':v[20] or 'BRL','priceBasis':'group','status':'pendente','priceStatus':'confirmado' if num(v[16]) is not None else 'pendente','queriedAt':date(v[32]),'queryPrecision':'dia; hora não registrada na origem','url':link,'sourceId':v[38],'capacity':num(v[12]),'beds':v[13],'privacy':v[14],'bathroom':v[15],'privacyVerified':norm(v[28]).startswith('sim'),'cleaningEvidence':v[29],'cleaningReviewDate':date(v[30]),'cancellation':v[22],'prepayment':v[23],'taxes':v[21],'notes':'; '.join(str(z) for z in [v[34],v[36]] if z),'legacy':raw,'roomName':None,'conditionsKey':None,'rateVerified':False}
  lodgings.append(q);original[v[0]]=q
 for v,l,raw in rows('Passagens'):
  q={'id':v[0],'destinationId':dest(v[1]),'mode':v[2],'terminal':v[3],'guests':num(v[4]),'departure':date(v[5]),'return':date(v[6]),'amount':num(v[7]),'adjustments':num(v[8]),'priceBasis':'group','currency':'BRL','companies':v[12],'stops':num(v[11]),'departureSummary':v[13],'arrivalSummary':v[14],'outboundHours':num(v[15]),'inboundHours':num(v[16]),'arrivalLocal':v[17],'returnLocal':v[18],'luggage':num(v[19]),'luggagePolicy':v[20],'taxes':v[21],'url':l.get(22) or url(v[22]),'returnUrl':l.get(36) or url(v[36]),'queriedAt':date(v[23]),'status':'pendente','priceStatus':'confirmado' if num(v[7]) is not None else 'pendente','itineraryVerified':False,'notes':v[28],'sourceId':v[30],'doorOutboundHours':num(v[25]) if norm(v[35]).startswith('sim') else None,'doorInboundHours':num(v[26]) if norm(v[35]).startswith('sim') else None,'usableDays':num(v[27]) if norm(v[35]).startswith('sim') else None,'legacy':raw}
  transport.append(q);orig_t[v[0]]=q
 for v,l,raw in rows('Transfers'):
  transfers.append({'id':v[0],'destinationId':dest(v[1]),'terminal':v[2],'guests':num(v[3]),'mode':v[4],'stages':v[5],'referenceAmount':num(v[6]),'manualAmount':num(v[7]),'amount':num(v[9]),'priceBasis':'group','currency':'BRL','outboundHours':num(v[11]),'returnHours':num(v[12]),'routeKm':num(v[13]),'night':v[14],'status':'estimado' if num(v[6]) is not None else 'pendente','url':l.get(16) or url(v[16]),'queriedAt':date(v[17]),'notes':v[18],'legacy':raw})
 for v,l,raw in rows('Rotas e Acessos'):
  routes.append({'id':v[0],'destinationId':dest(v[1]),'name':v[2],'station':v[5],'category':v[3],'walkMeters':num(v[6]),'walkMinutes':num(v[7]),'obligatory':v[8],'waitMinutes':num(v[9]),'rideMinutes':num(v[10]),'walk2Meters':num(v[11]),'walk2Minutes':num(v[12]),'outboundMinutesReference':num(v[16]),'returnMinutesReference':num(v[17]),'boat':('barco' in norm(str(v[3])+str(v[8])+str(v[24])) or 'gigoia' in norm(v[2])),'url':l.get(23),'queriedAt':date(v[25]),'notes':v[26],'stages':v[24],'legacy':raw})
 for v,l,raw in rows('Fontes e Pendências'):
  sources.append({'id':v[0],'category':v[1],'title':v[2],'url':l.get(3) or url(v[3]),'queriedAt':date(v[4]),'supports':v[5],'status':v[6],'pending':v[7]})
 for v,l,raw in rows('Escolha e Filtros'):
  if v[28] in original and v[29] in orig_t:combos.append({'id':v[39],'lodgingId':v[28],'transportId':v[29],'transferId':v[30],'guests':num(v[0]),'notes':v[24]})
 for v,l,raw in rows('Histórico de Cotações'):
  history.append({'id':uid('observation',v[0],v[2],v[3],v[5],v[6],v[7],v[8],v[9],v[11]),'destinationId':dest(v[2]),'propertyName':v[3],'countryReturned':v[4],'guests':num(v[5]),'units':num(v[6]),'checkin':date(v[7]),'checkout':date(v[8]),'amount':num(v[9]),'currency':v[10],'identity':v[11],'url':l.get(12) or url(v[12]),'queriedAt':date(v[0]),'conditionsKey':None,'status':'rejeitado' if any(z in norm(str(v[4])+' '+str(v[11])) for z in ['holanda','netherlands','paises baixos','incorret','erro de identidade']) else 'pendente'})
 for sn in ['Eventos','Salvador — Carnaval e Camarotes','BaianaSystem 2027']:
  for v,l,raw in rows(sn):events.append({'id':uid('event',sn,v[0]),'category':sn,'name':v[3] if sn=='Eventos' else v[2] if sn.startswith('Salvador') else v[3],'destinationId':dest(v[1] if sn=='Eventos' else 'Salvador' if sn.startswith('Salvador') else v[2]),'record':raw})
 for sn in ['Exterior','Grupo e Critérios','Datas Alternativas','Configurações','Parâmetros','Detalhes de Hospedagem','Rio — 3 pessoas','Rio — 5 pessoas','Rio — 6 pessoas','Salvador — Hospedagem','Belo Horizonte','Olinda e Recife','Passagens — Avião','Passagens — Ônibus']:
  for idx,(v,l,raw) in enumerate(rows(sn)):research.append({'id':uid('research',sn,idx),'category':sn,'record':raw})
 # Fresh two-adult observations; never rescale an earlier occupancy.
 h=load(a.research_dir/'rota27_research_2_hotels.json');flight=load(a.research_dir/'rota27_research_2_flights.json');rooms=load(a.research_dir/'rota27_research_2_rooms.json');airbnb=load(a.research_dir/'rota27_airbnb2.json');web=load(a.research_dir/'rota27_research_2_web.json')
 fresh={'lodgingSearches':len(h),'displayedLodgings':0,'roomSearches':len(rooms),'roomRates':0,'flightSearches':len(flight),'displayedFlights':0,'airbnbProperties':len(airbnb),'webRequests':len(web),'fullyVerifiedTrips':0}
 transfer_research=load(a.research_dir/'rota27_research_2_transfers.json');fresh['transferSources']=len(transfer_research)
 new_h={};new_p={};room_ids={}
 def source(platform,key,link,info):
  sid=uid('source2',platform,key,link);sources.append({'id':sid,'category':platform+' · 2 adultos','title':key,'url':url(link),'queriedAt':'2026-11-23','supports':info,'status':'Pesquisa nova','pending':'Conferir checkout, moeda de cobrança e taxas não discriminadas.'});return sid
 for k,v in h.items():
  d=payload(v);new_h[k]=[]
  for x in d.get('accommodations',[]):
   loc=x.get('location',{});p=uid('property',canonical(x['url']),next((name for kk,name,_,_ in DEST if kk==k),k));link=url(x['url']);sid=source('Booking',k,link,'Busca nova: 2 adultos, 1 unidade, 05–10/02/2027; total exibido, não checkout final.');props={'id':p,'destinationId':k,'name':x['name'],'country':loc.get('country_name'),'platform':'Booking','type':x.get('accommodationType'),'address':loc.get('address'),'area':loc.get('district_name'),'review':x.get('rating',{}).get('review_score'),'reviewScale':10,'reviewCount':x.get('rating',{}).get('number_of_reviews'),'url':link,'facilities':x.get('facilities',[]),'coordinates':loc.get('coordinates')};properties[p]={**properties.get(p,{}),**props}
   q={'id':uid('H2',x['id'],'2026-11-23','search'),'propertyId':p,'destinationId':k,'guests':2,'units':1,'checkin':'2027-02-05','checkout':'2027-02-10','amount':num(x.get('price',{}).get('book')),'currency':x.get('price',{}).get('currency','BRL'),'priceBasis':'group','status':'pendente','priceStatus':'confirmado','queriedAt':'2026-11-23','queryPrecision':'dia; ferramenta não informa hora de cotação','url':link,'sourceId':sid,'capacity':None,'beds':None,'privacy':'Conferência manual','bathroom':'Conferência manual','privacyVerified':False,'cleaningEvidence':'Sem avaliação recente datada validada','cancellation':None,'prepayment':None,'taxes':'Total exibido; discriminação de taxas e cobrança final pendentes','notes':'Pesquisa inédita para 2 adultos. O preço exibido não identifica a categoria exata do quarto.','roomName':None,'conditionsKey':None,'rateVerified':False}
   lodgings.append(q);new_h[k].append(q);room_ids[str(x['id'])]=(p,q);fresh['displayedLodgings']+=1
 for k,v in rooms.items():
  d=payload(v);pid=str(v.get('args',{}).get('accommodation_id'));base=room_ids.get(pid)
  if not base:continue
  p,old=base
  for room in d.get('rooms',[]):
   if (room.get('max_occupancy') or 0)<2:continue
   facilities='; '.join(room.get('facilities',[]));is_dorm=any(z in norm(room.get('name')) for z in ['dormitorio','dormitory','cama em']);bath='Compartilhado' if 'compartilhado' in norm(facilities+room['name']) else 'Privativo' if 'banheiro privativo' in norm(facilities) else 'Conferência manual'
   for rate in room.get('rates',[]):
    q={**old,'id':uid('H2rate',pid,room['name'],rate.get('checkout_url'),rate['price_total']),'amount':num(rate['price_total']),'currency':rate['currency'],'url':url(rate['checkout_url']),'capacity':room.get('max_occupancy'),'beds':room.get('bed_summary'),'privacy':'Dormitório coletivo' if is_dorm else 'Unidade privativa','bathroom':bath,'privacyVerified':not is_dorm,'roomName':room['name'],'facilities':room.get('facilities'),'cancellation':rate.get('cancellation_type'),'cancellationUntil':rate.get('free_cancellation_until'),'mealPlan':rate.get('meal_plan'),'availabilityCount':rate.get('availability_count'),'rateVerified':True,'conditionsKey':None,'taxes':'Tarifa de quarto retornada para 2 adultos; taxas extras não discriminadas, pagamento e depósito pendentes','notes':'Quarto e tarifa consultados diretamente para 2 adultos. Não equivale a reserva garantida; validar cobrança final.'}
    lodgings.append(q);new_h[k].append(q);fresh['roomRates']+=1
 for k,v in flight.items():
  key=k.split('-')[0];d=payload(v);new_p.setdefault(key,[]);args=v.get('args',{});arrival=args.get('routes',[{}])[0].get('arrival',{});airport=arrival.get('iata_code');iata_type=arrival.get('iata_type','AIRPORT');link=f'https://flights.booking.com/flights/CWB.AIRPORT-CWB.AIRPORT/?type=ROUNDTRIP&adults=2&cabinClass=ECONOMY&from=CWB.AIRPORT&to={airport}.{iata_type}&depart=2027-02-05&return=2027-02-10';sid=source('Booking Flights',k,link,'Busca nova ida e volta, dois adultos. Resumo não separa horários de ambos os trechos; bagagem e tarifa final pendentes.')
  for x in d.get('flight_offers',[]):
   q={'id':uid('P2',x['id']),'destinationId':key,'mode':'Avião','terminal':airport,'guests':2,'departure':'2027-02-05','return':'2027-02-10','amount':num(x.get('total_price',{}).get('amount')),'currency':x.get('total_price',{}).get('currency','BRL'),'priceBasis':'group','companies':', '.join(x.get('airlines',[])),'stops':x.get('stops'),'departureSummary':x.get('departure_time'),'arrivalSummary':x.get('arrival_time'),'outboundHours':None,'inboundHours':None,'doorOutboundHours':None,'doorInboundHours':None,'usableDays':None,'luggage':None,'luggagePolicy':'Conferência manual: não retornada','taxes':'Total exibido para dois adultos; confirmar cobrança final','url':link,'queriedAt':'2026-11-23','status':'pendente','priceStatus':'confirmado','itineraryVerified':False,'notes':'Resumo não separa ida e volta. Não subtrair estes horários para calcular duração.','sourceId':sid}
   transport.append(q);new_p[key].append(q);fresh['displayedFlights']+=1
 for x in airbnb:
  k=x['destination'];link=f"https://www.airbnb.com.br/rooms/{x['id']}?adults=2&check_in=2027-02-05&check_out=2027-02-10";p=uid('property',canonical(link),k);sid=source('Airbnb',k,link,'Anúncio real pesquisado; capacidade/camas da descrição, mas preço e disponibilidade de 05–10/02 para 2 adultos não verificáveis.');properties[p]={'id':p,'destinationId':k,'name':x['name'],'platform':'Airbnb','type':x['type'],'review':x.get('rating5'),'reviewScale':5,'reviewCount':x.get('reviews'),'url':link}
  q={'id':uid('H2airbnb',x['id']),'propertyId':p,'destinationId':k,'guests':2,'units':1,'checkin':'2027-02-05','checkout':'2027-02-10','amount':None,'currency':'BRL','priceBasis':'group','status':'pendente','priceStatus':'pendente','queriedAt':'2026-11-23','url':link,'sourceId':sid,'capacity':x.get('capacity'),'beds':x.get('beds'),'privacy':'Unidade privativa','bathroom':x.get('bath'),'privacyVerified':False,'rateVerified':False,'notes':'Descrição pública consultada; preço final, ocupação da tarifa, limpeza recente datada, taxas e disponibilidade: conferência manual.','conditionsKey':None}
  lodgings.append(q);new_h[k].append(q)
 # Preserve all source combinations. New pairings: one representative fare per airport,
 # rather than a needless Cartesian product. All transport quotes remain searchable.
 for k,hs in new_h.items():
  ps=new_p.get(k,[]);byairport={}
  for q in ps:
   if q['terminal'] not in byairport or (q['amount'] or float('inf')) < (byairport[q['terminal']]['amount'] or float('inf')):byairport[q['terminal']]=q
  for hq in hs:
   for pq in byairport.values():combos.append({'id':uid('C2',hq['id'],pq['id']),'lodgingId':hq['id'],'transportId':pq['id'],'transferId':None,'guests':2,'notes':'Combinação de pesquisas independentes para 2 adultos; transfer, bagagem e taxas adicionais pendentes.'})
 for x in web:
  sid=source(x['platform'],x['destination'],x['url'],x['result']);sources[-1]['checkedAt']=x.get('checked_at');sources[-1]['httpStatus']=x.get('http_status');sources[-1]['pending']=x['result']
  if x['category']=='ônibus' and 'departureDate=2027-02-05' in x['url']:
   k=x['destination'];pid=uid('P2bus',k);q={'id':pid,'destinationId':k,'mode':'Ônibus','terminal':'Rodoviária / conexões a confirmar','guests':2,'departure':'2027-02-05','return':'2027-02-10','amount':None,'currency':'BRL','priceBasis':'group','url':url(x['url']),'queriedAt':'2026-11-23','status':'pendente','sourceId':sid,'notes':'Busca efetivamente consultada; tarifa, assentos, duração e volta não verificáveis. Saída em 05/02 pode reduzir noites no destino.','itineraryVerified':False}
   transport.append(q)
   for hq in new_h.get(k,[]):combos.append({'id':uid('C2bus',hq['id'],pid),'lodgingId':hq['id'],'transportId':pid,'transferId':None,'guests':2,'notes':q['notes']})
 transfer2={}
 for x in transfer_research:
  k=x['destination'];sid=source('Transporte local',k,x['url'],x['result']);tid=uid('T2',k,x['terminal']);terminal='FOR' if k=='jeri' else x['terminal'];transfer2[k]=tid
  transfers.append({'id':tid,'destinationId':k,'terminal':terminal,'guests':2,'mode':'Conferência manual','stages':x.get('stages'),'amount':None,'referenceAmount':None,'currency':'BRL','priceBasis':'group','status':'pendente','url':url(x['url']),'queriedAt':'2026-11-23','checkedAt':x.get('checkedAt'),'notes':x['result'],'sourceId':sid})
  if k=='jeri':
   transfers[-1].update({'referenceAmount':800,'outboundHours':6,'returnHours':6,'status':'estimado','stages':'FOR → hotel em Fortaleza (acesso pendente) → van → Jijoca → 4×4 → pousada em Jeri','notes':'Fonte do operador reaberta em 23/11/2026: R$400 I/V por pessoa no serviço regular desde hotel em Fortaleza; dois adultos R$800 grupo como referência, não tarifa de fevereiro nem transfer desde JJD. Confirmar acesso desde FOR ao embarque, janela matinal, bagagem e retorno. Taxa local TTS atual R$41,50 por pessoa para até10 dias, à parte, com confirmação para2027 pendente.'})
 for combo in combos:
  if combo['guests']==2:
   pq=next((q for q in transport if q['id']==combo['transportId']),None);k=pq.get('destinationId') if pq else None
   if k in transfer2 and pq.get('mode')=='Avião' and (k!='jeri' or pq.get('terminal')=='FOR'):combo['transferId']=transfer2[k]
 if a.preserve_existing_two:
  oldmeta=load(a.out/'meta.json');oldh=[x for x in load(a.out/'lodgings.json') if x.get('guests')==2];oldp=[x for x in load(a.out/'transport.json') if x.get('guests')==2]
  lodgings.extend(oldh);transport.extend(oldp);combos.extend(x for x in load(a.out/'combinations.json') if x.get('guests')==2);transfers.extend(x for x in load(a.out/'transfers.json') if x.get('guests')==2);pids={x['propertyId'] for x in oldh}
  for p in load(a.out/'properties.json'):
   if p['id'] in pids:properties[p['id']]=p
  sources.extend(x for x in load(a.out/'sources.json') if '2 adultos' in str(x.get('category')))
  if not h and oldmeta:fresh=oldmeta.get('research2',fresh)
 elif not h and a.out.exists() and any(x.get('guests')==2 for x in load(a.out/'lodgings.json')):
  raise SystemExit('Há pesquisa de 2 pessoas publicada. Forneça os arquivos de pesquisa ou use --preserve-existing-two para não perder os registros.')
 # Preserve every valid quote, including alternatives, without exposing private originals.
 for name,items in [('properties',list(properties.values())),('lodgings',lodgings),('transport',transport),('transfers',transfers),('routes',routes),('sources',sources),('events',events),('history',history),('research',research),('combinations',combos)]:
  seen=set();out[name]=[x for x in items if not(x['id'] in seen or seen.add(x['id']))]
 meta['counts']={k:len(v) for k,v in out.items()};meta['original']={'lodgings':len(original),'transport':len(orig_t),'combinations':sum(x['guests'] in [3,5,6] for x in combos),'sheets':len(w.sheetnames)};meta['research2']=fresh
 meta['lastResearch']=max([x.get('queriedAt','') or '' for x in lodgings+transport+sources] or ['2026-11-23']);out['destinations']=[{'id':k,'name':name,'country':country,'airport':airport} for k,name,country,airport in DEST];out['meta']=meta
 updates=load(a.out/'updates.json') or [];entry={'id':uid('update',meta['sourceSha256'],fresh),'date':meta['lastResearch'],'action':'Importação da planilha e integração das pesquisas de dois adultos','sourceSha256':meta['sourceSha256'],'original':meta['original'],'research2':fresh}
 if not any(x['id']==entry['id'] for x in updates):updates.append(entry)
 out['updates']=updates
 a.out.mkdir(parents=True,exist_ok=True)
 for name,data in out.items():(a.out/(name+'.json')).write_text(json.dumps(data,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
 assert len(original)==meta['original']['lodgings'] and all(x['lodgingId'] in {q['id'] for q in lodgings} and x['transportId'] in {q['id'] for q in transport} for x in out['combinations'])
 print(json.dumps({'original':meta['original'],'counts':meta['counts'],'research2':fresh},ensure_ascii=False))
if __name__=='__main__':main()
