"""Oracle viseme-snapping experiment across all 21 videos.
Snap only 'nonsense' hyp spans (words outside scene lexicon) to viseme-close
phrases from the scene phrase bank. Score turn understanding before/after."""
import json, re, glob, difflib, itertools, os
import pronouncing

MIL = ['img_6824','img_6825','s2_tomer_ido_1','s2_yoad_tal_1','s2_yoad_tomer_1',
       's2_yoad_tomer_2','s2_yoad_tal_2','shaam_amosi_ido_1','shaam_amosi_ido_2']
DOC = {'img_6825':72.7,'img_6824':66.7,'s2_tomer_ido_1':62.5,'s2_yoad_tal_1':46.4,
 's1_tomer_yoad_1':45.8,'s2_yoad_tomer_2':44.8,'shaam_amosi_ido_2':42.9,
 's2_yoad_tomer_1':39.4,'s1_tomer_yoad_2':35.7,'img_6822':35.3,'s1_tomer_ido_1':33.3,
 's1_yoad_tal_z30_1':30.4,'s2_yoad_tal_2':29.0,'s1_yoad_tal_1':27.6,'img_6821':19.0,
 'shaam_yoad_amosi_2':17.2,'img_6823':14.8,'shaam_yoad_amosi_3':14.8,
 'shaam_amosi_ido_1':12.0,'s1_yoad_tal_z45_1':11.5,'shaam_yoad_amosi_1':10.0}
STOP=set('''a an the and or but if so to of in on at for with from by is are was were be been am
i you he she it we they that this these those there here what who how when where why will would
can could should shall may might must do does did done have has had not no yes oh uh um my your
his her its our their me him them us as its it's don't didn't isn't aren't i'm you're he's she's
we're they're that's what's let's very just really then than too also about into over under
again once know knows going go get got'''.split())

VIS={**{p:'p' for p in ['P','B','M']},**{p:'f' for p in ['F','V']},
     **{p:'T' for p in ['TH','DH']},**{p:'t' for p in ['T','D','S','Z','N','L']},
     **{p:'S' for p in ['SH','ZH','CH','JH']},**{p:'k' for p in ['K','G','NG','HH']},
     'W':'w','R':'w','Y':'y',
     **{p:'O' for p in ['UW','UH','OW','AO','OY']},
     **{p:'A' for p in ['AA','AE','AH','AY','AW']},
     **{p:'E' for p in ['IY','IH','EY','EH','ER']}}
_vc={}
def vis_word(w):
    if w in _vc: return _vc[w]
    ph=pronouncing.phones_for_word(w)
    v=''.join(VIS.get(re.sub(r'\d','',p),'?') for p in ph[0].split()) if ph else None
    _vc[w]=v; return v
def vis_seq(ws):
    parts=[vis_word(w) for w in ws]
    return None if any(p is None for p in parts) else ''.join(parts)
def vsim(a,b):
    return difflib.SequenceMatcher(None,a,b).ratio() if a and b else 0

def wl(s):
    s=re.sub(r"[^a-z0-9' ]",' ',s.lower())
    return [w for w in s.split() if w and (len(w)>1 or w in ('a','i'))]

def load():
    data={}
    for d in sorted(glob.glob('ex_*')):
        name=d[3:]
        turns=json.load(open(f'{d}/turns.json'))
        # merge consecutive duplicate turns (OCR grouping repeats)
        out=[]
        for t in turns:
            s=' '.join(wl(t['said']))
            if out and difflib.SequenceMatcher(None,s,out[-1]['s']).ratio()>0.8:
                if len(t.get('hyp',''))>len(out[-1]['hyp']): out[-1]['hyp']=t.get('hyp','')
                continue
            out.append({'s':s,'said':t['said'],'hyp':t.get('hyp',''),'sp':t.get('sp','?')})
        data[name]=out
    return data

def content(ws): return [w for w in ws if w not in STOP and (len(w)>=3 or w.isdigit())]

def build_bank(data, names):
    grams={}; lex={}
    for n in names:
        for t in data[n]:
            ws=wl(t['said'])
            for w in content(ws): lex[w]=lex.get(w,0)+1
            for i in range(len(ws)):
                for L in range(1,5):
                    if i+L<=len(ws):
                        g=tuple(ws[i:i+L]); grams[g]=grams.get(g,0)+1
    lexset={w for w,c in lex.items() if c>=2}
    bank=[(g,vis_seq(g)) for g,c in grams.items() if c>=2]
    bank=[(g,v) for g,v in bank if v]
    return lexset, bank

