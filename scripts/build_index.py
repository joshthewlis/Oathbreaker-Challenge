#!/usr/bin/env python3
"""Generate a compact static browser catalogue from MTGJSON.

pip install ijson; run using GitHub Actions (not per visitor).
Pricing: minimum nonfoil-finish Cardmarket paper retail EUR price among
regular English paper printings; converted at an automatically fetched EUR/GBP rate.
"""
import argparse
import gzip
import json
import os
from pathlib import Path
from urllib.request import Request, urlopen
from datetime import datetime, timezone
import ijson

BASE = 'https://mtgjson.com/api/v5/'
FX = 'https://api.frankfurter.dev/v1/latest?base=EUR&symbols=GBP'
BASICS = {x.lower() for x in ('Plains','Island','Swamp','Mountain','Forest','Wastes','Snow-Covered Plains','Snow-Covered Island','Snow-Covered Swamp','Snow-Covered Mountain','Snow-Covered Forest')}

def stream_entries(url, fixture=None):
    if fixture:
        with open(fixture,'rb') as f:
            yield from ijson.kvitems(f,'data')
    else:
        req=Request(url,headers={'User-Agent':'OathbreakerChallengePriceIndex/1.0','Accept-Encoding':'identity'})
        with urlopen(req,timeout=150) as raw:
            with gzip.GzipFile(fileobj=raw) as f:
                yield from ijson.kvitems(f,'data')

def get_fx(path=None):
    if path:
        d=json.loads(Path(path).read_text())
    else:
        with urlopen(Request(FX,headers={'User-Agent':'OathbreakerChallenge/1.0'}),timeout=30) as r:
            d=json.load(r)
    rate=float(d['rates']['GBP'])
    if not (0.01 < rate < 5):
        raise ValueError('Currency rate outside plausible range')
    return rate,d['date']

def cardmarket_price(point):
    market=point.get('paper',{}).get('cardmarket',{})
    if market.get('currency','EUR')!='EUR': return None
    dated=market.get('retail',{}).get('normal',{})
    vals=[(date,float(val)) for date,val in dated.items() if val is not None and 0<float(val)<1000000]
    return max(vals,key=lambda x:x[0]) if vals else None

def eligible(card):
    # Avoid promo/collector-only, foreign-language, digital and foil-only variants.
    if 'paper' not in card.get('availability',[]):return False
    if str(card.get('language','English')).lower()!='english':return False
    if card.get('isPromo') or card.get('isOnlineOnly') or card.get('isOversized') or card.get('isAlternative') or card.get('isFunny'):return False
    if 'nonfoil' not in card.get('finishes',[]):return False
    return True

def build(prices_file=None, cards_file=None, fx_file=None, output='cards-index.json'):
    rate,fx_date=get_fx(fx_file)
    prices={}
    for uuid,entry in stream_entries(BASE+'AllPricesToday.json.gz',prices_file):
        result=cardmarket_price(entry)
        if result: prices[uuid]=result
    print('Priced printing IDs:',len(prices),flush=True)
    result={}
    for uuid,card in stream_entries(BASE+'AllIdentifiers.json.gz',cards_file):
        name=card.get('name')
        if not name or not eligible(card):continue
        key=name.casefold().replace('’',"'").strip()
        item=result.get(key)
        if not item:
            item={'name':name,'type':card.get('type',''),'colors':card.get('colorIdentity',[]),
                  'legality':'unknown',
                  'text':card.get('text',''),'basic':key in BASICS or 'Basic Land' in card.get('type',''),
                  'set':None,'eur':None,'priceDate':None}
            result[key]=item
        # Legality belongs to the card, not its cheapest printing. In particular,
        # older/odd printing records may report not_legal or omit the format.
        # Prefer an explicit Legal result found on ANY eligible printing.
        raw_legality=str((card.get('legalities') or {}).get('oathbreaker') or 'unknown').lower().replace(' ', '_')
        previous=item['legality']
        if raw_legality=='legal':
            item['legality']='legal'
        elif previous!='legal' and raw_legality in ('banned','restricted'):
            item['legality']=raw_legality
        # not_legal/unknown is inconclusive: do not use it as a ban.
        price_info=prices.get(uuid)
        if price_info:
            date,eur=price_info
            if item['eur'] is None or eur<item['eur']:
                item['eur']=eur;item['set']=card.get('setCode');item['priceDate']=date
    for item in result.values():
        item['gbp']=0 if item['basic'] else (round(item['eur']*rate,5) if item['eur'] is not None else None)
        del item['eur']
    if not result:raise RuntimeError('No eligible cards; refusing to write empty index')
    payload={'meta':{'source':'MTGJSON AllIdentifiers + AllPricesToday, Cardmarket retail normal',
                     'generated':datetime.now(timezone.utc).isoformat(timespec='seconds'),
                     'fxDate':fx_date,'eurToGbp':rate,'cards':len(result),
                     'priced':sum(c['gbp'] is not None for c in result.values())},'cards':result}
    tmp=Path(output).with_suffix('.tmp')
    tmp.parent.mkdir(parents=True,exist_ok=True)
    tmp.write_text(json.dumps(payload,ensure_ascii=False,separators=(',',':')))
    tmp.replace(output)
    print(f"Wrote {output}: {len(result)} cards, {payload['meta']['priced']} priced",flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--prices-file');p.add_argument('--cards-file');p.add_argument('--fx-file');p.add_argument('--output',default='cards-index.json')
    build(**vars(p.parse_args()))
