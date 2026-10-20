// Merge three independently completed workflow artifacts; never sends transactions.
const fs=require('node:fs'),path=require('node:path');
const {root,assert,sourceHash,save}=require('./transport.cjs');
const {cases,plan}=require('./scenario.cjs');
const dirs=process.argv.slice(2);assert(dirs.length===3,'Pass split, bundle and review artifact directories in that order');
const suite=[],hashes={},runs=[];
for(const [index,id] of Object.keys(cases).entries()){
 const dir=path.resolve(dirs[index]),load=name=>JSON.parse(fs.readFileSync(path.join(dir,name+'.json')));
 const records=load('suite'),journal=load('transactions'),verification=load('verification-'+id);
 assert(records.length===1&&records[0].id===id&&records[0].source_sha256===sourceHash&&journal.source_sha256===sourceHash,'One source-bound scenario per artifact');
 const d=records[0],items=plan(id,d.accounts,d.fixture_revision);
 assert(verification.scope===id&&verification.live_state_match===true&&verification.source_sha256===sourceHash&&verification.transactions.length===items.length+1,'Completed fresh scenario verification');
 const labels=[id+'-deployment',...items.map(x=>x.label)];
 assert(Object.keys(journal.hashes).length===labels.length,'Exact scenario journal');
 for(const label of labels){assert(!hashes[label]&&journal.hashes[label],'Unique planned receipt');hashes[label]=journal.hashes[label];}
 const files=[...labels.map(x=>x+'-receipt.json'),id+'-initial-state.json',id+'-final-state.json',id+'-trace.json','verification-'+id+'.json'];
 for(const file of files)fs.copyFileSync(path.join(dir,file),path.join(root,'proofs',file));
 fs.copyFileSync(path.join(dir,'cloud-direct-tests.xml'),path.join(root,'proofs',id+'-direct-tests.xml'));
 const run=path.basename(dir).match(/^run-(\d+)$/)?.[1];assert(run,'Artifact directory must be run-<workflow-id>');
 runs.push({scenario:id,workflow_run:run,url:'https://github.com/mohammadisina1988-jpg/pivot-bond/actions/runs/'+run,source_sha256:sourceHash,fixture_revision:d.fixture_revision});
 suite.push(d);
}
assert(Object.keys(hashes).length===33,'Thirty-three finalized scenario receipts required');
save('suite',suite);save('transactions',{source_sha256:sourceHash,hashes});save('provenance',{repository:'mohammadisina1988-jpg/pivot-bond',network:'studionet',chain_id:61999,runs});
console.log('Merged 33 receipts; run verify-proofs.cjs --offline, then verify-proofs.cjs for fresh verification.');
