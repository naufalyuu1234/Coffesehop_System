(() => {
  const form = document.querySelector("[data-payment-form]");
  if (!form) return;

  const amountDue = Number(form.dataset.amountDue || 0);
  const amountInput = form.querySelector("[data-amount-paid]");
  const refWrapper = form.querySelector("[data-reference-wrapper]");
  const refInput = form.querySelector("[data-reference-input]");
  const changePreview = form.querySelector("[data-change-preview]");
  const statusPreview = form.querySelector("[data-status-preview]");
  const submitButton = form.querySelector("[data-submit-payment]");
  const methodInputs = [...form.querySelectorAll("input[name='payment_method']")];

  const toRupiah = (value) => `Rp${Math.max(value, 0).toLocaleString("id-ID")}`;

  const activeMethod = () => (methodInputs.find((item) => item.checked) || {}).value || "CASH";

  const toggleMethodStyles = () => {
    methodInputs.forEach((input) => {
      const card = input.closest(".tx-payment-option");
      if (!card) return;
      card.classList.toggle("is-active", input.checked);
    });
  };

  const updateState = () => {
    toggleMethodStyles();
    const method = activeMethod();
    const amountPaid = Number(amountInput.value || 0);
    const isCash = method === "CASH";

    refWrapper.hidden = isCash;
    refInput.required = !isCash;

    let valid = true;
    let message = "Siap diproses.";
    let change = 0;

    if (isCash) {
      change = amountPaid - amountDue;
      if (amountPaid < amountDue) {
        valid = false;
        message = "Nominal tunai kurang dari total tagihan.";
      } else {
        message = "Nominal tunai valid.";
      }
    } else {
      if (amountPaid !== amountDue) {
        valid = false;
        message = "Pembayaran non-tunai harus sama dengan total tagihan.";
      } else if (!refInput.value.trim()) {
        valid = false;
        message = "Referensi pembayaran wajib diisi.";
      } else {
        message = "Pembayaran non-tunai valid.";
      }
    }

    changePreview.textContent = toRupiah(change);
    statusPreview.textContent = message;
    statusPreview.className = `tx-status-note ${valid ? "tx-status-note--valid" : "tx-status-note--invalid"}`;
    submitButton.disabled = !valid;
  };

  methodInputs.forEach((input) => input.addEventListener("change", updateState));
  amountInput.addEventListener("input", updateState);
  refInput.addEventListener("input", updateState);

  form.addEventListener("submit", () => {
    submitButton.disabled = true;
    submitButton.textContent = "Memproses...";
  });

  updateState();
})();
