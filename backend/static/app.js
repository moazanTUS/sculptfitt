(() => {
  // ✅ If you don't see this change, app.js is not loading
  const jsStatus = document.getElementById("jsStatus");
  if (jsStatus) jsStatus.textContent = "JS loaded ✅";

  console.log("[app.js] loaded ✅");

  // Authentication check and logout setup
  async function setupAuth() {
    const start = Date.now();
    while (!window.Clerk && Date.now() - start < 10000) {
      await new Promise(r => setTimeout(r, 50));
    }

    if (!window.Clerk) {
      console.error("[setupAuth] Clerk not loaded");
      return;
    }

    try {
      if (!Clerk.loaded) await Clerk.load();

      // If no user, redirect to signin
      if (!Clerk.user) {
        window.location.href = '/signin';
        return;
      }

      // Show user info and logout button
      const authSlot = document.getElementById('authSlot');
      if (authSlot) {
        const userName = Clerk.user.firstName || Clerk.user.emailAddresses?.[0]?.emailAddress || 'User';
        authSlot.innerHTML = `
          <div style="display: flex; align-items: center; gap: 12px;">
            <span style="font-size: 13px; color: var(--muted);">👤 ${escapeHtml(userName)}</span>
            <button id="logoutBtn" class="btn" style="font-size: 12px; padding: 6px 12px; background: rgba(255,107,157,0.2); border-color: #ff6b9d; color: #ff6b9d;">
              Sign Out
            </button>
          </div>
        `;

        const logoutBtn = document.getElementById('logoutBtn');
        if (logoutBtn) {
          logoutBtn.onclick = async () => {
            logoutBtn.disabled = true;
            logoutBtn.textContent = 'Signing out...';
            try {
              await Clerk.signOut(() => {
                window.location.href = '/signin';
              });
            } catch (e) {
              console.error("Logout error:", e);
              window.location.href = '/signin';
            }
          };
        }
      }
    } catch (e) {
      console.error("[setupAuth] Error:", e);
    }
  }

  setupAuth();

  // Page Navigation
  function setupPageNavigation() {
    try {
      const navBtns = document.querySelectorAll(".navBtn");
      const pages = document.querySelectorAll(".page");

      console.log("[setupPageNavigation] Found buttons:", navBtns.length, "Found pages:", pages.length);

      if (navBtns.length === 0 || pages.length === 0) {
        console.error("[setupPageNavigation] ERROR: No nav buttons or pages found!");
        return;
      }

      navBtns.forEach((btn) => {
        btn.addEventListener("click", () => {
          const targetPage = btn.dataset.page;
          console.log("[navBtn click] Target page:", targetPage);

          // Update active button
          navBtns.forEach((b) => b.classList.remove("active"));
          btn.classList.add("active");

          // Update active page with animation
          pages.forEach((page) => {
            console.log("[page update] Page:", page.id, "target:", targetPage, "matches:", page.dataset.page === targetPage);
            if (page.dataset.page === targetPage) {
              page.classList.add("active");
            } else {
              page.classList.remove("active");
            }
          });

          // Refresh plans when switching to workouts
          if (targetPage === "workouts") {
            refreshMyPlans();
            initExploreWorkouts();
          }
        });
      });
      console.log("[setupPageNavigation] Setup complete ✅");
    } catch (err) {
      console.error("[setupPageNavigation] ERROR:", err);
    }
  }

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
          <button class="btnSmall" id="open-plan-${it.id}">📋 View Workout</button>
          <button class="btnSmall" id="export-plan-${it.id}" style="background-color:#1976d2; color:white;">📥 Export CSV</button>
          <button class="btnSmall" id="delete-plan-${it.id}" style="background-color:#d32f2f; color:white;">🗑️ Delete</button>
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

  async function renderExplorePlans() {
    const grid = document.getElementById("explorePlansGrid");
    if (!grid) return;

    grid.innerHTML = `<div class="muted">Loading available plans...</div>`;

    const plans = await loadAvailablePlans();
    grid.innerHTML = "";

    const allPlans = [];
    for (const [days, planList] of Object.entries(plans)) {
      for (const plan of planList) {
        allPlans.push({ ...plan, days: parseInt(days) });
      }
    }

    if (!allPlans.length) {
      grid.innerHTML = `<div class="muted">No plans available</div>`;
      return;
    }

    for (const plan of allPlans) {
      const card = document.createElement("div");
      card.className = "planCard";
      card.style.padding = "12px";
      card.style.display = "flex";
      card.style.flexDirection = "column";

      const expandId = `expand-${plan.id}`;
      const contentId = `content-${plan.id}`;
      const saveId = `save-${plan.id}`;

      card.innerHTML = `
        <p class="planCardTitle" style="font-size: 13px; margin: 0 0 4px 0; font-weight: bold;">${escapeHtml(plan.name)}</p>
        <p class="planCardSub" style="font-size: 11px; margin: 0 0 8px 0; color: var(--muted);">${plan.primary_focus.toUpperCase()} • ${plan.days}d</p>
        <div style="display: flex; gap: 6px; margin-bottom: 10px;">
          <button class="btn" style="flex: 1; font-size: 10px; padding: 6px 8px; white-space: nowrap;" id="${expandId}">View</button>
          <button class="btn" style="flex: 1; font-size: 10px; padding: 6px 8px; background: var(--accent); color: white; white-space: nowrap;" id="${saveId}">Save</button>
        </div>
        <div id="${contentId}" style="display: none; margin-top: 12px; padding: 10px; background: rgba(0,0,0,0.05); border-radius: 4px; max-height: 200px; overflow-y: auto; border-left: 3px solid var(--accent);">
          <div style="font-size: 10px; color: var(--muted);">Loading...</div>
        </div>
      `;

      const viewBtn = card.querySelector(`#${expandId}`);
      const saveBtn = card.querySelector(`#${saveId}`);
      const content = card.querySelector(`#${contentId}`);
      let loaded = false;

      // View Exercises - just show/hide, no saving
      viewBtn.onclick = async () => {
        if (content.style.display === "none") {
          content.style.display = "block";
          viewBtn.textContent = "Hide Exercises";

          if (!loaded) {
            // Fetch exercises without saving
            try {
              const res = await authedFetch(`/api/plans/${plan.id}`);
              const planData = await res.json();

              if (res.ok && planData.success) {
                const days = planData.days || [];
                let exList = [];

                for (const day of days) {
                  exList.push(`<div style="margin-bottom: 6px; padding-bottom: 6px; border-bottom: 1px solid var(--accent); color: var(--accent); font-weight: bold; font-size: 11px;">Day ${day.day}</div>`);
                  if (day.items && day.items.length) {
                    for (const item of day.items) {
                      exList.push(`<div style="font-size: 10px; margin: 3px 0; color: var(--text);">${escapeHtml(item.exercise)} - ${item.sets}x${item.reps}</div>`);
                    }
                  }
                }

                content.innerHTML = exList.join("") || '<div style="font-size: 10px; color: var(--muted);">No exercises</div>';
              } else {
                content.innerHTML = '<div style="font-size: 10px; color: var(--muted);">Failed to load exercises</div>';
              }
              loaded = true;
            } catch (e) {
              console.error("Error loading workout:", e);
              content.innerHTML = '<div style="font-size: 10px; color: var(--muted);">Error loading workout</div>';
              loaded = true;
            }
          }
        } else {
          content.style.display = "none";
          viewBtn.textContent = "View Exercises";
        }
      };

      // Save Workout - saves to user's workouts
      saveBtn.onclick = async () => {
        try {
          saveBtn.disabled = true;
          saveBtn.textContent = "Saving...";
          const formData = new FormData();
          formData.append("plan_id", plan.id);
          const res = await authedFetch("/api/select-plan", { method: "POST", body: formData });
          const data = await res.json();
          if (!res.ok || !data.success) throw new Error(data.error || "Failed to save plan");
          alert(`✅ ${data.message}\n\nNow open your plan to customize it!`);
          await refreshMyPlans();
        } catch (e) {
          console.error("Error saving plan:", e);
          alert("Failed to save plan: " + e.message);
        } finally {
          saveBtn.disabled = false;
          saveBtn.textContent = "Save Workout";
        }
      };

      grid.appendChild(card);
    }
  }

  // Initialize explore workouts button
  function initExploreWorkouts() {
    const btn = document.getElementById("exploreWorkoutsBtn");
    const container = document.getElementById("explorePlansContainer");
    if (!btn || !container) return;

    btn.onclick = async () => {
      if (container.style.display === "none") {
        container.style.display = "block";
        btn.textContent = "Hide Workouts";
        await renderExplorePlans();
      } else {
        container.style.display = "none";
        btn.textContent = "Explore Workouts";
      }
    };
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
      // Show all pages when authenticated
      document.querySelectorAll(".page").forEach(p => p.style.display = "none");
      document.getElementById("analysis-page").style.display = "block";
      await refreshMyPlans();
    } else {
      authSlot.innerHTML = "";
      // Show auth message
      alert("Please sign in to use SculpFit");
      Clerk.mountSignIn(document.getElementById("signIn") || document.body);
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

  function openVideoConsentModal() {
    return new Promise((resolve) => {
      const overlay = document.getElementById("videoConsentOverlay");
      const agreeBtn = document.getElementById("videoConsentAgreeBtn");
      const cancelBtn = document.getElementById("videoConsentCancelBtn");
      const closeBtn = document.getElementById("videoConsentCloseBtn");

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
      const difficultyRadio = document.querySelector('input[name="difficulty"]:checked');
      const difficulty = difficultyRadio ? String(difficultyRadio.value) : "intermediate";
      const daysRadio = document.querySelector('input[name="daysPerWeek"]:checked');
      const daysPerWeek = daysRadio ? String(daysRadio.value) : "4";
      console.log(`[analyzeImageBtn] selected difficulty: ${difficulty}, days: ${daysPerWeek}`);

      const form = new FormData();
      form.append("file", imageInput.files[0]);
      form.append("consent", "true");
      form.append("difficulty", difficulty);
      form.append("daysPerWeek", daysPerWeek);

      imageResult.textContent = "🔄 Analyzing your physique with AI...";

      const res = await authedFetch(`/api/analyze-image-v2`, { method: "POST", body: form });
      const data = await readJsonOrText(res);
      if (!res.ok) throw new Error(JSON.stringify(data, null, 2));

      // Display results summary
      let resultText = `✅ Analysis Complete!\n`;
      resultText += `Body Type: ${data.body_type || 'Unknown'}\n`;
      resultText += `Primary Focus: ${data.primary_focus || 'Chest'}\n`;
      resultText += `Secondary Focus: ${(data.secondary_focuses || []).join(', ')}\n`;
      resultText += `Difficulty: ${data.difficulty}\n`;
      resultText += `Duration: 8 weeks, 4 days/week\n`;
      resultText += `\nRationale:\n${data.rationale || 'N/A'}`;

      imageResult.textContent = resultText;

      // Display workout plan
      if (data.workout_plan) {
        displayWorkoutPlan(data.workout_plan, data.primary_focus);
      }

      console.log(`[analyzeImageBtn] Analysis complete:`, data);

      await refreshMyPlans();
    } catch (e) {
      alert("Analyze failed: " + e.message);
    } finally {
      analyzeImageInProgress = false;
    }
  });

  // Display generated workout plan on Body Analysis page
  function displayWorkoutPlan(plan, primaryFocus) {
    const container = document.getElementById("workoutResultsContainer");
    const detailsDiv = document.getElementById("workoutDetailsDisplay");
    const titleH2 = document.getElementById("workoutTitle");

    if (!container || !detailsDiv || !plan) return;

    titleH2.textContent = `${primaryFocus || 'Personalized'} Focus Plan`;
    detailsDiv.innerHTML = "";

    const daysData = plan.days || [];

    daysData.forEach((dayObj) => {
      const dayCard = document.createElement("div");
      dayCard.style.cssText = "margin-bottom: 20px; padding: 15px; border-left: 3px solid var(--accent); background: rgba(255, 255, 255, 0.05);";

      let dayHTML = `<h3 style="margin: 0 0 10px 0; color: var(--accent);">Day ${dayObj.day}: ${dayObj.focus || dayObj.name || 'Workout'}</h3>`;

      if (dayObj.exercises && Array.isArray(dayObj.exercises)) {
        dayHTML += `<div style="margin-top: 10px;">`;
        dayObj.exercises.forEach((ex) => {
          dayHTML += `<div style="margin-bottom: 8px; padding: 10px; background: rgba(0,0,0,0.2); border-radius: 6px;">
            <div style="font-weight: 500;">${escapeHtml(ex.name)}</div>
            <div style="font-size: 12px; color: var(--muted); margin-top: 4px;">
              ${ex.sets}x${ex.reps} • ${ex.rest_seconds}s rest
            </div>
          </div>`;
        });
        dayHTML += `</div>`;
      }

      dayCard.innerHTML = dayHTML;
      detailsDiv.appendChild(dayCard);
    });

    container.style.display = "block";
  }

  // Display workout in read-only format on Body Analysis page (legacy)
  function displayWorkoutReadOnly(plan, days) {
    const container = document.getElementById("workoutResultsContainer");
    const detailsDiv = document.getElementById("workoutDetailsDisplay");
    const titleH2 = document.getElementById("workoutTitle");

    if (!container || !detailsDiv || !plan) return;

    titleH2.textContent = plan.name || "Workout Plan";
    detailsDiv.innerHTML = "";

    // Display each day - use the days array passed separately
    for (const day of days || []) {
      const daySection = document.createElement("div");
      daySection.style.marginBottom = "20px";
      daySection.style.padding = "15px";
      daySection.style.background = "rgba(255, 255, 255, 0.03)";
      daySection.style.borderRadius = "10px";
      daySection.style.borderLeft = "3px solid var(--accent)";

      const dayNum = day.day || day.day_number || "?";
      let dayHTML = `<h3 style="margin-top: 0; margin-bottom: 10px; color: var(--accent);">Day ${dayNum}</h3>`;

      if (day.title) {
        dayHTML += `<p style="margin: 5px 0; font-size: 0.95em; color: var(--muted);">${day.title}</p>`;
      }

      dayHTML += "<ul style='margin: 10px 0; padding-left: 20px;'>";
      const itemsList = day.items || [];
      for (const item of itemsList) {
        const exerciseName = item.exercise || item.exercise_name || "Exercise";
        const sets = item.sets || 3;
        const reps = item.reps || "8-12";
        const itemText = `${exerciseName} - ${sets} sets x ${reps} reps`;
        dayHTML += `<li style="margin: 5px 0; line-height: 1.5;">${itemText}</li>`;
      }
      dayHTML += "</ul>";

      daySection.innerHTML = dayHTML;
      detailsDiv.appendChild(daySection);
    }

    container.style.display = "block";
  }

  // Visual Video Trimmer
  let trimmerState = {
    isDraggingStart: false,
    isDraggingEnd: false,
    startPercent: 0,
    endPercent: 100,
    videoDuration: 0
  };

  function initTrimmer() {
    const videoPreview = document.getElementById("videoPreview");
    const trimmerStartHandle = document.getElementById("trimmerStartHandle");
    const trimmerEndHandle = document.getElementById("trimmerEndHandle");
    const trimmerSelection = document.getElementById("trimmerSelection");
    const trimmerContainer = document.getElementById("trimmerContainer");
    const trimmerTimeDisplay = document.getElementById("trimmerTimeDisplay");
    const repCountInput = document.getElementById("repCount");

    if (!videoPreview.duration) return;

    trimmerState.videoDuration = videoPreview.duration;

    // Handle start drag
    trimmerStartHandle.addEventListener("mousedown", () => {
      trimmerState.isDraggingStart = true;
    });

    // Handle end drag
    trimmerEndHandle.addEventListener("mousedown", () => {
      trimmerState.isDraggingEnd = true;
    });

    // Handle timeline click
    trimmerContainer.addEventListener("click", (e) => {
      const rect = trimmerContainer.getBoundingClientRect();
      const clickPercent = ((e.clientX - rect.left) / rect.width) * 100;

      // Snap to nearest handle if close enough
      if (Math.abs(clickPercent - trimmerState.startPercent) < 5) {
        trimmerState.startPercent = Math.min(clickPercent, trimmerState.endPercent - 5);
      } else if (Math.abs(clickPercent - trimmerState.endPercent) < 5) {
        trimmerState.endPercent = Math.max(clickPercent, trimmerState.startPercent + 5);
      } else {
        // Otherwise move the closer handle
        if (clickPercent - trimmerState.startPercent < trimmerState.endPercent - clickPercent) {
          trimmerState.startPercent = Math.min(clickPercent, trimmerState.endPercent - 5);
        } else {
          trimmerState.endPercent = Math.max(clickPercent, trimmerState.startPercent + 5);
        }
      }
      updateTrimmerUI();
      // Sync video to clicked position
      const clickTime = (clickPercent / 100) * trimmerState.videoDuration;
      videoPreview.currentTime = clickTime;
    });

    // Handle mouse move for dragging
    document.addEventListener("mousemove", (e) => {
      const container = trimmerContainer;
      const rect = container.getBoundingClientRect();
      const movePercent = ((e.clientX - rect.left) / rect.width) * 100;

      if (trimmerState.isDraggingStart) {
        trimmerState.startPercent = Math.max(0, Math.min(movePercent, trimmerState.endPercent - 5));
        updateTrimmerUI();
        // Sync video to new start position
        const startTime = (trimmerState.startPercent / 100) * trimmerState.videoDuration;
        videoPreview.currentTime = startTime;
      } else if (trimmerState.isDraggingEnd) {
        trimmerState.endPercent = Math.min(100, Math.max(movePercent, trimmerState.startPercent + 5));
        updateTrimmerUI();
        // Sync video to end position
        const endTime = (trimmerState.endPercent / 100) * trimmerState.videoDuration;
        videoPreview.currentTime = endTime;
      }
    });

    // Handle mouse up
    document.addEventListener("mouseup", () => {
      trimmerState.isDraggingStart = false;
      trimmerState.isDraggingEnd = false;
    });

    // Update video playback with trim times
    videoPreview.addEventListener("play", () => {
      const startTime = (trimmerState.startPercent / 100) * trimmerState.videoDuration;
      videoPreview.currentTime = startTime;
    });

    // Update playhead indicator
    videoPreview.addEventListener("timeupdate", () => {
      const playPercent = (videoPreview.currentTime / trimmerState.videoDuration) * 100;
      const playheadIndicator = document.getElementById("playheadIndicator");
      playheadIndicator.style.left = playPercent + "%";
    });

    function updateTrimmerUI() {
      trimmerStartHandle.style.left = trimmerState.startPercent + "%";
      trimmerEndHandle.style.right = (100 - trimmerState.endPercent) + "%";
      trimmerSelection.style.left = trimmerState.startPercent + "%";
      trimmerSelection.style.width = (trimmerState.endPercent - trimmerState.startPercent) + "%";

      const startTime = (trimmerState.startPercent / 100) * trimmerState.videoDuration;
      const endTime = (trimmerState.endPercent / 100) * trimmerState.videoDuration;
      trimmerTimeDisplay.textContent = `${formatTime(startTime)} - ${formatTime(endTime)}`;

      // Store trim values in hidden inputs for form submission
      const startInput = document.getElementById("startTime");
      const endInput = document.getElementById("endTime");
      if (startInput) startInput.value = startTime.toFixed(1);
      if (endInput) endInput.value = endTime.toFixed(1);
    }

    function formatTime(seconds) {
      const mins = Math.floor(seconds / 60);
      const secs = Math.floor(seconds % 60);
      return `${mins}:${secs.toString().padStart(2, "0")}`;
    }

    // Initialize UI
    updateTrimmerUI();
  }

  // Video Preview Handler
  document.getElementById("videoInput")?.addEventListener("change", (event) => {
    const file = event.target.files[0];
    const videoPreview = document.getElementById("videoPreview");
    const videoPreviewSection = document.getElementById("videoPreviewSection");

    if (file) {
      const url = URL.createObjectURL(file);
      videoPreview.src = url;
      videoPreviewSection.style.display = "block";
      console.log("Video preview set up with src:", url);

      // Initialize trimmer when video metadata loads
      videoPreview.addEventListener("loadedmetadata", () => {
        console.log(`Video duration: ${videoPreview.duration.toFixed(1)}s`);
        initTrimmer();
      }, { once: true });
    } else {
      videoPreviewSection.style.display = "none";
    }
  });

  // Live Analysis WebSocket Handler
  function startLiveAnalysis(videoId, videoElement, exercise = 'squats', repCount = null, startTime = null, endTime = null) {
    const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:';
    let wsUrl = `${protocol}//${location.host}/ws/analyze-video/${videoId}?exercise=${exercise}`;

    // Add optional parameters to URL
    if (repCount) wsUrl += `&rep_count=${repCount}`;
    if (startTime) wsUrl += `&start_time=${startTime}`;
    if (endTime) wsUrl += `&end_time=${endTime}`;

    const ws = new WebSocket(wsUrl);

    console.log('Connecting to WebSocket:', wsUrl);

    ws.onopen = () => {
      console.log('WebSocket connected successfully');
    };

    ws.onmessage = (event) => {
      console.log('WebSocket message received:', event.data);
      const data = JSON.parse(event.data);

      if (data.type === 'analysis_progress') {
        console.log(`Analysis progress: ${data.progress_percent}%`);

      } else if (data.type === 'analysis_complete') {
        console.log('Analysis complete:', data);
        ws.close();

        // Show final analysis results
        const loadingContainer = document.querySelector('[data-analysis-results]');
        if (loadingContainer && data.feedback) {
          const exercise = data.exercise || 'exercise';
          const feedback = data.feedback || data.raw_response || "No feedback available";

          // Format feedback - convert text to HTML with proper styling
          const formattedFeedback = feedback
            .split('\n')
            .map(line => {
              if (line.startsWith('✓')) {
                return `<div style="color: #2ed573; margin: 8px 0; padding: 8px 12px; background: rgba(46, 213, 115, 0.1); border-left: 3px solid #2ed573; border-radius: 4px;">${line}</div>`;
              } else if (line.startsWith('⚠️') || line.startsWith('Warning')) {
                return `<div style="color: #ffc107; margin: 8px 0; padding: 8px 12px; background: rgba(255, 193, 7, 0.1); border-left: 3px solid #ffc107; border-radius: 4px;">${line}</div>`;
              } else if (line.startsWith('**') || line.includes('##')) {
                return `<h4 style="color: #6effe8; margin: 12px 0 8px 0; font-size: 14px;">${line.replace(/\*\*/g, '').replace(/#/g, '')}</h4>`;
              } else if (line.trim() !== '') {
                return `<div style="margin: 4px 0; line-height: 1.6; color: #a8b5d1; font-size: 13px;">${line}</div>`;
              }
              return '';
            })
            .join('');

          const analysisHTML = `
            <div style="background: linear-gradient(135deg, rgba(110, 255, 232, 0.1) 0%, rgba(110, 255, 232, 0.05) 100%); border: 1px solid rgba(110, 255, 232, 0.3); border-radius: 12px; padding: 24px;">
              <h3 style="margin: 0 0 20px 0; color: #f0f4ff; font-size: 18px;">✅ Analysis Complete</h3>
              
              <div style="background: rgba(110, 255, 232, 0.08); border: 1px solid rgba(110, 255, 232, 0.2); border-radius: 8px; padding: 16px; margin-bottom: 16px;">
                <div style="color: #6effe8; font-weight: 600; font-size: 14px; margin-bottom: 12px;">📋 ${exercise.charAt(0).toUpperCase() + exercise.slice(1)} Feedback</div>
                <div style="color: #a8b5d1;">
                  ${formattedFeedback}
                </div>
              </div>
              
              <div style="margin-top: 12px; padding: 12px; background: rgba(110, 255, 232, 0.05); border-radius: 6px; font-size: 11px; color: var(--muted);">
                <strong style="color: #6effe8;">Analyzed frames:</strong> ${data.num_frames_analyzed || 5} | <strong style="color: #6effe8;">Exercise:</strong> ${exercise.charAt(0).toUpperCase() + exercise.slice(1)}
              </div>
            </div>
          `;

          loadingContainer.innerHTML = analysisHTML;
        }
      } else if (data.type === 'error') {
        console.error('WebSocket error:', data.message);
        ws.close();

        // Show error and fallback
        const loadingContainer = document.querySelector('[data-analysis-results]');
        if (loadingContainer) {
          loadingContainer.innerHTML = `
            <div style="background: linear-gradient(135deg, rgba(255, 99, 71, 0.1) 0%, rgba(255, 99, 71, 0.05) 100%); border: 1px solid rgba(255, 99, 71, 0.3); border-radius: 12px; padding: 24px; text-align: center;">
              <p style="color: #ff6347; margin: 0 0 16px 0; font-size: 16px; font-weight: bold;">❌ Analysis Failed</p>
              <p style="color: #f0f4ff; margin: 0; font-size: 14px;">Error: ${data.message}</p>
            </div>
          `;
        }
      }
    };

    ws.onerror = (error) => {
      console.error('WebSocket connection error:', error);

      // Show connection error
      const loadingContainer = document.querySelector('[data-analysis-results]');
      if (loadingContainer) {
        loadingContainer.innerHTML = `
          <div style="background: linear-gradient(135deg, rgba(255, 99, 71, 0.1) 0%, rgba(255, 99, 71, 0.05) 100%); border: 1px solid rgba(255, 99, 71, 0.3); border-radius: 12px; padding: 24px; text-align: center;">
            <p style="color: #ff6347; margin: 0 0 16px 0; font-size: 16px; font-weight: bold;">❌ Connection Failed</p>
            <p style="color: #f0f4ff; margin: 0; font-size: 14px;">Could not connect to analysis server.</p>
          </div>
        `;
      }
    };

    ws.onclose = (event) => {
      console.log('WebSocket closed:', event.code, event.reason);
    };

    // Add timeout for WebSocket connection
    setTimeout(() => {
      if (ws.readyState === WebSocket.CONNECTING) {
        console.error('WebSocket connection timeout');
        ws.close();
      }
    }, 10000); // 10 second timeout

    return ws;
  }

  document.getElementById("analyzeVideoBtn")?.addEventListener("click", async () => {
    const videoInput = document.getElementById("videoInput");
    const exerciseSelect = document.getElementById("exerciseSelect");
    const videoResult = document.getElementById("videoResult");
    const downloadLink = document.getElementById("downloadLink");

    // Safety checks
    if (!videoInput || !exerciseSelect || !videoResult) {
      console.error("Required form elements not found");
      return;
    }

    // Check video file is selected
    if (!videoInput.files || !videoInput.files[0]) {
      showMessageModal("No Video", "Please select a video file to analyze.");
      return;
    }

    // Request consent for video analysis
    const consented = await openVideoConsentModal();
    if (!consented) {
      return;
    }

    // Hide the old elements
    if (videoResult) videoResult.style.display = "none";
    if (downloadLink) downloadLink.style.display = "none";

    if (!videoInput.files || videoInput.files.length === 0) {
      if (videoResult) {
        videoResult.style.display = "block";
        videoResult.textContent = "Pick a video first.";
      }
      return;
    }

    // Show loading state
    const existingContainer = document.querySelector('[data-analysis-results]');
    if (existingContainer) {
      existingContainer.remove();
    }

    const loadingContainer = document.createElement("div");
    loadingContainer.setAttribute('data-analysis-results', 'true');
    loadingContainer.style.marginTop = "20px";
    loadingContainer.innerHTML = `
      <div style="background: linear-gradient(135deg, rgba(110, 255, 232, 0.1) 0%, rgba(110, 255, 232, 0.05) 100%); border: 1px solid rgba(110, 255, 232, 0.3); border-radius: 12px; padding: 24px; text-align: center;">
        <div style="display: inline-block; width: 40px; height: 40px; border: 3px solid var(--muted); border-top-color: #6effe8; border-radius: 50%; animation: spin 0.8s linear infinite;"></div>
        <p style="color: #f0f4ff; margin: 16px 0 0 0; font-size: 14px;">Analyzing your video...</p>
      </div>
    `;
    videoResult.parentNode.insertBefore(loadingContainer, videoResult.nextSibling);
    videoResult.textContent = "";

    try {
      const form = new FormData();
      const startTimeEl = document.getElementById("startTime");
      const endTimeEl = document.getElementById("endTime");
      const repCountEl = document.getElementById("repCount");

      const startTime = startTimeEl?.value || "0";
      const endTime = endTimeEl?.value || "";
      const repCount = repCountEl?.value || "5";

      form.append("exercise", exerciseSelect.value);
      form.append("file", videoInput.files[0]);

      // Add optional trim parameters
      if (startTime && parseFloat(startTime) > 0) {
        form.append("start_time", startTime);
      }
      if (endTime && parseFloat(endTime) > 0) {
        form.append("end_time", endTime);
      }
      if (repCount && parseInt(repCount) > 0) {
        form.append("rep_count", repCount);
      }

      const res = await fetch(`/api/analyze-video`, { method: "POST", body: form });
      const data = await readJsonOrText(res);
      if (!res.ok) throw new Error(JSON.stringify(data, null, 2));

      // Start live analysis if we have video_id
      const videoPreview = document.getElementById("videoPreview");
      console.log("Live analysis check:", {
        video_id: data.video_id,
        videoPreview: !!videoPreview,
        videoPreviewSrc: videoPreview?.src,
        hasVideoSrc: !!videoPreview?.src
      });

      if (data.video_id && videoPreview && videoPreview.src) {
        console.log("Starting live analysis with video_id:", data.video_id);
        // Update loading message
        loadingContainer.innerHTML = `
          <div style="background: linear-gradient(135deg, rgba(110, 255, 232, 0.1) 0%, rgba(110, 255, 232, 0.05) 100%); border: 1px solid rgba(110, 255, 232, 0.3); border-radius: 12px; padding: 24px; text-align: center;">
            <p style="color: #6effe8; margin: 0 0 16px 0; font-size: 16px; font-weight: bold;">🎥 Analyzing Your Video Live</p>

          </div>
        `;

        // Start video playback
        videoPreview.currentTime = parseFloat(document.getElementById("startTime").value) || 0;
        videoPreview.play();

        // Start live analysis with all parameters
        const startTimeVal = document.getElementById("startTime").value;
        const endTimeVal = document.getElementById("endTime").value;
        const ws = startLiveAnalysis(data.video_id, videoPreview, exerciseSelect.value, repCount, startTimeVal, endTimeVal);

        // Store websocket for cleanup
        window.currentAnalysisWS = ws;

        // Don't show the static results immediately - wait for live analysis
        return;
      } else if (data.video_id) {
        console.log("Video ID available but no video preview, attempting live analysis anyway");
        // Try live analysis without video preview
        loadingContainer.innerHTML = `
          <div style="background: linear-gradient(135deg, rgba(110, 255, 232, 0.1) 0%, rgba(110, 255, 232, 0.05) 100%); border: 1px solid rgba(110, 255, 232, 0.3); border-radius: 12px; padding: 24px; text-align: center;">
            <p style="color: #6effe8; margin: 0 0 16px 0; font-size: 16px; font-weight: bold;">🎥 Analyzing Your Video Live</p>
            <p style="color: #f0f4ff; margin: 0; font-size: 14px;">Real-time rep counting in progress...</p>
            <div id="liveRepCounter" style="font-size: 32px; color: #6effe8; margin-top: 16px;">Reps: 0</div>
          </div>
        `;

        const ws = startLiveAnalysis(data.video_id, null, exerciseSelect.value);
        window.currentAnalysisWS = ws;
        return;
      }

      // Clear loading state and show results
      loadingContainer.remove();

      const resultsContainer = document.createElement("div");
      resultsContainer.setAttribute('data-analysis-results', 'true');
      resultsContainer.style.marginTop = "20px";

      const exercise = data.exercise || exerciseSelect.value;
      const feedback = data.feedback || data.raw_response || "No feedback available";

      // Format feedback - convert text to HTML with proper styling
      const formattedFeedback = feedback
        .split('\n')
        .map(line => {
          if (line.startsWith('✓')) {
            return `<div style="color: #2ed573; margin: 8px 0; padding: 8px 12px; background: rgba(46, 213, 115, 0.1); border-left: 3px solid #2ed573; border-radius: 4px;">${line}</div>`;
          } else if (line.startsWith('⚠️') || line.startsWith('Warning')) {
            return `<div style="color: #ffc107; margin: 8px 0; padding: 8px 12px; background: rgba(255, 193, 7, 0.1); border-left: 3px solid #ffc107; border-radius: 4px;">${line}</div>`;
          } else if (line.startsWith('**') || line.includes('##')) {
            return `<h4 style="color: #6effe8; margin: 12px 0 8px 0; font-size: 14px;">${line.replace(/\*\*/g, '').replace(/#/g, '')}</h4>`;
          } else if (line.trim() !== '') {
            return `<div style="margin: 4px 0; line-height: 1.6; color: #a8b5d1; font-size: 13px;">${line}</div>`;
          }
          return '';
        })
        .join('');

      const analysisHTML = `
        <div style="background: linear-gradient(135deg, rgba(110, 255, 232, 0.1) 0%, rgba(110, 255, 232, 0.05) 100%); border: 1px solid rgba(110, 255, 232, 0.3); border-radius: 12px; padding: 24px;">
          <h3 style="margin: 0 0 20px 0; color: #f0f4ff; font-size: 18px;">✅ Form Analysis Complete</h3>
          
          <div style="background: rgba(110, 255, 232, 0.08); border: 1px solid rgba(110, 255, 232, 0.2); border-radius: 8px; padding: 16px; margin-bottom: 16px;">
            <div style="color: #6effe8; font-weight: 600; font-size: 14px; margin-bottom: 12px;">📋 ${exercise.charAt(0).toUpperCase() + exercise.slice(1)} Feedback</div>
            <div style="color: #a8b5d1;">
              ${formattedFeedback}
            </div>
          </div>
          
          <div style="margin-top: 12px; padding: 12px; background: rgba(110, 255, 232, 0.05); border-radius: 6px; font-size: 11px; color: var(--muted);">
            <strong style="color: #6effe8;">Analyzed frames:</strong> ${data.num_frames_analyzed || 3} | <strong style="color: #6effe8;">Exercise:</strong> ${exercise.charAt(0).toUpperCase() + exercise.slice(1)}${data.detected_reps ? ` | <strong style="color: #6effe8;">Detected reps:</strong> ${data.detected_reps}` : ''}
          </div>
        </div>
      `;

      resultsContainer.innerHTML = analysisHTML;
      videoResult.parentNode.insertBefore(resultsContainer, videoResult.nextSibling);

    } catch (e) {
      console.error("Analyze video failed", e);
      // Remove loading state on error
      const loadingContainer = document.querySelector('[data-analysis-results]');
      if (loadingContainer) {
        loadingContainer.remove();
      }
      showMessageModal("Video analyze failed", e.message || "Unknown error");
    }
  });

  bootClerkUI();

  // Initialize page navigation after DOM is ready
  console.log("[INIT] Document ready state:", document.readyState);
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", () => {
      console.log("[INIT] DOMContentLoaded fired, calling setupPageNavigation");
      setupPageNavigation();
    });
  } else {
    console.log("[INIT] DOM already ready, calling setupPageNavigation immediately");
    setupPageNavigation();
  }
})();
