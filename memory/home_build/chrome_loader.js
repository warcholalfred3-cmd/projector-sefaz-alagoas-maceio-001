(function(){
var V='16';
var P=location.pathname;
var MINHAS=/\/(inscricao-realizada|pagamento-pix|minhas-inscricoes)(\.html)?\/?$/.test(P);
var BASE=':host{all:initial;display:block;font-family:"Open Sans",Helvetica,Arial,sans-serif;font-size:14px;line-height:1.42857;color:#333;text-align:left}'+
'.vn-wrap{font-size:14px}'+
'.vn-minhas{display:inline-flex;align-items:center;gap:7px;background:#d9534f;color:#fff!important;text-decoration:none!important;font:700 12px "Open Sans",Arial,sans-serif;text-transform:uppercase;padding:10px 14px;border-radius:2px;white-space:nowrap}'+
'.vn-minhas:hover{background:#c9302c}'+
'.vn-minhas-box{position:absolute;right:15px;top:50%;transform:translateY(-50%);z-index:5}'+
'.vn-burger{width:40px;height:36px;border:1px solid #ddd;border-radius:4px;background:#fff;display:flex;flex-direction:column;justify-content:center;align-items:center;gap:4px;cursor:pointer;padding:0}.vn-burger span{display:block;width:20px;height:2px;background:#333;border-radius:1px}.vn-drop{display:none;position:fixed;right:12px;top:66px;background:#fff;box-shadow:0 4px 14px rgba(0,0,0,.18);border-radius:4px;padding:8px;z-index:20}.vn-drop.open{display:block}'+
'.vn-minhas-desk{padding:8px 12px!important;letter-spacing:0!important}@media(min-width:992px){.vn-minhas-box{display:none}}@media(max-width:991px){.vn-minhas-desk{display:none!important}}';
function fontsLink(){
 if(document.getElementById('vn-fonts'))return;
 var l=document.createElement('link');l.id='vn-fonts';l.rel='stylesheet';l.href='/vunesp/fonts.css?v='+V;document.head.appendChild(l);
}
function host(id,html,atTop,extra){
 var h=document.createElement('div');h.id=id;
 h.style.cssText='display:block;width:100%;position:relative;z-index:'+(atTop?'9999':'100')+';visibility:hidden;';
 if(atTop)document.body.insertBefore(h,document.body.firstChild);else document.body.appendChild(h);
 var r=h.attachShadow({mode:'open'});
 r.innerHTML='<link rel="stylesheet" href="/vunesp/chrome.css?v='+V+'"><style>'+BASE+(extra||'')+'</style><div class="vn-wrap">'+html+'</div>';
 var ln=r.querySelector('link');ln.addEventListener('load',function(){h.style.visibility='visible';if(atTop)document.documentElement.classList.remove('vn-wait');});
 ln.addEventListener('error',function(){h.remove();document.documentElement.classList.remove('vn-wait');});
 setTimeout(function(){if(ln.sheet)h.style.visibility='visible';},2500);
 r.addEventListener('click',function(e){var a=e.target.closest&&e.target.closest('a');if(!a)return;var hr=a.getAttribute('href');if(!hr||hr==='#'){e.preventDefault();}});
 return r;
}
function build(parts){
 if(document.getElementById('seduc-header-host'))return;
 fontsLink();
 var hh=parts.h;
 if(MINHAS){hh=hh.replace('<a href=# title="Área do Candidato">Área do Candidato</a>','<a class="vn-minhas vn-minhas-desk" href="/minhas-inscricoes.html" data-testid="header-minhas-inscricoes-desktop-btn">Minhas inscrições</a>').replace('</header>','<div class="vn-minhas-box"><button type="button" class="vn-burger" aria-label="Menu" aria-expanded="false" data-testid="header-hamburger-btn"><span></span><span></span><span></span></button><div class="vn-drop" data-testid="header-hamburger-menu"><a class="vn-minhas" href="/minhas-inscricoes.html" data-testid="header-minhas-inscricoes-btn">Minhas inscrições</a></div></div></header>');}
 var r=host('seduc-header-host',hh,true,'header{position:relative}'+(MINHAS?'.social,.socialmedia-item{display:none!important}':''));
 if(MINHAS){var bg=r.querySelector('.vn-burger'),dr=r.querySelector('.vn-drop');if(bg&&dr){r.appendChild(dr);bg.addEventListener('click',function(e){e.stopPropagation();var o=dr.classList.toggle('open');bg.setAttribute('aria-expanded',o?'true':'false');});document.addEventListener('click',function(){dr.classList.remove('open');bg.setAttribute('aria-expanded','false');});}}
 document.querySelectorAll('#aocp-footer,.seduc-footer').forEach(function(el){el.remove();});
 host('vunesp-footer-host',parts.f,false,'#rodape{margin-top:40px}');
}
function go(){
 fetch('/vunesp/parts.json?v='+V).then(function(r){return r.json();}).then(build).catch(function(){document.documentElement.classList.remove('vn-wait');});
}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',go);else go();
})();
