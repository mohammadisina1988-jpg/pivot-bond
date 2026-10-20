const fs=require('node:fs'),path=require('node:path');
const {root,assert,equal,digest,sourceHash,save,invoke,read,rpc,receipt}=require('./transport.cjs');
const {cases,args,descriptor,initial,plan,replay}=require('./scenario.cjs');
async function main(){
 assert(await rpc('eth_chainId',[])==='0xf22f','Gasless StudioNet only');
 const actors=JSON.parse(process.env.PIVOT_ACCOUNTS||'null');assert(actors?.length===4,'Seller and three distinct signing bidders');
 const accounts=actors.map(a=>a.address.toLowerCase()),revision=fs.readFileSync(path.join(root,'config/fixture-revision.txt'),'utf8').trim();assert(/^[a-f0-9]{40}$/.test(revision),'Pinned fixture revision');
 const suite=[];
 const selected=process.env.PIVOT_SCENARIO||'all';assert(selected==='all'||Object.hasOwn(cases,selected),'Unknown proof scenario');
 for(const id of selected==='all'?Object.keys(cases):[selected]){
  const a=args(id,revision,accounts);for(let i=0;i<cases[id].length;i++){const d=descriptor(id,i,revision),web=await fetch(d.url,{signal:AbortSignal.timeout(45000)});assert(web.ok&&digest(Buffer.from(await web.arrayBuffer()))===d.sha256,'Exact public bid');}
  process.env.PIVOT_ACCOUNT=actors[0].name;
  const deployment=await invoke(id+'-deployment',['deploy','--contract','contracts/pivot_bond.py','--args',...a.map(v=>typeof v==='string'?v:JSON.stringify(v))]);
  const r=await receipt(id+'-deployment',deployment,true),contract=r.to_address||r.recipient;
  const d={id,args:a,contract,deployment,accounts,fixture_revision:revision,source_sha256:sourceHash,network:'studionet',chain_id:61999};suite.push(d);save('suite',suite);
  assert(fs.readFileSync(path.join(root,'contracts/pivot_bond.py')).equals(Buffer.from(await rpc('gen_getContractCode',[contract]),'base64')),'Exact live source');
  let state=await read(id+'-initial',['call',contract,'get_state']);assert(equal(state,initial(id,revision,accounts)),'Initial native endowment');save(id+'-initial-state',state);
  const trace=[];
  for(const item of plan(id,accounts,revision)){
   process.env.PIVOT_ACCOUNT=actors[item.caller].name;const before=state;
   const transaction=await invoke(item.label,['write',contract,item.method,...(item.args.length?['--args',...item.args.map(v=>typeof v==='string'?v:JSON.stringify(v))]:[])]);
   const rr=await receipt(item.label,transaction,!item.error);assert((rr.from_address||rr.sender).toLowerCase()===accounts[item.caller],'Actual participant signature');
   state=await read(item.label+'-state',['call',contract,'get_state']);replay(before,item,state,id,revision,accounts);
   if(item.error){const raw=Buffer.from(rr.consensus_data.leader_receipt[0].result,'base64');assert(raw[0]===1&&raw.subarray(1).toString('utf8')===item.error,'Exact expected rejection bytes');}
   trace.push({...item,transaction,state_before:before,state});save(id+'-trace',trace);console.log('VERIFIED',item.label,state.phase,JSON.stringify({credits:state.credits,escrow:state.escrow,seller_credits:state.seller_credits,owners:state.owners}));
  }
  save(id+'-final-state',state);
 }
}
main().catch(e=>{console.error(e.stack,e.cause?.message||'');process.exitCode=1;});
