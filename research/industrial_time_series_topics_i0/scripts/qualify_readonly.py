import csv,io,json,collections,zipfile,datetime,hashlib
from pathlib import Path
root=Path('research/industrial_time_series_topics_i0/provenance');cache=Path('data/industrial_time_series_topics_i0')
lab=list(csv.DictReader(io.StringIO((cache/'Laboratory.csv').read_text(encoding='utf-8-sig')),delimiter=';'));by={r['batch']:r for r in lab};par={r['batch']:r['batch'] for r in lab}
def find(x):
 while par[x]!=x:par[x]=par[par[x]];x=par[x]
 return x
edges={};lotcounts={}
for column in ['api_batch','smcc_batch','lactose_batch','starch_batch']:
 counts=collections.Counter()
 for row in lab:
  value=row[column]
  if not value:continue
  key=(column,row.get('api_code','') if column=='api_batch' else '',value);counts[key]+=1
  if key in edges:par[find(row['batch'])]=find(edges[key])
  else:edges[key]=row['batch']
 lotcounts[column]={'unique_nonmissing_lots':len(counts),'largest_batch_count':max(counts.values()),'lots_shared_by_multiple_batches':sum(x>1 for x in counts.values())}
components=collections.Counter(find(x) for x in par)
with zipfile.ZipFile(cache/'Process.zip') as z:
 name=sorted(n for n in z.namelist() if n.endswith('.csv'))[0];data=z.read(name);assert len(data)<=10_000_000
 rows=list(csv.DictReader(io.StringIO(data.decode('utf-8-sig')),delimiter=';'));groups=collections.defaultdict(list)
 for row in rows:groups[row['batch']].append(row)
 summary=[]
 for bid,rows_b in groups.items():
  ts=[datetime.datetime.fromisoformat(r['timestamp']) for r in rows_b];unique=sorted(set(ts));duration=(max(ts)-min(ts)).total_seconds();start=min(ts)
  summary.append({'batch':bid,'laboratory_join':bid in by,'code_matches_lab':bid in by and all(r['code']==by[bid]['code'] for r in rows_b),'rows':len(rows_b),'duplicate_timestamps':len(ts)-len(set(ts)),'duration_seconds':duration,'zero_speed_rows':sum(r['tbl_speed'] != '' and float(r['tbl_speed'])==0 for r in rows_b),'empty_speed_rows':sum(r['tbl_speed']=='' for r in rows_b),'empty_fields':sum(v=='' for r in rows_b for v in r.values()),'fixed_elapsed_prefix_rows':{str(minutes):sum(t<=start+datetime.timedelta(minutes=minutes) for t in ts) for minutes in [15,30,60]},'timestamp_delta_seconds':dict(collections.Counter((b-a).total_seconds() for a,b in zip(unique,unique[1:]))),'campaign_ids':sorted(set(r['campaign'] for r in rows_b))})
 mp=list(csv.DictReader(io.StringIO(next(cache.glob('InduTS_repo_data_MP*')).read_text())))
 mts=[datetime.datetime.strptime(r['date'],'%Y/%m/%d %H:%M') for r in mp]
 psc=list(csv.DictReader(io.StringIO(next(cache.glob('pyscrew_repo_data_csv_s01*')).read_text())))
 out={'no_model_or_correlation_runs':True,'pharma':{'lab_rows':len(lab),'lab_columns':len(lab[0]),'unique_batch_ids':len(by),'product_codes':dict(collections.Counter(r['code'] for r in lab)),'lot_counts':lotcounts,'genealogy_components':len(components),'largest_components':sorted(components.values(),reverse=True)[:10],'identity_assumption':'Typed lot fields, API lot scoped by api_code; missing values do not form edges. Anonymized ID stability across all product codes remains a source-semantic caveat.','lab_has_exact_result_return_time':False,'full_process_member':name,'member_sha256':hashlib.sha256(data).hexdigest(),'member_bytes':len(data),'member_rows':len(rows),'sampled_batches':summary,'target_fields':['dissolution_av','dissolution_min','resodual_solvent','impurities_total','impurity_o','impurity_l']},'MP':{'rows':len(mp),'delta_seconds_counts':dict(collections.Counter((b-a).total_seconds() for a,b in zip(mts,mts[1:]))),'strictly_increasing':all(b>a for a,b in zip(mts,mts[1:])),'fields_include_other_lab_quality':'% Iron Concentrate' in mp[0],'label_return_timestamp_present':False},'PyScrew_s01':{'rows':len(psc),'workpieces':len(set(r['workpiece_id'] for r in psc)),'locations':dict(collections.Counter(r['workpiece_location'] for r in psc)),'result_counts':dict(collections.Counter(r['workpiece_result'] for r in psc)),'usage_range':[min(int(r['workpiece_usage']) for r in psc),max(int(r['workpiece_usage']) for r in psc)],'raw_trajectory_downloaded':False,'independent_joint_strength_labels_verified':False}}
(root/'qualification_checks.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({'lab_batches':len(lab),'components':len(components),'largest':max(components.values()),'process_member':name,'process_rows':len(rows),'batches':len(summary),'joins':sum(s['laboratory_join'] for s in summary),'MP_delta_counts':out['MP']['delta_seconds_counts'],'s01':out['PyScrew_s01']},indent=2))
