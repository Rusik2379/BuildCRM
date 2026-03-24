document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('[data-open-modal]').forEach(btn => {
    btn.addEventListener('click', () => {
      const modal = document.getElementById(btn.dataset.openModal);
      if (modal) modal.classList.add('open');
    });
  });

  document.querySelectorAll('[data-close-modal]').forEach(btn => {
    btn.addEventListener('click', () => {
      const modal = document.getElementById(btn.dataset.closeModal);
      if (modal) modal.classList.remove('open');
    });
  });

  document.querySelectorAll('[data-autocomplete]').forEach(input => {
    const url = input.dataset.autocomplete;
    const list = input.parentElement.querySelector('.autocomplete-list');
    let timer = null;

    input.addEventListener('input', () => {
      clearTimeout(timer);
      const value = input.value.trim();
      if (!value) {
        list.innerHTML = '';
        list.classList.remove('open');
        return;
      }
      timer = setTimeout(async () => {
        try {
          const res = await fetch(`${url}?q=${encodeURIComponent(value)}`);
          const items = await res.json();
          list.innerHTML = '';
          if (!items.length) {
            list.classList.remove('open');
            return;
          }
          items.forEach(item => {
            const option = document.createElement('div');
            option.className = 'autocomplete-item';
            option.textContent = item.label;
            option.addEventListener('click', () => {
              input.value = item.name || item.label;
              list.classList.remove('open');
            });
            list.appendChild(option);
          });
          list.classList.add('open');
        } catch {
          list.classList.remove('open');
        }
      }, 250);
    });

    document.addEventListener('click', (e) => {
      if (!input.parentElement.contains(e.target)) {
        list.classList.remove('open');
      }
    });
  });
});
