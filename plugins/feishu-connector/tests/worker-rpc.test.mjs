import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import {spawn} from 'node:child_process';
import {createInterface} from 'node:readline';
import path from 'node:path';
import os from 'node:os';
import {pathToFileURL} from 'node:url';

// The input is a freshly built package. All executions occur in a temporary
// fixture copy; never attach its fake services to a deployed worker directory.
if (!process.argv[2]) throw new Error('Usage: node worker-rpc.test.mjs <build-directory> [paperclip-installation]');
const packageDirectory=path.resolve(process.argv[2]);
const paperclipDirectory=path.resolve(process.argv[3]??'/data/Applications/paperclip');
const sdkPath=path.join(paperclipDirectory,'node_modules/@paperclipai/plugin-sdk');
const {createHostClientHandlers}=await import(pathToFileURL(path.join(sdkPath,'dist/host-client-factory.js')));
const {buildHeartbeatRunStatusLiveEventPayload}=await import(pathToFileURL(path.join(paperclipDirectory,'node_modules/@paperclipai/server/dist/services/heartbeat-run-status-payload.js')));
const fixtureDirectory=await fs.mkdtemp(path.join(os.tmpdir(),'cm-feishu-worker-rpc-'));
const workerDirectory=path.join(fixtureDirectory,'package');
await fs.cp(packageDirectory,workerDirectory,{recursive:true,errorOnExist:true,force:false});
await fs.mkdir(path.join(fixtureDirectory,'node_modules/@paperclipai'),{recursive:true});
await fs.symlink(sdkPath,path.join(fixtureDirectory,'node_modules/@paperclipai/plugin-sdk'),'dir');
const {default:manifest}=await import(pathToFileURL(path.join(workerDirectory,'dist/manifest.js')));
const workerPath=path.join(workerDirectory,'dist/worker.js');
const fakeCli=path.join(fixtureDirectory,'fixture-lark.cjs');
const fakeNativeCli=path.join(fixtureDirectory,'fixture-native.cjs');
const nativeControl=path.join(fixtureDirectory,'native-control.json');
const nativeCapture=path.join(fixtureDirectory,'native-calls.jsonl');
const larkCapture=path.join(fixtureDirectory,'lark-calls.jsonl');
await fs.writeFile(nativeCapture,'');
await fs.writeFile(larkCapture,'');
await fs.writeFile(nativeControl,JSON.stringify({ready:[]}));
await fs.writeFile(fakeCli,`#!${process.execPath}
const fs=require('node:fs');
const args=process.argv.slice(2);
if(args.includes('+subscribe')) { setInterval(()=>{},1000); }
else {
  fs.appendFileSync(${JSON.stringify(larkCapture)},JSON.stringify(args)+'\\n');
  const id=args[args.indexOf('--message-id')+1]??'unknown';
  process.stdout.write(JSON.stringify({code:0,data:{message_id:'om_reply_'+id}}));
}
`,{mode:0o700});
await fs.writeFile(fakeNativeCli,`#!${process.execPath}
const fs=require('node:fs');
let text=''; process.stdin.on('data',chunk=>text+=chunk);
process.stdin.on('end',()=>{
  const request=JSON.parse(text);
  fs.appendFileSync(${JSON.stringify(nativeCapture)},JSON.stringify(request)+'\\n');
  const control=JSON.parse(fs.readFileSync(${JSON.stringify(nativeControl)},'utf8'));
  const shared={ok:true,conversationIssueId:'native-conversation-fixture',commentId:'comment-'+request.messageId};
  const response=request.operation==='send'?{...shared,status:'submitted'}:
    control.ready.includes(request.messageId)?{...shared,status:'replied',text:'native result '+request.messageId,runId:'run-'+request.messageId,replyCommentId:'reply-'+request.messageId}:
    {...shared,status:'running'};
  process.stdout.write(JSON.stringify(response));
});
`,{mode:0o700});
const readCapture=async filename=>(await fs.readFile(filename,'utf8')).split('\n').filter(Boolean).map(JSON.parse);
const company='company-fixture';
let config={larkCliBin:fakeCli,dryRunCli:true,enableEventSubscriber:true,enableQuickReply:true,quickReplyRegex:'^ping$',quickReplyText:'ok',ackOnInbound:false,connections:[{id:'selected',name:'CM fixture',profileName:'fictional-profile',enabled:true}],routes:[{id:'r1',connectionId:'selected',matchType:'chat',chatId:'oc_fixture',companyId:company,targetAgentId:'agent-fixture',replyMode:'thread'}]};
const state=new Map(),entities=new Map();
const key=p=>JSON.stringify([p.scopeKind,p.scopeId,p.namespace,p.stateKey]);
const entityKey=p=>JSON.stringify([p.scopeKind,p.scopeId,p.entityType,p.externalId]);
const calls=[],denials=[],subscribers=[],notifications=[];
const sessions=new Map(); let issueCreates=0, sends=0, failSend=false; const fullIssue={id:"issue-full",companyId:company,identifier:"FX-2",title:"reply fixture",status:"backlog"};
const services={
 config:{get:async p=>{assert.equal(p.companyId,company);return config;}},
 state:{get:async p=>state.get(key(p))??null,set:async p=>{state.set(key(p),p.value);return null;},delete:async p=>{state.delete(key(p));return null;}},
 entities:{list:async p=>[...entities.values()].filter(e=>(!p.entityType||e.entityType===p.entityType)&&(!p.scopeId||e.scopeId===p.scopeId)&&(!p.externalId||e.externalId===p.externalId)),upsert:async p=>{const e={id:entityKey(p),...p};entities.set(entityKey(p),e);return e;}},
 companies:{get:async p=>({id:p.companyId,name:'Fixture',issuePrefix:'FX'})},
 db:{query:async()=>[],execute:async()=>({rowCount:1})},
 events:{subscribe:async p=>{subscribers.push(p);return null;}},
 metrics:{write:async()=>null},
 activity:{log:async()=>null},
 agentSessions:{create:async p=>{const row={...p,sessionId:'session-'+(sessions.size+1)};sessions.set(row.sessionId,row);return row;},sendMessage:async p=>{const row=sessions.get(p.sessionId);if(!row || row.companyId!==p.companyId || !row.taskKey.startsWith('plugin:paperclipai.feishu-connector:session:'))throw new Error('Session not found: '+p.sessionId);if(failSend)throw new Error('fixture dispatch unavailable');sends++;return {runId:'run-full-'+sends};}},
 issues:{get:async p=>p.issueId==='issue-full'?fullIssue:({id:'issue-fixture',companyId:company,identifier:'FX-1',title:'fixture completed',status:'done'}),listComments:async p=>p.issueId==='issue-full'?[{id:'source-comment',body:'original user request',authorUserId:'user-fixture'}]:[{id:'comment-final',body:'已完成：fixture result',authorAgentId:'agent-fixture',createdAt:new Date().toISOString()}],createComment:async()=>({id:'audit-comment'}),create:async()=>{issueCreates++;return fullIssue;}},
 agents:new Proxy({},{get(){throw new Error('model calls forbidden');}}),
};
const host=createHostClientHandlers({pluginId:'fixture-plugin',capabilities:manifest.capabilities,services});
async function start(){
 const child=spawn(process.execPath,[workerPath],{stdio:['pipe','pipe','pipe'],env:{PATH:'/usr/bin:/bin',LANG:'C.UTF-8',NODE_ENV:'test'}});const pending=new Map(),active=new Map();let seq=10000,stderr='';
 child.stderr.on('data',d=>stderr+=d);
 const lines=createInterface({input:child.stdout});
 const send=m=>child.stdin.write(JSON.stringify(m)+'\n');
 lines.on('line',async line=>{let m;try{m=JSON.parse(line);}catch{return;}
  if(m.method&&m.id!==undefined){calls.push(m);try{
   let context={};const ref=m.params?.companyId??(m.params?.scopeKind==='company'?m.params.scopeId:null)??m.params?.filter?.companyId;
   if(m.paperclipInvocationId){context=active.has(m.paperclipInvocationId)?{invocationScope:{companyId:active.get(m.paperclipInvocationId)}}:{invalidInvocationScope:true};}
   else if(ref===company)context={invocationScope:{companyId:company}};
   const h=host[m.method];if(!h)throw new Error('unsupported host RPC '+m.method);
   const result=await h(m.params??{},context);send({jsonrpc:'2.0',id:m.id,result:result??null});
  }catch(e){denials.push({method:m.method,message:e.message});send({jsonrpc:'2.0',id:m.id,error:{code:e.code??-32002,message:e.message}});}
  }else if(m.id!==undefined){const p=pending.get(m.id);if(p){pending.delete(m.id);active.delete(p.invocation);clearTimeout(p.timer);m.error?p.reject(new Error(m.error.message)):p.resolve(m.result);}}
  else if(m.method)notifications.push(m);
 });
 function request(method,params={},scope){return new Promise((resolve,reject)=>{const id=seq++,invocation=scope?'inv-'+id:undefined; if(invocation)active.set(invocation,scope);const timer=setTimeout(()=>reject(new Error(method+' timeout '+stderr)),10000);pending.set(id,{resolve,reject,timer,invocation});send({jsonrpc:'2.0',id,method,params,...(invocation?{paperclipInvocation:{id:invocation}}:{})});});}
 async function close(){try{await request('shutdown');}finally{child.stdin.end();await new Promise(resolve=>{if(child.exitCode!==null)return resolve();child.once('exit',resolve);setTimeout(()=>{child.kill('SIGKILL');resolve();},2000).unref();});}}
 return {request,close,notify:(method,params)=>send({jsonrpc:"2.0",method,params})};
}
try {
const raw={message_id:'om_rpc_fixture',chat_id:'oc_fixture',root_id:'om_rpc_root',sender_type:'user',sender_open_id:'ou_fixture',text:'ping'};
const results=[];
let r;
// A production worker may intentionally enforce stricter legacy delivery guards
// than the original baseline fixture. Exercise its newly added native branch.
if (!process.argv.includes('--native-only')) {
r=await start();
try{
 await r.request('initialize',{manifest,config:{},apiVersion:1,databaseNamespace:'plugin_fixture'});assert.equal(calls.length,0);results.push('unconfigured initialization makes no company API call');
 await r.request('configChanged',{companyId:company,config},company);const health=await r.request('health');assert.equal(health.details.activeSubscribers,1);assert.equal(subscribers.length,5);assert.ok(subscribers.every(s=>s.filter.companyId===company));results.push('configured company starts one listener and scoped completion subscriptions');
 const first=await r.request('performAction',{key:'simulate-inbound-message',params:{connectionId:'selected',raw}},company);assert.equal(first.quickReply,true);assert.equal(first.ok,true);assert.ok(calls.filter(c=>c.method==='state.set').every(c=>c.params.scopeKind==='company'&&c.params.scopeId===company));results.push('quick reply stores deduplication within the selected company');
 const before=calls.length;await assert.rejects(r.request('getData',{key:'status'},'other-company'),/scope|company/i);assert.ok(calls.slice(before).some(c=>c.method==='config.get'));results.push('real host SDK rejects an action invocation from another company');
 await assert.rejects(r.request('configChanged',{companyId:'other-company',config:{...config,enableEventSubscriber:false}},'other-company'),/company|tenant/i);results.push('second-company configuration cannot replace selected identity');
}finally{await r.close();}
r=await start();
try{
 await r.request('initialize',{manifest,config:{},apiVersion:1,databaseNamespace:'plugin_fixture'});
 await r.request('configChanged',{companyId:company,config},company);
 const health=await r.request('health');assert.equal(health.details.activeSubscribers,1);results.push('cold restart plus host config replay restores listener');
 const dup=await r.request('performAction',{key:'simulate-inbound-message',params:{connectionId:'selected',raw}},company);assert.equal(dup.duplicate,true);results.push('persisted company-scoped deduplication survives worker restart');
 const session={connectionId:'selected',sessionKey:'feishu:selected:oc_fixture:root:om_complete',routeId:'r1',chatId:'oc_fixture',rootMessageId:'om_complete',lastMessageId:'om_complete',paperclipIssueId:'issue-fixture',paperclipAgentId:'agent-fixture',lastRunId:'run-fixture',updatedAt:new Date().toISOString()};
 const entity={entityType:'feishu-session',scopeKind:'company',scopeId:company,externalId:session.sessionKey,data:session};entities.set(entityKey(entity),entity);
 await r.request('onEvent',{event:{eventType:'issue.updated',companyId:company,entityType:'issue',entityId:'issue-fixture',payload:{issueId:'issue-fixture'}}},company);
 const updated=entities.get(entityKey(entity));assert.equal(updated.data.lastRunStatus,'done');assert.ok(updated.data.lastCompletionReplyKey);results.push('completion event writes final reply state within selected company');
 const fullRaw={...raw,message_id:'om_full',root_id:'om_full',text:'Reply with the fixture marker.'};
 failSend=true;
 await assert.rejects(r.request('performAction',{key:'simulate-inbound-message',params:{connectionId:'selected',raw:fullRaw}},company),/fixture dispatch unavailable/);
 assert.equal(issueCreates,1);assert.equal(sends,0);failSend=false;
 const retryParams={connectionId:'selected',raw:fullRaw,retryIssueId:'issue-full'};
 await assert.rejects(r.request('performAction',{key:'simulate-inbound-message',params:{...retryParams,raw:{...fullRaw,message_id:'om_other'}}},company),/same persisted/);
 const accepted=await r.request('performAction',{key:'simulate-inbound-message',params:retryParams},company);
 assert.equal(accepted.runId,'run-full-1');assert.equal(issueCreates,1);assert.equal(sends,1);
 const dispatched=calls.filter(c=>c.method==='agents.sessions.sendMessage').at(-1).params;
 assert.match(dispatched.prompt,/Paperclip issueId: issue-full/);assert.match(dispatched.prompt,/最终文本/);assert.doesNotMatch(dispatched.prompt,/只有一张 JSON|不要输出纯文本|finish_card 提交/);
 assert.equal(dispatched.issueId,undefined);
 results.push('ordinary text reaches SDK session dispatch with host ownership prefix, explicit issue prompt and no-card instructions');
 const fullEntity=[...entities.values()].find(e=>e.data?.paperclipIssueId==='issue-full');
 await assert.rejects(r.request('performAction',{key:'simulate-inbound-message',params:retryParams},company),/same persisted/);
 const noRetry=await r.request('performAction',{key:'simulate-inbound-message',params:{connectionId:'selected',raw:fullRaw}},company);assert.equal(noRetry.duplicate,true);assert.equal(sends,1);
 results.push('failed dispatch recovery preserves issue and exact source, refuses other messages and already accepted runs');
 await r.request('onEvent',{event:{eventType:'agent.run.finished',companyId:company,entityType:'run',entityId:'run-full-1',payload:{runId:'run-full-1',agentId:'agent-fixture',status:'succeeded'}}},company);
 await new Promise(resolve=>setTimeout(resolve,40));
 assert.equal(entities.get(entityKey(fullEntity)).data.lastCompletionReplyKey,undefined);
 const payload=buildHeartbeatRunStatusLiveEventPayload({id:'run-full-1',agentId:'agent-fixture',status:'succeeded',resultJson:{nativeResult:{schema:'paperclip.run_result.v1',summary:'CM full-path reply marker',reportedWorkDisposition:'completed'}}});
 assert.equal(payload.finalText,'CM full-path reply marker');
 r.notify('agents.sessions.event',{sessionId:dispatched.sessionId,runId:'run-full-1',eventType:'done',stream:'system',message:payload.finalText,payload});
 await new Promise(resolve=>setTimeout(resolve,100));
 const completed=entities.get(entityKey(fullEntity)).data;
 assert.equal(completed.lastRunStatus,'done');assert.ok(completed.lastCompletionReplyKey);assert.equal(completed.cardSession,undefined);
 results.push('actual host terminal payload supplies final text; earlier domain event and user source comment cannot consume completion');
 assert.equal(denials.length,2);assert.ok(denials.some(d=>d.message==='fixture dispatch unavailable'));results.push('host SDK gate enforced; session/model/Feishu transport remain offline fixtures');
}finally{await r.close();}

}
// Enable native private-chat routing only after exercising the unchanged legacy
// task path. The CLI records transport requests; it does not invoke a model.
const binding={companyId:company,agentId:'agent-fixture',connectionId:'selected',chatId:'oc_fixture',senderOpenId:'ou_fixture'};
config={...config,dryRunCli:false,enableQuickReply:false,nativeConversation:{enabled:true,command:fakeNativeCli,configPath:nativeControl,bindings:[binding]}};
const nativeRaw=(messageId,rootId,senderOpenId='ou_fixture')=>({
 message_id:messageId,chat_id:'oc_fixture',chat_type:'p2p',root_id:rootId,
 sender_type:'user',sender_open_id:senderOpenId,text:'Please continue the current conversation.'
});
const firstNative=nativeRaw('om_native_first','om_root_first');
const secondNative=nativeRaw('om_native_second','om_root_second');
const legacyCounts={issues:issueCreates,sends,sessions:sessions.size};
r=await start();
try{
 await r.request('initialize',{manifest,config:{},apiVersion:1,databaseNamespace:'plugin_fixture'});
 await r.request('configChanged',{companyId:company,config},company);
 const first=await r.request('performAction',{key:'simulate-inbound-message',params:{connectionId:'selected',raw:firstNative}},company);
 const second=await r.request('performAction',{key:'simulate-inbound-message',params:{connectionId:'selected',raw:secondNative}},company);
 assert.equal(first.nativeConversation,true);assert.equal(second.nativeConversation,true);
 assert.equal(first.status,'submitted');assert.equal(second.status,'submitted');
 assert.equal(first.conversationIssueId,'native-conversation-fixture');
 assert.equal(second.conversationIssueId,first.conversationIssueId);
 assert.deepEqual({issues:issueCreates,sends,sessions:sessions.size},legacyCounts);
 const sendsBefore=(await readCapture(nativeCapture)).filter(call=>call.operation==='send');
 assert.equal(sendsBefore.length,2);
 assert.ok(sendsBefore.every(call=>Object.entries(binding).every(([field,value])=>call[field]===value)));
 const nativeRows=[...entities.values()].filter(row=>row.entityType==='feishu-native-turn');
 assert.equal(nativeRows.length,2);assert.ok(nativeRows.every(row=>row.scopeId===company&&row.data.phase==='submitted'));
 assert.deepEqual(nativeRows.map(row=>row.data.source.rootMessageId).sort(),['om_root_first','om_root_second']);
 results.push('real worker hooks route two independent message roots to one native conversation without legacy issue/session dispatch');
 const callsBefore=(await readCapture(nativeCapture)).length;
 const duplicate=await r.request('performAction',{key:'simulate-inbound-message',params:{connectionId:'selected',raw:firstNative}},company);
 assert.equal(duplicate.duplicate,true);assert.equal((await readCapture(nativeCapture)).length,callsBefore);
 results.push('native duplicate delivery cannot submit another model turn');
 const denied=await r.request('performAction',{key:'simulate-inbound-message',params:{connectionId:'selected',raw:nativeRaw('om_wrong_owner','om_other_root','ou_wrong_owner')}},company);
 assert.equal(denied.reason,'native_identity_denied');assert.equal((await readCapture(nativeCapture)).length,callsBefore);
 results.push('wrong Feishu owner is rejected before native CLI execution');
 await assert.rejects(r.request('performAction',{key:'simulate-inbound-message',params:{connectionId:'selected',raw:firstNative}},'other-company'),/scope|company/i);
 assert.equal((await readCapture(nativeCapture)).length,callsBefore);
 results.push('real host SDK company scope prevents native routing from another company');
}finally{await r.close();}

r=await start();
try{
 await r.request('initialize',{manifest,config:{},apiVersion:1,databaseNamespace:'plugin_fixture'});
 await r.request('configChanged',{companyId:company,config},company);
 const restored=(await readCapture(nativeCapture)).filter(call=>call.operation==='status');
 assert.deepEqual(restored.map(call=>call.messageId).sort(),['om_native_first','om_native_second']);
 assert.equal((await readCapture(nativeCapture)).filter(call=>call.operation==='send').length,2);
 const duplicate=await r.request('performAction',{key:'simulate-inbound-message',params:{connectionId:'selected',raw:secondNative}},company);
 assert.equal(duplicate.duplicate,true);
 results.push('cold restart and config replay recover both pending native turns without resubmission');
 await fs.writeFile(nativeControl,JSON.stringify({ready:['om_native_first']}));
 const doneEvent={event:{eventType:'agent.run.finished',companyId:company,entityType:'run',entityId:'native-run-first',payload:{runId:'native-run-first',agentId:'agent-fixture',status:'succeeded'}}};
 await r.request('onEvent',doneEvent,company);
 await r.request('onEvent',doneEvent,company);
 const replies=(await readCapture(larkCapture)).filter(args=>args.includes('+messages-reply'));
 assert.equal(replies.length,1,JSON.stringify({notifications:notifications.filter(n=>n.params?.level==='error'),nativeCalls:await readCapture(nativeCapture),larkCalls:await readCapture(larkCapture)}));
 assert.equal(replies[0][replies[0].indexOf('--message-id')+1],'om_native_first');
 assert.equal(replies[0][replies[0].indexOf('--text')+1],'native result om_native_first');
 assert.ok(!replies[0].includes('--reply-in-thread'), 'private-chat replies stay in the main chat stream');
 assert.ok(replies[0][replies[0].indexOf('--idempotency-key')+1].length <= 50, 'real lark-cli idempotency limit');
 const firstRow=[...entities.values()].find(row=>row.entityType==='feishu-native-turn'&&row.data.source.messageId==='om_native_first');
 const secondRow=[...entities.values()].find(row=>row.entityType==='feishu-native-turn'&&row.data.source.messageId==='om_native_second');
 assert.equal(firstRow.data.phase,'delivered');assert.ok(firstRow.data.replyMessageId);
 assert.equal(secondRow.data.phase,'submitted');
 assert.deepEqual({issues:issueCreates,sends,sessions:sessions.size},legacyCounts);
 results.push('actual run-completion hook flushes one exact final reply; repeated events remain quiet and the next pending turn survives');
}finally{await r.close();}
console.log(JSON.stringify({passed:results.length,cases:results,expectedCrossCompanyDenials:denials,nativeCliSubmissions:(await readCapture(nativeCapture)).filter(call=>call.operation==='send').length,capturedNativeReplies:(await readCapture(larkCapture)).filter(args=>args.includes('+messages-reply')).length,realFeishuCalls:0,modelCalls:0},null,2));
}finally{await fs.rm(fixtureDirectory,{recursive:true,force:true});}
