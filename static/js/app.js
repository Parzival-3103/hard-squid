document.querySelector('.menu-button')?.addEventListener('click',()=>document.querySelector('.main-nav')?.classList.toggle('open'));
document.querySelector('.admin-menu')?.addEventListener('click',()=>document.querySelector('.admin-sidebar')?.classList.toggle('open'));
document.querySelectorAll('.flash button').forEach(button=>button.addEventListener('click',()=>button.parentElement.remove()));
setTimeout(()=>document.querySelectorAll('.flash').forEach(item=>item.remove()),5000);
document.querySelectorAll('[data-modal-open]').forEach(button=>button.addEventListener('click',()=>document.getElementById(button.dataset.modalOpen)?.showModal()));
document.querySelectorAll('.modal-close').forEach(button=>button.addEventListener('click',()=>button.closest('dialog').close()));
document.querySelectorAll('dialog').forEach(dialog=>dialog.addEventListener('click',event=>{if(event.target===dialog)dialog.close()}));

const flowSvg=document.getElementById('flowSvg');
const flowDesc=document.getElementById('flowDesc');
const flowTexts={
  clientes:['Clientes','Registro, consulta de usuario, compra y seguimiento de actividad.','Datos del cliente'],
  ventas:['Ventas','Seleccionar producto, confirmar cantidad, generar venta, descontar stock y emitir ticket.','Ticket / orden'],
  productos:['Productos','Alta o edición de producto, proveedor, imagen, costo, stock y publicación.','Inventario'],
  vendedores:['Vendedores','Alta de vendedor, acceso al panel, registro de ventas y baja/reactivación.','Personal'],
  proveedores:['Proveedores','Registro de proveedor, asociación con productos y compras realizadas.','Proveedor'],
  compras:['Compras','Seleccionar proveedor, capturar concepto, total y método de pago.','Compra']
};
function drawFlow(key='clientes'){
  if(!flowSvg)return;
  const data=flowTexts[key]||flowTexts.clientes;
  const box=(x,y,w,h,t,c='process')=>`<rect x="${x}" y="${y}" width="${w}" height="${h}" rx="${c==='start'?28:10}" class="flow-node ${c}"></rect><text x="${x+w/2}" y="${y+h/2+5}" text-anchor="middle">${t}</text>`;
  const diamond=(x,y,w,h,t)=>`<polygon points="${x+w/2},${y} ${x+w},${y+h/2} ${x+w/2},${y+h} ${x},${y+h/2}" class="flow-node decision"></polygon><text x="${x+w/2}" y="${y+h/2+5}" text-anchor="middle">${t}</text>`;
  const arrow=(x1,y1,x2,y2)=>`<path d="M${x1} ${y1} L${x2} ${y2}" class="flow-arrow" marker-end="url(#arrow)"></path>`;
  flowSvg.innerHTML=`<defs><marker id="arrow" markerWidth="8" markerHeight="8" refX="7" refY="3" orient="auto"><path d="M0,0 L0,6 L7,3 z"></path></marker></defs>
  <text x="34" y="34" class="flow-title">Proceso: ${data[0]}</text>
  ${box(60,70,130,54,'Inicio','start')}${arrow(190,97,255,97)}
  ${box(255,70,155,54,'Elegir módulo')}${arrow(410,97,475,97)}
  ${diamond(475,60,130,74,'¿Nuevo?')}${arrow(605,97,670,97)}
  ${box(670,70,145,54,'Guardar datos','data')}
  ${arrow(540,134,540,195)}${box(465,195,150,54,'Editar / Baja')}${arrow(540,249,540,310)}
  ${box(465,310,150,54,'Fin','start')}
  ${box(255,190,155,54,data[2],'data')}${arrow(410,217,465,217)}`;
  flowDesc.textContent=data[1];
}
document.querySelectorAll('[data-flow]').forEach((button,i)=>button.addEventListener('click',()=>{
  document.querySelectorAll('[data-flow]').forEach(b=>b.classList.remove('active'));
  button.classList.add('active');
  drawFlow(button.dataset.flow);
}));
if(flowSvg){
  const first=document.querySelector('[data-flow]');
  first?.classList.add('active');
  drawFlow(first?.dataset.flow);
}
