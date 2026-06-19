document.querySelector('.menu-button')?.addEventListener('click',()=>document.querySelector('.main-nav')?.classList.toggle('open'));
document.querySelector('.admin-menu')?.addEventListener('click',()=>document.querySelector('.admin-sidebar')?.classList.toggle('open'));
document.querySelectorAll('.flash button').forEach(button=>button.addEventListener('click',()=>button.parentElement.remove()));
setTimeout(()=>document.querySelectorAll('.flash').forEach(item=>item.remove()),5000);
document.querySelectorAll('[data-modal-open]').forEach(button=>button.addEventListener('click',()=>document.getElementById(button.dataset.modalOpen)?.showModal()));
document.querySelectorAll('.modal-close').forEach(button=>button.addEventListener('click',()=>button.closest('dialog').close()));
document.querySelectorAll('dialog').forEach(dialog=>dialog.addEventListener('click',event=>{if(event.target===dialog)dialog.close()}));
