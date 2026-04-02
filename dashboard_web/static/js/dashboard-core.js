
    let cy = null;
    let autoRefresh = true;
    let timerId = null;
    const initialGraph = null;
    const initialBackendStatus = null;
    const initialLiveOverview = null;

    const agentFilter = document.getElementById('agentFilter');
    const targetFilter = document.getElementById('targetFilter');
    const autoBtn = document.getElementById('autoBtn');
    const tutorMode = document.getElementById('tutorMode');
    const defenseList = document.getElementById('defenseList');
    const agentDefenseGrid = document.getElementById('agentDefenseGrid');
    const scenarioList = document.getElementById('scenarioList');
    const pathList = document.getElementById('pathList');
    const attackFocus = document.getElementById('attackFocus');
    const adversaryModel = document.getElementById('adversaryModel');
    const defenseLog = document.getElementById('defenseLog');
    const defenseInput = document.getElementById('defenseInput');
    const chatLog = document.getElementById('chatLog');
    const chatInput = document.getElementById('chatInput');
    const graphLayout = document.getElementById('graphLayout');
    const graphFitBtn = document.getElementById('graphFitBtn');
    const graphCenterBtn = document.getElementById('graphCenterBtn');
    const graphClearBtn = document.getElementById('graphClearBtn');
    const graphStateTabs = document.getElementById('graphStateTabs');
    const graphMeta = document.getElementById('graphMeta');
    const graphNodeCount = document.getElementById('graphNodeCount');
    const graphEdgeCount = document.getElementById('graphEdgeCount');
    const graphPathCount = document.getElementById('graphPathCount');
    const graphInspector = document.getElementById('graphInspector');
    const agentLiveList = document.getElementById('agentLiveList');
    const operationList = document.getElementById('operationList');
    const liveAgentTotal = document.getElementById('liveAgentTotal');
    const liveAgentAlive = document.getElementById('liveAgentAlive');
    const liveAgentDead = document.getElementById('liveAgentDead');
    const liveAgentUntrusted = document.getElementById('liveAgentUntrusted');
    const liveOperationTotal = document.getElementById('liveOperationTotal');
    const liveOperationRunning = document.getElementById('liveOperationRunning');
    const mappedAttackers = document.getElementById('mappedAttackers');
    const mapScopeLabel = document.getElementById('mapScopeLabel');
    const mapEmpty = document.getElementById('mapEmpty');
    const mapList = document.getElementById('mapList');
    const locateBtn = document.getElementById('locateBtn');
    const clearLocationBtn = document.getElementById('clearLocationBtn');
    const saveLocationBtn = document.getElementById('saveLocationBtn');
    const locationQueryInput = document.getElementById('locationQueryInput');
    const analystLocationNote = document.getElementById('analystLocationNote');
    const agentViewSummary = document.getElementById('agentViewSummary');
    const graphPathCountRibbon = document.getElementById('graphPathCountRibbon');
    const pathRibbonList = document.getElementById('pathRibbonList');
    let latestScenarioFocuses = [];
    let latestPathFocuses = [];
    let latestRecommendations = [];
    let latestAgentProfiles = [];
    let latestGraphData = initialGraph || {};
    let latestLiveOverview = initialLiveOverview || {};
    let agentViewMode = 'all';
    let graphAgentStateMode = (initialGraph && initialGraph.meta && initialGraph.meta.agent_state_filter) || 'all';
    let selectedFocus = null;
    let selectedRecommendation = '';
    let selectedAgentProfile = null;
    let graphSelectionId = '';
    let graphHoverActive = false;
    let threatMap = null;
    let threatMarkers = [];
    let analystMarker = null;
    let analystAccuracyCircle = null;


    function renderBackendStatus(status) {
      const panel = document.getElementById('backendPanel');
      const connected = !!status.connected;
      panel.classList.toggle('ok', connected);
      panel.classList.toggle('bad', !connected);
      document.getElementById('backendState').textContent = connected ? 'CONNECTED' : 'NOT CONNECTED';
      document.getElementById('backendUrl').textContent = status.url || 'Not configured';
      document.getElementById('backendOps').textContent = status.operations || 0;
      document.getElementById('backendAgents').textContent = status.agents || 0;
      document.getElementById('backendNeo4j').textContent = status.neo4j_agents || 0;
      document.getElementById('backendAbilities').textContent = status.abilities || 0;
      document.getElementById('backendConfig').textContent = status.configured ? 'YES' : 'NO';
      const errorEl = document.getElementById('backendError');
      if (status.error) {
        errorEl.style.display = 'block';
        errorEl.textContent = status.error;
      } else {
        errorEl.style.display = 'none';
        errorEl.textContent = '';
      }
      
      // Sync warning visibility
      const syncWarning = document.getElementById('syncWarning');
      if (syncWarning) {
        if (status.neo4j_agents !== status.agents) {
          syncWarning.style.display = 'block';
          syncWarning.textContent = `SYNC ISSUE: Neo4j ${status.neo4j_agents || 0} agents vs Caldera ${status.agents || 0}`;
        } else {
          syncWarning.style.display = 'none';
        }
      }
    }
    
    async function checkSyncStatus() {
      try {
        const res = await fetch('/api/sync_status');
        const data = await res.json();
        const statusEl = document.getElementById('syncStatus');
        if (data.sync_healthy) {
          statusEl.innerHTML = '<span style="color:#84f6b6;">✅ Sync healthy</span>';
        } else {
          statusEl.innerHTML = `
            <span style="color:#ff8a8a;">⚠️ ${data.diagnosis}</span><br>
            Caldera: ${data.caldera_agents} | Neo4j: ${data.neo4j_agents} (Active:${data.active_neo4j} Stale:${data.stale_neo4j})
            ${data.needs_cleanup ? '<button onclick="cleanupNeo4j()" style="margin-left:8px;padding:3px 6px;font-size:9px;">Clean Now</button>' : ''}
          `;
        }
      } catch (err) {
        document.getElementById('syncStatus').textContent = 'Sync check failed';
      }
    }
    
    async function cleanupNeo4j() {
      if (!confirm('Clean Neo4j of stale agents/facts? This removes inactive Agent nodes.')) return;
      try {
        const res = await fetch('/api/clean_neo4j', {method: 'POST'});
        const data = await res.json();
        if (data.success) {
          alert('Neo4j cleaned successfully!');
          fetchAndRender(); // Refresh dashboard
        } else {
          alert('Cleanup failed: ' + data.error);
        }
      } catch (err) {
        alert('Cleanup request failed');
      }
    }

    function setAgentViewMode(mode) {
      agentViewMode = ['all', 'alive', 'dead'].includes(mode) ? mode : 'all';
      document.querySelectorAll('[data-agent-view]').forEach((button) => {
        button.classList.toggle('active', button.dataset.agentView === agentViewMode);
      });
      renderLiveOverview(latestLiveOverview || {});
    }

    function setGraphAgentStateMode(mode, shouldRefresh = true) {
      graphAgentStateMode = ['all', 'alive', 'dead'].includes(mode) ? mode : 'all';
      document.querySelectorAll('[data-graph-agent-view]').forEach((button) => {
        button.classList.toggle('active', button.dataset.graphAgentView === graphAgentStateMode);
      });
      if (shouldRefresh) {
        fetchAndRender();
      }
    }

    function filterVisibleAgents(agents) {
      if (agentViewMode === 'alive') {
        return (agents || []).filter((agent) => ['alive', 'pending kill'].includes(String(agent.status || '').toLowerCase()));
      }
      if (agentViewMode === 'dead') {
        return (agents || []).filter((agent) => String(agent.status || '').toLowerCase() === 'dead');
      }
      return agents || [];
    }

    function sourceLabel(source) {
      if (source === 'host_public_ip') return 'Host public egress location (approximate)';
      if (source === 'analyst_console') return 'Analyst console location';
      if (source === 'place_search') return 'Saved analyst place';
      if (source === 'browser') return 'Device location';
      return 'Agent public IP';
    }

    function renderAnalystLocationNote(location) {
      if (!analystLocationNote) return;
      if (!location || typeof location.latitude !== 'number' || typeof location.longitude !== 'number') {
        analystLocationNote.textContent = 'Analyst location override is not set yet. Use your device location or set a place name to pin local WSL agents more accurately.';
        return;
      }
      const accuracyText = location.accuracy ? `Accuracy ${Math.round(location.accuracy)}m` : 'Manual or place-based pin';
      const approxText = location.approximate ? 'Approximate' : 'Pinned';
      analystLocationNote.textContent = `${approxText} analyst location: ${location.label || 'Analyst console'} (${location.latitude.toFixed(4)}, ${location.longitude.toFixed(4)}) • ${sourceLabel(location.source)} • ${accuracyText}`;
    }

    async function saveAnalystLocation(payload) {
      const res = await fetch('/api/analyst_location', {
        method: 'POST',
        credentials: 'same-origin',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload || {})
      });
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.error || 'Unable to save location');
      }
      await fetchLiveOverview();
      return data.location || null;
    }

    async function clearAnalystLocation() {
      const res = await fetch('/api/analyst_location', {
        method: 'DELETE',
        credentials: 'same-origin'
      });
      if (!res.ok) {
        throw new Error('Unable to clear analyst location');
      }
      locationQueryInput.value = '';
      await fetchLiveOverview();
    }

    function requestDeviceLocation() {
      if (!navigator.geolocation) {
        analystLocationNote.textContent = 'This browser cannot provide device geolocation. Use the place search field instead.';
        return;
      }
      analystLocationNote.textContent = 'Requesting device location permission...';
      navigator.geolocation.getCurrentPosition(async (position) => {
        try {
          await saveAnalystLocation({
            latitude: position.coords.latitude,
            longitude: position.coords.longitude,
            accuracy: position.coords.accuracy,
            label: 'Analyst device location',
            source: 'browser'
          });
        } catch (error) {
          analystLocationNote.textContent = error.message || 'Unable to save device location.';
        }
      }, (error) => {
        analystLocationNote.textContent = error && error.message
          ? `Device location blocked: ${error.message}. Use the place search field instead.`
          : 'Device location blocked. Use the place search field instead.';
      }, { enableHighAccuracy: true, timeout: 12000, maximumAge: 300000 });
    }

    function statusBadgeClass(status) {
      const normalized = String(status || '').toLowerCase();
      if (normalized === 'alive') return 'alive';
      if (normalized === 'pending kill') return 'pending';
      if (normalized === 'dead') return 'dead';
      return '';
    }

    function operationBadgeClass(state) {
      const normalized = String(state || '').toLowerCase();
      return ['finished', 'cleanup', 'out_of_time', 'closed', 'archived'].includes(normalized)
        ? 'operation-finished'
        : 'operation-running';
    }

    function formatWhen(value) {
      if (!value) return 'unknown';
      const date = new Date(value);
      if (Number.isNaN(date.getTime())) return String(value);
      return date.toLocaleString();
    }

    function activateMenuButton(targetId) {
      document.querySelectorAll('.nav-btn[data-jump]').forEach((button) => {
        button.classList.toggle('active', button.dataset.jump === targetId);
      });
    }

    function jumpToPanel(targetId) {
      const target = document.getElementById(targetId);
      if (!target) return;
      activateMenuButton(targetId);
      target.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'nearest' });
    }

    function ensureThreatMap() {
      if (threatMap) return threatMap;
      threatMap = L.map('threatMap', { zoomControl: true, scrollWheelZoom: false }).setView([18, 0], 2);
      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 19,
        attribution: '&copy; OpenStreetMap contributors'
      }).addTo(threatMap);
      return threatMap;
    }

    function renderThreatMap(markers, agents, analystLocation) {
      const visibleMarkers = (markers || []).filter((marker) =>
        typeof marker.latitude === 'number' && typeof marker.longitude === 'number'
      );
      const localOnlyAgents = (agents || []).filter((agent) => !agent.geolocation || agent.geolocation.private);
      mappedAttackers.textContent = visibleMarkers.length;
      mapScopeLabel.textContent = visibleMarkers.length
        ? `${visibleMarkers.length} mapped location${visibleMarkers.length === 1 ? '' : 's'}`
        : 'No mapped locations yet';
      renderAnalystLocationNote(analystLocation);

      if (!visibleMarkers.length) {
        mapEmpty.style.display = 'block';
        mapEmpty.textContent = localOnlyAgents.length
          ? 'Only internal agent IPs are visible right now. Set an analyst location to pin your WSL or lab agents near the real workstation instead of relying on public-IP estimates.'
          : 'No attacker IP data is available yet.';
      } else {
        mapEmpty.style.display = 'none';
      }

      mapList.innerHTML = '';
      if (analystLocation && typeof analystLocation.latitude === 'number' && typeof analystLocation.longitude === 'number') {
        const analystItem = document.createElement('div');
        analystItem.className = 'map-list-item';
        analystItem.innerHTML = `
          <strong>Analyst Console</strong><br>
          ${escapeHtml(analystLocation.label || 'Pinned location')}<br>
          Coordinates: ${escapeHtml(`${analystLocation.latitude.toFixed(4)}, ${analystLocation.longitude.toFixed(4)}`)}<br>
          Source: ${escapeHtml(sourceLabel(analystLocation.source))}
        `;
        mapList.appendChild(analystItem);
      }
      if (!visibleMarkers.length && !localOnlyAgents.length) {
        mapList.innerHTML += '<div class="empty-state">Deploy agents or wait for CALDERA metadata to populate this map.</div>';
      } else {
        visibleMarkers.forEach((marker) => {
          const item = document.createElement('div');
          item.className = 'map-list-item';
          item.innerHTML = `
            <strong>${escapeHtml(marker.display_name || marker.paw || marker.ip)}</strong><br>
            ${escapeHtml([marker.city, marker.region, marker.country].filter(Boolean).join(', ') || 'Unknown location')}<br>
            IP: ${escapeHtml(marker.ip)}<br>
            Coordinates: ${escapeHtml(`${marker.latitude.toFixed(4)}, ${marker.longitude.toFixed(4)}`)}<br>
            Source: ${escapeHtml(sourceLabel(marker.source))}
          `;
          mapList.appendChild(item);
        });
        localOnlyAgents.slice(0, 4).forEach((agent) => {
          const item = document.createElement('div');
          item.className = 'map-list-item';
          const ipText = (agent.candidate_ips || []).join(', ') || 'no IPs reported';
          item.innerHTML = `
            <strong>${escapeHtml(agent.display_name || agent.paw || 'Internal agent')}</strong><br>
            Internal address only<br>
            IPs: ${escapeHtml(ipText)}<br>
            Reason: ${escapeHtml((agent.geolocation || {}).reason || 'Private or internal address')}
          `;
          mapList.appendChild(item);
        });
      }

      const map = ensureThreatMap();
      threatMarkers.forEach((marker) => marker.remove());
      threatMarkers = [];
      if (analystMarker) {
        analystMarker.remove();
        analystMarker = null;
      }
      if (analystAccuracyCircle) {
        analystAccuracyCircle.remove();
        analystAccuracyCircle = null;
      }

      const bounds = [];
      const collisionMap = {};
      visibleMarkers.forEach((marker) => {
        const key = `${marker.latitude.toFixed(4)}:${marker.longitude.toFixed(4)}`;
        collisionMap[key] = collisionMap[key] || [];
        collisionMap[key].push(marker);
      });

      visibleMarkers.forEach((marker) => {
        const key = `${marker.latitude.toFixed(4)}:${marker.longitude.toFixed(4)}`;
        const peers = collisionMap[key] || [];
        const index = peers.indexOf(marker);
        const offset = peers.length > 1 ? 0.02 : 0;
        const angle = peers.length > 1 ? ((Math.PI * 2) / peers.length) * index : 0;
        const latitude = marker.latitude + (Math.sin(angle) * offset);
        const longitude = marker.longitude + (Math.cos(angle) * offset);
        const leafletMarker = L.marker([latitude, longitude]).addTo(map);
        leafletMarker.bindPopup(`
          <strong>${escapeHtml(marker.display_name || marker.paw || marker.ip)}</strong><br>
          ${escapeHtml([marker.city, marker.region, marker.country].filter(Boolean).join(', ') || 'Unknown location')}<br>
          IP: ${escapeHtml(marker.ip)}<br>
          Status: ${escapeHtml(marker.status || 'unknown')}<br>
          Source: ${escapeHtml(sourceLabel(marker.source))}
        `);
        threatMarkers.push(leafletMarker);
        bounds.push([latitude, longitude]);
      });

      if (analystLocation && typeof analystLocation.latitude === 'number' && typeof analystLocation.longitude === 'number') {
        analystMarker = L.circleMarker([analystLocation.latitude, analystLocation.longitude], {
          radius: 8,
          color: '#7fe6ff',
          weight: 2,
          fillColor: '#102b40',
          fillOpacity: 0.9
        }).addTo(map);
        analystMarker.bindPopup(`
          <strong>Analyst Console</strong><br>
          ${escapeHtml(analystLocation.label || 'Pinned location')}<br>
          Source: ${escapeHtml(sourceLabel(analystLocation.source))}
        `);
        if (analystLocation.accuracy) {
          analystAccuracyCircle = L.circle([analystLocation.latitude, analystLocation.longitude], {
            radius: analystLocation.accuracy,
            color: '#7fe6ff',
            weight: 1,
            fillOpacity: 0.05
          }).addTo(map);
        }
        bounds.push([analystLocation.latitude, analystLocation.longitude]);
      }

      if (!bounds.length) {
        map.setView([18, 0], 2);
        setTimeout(() => map.invalidateSize(), 50);
        return;
      }
      if (bounds.length === 1) {
        map.setView(bounds[0], 10);
      } else {
        map.fitBounds(bounds, { padding: [30, 30] });
      }
      setTimeout(() => map.invalidateSize(), 50);
    }

    function renderLiveOverview(overview) {
      latestLiveOverview = overview || {};
      const stats = latestLiveOverview.stats || {};
      const agents = latestLiveOverview.agents || [];
      const visibleAgents = filterVisibleAgents(agents);
      const operations = latestLiveOverview.operations || [];

      liveAgentTotal.textContent = stats.agent_total || 0;
      liveAgentAlive.textContent = stats.agent_alive || 0;
      liveAgentDead.textContent = stats.agent_dead || 0;
      liveAgentUntrusted.textContent = stats.agent_untrusted || 0;
      liveOperationTotal.textContent = stats.operation_total || 0;
      liveOperationRunning.textContent = stats.operation_running || 0;
      agentViewSummary.textContent = agentViewMode === 'alive'
        ? `Showing ${visibleAgents.length} alive or pending agents`
        : agentViewMode === 'dead'
          ? `Showing ${visibleAgents.length} dead agents retained from CALDERA`
          : `Showing all ${agents.length} CALDERA agents`;

      agentLiveList.innerHTML = '';
      if (!visibleAgents.length) {
        agentLiveList.innerHTML = '<div class="empty-state">No agents are currently visible from CALDERA.</div>';
      } else {
        visibleAgents.forEach((agent) => {
          const card = document.createElement('div');
          card.className = 'live-card';
          const badgeClass = statusBadgeClass(agent.status);
          const trustText = agent.trusted ? 'trusted' : 'untrusted';
          const ipText = (agent.candidate_ips || []).join(', ') || 'no IPs reported';
          card.innerHTML = `
            <div class="live-card-header">
              <div>
                <div class="live-card-title">${escapeHtml(agent.display_name || agent.paw)}</div>
                <div class="live-card-meta">
                  <span class="tiny-chip">${escapeHtml(agent.paw || 'unknown paw')}</span>
                  <span class="tiny-chip">${escapeHtml(agent.host || 'unknown host')}</span>
                  <span class="tiny-chip">${escapeHtml(agent.platform || 'unknown platform')}</span>
                </div>
              </div>
              <span class="status-badge ${badgeClass}">${escapeHtml(agent.status || 'unknown')}</span>
            </div>
            <div class="live-card-meta">
              <span class="tiny-chip">${escapeHtml(trustText)}</span>
              <span class="tiny-chip">${escapeHtml(agent.group || 'group n/a')}</span>
              <span class="tiny-chip">${escapeHtml(agent.privilege || 'privilege n/a')}</span>
              <span class="tiny-chip">${escapeHtml(`${agent.link_count || 0} links`)}</span>
            </div>
            <div class="agent-meta">Last seen: ${escapeHtml(formatWhen(agent.last_seen))}</div>
            <div class="agent-meta">IPs: ${escapeHtml(ipText)}</div>
          `;
          card.addEventListener('click', () => {
            if (agentFilter.value !== agent.paw) {
              agentFilter.value = agent.paw;
              fetchAndRender();
            }
          });
          agentLiveList.appendChild(card);
        });
      }

      operationList.innerHTML = '';
      if (!operations.length) {
        operationList.innerHTML = '<div class="empty-state">No operations are currently present in CALDERA.</div>';
      } else {
        operations.forEach((operation) => {
          const card = document.createElement('div');
          card.className = 'operation-card';
          card.innerHTML = `
            <div class="operation-card-header">
              <div>
                <div class="operation-card-title">${escapeHtml(operation.name || operation.id || 'Operation')}</div>
                <div class="operation-card-meta">
                  <span class="tiny-chip">${escapeHtml(operation.id || 'no id')}</span>
                  <span class="tiny-chip">${escapeHtml(operation.adversary || 'unknown adversary')}</span>
                </div>
              </div>
              <span class="status-badge ${operationBadgeClass(operation.state)}">${escapeHtml(operation.state || 'unknown')}</span>
            </div>
            <div class="operation-card-meta">
              <span class="tiny-chip">${escapeHtml(`${operation.agent_count || 0} agents`)}</span>
              <span class="tiny-chip">${escapeHtml(`${operation.chain_count || 0} links`)}</span>
              <span class="tiny-chip">${escapeHtml(`${operation.completed_links || 0} complete`)}</span>
              <span class="tiny-chip">${escapeHtml(`${operation.failed_links || 0} failed`)}</span>
            </div>
            <div class="agent-meta">Started: ${escapeHtml(formatWhen(operation.start))}</div>
            <div class="agent-meta">Finished: ${escapeHtml(formatWhen(operation.finish))}</div>
          `;
          operationList.appendChild(card);
        });
      }

      renderThreatMap(latestLiveOverview.map_markers || [], agents, latestLiveOverview.analyst_location || null);
    }

    async function fetchLiveOverview() {
      const res = await fetch('/api/live_overview', { credentials: 'same-origin' });
      const data = await res.json();
      renderLiveOverview(data || {});
    }


    function setOptions(selectEl, values, label) {
      const current = selectEl.value;
      selectEl.innerHTML = `<option value="">${label}</option>`;
      values.forEach(v => {
        const opt = document.createElement('option');
        opt.value = v;
        opt.textContent = v;
        selectEl.appendChild(opt);
      });
      if ([...selectEl.options].some(o => o.value === current)) {
        selectEl.value = current;
      }
    }

    function escapeHtml(value) {
      return String(value || '')
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
    }

    function focusId(focus) {
      return `${focus.type || 'general'}|${focus.title || ''}|${focus.target || ''}`;
    }

    function markSelectedFocus() {
      const activeId = selectedFocus ? focusId(selectedFocus) : '';
      document.querySelectorAll('.selectable-item[data-focus-id]').forEach((el) => {
        el.classList.toggle('selected', el.dataset.focusId === activeId);
      });
      document.querySelectorAll('.selectable-item[data-recommendation]').forEach((el) => {
        el.classList.toggle('selected', (el.dataset.recommendation || '') === selectedRecommendation);
      });
      document.querySelectorAll('.agent-card[data-agent-id]').forEach((el) => {
        el.classList.toggle('selected', !!selectedAgentProfile && el.dataset.agentId === selectedAgentProfile.agent_id);
      });
    }

    function renderSelectedFocus() {
      if (!selectedFocus) {
        attackFocus.textContent = 'Select a likely attack or attack path to guide the chatbot.';
        const agentText = selectedAgentProfile ? ` for ${selectedAgentProfile.agent_id}` : '';
        chatInput.placeholder = `Ask: how to face this attack${agentText}?`;
        defenseInput.placeholder = `Ask: what is the best defense${agentText}?`;
        markSelectedFocus();
        return;
      }

      const techniques = (selectedFocus.techniques || [])
        .slice(0, 5)
        .map((item) => `<span class="focus-tag">${escapeHtml(item)}</span>`)
        .join('');

      attackFocus.innerHTML = `
        <div class="focus-title">${escapeHtml(selectedFocus.title)}</div>
        <div class="focus-subtitle">${escapeHtml(selectedFocus.summary || 'Focused incident context for the chatbot.')}</div>
        ${techniques ? `<div class="focus-tags">${techniques}</div>` : ''}
        <div><strong>Guidance:</strong> ${escapeHtml(selectedFocus.guidance || 'Use this focus to ask about containment, detection, or validation.')}</div>
        ${selectedAgentProfile ? `<div style="margin-top:8px;"><strong>Selected agent:</strong> ${escapeHtml(selectedAgentProfile.agent_id)} | ${escapeHtml(selectedAgentProfile.risk_level)} ${escapeHtml(selectedAgentProfile.risk_score)}</div>` : ''}
      `;
      const agentText = selectedAgentProfile ? ` on ${selectedAgentProfile.agent_id}` : '';
      chatInput.placeholder = `Ask about ${selectedFocus.title.toLowerCase()}${agentText}`;
      defenseInput.placeholder = `Ask how to defend ${selectedFocus.title.toLowerCase()}${agentText}`;
      markSelectedFocus();
    }

    function ensureSelectedFocus() {
      const available = [...latestScenarioFocuses, ...latestPathFocuses];
      if (!available.length) {
        selectedFocus = null;
        renderSelectedFocus();
        return;
      }
      if (!selectedFocus) {
        selectedFocus = available[0];
        renderSelectedFocus();
        return;
      }
      const match = available.find((item) => focusId(item) === focusId(selectedFocus));
      selectedFocus = match || available[0];
      renderSelectedFocus();
    }

    function normalizeAgentProfileSelection() {
      if (!latestAgentProfiles.length) {
        selectedAgentProfile = null;
        return;
      }

      if (agentFilter.value) {
        const exact = latestAgentProfiles.find((item) => item.agent_id === agentFilter.value);
        if (exact) {
          selectedAgentProfile = exact;
          return;
        }
      }

      if (selectedAgentProfile) {
        const match = latestAgentProfiles.find((item) => item.agent_id === selectedAgentProfile.agent_id);
        if (match) {
          selectedAgentProfile = match;
          return;
        }
      }

      selectedAgentProfile = latestAgentProfiles[0];
    }

    function riskClass(level) {
      const normalized = String(level || 'LOW').toLowerCase();
      if (normalized === 'critical') return 'critical';
      if (normalized === 'elevated') return 'elevated';
      return 'low';
    }

    function renderAgentProfiles(profiles) {
      latestAgentProfiles = profiles || [];
      normalizeAgentProfileSelection();
      agentDefenseGrid.innerHTML = '';

      if (!latestAgentProfiles.length) {
        agentDefenseGrid.innerHTML = '<div class="focus-card">No agent-specific defense data yet.</div>';
        markSelectedFocus();
        return;
      }

      latestAgentProfiles.forEach((profile) => {
        const card = document.createElement('div');
        card.className = 'agent-card';
        card.dataset.agentId = profile.agent_id;
        const primaryRecommendation = (profile.recommendations || [])[0] || 'Collect host-specific telemetry and validate scope.';
        const targetText = (profile.targets || []).slice(0, 3).join(', ') || 'no target labels yet';
        card.innerHTML = `
          <div class="agent-card-header">
            <div class="agent-name">${escapeHtml(profile.agent_id)}</div>
            <div class="agent-pill ${riskClass(profile.risk_level)}">${escapeHtml(profile.risk_level)} ${escapeHtml(profile.risk_score)}</div>
          </div>
          <div class="agent-meta">Targets: ${escapeHtml(targetText)}</div>
          <div class="agent-meta">Techniques: ${escapeHtml((profile.techniques || []).slice(0, 4).join(', ') || 'none')}</div>
          <div class="agent-meta" style="margin-top:6px;">${escapeHtml(primaryRecommendation)}</div>
        `;
        card.addEventListener('click', () => {
          selectedAgentProfile = profile;
          if (agentFilter.value !== profile.agent_id) {
            agentFilter.value = profile.agent_id;
            fetchAndRender();
            return;
          }
          selectedRecommendation = (profile.recommendations || [])[0] || '';
          renderDefense(profile.recommendations || latestRecommendations);
          renderSelectedFocus();
          markSelectedFocus();
        });
        agentDefenseGrid.appendChild(card);
      });

      markSelectedFocus();
    }

    function renderSummary(summary) {
      document.getElementById('kpiAgents').textContent = summary.agent_count || 0;
      document.getElementById('kpiFacts').textContent = summary.fact_count || 0;
      document.getElementById('kpiChains').textContent = summary.chain_count || 0;
      document.getElementById('kpiTech').textContent = summary.technique_count || 0;
      document.getElementById('riskLevel').textContent = summary.risk_level || 'LOW';
      document.getElementById('riskScore').textContent = summary.risk_score || 0;
      document.getElementById('riskFill').style.width = `${summary.risk_score || 0}%`;

      const critical = document.getElementById('criticalBanner');
      critical.style.display = (summary.risk_level === 'CRITICAL') ? 'block' : 'none';
    }

    function renderMitre(techniques) {
      const list = document.getElementById('mitreList');
      list.innerHTML = '';
      if (!techniques || !techniques.length) {
        list.innerHTML = '<li><span>No MITRE mapping yet</span><span>0</span></li>';
        return;
      }
      techniques.forEach(item => {
        const li = document.createElement('li');
        li.innerHTML = `<span>${item.id}</span><span>${item.count}</span>`;
        list.appendChild(li);
      });
    }

    function updateGraphStats(graphData) {
      const nodeCount = graphData?.nodes?.length || 0;
      const edgeCount = graphData?.edges?.length || 0;
      const pathCount = graphData?.attack_paths?.length || 0;
      const meta = graphData?.meta || {};
      graphNodeCount.textContent = nodeCount;
      graphEdgeCount.textContent = edgeCount;
      graphPathCount.textContent = pathCount;
      graphPathCountRibbon.textContent = pathCount;

      const parts = [];
      if (agentFilter.value) parts.push(`agent ${agentFilter.value}`);
      if (targetFilter.value) parts.push(`target ${targetFilter.value}`);
      if (graphAgentStateMode !== 'all') {
        parts.push(`${graphAgentStateMode} agents only`);
      } else if (meta.alive_agent_count || meta.dead_agent_count) {
        parts.push(`${meta.alive_agent_count || 0} alive / ${meta.dead_agent_count || 0} dead in CALDERA`);
      }
      if (parts.length) {
        graphMeta.textContent = `Filtered view for ${parts.join(' and ')}. Click nodes to inspect local chains without refreshing the dashboard.`;
        return;
      }
      if (!nodeCount) {
        graphMeta.textContent = 'No graph data is available for the current filters.';
        return;
      }
      graphMeta.textContent = 'Live agent-to-fact graph with focused inspection, clearer path layouts, and risk-centered navigation.';
    }

    function renderPathRibbon(graphData) {
      const attackPaths = graphData?.attack_paths || [];
      pathRibbonList.innerHTML = '';
      if (!attackPaths.length) {
        pathRibbonList.innerHTML = '<div class="empty-state">No readable attack paths are available yet. Once CALDERA and Neo4j have more linked facts, the top chains will appear here automatically.</div>';
        return;
      }

      attackPaths.slice(0, 6).forEach((path, index) => {
        const card = document.createElement('button');
        card.type = 'button';
        card.className = `path-ribbon-card${index === 0 ? ' active' : ''}`;
        const techniques = (path.techniques || []).filter(Boolean).slice(0, 4);
        const agents = (path.agents || []).filter(Boolean);
        card.innerHTML = `
          <strong>Path ${index + 1}${path.target ? ` • ${escapeHtml(path.target)}` : ''}</strong>
          <div class="path-ribbon-meta">
            <span>Risk ${escapeHtml(path.risk_score || 0)}</span>
            <span>${escapeHtml(path.length || (path.nodes || []).length || 0)} steps</span>
            <span>${escapeHtml(agents.join(', ') || 'No agent label')}</span>
          </div>
          <div class="path-ribbon-steps">
            ${techniques.length ? techniques.map((tech) => `<span class="path-step">${escapeHtml(tech)}</span>`).join('') : '<span class="path-step">unmapped</span>'}
          </div>
        `;
        card.addEventListener('click', () => {
          document.querySelectorAll('.path-ribbon-card').forEach((item) => item.classList.remove('active'));
          card.classList.add('active');
          selectedFocus = {
            type: 'path',
            title: `Attack Path ${index + 1}`,
            summary: `Target ${path.target || 'unknown'} with risk ${path.risk_score || 0}.`,
            guidance: 'Use the graph center action to trace this path, then ask the copilot about containment or validation.',
            target: path.target || '',
            techniques: path.techniques || []
          };
          renderSelectedFocus();
          focusHighestRiskPath(path);
        });
        pathRibbonList.appendChild(card);
      });
    }

    function setGraphInspector(title, typeLabel, cards, note) {
      const cardHtml = (cards || [])
        .map((item) => `
          <div class="inspector-card">
            <span class="label">${escapeHtml(item.label)}</span>
            <div class="value">${escapeHtml(item.value)}</div>
          </div>
        `)
        .join('');

      graphInspector.innerHTML = `
        <h3>Graph Inspector</h3>
        <div class="inspector-title">${escapeHtml(title)}</div>
        ${typeLabel ? `<div class="inspector-type">${escapeHtml(typeLabel)}</div>` : ''}
        ${cardHtml ? `<div class="inspector-grid">${cardHtml}</div>` : ''}
        <div class="inspector-note">${escapeHtml(note)}</div>
        <div class="graph-hint">Tap empty space or use “Clear Focus” to return to the full graph view.</div>
      `;
    }

    function resetGraphInspector() {
      setGraphInspector(
        'Nothing selected',
        '',
        [],
        'Click a node or edge to inspect it. The graph will dim unrelated items so attack chains are easier to follow.'
      );
    }

    function showGraphCanvasMessage(title, detail) {
      const graphEl = document.getElementById('graph');
      if (!graphEl) return;
      graphEl.innerHTML = `
        <div style="height:100%;min-height:420px;display:flex;align-items:center;justify-content:center;padding:24px;">
          <div style="max-width:520px;border:1px solid rgba(127,230,255,0.18);border-radius:18px;padding:22px 24px;background:linear-gradient(180deg, rgba(12, 19, 29, 0.96), rgba(7, 11, 17, 0.96));box-shadow:0 16px 36px rgba(0,0,0,0.24);text-align:center;">
            <div style="color:#7fe6ff;font-size:18px;font-weight:700;letter-spacing:0.3px;margin-bottom:8px;">${escapeHtml(title)}</div>
            <div style="color:#90a9c1;font-size:13px;line-height:1.6;">${escapeHtml(detail)}</div>
          </div>
        </div>
      `;
    }

    function getLayoutConfig(name) {
      if (name === 'concentric') {
        return {
          name: 'concentric',
          animate: false,
          fit: true,
          padding: 48,
          spacingFactor: 1.18,
          minNodeSpacing: 44,
          concentric(node) {
            return node.data('type') === 'agent' ? 3 : (node.data('technique') ? 2 : 1);
          },
          levelWidth() {
            return 1;
          }
        };
      }

      if (name === 'cose') {
        return {
          name: 'cose',
          animate: false,
          fit: true,
          padding: 48,
          nodeRepulsion: 12000,
          idealEdgeLength: 150,
          edgeElasticity: 80,
          nestingFactor: 0.9
        };
      }

      return {
        name: 'breadthfirst',
        animate: false,
        fit: true,
        padding: 48,
        directed: true,
        spacingFactor: 1.38,
        avoidOverlap: true,
        nodeDimensionsIncludeLabels: true
      };
    }

    function applyGraphLayout() {
      if (!cy) return;
      cy.layout(getLayoutConfig(graphLayout.value)).run();
    }

    function clearGraphSelection() {
      graphSelectionId = '';
      graphHoverActive = false;
      if (cy) {
        cy.elements().removeClass('selected faded hovered dimmed');
      }
      resetGraphInspector();
    }

    function renderGraphSelection(element) {
      if (!cy || !element) return;

      graphHoverActive = false;
      cy.elements().removeClass('selected faded hovered dimmed');

      let highlighted = element.closedNeighborhood();
      if (element.isNode && element.isNode()) {
        highlighted = highlighted.union(element.predecessors()).union(element.successors());
        graphSelectionId = element.id();
        const data = element.data();
        if (data.type === 'agent') {
          const executedCount = element.outgoers('edge[relation = "executed"]').length;
          const chainCount = element.outgoers('node[type = "fact"]').length;
          setGraphInspector(
            data.label || data.id,
            'Agent',
            [
              { label: 'Status', value: data.status || 'unknown' },
              { label: 'Executed Facts', value: String(executedCount) },
              { label: 'Local Fan-out', value: String(chainCount) },
              { label: 'Filter Match', value: agentFilter.value || 'All agents' }
            ],
            'This agent is acting as an entry point into the visible chain. Use the top filters if you want the whole dashboard narrowed to this agent.'
          );
        } else {
          const predecessorCount = element.predecessors('node').length;
          const successorCount = element.successors('node').length;
          setGraphInspector(
            data.label || data.id,
            'Fact',
            [
              { label: 'Technique', value: data.technique || 'unmapped' },
              { label: 'Target', value: data.target || 'unknown' },
              { label: 'Upstream Nodes', value: String(predecessorCount) },
              { label: 'Downstream Nodes', value: String(successorCount) }
            ],
            'This fact node represents an observed command or artifact. The highlighted neighborhood shows how it connects to nearby steps in the attack path.'
          );
        }
      } else if (element.isEdge && element.isEdge()) {
        highlighted = element.connectedNodes().union(element);
        graphSelectionId = element.id();
        const data = element.data();
        setGraphInspector(
          `${data.source} -> ${data.target}`,
          'Relationship',
          [
            { label: 'Relation', value: data.relation || 'unknown' },
            { label: 'Source', value: data.source || 'unknown' },
            { label: 'Target', value: data.target || 'unknown' },
            { label: 'Edge Id', value: data.id || 'n/a' }
          ],
          'Relationships show whether an agent executed a fact directly or whether one fact led to the next stage in the chain.'
        );
      }

      highlighted.addClass('selected');
      cy.elements().difference(highlighted).addClass('faded');
    }

    function previewGraphSelection(element) {
      if (!cy || !element || graphSelectionId) return;

      cy.elements().removeClass('hovered dimmed');
      let highlighted = element.closedNeighborhood();

      if (element.isNode && element.isNode()) {
        highlighted = highlighted.union(element.predecessors()).union(element.successors());
        const data = element.data();
        setGraphInspector(
          data.label || data.id,
          data.type === 'agent' ? 'Agent Preview' : 'Fact Preview',
          data.type === 'agent'
            ? [
                { label: 'Status', value: data.status || 'unknown' },
                { label: 'Host', value: data.host || 'unknown' },
                { label: 'Privilege', value: data.privilege || 'n/a' },
                { label: 'Last Seen', value: data.last_seen || 'n/a' }
              ]
            : [
                { label: 'Technique', value: data.technique || 'unmapped' },
                { label: 'Target', value: data.target || 'unknown' },
                { label: 'Operation', value: data.operation_id || 'n/a' },
                { label: 'Timestamp', value: data.timestamp || 'n/a' }
              ],
          'Hover preview: click to lock focus and dim the rest of the graph around this chain.'
        );
      } else if (element.isEdge && element.isEdge()) {
        highlighted = element.connectedNodes().union(element);
        const data = element.data();
        setGraphInspector(
          `${data.source} -> ${data.target}`,
          'Relationship Preview',
          [
            { label: 'Relation', value: data.relation || 'unknown' },
            { label: 'Source', value: data.source || 'unknown' },
            { label: 'Target', value: data.target || 'unknown' }
          ],
          'Hover preview: click to hold this relationship in focus.'
        );
      }

      highlighted.addClass('hovered');
      cy.elements().difference(highlighted).addClass('dimmed');
      graphHoverActive = true;
    }

    function clearGraphPreview() {
      if (!cy || graphSelectionId || !graphHoverActive) return;
      graphHoverActive = false;
      cy.elements().removeClass('hovered dimmed');
      resetGraphInspector();
    }

    function focusHighestRiskPath(targetPath = null) {
      if (!cy) return;
      const path = targetPath || latestGraphData?.attack_paths?.[0];
      if (!path?.nodes?.length) {
        clearGraphSelection();
        if (cy.elements().length) cy.fit(cy.elements(), 34);
        return;
      }

      let collection = cy.collection();
      path.nodes.forEach((id) => {
        const node = cy.getElementById(id);
        if (node.length) {
          collection = collection.union(node);
        }
      });
      if (!collection.length) return;

      const connectedEdges = collection.connectedEdges().filter((edge) =>
        collection.contains(edge.source()) && collection.contains(edge.target())
      );
      collection = collection.union(connectedEdges);
      cy.elements().removeClass('selected faded');
      collection.addClass('selected');
      cy.elements().difference(collection).addClass('faded');
      cy.animate({ fit: { eles: collection, padding: 56 }, duration: 400 });
      graphSelectionId = `risk:${path.nodes.join('|')}`;
      setGraphInspector(
        `Risk Path (${path.risk_score || 0})`,
        'Attack Path',
        [
          { label: 'Target', value: path.target || 'unknown' },
          { label: 'Agents', value: (path.agents || []).join(', ') || 'none' },
          { label: 'Length', value: String(path.length || path.nodes.length || 0) },
          { label: 'Techniques', value: (path.techniques || []).join(', ') || 'none' }
        ],
        'This is the highest risk path currently visible in the graph. It is useful for quickly centering the most urgent chain during triage.'
      );
    }

    function renderGraph(graphData) {
      const hasNodes = graphData && graphData.nodes && graphData.nodes.length > 0;
      document.getElementById('empty').style.display = hasNodes ? 'none' : 'block';
      updateGraphStats(graphData);
      renderPathRibbon(graphData);
      resetGraphInspector();

      if (cy) {
        cy.destroy();
        cy = null;
      }

      document.getElementById('graph').innerHTML = '';

      if (!hasNodes) {
        showGraphCanvasMessage(
          'No graph data yet',
          'No linked CALDERA activity is available for the current filters. Try widening the scope or run another operation to populate the attack path graph.'
        );
        return;
      }

      if (typeof window.cytoscape !== 'function') {
        showGraphCanvasMessage(
          'Graph renderer unavailable',
          'Cytoscape did not load in this browser session, so the interactive SOC graph could not start.'
        );
        return;
      }

      try {
        cy = cytoscape({
          container: document.getElementById('graph'),
          elements: [...graphData.nodes, ...graphData.edges],
          minZoom: 0.4,
          maxZoom: 2.2,
          style: [
            {
              selector: 'node[type="agent"]',
              style: {
                'background-color': '#00ffcc',
                'background-gradient-stop-colors': '#00ffcc #46c8ff',
                'background-gradient-direction': 'to-bottom-right',
                'border-width': 2.4,
                'border-color': '#0f8a74',
                'label': 'data(label)',
                'color': '#031019',
                'font-size': 12,
                'font-weight': 700,
                'text-wrap': 'wrap',
                'text-max-width': 132,
                'text-valign': 'center',
                'text-halign': 'center',
                'shape': 'round-rectangle',
                'width': 150,
                'height': 52,
                'padding': '10px'
              }
            },
            {
              selector: 'node[type="agent"][status = "pending kill"]',
              style: {
                'background-color': '#58b5ff',
                'background-gradient-stop-colors': '#58b5ff #7fe6ff',
                'border-color': '#1c6fa5',
                'color': '#06131f'
              }
            },
            {
              selector: 'node[type="agent"][status = "dead"]',
              style: {
                'background-color': '#ff8f5a',
                'background-gradient-stop-colors': '#ff8f5a #ff4d4d',
                'border-color': '#7f1212',
                'color': '#fff',
                'shape': 'diamond'
              }
            },
            {
              selector: 'node[type="agent"][!trusted]',
              style: {
                'border-style': 'dashed',
                'border-color': '#f7b955'
              }
            },
            {
              selector: 'node[type="fact"]',
              style: {
                'background-color': '#ff5f8d',
                'background-gradient-stop-colors': '#ff5f8d #ff875f',
                'background-gradient-direction': 'to-bottom-right',
                'label': 'data(label)',
                'color': '#fff',
                'font-size': 10,
                'text-wrap': 'wrap',
                'text-max-width': 156,
                'text-valign': 'center',
                'text-halign': 'center',
                'shape': 'round-rectangle',
                'width': 176,
                'height': 56,
                'padding': '8px'
              }
            },
            {
              selector: 'edge[relation="executed"]',
              style: {
                'line-color': '#43d9bd',
                'target-arrow-color': '#43d9bd',
                'target-arrow-shape': 'triangle',
                'curve-style': 'bezier',
                'width': 2.6,
                'arrow-scale': 1,
                'opacity': 0.92
              }
            },
            {
              selector: 'edge[relation="next"]',
              style: {
                'line-color': '#f7b955',
                'target-arrow-color': '#f7b955',
                'target-arrow-shape': 'triangle',
                'curve-style': 'bezier',
                'line-style': 'dashed',
                'width': 2.1,
                'arrow-scale': 0.96,
                'opacity': 0.86
              }
            },
            {
              selector: '.hovered',
              style: {
                'opacity': 1,
                'border-width': 3,
                'border-color': '#7fe6ff',
                'line-color': '#7fe6ff',
                'target-arrow-color': '#7fe6ff',
                'z-index': 990
              }
            },
            {
              selector: '.dimmed',
              style: {
                'opacity': 0.24
              }
            },
            {
              selector: '.selected',
              style: {
                'opacity': 1,
                'border-width': 3,
                'border-color': '#fff4b0',
                'line-color': '#fff4b0',
                'target-arrow-color': '#fff4b0',
                'z-index': 999
              }
            },
            {
              selector: '.faded',
              style: {
                'opacity': 0.16
              }
            }
          ],
          layout: getLayoutConfig(graphLayout?.value || 'breadthfirst')
        });
      } catch (error) {
        console.error('Graph render failed.', error);
        showGraphCanvasMessage(
          'Graph render failed',
          error.message || 'The Cytoscape renderer could not initialize the operational graph.'
        );
        return;
      }

      cy.on('layoutstop', function() {
        if (!cy) return;
        window.requestAnimationFrame(() => {
          if (!cy) return;
          cy.resize();
          cy.fit(cy.elements(), 48);
          cy.center();
        });
      });

      cy.on('tap', 'node', function(evt) {
        renderGraphSelection(evt.target);
      });
      cy.on('tap', 'edge', function(evt) {
        renderGraphSelection(evt.target);
      });
      cy.on('mouseover', 'node, edge', function(evt) {
        previewGraphSelection(evt.target);
      });
      cy.on('mouseout', 'node, edge', function() {
        clearGraphPreview();
      });
      cy.on('tap', function(evt) {
        if (evt.target === cy) {
          clearGraphSelection();
        }
      });
    }

    function renderDefense(recommendations) {
      latestRecommendations = recommendations || [];
      const sourceRecommendations = (selectedAgentProfile && selectedAgentProfile.recommendations && selectedAgentProfile.recommendations.length)
        ? selectedAgentProfile.recommendations
        : latestRecommendations;
      defenseList.innerHTML = '';
      if (!sourceRecommendations || !sourceRecommendations.length) {
        defenseList.innerHTML = '<li>No recommendations yet</li>';
        selectedRecommendation = '';
        markSelectedFocus();
        return;
      }
      sourceRecommendations.forEach(item => {
        const li = document.createElement('li');
        li.className = 'selectable-item';
        li.dataset.recommendation = item;
        li.textContent = item;
        li.addEventListener('click', () => {
          selectedRecommendation = item;
          defenseInput.value = `Use this defense suggestion: ${item}`;
          markSelectedFocus();
        });
        defenseList.appendChild(li);
      });
      if (!sourceRecommendations.includes(selectedRecommendation) && sourceRecommendations.length) {
        selectedRecommendation = sourceRecommendations[0];
      }
      markSelectedFocus();
    }

    function renderScenarios(scenarios) {
      latestScenarioFocuses = [];
      scenarioList.innerHTML = '';
      if (!scenarios || !scenarios.length) {
        scenarioList.innerHTML = '<li>No strong attack chain match yet.</li>';
        ensureSelectedFocus();
        return;
      }
      scenarios.slice(0, 4).forEach((s, idx) => {
        const confidence = Math.round((s.confidence || 0) * 100);
        const matched = (s.matched || []).join(', ') || 'none';
        const focus = {
          type: 'scenario',
          title: s.name || `Scenario ${idx + 1}`,
          target: targetFilter.value || '',
          summary: `[${s.severity || 'MEDIUM'}] confidence ${confidence}% | matched ${matched}`,
          guidance: s.response || s.detection || 'Review telemetry, contain affected systems, and validate recovery.',
          techniques: s.matched || s.required || [],
        };
        latestScenarioFocuses.push(focus);
        const li = document.createElement('li');
        li.className = 'selectable-item';
        li.dataset.focusId = focusId(focus);
        li.textContent = `#${idx + 1} [${s.severity || 'MEDIUM'}] ${s.name || 'Scenario'} | confidence ${confidence}% | matched ${matched}`;
        li.addEventListener('click', () => {
          selectedFocus = focus;
          renderSelectedFocus();
        });
        scenarioList.appendChild(li);
      });
      ensureSelectedFocus();
    }

    function renderAttackPaths(paths, targetRisk) {
      latestPathFocuses = [];
      pathList.innerHTML = '';
      if (!paths || !paths.length) {
        pathList.innerHTML = '<li>No attack paths built yet.</li>';
        ensureSelectedFocus();
        return;
      }
      paths.slice(0, 5).forEach((p, idx) => {
        const agents = (p.agents || []).join(', ') || 'unknown';
        const tech = (p.techniques || []).slice(0, 3).join(' -> ') || 'none';
        const targetInfo = targetRisk && targetRisk[p.target] ? ` | target risk ${targetRisk[p.target].max_path_risk}` : '';
        const focus = {
          type: 'path',
          title: `Attack Path #${idx + 1}`,
          target: p.target || '',
          summary: `${p.target || 'unknown target'} | depth ${p.length} | risk ${p.risk_score}${targetInfo}`,
          guidance: `Agents involved: ${agents}. Techniques: ${tech}. Prioritize scope, containment, and evidence preservation for this path.`,
          techniques: p.techniques || [],
        };
        latestPathFocuses.push(focus);
        const li = document.createElement('li');
        li.className = 'selectable-item';
        li.dataset.focusId = focusId(focus);
        li.textContent = `#${idx + 1} ${p.target} | depth ${p.length} | risk ${p.risk_score}${targetInfo} | agent ${agents} | tech ${tech}`;
        li.addEventListener('click', () => {
          selectedFocus = focus;
          renderSelectedFocus();
        });
        pathList.appendChild(li);
      });
      ensureSelectedFocus();
    }

    function renderAdversaryModel(model) {
      if (!model || !model.name) {
        adversaryModel.textContent = 'WSL adversary model is not available yet.';
        return;
      }

      const live = model.live_context || {};
      const phases = (model.phases || [])
        .map((phase) => `<li><strong>${escapeHtml(phase.name)}</strong>: ${escapeHtml(phase.goal)} (${escapeHtml((phase.techniques || []).join(', '))})</li>`)
        .join('');
      const steps = (model.operation_steps || [])
        .map((item) => `<li>${escapeHtml(item)}</li>`)
        .join('');
      const defenses = (model.defense_priorities || [])
        .map((item) => `<li>${escapeHtml(item)}</li>`)
        .join('');
      const tags = (live.highlighted_techniques || [])
        .map((item) => `<span class="focus-tag">${escapeHtml(item)}</span>`)
        .join('');

      adversaryModel.innerHTML = `
        <div class="focus-title">${escapeHtml(model.name)}</div>
        <div class="focus-subtitle">${escapeHtml(model.summary || '')}</div>
        <div><strong>Platform:</strong> ${escapeHtml(model.platform || 'WSL / Linux')}</div>
        <div><strong>Adversary ID:</strong> ${escapeHtml(model.id || 'n/a')}</div>
        <div><strong>CALDERA file:</strong> ${escapeHtml(model.caldera_file || 'n/a')}</div>
        <div><strong>Operation mode:</strong> ${escapeHtml(model.operation_mode || 'Concurrent multi-agent operation')}</div>
        <div><strong>Live scope:</strong> ${escapeHtml(`${live.active_agent_count || 0} agents | ${live.tracked_target_count || 0} targets | ${live.parallel_attack_paths || 0} attack paths`)}</div>
        ${tags ? `<div class="focus-tags">${tags}</div>` : ''}
        <div><strong>Active systems:</strong> ${escapeHtml((live.active_agents || []).join(', '))}</div>
        <div><strong>Tracked targets:</strong> ${escapeHtml((live.active_targets || []).join(', '))}</div>
        <ul class="compact-list">${phases}</ul>
        <div class="focus-subtitle" style="margin-top:8px;">Operation setup</div>
        <ul class="compact-list">${steps}</ul>
        <div class="focus-subtitle" style="margin-top:8px;">Defense priorities</div>
        <ul class="compact-list">${defenses}</ul>
      `;
    }

    async function fetchDefense() {
      const params = new URLSearchParams();
      if (agentFilter.value) params.set('agent', agentFilter.value);
      if (targetFilter.value) params.set('target', targetFilter.value);
      const res = await fetch(`/api/defense?${params.toString()}`, { credentials: 'same-origin' });
      const data = await res.json();
      renderAgentProfiles(data.agent_profiles || []);
      renderScenarios(data.matched_scenarios || []);
      renderDefense(data.recommendations || []);
      renderAdversaryModel(data.adversary_model || {});
      renderSelectedFocus();
    }

    async function fetchBackendStatus() {
      const res = await fetch('/api/backend_status', { credentials: 'same-origin' });
      const data = await res.json();
      renderBackendStatus(data || {});
    }

    function appendChatMessage(container, speaker, message, role) {
      const entry = document.createElement('div');
      entry.className = `chat-entry ${role}`;
      entry.innerHTML = `
        <span class="speaker">${escapeHtml(speaker)}</span>
        <div>${escapeHtml(message)}</div>
      `;
      container.appendChild(entry);
      container.scrollTop = container.scrollHeight;
    }

    function appendChatLine(line) {
      const [speaker, ...parts] = String(line || '').split(':');
      const message = parts.join(':').trim() || line;
      appendChatMessage(chatLog, speaker || 'Bot', message, /^(You)$/i.test(speaker || '') ? 'user' : 'bot');
    }

    function appendDefenseLine(line) {
      const [speaker, ...parts] = String(line || '').split(':');
      const message = parts.join(':').trim() || line;
      appendChatMessage(defenseLog, speaker || 'Advisor', message, /^(You)$/i.test(speaker || '') ? 'user' : 'bot');
    }

    function initializeChatPanels() {
      chatLog.innerHTML = '';
      defenseLog.innerHTML = '';
      appendChatMessage(chatLog, 'Bot', 'Ask me about attack risk, the graph, MITRE techniques, or what the current CALDERA activity means.', 'bot');
      appendChatMessage(defenseLog, 'Advisor', 'Select an attack focus or defense suggestion, then ask what to contain, detect, harden, or validate.', 'bot');
    }

    function primeChat(message) {
      chatInput.value = message;
      sendChat();
    }

    async function sendDefenseQuery(messageOverride) {
      const message = (messageOverride || defenseInput.value || '').trim();
      if (!message) return;
      appendDefenseLine(`You: ${message}`);
      defenseInput.value = '';

      const payload = {
        message,
        agent: agentFilter.value || null,
        target: targetFilter.value || null,
        focus: selectedFocus,
        recommendation: selectedRecommendation || '',
        agentProfile: selectedAgentProfile
      };

      const res = await fetch('/api/defense/advisor', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'same-origin',
        body: JSON.stringify(payload)
      });
      const data = await res.json();
      appendDefenseLine(`Advisor: ${data.reply || 'No defense guidance available.'}`);
    }

    function sendDefensePreset(question) {
      defenseInput.value = question;
      sendDefenseQuery(question);
    }

    async function sendChat() {
      const message = chatInput.value.trim();
      if (!message) return;
      appendChatLine(`You: ${message}`);
      chatInput.value = '';

      const payload = {
        message,
        agent: agentFilter.value || null,
        target: targetFilter.value || null,
        focus: selectedFocus,
        agentProfile: selectedAgentProfile
      };

      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'same-origin',
        body: JSON.stringify(payload)
      });
      const data = await res.json();
      appendChatLine(`Bot: ${data.reply || 'No response available.'}`);
    }

    async function fetchAndRender() {
      const params = new URLSearchParams();
      if (agentFilter.value) params.set('agent', agentFilter.value);
      if (targetFilter.value) params.set('target', targetFilter.value);
      if (graphAgentStateMode && graphAgentStateMode !== 'all') params.set('agent_state', graphAgentStateMode);

      const res = await fetch(`/api/graph?${params.toString()}`, { credentials: 'same-origin' });
      const data = await res.json();
      latestGraphData = data;

      setOptions(agentFilter, data.filters?.agents || [], 'All Agents');
      setOptions(targetFilter, data.filters?.targets || [], 'All Targets');
      renderSummary(data.summary || {});
      renderMitre(data.techniques || []);
      renderAttackPaths(data.attack_paths || [], data.target_risk || {});
      renderGraph(data);
      await fetchBackendStatus();
      await fetchLiveOverview();
      await fetchDefense();
    }

    function startAutoRefresh() {
      stopAutoRefresh();
      timerId = setInterval(fetchAndRender, 8000);
    }

    function stopAutoRefresh() {
      if (timerId) clearInterval(timerId);
      timerId = null;
    }

    function applyInitialState() {
      latestGraphData = initialGraph || {};
      latestLiveOverview = initialLiveOverview || {};
      setAgentViewMode(agentViewMode);
      setGraphAgentStateMode(graphAgentStateMode, false);
      renderBackendStatus(initialBackendStatus || {});
      renderLiveOverview(latestLiveOverview);
      setOptions(agentFilter, initialGraph.filters?.agents || [], 'All Agents');
      setOptions(targetFilter, initialGraph.filters?.targets || [], 'All Targets');
      renderSummary(initialGraph.summary || {});
      renderMitre(initialGraph.techniques || []);
      renderAttackPaths(initialGraph.attack_paths || [], initialGraph.target_risk || {});
      renderGraph(initialGraph);
      initializeChatPanels();
      renderSelectedFocus();
      fetchDefense();
      if (autoRefresh) startAutoRefresh();
    }

    async function loadTutorMode() {
      const res = await fetch('/api/tutor_mode?module=soc', { credentials: 'same-origin' });
      const data = await res.json();
      if (data.mode) tutorMode.value = data.mode;
    }

    document.getElementById('refreshBtn').addEventListener('click', fetchAndRender);
    agentFilter.addEventListener('change', fetchAndRender);
    targetFilter.addEventListener('change', fetchAndRender);
    tutorMode.addEventListener('change', async () => {
      await fetch('/api/tutor_mode', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'same-origin',
        body: JSON.stringify({ module: 'soc', mode: tutorMode.value })
      });
    });
    document.getElementById('chatSendBtn').addEventListener('click', sendChat);
    document.getElementById('defenseSendBtn').addEventListener('click', () => sendDefenseQuery());
    graphLayout.addEventListener('change', applyGraphLayout);
    document.querySelectorAll('[data-agent-view]').forEach((button) => {
      button.addEventListener('click', () => setAgentViewMode(button.dataset.agentView));
    });
    document.querySelectorAll('[data-graph-agent-view]').forEach((button) => {
      button.addEventListener('click', () => setGraphAgentStateMode(button.dataset.graphAgentView));
    });
    graphFitBtn.addEventListener('click', () => {
      if (!cy) return;
      clearGraphSelection();
      cy.animate({ fit: { eles: cy.elements(), padding: 48 }, duration: 300 });
    });
    graphCenterBtn.addEventListener('click', focusHighestRiskPath);
    graphClearBtn.addEventListener('click', () => {
      if (!cy) return;
      clearGraphSelection();
      cy.animate({ fit: { eles: cy.elements(), padding: 48 }, duration: 300 });
    });
    document.querySelectorAll('.nav-btn[data-jump]').forEach((button) => {
      button.addEventListener('click', () => jumpToPanel(button.dataset.jump));
    });
    chatInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') sendChat();
    });
    defenseInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') sendDefenseQuery();
    });
    autoBtn.addEventListener('click', () => {
      autoRefresh = !autoRefresh;
      autoBtn.textContent = autoRefresh ? 'Auto: ON (8s)' : 'Auto: OFF';
      if (autoRefresh) startAutoRefresh(); else stopAutoRefresh();
    });
    locateBtn.addEventListener('click', requestDeviceLocation);
    clearLocationBtn.addEventListener('click', async () => {
      try {
        await clearAnalystLocation();
      } catch (error) {
        analystLocationNote.textContent = error.message || 'Unable to clear analyst location.';
      }
    });
    saveLocationBtn.addEventListener('click', async () => {
      const query = (locationQueryInput.value || '').trim();
      if (!query) {
        analystLocationNote.textContent = 'Enter a place name first, for example Badangpet, Hyderabad.';
        return;
      }
      analystLocationNote.textContent = 'Searching for that place...';
      try {
        await saveAnalystLocation({ query });
      } catch (error) {
        analystLocationNote.textContent = error.message || 'Unable to save place.';
      }
    });
    locationQueryInput.addEventListener('keydown', (event) => {
      if (event.key === 'Enter') {
        event.preventDefault();
        saveLocationBtn.click();
      }
    });
    window.addEventListener('resize', () => {
      if (!cy) return;
      cy.resize();
    });

    applyInitialState();
    loadTutorMode();
  
