(function(){
'use strict';
var $=function(s){return document.querySelector(s)};
var $$=function(s){return Array.prototype.slice.call(document.querySelectorAll(s))};
var palette=['#0e7c74','#7c5cbf','#3b6fd4','#b7791f','#c4533a'];
var colorIndex=0;
var doneTasks=[
  {title:'后端周接口与导出接口',goal:'个人网站 P0',imp:'高',note:'含按周筛选、顺延与导出文本，导出支持 Markdown 与 CSV。',doneAt:'昨天 21:04',color:'#0e7c74'},
  {title:'跑步 5 公里',goal:'健身 3 次',imp:'中',note:'配速 6 分半，状态不错。',doneAt:'周二 19:10',color:'#7c5cbf'},
  {title:'读完前半',goal:'读完《小王子》',imp:'低',note:'',doneAt:'周三 22:30',color:'#3b6fd4'}
];
function esc(s){return String(s==null?'':s).replace(/[&<>"']/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]})}
function goalColor(name){
  if(!name)return '#0e7c74';
  var card=$$('.goal-card').filter(function(g){return g.querySelector('h3').textContent===name})[0];
  if(card)return (card.style.getPropertyValue('--c')||'#0e7c74').trim();
  return '#0e7c74';
}
function impCls(i){return i==='高'?'high':i==='中'?'mid':'low'}
function formatNow(){var d=new Date();return '今天 '+String(d.getHours()).padStart(2,'0')+':'+String(d.getMinutes()).padStart(2,'0')}

var modals={};
function openModal(name){var m=modals[name];if(!m)return;m.classList.add('show');document.body.style.overflow='hidden'}
function closeModal(name){var m=modals[name];if(!m)return;m.classList.remove('show');if(!$$('.modal-overlay.show').length)document.body.style.overflow=''}

function buildModals(){
  var add=document.createElement('div');add.className='modal-overlay';add.id='addModal';
  add.innerHTML=
    '<div class="modal" role="dialog" aria-label="添加">'+
    '<div class="modal-head"><h3>添加</h3><button class="close" data-close="addModal" aria-label="关闭">×</button></div>'+
    '<div class="seg" id="addSeg">'+
    '<button class="on" data-addtype="task">日任务</button>'+
    '<button data-addtype="goal">周目标</button></div>'+
    '<div class="form" id="taskFields">'+
    '<label>内容</label><input id="fTitle" type="text" placeholder="今天要做的一件事">'+
    '<div class="form-row"><div><label>重要度</label><select id="fImp"><option>高</option><option selected>中</option><option>低</option></select></div>'+
    '<div><label>日期</label><input id="fDate" type="date"></div></div>'+
    '<label>属于哪个方向（可留空）</label><select id="fGoal"></select>'+
    '<label>备注（可选）</label><textarea id="fNote" rows="2" placeholder="补充细节"></textarea></div>'+
    '<div class="form" id="goalFields" hidden>'+
    '<label>方向名称</label><input id="gTitle" type="text" placeholder="本周想推进的大方向">'+
    '<label>备注（可选）</label><textarea id="gNote" rows="2" placeholder="一句话说明这个方向"></textarea></div>'+
    '<div class="modal-foot"><button class="btn ghost" data-close="addModal">取消</button><button class="btn" id="addConfirm">添加</button></div></div>';
  document.body.appendChild(add);modals.add=add;

  var done=document.createElement('div');done.className='modal-overlay';done.id='doneModal';
  done.innerHTML='<div class="modal wide" role="dialog" aria-label="已完成任务">'+
    '<div class="modal-head"><h3>已完成任务</h3><button class="close" data-close="doneModal" aria-label="关闭">×</button></div>'+
    '<div class="done-body"><div class="done-list" id="doneList"></div><div class="done-detail" id="doneDetail"><p class="placeholder">选中左侧任务查看详情</p></div></div></div>';
  document.body.appendChild(done);modals.done=done;

  var rev=document.createElement('div');rev.className='modal-overlay';rev.id='reviewModal';
  rev.innerHTML='<div class="modal wide" role="dialog" aria-label="夜间复盘">'+
    '<div class="modal-head"><h3>夜间复盘 · 8月15日 周六</h3><button class="close" data-close="reviewModal" aria-label="关闭">×</button></div>'+
    '<div class="review-body">'+
    '<div class="review-main"><h4>未完成 · <span id="revCount">0</span> 项</h4><div id="revList"></div><button class="btn full" id="revAll">全部顺延到明天</button></div>'+
    '<div class="review-side"><h4>今日回顾</h4>'+
    '<div class="stat"><span class="k">今日专注</span><span class="v">45 分钟</span></div>'+
    '<div class="stat"><span class="k">今日日记</span><span class="v">未写</span></div>'+
    '<div class="stat"><span class="k">本周完成度</span><span class="v" id="weekNum">50%</span></div>'+
    '<div class="mini-bar" style="width:100%;margin-top:8px"><i id="weekBar" style="width:50%"></i></div>'+
    '<button class="btn ghost full" style="margin-top:16px">写今日日记 →</button>'+
    '</div></div></div>';
  document.body.appendChild(rev);modals.review=rev;
}

function setDateDefault(){
  var d=$('#fDate');if(!d)return;
  var n=new Date();d.value=new Date(n.getTime()-n.getTimezoneOffset()*60000).toISOString().slice(0,10);
}
function buildGoalOptions(){
  var sel=$('#fGoal');if(!sel)return;
  var opts=['（不归属方向）'].concat($$('.goal-card h3').map(function(h){return h.textContent}));
  sel.innerHTML=opts.map(function(o){return '<option>'+esc(o)+'</option>'}).join('');
}
var addType='task';
function openAdd(type){
  addType=type||'task';
  buildGoalOptions();setDateDefault();
  $$('#addSeg button').forEach(function(b){b.classList.toggle('on',b.dataset.addtype===addType)});
  $('#taskFields').hidden=addType!=='task';
  $('#goalFields').hidden=addType!=='goal';
  openModal('add');
  var input=addType==='task'?$('#fTitle'):$('#gTitle');
  if(input)setTimeout(function(){input.focus()},60);
}
function switchAddType(type){
  addType=type;
  $$('#addSeg button').forEach(function(b){b.classList.toggle('on',b.dataset.addtype===type)});
  $('#taskFields').hidden=type!=='task';
  $('#goalFields').hidden=type!=='goal';
}
function confirmAdd(){
  if(addType==='task'){
    var t=$('#fTitle').value.trim();if(!t){$('#fTitle').focus();return}
    var goal=$('#fGoal').value;
    if(goal==='（不归属方向）')goal='';
    addTaskRow(t,$('#fImp').value,goal,$('#fNote').value.trim());
    $('#fTitle').value='';$('#fNote').value='';
  }else{
    var g=$('#gTitle').value.trim();if(!g){$('#gTitle').focus();return}
    addGoalCard(g);
    $('#gTitle').value='';$('#gNote').value='';
  }
  closeModal('add');refreshAll();
}

function addTaskRow(title,imp,goalTitle,note){
  var color=goalColor(goalTitle)||'#0e7c74';
  var tag=goalTitle?'<span class="goal-tag"><i style="background:'+color+'"></i>'+esc(goalTitle)+'</span>':'';
  var row=document.createElement('div');row.className='task';row.dataset.title=title;row.dataset.imp=imp;
  row.innerHTML='<span class="check" aria-label="完成"></span>'+
    '<div class="task-main"><div class="task-title">'+esc(title)+tag+'</div>'+(note?'<div class="task-note">'+esc(note)+'</div>':'')+'</div>'+
    '<span class="imp '+impCls(imp)+'">'+esc(imp)+'</span>'+
    '<div class="task-actions"><button class="edit">编辑</button><button class="later">顺延明天</button></div>';
  var list=$('#todayList');
  if(list){
    var empty=list.querySelector('.empty');if(empty)empty.remove();
    list.appendChild(row);
  }
  return row;
}
function toggleTask(el){
  var row=el.closest('.task');if(!row||row.classList.contains('done'))return;
  row.classList.add('done');el.classList.add('on');
  var title=row.dataset.title||row.querySelector('.task-title').childNodes[0].nodeValue.trim();
  var tag=row.querySelector('.goal-tag');
  var goal=tag?tag.textContent.trim():'';
  var imp=row.dataset.imp||'中';
  var noteEl=row.querySelector('.task-note');
  var note=noteEl?noteEl.textContent:'';
  var color=goalColor(goal);
  setTimeout(function(){
    doneTasks.unshift({title:title,goal:goal,imp:imp,note:note,doneAt:formatNow(),color:color});
    row.remove();
    refreshAll();
    if(modals.done.classList.contains('show'))renderDoneInto($('#doneList'),$('#doneDetail'));
    if($('#panel-done')&&$('#panel-done').classList.contains('show'))renderDoneTab();
    if(modals.review.classList.contains('show'))renderReviewInto($('#revList'));
    if($('#panel-review')&&$('#panel-review').classList.contains('show'))renderReviewTab();
  },260);
}
function rolloverRow(row){
  if(!row||row.classList.contains('done'))return;
  var tag=document.createElement('span');
  tag.className='goal-tag';tag.style.background='#faf1dd';tag.style.color='#92610a';
  tag.textContent='已顺延 → 明天';
  var t=row.querySelector('.task-title');if(t)t.appendChild(tag);
  row.classList.add('later');
  setTimeout(function(){
    row.remove();refreshAll();
    if(modals.review.classList.contains('show'))renderReviewInto($('#revList'));
    if($('#panel-review')&&$('#panel-review').classList.contains('show'))renderReviewTab();
  },360);
}
function rolloverAll(){
  $$('#todayList .task').filter(function(r){return !r.classList.contains('done')}).forEach(rolloverRow);
}

function updateGoal(card){
  var rows=card.querySelectorAll('.sub-row');
  var total=rows.length;
  var done=card.querySelectorAll('.sub-row .check.on').length;
  var pct=total?Math.round(done/total*100):0;
  var fg=card.querySelector('.ring .fg');if(fg)fg.style.setProperty('--p',pct);
  var num=card.querySelector('.ring-num');if(num)num.textContent=pct+'%';
  var meta=card.querySelector('.meta');if(meta)meta.textContent=done+'/'+total+' 子任务';
  card.classList.toggle('done',total>0&&done===total);
}
function toggleSub(el){el.classList.toggle('on');updateGoal(el.closest('.goal-card'));refreshAll()}
function addSubRow(card){
  var name=prompt('子任务内容：');
  if(!name||!name.trim())return;
  var subs=card.querySelector('.subs');
  var row=document.createElement('div');row.className='sub-row';
  row.innerHTML='<span class="check" aria-label="完成"></span><span class="name"></span>';
  row.querySelector('.name').textContent=name.trim();
  subs.insertBefore(row,subs.querySelector('.add-sub'));
  updateGoal(card);refreshAll();
}
function addGoalCard(title){
  var color=palette[colorIndex++%palette.length];
  var card=document.createElement('article');card.className='goal-card';card.style.setProperty('--c',color);
  card.innerHTML='<div class="card-top">'+
    '<svg class="ring" viewBox="0 0 58 58"><circle class="bg" cx="29" cy="29" r="20"/><circle class="fg" cx="29" cy="29" r="20" style="--p:0"/><text class="ring-num" x="29" y="33" text-anchor="middle">0%</text></svg>'+
    '<div><h3></h3><p class="meta">0/0 子任务</p></div></div>'+
    '<button class="toggle-subs">查看子任务 ▾</button>'+
    '<div class="subs"></div>';
  card.querySelector('h3').textContent=title;
  var subs=card.querySelector('.subs');
  var addSub=document.createElement('button');addSub.className='add-sub';addSub.textContent='＋ 子任务';
  addSub.onclick=function(){addSubRow(card)};
  subs.appendChild(addSub);
  var grid=$('#goalGrid');
  if(grid){
    var addCard=grid.querySelector('.add-card');
    if(addCard)grid.insertBefore(card,addCard);else grid.appendChild(card);
  }
  return card;
}

function renderDoneInto(list,detail){
  if(!list)return;
  list.innerHTML='';
  var groups={};
  doneTasks.forEach(function(t,i){var g=t.doneAt.split(' ')[0];(groups[g]=groups[g]||[]).push({t:t,i:i})});
  Object.keys(groups).forEach(function(g){
    var h=document.createElement('div');h.className='group-h';h.textContent=g;list.appendChild(h);
    groups[g].forEach(function(x){
      var b=document.createElement('button');b.className='done-item';b.dataset.i=x.i;
      b.innerHTML='<span class="t2"></span><span class="s2"></span>';
      b.querySelector('.t2').textContent=x.t.title;
      b.querySelector('.s2').textContent=(x.t.goal||'无方向')+' · '+x.t.imp+' · '+x.t.doneAt;
      list.appendChild(b);
    });
  });
  if(detail)detail.innerHTML='<p class="placeholder">选中左侧任务查看详情</p>';
}
function renderDoneModal(){
  renderDoneInto($('#doneList'),$('#doneDetail'));
}
function selectDone(i,btn){
  $$('.done-item').forEach(function(b){b.classList.toggle('on',b===btn)});
  var t=doneTasks[i];if(!t)return;
  var body=btn.closest('.done-body');
  var detail=body?body.querySelector('.done-detail'):null;if(!detail)return;
  detail.innerHTML='<h4></h4>'+
    '<div class="detail-meta"><span class="imp '+impCls(t.imp)+'">'+esc(t.imp)+'</span>'+
    '<span class="goal-tag"><i style="background:'+esc(t.color)+'"></i>'+esc(t.goal||'无方向')+'</span></div>'+
    '<p class="detail-note"></p>'+
    '<p class="detail-when">完成于 '+esc(t.doneAt)+'</p>'+
    '<button class="btn ghost" style="margin-top:18px" data-reopen="'+i+'">重新打开</button>';
  detail.querySelector('h4').textContent=t.title;
  detail.querySelector('.detail-note').textContent=t.note||'没有备注';
}
function reopenDone(i){
  var t=doneTasks.splice(i,1)[0];if(!t)return;
  addTaskRow(t.title,t.imp,t.goal,t.note);
  closeModal('done');
  refreshAll();renderDoneModal();
  if($('#panel-done')&&$('#panel-done').classList.contains('show'))renderDoneTab();
}

function renderReviewInto(list){
  if(!list)return;
  var rows=$$('#todayList .task').filter(function(r){return !r.classList.contains('done')});
  list.innerHTML='';
  rows.forEach(function(r){
    var title=r.dataset.title||'';
    var row=document.createElement('div');row.className='rev-row';
    row.innerHTML='<span class="title"></span><button class="do" data-revdo="">完成</button><button class="later" data-revlater="">顺延明天</button>';
    row.querySelector('.title').textContent=title;
    row.querySelector('[data-revdo]').dataset.revdo=title;
    row.querySelector('[data-revlater]').dataset.revlater=title;
    list.appendChild(row);
  });
  var c=$('#revCount');if(c)c.textContent=rows.length;
}
function renderReviewModal(){renderReviewInto($('#revList'))}
function revComplete(title){
  var row=$$('#todayList .task').filter(function(r){return r.dataset.title===title})[0];
  if(row){var c=row.querySelector('.check');if(c)toggleTask(c)}
}
function revLaterOne(title){
  var row=$$('#todayList .task').filter(function(r){return r.dataset.title===title})[0];
  if(row)rolloverRow(row);
}
function renderDoneTab(){renderDoneInto($('#doneTabList'),$('#doneTabDetail'))}
function renderReviewTab(){
  var list=$('#revTabList');if(!list)return;
  var rows=$$('#todayList .task').filter(function(r){return !r.classList.contains('done')});
  list.innerHTML='';
  rows.forEach(function(r){
    var title=r.dataset.title||'';
    var row=document.createElement('div');row.className='rev-row';
    row.innerHTML='<span class="title"></span><button class="do" data-revdo="">完成</button><button class="later" data-revlater="">顺延明天</button>';
    row.querySelector('.title').textContent=title;
    row.querySelector('[data-revdo]').dataset.revdo=title;
    row.querySelector('[data-revlater]').dataset.revlater=title;
    list.appendChild(row);
  });
  var c=$('#revTabCount');if(c)c.textContent=rows.length;
}
function refreshAll(){
  var rows=$$('#todayList .task');
  var undone=rows.filter(function(r){return !r.classList.contains('done')}).length;
  var done=doneTasks.length;
  var total=undone+done;
  var set=function(sel,fn){var el=$(sel);if(el)fn(el)};
  set('#todayNum',function(el){el.textContent=done+'/'+total});
  set('#todayBar',function(el){el.style.width=(total?Math.round(done/total*100):0)+'%'});
  set('#doneBadge',function(el){el.textContent=done});
  $$('.goal-card').forEach(updateGoal);
  var wTotal=0,wDone=0;
  $$('.goal-card').forEach(function(g){
    wTotal+=g.querySelectorAll('.sub-row').length;
    wDone+=g.querySelectorAll('.sub-row .check.on').length;
  });
  wTotal+=undone+done;wDone+=done;
  var pct=wTotal?Math.round(wDone/wTotal*100):0;
  set('#weekNum',function(el){el.textContent=pct+'%'});
  set('#weekBar',function(el){el.style.width=pct+'%'});
  var list=$('#todayList');
  if(list){
    var emp=list.querySelector('.empty');
    if(undone===0&&!emp){
      var e=document.createElement('p');e.className='empty';e.textContent='今天没有待办，点「添加」安排一件吧。';
      list.appendChild(e);
    }
    if(undone>0&&emp)emp.remove();
  }
}

function switchTab(name){
  $$('[data-tab]').forEach(function(b){b.classList.toggle('on',b.dataset.tab===name)});
  $$('[data-panel]').forEach(function(p){p.classList.toggle('show',p.dataset.panel===name)});
  if(name==='done')renderDoneTab();
  if(name==='review')renderReviewTab();
  if(name==='today')refreshAll();
}

document.addEventListener('click',function(e){
  var check=e.target.closest('.check');
  if(check){
    if(check.closest('.sub-row')){toggleSub(check);return}
    if(check.closest('.task')){toggleTask(check);return}
  }
  var open=e.target.closest('[data-open]');
  if(open){
    var name=open.dataset.open;
    if(name==='add')openAdd(open.dataset.type);
    else if(name==='done'){renderDoneModal();openModal('done')}
    else if(name==='review'){renderReviewModal();openModal('review')}
    return;
  }
  var close=e.target.closest('[data-close]');
  if(close){closeModal(close.dataset.close);return}
  var seg=e.target.closest('#addSeg button');
  if(seg){switchAddType(seg.dataset.addtype);return}
  var confirmBtn=e.target.closest('#addConfirm');
  if(confirmBtn){confirmAdd();return}
  var revAll=e.target.closest('#revAll,#revAll2');
  if(revAll){rolloverAll();return}
  var toggle=e.target.closest('.toggle-subs');
  if(toggle){toggle.closest('.goal-card').classList.toggle('open');return}
  var addSub=e.target.closest('.add-sub');
  if(addSub){addSubRow(addSub.closest('.goal-card'));return}
  var edit=e.target.closest('.task-actions .edit');
  if(edit){
    var row=edit.closest('.task');
    var cur=row.dataset.title||'';
    var t=prompt('任务内容',cur);
    if(t&&t.trim()){
      row.dataset.title=t.trim();
      row.querySelector('.task-title').childNodes[0].nodeValue=t.trim()+' ';
    }
    return;
  }
  var later=e.target.closest('.task-actions .later');
  if(later){rolloverRow(later.closest('.task'));return}
  var tab=e.target.closest('[data-tab]');
  if(tab){switchTab(tab.dataset.tab);return}
  var item=e.target.closest('.done-item');
  if(item){selectDone(parseInt(item.dataset.i,10),item);return}
  var reopen=e.target.closest('[data-reopen]');
  if(reopen){reopenDone(parseInt(reopen.dataset.reopen,10));return}
  var revdo=e.target.closest('[data-revdo]');
  if(revdo){revComplete(revdo.dataset.revdo);return}
  var revlater=e.target.closest('[data-revlater]');
  if(revlater){revLaterOne(revlater.dataset.revlater);return}
  var compact=e.target.closest('.goal-card.compact .card-top');
  if(compact){compact.closest('.goal-card').classList.toggle('open');return}
});

buildModals();
refreshAll();
})();
