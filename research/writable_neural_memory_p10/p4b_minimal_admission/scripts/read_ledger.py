import csv,gzip,json
INTS=["point_id","score_time","alarm","decision_time","mutation_time","candidate_start","candidate_count","candidate_reset","parameter_mutation","adapter_mutation","optimizer_state_mutation","scaler_EMA_mutation","reference_mutation","calibration_mutation","encoder_mutation"]
FLOATS=["score","latent0","latent1"]
JSONS=["selected_ids","buffer_entry_ids","buffer_exit_ids","pending_pre","pending_post","loss_ids","loss_weights","effective_written_ids"]
def read(path):
 with gzip.open(path,"rt") as f:
  for row in csv.DictReader(f):
   for k in INTS:row[k]=int(row[k])
   for k in FLOATS:row[k]=float(row[k])
   for k in JSONS:row[k]=json.loads(row[k])
   yield row
