import os,json,hashlib,platform
from pathlib import Path
import numpy as np,pandas as pd,sklearn,xgboost
from xgboost import XGBClassifier
from sklearn.metrics import roc_auc_score,average_precision_score
root=Path(os.environ.get('AML_INPUT_DIR', 'data/local'));out=Path(os.environ.get('AML_OUTPUT_DIR', 'artifacts'));out.mkdir(parents=True,exist_ok=True)
source_hash=hashlib.file_digest(open(root/'aml_modeling_dev.tsv','rb'),'sha256').hexdigest()
expected_hash='d6194ac2c29f4a90e4fa1e1740945ca2f558388a799020a15f16623eee9c6012'
assert source_hash == expected_hash, 'Input TSV differs from the validated canonical source; metrics may not match'
df=pd.read_csv(root/'aml_modeling_dev.tsv',sep='\t');df['activity_date']=pd.to_datetime(df.activity_date)
assert not df[['account_id','activity_date']].duplicated().any()
train=df[df.activity_date.between('2022-09-01','2022-09-06')];val=df[df.activity_date.between('2022-09-07','2022-09-08')];test=df[df.activity_date.between('2022-09-09','2022-09-10')].copy()
assert (len(train),len(val),len(test))==(1534403,450244,494707)
logs=['transaction_count','total_sent','total_received','avg_transaction_amount','max_transaction_amount','unique_banks'];direct=['outgoing_ratio','currency_diversity','rapid_transaction_ratio']
def features(d):
 x=pd.DataFrame(index=d.index)
 for c in logs:x['log_'+c]=np.log1p(d[c])
 for c in direct:x[c]=d[c]
 assert np.isfinite(x.to_numpy()).all()
 return x
xt,xv,xe=features(train),features(val),features(test)
y=train.has_laundering_tx;yv=val.has_laundering_tx;yt=test.has_laundering_tx
weight=int((y==0).sum())/int((y==1).sum())
model=XGBClassifier(n_estimators=300,max_depth=5,learning_rate=.05,subsample=.8,colsample_bytree=.8,objective='binary:logistic',eval_metric='aucpr',scale_pos_weight=weight,random_state=42,n_jobs=2)
model.fit(xt,y)
model.save_model(out/'xgboost_canonical.json')
val_prob=model.predict_proba(xv)[:,1];test_prob=model.predict_proba(xe)[:,1]
capacity=round(len(test)*2500/len(val));assert capacity==2747
# Stable tie-break: preserve original test row order
rank_order=np.argsort(-test_prob,kind='stable');ranks=np.empty(len(test),dtype=np.int32);ranks[rank_order]=np.arange(1,len(test)+1)
test['risk_score']=test_prob;test['risk_rank']=ranks;test['selected_for_review']=(ranks<=capacity).astype('int8')
test['model_outcome']=np.select([(test.selected_for_review.eq(1)&test.has_laundering_tx.eq(1)),(test.selected_for_review.eq(1)&test.has_laundering_tx.eq(0)),(test.selected_for_review.eq(0)&test.has_laundering_tx.eq(1))],['True Positive','False Positive','False Negative'],default='True Negative')
test.to_csv(out/'aml_tableau_decision_data_canonical.csv',index=False)
tp=int(test.loc[test.selected_for_review.eq(1),'has_laundering_tx'].sum());total=int(yt.sum());base=float(yt.mean())
metrics={'train_rows':len(train),'validation_rows':len(val),'test_rows':len(test),'train_positives':int(y.sum()),'validation_positives':int(yv.sum()),'test_positives':total,'validation_capacity':2500,'test_capacity':capacity,'selected_positives':tp,'precision':tp/capacity,'recall':tp/total,'lift':(tp/capacity)/base,'roc_auc':roc_auc_score(yt,test_prob),'pr_auc':average_precision_score(yt,test_prob),'xgboost_version':xgboost.__version__,'pandas_version':pd.__version__,'sklearn_version':sklearn.__version__,'python_version':platform.python_version(),'seed':42,'n_jobs':2,'features':xt.columns.tolist(),'source_file_sha256':hashlib.file_digest(open(root/'aml_modeling_dev.tsv','rb'),'sha256').hexdigest()}
(out/'metrics.json').write_text(json.dumps(metrics,indent=2));
# The published website expects rows [{k,tp,precision,recall,lift}, ...].
# Use the exact same serialization contract for a fresh pipeline run.
labels=yt.to_numpy()[rank_order].astype('int8')
cum=np.cumsum(labels,dtype=np.int64)
rows=[]
for k in range(1, 15001):
    tp_k=int(cum[k-1])
    precision_k=tp_k/k
    rows.append({'k':k, 'tp':tp_k, 'precision':precision_k,
                 'recall':tp_k/total, 'lift':precision_k/base})
capacity_json={'rows':rows,'provenance':'Canonical XGBoost 3.1.3 model; September 9-10 2022 test; frozen validation-derived review rate'}
(out/'capacity.json').write_text(json.dumps(capacity_json,separators=(',',':')))
print(json.dumps(metrics,indent=2),flush=True)
