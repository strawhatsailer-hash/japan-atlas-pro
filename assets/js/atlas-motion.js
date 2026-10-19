/* Japan Atlas micro-interactions. Progressive enhancement only; no itinerary data is changed here. */
(function(){
 'use strict';
 const reduceMotion=()=>window.matchMedia&&window.matchMedia('(prefers-reduced-motion: reduce)').matches;
 function replaySection(section){
  if(!section||!section.classList.contains('active')||reduceMotion())return;
  section.classList.remove('atlas-section-enter');
  void section.offsetWidth;
  section.classList.add('atlas-section-enter');
 }
 function observeSections(){
  const sections=document.querySelectorAll('.section');
  if(!sections.length)return;
  const observer=new MutationObserver(records=>records.forEach(record=>{
   if(record.attributeName==='class'&&record.target.classList.contains('active'))replaySection(record.target);
  }));
  sections.forEach(section=>observer.observe(section,{attributes:true,attributeFilter:['class']}));
 }
 document.addEventListener('pointerdown',event=>{
  const button=event.target.closest('button,.btn,.atlas-btn,.atlas-route-button');
  if(button&&!reduceMotion())button.classList.add('atlas-pressing');
 });
 ['pointerup','pointercancel'].forEach(type=>document.addEventListener(type,event=>{
  document.querySelectorAll('.atlas-pressing').forEach(el=>el.classList.remove('atlas-pressing'));
 }));
 document.addEventListener('change',event=>{
  const input=event.target;
  if(input.matches('input[type="checkbox"]')&&input.closest('.check-item')){
   const item=input.closest('.check-item');
   if(item&&!reduceMotion()){item.classList.remove('atlas-check-feedback');void item.offsetWidth;item.classList.add('atlas-check-feedback')}
  }
 });
 function animateNumber(el){
  if(!el||reduceMotion())return;
  el.classList.remove('atlas-number-updated');void el.offsetWidth;el.classList.add('atlas-number-updated');
 }
 function observeBudget(){
  ['budgetBig','statBudget','budgetPerPerson','checkPct','checkDone'].forEach(id=>{
   const el=document.getElementById(id);if(!el)return;
   new MutationObserver(()=>animateNumber(el)).observe(el,{childList:true,characterData:true,subtree:true});
  });
 }
 function routeCoordinates(){
  const state=window.state;
  if(!state||!Array.isArray(state.places))return [];
  return state.places.map((place,index)=>({place,index}))
   .filter(x=>x.place.status!=='Excluded'&&x.place.day&&Number.isFinite(Number(x.place.lat))&&Number.isFinite(Number(x.place.lng))&&x.place.lat!==''&&x.place.lng!=='')
   .sort((a,b)=>(Number(a.place.day)||99)-(Number(b.place.day)||99)||a.index-b.index)
   .map(x=>[Number(x.place.lng),Number(x.place.lat)]);
 }
 function updateRoutes(){
  const maps=window.__atlasMaps;
  if(!Array.isArray(maps)||!window.maplibregl)return;
  const coords=routeCoordinates();
  maps.forEach(entry=>{
   const map=entry&&entry.map;
   if(!map||!map.isStyleLoaded())return;
   try{
    const source=map.getSource('atlas-itinerary-route');
    const data=coords.length>1?{type:'Feature',properties:{kind:'planning-sequence'},geometry:{type:'LineString',coordinates:coords}}:{type:'FeatureCollection',features:[]};
    if(source){source.setData(data)}
    else{
     map.addSource('atlas-itinerary-route',{type:'geojson',data,lineMetrics:true});
     const firstSymbol=(map.getStyle().layers||[]).find(layer=>layer.type==='symbol')?.id;
     map.addLayer({id:'atlas-itinerary-route-line',type:'line',source:'atlas-itinerary-route',layout:{'line-cap':'round','line-join':'round'},paint:{'line-color':'#c7503d','line-width':['interpolate',['linear'],['zoom'],4,2,12,3.5],'line-opacity':.78,'line-dasharray':[1.5,1.2]}},firstSymbol);
    }
   }catch(e){/* Map styles can be between reloads; next refresh will retry. */}
  });
 }
 function updateSelectedPin(){
  const selected=window.state?.places?.find(place=>place.id===window.state.selectedId);
  document.querySelectorAll('.maplibregl-marker button[aria-label]').forEach(pin=>{
   const isSelected=!!selected&&pin.getAttribute('aria-label')===selected.name;
   pin.classList.toggle('atlas-stop-selected',isSelected);
   if(isSelected)pin.setAttribute('aria-current','location');else pin.removeAttribute('aria-current');
  });
 }
 function installMapEnhancements(){
  if(typeof window.refreshMaps==='function'&&!window.__atlasMotionRefreshWrapped){
   const original=window.refreshMaps;
   window.refreshMaps=function(){const result=original.apply(this,arguments);updateRoutes();updateSelectedPin();return result};
   window.__atlasMotionRefreshWrapped=true;
  }
  const maps=window.__atlasMaps;
  if(Array.isArray(maps))maps.forEach(entry=>{
   if(entry?.map&&!entry.map.__atlasMotionHooks){
    entry.map.__atlasMotionHooks=true;
    entry.map.on('style.load',()=>{updateRoutes();updateSelectedPin()});
    entry.map.on('load',()=>{updateRoutes();updateSelectedPin()});
   }
  });
  updateRoutes();updateSelectedPin();
 }
 function watchDynamicMap(){
  const root=document.getElementById('mapPlaceList')||document.body;
  new MutationObserver(()=>{updateSelectedPin()}).observe(root,{childList:true,subtree:true,attributes:true,attributeFilter:['class']});
  document.addEventListener('click',event=>{
   if(event.target.closest('[data-page="map"],[data-goto="map"],.place-list-row'))requestAnimationFrame(()=>{installMapEnhancements();updateSelectedPin()});
  });
  if(typeof window.refreshMaps==='function'){
   const original=window.refreshMaps;
   if(!window.__atlasMotionRefreshWrapped){
    window.refreshMaps=function(){const result=original.apply(this,arguments);installMapEnhancements();return result};
    window.__atlasMotionRefreshWrapped=true;
   }
  }
 }
 function init(){
  observeSections();observeBudget();watchDynamicMap();
  document.querySelectorAll('.section.active').forEach(replaySection);
  installMapEnhancements();
 }
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init,{once:true});else init();
})();
