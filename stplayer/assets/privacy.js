(function(){
  "use strict";
  var SUPPORTED = ["en","de","es","fi","fr","ja","nl","pt","ru","sv","tr","zh"];
  var TITLES = {
    en:"STPlayer Privacy Policy",
    de:"STPlayer Datenschutzerklärung",
    es:"Política de privacidad de STPlayer",
    fi:"STPlayerin tietosuojakäytäntö",
    fr:"Politique de confidentialité de STPlayer",
    ja:"STPlayer プライバシーポリシー",
    nl:"STPlayer-privacybeleid",
    pt:"Política de Privacidade do STPlayer",
    ru:"Политика конфиденциальности STPlayer",
    sv:"STPlayer integritetspolicy",
    tr:"STPlayer Gizlilik Politikası",
    zh:"STPlayer 隐私政策"
  };
  var HEADINGS = {
    en:"Privacy Policy", de:"Datenschutzerklärung", es:"Política de privacidad",
    fi:"Tietosuojakäytäntö", fr:"Politique de confidentialité", ja:"プライバシーポリシー",
    nl:"Privacybeleid", pt:"Política de Privacidade", ru:"Политика конфиденциальности",
    sv:"Integritetspolicy", tr:"Gizlilik Politikası", zh:"隐私政策"
  };
  var LABELS = {
    en:"Language", de:"Sprache", es:"Idioma", fi:"Kieli", fr:"Langue", ja:"言語",
    nl:"Taal", pt:"Idioma", ru:"Язык", sv:"Språk", tr:"Dil", zh:"语言"
  };
  var KEY = "stp-privacy-lang";

  // "ru-RU", "RU", " ru " -> "ru"; null when unsupported or empty.
  function normalize(raw){
    if(!raw) return null;
    var base = String(raw).trim().toLowerCase().replace(/_/g,"-").split("-")[0];
    return SUPPORTED.indexOf(base) !== -1 ? base : null;
  }

  function fromQuery(){
    var m = /[?&]lang=([^&#]*)/.exec(location.search);
    if(!m) return null;
    var raw;
    try { raw = decodeURIComponent(m[1]); } catch(e){ raw = m[1]; }
    return normalize(raw);
  }

  function stored(){
    try { return normalize(localStorage.getItem(KEY)); } catch(e){ return null; }
  }

  function store(lang){
    try { localStorage.setItem(KEY, lang); } catch(e){ /* private mode: ignore */ }
  }

  function fromBrowser(){
    var list = (navigator.languages && navigator.languages.length)
      ? navigator.languages : [navigator.language];
    for(var i=0;i<list.length;i++){
      var n = normalize(list[i]);
      if(n) return n;
    }
    return null;
  }

  var sections = document.querySelectorAll("[data-lang]");
  var selector = document.getElementById("lang");
  var heading = document.querySelector("h1");
  var label = document.querySelector(".langbar label");

  function apply(lang, updateUrl){
    for(var i=0;i<sections.length;i++){
      var s = sections[i];
      if(s.getAttribute("data-lang") === lang) s.className = "on";
      else s.className = "";
    }
    document.documentElement.lang = lang;
    document.title = TITLES[lang];
    heading.textContent = HEADINGS[lang];
    label.textContent = LABELS[lang];
    selector.value = lang;
    if(updateUrl && window.history && history.replaceState){
      history.replaceState(null, "", "?lang=" + lang);
    }
  }

  apply(fromQuery() || stored() || fromBrowser() || "en", false);

  selector.addEventListener("change", function(){
    var lang = normalize(selector.value) || "en";
    apply(lang, true);
    store(lang);
  });
})();
