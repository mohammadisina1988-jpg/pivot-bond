const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const root=path.resolve(__dirname,'..'),repo='mohammadisina1988-jpg/pivot-bond';
const cases={split:['split-zero','amber-one','cobalt-two'],bundle:['bundle-zero','amber-one','cobalt-two'],review:['split-zero','review-one']};
const values={'split-zero':[0,0,18],'bundle-zero':[0,0,24],'amber-one':[11,0,11],'cobalt-two':[0,10,10],'review-one':[11,0,-1]};
const canonical=x=>Array.isArray(x)?x.map(canonical):x&&typeof x==='object'?Object.fromEntries(Object.keys(x).sort().map(k=>[k,canonical(x[k])])):x;
const equal=(a,b)=>JSON.stringify(canonical(a))===JSON.stringify(canonical(b));
const clone=x=>JSON.parse(JSON.stringify(x));
function assert(ok,message){if(!ok)throw Error(message);}
function descriptor(id,i,revision){const name=cases[id][i];return {url:`https://raw.githubusercontent.com/${repo}/${revision}/fixtures/${name}.json`,sha256:crypto.createHash('sha256').update(fs.readFileSync(path.join(root,'fixtures',name+'.json'))).digest('hex')};}
function args(id,revision,accounts){return [repo,'rights-auction',['Amber','Cobalt'],accounts.slice(1,1+cases[id].length),cases[id].map(()=>30)];}
function configuration(a){return {repository:a[0],auction:a[1],items:a[2],bidders:a[3],initial_credits:a[4]};}
function initial(id,revision,accounts){const config=configuration(args(id,revision,accounts)),n=cases[id].length;return {configuration:config,seller:accounts[0],bids:Array(n).fill(null),credits:Array(n).fill(30),escrow:Array(n).fill(0),approved:Array(n).fill(false),owners:Array(2).fill(accounts[0]),seller_credits:0,phase:'OPEN',settlement:null,transfers:[]};}
function allocations(vectors,m,excluded=-1){
 // Independent disjoint-bundle enumeration; the contract enumerates item owners.
 const n=vectors.length,candidates=[];
 function visit(i,used,masks){
  if(i===n){
   const owners=Array.from({length:m},(_,bit)=>{const owner=masks.findIndex(mask=>mask&(1<<bit));return owner<0?n:owner;});
   candidates.push({welfare:masks.reduce((s,mask,j)=>s+(j===excluded?0:vectors[j][mask]),0),masks:[...masks],owners});return;
  }
  for(let mask=0;mask<(1<<m);mask++)if(!(mask&used)&&(i!==excluded||mask===0))visit(i+1,used|mask,[...masks,mask]);
 }
 visit(0,0,[]);
 candidates.sort((a,b)=>b.welfare-a.welfare||a.owners.filter(x=>x<n).length-b.owners.filter(x=>x<n).length||a.owners.reduce((d,x,i)=>d||x-b.owners[i],0));
 return candidates[0];
}
function oracle(vectors,m){const chosen=allocations(vectors,m),counterfactuals=vectors.map((_,i)=>allocations(vectors,m,i));return {...chosen,counterfactuals,payments:counterfactuals.map((x,i)=>x.welfare-(chosen.welfare-vectors[i][chosen.masks[i]]))};}
function check(s,id,revision,accounts){
 assert(Object.keys(s).sort().join(',')==='approved,bids,configuration,credits,escrow,owners,phase,seller,seller_credits,settlement,transfers','Full state schema');
 assert(equal(s.configuration,configuration(args(id,revision,accounts)))&&s.seller===accounts[0],'Frozen participants and endowment');
 const n=cases[id].length;
 assert([s.bids,s.credits,s.escrow,s.approved].every(x=>Array.isArray(x)&&x.length===n)&&s.owners.length===2,'Ledger dimensions');
 assert([...s.credits,...s.escrow,s.seller_credits].every(x=>Number.isSafeInteger(x)&&x>=0),'Nonnegative credit ledger');
 assert([...s.credits,...s.escrow,s.seller_credits].reduce((a,b)=>a+b,0)===30*n,'Conserved credits including seller and reserve');
 assert(s.approved.every(x=>typeof x==='boolean')&&s.owners.every(a=>/^0x[a-f0-9]{40}$/.test(a)),'Ownership and consent types');
 s.bids.forEach((bid,i)=>{
  if(bid===null)return;
  const d=descriptor(id,i,revision);assert(bid.url===d.url&&bid.sha256===d.sha256,'Signed bid descriptor');
  if(bid.status==='SUBMITTED'){assert(Object.keys(bid).sort().join(',')==='sha256,status,url','Submitted schema');return;}
  const source=JSON.parse(fs.readFileSync(path.join(root,'fixtures',cases[id][i]+'.json'))),v=bid.valuation;
  assert(Object.keys(bid).sort().join(',')==='sha256,source,status,url,valuation'&&equal(bid.source,source)&&Object.keys(v).sort().join(',')==='anchors,values'&&equal(v.values,values[cases[id][i]]),'Complete source and exact bundle totals');
  assert(bid.status===(v.values.includes(-1)?'REVIEW':'VALUED'),'Exact ambiguity boundary');
  assert(Array.isArray(v.anchors)&&v.anchors.length===3&&v.anchors.every((a,j)=>Array.isArray(a)&&a.length<=4&&(v.values[j]===-1||a.length>0)&&a.every(k=>Number.isInteger(k)&&k>=0&&k<source.clauses.length)&&equal(a,[...new Set(a)].sort((x,y)=>x-y))),'Every source anchor');
 });
}
function plan(id,accounts,revision){
 const p=[],n=cases[id].length;
 const add=(label,caller,method,args=[],error)=>p.push({label:id+'-'+label,caller,method,args,...(error?{error}:{})});
 for(let i=0;i<n;i++){const d=descriptor(id,i,revision);add('submit-'+i,i+1,'submit',[d.url,d.sha256]);}
 for(let i=0;i<n;i++)add('interpret-'+i,0,'interpret',[i]);
 if(id==='review'){
  add('approve-0',1,'approve',[values['split-zero']]);
  add('reject-ambiguous',2,'approve',[[11,0,20]],'[EXPECTED] Complete valuation required');
  add('abort',2,'abort');add('reject-late-settle',0,'settle',[],'[EXPECTED] Every bidder must approve');
 }else{
  for(let i=0;i<n;i++)add('approve-'+i,i+1,'approve',[values[cases[id][i]]]);
  add('settle',0,'settle');
  if(id==='split'){
   add('reject-nonholder',1,'transfer_right',[0,accounts[1]],'[EXPECTED] Right owner only');
   add('holder-transfer',2,'transfer_right',[0,accounts[1]]);
  }
 }
 return p;
}
function replay(before,item,after,id,revision,accounts){
 check(before,id,revision,accounts);check(after,id,revision,accounts);
 const expected=clone(before),i=item.caller-1;
 if(item.error){assert(equal(before,after),'Rejected call changed state');return;}
 if(item.method==='submit'){expected.bids[i]={url:item.args[0],sha256:item.args[1],status:'SUBMITTED'};}
 else if(item.method==='interpret'){
  const j=item.args[0];expected.bids[j]=clone(after.bids[j]);
  assert(after.bids[j].status===(values[cases[id][j]].includes(-1)?'REVIEW':'VALUED'),'Interpreted bid status');
 }else if(item.method==='approve'){
  assert(i>=0&&!before.approved[i]&&equal(item.args[0],before.bids[i].valuation.values),'Exact signed consent');
  const reserve=Math.max(...item.args[0]);expected.credits[i]-=reserve;expected.escrow[i]=reserve;expected.approved[i]=true;
  if(expected.approved.every(Boolean))expected.phase='READY';
 }else if(item.method==='abort'){
  for(let j=0;j<expected.credits.length;j++){expected.credits[j]+=expected.escrow[j];expected.escrow[j]=0;}expected.phase='ABORTED';
 }else if(item.method==='settle'){
  assert(before.phase==='READY','Only approved bids settle');const vectors=before.bids.map(b=>[0,...b.valuation.values]),result=oracle(vectors,2);
  assert(result.payments.every((x,j)=>Number.isInteger(x)&&x>=0&&x<=vectors[j][result.masks[j]]&&x<=before.escrow[j]),'Externality payment bounds');
  expected.settlement=result;expected.phase='SETTLED';expected.seller_credits=result.payments.reduce((a,b)=>a+b,0);
  expected.credits=before.credits.map((x,j)=>x+before.escrow[j]-result.payments[j]);expected.escrow=before.escrow.map(()=>0);
  expected.owners=result.owners.map(owner=>owner===vectors.length?accounts[0]:accounts[owner+1]);
 }else if(item.method==='transfer_right'){
  const [right,recipient]=item.args;assert(before.owners[right]===accounts[item.caller],'Signed holder');expected.owners[right]=recipient;
  expected.transfers.push({item:right,sender:accounts[item.caller],recipient});
 }else throw Error('Unknown action');
 assert(equal(expected,after),'Every field must match independent state replay: '+item.label);
}
module.exports={cases,values,args,descriptor,initial,plan,replay,oracle,check};
