"""No-model trace of inspected wrapper input/write semantics using index IDs.

Extracts only the two relevant method bodies via AST into harmless spy objects.
No detector, JVM, training, labels, scoring metric or benchmark rerun occurs.
"""
import ast
import json
from pathlib import Path
import numpy as np
from sources import ROOT,CACHE


def extract(path,class_name,method_name,namespace):
    source=Path(path).read_text();tree=ast.parse(source)
    cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name==class_name)
    method=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name==method_name)
    module=ast.Module(body=[method],type_ignores=[]);ast.fix_missing_locations(module)
    exec(compile(module,str(path),'exec'),namespace)
    return namespace[method_name]


class CountingBackend:
    def __init__(self):self.ids=[]
    def fit_predict(self,x):self.ids.extend(np.asarray(x)[:,0].astype(int).tolist());return np.asarray(x)[:,0]
    def scoreNormalized(self,x):return self.fit_predict(x)


def trace_swknn(n=512,w=64):
    method=extract(CACHE/'StrAD/models/streaming/base_model_adapter.py','AdapterDSalmon','decision_function',{'np':np})
    spy=type('Spy',(),{})();spy.model=CountingBackend()
    for i in range(n-w+1):method(spy,np.arange(i,i+w)[:,None].astype(float))
    counts=np.bincount(spy.model.ids,minlength=n)
    return {'n':n,'window':w,'driver_calls':n-w+1,'backend_rows_consumed':len(spy.model.ids),'maximum_ingestions_per_observation':int(counts.max()),'middle_observation_ingestions':int(counts[n//2]),'one_new_point_per_call':False,'scope':'wrapper input trace; no claim about release score impact or internal dSalmon implementation'}


def trace_leap(n=512,w=256,slide=32):
    method=extract(CACHE/'StrAD/models/streaming/LEAP.py','LEAP','decision_function',{'np':np})
    spy=type('Spy',(),{})();spy.mean=np.zeros(1);spy.std=np.ones(1);spy._buffer=np.empty((0,1));spy._java_runner=CountingBackend();spy.slide=slide;spy.mode='normalized';spy._n_seen=w
    spy._ensure_2d=lambda x:np.asarray(x,dtype=float);spy._to_java_2d_array=lambda x:np.asarray(x,dtype=float)
    output=np.zeros(n);availability=np.full(n,-1);nonempty=0
    for i in range(n-w+1):
        values=method(spy,np.arange(i,i+w)[:,None].astype(float))
        if values.size:
            nonempty+=1;first=(w-slide)+i;last=(w-1)+i
            output[first:last+1]=values;availability[first:last+1]=last
            assert np.array_equal(values,np.arange(first,last+1))
    real=availability>=0;lags=availability[real]-np.arange(n)[real]
    return {'n':n,'window':w,'slide':slide,'driver_calls':n-w+1,'nonempty_calls':nonempty,'backend_rows_consumed':len(spy._java_runner.ids),'ingests_only_newest_point_per_call':True,'score_timestamp_alignment':'PASS with spy IDs','batch_availability_lag_min':int(lags.min()),'batch_availability_lag_max':int(lags.max()),'unemitted_tail_points':int((availability[w-1:]<0).sum()),'scope':'availability/index trace; no Java model scores or accuracy recomputed'}


def main():
    sw=trace_swknn();leap=trace_leap()
    assert sw['maximum_ingestions_per_observation']==64 and sw['backend_rows_consumed']==64*(512-64+1)
    assert leap['batch_availability_lag_max']==31 and leap['unemitted_tail_points']==1
    source=(CACHE/'StrAD/exp/Run_Online_Detector.py').read_text();stream=(CACHE/'StrAD/exp/Run_Streaming_Detector_M.py').read_text()
    assert 'final_output[: slidingWindow-1] = final_output[slidingWindow]' in source
    assert 'final_output[: slidingWindow-1] = final_output[slidingWindow]' in stream
    assert 'for filename in [file_list[153]]:' in source
    result={'no_models_run':True,'SWKNN_overlap_trace':sw,'LEAP_batch_trace':leap,'generic_padding':'positions0..W-2 backfilled from score atW, one step after first available targetW-1','initial_training_replay':'drivers fit an initial prefix then stream over complete data; implementation-specific initialization varies','raw_score_sensitivity':'NOT_AVAILABLE; no detector score vectors found in Git tree or paper-linked Zenodo archive'}
    (ROOT/'results/semantics_trace.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))


if __name__=='__main__':main()
