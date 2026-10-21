(function(){
var V='18';
function fontsLink(){
 if(document.getElementById('ceb-fonts'))return;
 var l=document.createElement('link');l.id='ceb-fonts';l.rel='stylesheet';l.href='/cebraspe/fonts.css?v='+V;document.head.appendChild(l);
}
function host(id,html,cls,atTop){
 var h=document.createElement('div');h.id=id;
 h.style.cssText='display:block;width:100%;position:relative;z-index:'+(atTop?'9999':'100')+';visibility:hidden;';
 if(atTop)document.body.insertBefore(h,document.body.firstChild);else document.body.appendChild(h);
 var r=h.attachShadow({mode:'open'});
 r.innerHTML='<link rel="stylesheet" href="/cebraspe/chrome.css?v='+V+'"><div class="sfbody '+cls+'">'+html+'</div>';
 var ln=r.querySelector('link');
 function show(){h.style.visibility='visible';if(atTop)document.documentElement.classList.remove('vn-wait');}
 ln.addEventListener('load',show);
 ln.addEventListener('error',function(){h.remove();document.documentElement.classList.remove('vn-wait');});
 setTimeout(show,2500);
 r.addEventListener('click',function(e){
  var a=e.target.closest&&e.target.closest('a');if(!a)return;
  var hr=a.getAttribute('href');
  if(!hr||hr==='#'){e.preventDefault();return;}
  var pl=document.getElementById('__page_loader');if(pl)pl.classList.remove('__hidden');
 });
 return r;
}
function menu(r){
 var wrap=r.querySelector('.sfbody'),dr=r.getElementById('mnav'),op=r.getElementById('mnav-open');
 if(!wrap||!dr||!op)return;
 function set(on){wrap.classList.toggle('mnav-on',on);dr.setAttribute('aria-hidden',on?'false':'true');document.documentElement.style.overflow=on?'hidden':'';}
 op.addEventListener('click',function(){set(true);});
 r.querySelector('#mnav .mnav-close').addEventListener('click',function(){set(false);});
 r.getElementById('mnav-backdrop').addEventListener('click',function(){set(false);});
 document.addEventListener('keydown',function(e){if(e.key==='Escape')set(false);});
}
function build(p){
 if(document.getElementById('seduc-header-host'))return;
 fontsLink();
 var hr=host('seduc-header-host',p.h,p.cls,true);
 if(/minhas-inscricoes/.test(location.pathname)){hr.querySelectorAll('.header__action-follow-button,[data-testid=header-minhas-inscricoes-btn]').forEach(function(el){el.remove();});}
 menu(hr);
 document.querySelectorAll('#aocp-footer,.seduc-footer').forEach(function(el){el.remove();});
 host('vunesp-footer-host',p.f,p.cls,false);
}
function go(){
 fetch('/cebraspe/parts.json?v='+V).then(function(r){return r.json();}).then(build).catch(function(){document.documentElement.classList.remove('vn-wait');});
}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',go);else go();
})();
