(() => {
  // ✅ If you don't see this change, app.js is not loading
  const jsStatus = document.getElementById("jsStatus");
  if (jsStatus) jsStatus.textContent = "JS loaded ✅";

  console.log("[app.js] loaded ✅");

  window.addEventListener("error", (e) => {
    console.error("JS error:", e.error || e.message, e);
    alert("JS error: " + (e?.error?.message || e?.message || "unknown"));
  });

  window.addEventListener("unhandledrejection", (e) => {
    console.error("Unhandled promise rejection:", e.reason, e);
    alert("Unhandled promise rejection: " + (e?.reason?.message || String(e?.reason || "unknown")));
  });

  function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }
  function pretty(obj) { return JSON.stringify(obj, null, 2); }

  async function readJsonOrText(res) {
    const text = await res.text();
    try { return JSON.parse(text); } catch { return { raw: text }; }
  }

  function escapeHtml(str) {
    return String(str)
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#039;");
  }

  async function ensureClerkLoaded() {
    const start = Date.now();
    while (!window.Clerk) {
      await sleep(50);
      if (Date.now() - start > 10000) return false;
    }
    try {
      if (!Clerk.loaded) await Clerk.load();
      return true;
    } catch (e) {
      console.error("Clerk.load failed:", e);
      return false;
    }
  }

  async function getClerkJwt() {
    const ok = await ensureClerkLoaded();
    if (!ok) return null;
    if (!Clerk.session) return null;
    try { return (await Clerk.session.getToken()) || null; }
    catch { return null; }
  }

  async function authedFetch(url, options = {}) {
    const token = await getClerkJwt();
    const headers = new Headers(options.headers || {});
    if (token) headers.set("Authorization", `Bearer ${token}`);
    return fetch(url, { ...options, headers, credentials: "include" });
  }

  async function api(url, opts = {}) {
    const res = await authedFetch(url, {
      headers: { "Content-Type": "application/json", ...(opts.headers || {}) },
      ...opts,
    });

    const text = await res.text();
    let data = {};
    try { data = JSON.parse(text); } catch { data = { raw: text }; }

    if (!res.ok || data.success === false) {
      const detail = data?.detail
        ? (typeof data.detail === "string" ? data.detail : JSON.stringify(data.detail, null, 2))
        : null;
      throw new Error(data.error || detail || `Request failed: ${res.status}`);
    }
    return data;
  }

  const editorCard = document.getElementById("editorCard");
  const editorBody = document.getElementById("editorBody");
  const closeEditorBtn = document.getElementById("closeEditorBtn");
  if (closeEditorBtn) closeEditorBtn.onclick = () => {
    if (editorCard) editorCard.style.display = "none";
    if (editorBody) editorBody.innerHTML = "";
  };

  function showEditor() {
    if (editorCard) editorCard.style.display = "block";
  }

  async function openPlan(savedId) {
    showEditor();
    editorBody.innerHTML = `<div class="muted">Loading...</div>`;
    const data = await api(`/api/my-plans/${savedId}/editable`, { method: "GET" });
    renderEditablePlan(savedId, data.plan, data.days);
    console.log("Loaded days:", data.days);

  }

  function dayEditorHtml(d) {
    const dayId = d.day_id ?? d.id;
    const dayNum = d.day ?? d.day_number ?? "?";

    const rows = (d.items || []).map(it => {
      const itemId = it.item_id ?? it.id;
      return `
        <tr>
          <td><input id="ex-${itemId}" value="${escapeHtml(it.exercise || it.name || "")}"></td>
          <td><input id="sets-${itemId}" type="number" min="1" value="${it.sets ?? 3}" style="width:70px"></td>
          <td><input id="reps-${itemId}" value="${escapeHtml(it.reps || "8-12")}" style="width:90px"></td>
          <td><input id="rest-${itemId}" type="number" min="0" value="${it.rest_seconds ?? 60}" style="width:90px"></td>
          <td>
            <button class="btnSmall" id="save-item-${itemId}">Save</button>
            <button class="btnSmall" id="del-item-${itemId}">Delete</button>
          </td>
        </tr>
      `;
    }).join("");

    return `
      <div class="card" style="margin-top:10px;">
        <div class="row">
          <div><b>Day ${escapeHtml(String(dayNum))}</b></div>
          <button class="btnSmall" id="add-item-${dayId}">+ Exercise</button>
        </div>

        <div style="display:flex; gap:8px; align-items:center; margin-top:10px;">
          <input id="day-title-${dayId}" value="${escapeHtml(d.title || "")}" style="flex:1">
          <button class="btnSmall" id="day-title-save-${dayId}">Save Title</button>
        </div>

        <table style="width:100%; margin-top:10px;">
          <thead>
            <tr><th>Exercise</th><th>Sets</th><th>Reps</th><th>Rest</th><th>Actions</th></tr>
          </thead>
          <tbody>${rows}</tbody>
        </table>
      </div>
    `;
  }

  function renderEditablePlan(savedId, plan, days) {
    editorBody.innerHTML = `
      <div class="muted">
        <b>${escapeHtml(plan.name)}</b> • Focus: <b>${escapeHtml(plan.primary_focus || "")}</b>
      </div>
      <div id="edit-days"></div>
    `;

    const wrap = document.getElementById("edit-days");
    wrap.innerHTML = (days || []).map(dayEditorHtml).join("");

    (days || []).forEach(d => {
      const dayId = d.day_id ?? d.id;

      document.getElementById(`day-title-save-${dayId}`).onclick = async () => {
        try {
          const title = document.getElementById(`day-title-${dayId}`).value;
          await api(`/api/edit/days/${dayId}`, { method: "PATCH", body: JSON.stringify({ title }) });
          alert("Saved title");
        } catch (e) {
          alert(e.message);
        }
      };

      document.getElementById(`add-item-${dayId}`).onclick = async () => {
        try {
          const name = prompt("Exercise name?");
          if (!name) return;
          await api(`/api/edit/days/${dayId}/items`, {
            method: "POST",
            body: JSON.stringify({ exercise_name: name, sets: 3, reps: "8-12", rest_seconds: 60 }),
          });
          await openPlan(savedId);
        } catch (e) {
          alert(e.message);
        }
      };

      (d.items || []).forEach(it => {
        const itemId = it.item_id ?? it.id;

        document.getElementById(`save-item-${itemId}`).onclick = async () => {
          try {
            const exercise_name = document.getElementById(`ex-${itemId}`).value;
            const sets = parseInt(document.getElementById(`sets-${itemId}`).value || "0", 10);
            const reps = document.getElementById(`reps-${itemId}`).value;
            const rest_seconds = parseInt(document.getElementById(`rest-${itemId}`).value || "0", 10);

            await api(`/api/edit/items/${itemId}`, {
              method: "PATCH",
              body: JSON.stringify({ exercise_name, sets, reps, rest_seconds }),
            });
            alert("Saved");
          } catch (e) {
            alert(e.message);
          }
        };

        document.getElementById(`del-item-${itemId}`).onclick = async () => {
          try {
            if (!confirm("Delete?")) return;
            await api(`/api/edit/items/${itemId}`, { method: "DELETE" });
            await openPlan(savedId);
          } catch (e) {
            alert(e.message);
          }
        };
      });
    });
  }

  async function refreshMyPlans() {
    const tbody = document.getElementById("myPlansTbody");
    if (!tbody) return;
    tbody.innerHTML = `<tr><td colspan="7" class="muted">Loading...</td></tr>`;

    const res = await authedFetch(`/api/my-plans`, { method: "GET" });
    const data = await readJsonOrText(res);

    if (!res.ok || data.success === false) {
      tbody.innerHTML = `<tr><td colspan="7" class="muted">Not authenticated</td></tr>`;
      return;
    }

    const items = data.items || [];
    if (!items.length) {
      tbody.innerHTML = `<tr><td colspan="7" class="muted">No plans yet</td></tr>`;
      return;
    }

    tbody.innerHTML = "";
    for (const it of items) {
      const focus = [it.focus1, it.focus2, it.focus3].filter(Boolean).join(", ");
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td>${escapeHtml(String(it.created_at))}</td>
        <td>${escapeHtml(it.plan_name)}</td>
        <td>${escapeHtml(it.primary_focus)}</td>
        <td>${escapeHtml(it.body_type || "")}</td>
        <td>${escapeHtml(focus)}</td>
        <td>
          <button class="btnSmall" id="open-plan-${it.id}">Open</button>
          <button class="btnSmall" id="export-plan-${it.id}" style="background-color:#1976d2; color:white;">Export CSV</button>
          <button class="btnSmall" id="delete-plan-${it.id}" style="background-color:#d32f2f; color:white;">Delete</button>
        </td>
      `;
      tr.querySelector(`#open-plan-${it.id}`).onclick = () => openPlan(it.id);
      tr.querySelector(`#export-plan-${it.id}`).onclick = async () => {
        try {
          const response = await authedFetch(`/api/my-plans/${it.id}/export-csv`);
          if (!response.ok) {
            const err = await readJsonOrText(response);
            throw new Error(err.error || "Export failed");
          }
          // Create blob from response and trigger download
          const blob = await response.blob();
          const url = window.URL.createObjectURL(blob);
          const a = document.createElement('a');
          a.href = url;
          a.download = response.headers.get('content-disposition')?.split('filename=')[1]?.replace(/"/g, '') || 'plan.csv';
          document.body.appendChild(a);
          a.click();
          window.URL.revokeObjectURL(url);
          a.remove();
          alert("Plan exported successfully!");
        } catch (e) {
          alert("Export failed: " + e.message);
        }
      };
      tr.querySelector(`#delete-plan-${it.id}`).onclick = async () => {
        if (!confirm(`Delete "${escapeHtml(it.plan_name)}"?`)) return;
        try {
          await api(`/api/my-plans/${it.id}`, { method: "DELETE" });
          alert("Plan deleted");
          await refreshMyPlans();
        } catch (e) {
          alert("Delete failed: " + e.message);
        }
      };
      tbody.appendChild(tr);
    }
  }

  // ==================== PLAN SELECTION ====================
  async function loadAvailablePlans() {
    try {
      const res = await fetch(`/api/available-plans`);
      const data = await res.json();
      if (!res.ok || !data.success) throw new Error(data.error || "Failed to load plans");
      return data.plans; // { "3": [...], "5": [...] }
    } catch (e) {
      console.error("Error loading plans:", e);
      alert("Failed to load available plans: " + e.message);
      return {};
    }
  }

  function showPlanSelectionModal() {
    const overlay = document.getElementById("planSelectionOverlay");
    if (overlay) overlay.style.display = "flex";
  }

  function closePlanSelectionModal() {
    const overlay = document.getElementById("planSelectionOverlay");
    if (overlay) overlay.style.display = "none";
  }

  async function renderPlanSelection() {
    const plans = await loadAvailablePlans();
    const body = document.getElementById("planSelectionBody");
    if (!body) return;

    let html = "";
    for (const [days, planList] of Object.entries(plans).sort()) {
      html += `<div style="margin-bottom: 24px;">`;
      html += `<p class="eyebrow" style="margin-bottom: 12px;">${days}-Day Plans</p>`;
      html += `<div class="planGrid">`;

      for (const plan of planList) {
        html += `
          <div class="planCard" id="plan-btn-${plan.id}" style="cursor:pointer;">
            <p class="planCardTitle">${escapeHtml(plan.name)}</p>
            <p class="planCardSub">Focus: <strong>${escapeHtml(plan.primary_focus.toUpperCase())}</strong></p>
            <p class="planCardSub">${days}-Day Split</p>
          </div>
        `;
      }
      html += `</div></div>`;
    }

    body.innerHTML = html;

    // Attach click handlers
    for (const [days, planList] of Object.entries(plans)) {
      for (const plan of planList) {
        const btn = document.getElementById(`plan-btn-${plan.id}`);
        if (btn) {
          btn.onclick = async () => {
            await selectPlan(plan.id);
            closePlanSelectionModal();
          };
        }
      }
    }
  }

  async function selectPlan(planId) {
    try {
      const formData = new FormData();
      formData.append("plan_id", planId);
      const res = await authedFetch(`/api/select-plan`, { method: "POST", body: formData });
      const data = await res.json();
      if (!res.ok || !data.success) throw new Error(data.error || "Failed to select plan");
      alert(`✅ ${data.message}\n\nNow open your plan to customize it!`);
      await refreshMyPlans();
    } catch (e) {
      console.error("Error selecting plan:", e);
      alert("Failed to select plan: " + e.message);
    }
  }

  async function bootClerkUI() {
    const signedOut = document.getElementById("signedOut");
    const signedIn = document.getElementById("signedIn");
    const signedInContent = document.getElementById("signedInContent");
    const authSlot = document.getElementById("authSlot");
    const authError = document.getElementById("authError");

    const ok = await ensureClerkLoaded();
    if (!ok) {
      if (authError) {
        authError.style.display = "block";
        authError.textContent = "Clerk failed to load. Check publishable key + allowed origins.";
      }
      return;
    }

    if (Clerk.user) {
      authSlot.innerHTML = `<div id="userButton"></div>`;
      Clerk.mountUserButton(document.getElementById("userButton"));
      signedOut.style.display = "none";
      signedIn.style.display = "block";
      if (signedInContent) signedInContent.style.display = "block";
      await refreshMyPlans();
    } else {
      authSlot.innerHTML = "";
      signedOut.style.display = "block";
      signedIn.style.display = "none";
      if (signedInContent) signedInContent.style.display = "none";
      Clerk.mountSignIn(document.getElementById("signIn"));
    }
  }

  function openConsentModal() {
    return new Promise((resolve) => {
      const overlay = document.getElementById("consentOverlay");
      const agreeBtn = document.getElementById("consentAgreeBtn");
      const cancelBtn = document.getElementById("consentCancelBtn");
      const closeBtn = document.getElementById("consentCloseBtn");

      const cleanup = () => {
        agreeBtn?.removeEventListener("click", onAgree);
        cancelBtn?.removeEventListener("click", onCancel);
        closeBtn?.removeEventListener("click", onCancel);
        if (overlay) overlay.style.display = "none";
      };

      const onAgree = () => { cleanup(); resolve(true); };
      const onCancel = () => { cleanup(); resolve(false); };

      agreeBtn?.addEventListener("click", onAgree);
      cancelBtn?.addEventListener("click", onCancel);
      closeBtn?.addEventListener("click", onCancel);

      if (overlay) overlay.style.display = "grid";
    });
  }

  function showMessageModal(title, body) {
    const overlay = document.getElementById("messageOverlay");
    const titleEl = document.getElementById("messageTitle");
    const bodyEl = document.getElementById("messageBody");
    const okBtn = document.getElementById("messageOkBtn");
    const closeBtn = document.getElementById("messageCloseBtn");

    if (titleEl) titleEl.textContent = title || "Notice";
    if (bodyEl) bodyEl.textContent = body || "";

    const cleanup = () => {
      okBtn?.removeEventListener("click", onClose);
      closeBtn?.removeEventListener("click", onClose);
      if (overlay) overlay.style.display = "none";
    };

    const onClose = () => cleanup();

    okBtn?.addEventListener("click", onClose);
    closeBtn?.addEventListener("click", onClose);

    if (overlay) overlay.style.display = "grid";
  }

  // Bind buttons
  document.getElementById("refreshPlansBtn")?.addEventListener("click", refreshMyPlans);

  document.getElementById("planSelectionCloseBtn")?.addEventListener("click", closePlanSelectionModal);

  // Open plan selection when signed in
  const selectPlanBtn = document.getElementById("selectPlanBtn");
  if (selectPlanBtn) {
    selectPlanBtn.addEventListener("click", async () => {
      await renderPlanSelection();
      showPlanSelectionModal();
    });
  }

  let analyzeImageInProgress = false;

  document.getElementById("analyzeImageBtn")?.addEventListener("click", async () => {
    // Prevent double submissions
    if (analyzeImageInProgress) {
      console.log("[analyzeImageBtn] Already in progress, ignoring duplicate click");
      return;
    }

    const imageInput = document.getElementById("imageInput");
    const imageResult = document.getElementById("imageResult");
    imageResult.textContent = "";

    if (!imageInput.files || imageInput.files.length === 0) {
      imageResult.textContent = "Pick an image first.";
      return;
    }

    const agreed = await openConsentModal();
    if (!agreed) {
      imageResult.textContent = "Image analysis canceled — consent not given.";
      return;
    }

    analyzeImageInProgress = true;

    try {
      const planDaysRadio = document.querySelector('input[name="planDays"]:checked');
      const planDays = planDaysRadio ? String(planDaysRadio.value) : "3";
      console.log(`[analyzeImageBtn] selected plan_days: ${planDays}`);

      const form = new FormData();
      form.append("file", imageInput.files[0]);
      form.append("consent", "true");
      form.append("plan_days", planDays);

      const res = await authedFetch(`/api/analyze-image`, { method: "POST", body: form });
      const data = await readJsonOrText(res);
      if (!res.ok) throw new Error(JSON.stringify(data, null, 2));

      // Display minimal results
      let resultText = `Analysis Complete!\n`;
      resultText += `Body Type: ${data.detected_body_type || 'Unknown'}\n`;
      resultText += `Plan: ${data.selected_plan_name || 'Unknown'}\n`;
      resultText += `Duration: ${data.plan_days_selected || '3'} days/week`;

      imageResult.textContent = resultText;
      console.log(`[analyzeImageBtn] Detected: ${data.detected_body_type}, Selected: ${data.selected_plan_body_type}`);

      await refreshMyPlans();
    } catch (e) {
      alert("Analyze failed: " + e.message);
    } finally {
      analyzeImageInProgress = false;
    }
  });

  document.getElementById("analyzeVideoBtn")?.addEventListener("click", async () => {
    const videoInput = document.getElementById("videoInput");
    const exerciseSelect = document.getElementById("exerciseSelect");
    const videoResult = document.getElementById("videoResult");
    const downloadLink = document.getElementById("downloadLink");

    videoResult.textContent = "";
    downloadLink.textContent = "";
    downloadLink.href = "";

    if (!videoInput.files || videoInput.files.length === 0) {
      videoResult.textContent = "Pick a video first.";
      return;
    }

    try {
      const form = new FormData();
      form.append("exercise", exerciseSelect.value);
      form.append("file", videoInput.files[0]);

      const res = await fetch(`/api/analyze-video`, { method: "POST", body: form });
      const data = await readJsonOrText(res);
      if (!res.ok) throw new Error(JSON.stringify(data, null, 2));

      videoResult.textContent = pretty(data);
      if (data.annotated_video_url) {
        downloadLink.href = data.annotated_video_url;
        downloadLink.textContent = "Open annotated video";
      }
    } catch (e) {
      console.error("Analyze video failed", e);
      showMessageModal("Video analyze failed", e.message || "Unknown error");
    }
  });

  bootClerkUI();
})();
