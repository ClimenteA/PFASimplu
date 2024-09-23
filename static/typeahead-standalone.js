/**
 * Skipped minification because the original files appears to be already minified.
 * Original file: /npm/typeahead-standalone@5.3.0/dist/typeahead-standalone.umd.js
 *
 * Do NOT use SRI with dynamically generated files! More information: https://www.jsdelivr.com/using-sri-with-dynamic-files
 */
(function(H,F){typeof exports=="object"&&typeof module<"u"?module.exports=F():typeof define=="function"&&define.amd?define(F):(H=typeof globalThis<"u"?globalThis:H||self,H.typeahead=F())})(this,function(){"use strict";const H=(...n)=>{},F=n=>n.replace(/[-[\]{}()*+?.,\\^$|#\s]/g,"\\$&"),U=n=>n!==null&&n?.constructor.name==="Object",se=n=>typeof n=="string",S=(n,l)=>{let m=n;const D=l.split(".");for(const L of D){if(!U(m)||!(L in m))return"";m=m[L]}return`${m}`},I=(n="")=>n.normalize("NFD").replace(/\p{Diacritic}/gu,""),z=(n,l)=>{if(!n.length)return[];if(U(n[0])){for(const m of n)if(!S(m,l))throw new Error("e03");return n}return n.map(m=>({[l]:se(m)?m:JSON.stringify(m)}))},ie=n=>n.split(/\s+/),ge=async function(n,l){const m=await fetch(n,l||{method:"GET"});return ve(m)},ve=async function(n){const l=await n.text(),m=l&&JSON.parse(l);return n.ok?m:Promise.reject(m&&m.message||n.statusText)},le={get:ge},be=(n={})=>{const{hasDiacritics:l,tokenizer:m}=n;let D={};const L="\0";function P(c=""){return c=`${c}`.trim(),l&&(c=I(c)),(m||ie)(c.toLowerCase())}function W(c,w="",x){if(!c)return;let y;c=Array.isArray(c)?c:[c];const h=se(c[0]);for(const T of c){const v=P(h?T:S(T,w));for(const g of v){if(!g)continue;y=D;for(const O of g)y=y[O]||(y[O]={});const d=h?T:x&&x(T)||JSON.stringify(T),X=y[L]??(y[L]={});X[d]=T}}}function i(c){let w=D;const x={};for(const h of c)if(w=w?.[h],typeof w>"u")return{};const y=[{node:w,prefix:c}];for(;y.length;){const{node:h,prefix:T}=y.pop();for(const v in h)if(v===L){const g=h[L];for(const d in g)x[d]=g[d]}else y.push({node:h[v],prefix:T+v})}return x}const k=(c,w)=>{const x={};for(const y in c)y in w&&(x[y]=c[y]);return x};function $(c,w){const x=P(c),y=x.length<=20?x.length:20;let h=i(x[0]);for(let v=1;v<y&&(h=k(h,i(x[v])),!!Object.keys(h).length);v++);h=Object.values(h);const T=h.length;return w&&T>w&&(h.length=w),{suggestions:h,count:T}}function B(){D={}}return{add:W,clear:B,search:$}};return n=>{if(!n.input)throw new Error("e01");if(!U(n.source))throw new Error("e02");const l=document.createElement("div"),m=n.preventSubmit||!1,D=n.minLength||1,L=n.hint!==!1,P=n.autoSelect||!1,W=n.tokenizer||ie,i=n.templates,k=Array.isArray(n.source.keys)?n.source.keys:["label"],$=n.source.groupKey||"",B=e=>S(e,k[0]),c=n.display||B,w=n.source.identity||B,x=n.onSubmit||H,y=n.source.transform||(e=>e),h=n.source.local||null,T=typeof n.source.remote?.url,v=T==="function"||T==="string"&&n.source.remote.wildcard?n.source.remote:null,g=n.source.prefetch?.url?{when:"onInit",done:!1,...n.source.prefetch}:null,d={wrapper:"typeahead-standalone",input:"tt-input",hint:"tt-hint",highlight:"tt-highlight",hide:"tt-hide",show:"tt-show",list:"tt-list",selected:"tt-selected",header:"tt-header",footer:"tt-footer",loader:"tt-loader",suggestion:"tt-suggestion",group:"tt-group",empty:"tt-empty",notFound:"tt-notFound",...n.classNames||{}},X={block:"nearest",...n.listScrollOptions||{}};if(!h&&!g&&!v)throw new Error("e02");const O=be({hasDiacritics:n.diacritics,tokenizer:W}),R=document.createElement("div");R.className=d.wrapper;const r={query:"",hits:[],count:0,limit:n.limit||5,wrapper:R};let J={},V={},f,Y,j=!1,G="";i&&(i.header=typeof i.header=="function"?i.header:void 0,i.footer=typeof i.footer=="function"?i.footer:void 0,i.notFound=typeof i.notFound=="function"?i.notFound:void 0,i.group=typeof i.group=="function"?i.group:void 0,i.suggestion=typeof i.suggestion=="function"?i.suggestion:void 0,i.loader=typeof i.loader=="function"?i.loader:void 0,i.empty=typeof i.empty=="function"?i.empty:void 0);const Z=(e=[])=>{oe(z(e,k[0]))};h&&Z(h);const a=n.input;a.classList.add(d.input);const ce=window.getComputedStyle(a),_=a.parentNode,Ee=[..._.children].indexOf(a);_.removeChild(a),R.appendChild(a),_.insertBefore(R,_.children[Ee]);const K=a.cloneNode();L&&Oe(K),l.classList.add(d.list,d.hide),l.setAttribute("aria-label","menu-options"),l.setAttribute("role","listbox"),l.style.position="absolute",l.style.width=`${a.offsetWidth}px`,l.style.marginTop=`${a.offsetHeight+parseInt(ce.marginTop)}px`,R.appendChild(l),g&&g.when==="onInit"&&ae();function ae(){if(!g||g.done)return;let e=[];le.get(typeof g.url=="function"?g.url():g.url,g?.requestOptions).then(t=>{e=y(t),e=z(e,k[0]),oe(e)},t=>{console.error("e04",t)}).finally(()=>{typeof g.process=="function"&&g.process(e)}),g.done=!0}const ee=()=>{l.classList.remove(d.hide)},we=()=>{l.classList.add(d.hide)},xe=()=>!l.classList.contains(d.hide)&&!!Array.from(l.children).find(e=>e.classList.contains(d.suggestion)),ue=()=>Y&&clearTimeout(Y),A=()=>{r.hits=[],K.value="",G="",we()},de=()=>{a.dispatchEvent(new InputEvent("input",{bubbles:!0,inputType:"insertCompositionText",data:a.value}))},te=(e=!1)=>{if(!r.hits.length&&r.query){A(),ne();const t=i?.notFound?.(r);if(!t)return!0;const o=p=>{const s=document.createElement("div");s.classList.add(d.notFound),N(s,p),l.appendChild(s)};return v?(J[JSON.stringify(r.query)]||e&&!j)&&o(t):o(t),ee(),!0}},ne=()=>{for(;l.firstChild;)l.firstChild.remove()},fe=()=>{if(!i?.loader)return;if(!j){const t=l.querySelector(`.${d.loader}`);t&&l.removeChild(t);return}const e=document.createElement("div");e.classList.add(d.loader),N(e,i.loader()),i?.footer?l.insertBefore(e,l.querySelector(`.${d.footer}`)):l.appendChild(e)},Q=()=>{if(te())return;ne();const e=s=>{const u=document.createElement("div");return u.classList.add(d.suggestion),u.setAttribute("role","option"),u.setAttribute("aria-selected","false"),u.setAttribute("aria-label",c(s)),i?.suggestion?N(u,i.suggestion(s,r)):u.textContent=S(s,k[0]),u},t=s=>{const u=document.createElement("div");return u.classList.add(d.group),u.setAttribute("role","group"),u.setAttribute("aria-label",s),i?.group?N(u,i.group(s,r)):u.textContent=s||"",u},o=document.createDocumentFragment(),p=[];if(i?.header){const s=document.createElement("div");s.classList.add(d.header),s.setAttribute("role","presentation"),N(s,i.header(r))&&o.appendChild(s)}for(const[s,u]of r.hits.entries()){if(s===r.limit)break;const E=S(u,$);if(E&&!p.includes(E)){p.push(E);const C=t(E);o.appendChild(C)}const b=e(u);b.addEventListener("click",C=>{A(),f=u,a.value=c(u,C),de()}),u===f&&(b.classList.add(d.selected),b.setAttribute("aria-selected","true")),o.appendChild(b),n.highlight!==!1&&De(b,r.query)}if(i?.footer){const s=document.createElement("div");s.classList.add(d.footer),s.setAttribute("role","presentation"),N(s,i.footer(r))&&o.appendChild(s)}l.appendChild(o),L&&Ne(f||r.hits[0]),l.querySelector(`.${d.selected}`)?.scrollIntoView(X),ee()},Te=e=>{typeof e.inputType>"u"||e.inputType==="insertCompositionText"&&!e.isComposing||(G=a.value,pe())},Ce=e=>{const t=r.hits.length>=r.limit?r.limit:r.hits.length;if(f===r.hits[0]){f=void 0,a.value=G;return}if(!f)f=r.hits[t-1];else for(let o=t-1;o>0;o--)if(f===r.hits[o]||o===1){f=r.hits[o-1];break}a.value=c(f,e)},Le=e=>{const t=r.hits.length>=r.limit?r.limit:r.hits.length;if(!f){f=r.hits[0],a.value=c(f,e);return}if(f===r.hits[t-1]){f=void 0,a.value=G;return}for(let o=0;o<t-1;o++)if(f===r.hits[o]){f=r.hits[o+1];break}a.value=c(f,e)},ke=e=>{if(e.key==="Escape"||!a.value.length&&!r.hits.length)return A();if(r.hits.length&&(e.key==="ArrowUp"||e.key==="ArrowDown")){e.key==="ArrowDown"?Le(e):Ce(e),Q(),e.preventDefault(),e.stopPropagation();return}if(!r.query)return;const t=(o=!1)=>{if(!f&&o&&r.hits.length&&(f=r.hits[0]),f)return A(),a.value=c(f,e),de(),f};if(e.key==="Enter"){m&&e.preventDefault(),x(e,t());return}e.key==="Tab"&&xe()&&(n.retainFocus!==!1&&e.preventDefault(),t(!0))},qe=()=>{g?.when==="onFocus"&&ae(),pe()},pe=()=>{ue();const e=a.value.replace(/\s{2,}/g," ").trim();if(i?.empty&&!e.length){const t=i.empty(r);if(r.query="",Array.isArray(t)&&t.length)return r.hits=z(t,k[0]),Q();if(A(),ne(),t){const o=document.createElement("div");o.classList.add(d.empty),N(o,`${t}`),l.appendChild(o)}return ee()}if(e.length>=D){r.query=e,re();const t=JSON.stringify(r.query);v&&r.hits.length<r.limit&&V[t]?.length&&re(V[t]),Q(),Y=setTimeout(()=>{r.hits.length<r.limit&&!j&&me()},v?.debounce||200)}else r.query="",A()},he=(e="")=>(n.diacritics&&(e=I(e)),e.toLowerCase()),re=e=>{let{suggestions:t,count:o}=O.search(r.query,r.limit);if(e?.length){e.push(...t);const p={};for(const s of e)p[w(s)]=s;t=Object.values(p),o=t.length}Se(t),$&&Ae(t),r.hits=t,r.count=o,f=void 0,P&&r.hits.length&&(f=r.hits[0])},me=()=>{if(!v)return;j=!0;const e=r.query,t=JSON.stringify(e);if(J[t]||!r.query.length){j=!1,te(!0);return}fe();let o=[];le.get(typeof v.url=="function"?v.url(e):v.url.replace(v.wildcard,e),v.requestOptions).then(p=>{o=y(p),o=z(o,k[0]),oe(o)},p=>{console.error("e05",p)}).finally(()=>{J[t]=!0,V[t]=o||[],j=!1,fe(),o.length&&r.query.length&&(re(o),Q()),r.query.length&&e!==r.query&&me(),te(!0)})};function oe(e){if(e.length)for(const t of k)O.add(e,t,w)}const Se=e=>{const t=r.query.toLowerCase();e.sort((o,p)=>{const s=S(o,k[0]).toLowerCase(),u=S(p,k[0]).toLowerCase(),E=s.startsWith(t),b=u.startsWith(t);return E&&b?s.length-u.length:E?-1:b?1:0})},Ae=e=>{e.sort((t,o)=>{const p=S(t,$),s=S(o,$);return!p&&!s?0:p?s?p<s?-1:p>s?1:0:1:-1})},De=(e,t)=>{if(!t)return;const p=(E=>{const b=W(E.trim()).map(C=>F(C)).sort((C,q)=>q.length-C.length);return new RegExp(`(${b.join("|")})`,"i")})(t),s=E=>{let b=p.exec(E.data);if(n.diacritics&&!b&&(b=p.exec(I(E.data))),b){const C=document.createElement("span");C.className=d.highlight;const q=E.splitText(b.index);return q.splitText(b[0].length),C.appendChild(q.cloneNode(!0)),E.parentNode?.replaceChild(C,q),!0}return!1},u=(E,b)=>{let q;for(let M=0;M<E.childNodes.length;M++)q=E.childNodes[M],q.nodeType===3?M+=b(q)?1:0:u(q,b)};u(e,s)};function Oe(e){["id","name","placeholder","required","aria-label"].forEach(t=>e.removeAttribute(t)),e.setAttribute("readonly","true"),e.setAttribute("aria-hidden","true"),e.style.marginTop=`-${a.offsetHeight+parseInt(ce.marginBottom)}px`,e.tabIndex=-1,e.className=d.hint,a.after(e)}const Ne=e=>{const t=a.value;if(!t||c(e)===t||he(c(e)).indexOf(he(t).replace(/\s{2,}/g," ").trimStart())!==0)K.value="";else{const o=c(e),p=new RegExp(F(r.query),"i");let s=p.exec(o);n.diacritics&&!s&&(s=p.exec(I(o))),s&&(K.value=t.replace(/\s?$/,"")+o.substring(s[0].length))}},N=(e,t)=>{const o=document.createElement("template");return o.innerHTML=t,e.appendChild(o.content),t},Fe=()=>{setTimeout(()=>{document.activeElement!==a&&A()},50)};l.addEventListener("mousedown",function(e){e.stopPropagation(),e.preventDefault()});const ye=e=>{A(),O.clear(),h&&!e&&Z(h),J={},V={},g&&(g.done=!1)},$e=()=>{ue(),ye(),R.replaceWith(a.cloneNode())};return a.addEventListener("keydown",ke),a.addEventListener("input",Te),a.addEventListener("blur",Fe),a.addEventListener("focus",qe),{addToIndex:Z,reset:ye,destroy:$e}}});