def snap_turn(hyp_ws, lexset, bank):
    subs=[]; ws=list(hyp_ws)
    # nonsense spans: maximal runs of words that are content-y but not in scene lexicon
    flags=[(w not in STOP and w not in lexset and not w.isdigit()) for w in ws]
    i=0
    while i<len(ws):
        if not flags[i]: i+=1; continue
        j=i
        while j<len(ws) and (flags[j] or (j+1<len(ws) and flags[j+1] and ws[j] in STOP)): j+=1
        # expand one stopword left/right for phrase context
        a=max(0,i-1); b=min(len(ws),j+1)
        span=ws[a:b]; v=vis_seq(span)
        if v and len(v)>=4:
            best=None
            for g,gv in bank:
                if abs(len(gv)-len(v))>max(3,len(v)//2): continue
                s=vsim(v,gv)
                if s>=0.78 and (best is None or s>best[1]): best=(g,s)
            if best and list(best[0])!=span:
                subs.append((' '.join(span),' '.join(best[0]),round(best[1],2)))
                ws[a:b]=list(best[0])
                flags=[(w not in STOP and w not in lexset and not w.isdigit()) for w in ws]
                i=a+len(best[0]); continue
        i=j
    return ws, subs

def turn_score(said_ws, hyp_ws, thY, thP):
    ref=content(said_ws)
    if not ref: return None
    hset=set(hyp_ws)
    hits=0; distinct=0
    for w in ref:
        ok=w in hset or any(difflib.SequenceMatcher(None,w,h).ratio()>=0.87 for h in hset)
        if ok:
            hits+=1
            if len(w)>=6 or w.isdigit(): distinct+=1
    r=hits/len(ref)
    if r>=thY: return 'Y'
    if r>=thP or distinct>=1: return 'P'
    return 'N'

def yp(turns, lexset, bank, thY, thP, snapped):
    vs=[]
    for t in turns:
        sw=wl(t['said']); hw=wl(t['hyp'])
        if snapped: hw,_=snap_turn(hw,lexset,bank)
        v=turn_score(sw,hw,thY,thP)
        if v: vs.append(v)
    if not vs: return 0,0
    return 100*sum(v in 'YP' for v in vs)/len(vs), len(vs)

if __name__=='__main__':
    data=load()
    banks={}
    mil=[n for n in data if n in MIL]; emma=[n for n in data if n not in MIL]
    lex_m,bank_m=build_bank(data,mil); lex_e,bank_e=build_bank(data,emma)
    # calibrate thresholds on BEFORE vs DOC
    best=None
    for thY in [0.5,0.55,0.6,0.65,0.7]:
        for thP in [0.2,0.25,0.3,0.35]:
            err=0
            for n in data:
                l,b=(lex_m,bank_m) if n in MIL else (lex_e,bank_e)
                p,_=yp(data[n],l,b,thY,thP,False)
                err+=abs(p-DOC[n])
            if best is None or err<best[0]: best=(err,thY,thP)
    _,thY,thP=best
    print(f'calibrated thY={thY} thP={thP} MAE={best[0]/21:.1f}')
    rows=[]; allsubs={}
    for n in sorted(data,key=lambda x:-DOC[x]):
        l,b=(lex_m,bank_m) if n in MIL else (lex_e,bank_e)
        b0,nt=yp(data[n],l,b,thY,thP,False)
        b1,_=yp(data[n],l,b,thY,thP,True)
        subs=[]
        for t in data[n]:
            _,s=snap_turn(wl(t['hyp']),l,b)
            subs+=s
        allsubs[n]=subs
        rows.append((n,nt,DOC[n],round(b0,1),round(b1,1),round(b1-b0,1),len(subs)))
    print(f"{'video':24s} turns docY+P proxy_before proxy_after delta subs")
    for r in rows: print(f"{r[0]:24s} {r[1]:>4} {r[2]:>6} {r[3]:>8} {r[4]:>8} {r[5]:>+6} {r[6]:>4}")
    import statistics
    d=[r[5] for r in rows]
    print('mean delta', round(sum(d)/len(d),2), 'videos improved:', sum(x>0 for x in d))
    json.dump({'rows':rows,'subs':{k:v for k,v in allsubs.items()}}, open('snap_results.json','w'))
