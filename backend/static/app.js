(() => {

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

            <button id="logoutBtn" class="btn" style="font-size: 12px; padding: 6px 12px; background: rgba(224,145,69,0.15); border: 1px solid #e09145; color: #e09145; box-shadow: none;">

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



      // Now that Clerk is loaded and user is authenticated, check for incomplete workouts

      console.log("[setupAuth] Authentication complete, checking for incomplete workouts");

      checkForIncompleteWorkout();

    } catch (e) {

      console.error("[setupAuth] Error:", e);

    }

  }



  setupAuth();



  // Check for incomplete workout sessions

  async function checkForIncompleteWorkout() {

    try {

      console.log("[checkForIncompleteWorkout] Fetching workout sessions...");



      // Get Bearer token from Clerk

      let token = null;

      try {

        token = await Clerk.session.getToken();

        console.log("[checkForIncompleteWorkout] Got Clerk token");

      } catch (e) {

        console.log("[checkForIncompleteWorkout] Could not get Clerk token:", e.message);

      }



      const headers = {};

      if (token) {

        headers["Authorization"] = `Bearer ${token}`;

      }



      const res = await fetch("/api/workout-sessions", { headers });

      const data = await readJsonOrText(res);



      console.log("[checkForIncompleteWorkout] Response:", data);



      if (!data.sessions || !Array.isArray(data.sessions)) {

        console.log("[checkForIncompleteWorkout] No sessions data");

        return;

      }



      console.log("[checkForIncompleteWorkout] Found sessions:", data.sessions.length);



      // Find the most recent incomplete session

      const incompleteSessions = data.sessions.filter(s => !s.completed_at);

      console.log("[checkForIncompleteWorkout] Incomplete sessions:", incompleteSessions.length);



      if (incompleteSessions.length === 0) {

        console.log("[checkForIncompleteWorkout] No incomplete workouts");

        return;

      }



      const latestIncomplete = incompleteSessions.sort((a, b) =>

        new Date(b.session_date) - new Date(a.session_date)

      )[0];



      // Store it globally for resume

      window.incompleteSessionId = latestIncomplete.id;

      window.incompleteSessionData = latestIncomplete;



      // Show resume banner with workout name

      const banner = document.getElementById("resumeWorkoutBanner");

      const workoutNameEl = document.getElementById("resumeWorkoutName");

      console.log("[checkForIncompleteWorkout] Banner element:", banner);



      if (banner) {

        // Update the workout name in the banner

        if (workoutNameEl) {

          workoutNameEl.textContent = latestIncomplete.workout_name || "Unfinished Workout";

        }

        banner.style.display = "flex";

        console.log("[checkForIncompleteWorkout] Banner shown ✅");

      }



      console.log("[checkForIncompleteWorkout] Found incomplete session:", latestIncomplete.id);

    } catch (e) {

      console.log("[checkForIncompleteWorkout] Error:", e.message);

    }

  }



  // Resume incomplete workout

  window.resumeWorkout = async function () {

    if (!window.incompleteSessionId) {

      alert("No incomplete workout found");

      return;

    }



    try {

      // Get Bearer token

      let token = null;

      try {

        token = await Clerk.session.getToken();

      } catch (e) {

        console.log("[resumeWorkout] Could not get Clerk token:", e.message);

      }



      const headers = {};

      if (token) {

        headers["Authorization"] = `Bearer ${token}`;

      }



      // Fetch the full session details with exercises

      const res = await fetch(`/api/workout-sessions/${window.incompleteSessionId}`, { headers });

      const data = await readJsonOrText(res);



      console.log("[resumeWorkout] Session data:", data);



      if (data.success && data.session) {

        const session = data.session;

        const exercises = data.exercises || [];



        // Show the execution modal with the incomplete session

        window.showWorkoutExecution(

          session.id,

          session.workout_name || "Resume Workout",

          exercises

        );



        // Hide the banner

        const banner = document.getElementById("resumeWorkoutBanner");

        if (banner) banner.style.display = "none";

      } else {

        throw new Error(data.error || "Failed to load workout");

      }

    } catch (e) {

      console.error("[resumeWorkout] Error:", e);

      alert("Error loading workout: " + e.message);

    }

  };



  // Test function to create an incomplete workout

  window.createTestIncompleteWorkout = async function () {

    try {

      // Get Bearer token

      let token = null;

      try {

        token = await Clerk.session.getToken();

      } catch (e) {

        console.log("[createTestIncompleteWorkout] Could not get Clerk token:", e.message);

      }



      const headers = {

        "Content-Type": "application/x-www-form-urlencoded"

      };

      if (token) {

        headers["Authorization"] = `Bearer ${token}`;

      }



      const res = await fetch("/api/workout-sessions", {

        method: "POST",

        headers,

        body: new URLSearchParams({

          workout_plan_id: 1,

          workout_plan_type: "ai",

          workout_name: "💪 Test Incomplete Workout",

          day_number: 1

        })

      });



      const data = await readJsonOrText(res);

      console.log("[createTestIncompleteWorkout] Response:", data);



      if (data.success) {

        alert("Test incomplete workout created! Reload the page to see the resume banner.");

      } else {

        alert("Error: " + (data.error || "Unknown error"));

      }

    } catch (e) {

      console.error("[createTestIncompleteWorkout] Error:", e);

      alert("Error creating test workout: " + e.message);

    }

  };



  // Abandon incomplete workout

  window.abandonWorkout = async function () {

    if (!window.incompleteSessionId) {

      alert("No incomplete workout to abandon");

      return;

    }



    if (!confirm("Are you sure you want to abandon this workout? This action cannot be undone.")) {

      return;

    }



    try {

      // Get Bearer token

      let token = null;

      try {

        token = await Clerk.session.getToken();

      } catch (e) {

        console.log("[abandonWorkout] Could not get Clerk token:", e.message);

      }



      const headers = {};

      if (token) {

        headers["Authorization"] = `Bearer ${token}`;

      }



      // Delete the workout session

      const res = await fetch(`/api/workout-sessions/${window.incompleteSessionId}`, {

        method: "DELETE",

        headers

      });



      const data = await readJsonOrText(res);

      console.log("[abandonWorkout] Response:", data);



      if (data.success || res.ok) {

        console.log("[abandonWorkout] Workout abandoned ✅");



        // Hide the banner

        const banner = document.getElementById("resumeWorkoutBanner");

        if (banner) banner.style.display = "none";



        window.incompleteSessionId = null;

        window.incompleteSessionData = null;



        showMessageModal("✅ Workout Abandoned", "The incomplete workout has been deleted.", true);

      } else {

        throw new Error(data.error || "Failed to abandon workout");

      }

    } catch (e) {

      console.error("[abandonWorkout] Error:", e);

      alert("Error abandoning workout: " + e.message);

    }

  };



  // Delete workout session from history

  window.deleteWorkoutSession = async function (sessionId) {

    if (!confirm("Are you sure you want to delete this workout? This action cannot be undone.")) {

      return;

    }



    try {

      // Get Bearer token

      let token = null;

      try {

        token = await Clerk.session.getToken();

      } catch (e) {

        console.log("[deleteWorkoutSession] Could not get Clerk token:", e.message);

      }



      const headers = {};

      if (token) {

        headers["Authorization"] = `Bearer ${token}`;

      }



      // Delete the workout session

      const res = await fetch(`/api/workout-sessions/${sessionId}`, {

        method: "DELETE",

        headers

      });



      const data = await readJsonOrText(res);

      console.log("[deleteWorkoutSession] Response:", data);



      if (data.success || res.ok) {

        console.log("[deleteWorkoutSession] Workout deleted ✅");



        // Refresh the history list

        loadWorkoutHistory();



        // Close the modal

        const messageOverlay = document.getElementById("messageOverlay");

        if (messageOverlay) messageOverlay.style.display = "none";



        showMessageModal("✅ Workout Deleted", "The workout has been removed from your history.", true);

      } else {

        throw new Error(data.error || "Failed to delete workout");

      }

    } catch (e) {

      console.error("[deleteWorkoutSession] Error:", e);

      alert("Error deleting workout: " + e.message);

    }

  };



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

            initCustomWorkout();

          }



          // Load history when switching to history tab

          if (targetPage === "history") {

            setTimeout(() => {

              loadProgressStats();

              loadWorkoutHistory();

            }, 100);

          }



          // Load video library when switching to library tab

          if (targetPage === "library") {

            setTimeout(() => {

              window.loadVideoLibrary();

              window.setupVideoLibraryModals();

            }, 100);

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

          <div style="display:flex; gap:6px;">

            <button class="btnSmall" id="add-item-${dayId}">+ Exercise</button>

            <button class="btnSmall" id="start-day-${dayId}" style="background: var(--accent); color: var(--bg);">▶ Start</button>

          </div>

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

      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">

        <div class="muted">

          <b>${escapeHtml(plan.name)}</b> • Focus: <b>${escapeHtml(plan.primary_focus || "")}</b>

        </div>

      </div>

      <div id="edit-days"></div>

    `;



    const wrap = document.getElementById("edit-days");

    wrap.innerHTML = (days || []).map(dayEditorHtml).join("");



    // Add start workout handlers for each day

    (days || []).forEach((d, idx) => {

      const dayId = d.day_id ?? d.id;

      const dayNum = idx + 1;

      const startBtn = document.getElementById(`start-day-${dayId}`);



      if (startBtn) {

        startBtn.onclick = async () => {

          try {

            // Extract type and ID from composite ID

            let workoutType = 'ai', workoutId = parseInt(savedId);

            if (savedId.startsWith('custom_')) {

              workoutType = 'custom';

              workoutId = parseInt(savedId.split('_')[1]);

            } else if (savedId.startsWith('ai_')) {

              workoutType = 'ai';

              workoutId = parseInt(savedId.split('_')[1]);

            } else if (savedId.startsWith('saved_')) {

              workoutType = 'saved';

              workoutId = parseInt(savedId.split('_')[1]);

            }



            const formData = new FormData();

            formData.append("workout_plan_id", workoutId);

            formData.append("workout_plan_type", workoutType);

            formData.append("workout_name", plan.name);

            formData.append("day_number", dayNum);



            const res = await authedFetch("/api/workout-sessions", {

              method: "POST",

              body: formData

            });



            const data = await res.json();

            if (data.success) {

              // Open workout execution modal with day-specific name

              const dayTitle = d.title ? `${plan.name} - ${d.title}` : `${plan.name} - Day ${dayNum}`;

              showWorkoutExecution(data.session_id, dayTitle, data.exercises);

              editorCard.style.display = "none";

            } else {

              alert("Failed to start workout: " + data.error);

            }

          } catch (e) {

            console.error("Error starting workout:", e);

            alert("Error starting workout");

          }

        };

      }

    });

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

        // Determine item_type from savedId prefix

        const item_type = savedId.startsWith('custom_') ? 'custom' : 'user';



        document.getElementById(`save-item-${itemId}`).onclick = async () => {

          try {

            const exercise_name = document.getElementById(`ex-${itemId}`).value;

            const sets = parseInt(document.getElementById(`sets-${itemId}`).value || "0", 10);

            const reps = document.getElementById(`reps-${itemId}`).value;

            const rest_seconds = parseInt(document.getElementById(`rest-${itemId}`).value || "0", 10);



            await api(`/api/edit/items/${itemId}`, {

              method: "PATCH",

              body: JSON.stringify({ exercise_name, sets, reps, rest_seconds, item_type }),

            });

            alert("Saved");

            await openPlan(savedId);

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



  // Initialize custom workout creation

  function initCustomWorkout() {

    const btn = document.getElementById("createCustomWorkoutBtn");

    const overlay = document.getElementById("customWorkoutOverlay");

    const closeBtn = document.getElementById("customWorkoutCloseBtn");

    const cancelBtn = document.getElementById("customWorkoutCancelBtn");

    const createBtn = document.getElementById("customWorkoutCreateBtn");

    const form = document.getElementById("customWorkoutForm");

    const addExerciseBtn = document.getElementById("addExerciseBtn");

    const exercisesContainer = document.getElementById("exercisesContainer");



    if (!btn) return;



    let exerciseCount = 0;



    function addExerciseRow() {

      exerciseCount++;

      const rowId = `exercise-${exerciseCount}`;

      const row = document.createElement("div");

      row.id = rowId;

      row.style.cssText = "display: grid; grid-template-columns: 1fr 1fr 1fr 1fr auto; gap: 8px; align-items: end; background: rgba(255,255,255,0.05); padding: 12px; border-radius: 6px; border: 1px solid var(--border);";

      row.innerHTML = `

        <div>

          <label style="font-size: 11px; color: var(--muted);">Exercise</label>

          <input type="text" class="exercise-name" placeholder="Bench Press" required style="width: 100%; padding: 8px; border-radius: 4px; border: 1px solid var(--border); background: var(--bg); color: var(--text); font-size: 12px;" />

        </div>

        <div>

          <label style="font-size: 11px; color: var(--muted);">Sets</label>

          <input type="number" class="exercise-sets" placeholder="3" value="3" min="1" max="10" required style="width: 100%; padding: 8px; border-radius: 4px; border: 1px solid var(--border); background: var(--bg); color: var(--text); font-size: 12px;" />

        </div>

        <div>

          <label style="font-size: 11px; color: var(--muted);">Reps</label>

          <input type="text" class="exercise-reps" placeholder="8-12" value="8-12" required style="width: 100%; padding: 8px; border-radius: 4px; border: 1px solid var(--border); background: var(--bg); color: var(--text); font-size: 12px;" />

        </div>

        <div>

          <label style="font-size: 11px; color: var(--muted);">Rest (sec)</label>

          <input type="number" class="exercise-rest" placeholder="60" value="60" min="15" max="300" required style="width: 100%; padding: 8px; border-radius: 4px; border: 1px solid var(--border); background: var(--bg); color: var(--text); font-size: 12px;" />

        </div>

        <button type="button" class="btnSmall btnGhost" style="padding: 6px 10px;" onclick="document.getElementById('${rowId}').remove();">✕</button>

      `;

      exercisesContainer.appendChild(row);

    }



    btn.onclick = () => {

      overlay.style.display = "flex";

      form.reset();

      exercisesContainer.innerHTML = "";

      exerciseCount = 0;

      addExerciseRow(); // Start with one empty exercise row

    };



    closeBtn.onclick = () => {

      overlay.style.display = "none";

    };



    cancelBtn.onclick = () => {

      overlay.style.display = "none";

    };



    addExerciseBtn.onclick = (e) => {

      e.preventDefault();

      addExerciseRow();

    };



    createBtn.onclick = async () => {

      const name = document.getElementById("customWorkoutName").value.trim();

      const description = document.getElementById("customWorkoutDesc").value.trim();



      if (!name) {

        alert("Please enter a workout name");

        return;

      }



      // Collect exercises

      const exercises = [];

      const exerciseRows = exercisesContainer.querySelectorAll("div[id^='exercise-']");



      if (exerciseRows.length === 0) {

        alert("Please add at least one exercise");

        return;

      }



      exerciseRows.forEach((row, idx) => {

        const exerciseName = row.querySelector(".exercise-name").value.trim();

        const sets = row.querySelector(".exercise-sets").value;

        const reps = row.querySelector(".exercise-reps").value.trim();

        const rest = row.querySelector(".exercise-rest").value;



        if (!exerciseName || !sets || !reps || !rest) {

          throw new Error("All exercise fields are required");

        }



        exercises.push({

          position: idx + 1,

          exercise_name: exerciseName,

          sets: parseInt(sets),

          reps: reps,

          rest_seconds: parseInt(rest)

        });

      });



      try {

        createBtn.disabled = true;

        createBtn.textContent = "Creating...";



        const formData = new FormData();

        formData.append("name", name);

        formData.append("description", description);

        formData.append("exercises", JSON.stringify(exercises));



        const res = await authedFetch("/api/custom-workouts", {

          method: "POST",

          body: formData

        });



        const data = await res.json();



        if (!res.ok || !data.success) {

          throw new Error(data.error || "Failed to create workout");

        }



        // Show success modal

        const successModal = document.getElementById("successModal");

        const successMessage = document.getElementById("successMessage");

        const successCloseBtn = document.getElementById("successCloseBtn");



        successMessage.textContent = `"${name}" with ${exercises.length} exercise${exercises.length !== 1 ? 's' : ''} is ready to use!`;

        successModal.style.display = "flex";



        successCloseBtn.onclick = () => {

          successModal.style.display = "none";

          overlay.style.display = "none";

          form.reset();

          exercisesContainer.innerHTML = "";

          exerciseCount = 0;

          refreshMyPlans();

        };



        // Auto-close after 5 seconds if user doesn't click

        setTimeout(() => {

          if (successModal.style.display !== "none") {

            successModal.style.display = "none";

            overlay.style.display = "none";

            form.reset();

            exercisesContainer.innerHTML = "";

            exerciseCount = 0;

            refreshMyPlans();

          }

        }, 5000);

      } catch (e) {

        console.error("Error creating custom workout:", e);

        alert("Failed to create workout: " + e.message);

      } finally {

        createBtn.disabled = false;

        createBtn.textContent = "Create Workout";

      }

    };



    // Close on escape

    overlay.onclick = (e) => {

      if (e.target === overlay) {

        overlay.style.display = "none";

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



  function showMessageModal(title, body, isHtml = false) {

    const overlay = document.getElementById("messageOverlay");

    const titleEl = document.getElementById("messageTitle");

    const bodyEl = document.getElementById("messageBody");

    const okBtn = document.getElementById("messageOkBtn");

    const closeBtn = document.getElementById("messageCloseBtn");



    if (titleEl) titleEl.textContent = title || "Notice";

    if (bodyEl) {

      if (isHtml) {

        bodyEl.innerHTML = body || "";

      } else {

        bodyEl.textContent = body || "";

      }

    }



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



      // Show progress with styled HTML

      imageResult.innerHTML = `

        <div style="text-align: center; padding: 24px;">

          <div style="font-size: 48px; margin-bottom: 16px; animation: spin 2s linear infinite;">⚡</div>

          <div style="font-size: 18px; font-weight: 600; margin-bottom: 8px;">Analyzing Your Physique</div>

          <div style="font-size: 13px; color: var(--muted); margin-bottom: 20px;">This may take a few moments</div>

          <div style="margin-top: 20px;">

            <div id="progressStep1" style="font-size: 14px; margin: 8px 0; color: var(--muted);">

              <span style="display: inline-block; width: 20px;">â³</span> Detecting pose...

            </div>

            <div id="progressStep2" style="font-size: 14px; margin: 8px 0; color: var(--muted);">

              <span style="display: inline-block; width: 20px;">⟳</span> Analyzing muscles...

            </div>

            <div id="progressStep3" style="font-size: 14px; margin: 8px 0; color: var(--muted);">

              <span style="display: inline-block; width: 20px;">⊙</span> Generating plan...

            </div>

          </div>

          <div style="width: 100%; height: 4px; background: rgba(255,255,255,0.1); border-radius: 2px; margin-top: 20px; overflow: hidden;">

            <div id="progressBar" style="height: 100%; width: 0%; background: linear-gradient(90deg, #e09145, #c77b3f); border-radius: 2px; transition: width 0.3s ease;"></div>

          </div>

        </div>

        <style>

          @keyframes spin {

            0% { transform: rotate(0deg); }

            100% { transform: rotate(360deg); }

          }

        </style>

      `;



      // Simulate progress updates

      let progressStep = 0;

      let progressPercent = 0;

      const progressInterval = setInterval(() => {

        progressPercent = Math.min(progressPercent + 15, 90);

        document.getElementById("progressBar").style.width = progressPercent + "%";



        progressStep++;

        if (progressStep === 1) {

          document.getElementById("progressStep1").innerHTML = '<span style="display: inline-block; width: 20px;">✓</span> <span style="color: var(--accent);">Pose detected</span>';

          document.getElementById("progressStep1").style.color = "var(--accent)";

        } else if (progressStep === 2) {

          document.getElementById("progressStep2").innerHTML = '<span style="display: inline-block; width: 20px;">✓</span> <span style="color: var(--accent);">Muscle analysis complete</span>';

          document.getElementById("progressStep2").style.color = "var(--accent)";

        }

      }, 2000);



      const res = await authedFetch(`/api/analyze-image-v2`, { method: "POST", body: form });

      clearInterval(progressInterval);



      const data = await readJsonOrText(res);

      if (!res.ok) throw new Error(JSON.stringify(data, null, 2));



      // Replace progress with results (no scrolling)

      imageResult.style.maxHeight = "none";

      imageResult.style.overflow = "visible";

      imageResult.style.minHeight = "auto";

      imageResult.innerHTML = `

        <div style="text-align: center; padding: 16px 12px;">

          <div style="text-align: center; margin-bottom: 12px;">

            <div style="font-size: 32px; margin-bottom: 6px;">✅</div>

            <h2 style="margin: 0; font-size: 18px; color: var(--accent);">Analysis Complete!</h2>

          </div>

          <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 12px;">

            <div style="padding: 12px; background: rgba(224, 145, 69, 0.08); border-radius: 6px; border-left: 3px solid #e09145;">

              <div style="font-size: 11px; color: var(--muted); margin-bottom: 3px;">BODY TYPE</div>

              <div style="font-size: 15px; font-weight: 600;">${data.body_type || 'Unknown'}</div>

            </div>

            <div style="padding: 12px; background: rgba(224, 145, 69, 0.08); border-radius: 6px; border-left: 3px solid #e09145;">

              <div style="font-size: 11px; color: var(--muted); margin-bottom: 3px;">PRIMARY FOCUS</div>

              <div style="font-size: 15px; font-weight: 600;">${data.primary_focus || 'Chest'}</div>

            </div>

            <div style="padding: 12px; background: rgba(224, 145, 69, 0.08); border-radius: 6px; border-left: 3px solid #e09145;">

              <div style="font-size: 11px; color: var(--muted); margin-bottom: 3px;">SECONDARY</div>

              <div style="font-size: 13px; font-weight: 600;">${(data.secondary_focuses || []).join(', ') || 'N/A'}</div>

            </div>

            <div style="padding: 12px; background: rgba(224, 145, 69, 0.08); border-radius: 6px; border-left: 3px solid #e09145;">

              <div style="font-size: 11px; color: var(--muted); margin-bottom: 3px;">PROGRAM</div>

              <div style="font-size: 15px; font-weight: 600;">8 weeks, ${data.difficulty}</div>

            </div>

          </div>

          <div style="padding: 12px; background: rgba(255,255,255,0.05); border-radius: 6px; font-size: 13px; line-height: 1.5; color: var(--muted);">

            <strong style="color: var(--text);">Why this plan?</strong> ${data.rationale || 'Tailored to your physique and goals.'}

          </div>

        </div>

      `;



      // Auto-scroll to results

      setTimeout(() => {

        window.scrollTo({ top: imageResult.offsetTop - 100, behavior: 'smooth' });

      }, 100);



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

                return `<h4 style="color: #e09145; margin: 12px 0 8px 0; font-size: 14px;">${line.replace(/\*\*/g, '').replace(/#/g, '')}</h4>`;

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

                <div style="color: #e09145; font-weight: 600; font-size: 14px; margin-bottom: 12px;">📋 ${exercise.charAt(0).toUpperCase() + exercise.slice(1)} Feedback</div>

                <div style="color: #a8b5d1;">

                  ${formattedFeedback}

                </div>

              </div>

              

              <div style="margin-top: 12px; padding: 12px; background: rgba(110, 255, 232, 0.05); border-radius: 6px; font-size: 11px; color: var(--muted);">

                <strong style="color: #e09145;">Analyzed frames:</strong> ${data.num_frames_analyzed || 5} | <strong style="color: #e09145;">Exercise:</strong> ${exercise.charAt(0).toUpperCase() + exercise.slice(1)}

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

              <p style="color: #ff6347; margin: 0 0 16px 0; font-size: 16px; font-weight: bold;">âŒ Analysis Failed</p>

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

            <p style="color: #ff6347; margin: 0 0 16px 0; font-size: 16px; font-weight: bold;">âŒ Connection Failed</p>

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



    // Show loading state - simple spinner in videoResult element

    videoResult.style.display = "block";

    videoResult.style.maxHeight = "none";

    videoResult.style.overflow = "visible";

    videoResult.style.minHeight = "auto";

    videoResult.innerHTML = `

      <div style="background: linear-gradient(135deg, rgba(110, 255, 232, 0.1) 0%, rgba(110, 255, 232, 0.05) 100%); border: 1px solid rgba(110, 255, 232, 0.3); border-radius: 12px; padding: 24px; text-align: center;">

        <div style="font-size: 48px; margin-bottom: 12px; animation: spin 2s linear infinite;">⚡</div>

        <p style="color: #f0f4ff; margin: 0; font-size: 14px; font-weight: 600;">Analyzing your video...</p>

        <p style="color: var(--muted); margin: 4px 0 0 0; font-size: 12px;">This may take a while</p>

      </div>

      <style>

        @keyframes spin {

          0% { transform: rotate(0deg); }

          100% { transform: rotate(360deg); }

        }

      </style>

    `;



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



      const res = await authedFetch(`/api/analyze-video`, { method: "POST", body: form });

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

        videoResult.innerHTML = `

          <div style="background: linear-gradient(135deg, rgba(110, 255, 232, 0.1) 0%, rgba(110, 255, 232, 0.05) 100%); border: 1px solid rgba(110, 255, 232, 0.3); border-radius: 12px; padding: 24px; text-align: center;">

            <p style="color: #e09145; margin: 0 0 16px 0; font-size: 16px; font-weight: bold;">🎥 Analyzing Your Video Live</p>



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

        videoResult.innerHTML = `

          <div style="background: linear-gradient(135deg, rgba(110, 255, 232, 0.1) 0%, rgba(110, 255, 232, 0.05) 100%); border: 1px solid rgba(110, 255, 232, 0.3); border-radius: 12px; padding: 24px; text-align: center;">

            <p style="color: #e09145; margin: 0 0 16px 0; font-size: 16px; font-weight: bold;">🎥 Analyzing Your Video Live</p>

            <p style="color: #f0f4ff; margin: 0; font-size: 14px;">Real-time rep counting in progress...</p>

            <div id="liveRepCounter" style="font-size: 32px; color: #e09145; margin-top: 16px;">Reps: 0</div>

          </div>

        `;



        const ws = startLiveAnalysis(data.video_id, null, exerciseSelect.value);

        window.currentAnalysisWS = ws;

        return;

      }



      // Replace loading state with results in videoResult

      const exercise = data.exercise || exerciseSelect.value;

      const feedback = data.feedback || data.raw_response || "No feedback available";



      // Format feedback - convert text to HTML with proper styling

      const formattedFeedback = feedback

        .split('\n')

        .map(line => {

          if (line.startsWith('✓')) {

            return `<div style="color: #2ed573; margin: 6px 0; padding: 8px 12px; background: rgba(46, 213, 115, 0.1); border-left: 2px solid #2ed573; border-radius: 3px; font-size: 14px;">${line}</div>`;

          } else if (line.startsWith('⚠️') || line.startsWith('Warning')) {

            return `<div style="color: #ffc107; margin: 6px 0; padding: 8px 12px; background: rgba(255, 193, 7, 0.1); border-left: 2px solid #ffc107; border-radius: 3px; font-size: 14px;">${line}</div>`;

          } else if (line.startsWith('**') || line.includes('##')) {

            return `<h4 style="color: #e09145; margin: 10px 0 6px 0; font-size: 13px; font-weight: 600;">${line.replace(/\*\*/g, '').replace(/#/g, '')}</h4>`;

          } else if (line.trim() !== '') {

            return `<div style="margin: 4px 0; line-height: 1.5; color: #a8b5d1; font-size: 14px;">${line}</div>`;

          }

          return '';

        })

        .join('');



      const analysisHTML = `

        <div style="background: linear-gradient(135deg, rgba(110, 255, 232, 0.1) 0%, rgba(110, 255, 232, 0.05) 100%); border: 1px solid rgba(110, 255, 232, 0.3); border-radius: 8px; padding: 16px;">

          <h3 style="margin: 0 0 12px 0; color: #f0f4ff; font-size: 16px;">✅ Analysis Complete</h3>

          

          <div style="background: rgba(110, 255, 232, 0.08); border: 1px solid rgba(110, 255, 232, 0.2); border-radius: 6px; padding: 12px; margin-bottom: 12px;">

            <div style="color: #e09145; font-weight: 600; font-size: 14px; margin-bottom: 8px;">📋 ${exercise.charAt(0).toUpperCase() + exercise.slice(1)} Feedback</div>

            <div style="color: #a8b5d1;">

              ${formattedFeedback}

            </div>

          </div>

          

          <div style="margin-top: 8px; padding: 10px; background: rgba(110, 255, 232, 0.05); border-radius: 4px; font-size: 12px; color: var(--muted);">

            <strong style="color: #e09145;">Frames:</strong> ${data.num_frames_analyzed || 3} | <strong style="color: #e09145;">Exercise:</strong> ${exercise.charAt(0).toUpperCase() + exercise.slice(1)}${data.detected_reps ? ` | <strong style="color: #e09145;">Reps:</strong> ${data.detected_reps}` : ''}

          </div>

        </div>

      `;



      // Set styles to show results without scrolling

      videoResult.style.maxHeight = "none";

      videoResult.style.overflow = "visible";

      videoResult.style.minHeight = "auto";

      videoResult.innerHTML = analysisHTML;



    } catch (e) {

      console.error("Analyze video failed", e);

      // Clear loading state on error

      videoResult.textContent = e.message || "Analysis failed";

      showMessageModal("Video analyze failed", e.message || "Unknown error");

    }

  });



  // ===========================

  // Workout Logging Functions

  // ===========================



  async function loadProgressStats() {

    try {

      const res = await api("/api/progress/stats");

      if (res.success) {

        document.getElementById("totalWorkouts").textContent = res.stats.total_workouts || "0";

        document.getElementById("totalMinutes").textContent = res.stats.total_minutes || "0";

        document.getElementById("avgRating").textContent = res.stats.average_rating ? res.stats.average_rating.toFixed(1) : "-";



        // Load top exercises

        const topExercisesEl = document.getElementById("topExercises");

        if (res.top_exercises && res.top_exercises.length > 0) {

          topExercisesEl.innerHTML = res.top_exercises.map((ex, i) => `

            <div style="background: var(--panel); padding: 12px; border-radius: 6px; border-left: 3px solid var(--accent);">

              <div style="font-weight: 500;">${escapeHtml(ex.exercise_name)}</div>

              <div style="font-size: 12px; color: var(--muted); margin-top: 4px;">

                ${ex.total_times_completed} times • ${ex.personal_record_weight ? ex.personal_record_weight + ' lbs PR' : 'No weight'}

              </div>

            </div>

          `).join("");

        }

      }

    } catch (e) {

      console.error("Error loading stats:", e);

    }

  }



  async function loadWorkoutHistory() {

    try {

      const res = await api("/api/workout-sessions");

      if (res.success && res.sessions) {

        const historyEl = document.getElementById("historyList");

        if (res.sessions.length === 0) {

          historyEl.innerHTML = '<div class="muted" style="text-align: center; padding: 20px;">No workouts logged yet. Start tracking your progress!</div>';

          return;

        }



        historyEl.innerHTML = res.sessions.map(session => `

          <div style="background: var(--panel); padding: 14px; border-radius: 10px; border: 1px solid var(--border); border-left: 4px solid ${session.completed_at ? 'var(--accent)' : '#7b7b7b'}; margin-bottom: 10px;">

            <div style="display: flex; justify-content: space-between; align-items: start; gap: 10px;">

              <div>

                <div style="font-weight: 600; font-size: 14px;">${escapeHtml(session.workout_name)} - Day ${session.day_number}</div>

                <div style="font-size: 12px; color: var(--muted); margin-top: 4px;">

                  📅 ${new Date(session.session_date).toLocaleDateString()} 

                  ${session.duration_minutes ? `• ⏱️ ${session.duration_minutes} min` : ''}

                  ${session.rating ? `• Rating ${session.rating}/5` : ''}
                  ${session.completed_at ? '• Completed' : '• In progress'}

                </div>

              </div>

              <div style="display: flex; gap: 6px;">

                <button class="btnSmall" onclick="viewSessionDetails(${session.id})">View</button>

                <button class="btnSmall" style="background: rgba(212,93,93,0.15); border-color: #d45d5d; color: #d45d5d;" onclick="deleteWorkoutSession(${session.id})">Delete</button>

              </div>

            </div>

          </div>

        `).join("");

      }

    } catch (e) {

      console.error("Error loading history:", e);

    }

  }



  window.viewSessionDetails = async function (sessionId) {

    try {

      const res = await api(`/api/workout-sessions/${sessionId}`);

      if (res.success) {

        const session = res.session;

        const exercises = res.exercises;



        const isCompleted = session.completed_at !== null;
        const statusLabel = isCompleted ? 'Completed' : 'In Progress';
        const detailsHTML = `
          <section class="workoutDetails">
            <header class="workoutDetailsHeader">
              <div>
                <p class="workoutDetailsTitle">${escapeHtml(session.workout_name)}</p>
                <p class="workoutDetailsSubtitle">Day ${session.day_number}</p>
              </div>
              <span class="workoutStatus ${isCompleted ? 'completed' : 'inprogress'}">${statusLabel}</span>
            </header>

            <div class="workoutStatsGrid">
              <article class="workoutStatCard">
                <p class="workoutStatLabel">Date</p>
                <p class="workoutStatValue">${new Date(session.session_date).toLocaleDateString()}</p>
              </article>
              ${session.duration_minutes ? `
                <article class="workoutStatCard">
                  <p class="workoutStatLabel">Duration</p>
                  <p class="workoutStatValue">${session.duration_minutes} min</p>
                </article>
              ` : ''}
              ${session.rating ? `
                <article class="workoutStatCard">
                  <p class="workoutStatLabel">Rating</p>
                  <p class="workoutStatValue">${session.rating}/5</p>
                </article>
              ` : ''}
            </div>

            ${session.notes ? `
              <article class="workoutNotesCard">
                <p class="workoutNotesLabel">Coach Notes</p>
                <p class="workoutNotesText">${escapeHtml(session.notes)}</p>
              </article>
            ` : ''}

            <section class="workoutExerciseSection">
              <p class="workoutExerciseHeading">Exercises (${exercises.length})</p>
              ${exercises.length === 0 ? `
                <div class="workoutEmptyState">No exercises logged yet.</div>
              ` : exercises.map((ex, idx) => {
          const isLogged = ex.completed_sets > 0;
          return `
                <article class="workoutExerciseCard ${isLogged ? 'logged' : 'pending'}">
                  <div class="workoutExerciseTop">
                    <p class="workoutExerciseName">${idx + 1}. ${escapeHtml(ex.exercise_name)}</p>
                    <span class="workoutExerciseState">${isLogged ? 'Logged' : 'Pending'}</span>
                  </div>

                  <div class="workoutExerciseMetrics">
                    <div>
                      <p class="workoutMetricLabel">Planned</p>
                      <p class="workoutMetricValue">${ex.planned_sets} x ${ex.planned_reps}</p>
                    </div>
                    <div>
                      <p class="workoutMetricLabel">Completed</p>
                      <p class="workoutMetricValue ${isLogged ? 'ok' : 'muted'}">${isLogged ? `${ex.completed_sets} x ${ex.completed_reps || ''}` : 'Not logged'}</p>
                    </div>
                    ${ex.weight_used ? `
                      <div>
                        <p class="workoutMetricLabel">Weight</p>
                        <p class="workoutMetricValue">${ex.weight_used} lbs</p>
                      </div>
                    ` : ''}
                    ${ex.rpe ? `
                      <div>
                        <p class="workoutMetricLabel">RPE</p>
                        <p class="workoutMetricValue">${ex.rpe}/10</p>
                      </div>
                    ` : ''}
                  </div>
                </article>
              `;
        }).join('')}
            </section>
          </section>
        `;



        showMessageModal("Workout Details", detailsHTML, true);



        // Add delete button to the modal

        const deleteBtn = document.createElement("button");

        deleteBtn.textContent = "Delete Workout";
        deleteBtn.className = "btn workoutDeleteBtn";

        deleteBtn.onclick = () => {

          deleteWorkoutSession(sessionId);

          document.getElementById("messageOverlay").style.display = "none";

        };



        const bodyEl = document.getElementById("messageBody");

        if (bodyEl) {

          bodyEl.appendChild(deleteBtn);

        }

      }

    } catch (e) {

      console.error("Error loading session:", e);

      alert("Error loading session details");

    }

  };



  bootClerkUI();



  // Initialize page navigation after DOM is ready

  console.log("[INIT] Document ready state:", document.readyState);

  if (document.readyState === "loading") {

    document.addEventListener("DOMContentLoaded", () => {

      console.log("[INIT] DOMContentLoaded fired, calling setupPageNavigation");

      setupPageNavigation();

    });

  }



  // ===========================

  // Workout Execution

  // ===========================



  window.showWorkoutExecution = function (sessionId, workoutName, exercises) {

    const modal = document.getElementById("workoutExecutionModal");

    const title = document.getElementById("workoutTitle");

    const container = document.getElementById("workoutExercisesContainer");

    const durationInput = document.getElementById("workoutDuration");

    const ratingSelect = document.getElementById("workoutRating");

    const completeBtn = document.getElementById("completeWorkoutBtn");

    const closeBtn = document.getElementById("workoutCloseBtn");



    title.textContent = workoutName;

    durationInput.value = "";

    ratingSelect.value = "";



    // Render exercises

    container.innerHTML = exercises.map((ex, idx) => `

      <div style="background: var(--panel); padding: 16px; border-radius: 8px; border-left: 3px solid var(--border);">

        <div style="font-weight: 600; margin-bottom: 12px; font-size: 14px;">${idx + 1}. ${escapeHtml(ex.exercise_name)}</div>

        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 12px; font-size: 13px;">

          <div>

            <label style="color: var(--muted); display: block; margin-bottom: 4px;">Sets</label>

            <input type="number" class="completed-sets" data-ex-id="${ex.id}" min="0" max="20" placeholder="${ex.planned_sets}" value="${ex.completed_sets || ''}" style="width: 100%; padding: 6px; border: 1px solid var(--border); background: var(--bg); color: var(--text); border-radius: 4px;">

          </div>

          <div>

            <label style="color: var(--muted); display: block; margin-bottom: 4px;">Reps</label>

            <input type="text" class="completed-reps" data-ex-id="${ex.id}" placeholder="${escapeHtml(ex.planned_reps)}" value="${ex.completed_reps || ''}" style="width: 100%; padding: 6px; border: 1px solid var(--border); background: var(--bg); color: var(--text); border-radius: 4px;">

          </div>

        </div>

        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px; font-size: 13px;">

          <div>

            <label style="color: var(--muted); display: block; margin-bottom: 4px;">Weight (lbs)</label>

            <input type="number" class="weight-used" data-ex-id="${ex.id}" min="0" step="0.5" placeholder="0" value="${ex.weight_used || ''}" style="width: 100%; padding: 6px; border: 1px solid var(--border); background: var(--bg); color: var(--text); border-radius: 4px;">

          </div>

          <div>

            <label style="color: var(--muted); display: block; margin-bottom: 4px;">RPE (1-10)</label>

            <input type="number" class="rpe" data-ex-id="${ex.id}" min="1" max="10" placeholder="6" value="${ex.rpe || ''}" style="width: 100%; padding: 6px; border: 1px solid var(--border); background: var(--bg); color: var(--text); border-radius: 4px;">

          </div>

        </div>

      </div>

    `).join("");



    modal.style.display = "block";



    // Close button

    closeBtn.onclick = () => {

      modal.style.display = "none";

    };



    // Add abandon button next to close button

    let abandonBtn = document.getElementById("abandonWorkoutExecBtn");

    if (!abandonBtn) {

      abandonBtn = document.createElement("button");

      abandonBtn.id = "abandonWorkoutExecBtn";

      abandonBtn.style.cssText = "padding: 8px 16px; background: rgba(212,93,93,0.15); border: 1px solid #d45d5d; color: #d45d5d; border-radius: 4px; cursor: pointer; font-size: 13px; margin-left: 8px;";

      abandonBtn.textContent = "🗑️ Abandon";

      closeBtn.parentNode.appendChild(abandonBtn);

    }



    abandonBtn.onclick = async () => {

      if (!confirm("Abandon this workout? Any unsaved data will be lost.")) return;



      try {

        let token = null;

        try {

          token = await Clerk.session.getToken();

        } catch (e) {

          console.log("[abandon] Could not get Clerk token");

        }



        const headers = {};

        if (token) headers["Authorization"] = `Bearer ${token}`;



        const res = await fetch(`/api/workout-sessions/${sessionId}`, {

          method: "DELETE",

          headers

        });



        const data = await readJsonOrText(res);

        if (data.success || res.ok) {

          modal.style.display = "none";

          checkForIncompleteWorkout();

          showMessageModal("✅ Workout Abandoned", "The workout has been deleted.", true);

        }

      } catch (e) {

        alert("Error: " + e.message);

      }

    };



    // Complete workout

    completeBtn.onclick = async () => {

      try {

        completeBtn.disabled = true;

        completeBtn.textContent = "Saving...";



        // Log all exercises first

        const sets = container.querySelectorAll(".completed-sets");

        for (let setInput of sets) {

          const exId = setInput.getAttribute("data-ex-id");

          const repsInput = container.querySelector(`.completed-reps[data-ex-id="${exId}"]`);

          const weightInput = container.querySelector(`.weight-used[data-ex-id="${exId}"]`);

          const rpeInput = container.querySelector(`.rpe[data-ex-id="${exId}"]`);



          const completedSets = parseInt(setInput.value) || 0;

          if (completedSets > 0) {

            const formData = new FormData();

            formData.append("completed_sets", completedSets);

            formData.append("completed_reps", repsInput.value || "");

            formData.append("weight_used", parseFloat(weightInput.value) || null);

            formData.append("rpe", parseInt(rpeInput.value) || null);



            await authedFetch(`/api/workout-sessions/${sessionId}/exercises/${exId}/log`, {

              method: "POST",

              body: formData

            });

          }

        }



        // Complete the workout

        const duration = parseInt(durationInput.value) || 0;

        const rating = parseInt(ratingSelect.value) || null;



        const completeForm = new FormData();

        completeForm.append("duration_minutes", duration);

        completeForm.append("rating", rating);

        completeForm.append("notes", "");



        const completeRes = await authedFetch(`/api/workout-sessions/${sessionId}/complete`, {

          method: "POST",

          body: completeForm

        });



        const completeData = await completeRes.json();

        if (completeData.success) {

          modal.style.display = "none";

          alert("✅ Workout completed! Your progress has been saved.");

          loadWorkoutHistory();

          loadProgressStats();

        }

      } catch (e) {

        console.error("Error completing workout:", e);

        alert("Error saving workout: " + e.message);

      } finally {

        completeBtn.disabled = false;

        completeBtn.textContent = "✓ Finish";

      }

    };

  };



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



  // VIDEO LIBRARY FUNCTIONS

  window.loadVideoLibrary = async function () {

    console.log("[VIDEO LIBRARY] Loading exercises...");

    try {

      const res = await fetch("/api/exercises");

      const data = await res.json();

      const exercises = data.exercises || [];



      // Load muscle groups

      const muscleRes = await fetch("/api/exercises/muscle-groups");

      const muscleData = await muscleRes.json();

      const muscleGroups = muscleData.muscle_groups || [];



      // Populate muscle group filter

      const filterContainer = document.getElementById("muscleGroupFilter");

      filterContainer.innerHTML = '<button class="btn" data-muscle="All" onclick="window.filterByMuscleGroup(\'All\')" style="padding: 8px 16px; font-size: 13px;">All Exercises</button>';



      muscleGroups.forEach(group => {

        const btn = document.createElement("button");

        btn.className = "btn";

        btn.setAttribute("data-muscle", group);

        btn.textContent = group;

        btn.style.cssText = "padding: 8px 16px; font-size: 13px;";

        btn.onclick = () => window.filterByMuscleGroup(group);

        filterContainer.appendChild(btn);

      });



      // Display exercises

      window.displayExercises(exercises);

    } catch (e) {

      console.error("Error loading video library:", e);

      document.getElementById("exerciseList").innerHTML = '<div style="text-align: center; padding: 40px; color: var(--muted); grid-column: 1 / -1;">Error loading exercises. Please refresh.</div>';

    }

  };



  window.displayExercises = function (exercises) {

    const container = document.getElementById("exerciseList");

    if (!exercises || exercises.length === 0) {

      container.innerHTML = '<div style="text-align: center; padding: 40px; color: var(--muted); grid-column: 1 / -1;">No exercises found</div>';

      return;

    }



    container.innerHTML = exercises.map(ex => `

      <div style="background: var(--panel); border: 1px solid var(--border); border-radius: 8px; padding: 16px; cursor: pointer; transition: all 0.2s;" 

        onmouseover="this.style.borderColor='var(--accent)'" 

        onmouseout="this.style.borderColor='var(--border)'" 

        onclick="window.viewExerciseDetails(${ex.id})">

        <div style="font-size: 28px; margin-bottom: 8px;">🏋️</div>

        <h3 style="margin: 0 0 4px 0; color: var(--text);">${escapeHtml(ex.name)}</h3>

        <p style="margin: 0 0 8px 0; font-size: 12px; color: var(--muted);">${escapeHtml(ex.muscle_group)}</p>

        <p style="margin: 0 0 12px 0; font-size: 12px; color: var(--text); line-height: 1.4;">${ex.description ? escapeHtml(ex.description.substring(0, 80)) + '...' : 'No description'}</p>

        <div style="display: flex; justify-content: space-between; align-items: center;">

          <span style="font-size: 12px; color: var(--accent);">${ex.video_count || 0} videos</span>

          <span style="font-size: 12px; background: var(--bg); padding: 4px 8px; border-radius: 4px; color: var(--muted);">${ex.difficulty}</span>

        </div>

      </div>

    `).join("");

  };



  window.viewExerciseDetails = async function (exerciseId) {

    console.log("[VIDEO LIBRARY] Viewing exercise:", exerciseId);

    try {

      const res = await fetch(`/api/exercises/${exerciseId}`);

      const exercise = await res.json();



      const modal = document.getElementById("exerciseVideoModal");

      document.getElementById("videoExerciseName").textContent = exercise.name;

      document.getElementById("videoExerciseMuscle").textContent = exercise.muscle_group || "General";

      document.getElementById("videoExerciseDescription").textContent = exercise.description || "No description available";



      const videosContainer = document.getElementById("videosContainer");

      if (!exercise.videos || exercise.videos.length === 0) {

        videosContainer.innerHTML = '<div style="text-align: center; padding: 40px; color: var(--muted);">No videos available for this exercise</div>';

      } else {

        videosContainer.innerHTML = exercise.videos.map((video, idx) => `

          <div style="border: 1px solid var(--border); border-radius: 8px; overflow: hidden;">

            <div style="position: relative; background: black; aspect-ratio: 16/9; overflow: hidden;">

              <iframe width="100%" height="100%" src="${escapeHtml(video.video_url)}" 

                frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" 

                allowfullscreen style="border: none;"></iframe>

            </div>

            <div style="padding: 16px;">

              <h3 style="margin: 0 0 8px 0; color: var(--text);">${escapeHtml(video.title)}</h3>

              <p style="margin: 0 0 12px 0; font-size: 13px; color: var(--muted); line-height: 1.5;">${escapeHtml(video.description || '')}</p>



              <div style="background: var(--bg); padding: 12px; border-radius: 6px; margin-bottom: 12px;">

                <p style="margin: 0 0 8px 0; font-size: 12px; font-weight: bold; color: var(--accent);">💡 Form Tips:</p>

                <p style="margin: 0; font-size: 12px; color: var(--text); line-height: 1.5; white-space: pre-wrap;">${escapeHtml(video.form_tips || 'No tips available')}</p>

              </div>



              <div style="background: var(--bg); padding: 12px; border-radius: 6px;">

                <p style="margin: 0 0 8px 0; font-size: 12px; font-weight: bold; color: #d45d5d;">âŒ Common Mistakes:</p>

                <p style="margin: 0; font-size: 12px; color: var(--text); line-height: 1.5; white-space: pre-wrap;">${escapeHtml(video.common_mistakes || 'None listed')}</p>

              </div>



              <div style="display: flex; gap: 8px; margin-top: 12px; font-size: 11px; color: var(--muted);">

                <span>⏱️ ${video.duration_seconds ? Math.round(video.duration_seconds / 60) + ' min' : 'N/A'}</span>

                <span>👁️ ${video.views || 0} views</span>

                <span>📊 ${video.difficulty_level}</span>

              </div>

            </div>

          </div>

        `).join("");

      }



      modal.style.display = "block";

    } catch (e) {

      console.error("Error fetching exercise details:", e);

      alert("Error loading exercise details: " + e.message);

    }

  };



  window.filterByMuscleGroup = async function (muscleGroup) {

    console.log("[VIDEO LIBRARY] Filtering by muscle group:", muscleGroup);

    try {

      let res;

      if (muscleGroup === "All") {

        res = await fetch("/api/exercises");

      } else {

        res = await fetch(`/api/exercises/by-muscle-group/${encodeURIComponent(muscleGroup)}`);

      }

      const data = await res.json();

      const exercises = data.exercises || [];

      window.displayExercises(exercises);

    } catch (e) {

      console.error("Error filtering exercises:", e);

      alert("Error filtering exercises: " + e.message);

    }

  };



  window.searchExercises = async function () {

    const query = document.getElementById("exerciseSearch").value.trim();

    if (query.length < 2) {

      alert("Please enter at least 2 characters to search");

      return;

    }



    console.log("[VIDEO LIBRARY] Searching for:", query);

    try {

      const res = await fetch(`/api/exercises/videos/search?q=${encodeURIComponent(query)}`);

      const data = await res.json();

      const exercises = data.exercises || [];

      window.displayExercises(exercises);

    } catch (e) {

      console.error("Error searching exercises:", e);

      alert("Error searching exercises: " + e.message);

    }

  };



  // Setup modal close handlers for video library

  window.setupVideoLibraryModals = function () {

    const videoModal = document.getElementById("exerciseVideoModal");

    const closeBtn = document.getElementById("videoModalCloseBtn");

    if (closeBtn) {

      closeBtn.onclick = () => { videoModal.style.display = "none"; };

    }

    if (videoModal) {

      videoModal.onclick = (e) => {

        if (e.target === videoModal) videoModal.style.display = "none";

      };

    }

  };



  // ADMIN PANEL FUNCTIONS

})();

