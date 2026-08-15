(function(){
'use strict';
var $=function(s){return document.querySelector(s)};
var $$=function(s){return Array.prototype.slice.call(document.querySelectorAll(s))};
var palette=['#0e7c74','#7c5cbf','#3b6fd4','#b7791f','#c4533a'];
var colorIndex=0;
var doneTasks=[
  {title:'后端周接口与导出接口',goal:'个人网站 P0',imp:'高',note:'含按周筛选、顺延与导出文本，导出支持 Markdown 与 CSV。',doneAt:'昨天 21:04',color:'#0e7c74'},
  {title:'跑步 5 公里',goal:'健身 3 次',imp:'中',note:'配速 6 分半，状态不错。',doneAt:'周二 19:10',color:'#7c5cbf'},
  {title:'读完前半',goal:'读完《小王子》',imp:'中',note:'',doneAt:'周三 22:30',color:'#3b6fd4'}
];
var picked={gid:null,sid:null};
var currentGoalCard=null;
var currentTaskRow=null;
var currentSubRow=null;
var currentReviewRow=null;
function esc(s){return String(s==null?'':s).replace(/[&<>"']/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]})}
function goalColor(name){
  if(!name)return '#0e7c74';
  var card=$$('.goal-card').filter(function(g){return g.querySelector('h3').textContent===name})[0];
  if(card)return (card.style.getPropertyValue('--c')||'#0e7c74').trim();
  return '#0e7c74';
}
function impCls(i){return i==='高'?'high':i==='中'?'mid':'low'}
function formatNow(){var d=new Date();return '今天 '+String(d.getHours()).padStart(2,'0')+':'+String(d.getMinutes()).padStart(2,'0')}
function openModal(name){var m=document.getElementById(name+'Modal');if(m){m.classList.add('show');document.body.style.overflow='hidden'}}
function closeModal(name){var m=document.getElementById(name+'Modal');if(m){m.classList.remove('show');if(!$$('.modal-overlay.show').length)document.body.style.overflow=''}}

function buildModals(){
  var task=document.createElement('div');task.className='modal-overlay';task.id='taskModal';
  task.innerHTML=
    '<div class="modal" role="dialog" aria-label="添加任务">'+
    '<div class="modal-head"><h3>添加今日任务</h3><button class="close" data-close="taskModal" aria-label="关闭">×</button></div>'+
    '<div class="form">'+
    '<label>内容</label><input id="tTitle" type="text" placeholder="今天要做的一件事">'+
    '<div class="form-row"><div><label>重要度</label><select id="tImp"><option>高</option><option selected>中</option><option>低</option></select></div>'+
    '<div><label>日期</label><input id="tDate" type="date"></div></div>'+
    '<label>所属计划（可留空）</label><select id="tGoal"></select>'+
    '<label>备注（可选）</label><textarea id="tNote" rows="2" placeholder="补充细节"></textarea>'+
    '<div class="picker"><h5>从本周计划子任务挑选（点一个自动带过来）</h5><div id="subPicker"></div><p class="placeholder picker-note" style="display:none">本周还没有可挑的子任务</p></div>'+
    '</div>'+
    '<div class="modal-foot"><button class="btn ghost" data-close="taskModal">取消</button><button class="btn" id="taskConfirm">添加</button></div></div>';
  document.body.appendChild(task);
  var tg=$('#tGoal');
  if(tg)tg.addEventListener('change',function(){picked={gid:null,sid:null};renderSubPicker(this.value)});

  var goal=document.createElement('div');goal.className='modal-overlay';goal.id='goalModal';
  goal.innerHTML=
    '<div class="modal" role="dialog" aria-label="添加本周计划">'+
    '<div class="modal-head"><h3>添加本周计划</h3><button class="close" data-close="goalModal" aria-label="关闭">×</button></div>'+
    '<div class="form">'+
    '<label>计划名称</label><input id="gTitle" type="text" placeholder="本周想推进的大事">'+
    '<label>重要度</label><select id="gImp"><option>高</option><option selected>中</option><option>低</option></select>'+
    '<label>备注（可选）</label><textarea id="gNote" rows="2" placeholder="一句话说明这个计划"></textarea>'+
    '</div>'+
    '<div class="modal-foot"><button class="btn ghost" data-close="goalModal">取消</button><button class="btn" id="goalConfirm">添加</button></div></div>';
  document.body.appendChild(goal);

  var detail=document.createElement('div');detail.className='modal-overlay';detail.id='taskDetailModal';
  detail.innerHTML=
    '<div class="modal" role="dialog" aria-label="任务详情">'+
    '<div class="modal-head"><h3>任务详情</h3><button class="close" data-close="taskDetailModal" aria-label="关闭">×</button></div>'+
    '<div class="form">'+
    '<label>内容</label><input id="dtTitle" type="text">'+
    '<div class="form-row"><div><label>重要度</label><select id="dtImp"><option>高</option><option selected>中</option><option>低</option></select></div>'+
    '<div><label>日期</label><input id="dtDate" type="date"></div></div>'+
    '<label>所属计划（可留空）</label><select id="dtGoal"></select>'+
    '<label>备注</label><textarea id="dtNote" rows="3"></textarea>'+
    '</div>'+
    '<div class="modal-foot"><button class="btn ghost" data-close="taskDetailModal">取消</button><button class="btn" id="taskDetailSave">保存</button></div></div>';
  document.body.appendChild(detail);

  var sub=document.createElement('div');sub.className='modal-overlay';sub.id='subModal';
  sub.innerHTML=
    '<div class="modal" role="dialog" aria-label="子任务">'+
    '<div class="modal-head"><h3 id="subModalTitle">添加子任务</h3><button class="close" data-close="subModal" aria-label="关闭">×</button></div>'+
    '<div class="form">'+
    '<label>名字</label><input id="sTitle" type="text" placeholder="子任务名字">'+
    '<label>重要度</label><select id="sImp"><option>高</option><option selected>中</option><option>低</option></select>'+
    '<label>备注（可选）</label><textarea id="sNote" rows="2" placeholder="补充细节"></textarea>'+
    '</div>'+
    '<div class="modal-foot"><button class="btn ghost" data-close="subModal">取消</button><button class="btn" id="subSave">保存</button></div></div>';
  document.body.appendChild(sub);

  var done=document.createElement('div');done.className='modal-overlay';done.id='doneModal';
  done.innerHTML='<div class="modal wide" role="dialog" aria-label="已完成任务">'+
    '<div class="modal-head"><h3>已完成任务</h3><button class="close" data-close="doneModal" aria-label="关闭">×</button></div>'+
    '<div class="done-body"><div class="done-list" id="doneList"></div><div class="done-detail" id="doneDetail"><p class="placeholder">选中左侧任务查看详情</p></div></div></div>';
  document.body.appendChild(done);

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
  document.body.appendChild(rev);

  var rn=document.createElement('div');rn.className='modal-overlay';rn.id='reviewNoteModal';
  rn.innerHTML='<div class="modal" role="dialog" aria-label="顺延说明">'+
    '<div class="modal-head"><h3>计划复盘</h3><button class="close" data-close="reviewNoteModal" aria-label="关闭">×</button></div>'+
    '<div class="form">'+
    '<label>任务</label><p id="rnTask" style="font-size:14px;font-weight:600;margin-bottom:4px"></p>'+
    '<label>说明（可选）</label><textarea id="rnNote" rows="3" placeholder="写下为什么没完成，方便之后复盘…"></textarea>'+
    '</div>'+
    '<div class="modal-foot"><button class="btn ghost" data-close="reviewNoteModal">取消</button><button class="btn" id="rnConfirm">顺延到明天</button></div></div>';
  document.body.appendChild(rn);
}

function setDateDefault(){
  var d=$('#tDate');if(!d)return;
  var n=new Date();d.value=new Date(n.getTime()-n.getTimezoneOffset()*60000).toISOString().slice(0,10);
}
function buildGoalOptions(sel){
  if(!sel)return;
  var opts=['（不归属计划）'].concat($$('.goal-card h3').map(function(h){return h.textContent}));
  sel.innerHTML=opts.map(function(o){return '<option>'+esc(o)+'</option>'}).join('');
}
function renderSubPicker(goalTitle){
  var wrap=$('#subPicker');if(!wrap)return;
  var picker=wrap.closest('.picker');
  if(!goalTitle||goalTitle==='（不归属计划）'){
    if(picker)picker.style.display='none';
    return;
  }
  if(picker)picker.style.display='block';
  wrap.innerHTML='';
  var card=$$('.goal-card').filter(function(g){return g.querySelector('h3').textContent===goalTitle})[0];
  var any=false;
  if(card){
    var subs=Array.prototype.filter.call(card.querySelectorAll('.sub-row'),function(s){return !s.querySelector('.check').classList.contains('on')});
    var color=(card.style.getPropertyValue('--c')||'#0e7c74').trim();
    subs.forEach(function(s){
      any=true;
      var b=document.createElement('button');b.type='button';b.className='pick-item';b.dataset.gid=card.dataset.gid;b.dataset.sid=s.dataset.sid;
      b.innerHTML='<span class="dot" style="background:'+color+'"></span><span class="nm"></span>';
      b.querySelector('.nm').textContent=s.querySelector('.name').textContent;
      wrap.appendChild(b);
    });
  }
  var note=$('.picker-note');if(note)note.style.display=any?'none':'block';
}
function togglePick(item){
  var on=item.classList.contains('on');
  $$('.pick-item').forEach(function(b){b.classList.remove('on')});
  if(on){picked={gid:null,sid:null};return}
  item.classList.add('on');
  picked={gid:item.dataset.gid,sid:item.dataset.sid};
  var t=$('#tTitle');if(t)t.value=item.querySelector('.nm').textContent;
  var card=$('#goalGrid .goal-card[data-gid="'+item.dataset.gid+'"]');
  var sel=$('#tGoal');
  if(sel&&card){
    var gn=card.querySelector('h3').textContent;
    if(sel.querySelector('option[value="'+gn+'"]'))sel.value=gn;
  }
}
function openTaskModal(){
  buildGoalOptions($('#tGoal'));setDateDefault();
  renderSubPicker($('#tGoal').value);
  picked={gid:null,sid:null};
  openModal('task');
  var t=$('#tTitle');if(t)setTimeout(function(){t.focus()},60);
}
function openGoalModal(){
  openModal('goal');
  var t=$('#gTitle');if(t)setTimeout(function(){t.focus()},60);
}
function confirmTaskAdd(){
  var t=$('#tTitle').value.trim();if(!t){$('#tTitle').focus();return}
  var goal=$('#tGoal').value;
  if(goal==='（不归属计划）')goal='';
  addTaskRow(t,$('#tImp').value,goal,$('#tDate').value,$('#tNote').value.trim(),picked.gid,picked.sid);
  picked={gid:null,sid:null};
  $('#tTitle').value='';$('#tNote').value='';
  closeModal('task');refreshAll();
}
function confirmGoalAdd(){
  var t=$('#gTitle').value.trim();if(!t){$('#gTitle').focus();return}
  var card=addGoalCard(t,$('#gImp').value);
  $('#gTitle').value='';$('#gNote').value='';
  closeModal('goal');
  updateGoal(card);refreshAll();
  openGoalDetail(card);
}

function addTaskRow(title,imp,goalTitle,date,note,linkgid,linksid){
  var color=goalColor(goalTitle)||'#0e7c74';
  var row=document.createElement('div');row.className='task';row.dataset.title=title;row.dataset.imp=imp;row.dataset.date=date||'';row.dataset.goal=goalTitle||'';row.dataset.note=note||'';row.dataset.linkgid=linkgid||'';row.dataset.linksid=linksid||'';
  row.innerHTML='<span class="check" aria-label="完成"></span>'+
    '<div class="task-main"><div class="task-title">'+esc(title)+'</div></div>'+
    '<span class="task-goal'+(goalTitle?' goal-tag':'')+'">'+(goalTitle?'<i style="background:'+color+'"></i>'+esc(goalTitle):'')+'</span>'+
    '<span class="task-note">'+(note?esc(note):'')+'</span>'+
    '<span class="imp '+impCls(imp)+'">'+esc(imp)+'</span>';
  var list=$('#todayList');
  if(list){
    var empty=list.querySelector('.empty');if(empty)empty.remove();
    list.appendChild(row);
  }
  return row;
}
function openTaskDetail(row){
  if(!row)return;
  currentTaskRow=row;
  buildGoalOptions($('#dtGoal'));
  $('#dtTitle').value=row.dataset.title||'';
  $('#dtImp').value=row.dataset.imp||'中';
  $('#dtDate').value=row.dataset.date||'2026-08-15';
  var g=row.dataset.goal||'';
  var sel=$('#dtGoal');
  if(sel){
    if(g&&sel.querySelector('option[value="'+g+'"]'))sel.value=g;
    else sel.value='（不归属计划）';
  }
  $('#dtNote').value=row.dataset.note||'';
  openModal('taskDetail');
}
function saveTaskDetail(){
  if(!currentTaskRow)return;
  var t=$('#dtTitle').value.trim();if(!t){$('#dtTitle').focus();return}
  var goal=$('#dtGoal').value;
  if(goal==='（不归属计划）')goal='';
  var imp=$('#dtImp').value;
  var note=$('#dtNote').value.trim();
  currentTaskRow.dataset.title=t;
  currentTaskRow.dataset.imp=imp;
  currentTaskRow.dataset.goal=goal;
  currentTaskRow.dataset.note=note;
  currentTaskRow.dataset.date=$('#dtDate').value;
  var titleEl=currentTaskRow.querySelector('.task-title');
  titleEl.childNodes[0].nodeValue=t+' ';
  var tagEl=currentTaskRow.querySelector('.task-goal');
  tagEl.className='task-goal'+(goal?' goal-tag':'');
  tagEl.innerHTML=goal?'<i style="background:'+goalColor(goal)+'"></i>'+esc(goal):'';
  if(goal){
    tagEl.style.display='flex';
  }
  currentTaskRow.querySelector('.task-note').textContent=note;
  var impEl=currentTaskRow.querySelector('.imp');
  impEl.textContent=imp;
  impEl.className='imp '+impCls(imp);
  closeModal('taskDetail');refreshAll();
}

function toggleTask(el){
  var row=el.closest('.task');if(!row||row.classList.contains('done'))return;
  row.classList.add('done');el.classList.add('on');
  var title=row.dataset.title||row.querySelector('.task-title').childNodes[0].nodeValue.trim();
  var goal=row.dataset.goal||'';
  var imp=row.dataset.imp||'中';
  var note=row.dataset.note||'';
  var lg=row.dataset.linkgid,ls=row.dataset.linksid;
  setTimeout(function(){
    var link=null;
    if(lg&&ls){
      var card=$('#goalGrid .goal-card[data-gid="'+lg+'"]');
      if(card){
        var s=card.querySelector('.sub-row[data-sid="'+ls+'"]');
        if(s){
          s.querySelector('.check').classList.add('on');
          s.querySelector('.day').textContent='完成于 '+formatNow();
          updateGoal(card);renderGoalDetail();
          link={gid:lg,sid:ls};
        }
      }
    }
    doneTasks.unshift({title:title,goal:goal,imp:imp,note:note,doneAt:formatNow(),color:goalColor(goal),link:link});
    row.remove();
    refreshAll();
    if($('#doneModal')&&$('#doneModal').classList.contains('show'))renderDoneInto($('#doneList'),$('#doneDetail'));
    if($('#panel-done')&&$('#panel-done').classList.contains('show'))renderDoneTab();
    if($('#reviewModal')&&$('#reviewModal').classList.contains('show'))renderReviewInto($('#revList'));
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
    if($('#reviewModal')&&$('#reviewModal').classList.contains('show'))renderReviewInto($('#revList'));
    if($('#panel-review')&&$('#panel-review').classList.contains('show'))renderReviewTab();
  },360);
}
function rolloverAll(){$$('#todayList .task').filter(function(r){return !r.classList.contains('done')}).forEach(rolloverRow)}

function createSubRow(card,name,note,imp){
  var subs=card.querySelector('.subs');
  var max=0;
  subs.querySelectorAll('.sub-row').forEach(function(s){var n=parseInt(s.dataset.sid,10);if(!isNaN(n)&&n>=max)max=n+1});
  var row=document.createElement('div');row.className='sub-row';row.dataset.sid=max;row.dataset.imp=imp||'中';row.dataset.note=note||'';
  row.innerHTML='<span class="check"></span><span class="name"></span><span class="day">待完成</span>';
  row.querySelector('.name').textContent=name;
  subs.appendChild(row);
  return row;
}
function addGoalCard(title,imp){
  var color=palette[colorIndex++%palette.length];
  var card=document.createElement('article');card.className='goal-card';card.style.setProperty('--c',color);card.dataset.gid='g'+Date.now();card.dataset.imp=imp||'中';
  card.innerHTML='<div class="card-top">'+
    '<svg class="ring" viewBox="0 0 58 58"><circle class="bg" cx="29" cy="29" r="20"/><circle class="fg" cx="29" cy="29" r="20" style="--p:0"/><text class="ring-num" x="29" y="33" text-anchor="middle">0%</text></svg>'+
    '<div><h3></h3><p class="meta"><span class="mtext">0/0 子任务</span><span class="imp '+impCls(imp)+' goal-imp">'+esc(imp)+'</span></p></div></div>'+
    '<div class="subs"></div>';
  card.querySelector('h3').textContent=title;
  var grid=$('#goalGrid');
  if(grid)grid.appendChild(card);
  return card;
}
function updateGoal(card){
  var rows=card.querySelectorAll('.sub-row');
  var total=rows.length;
  var done=card.querySelectorAll('.sub-row .check.on').length;
  var pct=total?Math.round(done/total*100):0;
  var fg=card.querySelector('.ring .fg');if(fg)fg.style.setProperty('--p',pct);
  var num=card.querySelector('.ring-num');if(num)num.textContent=pct+'%';
  var mt=card.querySelector('.mtext');if(mt)mt.textContent=done+'/'+total+' 子任务';
  card.classList.toggle('done',total>0&&done===total);
}
function renderGoalDetail(){
  var body=$('#goalDetailBody');var card=currentGoalCard;if(!body||!card)return;
  var color=(card.style.getPropertyValue('--c')||'#0e7c74').trim();
  var title=card.querySelector('h3').textContent;
  var imp=card.dataset.imp||'中';
  var subs=card.querySelectorAll('.sub-row');
  var total=subs.length;
  var done=card.querySelectorAll('.sub-row .check.on').length;
  var pct=total?Math.round(done/total*100):0;
  var listHtml=total?'':'<p class="placeholder">还没有子任务，点右上角「添加子任务」加一条吧</p>';
  subs.forEach(function(s){
    var on=s.querySelector('.check').classList.contains('on');
    var note=s.dataset.note||'';
    var simp=s.dataset.imp||'中';
    listHtml+='<div class="goal-detail-sub"><span class="check'+(on?' on':'')+'" data-sid="'+esc(s.dataset.sid)+'"></span><span class="name">'+esc(s.querySelector('.name').textContent)+'</span>'+
      '<span class="note">'+(note?esc(note):'')+'</span>'+
      '<span class="imp '+impCls(simp)+'">'+esc(simp)+'</span>'+
      '<span class="day">'+esc(s.querySelector('.day').textContent)+'</span>'+
      '<button class="detail-del" data-del="'+esc(s.dataset.sid)+'">×</button></div>';
  });
  body.innerHTML='<div class="goal-detail-head">'+
    '<svg class="ring" viewBox="0 0 58 58"><circle class="bg" cx="29" cy="29" r="20"/><circle class="fg" cx="29" cy="29" r="20" style="stroke:'+color+';--p:'+pct+'"/><text class="ring-num" x="29" y="33" text-anchor="middle">'+pct+'%</text></svg>'+
    '<div><h3>'+esc(title)+' <span class="imp '+impCls(imp)+' goal-imp">'+esc(imp)+'</span></h3><p class="meta">'+done+'/'+total+' 子任务</p></div>'+
    '<button class="btn small" id="goalSubAdd">＋ 添加子任务</button>'+
    '</div>'+
    '<div class="detail-subs"><div class="detail-subs-head"><span></span><span>名字<span class="resize-handle" data-table="sub" data-col="2"></span></span><span>备注<span class="resize-handle" data-table="sub" data-col="3"></span></span><span>重要度<span class="resize-handle" data-table="sub" data-col="4"></span></span><span>状态</span><span></span></div>'+listHtml+'</div>';
  var subBtn=body.querySelector('#goalSubAdd');
  if(subBtn){subBtn.style.background=color;subBtn.style.border='0'}
}
function openReviewNoteModal(row){
  if(!row)return;
  currentReviewRow=row;
  $('#rnTask').textContent=row.dataset.title||'';
  $('#rnNote').value=row.dataset.reviewNote||'';
  openModal('reviewNote');
  var t=$('#rnNote');if(t)setTimeout(function(){t.focus()},60);
}
function confirmReviewNote(){
  if(!currentReviewRow)return;
  currentReviewRow.dataset.reviewNote=$('#rnNote').value.trim();
  closeModal('reviewNote');
  rolloverRow(currentReviewRow);
}
function openGoalDetail(card){
  if(!card)return;
  currentGoalCard=card;
  $$('.goal-card').forEach(function(g){g.classList.toggle('selected',g===card)});
  renderGoalDetail();
}
function toggleSubAt(card,sid){
  var s=card?card.querySelector('.sub-row[data-sid="'+sid+'"]'):null;if(!s)return;
  var c=s.querySelector('.check');
  c.classList.toggle('on');
  s.querySelector('.day').textContent=c.classList.contains('on')?('完成于 '+formatNow()):'待完成';
  updateGoal(card);renderGoalDetail();refreshAll();
}
function openSubModal(subRow){
  currentSubRow=subRow||null;
  $('#subModalTitle').textContent=subRow?'编辑子任务':'添加子任务';
  $('#sTitle').value=subRow?subRow.querySelector('.name').textContent:'';
  $('#sImp').value=subRow?(subRow.dataset.imp||'中'):'中';
  $('#sNote').value=subRow?(subRow.dataset.note||''):'';
  openModal('sub');
  var t=$('#sTitle');if(t)setTimeout(function(){t.focus()},60);
}
function saveSub(){
  var name=$('#sTitle').value.trim();if(!name){$('#sTitle').focus();return}
  var imp=$('#sImp').value;
  var note=$('#sNote').value.trim();
  if(currentSubRow){
    currentSubRow.querySelector('.name').textContent=name;
    currentSubRow.dataset.imp=imp;
    currentSubRow.dataset.note=note;
  }else if(currentGoalCard){
    createSubRow(currentGoalCard,name,note,imp);
  }
  $('#sTitle').value='';$('#sNote').value='';
  closeModal('sub');
  if(currentGoalCard){updateGoal(currentGoalCard);renderGoalDetail();}
  refreshAll();
}
function delSubAt(card,sid){
  var s=card?card.querySelector('.sub-row[data-sid="'+sid+'"]'):null;if(!s)return;
  if(!confirm('确定删除子任务「'+s.querySelector('.name').textContent+'」吗？'))return;
  s.remove();
  updateGoal(card);renderGoalDetail();refreshAll();
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
      b.querySelector('.s2').textContent=(x.t.goal||'无计划')+' · '+x.t.imp+' · '+x.t.doneAt;
      list.appendChild(b);
    });
  });
  if(detail)detail.innerHTML='<p class="placeholder">选中左侧任务查看详情</p>';
}
function selectDone(i,btn){
  $$('.done-item').forEach(function(b){b.classList.toggle('on',b===btn)});
  var t=doneTasks[i];if(!t)return;
  var body=btn.closest('.done-body');
  var detail=body?body.querySelector('.done-detail'):null;if(!detail)return;
  detail.innerHTML='<h4></h4>'+
    '<div class="detail-meta"><span class="imp '+impCls(t.imp)+'">'+esc(t.imp)+'</span>'+
    '<span class="goal-tag"><i style="background:'+esc(t.color)+'"></i>'+esc(t.goal||'无计划')+'</span></div>'+
    '<p class="detail-note"></p>'+
    '<p class="detail-when">完成于 '+esc(t.doneAt)+'</p>'+
    '<button class="btn ghost" style="margin-top:18px" data-reopen="'+i+'">重新打开</button>';
  detail.querySelector('h4').textContent=t.title;
  detail.querySelector('.detail-note').textContent=t.note||'没有备注';
}
function reopenDone(i){
  var t=doneTasks[i];if(!t)return;
  if(!confirm('确定把「'+t.title+'」重新打开，回到今日列表吗？'))return;
  doneTasks.splice(i,1);
  if(t.link){
    var card=$('#goalGrid .goal-card[data-gid="'+t.link.gid+'"]');
    if(card){
      var s=card.querySelector('.sub-row[data-sid="'+t.link.sid+'"]');
      if(s){
        s.querySelector('.check').classList.remove('on');
        s.querySelector('.day').textContent='待完成';
        updateGoal(card);renderGoalDetail();
      }
    }
  }
  addTaskRow(t.title,t.imp,t.goal,'2026-08-15',t.note,t.link?t.link.gid:null,t.link?t.link.sid:null);
  closeModal('done');
  refreshAll();
  if($('#panel-done')&&$('#panel-done').classList.contains('show'))renderDoneTab();
}
function renderDoneTab(){renderDoneInto($('#doneTabList'),$('#doneTabDetail'))}
function renderReviewInto(list){
  if(!list)return;
  var rows=$$('#todayList .task').filter(function(r){return !r.classList.contains('done')});
  list.innerHTML='';
  rows.forEach(function(r){
    var title=r.dataset.title||'';
    var goal=r.dataset.goal||'';
    var row=document.createElement('div');row.className='rev-row';
    row.innerHTML='<span class="check" aria-label="完成"></span><span class="title"></span>'+
      (goal?'<span class="goal-tag"><i style="background:'+goalColor(goal)+'"></i>'+esc(goal)+'</span>':'');
    row.querySelector('.title').textContent=title;
    list.appendChild(row);
  });
  var c=$('#revCount');if(c)c.textContent=rows.length;
}
function renderReviewTab(){
  var list=$('#revTabList');if(!list)return;
  var rows=$$('#todayList .task').filter(function(r){return !r.classList.contains('done')});
  list.innerHTML='';
  rows.forEach(function(r){
    var title=r.dataset.title||'';
    var goal=r.dataset.goal||'';
    var row=document.createElement('div');row.className='rev-row';
    row.innerHTML='<span class="check" aria-label="完成"></span><span class="title"></span>'+
      (goal?'<span class="goal-tag"><i style="background:'+goalColor(goal)+'"></i>'+esc(goal)+'</span>':'');
    row.querySelector('.title').textContent=title;
    list.appendChild(row);
  });
  var c=$('#revTabCount');if(c)c.textContent=rows.length;
}
function revComplete(title){
  var row=$$('#todayList .task').filter(function(r){return r.dataset.title===title})[0];
  if(row){var c=row.querySelector('.check');if(c)toggleTask(c)}
}
function revLaterOne(title){
  var row=$$('#todayList .task').filter(function(r){return r.dataset.title===title})[0];
  if(row)rolloverRow(row);
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
  set('#weekNum2',function(el){el.textContent=pct+'%'});
  set('#weekBar2',function(el){el.style.width=pct+'%'});
  var list=$('#todayList');
  if(list){
    var emp=list.querySelector('.empty');
    if(undone===0&&!emp){
      var e=document.createElement('p');e.className='empty';e.textContent='今天没有待办，点「添加任务」安排一件吧。';
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
    if(check.closest('.rev-row')){
      var rw=check.closest('.rev-row');
      revComplete(rw.querySelector('.title').textContent);return;
    }
    if(check.closest('.goal-detail-sub')){toggleSubAt(currentGoalCard,check.dataset.sid);return}
    if(check.closest('.task')){toggleTask(check);return}
    return;
  }
  var del=e.target.closest('.detail-del');
  if(del){delSubAt(currentGoalCard,del.dataset.del);return}
  var revRowEl=e.target.closest('.rev-row');
  if(revRowEl&&!e.target.closest('.check')){
    var rtitle=revRowEl.querySelector('.title').textContent;
    var trow=$$('#todayList .task').filter(function(r){return r.dataset.title===rtitle})[0];
    if(trow)openReviewNoteModal(trow);
    return;
  }
  var subRow=e.target.closest('.goal-detail-sub');
  if(subRow){openSubModal(currentGoalCard.querySelector('.sub-row[data-sid="'+subRow.querySelector('.check').dataset.sid+'"]'));return}
  var card=e.target.closest('.goal-card');
  if(card){openGoalDetail(card);return}
  var taskRow=e.target.closest('.task');
  if(taskRow){openTaskDetail(taskRow);return}
  var open=e.target.closest('[data-open]');
  if(open){
    var name=open.dataset.open;
    if(name==='task')openTaskModal();
    else if(name==='goal')openGoalModal();
    else if(name==='done'){renderDoneInto($('#doneList'),$('#doneDetail'));openModal('done')}
    else if(name==='review'){renderReviewInto($('#revList'));openModal('review')}
    return;
  }
  var close=e.target.closest('[data-close]');
  if(close){closeModal(close.dataset.close);return}
  var taskConfirm=e.target.closest('#taskConfirm');
  if(taskConfirm){confirmTaskAdd();return}
  var goalConfirm=e.target.closest('#goalConfirm');
  if(goalConfirm){confirmGoalAdd();return}
  var taskDetailSave=e.target.closest('#taskDetailSave');
  if(taskDetailSave){saveTaskDetail();return}
  var subSave=e.target.closest('#subSave');
  if(subSave){saveSub();return}
  var subAdd=e.target.closest('#goalSubAdd');
  if(subAdd){openSubModal(null);return}
  var revAll=e.target.closest('#revAll,#revAll2');
  if(revAll){rolloverAll();return}
  var rnConfirm=e.target.closest('#rnConfirm');
  if(rnConfirm){confirmReviewNote();return}
  var pick=e.target.closest('.pick-item');
  if(pick){togglePick(pick);return}
  var ov=e.target.closest('.modal-overlay');
  if(ov&&e.target===ov){closeModal(ov.id.slice(0,-5));return}
  var tab=e.target.closest('[data-tab]');
  if(tab){switchTab(tab.dataset.tab);return}
  var item=e.target.closest('.done-item');
  if(item){selectDone(parseInt(item.dataset.i,10),item);return}
  var reopen=e.target.closest('[data-reopen]');
  if(reopen){reopenDone(parseInt(reopen.dataset.reopen,10));return}
});
document.addEventListener('keydown',function(e){
  if(e.key!=='Enter')return;
  if(e.target.id==='tTitle')confirmTaskAdd();
  else if(e.target.id==='gTitle')confirmGoalAdd();
  else if(e.target.id==='dtTitle')saveTaskDetail();
  else if(e.target.id==='sTitle')saveSub();
});

buildModals();refreshAll();
var savedCols=localStorage.getItem('plan-cols');
if(savedCols){var cardEl=$('.card');if(cardEl)cardEl.style.setProperty('--cols',savedCols);}
var savedSubs=localStorage.getItem('plan-subcols');
if(savedSubs){var paneEl=$('#goalDetailBody');if(paneEl)paneEl.style.setProperty('--subcols',savedSubs);}
var first=$('#goalGrid .goal-card');
if(first)openGoalDetail(first);
document.addEventListener('mousedown',function(e){
  var h=e.target.closest('.resize-handle');if(!h)return;
  e.preventDefault();
  var table=h.dataset.table;
  var header=table==='task'?h.closest('.task-head'):h.closest('.detail-subs-head');
  var root=table==='task'?h.closest('.card'):$('#goalDetailBody');
  if(!header||!root)return;
  var col=parseInt(h.dataset.col,10);
  var prop=table==='task'?'--cols':'--subcols';
  var cs=getComputedStyle(header);
  var widths=cs.gridTemplateColumns.split(' ').map(function(x){return parseFloat(x)});
  var gap=parseFloat(cs.columnGap||cs.gap)||0;
  var left=header.getBoundingClientRect().left+parseFloat(cs.paddingLeft||'0');
  var boundary=gap*(col-1);
  for(var i=1;i<=col;i++)boundary+=widths[i-1];
  var bPrev=boundary-gap-widths[col-1];
  var bNext=boundary+gap+widths[col];
  var offset=boundary-(e.clientX-left);
  var flex=5;
  var moving=function(ev){
    var b=ev.clientX+offset-left;
    var minB=bPrev+gap+50;
    var maxB=bNext-gap-50;
    if(b<minB)b=minB;
    if(b>maxB)b=maxB;
    var arr=widths.slice();
    arr[col-1]=b-bPrev-gap;
    arr[col]=bNext-b-gap;
    var parts=arr.map(function(v,i){return (i+1)===flex?'minmax(0,1fr)':v+'px'});
    root.style.setProperty(prop,parts.join(' '));
  };
  var up=function(){
    document.removeEventListener('mousemove',moving);
    document.removeEventListener('mouseup',up);
    document.body.classList.remove('resizing');
    var parts=getComputedStyle(header).gridTemplateColumns.split(' ');
    if(parts.length>4)parts[4]='minmax(0,1fr)';
    localStorage.setItem(table==='task'?'plan-cols':'plan-subcols',parts.join(' '));
  };
  document.body.classList.add('resizing');
  document.addEventListener('mousemove',moving);
  document.addEventListener('mouseup',up);
});
})();
