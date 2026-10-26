/* Study guide engine: quizzes, saved progress, sidebar scores, final exam review,
   math typesetting, active section highlight, print formula sheet.
   Reads window.GUIDE = {title, quizzes:{id:{title, questions:[{q, options[4], answer, explain, mistakes[4], review}]}}}
   Tested once; guides should not modify this file. */
(function(){
  "use strict";
  var G = window.GUIDE || {quizzes:{}};
  var KEY = "guide:" + String(G.title||document.title).toLowerCase().replace(/[^a-z0-9]+/g,"-");
  var L = ["A","B","C","D","E"];
  var state = load();

  function load(){ try{ return JSON.parse(localStorage.getItem(KEY)) || {}; }catch(e){ return {}; } }
  function save(){ try{ localStorage.setItem(KEY, JSON.stringify(state)); }catch(e){} }

  function typeset(root){
    if (window.renderMathInElement){
      try{ renderMathInElement(root||document.body,{
        delimiters:[{left:"\\[",right:"\\]",display:true},{left:"\\(",right:"\\)",display:false}],
        throwOnError:false }); }catch(e){}
    }
  }
  window.typeset = typeset;

  function el(tag, cls, html){ var e=document.createElement(tag); if(cls) e.className=cls; if(html!=null) e.innerHTML=html; return e; }

  function score(id){
    var qs=G.quizzes[id].questions, a=state[id]||[], n=0, right=0;
    qs.forEach(function(q,i){ if(a[i]!=null){ n++; if(a[i]===q.answer) right++; } });
    return {n:n, right:right, total:qs.length};
  }

  function updateChip(id){
    var s=score(id);
    document.querySelectorAll('[data-chip="'+id+'"]').forEach(function(c){
      c.textContent = s.n ? (s.right+"/"+s.total) : "";
      c.classList.toggle("done", s.n===s.total);
    });
    var box=document.querySelector('.quiz[data-quiz="'+id+'"] .score');
    if (box) box.textContent = "Score: "+s.right+"/"+s.total + (s.n<s.total ? "  ("+s.n+" answered)" : "");
  }

  function explanation(id, q, chosen){
    var html = chosen===q.answer
      ? '<b class="ok">Correct.</b> '
      : '<b class="no">Not quite.</b> You chose '+L[chosen]+((q.mistakes&&q.mistakes[chosen])?', which comes from '+q.mistakes[chosen]+'.':'.')+' The answer is '+L[q.answer]+'. ';
    html += q.explain || "";
    if (q.review){ var t=document.getElementById(q.review); var name=t?(t.querySelector("h3 .num")||{}).textContent||q.review:q.review;
      html += ' <a href="#'+q.review+'">Review: '+name+'</a>'; }
    return html;
  }

  function renderQuestion(id, i, item){
    var q=G.quizzes[id].questions[i], chosen=(state[id]||[])[i];
    item.innerHTML="";
    item.appendChild(el("div","qq",'<span class="qn">'+(i+1)+'.</span>'+q.q));
    var opts=el("div","opts");
    q.options.forEach(function(o,k){
      var b=el("button","opt",'<span class="L">'+L[k]+'</span><span>'+o+'</span>');
      b.type="button";
      if (chosen!=null){ b.disabled=true; if(k===q.answer) b.classList.add("right"); else if(k===chosen) b.classList.add("wrong"); }
      else b.addEventListener("click",function(){ (state[id]=state[id]||[])[i]=k; save(); renderQuestion(id,i,item); updateChip(id); if(id==="final") renderReview(); });
      opts.appendChild(b);
    });
    item.appendChild(opts);
    if (chosen!=null) item.appendChild(el("div","expl",explanation(id,q,chosen)));
    typeset(item);
  }

  function renderReview(){
    var box=document.getElementById("finalReview"); if(!box||!G.quizzes.final) return;
    var s=score("final"); box.innerHTML="";
    if (s.n<s.total) return;
    var qs=G.quizzes.final.questions, a=state.final, wrong=[];
    qs.forEach(function(q,i){ if(a[i]!==q.answer) wrong.push(i); });
    var h='<h4>Review my wrong answers</h4>';
    if(!wrong.length) h+='<p>All '+s.total+' correct. Nothing to review.</p>';
    else { h+='<ol class="plain review">'; wrong.forEach(function(i){ var q=qs[i];
      h+='<li><b>Q'+(i+1)+'.</b> '+q.q+'<br>You chose '+L[a[i]]+': '+q.options[a[i]]+'<br>Correct: '+L[q.answer]+': '+q.options[q.answer]+(q.review?'<br><a href="#'+q.review+'">Review this section</a>':'')+'</li>'; });
      h+='</ol>'; }
    box.innerHTML=h; typeset(box);
  }

  function renderQuiz(box){
    var id=box.getAttribute("data-quiz"), Q=G.quizzes[id];
    if(!Q){ box.innerHTML='<div class="quiz-head"><span class="qt">Missing quiz data: '+id+'</span></div>'; return; }
    box.innerHTML="";
    var head=el("div","quiz-head",'<span class="qt">'+(Q.title||"Quiz")+'</span><span class="score"></span>');
    var list=el("div","qlist");
    Q.questions.forEach(function(_,i){ var it=el("div","qitem"); list.appendChild(it); renderQuestion(id,i,it); });
    var foot=el("div","quiz-foot",'<span>'+Q.questions.length+' questions</span>');
    var reset=el("button","btn","Reset"); reset.type="button";
    reset.addEventListener("click",function(){ delete state[id]; save(); renderQuiz(box); if(id==="final") renderReview(); });
    foot.appendChild(reset);
    box.appendChild(head); box.appendChild(list); box.appendChild(foot);
    if(id==="final"){ var r=el("div",""); r.id="finalReview"; r.style.padding="0 16px 8px"; box.appendChild(r); renderReview(); }
    updateChip(id);
  }

  function init(){
    document.querySelectorAll(".quiz[data-quiz]").forEach(renderQuiz);
    Object.keys(G.quizzes).forEach(updateChip);
    var ra=document.getElementById("resetAll");
    if(ra) ra.addEventListener("click",function(){ if(confirm("Clear all quiz answers and scores for this guide?")){ state={}; save(); document.querySelectorAll(".quiz[data-quiz]").forEach(renderQuiz); } });
    var pb=document.getElementById("printSheet");
    if(pb) pb.addEventListener("click",function(){ document.body.classList.add("print-sheet"); window.print(); });
    window.addEventListener("afterprint",function(){ document.body.classList.remove("print-sheet"); });
    if("IntersectionObserver" in window){
      var links={}; document.querySelectorAll('nav.toc a[href^="#"]').forEach(function(a){ links[a.getAttribute("href").slice(1)]=a; });
      var io=new IntersectionObserver(function(es){ es.forEach(function(e){ if(e.isIntersecting&&links[e.target.id]){
        Object.keys(links).forEach(function(k){ links[k].classList.remove("active"); }); links[e.target.id].classList.add("active"); } }); },{rootMargin:"-20% 0px -70% 0px"});
      document.querySelectorAll("section.sec[id]").forEach(function(s){ io.observe(s); });
    }
    typeset();
    if (typeof window.initDemos==="function"){ try{ window.initDemos(); }catch(e){ console.error(e); } }
  }
  if(document.readyState==="loading") document.addEventListener("DOMContentLoaded",function(){ waitKatex(init); }); else waitKatex(init);
  function waitKatex(fn){ var t=0; (function w(){ if(window.renderMathInElement||t++>40) fn(); else setTimeout(w,50); })(); }
})();
