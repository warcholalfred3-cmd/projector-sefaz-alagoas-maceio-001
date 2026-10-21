(function(){
var CSS=':host{all:initial;display:block}*{box-sizing:border-box;margin:0;padding:0}'+
'.top{background:linear-gradient(to right,#204D37,#00853B 40%)}'+
'.top-in{max-width:1140px;margin:0 auto;padding:0 15px;height:28px;display:flex;align-items:center;justify-content:space-between;background:rgba(0,0,0,.15);font:11px "OpenSans-Regular",Helvetica,Arial,sans-serif;color:#fff;text-transform:uppercase}'+
'.top-in span+span{border-left:1px solid #fff;padding-left:6px;margin-left:6px}'+
'.bar{position:relative;background:url(/seduc/onda.svg) no-repeat -50px bottom #fff;background-size:700px;border-bottom:5px solid #00bd19;box-shadow:0 5px 25px rgba(0,0,0,.35)}'+
'.bar-in{max-width:1140px;margin:0 auto;padding:18px 15px 30px;display:flex;align-items:center;justify-content:space-between;gap:16px}'+
'.logo img{height:64px;width:auto;display:block}'+
'nav{display:flex;align-items:center}'+
'nav a{color:#00a84a;font:bold 12px "Geomanist Regular","OpenSans-Bold",Helvetica,Arial,sans-serif;text-transform:uppercase;text-decoration:none;padding:3px 14px;transition:color .2s}'+
'nav a:not(:last-child){border-right:3px solid #00a84a}nav a:last-child{padding-right:0}'+
'nav a:hover{color:#ffbd00}'+
'nav a.minhas{display:inline-flex;align-items:center;gap:7px;background:#008d3c;color:#fff;border:0!important;border-radius:5px;padding:9px 16px!important;font-size:12px;box-shadow:0 4px 10px rgba(0,141,60,.25);transition:background-color .2s}'+
'nav a.minhas:hover{background:#006b2d;color:#fff}'+
'@media(max-width:768px){.top-in .r{display:none}.bar{background-size:420px}.bar-in{padding:12px 12px 22px}.logo img{height:44px}nav a{padding:3px 9px;font-size:11px}nav a.sair{display:none}nav a:nth-child(2){border-right:0;padding-right:0}nav a.minhas{padding:8px 12px!important;font-size:11px}}';
var HTML='<div class="top"><div class="top-in"><div><span>Portal da UECE</span><span>CEV</span></div><div class="r">Concurso Professor Seduc 2026</div></div></div>'+
'<div class="bar"><div class="bar-in"><a class="logo" href="/inicio.html"><img src="/seduc/cev-logo.png" alt="CEV - Comissão Executiva do Vestibular da UECE"></a>'+
'<nav><a href="/inicio.html" data-testid="header-inicio-link">Início</a><a href="/inicio.html" data-testid="header-concursos-link">Concursos</a><a class="sair" href="/inicio.html" data-testid="header-sair-link">Sair</a></nav></div></div>';
var MINHAS=/\/(inscricao-realizada|pagamento-pix)(\.html)?\/?$/.test(location.pathname);
if(MINHAS)HTML=HTML.replace(/<nav>.*<\/nav>/,'<nav><a class="minhas" href="/minhas-inscricoes.html" data-testid="header-minhas-inscricoes-btn"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><path d="M14 2v6h6"/><path d="M8 13h8M8 17h6"/></svg>Minhas inscrições</a></nav>');
if(/\/minhas-inscricoes(\.html)?\/?$/.test(location.pathname))HTML=HTML.replace(/<nav>.*<\/nav>/,'');
function inject(){
 if(document.getElementById('seduc-header-host'))return;
 var host=document.createElement('div');
 host.id='seduc-header-host';
 host.style.cssText='display:block;width:100%;position:relative;z-index:9999;';
 document.body.insertBefore(host,document.body.firstChild);
 var r=host.attachShadow({mode:'open'});
 r.innerHTML='<style>'+CSS+'</style>'+HTML;
}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',inject);else inject();
})();
