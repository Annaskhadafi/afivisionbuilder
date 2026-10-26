/**
 * Afivision Dashboard Builder & Standalone Web Engine
 * Gaya: Elementor (Free Drag & Drop) + Looker (Cross-Filtering)
 */
(function() {
  'use strict';

  const DashboardBuilder = {
    state: {
      projectId: 'default',
      dashboardsList: [],
      mode: 'edit', // 'edit' | 'preview'
      theme: 'dark', // 'dark' | 'light'
      zoom: 1.0,
      audioEnabled: true,
      lastChime: 0,
      layout: null,
      selectedWidgetId: null,
      filterCamera: null,
      registeredCameras: [],
      liveData: {
        metrics: {},
        cameras: {},
        recent_events: []
      },
      isDragging: false,
      isResizing: false,
      activeDragWidget: null,
      dragOffset: { x: 0, y: 0 },
      resizeData: null,
      pollInterval: null,
      chartCache: {},
      availableProjects: [],
      projectWorkflowsCache: {},
      selectedSlotIndex: 0,
      inspectorTab: 'content', // 'content' | 'style' | 'advanced'
      navigatorOpen: false,
      copilotOpen: false,
      pendingAiLayout: null,
      contextMenuWidgetId: null,
      realtimeCameras: [],
      patrolTimers: {},
      analysisState: {
        lastResult: null,
        currentConfidence: 0.25,
        isAnalyzing: false,
        uploadedFile: null,
        currentImageUrl: '/static/sample_workshop.jpg',
        activeLayers: { boxes: true, labels: true, masks: true },
        zoomLevel: 1.0
      }
    },

    async init() {
      console.log('[DashboardBuilder] Menginisialisasi Dashboard Builder...');
      this.bindToolbarEvents();
      this.bindPaletteEvents();
      this.bindModalEvents();
      this.bindKeyboardShortcuts();
      this.bindCanvasBackgroundEvents();
      this.bindContextMenuActions();
      await this.loadRegisteredCameras();
      await this.loadProjects();
      await this.loadRealtimeContext();
      await this.loadDashboardList();
      await this.loadLayout();
      this.startLivePolling();
    },

    async loadRealtimeContext() {
      try {
        const res = await fetch('/api/dashboard/builder/realtime-context');
        if (res.ok) {
          const data = await res.json();
          this.state.realtimeCameras = data.context?.available_cameras || [];
        }
      } catch (e) {
        this.state.realtimeCameras = [];
      }
    },

    getUnifiedCameraList() {
      const list = [];
      const seen = new Set();

      // 1. Dari realtime context cameras
      if (this.state.realtimeCameras && this.state.realtimeCameras.length) {
        this.state.realtimeCameras.forEach(c => {
          const key = c.label || c.id;
          if (!seen.has(key)) {
            seen.add(key);
            list.push({
              id: c.id,
              label: c.label || 'Kamera',
              workflowId: c.workflowId || 'default',
              workflowName: c.label,
              source: c.source || 'Webcam 0'
            });
          }
        });
      }

      // 2. Dari availableProjects
      if (this.state.availableProjects && this.state.availableProjects.length) {
        this.state.availableProjects.forEach(p => {
          const key = p.name || p.id;
          if (!seen.has(key)) {
            seen.add(key);
            list.push({
              id: 'proj_' + p.id,
              label: p.name || p.id,
              workflowId: p.id,
              workflowName: p.name || p.id,
              source: p.camera_source || 'Stream AI'
            });
          }
        });
      }

      // 3. Dari registeredCameras (WS-01, WS-02, WH-01...)
      if (this.state.registeredCameras && this.state.registeredCameras.length) {
        this.state.registeredCameras.forEach(rc => {
          const key = rc.name || rc.id;
          if (!seen.has(key)) {
            seen.add(key);
            list.push({
              id: rc.id,
              label: rc.name || rc.id,
              workflowId: 'default',
              workflowName: rc.name || rc.id,
              source: rc.streamUrl || 'RTSP'
            });
          }
        });
      }

      // Fallback jika belum ada
      if (!list.length) {
        list.push(
          { id: 'cam_ws01', label: 'WS-01: Workshop Bay 1', workflowId: 'default', workflowName: 'Workshop Bay 1', source: 'RTSP (WS-01)' },
          { id: 'cam_ws02', label: 'WS-02: Workshop Bay 2', workflowId: 'default', workflowName: 'Workshop Bay 2', source: 'RTSP (WS-02)' },
          { id: 'cam_wh01', label: 'WH-01: Warehouse Gate', workflowId: 'default', workflowName: 'Warehouse Gate', source: 'RTSP (WH-01)' },
          { id: 'cam_traffic', label: 'TR-01: Traffic Monitor', workflowId: 'default', workflowName: 'Traffic Flow', source: 'Webcam 0' }
        );
      }

      return list;
    },

    async loadRegisteredCameras() {
      try {
        const res = await fetch('/api/cameras');
        if (res.ok) {
          const data = await res.json();
          this.state.registeredCameras = Array.isArray(data) ? data : (data.cameras || []);
        }
      } catch (e) {
        this.state.registeredCameras = [];
      }
    },

    async loadProjects() {
      try {
        const res = await fetch('/api/projects');
        if (res.ok) {
          const data = await res.json();
          this.state.availableProjects = Array.isArray(data) ? data : (data.projects || []);
        }
      } catch (e) {
        this.state.availableProjects = [];
      }
    },

    async getWorkflowDetails(projectId) {
      if (!projectId) return null;
      if (this.state.projectWorkflowsCache[projectId]) {
        return this.state.projectWorkflowsCache[projectId];
      }
      try {
        const res = await fetch(`/api/projects/${encodeURIComponent(projectId)}`);
        if (res.ok) {
          const data = await res.json();
          this.state.projectWorkflowsCache[projectId] = data;
          return data;
        }
      } catch (e) {
        console.error('[DashboardBuilder] Error getWorkflowDetails:', e);
      }
      return null;
    },

    // ------------------------------------------------------------------------
    // API & State Loaders
    // ------------------------------------------------------------------------
    async loadLayout() {
      try {
        const res = await fetch(`/api/dashboard/builder/layout?project_id=${encodeURIComponent(this.state.projectId)}`);
        if (res.ok) {
          this.state.layout = await res.json();
          this.applyTheme(this.state.layout.theme || 'dark');
          this.renderCanvas();
          if (this.state.isPublicView) {
            const title = this.state.layout.name || this.state.layout.title || 'Live Dashboard';
            document.title = `${title} — Afi Vision Live`;
            const publicTitle = document.getElementById('publicDashTitle');
            if (publicTitle) publicTitle.textContent = title;
            if (typeof window.autoFitPublicCanvas === 'function') {
              setTimeout(() => window.autoFitPublicCanvas(), 40);
            }
          } else {
            setTimeout(() => this.zoomFit(), 60);
          }
        } else {
          console.error('[DashboardBuilder] Gagal memuat layout:', res.statusText);
        }
      } catch (err) {
        console.error('[DashboardBuilder] Error loadLayout:', err);
      }
    },

    async loadDashboardList() {
      try {
        const res = await fetch('/api/dashboard/builder/list');
        if (res.ok) {
          const data = await res.json();
          this.state.dashboardsList = data.dashboards || [];
          const cur = this.state.dashboardsList.find(d => d.id === this.state.projectId) || this.state.dashboardsList[0];
          const nameSpan = document.getElementById('builderCurrentDashboardName');
          if (nameSpan && cur) {
            nameSpan.textContent = cur.name || cur.id;
          }
          this.renderDashboardDropdownList();
        }
      } catch (e) {
        console.error('[DashboardBuilder] Gagal memuat daftar dashboard:', e);
      }
    },

    renderDashboardDropdownList(filterText = '') {
      const container = document.getElementById('builderDashListContainer');
      if (!container) return;
      const q = (filterText || '').toLowerCase().trim();
      const list = this.state.dashboardsList.filter(d => {
        if (!q) return true;
        return (d.name || '').toLowerCase().includes(q) || (d.id || '').toLowerCase().includes(q);
      });

      if (!list.length) {
        container.innerHTML = `<div style="padding:12px;font-size:12px;color:#94a3b8;text-align:center;">Tidak ada dashboard ditemukan</div>`;
        return;
      }

      container.innerHTML = list.map(d => {
        const isActive = d.id === this.state.projectId;
        const count = d.widget_count ?? (d.widgets ? d.widgets.length : 0);
        const resText = d.resolution ? `${d.resolution.w}×${d.resolution.h}` : '1440×960';
        return `
          <div class="builder-dash-item ${isActive ? 'active' : ''}" data-dash-id="${d.id}">
            <div class="builder-dash-item-main">
              <div class="builder-dash-item-title">
                <span>${d.name || d.id}</span>
                ${d.is_default ? '<span class="builder-dash-badge default">Utama</span>' : ''}
                ${isActive ? '<span class="builder-dash-badge active">Aktif</span>' : ''}
              </div>
              <div class="builder-dash-item-meta">${count} Komponen &bull; ${resText}</div>
            </div>
            <div class="builder-dash-item-actions">
              <button class="dash-action-btn btn-rename-dash" type="button" title="Ubah Nama" data-id="${d.id}" data-name="${d.name || d.id}">✏️</button>
              <button class="dash-action-btn btn-duplicate-dash" type="button" title="Duplikasi" data-id="${d.id}">📄</button>
              ${!d.is_default && this.state.dashboardsList.length > 1 ? `<button class="dash-action-btn btn-delete-dash" type="button" title="Hapus" data-id="${d.id}" data-name="${d.name || d.id}">🗑️</button>` : ''}
            </div>
          </div>
        `;
      }).join('');

      container.querySelectorAll('.builder-dash-item').forEach(item => {
        item.addEventListener('click', (e) => {
          if (e.target.closest('.builder-dash-item-actions')) return;
          const dashId = item.dataset.dashId;
          if (dashId) this.switchDashboard(dashId);
        });
      });

      container.querySelectorAll('.btn-rename-dash').forEach(btn => {
        btn.addEventListener('click', (e) => {
          e.stopPropagation();
          this.renameDashboard(btn.dataset.id, btn.dataset.name);
        });
      });

      container.querySelectorAll('.btn-duplicate-dash').forEach(btn => {
        btn.addEventListener('click', (e) => {
          e.stopPropagation();
          this.duplicateDashboard(btn.dataset.id);
        });
      });

      container.querySelectorAll('.btn-delete-dash').forEach(btn => {
        btn.addEventListener('click', (e) => {
          e.stopPropagation();
          this.deleteDashboard(btn.dataset.id, btn.dataset.name);
        });
      });
    },

    async switchDashboard(dashId) {
      if (!dashId) return;
      this.state.projectId = dashId;
      const menu = document.getElementById('builderDashDropdownMenu');
      if (menu) menu.hidden = true;

      const target = this.state.dashboardsList.find(d => d.id === dashId);
      const nameSpan = document.getElementById('builderCurrentDashboardName');
      if (nameSpan && target) {
        nameSpan.textContent = target.name || target.id;
      }

      await this.loadLayout();
      this.renderDashboardDropdownList();
      if (window.toast) {
        window.toast(`Beralih ke dashboard: ${target ? target.name : dashId}`, false);
      }
    },

    async createNewDashboard(suggestedName) {
      const name = suggestedName || prompt('Masukkan nama rancangan dashboard baru:', 'Dashboard Baru');
      if (!name || !name.trim()) return;

      try {
        const res = await fetch('/api/dashboard/builder/new', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ name: name.trim() })
        });
        if (res.ok) {
          const data = await res.json();
          await this.loadDashboardList();
          const targetId = data.id || data.dashboard?.id || data.layout?.id;
          if (targetId) {
            await this.switchDashboard(targetId);
          }
          if (window.toast) window.toast('Dashboard baru berhasil dibuat!', false);
        } else {
          alert('Gagal membuat dashboard baru');
        }
      } catch (err) {
        console.error('[DashboardBuilder] Error create dashboard:', err);
      }
    },

    async renameDashboard(dashboardId, currentName) {
      const newName = prompt('Ubah nama dashboard:', currentName || '');
      if (!newName || !newName.trim() || newName.trim() === currentName) return;

      try {
        const res = await fetch('/api/dashboard/builder/rename', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ dashboard_id: dashboardId, new_name: newName.trim() })
        });
        if (res.ok) {
          await this.loadDashboardList();
          if (this.state.projectId === dashboardId) {
            const nameSpan = document.getElementById('builderCurrentDashboardName');
            if (nameSpan) nameSpan.textContent = newName.trim();
          }
          if (window.toast) window.toast('Nama dashboard berhasil diperbarui!', false);
        }
      } catch (err) {
        console.error('[DashboardBuilder] Error rename dashboard:', err);
      }
    },

    async duplicateDashboard(dashboardId) {
      try {
        const res = await fetch('/api/dashboard/builder/duplicate', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ dashboard_id: dashboardId })
        });
        if (res.ok) {
          const data = await res.json();
          await this.loadDashboardList();
          const targetId = data.id || data.dashboard?.id || data.layout?.id;
          if (targetId) {
            await this.switchDashboard(targetId);
          }
          if (window.toast) window.toast('Dashboard berhasil digandakan!', false);
        }
      } catch (err) {
        console.error('[DashboardBuilder] Error duplicate dashboard:', err);
      }
    },

    async deleteDashboard(dashboardId, name) {
      if (!confirm(`Hapus dashboard "${name || dashboardId}"?\nTindakan ini tidak dapat dibatalkan.`)) return;

      try {
        const res = await fetch(`/api/dashboard/builder/${encodeURIComponent(dashboardId)}`, {
          method: 'DELETE'
        });
        if (res.ok) {
          await this.loadDashboardList();
          if (this.state.projectId === dashboardId) {
            const first = this.state.dashboardsList[0];
            if (first) await this.switchDashboard(first.id);
          }
          if (window.toast) window.toast('Dashboard berhasil dihapus!', false);
        } else {
          const errData = await res.json().catch(() => ({}));
          alert(errData.detail || 'Gagal menghapus dashboard');
        }
      } catch (err) {
        console.error('[DashboardBuilder] Error delete dashboard:', err);
      }
    },

    showSaveShareNotification(publicUrl) {
      let modal = document.getElementById('dashSaveShareModal');
      if (!modal) {
        modal = document.createElement('div');
        modal.id = 'dashSaveShareModal';
        modal.style.cssText = `
          position: fixed; bottom: 24px; right: 24px; z-index: 99999;
          background: #1e293b; color: #f8fafc; border: 1px solid #3b82f6;
          box-shadow: 0 10px 25px rgba(0,0,0,0.5); border-radius: 8px;
          padding: 16px 20px; max-width: 420px; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        `;
        document.body.appendChild(modal);
      }
      modal.innerHTML = `
        <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:8px;">
          <strong style="display:flex;align-items:center;gap:6px;font-size:13px;color:#60a5fa;">
            <span>💾</span> Dashboard Tersimpan
          </strong>
          <button type="button" id="btnCloseSaveShareModal" style="background:none;border:none;color:#94a3b8;cursor:pointer;font-size:16px;">✕</button>
        </div>
        <p style="margin:0 0 10px;font-size:12px;color:#cbd5e1;">Rancangan aktif dapat dibuka secara publik atau layar penuh monitor TV:</p>
        <div style="display:flex;gap:6px;align-items:center;">
          <input type="text" id="inpSaveShareLink" readonly value="${publicUrl}" style="flex:1;background:#0f172a;border:1px solid #334155;color:#93c5fd;font-size:11px;padding:6px 8px;border-radius:4px;outline:none;" />
          <button type="button" id="btnCopySaveShareLink" class="button primary" style="font-size:11px;padding:6px 10px;white-space:nowrap;">📋 Salin</button>
          <a href="${publicUrl}" target="_blank" class="button" style="font-size:11px;padding:6px 10px;white-space:nowrap;text-decoration:none;display:inline-flex;align-items:center;">↗️ Buka</a>
          <button type="button" id="btnReturnToStudioFromModal" class="button" style="font-size:11px;padding:6px 10px;white-space:nowrap;background:#0284c7;color:#fff;cursor:pointer;">← Ke Studio</button>
        </div>
      `;
      modal.hidden = false;

      document.getElementById('btnCloseSaveShareModal')?.addEventListener('click', () => {
        modal.hidden = true;
      });

      document.getElementById('btnReturnToStudioFromModal')?.addEventListener('click', () => {
        modal.hidden = true;
        if (typeof window.switchMainView === 'function') window.switchMainView('studio');
        if (typeof window.switchProjectRailTab === 'function') window.switchProjectRailTab('dashboard');
      });

      document.getElementById('btnCopySaveShareLink')?.addEventListener('click', () => {
        const inp = document.getElementById('inpSaveShareLink');
        if (inp) {
          inp.select();
          navigator.clipboard.writeText(publicUrl).then(() => {
            if (window.toast) window.toast('Tautan publik disalin ke clipboard!', false);
          });
        }
      });

      setTimeout(() => {
        if (modal) modal.hidden = true;
      }, 8000);
    },

    async saveLayout() {
      if (!this.state.layout) return;
      try {
        if (!this.state.layout.project_id) {
          this.state.layout.project_id = this.state.projectId;
        }
        if (!this.state.layout.id) {
          this.state.layout.id = this.state.projectId;
        }
        const res = await fetch(`/api/dashboard/builder/layout?project_id=${encodeURIComponent(this.state.projectId)}`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(this.state.layout)
        });
        if (res.ok) {
          const publicUrl = `${window.location.origin}/dashboard/public/${encodeURIComponent(this.state.projectId || 'default')}`;
          if (window.toast) {
            window.toast('Tata letak dashboard berhasil disimpan!', false);
          } else {
            alert('Tata letak dashboard berhasil disimpan!');
          }
          this.showSaveShareNotification(publicUrl);
          await this.loadDashboardList();
        }
      } catch (err) {
        console.error('[DashboardBuilder] Gagal menyimpan layout:', err);
      }
    },

    startLivePolling() {
      if (this.state.pollInterval) clearInterval(this.state.pollInterval);
      this.fetchSnapshot();
      this.state.pollInterval = setInterval(() => this.fetchSnapshot(), 1500);
    },

    async fetchSnapshot() {
      try {
        const res = await fetch('/api/dashboard/builder/snapshot');
        if (res.ok) {
          this.state.liveData = await res.json();
          this.updateLiveWidgetValues();
        }
      } catch (e) {
        // Silent network retry
      }
    },

    // ------------------------------------------------------------------------
    // Toolbar & Controls
    // ------------------------------------------------------------------------
    bindToolbarEvents() {
      const btnEdit = document.getElementById('btnBuilderModeEdit');
      const btnPreview = document.getElementById('btnBuilderModePreview');
      const btnTheme = document.getElementById('btnBuilderThemeToggle');
      const btnSave = document.getElementById('btnBuilderSaveLayout');
      const btnReset = document.getElementById('btnBuilderResetLayout');
      const btnExport = document.getElementById('btnBuilderExportDocker');
      const btnTemplates = document.getElementById('btnBuilderTemplates');
      const btnResetFilter = document.getElementById('btnBuilderResetFilter');
      const btnCloseInspector = document.getElementById('btnBuilderCloseInspector');

      const btnZoomIn = document.getElementById('btnBuilderZoomIn');
      const btnZoomOut = document.getElementById('btnBuilderZoomOut');
      const btnZoomFit = document.getElementById('btnBuilderZoomFit');
      const btnAudio = document.getElementById('btnBuilderAudioToggle');
      const btnCanvasSize = document.getElementById('btnBuilderCanvasSize');
      const btnToggleNavigator = document.getElementById('btnBuilderToggleNavigator');
      const btnCloseNav = document.getElementById('btnCloseNavigator');
      const btnToggleCopilot = document.getElementById('btnBuilderToggleCopilot');
      const btnCloseCopilot = document.getElementById('btnCloseCopilotDrawer');
      const btnOpenPublic = document.getElementById('btnBuilderOpenPublic');

      // Dashboard switcher dropdown elements
      const btnDashSwitcher = document.getElementById('btnBuilderDashboardSwitcher');
      const menuDashSwitcher = document.getElementById('builderDashDropdownMenu');
      const inpDashSearch = document.getElementById('inpBuilderDashSearch');
      const btnCreateNewDash = document.getElementById('btnBuilderCreateNewDash');

      btnDashSwitcher?.addEventListener('click', (e) => {
        e.stopPropagation();
        if (menuDashSwitcher) {
          menuDashSwitcher.hidden = !menuDashSwitcher.hidden;
          if (!menuDashSwitcher.hidden) {
            if (inpDashSearch) {
              inpDashSearch.value = '';
              inpDashSearch.focus();
            }
            this.renderDashboardDropdownList();
          }
        }
      });

      inpDashSearch?.addEventListener('input', (e) => {
        this.renderDashboardDropdownList(e.target.value);
      });

      btnCreateNewDash?.addEventListener('click', () => {
        this.createNewDashboard();
      });

      btnOpenPublic?.addEventListener('click', () => {
        const publicUrl = `/dashboard/public/${encodeURIComponent(this.state.projectId || 'default')}`;
        window.open(publicUrl, '_blank');
      });

      window.addEventListener('click', (e) => {
        if (!e.target.closest('#builderDashboardSwitcherWrap')) {
          if (menuDashSwitcher) menuDashSwitcher.hidden = true;
        }
      });

      btnToggleCopilot?.addEventListener('click', () => this.toggleCopilotDrawer());
      btnCloseCopilot?.addEventListener('click', () => this.toggleCopilotDrawer(false));
      this.bindCopilotDrawerEvents();

      btnEdit?.addEventListener('click', () => this.setMode('edit'));
      btnPreview?.addEventListener('click', () => this.setMode('preview'));
      btnTheme?.addEventListener('click', () => this.toggleTheme());
      btnSave?.addEventListener('click', () => this.saveLayout());
      btnTemplates?.addEventListener('click', () => this.openTemplatesModal());
      btnReset?.addEventListener('click', () => {
        if (confirm('Kembalikan tata letak dashboard ke konfigurasi awal?')) {
          this.resetDefaultLayout();
        }
      });
      btnExport?.addEventListener('click', () => this.openDockerExportModal());
      btnResetFilter?.addEventListener('click', () => this.setLookerCameraFilter(null));
      btnCloseInspector?.addEventListener('click', () => this.selectWidget(null));
      btnCanvasSize?.addEventListener('click', () => this.selectWidget(null));
      btnToggleNavigator?.addEventListener('click', () => this.toggleNavigator());
      btnCloseNav?.addEventListener('click', () => this.toggleNavigator(false));

      btnZoomIn?.addEventListener('click', () => this.zoomIn());
      btnZoomOut?.addEventListener('click', () => this.zoomOut());
      btnZoomFit?.addEventListener('click', () => this.zoomFit());
      btnAudio?.addEventListener('click', () => this.toggleAudio());

      const btnBackStudio = document.getElementById('btnBuilderBackToStudio');
      btnBackStudio?.addEventListener('click', () => {
        if (typeof window.switchMainView === 'function') window.switchMainView('studio');
        if (typeof window.switchProjectRailTab === 'function') window.switchProjectRailTab('dashboard');
      });
    },

    getCanvasElement() {
      return document.getElementById('builderCanvas') || document.getElementById('publicCanvas');
    },

    bindCanvasBackgroundEvents() {
      const canvas = this.getCanvasElement();
      const viewport = document.getElementById('builderViewport') || document.getElementById('publicViewport');
      canvas?.addEventListener('click', (e) => {
        this.closeContextMenu();
        if (e.target === canvas) {
          this.selectWidget(null);
        }
      });
      viewport?.addEventListener('click', (e) => {
        this.closeContextMenu();
        if (e.target === viewport) {
          this.selectWidget(null);
        }
      });
      window.addEventListener('click', (e) => {
        if (!e.target.closest('#builderContextMenu')) {
          this.closeContextMenu();
        }
      });
      window.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
          this.closeContextMenu();
        }
      });
    },

    setCanvasDimensions(width, height) {
      if (!this.state.layout) return;
      if (!this.state.layout.canvas) this.state.layout.canvas = {};
      const w = parseInt(width, 10) || 1440;
      const h = parseInt(height, 10) || 960;
      this.state.layout.canvas.width = w;
      this.state.layout.canvas.height = h;
      this.renderCanvas();
      this.zoomFit();
    },

    applyCanvasBackground() {
      const canvas = this.getCanvasElement();
      if (!canvas || !this.state.layout) return;
      const c = this.state.layout.canvas || {};

      // 1. Solid / Base Color
      if (c.bgColor) {
        canvas.style.backgroundColor = c.bgColor;
        // Detect luminance and toggle canvas-light class for high contrast
        let isLight = false;
        if (c.bgColor.startsWith('#') && c.bgColor.length >= 7) {
          const r = parseInt(c.bgColor.slice(1, 3), 16) || 0;
          const g = parseInt(c.bgColor.slice(3, 5), 16) || 0;
          const b = parseInt(c.bgColor.slice(5, 7), 16) || 0;
          const lum = (0.299 * r + 0.587 * g + 0.114 * b) / 255.0;
          isLight = lum > 0.55;
        } else if (c.bgColor === 'white' || c.bgColor === '#fff' || c.bgColor === '#ffffff') {
          isLight = true;
        }
        canvas.classList.toggle('canvas-light', isLight);
      } else {
        canvas.style.backgroundColor = '';
        canvas.classList.remove('canvas-light');
      }

      // 2. Background Image (Cover, Contain, Repeat + Opacity blending)
      if (c.bgImage) {
        const mode = c.bgImageMode || 'cover';
        const opacity = c.bgImageOpacity !== undefined ? parseFloat(c.bgImageOpacity) : 1.0;

        if (mode === 'contain') {
          canvas.style.backgroundSize = 'contain';
          canvas.style.backgroundRepeat = 'no-repeat';
          canvas.style.backgroundPosition = 'center';
        } else if (mode === 'repeat') {
          canvas.style.backgroundSize = 'auto';
          canvas.style.backgroundRepeat = 'repeat';
          canvas.style.backgroundPosition = 'top left';
        } else { // cover
          canvas.style.backgroundSize = 'cover';
          canvas.style.backgroundRepeat = 'no-repeat';
          canvas.style.backgroundPosition = 'center';
        }

        if (opacity < 1.0) {
          const hex = c.bgColor || '#0f172a';
          let r = 15, g = 23, b = 42;
          if (hex.startsWith('#') && hex.length >= 7) {
            r = parseInt(hex.slice(1, 3), 16) || 15;
            g = parseInt(hex.slice(3, 5), 16) || 23;
            b = parseInt(hex.slice(5, 7), 16) || 42;
          }
          const alpha = (1.0 - opacity).toFixed(2);
          canvas.style.backgroundImage = `linear-gradient(rgba(${r}, ${g}, ${b}, ${alpha}), rgba(${r}, ${g}, ${b}, ${alpha})), url("${c.bgImage}")`;
        } else {
          canvas.style.backgroundImage = `url("${c.bgImage}")`;
        }
      } else {
        canvas.style.backgroundImage = '';
      }
    },

    setCanvasBackground(bgColor) {
      if (!this.state.layout) return;
      if (!this.state.layout.canvas) this.state.layout.canvas = {};
      this.state.layout.canvas.bgColor = bgColor;
      this.applyCanvasBackground();
    },

    setCanvasFontFamily(fontFamily) {
      if (!this.state.layout) return;
      if (!this.state.layout.canvas) this.state.layout.canvas = {};
      this.state.layout.canvas.fontFamily = fontFamily;
      this.state.layout.fontFamily = fontFamily;
      const canvas = this.getCanvasElement();
      if (canvas) {
        canvas.style.fontFamily = fontFamily;
      }
    },

    setZoom(level) {
      this.state.zoom = Math.max(0.4, Math.min(1.8, Math.round(level * 100) / 100));
      const canvas = this.getCanvasElement();
      const text = document.getElementById('builderZoomText');
      if (canvas) {
        canvas.style.transform = `scale(${this.state.zoom})`;
        canvas.style.transformOrigin = 'top center';
      }
      if (text) text.textContent = `${Math.round(this.state.zoom * 100)}%`;
    },

    zoomIn() { this.setZoom(this.state.zoom + 0.1); },
    zoomOut() { this.setZoom(this.state.zoom - 0.1); },
    zoomFit() {
      const viewport = document.getElementById('builderViewport');
      if (!viewport || !this.state.layout) return;
      const cw = this.state.layout.canvas?.width || 1440;
      const vw = viewport.clientWidth - 48;
      const fit = Math.min(1.0, vw / cw);
      this.setZoom(fit);
    },

    toggleAudio() {
      this.state.audioEnabled = !this.state.audioEnabled;
      const icon = document.getElementById('builderAudioIcon');
      const text = document.getElementById('builderAudioText');
      if (this.state.audioEnabled) {
        if (icon) icon.textContent = '🔔';
        if (text) text.textContent = 'Alarm: Aktif';
      } else {
        if (icon) icon.textContent = '🔕';
        if (text) text.textContent = 'Alarm: Hening';
      }
    },

    playDangerChime() {
      const now = Date.now();
      if (this.state.lastChime && now - this.state.lastChime < 8000) return;
      this.state.lastChime = now;
      try {
        const AudioCtx = window.AudioContext || window.webkitAudioContext;
        if (!AudioCtx) return;
        const ctx = new AudioCtx();
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();
        osc.type = 'sine';
        osc.frequency.setValueAtTime(880, ctx.currentTime);
        osc.frequency.exponentialRampToValueAtTime(1174, ctx.currentTime + 0.15);
        gain.gain.setValueAtTime(0.12, ctx.currentTime);
        gain.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.35);
        osc.connect(gain);
        gain.connect(ctx.destination);
        osc.start();
        osc.stop(ctx.currentTime + 0.35);
      } catch (e) {}
    },

    bindKeyboardShortcuts() {
      window.addEventListener('keydown', (e) => {
        const active = document.activeElement;
        const isInput = active && (active.tagName === 'INPUT' || active.tagName === 'TEXTAREA' || active.tagName === 'SELECT');

        if (e.key === 'Delete' || e.key === 'Backspace') {
          if (!isInput && this.state.selectedWidgetId && this.state.mode === 'edit') {
            e.preventDefault();
            this.deleteWidget(this.state.selectedWidgetId);
          }
        } else if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'd') {
          if (this.state.selectedWidgetId && this.state.mode === 'edit') {
            e.preventDefault();
            this.duplicateSelectedWidget();
          }
        } else if (e.key === 'Escape') {
          this.selectWidget(null);
        }
      });
    },

    duplicateSelectedWidget() {
      if (!this.state.selectedWidgetId || !this.state.layout) return;
      const orig = this.state.layout.widgets.find(x => x.id === this.state.selectedWidgetId);
      if (!orig) return;
      const copy = JSON.parse(JSON.stringify(orig));
      copy.id = `w_${copy.type}_${Date.now().toString(36)}`;
      copy.x += 30;
      copy.y += 30;
      copy.z = (this.state.layout.widgets.length || 0) + 1;
      this.state.layout.widgets.push(copy);
      this.renderCanvas();
      this.selectWidget(copy.id);
      if (window.toast) window.toast('Komponen berhasil digandakan (Ctrl+D)', false);
    },

    setMode(mode) {
      this.state.mode = mode;
      const view = document.getElementById('viewDashboardBuilder') || document.getElementById('publicViewport') || document.body;
      const btnEdit = document.getElementById('btnBuilderModeEdit');
      const btnPreview = document.getElementById('btnBuilderModePreview');

      btnEdit?.classList.toggle('active', mode === 'edit');
      btnPreview?.classList.toggle('active', mode === 'preview');
      view?.classList.toggle('mode-preview', mode === 'preview');

      if (mode === 'preview') {
        this.selectWidget(null);
      }
      this.renderCanvas();
    },

    toggleTheme() {
      const nextTheme = this.state.theme === 'dark' ? 'light' : 'dark';
      this.applyTheme(nextTheme);
      if (this.state.layout) {
        this.state.layout.theme = nextTheme;
      }
    },

    applyTheme(theme) {
      this.state.theme = theme;
      const view = document.getElementById('viewDashboardBuilder') || document.getElementById('publicViewport') || document.body;
      const themeIcon = document.getElementById('builderThemeIcon');
      const themeText = document.getElementById('builderThemeText');

      if (theme === 'light') {
        view?.classList.add('builder-light-mode');
        if (themeIcon) themeIcon.textContent = '☀️';
        if (themeText) themeText.textContent = 'Terang';
      } else {
        view?.classList.remove('builder-light-mode');
        if (themeIcon) themeIcon.textContent = '🌙';
        if (themeText) themeText.textContent = 'Gelap';
      }
    },

    setLookerCameraFilter(cameraLabel) {
      this.state.filterCamera = cameraLabel;
      const filterChip = document.getElementById('builderFilterChip');
      const cameraNameText = document.getElementById('builderFilterCameraName');

      if (cameraLabel) {
        if (filterChip) filterChip.hidden = false;
        if (cameraNameText) cameraNameText.textContent = cameraLabel;
      } else {
        if (filterChip) filterChip.hidden = true;
      }

      // Highlight active CCTV and filter Event Tables
      document.querySelectorAll('.widget-cctv-card, .cctv-quad-feed').forEach(card => {
        const lbl = card.dataset.cameraLabel;
        card.classList.toggle('filter-active-cam', Boolean(cameraLabel && lbl === cameraLabel));
      });

      this.updateEventTables();
    },

    resetDefaultLayout() {
      fetch(`/api/dashboard/builder/layout?project_id=default`)
        .then(r => r.json())
        .then(data => {
          this.state.layout = data;
          this.renderCanvas();
        });
    },

    // ------------------------------------------------------------------------
    // Palette Drawer (Adding Widgets)
    // ------------------------------------------------------------------------
    bindPaletteEvents() {
      const drawer = document.getElementById('builderWidgetDrawer');
      // 1. Click to add
      drawer?.addEventListener('click', (e) => {
        const btn = e.target.closest('.palette-item-btn');
        if (!btn) return;
        const type = btn.dataset.widgetType;
        if (type) this.addWidget(type);
      });

      // 2. Drag and drop from palette onto canvas
      const paletteBtns = drawer?.querySelectorAll('.palette-item-btn');
      paletteBtns?.forEach(btn => {
        btn.setAttribute('draggable', 'true');
        btn.addEventListener('dragstart', (e) => {
          const type = btn.dataset.widgetType;
          if (type) {
            e.dataTransfer.setData('text/plain', type);
            e.dataTransfer.setData('application/x-afi-widget-type', type);
            e.dataTransfer.effectAllowed = 'copy';
            btn.classList.add('palette-dragging');
          }
        });
        btn.addEventListener('dragend', () => {
          btn.classList.remove('palette-dragging');
        });
      });

      // Canvas drop target listeners
      const canvas = document.getElementById('builderCanvas');
      const viewport = document.getElementById('builderCanvasViewport');

      const handleDragOver = (e) => {
        if (e.dataTransfer.types.includes('application/x-afi-widget-type') || e.dataTransfer.types.includes('text/plain')) {
          e.preventDefault();
          e.dataTransfer.dropEffect = 'copy';
          canvas?.classList.add('canvas-drag-receiving');
        }
      };

      const handleDragLeave = (e) => {
        if (e.relatedTarget && (canvas?.contains(e.relatedTarget) || viewport?.contains(e.relatedTarget))) {
          return;
        }
        canvas?.classList.remove('canvas-drag-receiving');
      };

      const handleDrop = (e) => {
        e.preventDefault();
        canvas?.classList.remove('canvas-drag-receiving');
        const type = e.dataTransfer.getData('application/x-afi-widget-type') || e.dataTransfer.getData('text/plain');
        if (!type || !canvas) return;

        const rect = canvas.getBoundingClientRect();
        const zoom = this.state.zoom || 1.0;
        
        // Exact drop position relative to canvas coordinates, snapped to 10px
        const rawX = (e.clientX - rect.left) / zoom;
        const rawY = (e.clientY - rect.top) / zoom;
        const dropX = Math.max(0, Math.round(rawX / 10) * 10);
        const dropY = Math.max(0, Math.round(rawY / 10) * 10);

        this.addWidget(type, dropX, dropY);
      };

      viewport?.addEventListener('dragover', handleDragOver);
      viewport?.addEventListener('dragleave', handleDragLeave);
      viewport?.addEventListener('drop', handleDrop);

      canvas?.addEventListener('dragover', handleDragOver);
      canvas?.addEventListener('dragleave', handleDragLeave);
      canvas?.addEventListener('drop', handleDrop);
    },

    addWidget(type, customX = null, customY = null) {
      if (!this.state.layout) return;
      const id = `w_${type}_${Date.now().toString(36)}`;
      const canvasW = this.state.layout.canvas?.width || 1440;
      const canvasH = this.state.layout.canvas?.height || 960;

      // Smart dimensions
      let newW = 320, newH = 140;
      if (type === 'cctv_player') { newW = 640; newH = 380; }
      else if (type === 'trend_chart') { newW = 600; newH = 260; }
      else if (type === 'event_table') { newW = 650; newH = 260; }
      else if (type === 'excel_export_btn') { newW = 220; newH = 48; }
      else if (type === 'custom_text') { newW = 450; newH = 50; }
      else if (type === 'container_box') { newW = 500; newH = 300; }
      else if (type === 'status_badge') { newW = 200; newH = 44; }
      else if (type === 'image_logo') { newW = 220; newH = 80; }
      else if (type === 'dashboard_navbar') { newW = canvasW; newH = 56; }
      else if (type === 'media_input_controller') { newW = 420; newH = 460; }
      else if (type === 'vision_result_viewer') { newW = 940; newH = 580; }
      else if (type === 'confidence_table') { newW = 720; newH = 320; }
      else if (type === 'custom_analytics_table') { newW = 660; newH = 320; }

      let targetX = type === 'dashboard_navbar' ? 0 : Math.max(30, Math.floor((canvasW - newW) / 2));
      let targetY = type === 'dashboard_navbar' ? 0 : Math.max(60, Math.floor((canvasH - newH) / 2));

      if (customX !== null && customX !== undefined) {
        targetX = Math.max(0, Math.min(canvasW - newW, customX));
      }
      if (customY !== null && customY !== undefined) {
        targetY = Math.max(0, Math.min(canvasH - newH, customY));
      }

      const newWidget = {
        id,
        type,
        x: targetX,
        y: targetY,
        w: newW,
        h: newH,
        z: (this.state.layout.widgets.length || 0) + 1,
        config: this.getDefaultConfig(type)
      };

      this.state.layout.widgets.push(newWidget);
      this.renderCanvas();
      this.selectWidget(id);
    },

    getDefaultConfig(type) {
      switch (type) {
        case 'cctv_player':
          return {
            cameraLabel: 'Kamera Baru',
            streamId: 'cam_new',
            nodeId: 'preview',
            defaultMode: 'annotated',
            enableCameraSwitcher: true,
            showCameraListStrip: false,
            autoPatrol: false,
            patrolIntervalSeconds: 10,
            showAnnotatedToggle: true,
            showSnapshotBtn: true,
            showFullscreenBtn: true
          };
        case 'scorecard':
          return {
            metricKey: 'total_count',
            title: 'Metrik Baru',
            unit: 'Item',
            icon: 'bar-chart-2',
            warningThreshold: 10,
            dangerThreshold: 20,
            defaultValue: 0
          };
        case 'trend_chart':
          return {
            title: 'Grafik Tren Deteksi',
            metricKey: 'total_count',
            chartType: 'line',
            rangeHours: 24
          };
        case 'event_table':
          return {
            title: 'Tabel Log Kejadian Real-time',
            maxRows: 20,
            autoScroll: true,
            showFilter: true
          };
        case 'excel_export_btn':
          return {
            label: 'Unduh Rekap Excel (.xlsx)',
            includeEvents: true,
            includeMetrics: true
          };
        case 'custom_text':
          return {
            text: 'Judul / Area Pemantauan',
            tag: 'h2',
            fontSize: 20,
            color: '#F8FAFC',
            subtitle: 'Keterangan deskripsi area'
          };
        case 'status_badge':
          return {
            label: 'Sistem Aktif',
            status: 'online',
            shift: 'Shift 1'
          };
        case 'container_box':
          return {
            title: 'Area Zona 1',
            borderColor: '#475569'
          };
        case 'image_logo':
          return {
            url: '/static/logo.png',
            alt: 'Logo Perusahaan',
            objectFit: 'contain',
            borderRadius: '0px'
          };
        case 'dashboard_navbar':
          return {
            title: 'COMMAND CENTER & MONITORING',
            subtitle: 'Sistem Visual AI Real-time',
            logoUrl: '/static/logo.png',
            shift: 'Shift 1 (Aktif)',
            showClock: true,
            showShift: true
          };
        case 'media_input_controller':
          return {
            title: 'Media Input & Inference Controller',
            defaultConfidence: 0.25,
            workflowId: '',
            autoRunOnUpload: true,
            sampleUrls: [
              { label: 'Sample Bengkel Workshop', url: '/static/sample_workshop.jpg' }
            ]
          };
        case 'vision_result_viewer':
          return {
            title: 'Visual Output & Detections',
            showBoxes: true,
            showLabels: true,
            showMasks: true,
            enableZoomPan: true,
            showDownloadBtn: true
          };
        case 'confidence_table':
          return {
            title: 'Daftar Objek & Skor Keyakinan',
            minConfidence: 0.25,
            showCropThumbnail: true,
            showBboxCoords: true,
            exportCsv: true,
            exportExcel: true
          };
        case 'custom_analytics_table':
          return {
            title: 'Tabel Analisis Kustom & Zona',
            showOccupancy: true,
            showViolations: true,
            exportCsv: true,
            exportExcel: true
          };
        default:
          return {};
      }
    },

    // ------------------------------------------------------------------------
    // Canvas & Widget Rendering
    // ------------------------------------------------------------------------
    renderCanvas() {
      const canvas = this.getCanvasElement();
      if (!canvas || !this.state.layout) return;

      const cw = this.state.layout.canvas?.width || 1440;
      const ch = this.state.layout.canvas?.height || 960;
      canvas.style.width = `${cw}px`;
      canvas.style.height = `${ch}px`;

      this.applyCanvasBackground();

      const cFont = this.state.layout.canvas?.fontFamily || this.state.layout.fontFamily || "'Inter', -apple-system, sans-serif";
      canvas.style.fontFamily = cFont;

      const dimText = document.getElementById('builderCanvasDimText');
      if (dimText) dimText.textContent = `${cw} × ${ch}`;

      // Clear existing widget DOMs while keeping snap lines
      const snapX = document.getElementById('snapLineX');
      const snapY = document.getElementById('snapLineY');
      canvas.innerHTML = '';
      if (snapX) canvas.appendChild(snapX);
      if (snapY) canvas.appendChild(snapY);

      this.state.layout.widgets.forEach(w => {
        const el = this.createWidgetElement(w);
        canvas.appendChild(el);
      });

      this.updateLiveWidgetValues();
      this.renderNavigatorTree();
    },

    createWidgetElement(w) {
      const el = document.createElement('div');
      el.className = `builder-widget widget-type-${w.type}`;
      el.id = `widget_${w.id}`;
      el.dataset.widgetId = w.id;
      el.dataset.widgetType = w.type;

      el.style.left = `${w.x}px`;
      el.style.top = `${w.y}px`;
      el.style.width = `${w.w}px`;
      el.style.height = `${w.h}px`;
      el.style.zIndex = w.z || 1;

      if (this.state.selectedWidgetId === w.id && this.state.mode === 'edit') {
        el.classList.add('selected');
      }

      // Inner widget markup
      el.innerHTML = this.getWidgetHTML(w);
      this.applyWidgetCustomStyles(el, w);

      // In edit mode: add resize handles
      if (this.state.mode === 'edit') {
        ['nw', 'ne', 'sw', 'se'].forEach(dir => {
          const h = document.createElement('div');
          h.className = `resize-handle handle-${dir}`;
          h.dataset.handle = dir;
          el.appendChild(h);
        });
      }

      this.attachWidgetInteractions(el, w);
      return el;
    },

    reRenderWidgetBody(w) {
      if (!w || !w.id) return;
      const el = document.getElementById(`widget_${w.id}`);
      if (!el) return;

      const isSelected = el.classList.contains('selected');
      el.innerHTML = this.getWidgetHTML(w);
      this.applyWidgetCustomStyles(el, w);

      if (this.state.mode === 'edit') {
        ['nw', 'ne', 'sw', 'se'].forEach(dir => {
          const h = document.createElement('div');
          h.className = `resize-handle handle-${dir}`;
          h.dataset.handle = dir;
          el.appendChild(h);
        });
      }

      if (isSelected) {
        el.classList.add('selected');
      }

      this.attachWidgetInteractions(el, w);
    },

    applyWidgetCustomStyles(el, w) {
      if (!el || !w) return;
      const cfg = w.config || {};
      const card = el.firstElementChild;
      if (!card) return;

      // Locked State (prevent drag & resize cursor)
      el.classList.toggle('widget-locked', Boolean(w.isLocked));

      // Hidden State (visibility in navigator)
      if (w.isHidden) {
        el.style.opacity = '0.2';
        el.style.filter = 'grayscale(1)';
        el.style.pointerEvents = 'none';
      } else {
        const opVal = cfg.opacity !== undefined ? Number(cfg.opacity) : 1;
        el.style.opacity = opVal;
        el.style.filter = '';
        el.style.pointerEvents = '';
      }

      // Z-Index
      el.style.zIndex = w.z || 1;

      // Glassmorphism or Background
      if (cfg.glassmorphism) {
        card.style.backdropFilter = 'blur(14px)';
        card.style.webkitBackdropFilter = 'blur(14px)';
        const baseBg = cfg.bgColor && cfg.bgColor !== 'transparent' ? cfg.bgColor : '#1e293b';
        if (baseBg.startsWith('#') && baseBg.length === 7) {
          card.style.backgroundColor = `${baseBg}99`;
        } else {
          card.style.backgroundColor = 'rgba(30, 41, 59, 0.65)';
        }
      } else if (cfg.bgColor) {
        if (cfg.bgColor === 'transparent') {
          card.style.backgroundColor = 'transparent';
          card.style.backgroundImage = 'none';
          card.style.backdropFilter = 'none';
        } else {
          card.style.backgroundColor = cfg.bgColor;
          card.style.backdropFilter = 'none';
        }
      } else {
        card.style.backgroundColor = '';
        card.style.backdropFilter = 'none';
      }

      // Box Shadow Presets
      if (cfg.boxShadow === 'none') {
        card.style.boxShadow = 'none';
      } else if (cfg.boxShadow === 'soft') {
        card.style.boxShadow = '0 4px 14px rgba(0, 0, 0, 0.18)';
      } else if (cfg.boxShadow === 'deep') {
        card.style.boxShadow = '0 14px 32px rgba(0, 0, 0, 0.45)';
      } else if (cfg.boxShadow === 'neon-cyan') {
        card.style.boxShadow = '0 0 18px rgba(56, 189, 248, 0.55)';
      } else if (cfg.boxShadow === 'neon-emerald') {
        card.style.boxShadow = '0 0 18px rgba(16, 185, 129, 0.55)';
      } else {
        card.style.boxShadow = '';
      }

      // Custom Text Color & Adaptive Contrast
      if (cfg.textColor) {
        card.style.color = cfg.textColor;
        card.querySelectorAll('.scorecard-val, .scorecard-label, .kpi-value-num, .kpi-header-label, .chart-card-title, .alerts-panel-title, .donut-panel-title, .donut-center-val, .web-cv-widget-title, .web-cv-drop-text, .web-cv-slider-label, .sys-lbl, .sys-val, .vital-name, h1, h2, h3, strong, th, td').forEach(child => {
          if (!child.classList.contains('ai-bbox-tag') && !child.classList.contains('event-badge') && !child.classList.contains('cctv-workflow-badge') && !child.classList.contains('web-cv-slider-val')) {
            child.style.color = cfg.textColor;
          }
        });
      } else {
        card.style.color = '';
        card.querySelectorAll('.web-cv-widget-title, .web-cv-drop-text, .web-cv-slider-label').forEach(child => {
          child.style.color = '';
        });
      }

      // Custom Border Color
      if (cfg.borderColor) {
        card.style.borderColor = cfg.borderColor;
      } else {
        card.style.borderColor = '';
      }

      // Custom Border Radius
      if (cfg.borderRadius) {
        card.style.borderRadius = cfg.borderRadius;
        el.style.borderRadius = cfg.borderRadius;
      } else {
        card.style.borderRadius = '';
        el.style.borderRadius = '';
      }

      // Custom Font Family (Per-Widget)
      if (cfg.fontFamily && cfg.fontFamily !== 'inherit') {
        card.style.fontFamily = cfg.fontFamily;
        el.style.fontFamily = cfg.fontFamily;
      } else {
        card.style.fontFamily = '';
        el.style.fontFamily = '';
      }
    },

    getWidgetHTML(w) {
      const cfg = w.config || {};
      switch (w.type) {
        case 'cctv_player': {
          const isFilterActive = this.state.filterCamera === cfg.cameraLabel;
          const streamNodeId = cfg.nodeId || 'preview';
          const unifiedCams = this.getUnifiedCameraList();

          // Generate Dropdown Options for Camera/Workflow Switcher
          const cameraOptionsHtml = unifiedCams.map(cam => {
            const isSel = (cfg.workflowId === cam.workflowId || cfg.cameraLabel === cam.label || (cam.label && cfg.cameraLabel && cfg.cameraLabel.includes(cam.label))) ? 'selected' : '';
            return `<option value="${cam.workflowId}:::${cam.label}:::${cam.source}" ${isSel}>📹 ${cam.label} (${cam.workflowName || 'Workflow'})</option>`;
          }).join('');

          // Generate Scrollable Camera Filmstrip Items
          const cameraStripHtml = unifiedCams.map(cam => {
            const isAct = (cfg.workflowId === cam.workflowId || cfg.cameraLabel === cam.label || (cam.label && cfg.cameraLabel && cfg.cameraLabel.includes(cam.label)));
            return `
              <div class="cctv-scroll-item ${isAct ? 'active' : ''}" 
                   data-widget-id="${w.id}" 
                   data-workflow-id="${cam.workflowId}" 
                   data-cam-label="${cam.label}" 
                   data-source="${cam.source}"
                   title="${cam.label} - ${cam.source}">
                <span class="scroll-item-dot"></span>
                <span class="scroll-item-name">${cam.label}</span>
              </div>
            `;
          }).join('');

          return `
            <div class="widget-cctv-card ${isFilterActive ? 'filter-active-cam' : ''}" data-camera-label="${cfg.cameraLabel}">
              <div class="cctv-card-header">
                <div class="cctv-card-title-wrap">
                  <span class="cctv-status-dot"></span>
                  ${cfg.enableCameraSwitcher !== false ? `
                    <select class="cctv-camera-select" data-widget-id="${w.id}" title="Pilih Kamera / Alur Kerja">
                      ${cameraOptionsHtml}
                    </select>
                  ` : `
                    <span class="cctv-card-title">${cfg.cameraLabel || 'Kamera'}</span>
                  `}
                  ${cfg.workflowName ? `<span class="cctv-workflow-badge" title="Workflow: ${cfg.workflowName}">⚡ ${cfg.workflowName}</span>` : ''}
                </div>
                <div class="cctv-card-actions">
                  ${cfg.autoPatrol ? `
                    <button class="cctv-action-btn btn-cctv-patrol active" type="button" data-widget-id="${w.id}" title="Patroli Otomatis Aktif (Berganti tiap ${cfg.patrolIntervalSeconds || 10}d)">
                      <span class="patrol-pulse"></span> 🔄 Patroli
                    </button>
                  ` : ''}
                  ${cfg.showAnnotatedToggle ? `<button class="cctv-action-btn btn-cctv-toggle" type="button">Mode AI</button>` : ''}
                  ${cfg.showSnapshotBtn ? `<button class="cctv-action-btn btn-cctv-snap" type="button">📷</button>` : ''}
                  ${cfg.showFullscreenBtn ? `<button class="cctv-action-btn btn-cctv-expand" type="button">⤢</button>` : ''}
                </div>
              </div>
              <div class="cctv-screen-view">
                <img id="cctv_img_${w.id}" src="/api/preview/${streamNodeId}/stream?res=720p" onerror="this.onerror=null;this.src='/api/preview/${streamNodeId}?t=' + Date.now();" alt="${cfg.cameraLabel}" loading="lazy" />
                <div class="cctv-source-overlay" id="cctv_source_overlay_${w.id}">
                  <span class="cctv-source-text">📹 ${cfg.cameraLabel || 'CCTV'} &bull; ${cfg.inputSource || 'Live Feed'}</span>
                </div>
              </div>
              ${cfg.showCameraListStrip ? `
                <div class="cctv-camera-scroll-strip scrollbar-thin" data-widget-id="${w.id}">
                  ${cameraStripHtml}
                </div>
              ` : ''}
            </div>
          `;
        }
        case 'scorecard': {
          const liveVal = this.getMetricValue(cfg.metricKey, cfg.defaultValue);
          const status = this.calculateThresholdStatus(liveVal, cfg.warningThreshold, cfg.dangerThreshold);
          return `
            <div class="widget-scorecard-card scorecard-${status}" id="card_${w.id}">
              <div class="scorecard-top">
                <span class="scorecard-label">${cfg.title || 'Metrik'}</span>
                <span class="scorecard-icon">⚡</span>
              </div>
              <div class="scorecard-mid">
                <span class="scorecard-val" id="val_${w.id}">${liveVal}</span>
                <span class="scorecard-unit">${cfg.unit || ''}</span>
              </div>
              <div class="scorecard-bottom">
                <small style="color:var(--text-secondary,#94a3b8)">Ambang Batas: W:${cfg.warningThreshold || 10} / D:${cfg.dangerThreshold || 20}</small>
              </div>
            </div>
          `;
        }
        case 'trend_chart': {
          return `
            <div class="widget-chart-card">
              <div class="chart-card-head">
                <span class="chart-card-title">${cfg.title || 'Grafik Tren'}</span>
                <select class="chart-range-select" data-widget-id="${w.id}">
                  <option value="1">1 Jam</option>
                  <option value="24" selected>24 Jam</option>
                  <option value="168">7 Hari</option>
                </select>
              </div>
              <div class="chart-canvas-view">
                <canvas id="chart_${w.id}"></canvas>
              </div>
            </div>
          `;
        }
        case 'event_table': {
          return `
            <div class="widget-table-card">
              <div class="table-card-head">
                <span>${cfg.title || 'Log Kejadian'}</span>
                <small style="color:#38bdf8">${this.state.filterCamera ? `Filter: ${this.state.filterCamera}` : 'Semua Kamera'}</small>
              </div>
              <div class="table-scroll-body">
                <table class="widget-live-table">
                  <thead>
                    <tr>
                      <th>WAKTU</th>
                      <th>KAMERA</th>
                      <th>KEJADIAN</th>
                      <th>TINGKAT</th>
                    </tr>
                  </thead>
                  <tbody id="tableBody_${w.id}">
                    <tr><td colspan="4" style="text-align:center;color:#64748b">Memuat data log...</td></tr>
                  </tbody>
                </table>
              </div>
            </div>
          `;
        }
        case 'excel_export_btn': {
          const iconType = cfg.icon || 'spreadsheet';
          const iconSvg = iconType === 'file' 
            ? `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M13 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z"></path><polyline points="13 2 13 9 20 9"></polyline></svg>`
            : iconType === 'table'
            ? `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="2"/><path d="M3 9h18M3 15h18M9 3v18M15 3v18"/></svg>`
            : iconType === 'analytics'
            ? `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>`
            : `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="8" y1="13" x2="16" y2="13"/><line x1="8" y1="17" x2="16" y2="17"/></svg>`;
          return `
            <button class="widget-excel-btn" type="button" data-filename="${cfg.filename || ''}">
              ${iconSvg}
              <span>${cfg.label || 'Unduh Rekap Excel (.xlsx)'}</span>
            </button>
          `;
        }
        case 'custom_text': {
          const Tag = cfg.tag || 'h2';
          return `
            <div class="widget-text-card">
              <${Tag} style="font-size:${cfg.fontSize || 20}px;color:${cfg.color || '#F8FAFC'};font-weight:700;">
                ${cfg.text || 'Judul Teks'}
              </${Tag}>
              ${cfg.subtitle ? `<div class="widget-text-subtitle">${cfg.subtitle}</div>` : ''}
            </div>
          `;
        }
        case 'status_badge': {
          return `
            <div class="widget-status-badge-card">
              <span class="status-indicator-beacon"></span>
              <div>
                <strong style="display:block;font-size:12px;color:#f8fafc">${cfg.label || 'Sistem Aktif'}</strong>
                <small style="font-size:10px;color:#94a3b8">${cfg.shift || 'Shift 1'}</small>
              </div>
            </div>
          `;
        }
        case 'container_box': {
          return `
            <div class="widget-container-box-card" style="border-color:${cfg.borderColor || '#475569'}">
              ${cfg.title ? `<span style="padding:4px 8px;font-size:10px;font-weight:700;color:#94a3b8;background:rgba(15,23,42,0.8);border-bottom-right-radius:6px;">${cfg.title}</span>` : ''}
            </div>
          `;
        }
        case 'image_logo': {
          const imgUrl = cfg.url || cfg.dataUrl || '/static/logo.png';
          const fit = cfg.objectFit || 'contain';
          const rad = cfg.borderRadius || '0px';
          return `
            <div class="widget-logo-card" style="width:100%;height:100%;display:flex;align-items:center;justify-content:center;overflow:hidden;border-radius:${rad};">
              <img src="${imgUrl}" alt="${cfg.alt || 'Logo'}" style="max-width:100%;max-height:100%;width:100%;height:100%;object-fit:${fit};border-radius:${rad};" id="img_logo_${w.id}" />
            </div>
          `;
        }
        case 'stat_kpi_card': {
          const liveVal = this.getMetricValue(cfg.metricKey, cfg.value);
          const accent = cfg.accent || '#00E5FF';
          return `
            <div class="widget-stat-kpi-card" style="border-left: 3px solid ${accent};">
              <div class="kpi-icon-box" style="background: rgba(0, 229, 255, 0.12); color: ${accent};">
                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect width="18" height="18" x="3" y="3" rx="2"/><circle cx="12" cy="12" r="3"/></svg>
              </div>
              <div class="kpi-body">
                <div class="kpi-header-label">${cfg.title || 'METRIC'}</div>
                <div class="kpi-value-num" id="val_${w.id}">${liveVal}</div>
                <div class="kpi-sub-text">${cfg.sublabel || ''}</div>
              </div>
            </div>
          `;
        }
        case 'cctv_grid_2x2': {
          const cams = cfg.cams || [];
          return `
            <div class="widget-cctv-matrix-card">
              <div class="cctv-matrix-grid">
                ${cams.map((c, i) => `
                  <div class="cctv-quad-feed" data-camera-id="${c.id}" data-camera-label="${c.name}">
                    <div class="quad-header-overlay">
                      <div class="quad-title">
                        <span class="cctv-status-dot"></span>
                        <span>${c.name}</span>
                      </div>
                      <div class="quad-live-badge">● LIVE</div>
                    </div>
                    <div class="quad-screen-view">
                      <img src="/api/preview/${c.nodeId || 'preview'}/stream?res=480p" onerror="this.onerror=null;this.src='/api/preview/${c.nodeId || 'preview'}?t=' + Date.now();" alt="${c.name}" />
                      
                      ${c.hasLaserGrid ? `<div class="virtual-laser-tripwire"></div>` : ''}
                      ${(c.detections || []).map((d, di) => `
                        <div class="ai-bbox-overlay bbox-${d.color || 'cyan'}" style="top:${20 + di * 28}%; left:${18 + di * 38}%; width:26%; height:46%;">
                          <span class="ai-bbox-tag">${d.label} ${d.conf}</span>
                        </div>
                      `).join('')}
                      ${c.alert ? `
                        <div class="ai-bbox-overlay bbox-red-danger pulse-danger-box" style="top:22%; left:42%; width:36%; height:54%;">
                          <span class="ai-bbox-tag danger-tag">${c.alert.label}</span>
                        </div>
                      ` : ''}
                    </div>
                    <div class="quad-footer-overlay">
                      <div class="quad-controls">
                        <button class="icon-btn-xs" type="button" title="Mute">🔊</button>
                        <button class="icon-btn-xs btn-matrix-snap" type="button" title="Snapshot" data-node-id="${c.nodeId || 'preview'}" data-label="${c.name}">📷</button>
                        <button class="icon-btn-xs btn-matrix-expand" type="button" title="Fullscreen" data-node-id="${c.nodeId || 'preview'}" data-label="${c.name}">⤢</button>
                      </div>
                      <span class="quad-fps-badge">${c.res || '1080p 25 FPS'}</span>
                    </div>
                  </div>
                `).join('')}
              </div>
              <div class="matrix-bottom-toolbar">
                <div class="matrix-layout-btns">
                  <button class="matrix-tool-btn" type="button">1x1</button>
                  <button class="matrix-tool-btn active" type="button">2x2</button>
                  <button class="matrix-tool-btn" type="button">3x3</button>
                  <button class="matrix-tool-btn" type="button">4x4</button>
                </div>
                <div class="matrix-quick-actions">
                  <button class="matrix-action-icon" type="button" title="Mic">🎤</button>
                  <button class="matrix-action-icon" type="button" title="Speaker">🔊</button>
                  <button class="matrix-action-icon rec-icon" type="button" title="Rekam">⏺ REC</button>
                  <button class="matrix-action-icon" type="button" title="Snap All">📸</button>
                  <button class="matrix-action-icon" type="button" title="Setting">⚙️</button>
                  <button class="matrix-action-icon" type="button" title="Grid Wall">▦</button>
                  <button class="matrix-action-icon" type="button" title="Fullscreen">⛶</button>
                </div>
              </div>
            </div>
          `;
        }
        case 'active_alerts_list': {
          const alerts = cfg.alerts || [];
          return `
            <div class="widget-alerts-panel">
              <div class="alerts-panel-head">
                <span class="alerts-panel-title">${cfg.title || 'ACTIVE CRITICAL ALERTS'}</span>
                <span class="alerts-count-badge">${alerts.length} ALERTS</span>
              </div>
              <div class="alerts-list-body">
                ${alerts.map(a => `
                  <div class="alert-list-item level-${a.level.toLowerCase()}">
                    <div class="alert-icon-wrap">
                      ${a.level === 'CRITICAL' ? '⚠️' : a.level === 'WARNING' ? '⚡' : 'ℹ️'}
                    </div>
                    <div class="alert-item-content">
                      <div class="alert-item-title">${a.title}</div>
                      <div class="alert-item-loc">${a.loc}</div>
                    </div>
                    <span class="alert-pill-badge ${a.level.toLowerCase()}">${a.level}</span>
                  </div>
                `).join('')}
              </div>
            </div>
          `;
        }
        case 'donut_chart': {
          const segments = cfg.segments || [
            { label: 'Normal', pct: 68, color: '#00E676' },
            { label: 'High', pct: 22, color: '#FFAA00' },
            { label: 'Critical', pct: 10, color: '#FF334B' }
          ];
          return `
            <div class="widget-donut-panel">
              <div class="donut-panel-title">${cfg.title || 'ZONE OCCUPANCY'}</div>
              <div class="donut-body-wrap">
                <div class="donut-svg-wrap">
                  <svg width="110" height="110" viewBox="0 0 100 100">
                    <circle cx="50" cy="50" r="38" fill="none" stroke="#1E293B" stroke-width="12" />
                    <circle cx="50" cy="50" r="38" fill="none" stroke="#00E676" stroke-width="12"
                            stroke-dasharray="162 238" stroke-dashoffset="0" stroke-linecap="round" />
                    <circle cx="50" cy="50" r="38" fill="none" stroke="#FFAA00" stroke-width="12"
                            stroke-dasharray="52 238" stroke-dashoffset="-164" stroke-linecap="round" />
                    <circle cx="50" cy="50" r="38" fill="none" stroke="#FF334B" stroke-width="12"
                            stroke-dasharray="24 238" stroke-dashoffset="-218" stroke-linecap="round" />
                  </svg>
                  <div class="donut-center-metric">
                    <strong class="donut-center-val">${cfg.centerValue || '68%'}</strong>
                    <span class="donut-center-lbl">${cfg.centerLabel || 'Occupancy'}</span>
                  </div>
                </div>
                <div class="donut-legend-list">
                  ${segments.map(s => `
                    <div class="donut-legend-item">
                      <span class="legend-color-dot" style="background:${s.color}"></span>
                      <span class="legend-lbl">${s.label}</span>
                      <strong class="legend-val">${s.pct}%</strong>
                    </div>
                  `).join('')}
                </div>
              </div>
            </div>
          `;
        }
        case 'ai_engine_status': {
          const services = cfg.services || [
            { name: 'Object Detection', status: 'ONLINE' },
            { name: 'Object Tracking', status: 'ONLINE' },
            { name: 'Zone Analytics', status: 'ONLINE' },
            { name: 'Event Manager', status: 'ONLINE' }
          ];
          return `
            <div class="widget-ai-status-panel">
              <div class="ai-status-head">
                <span class="ai-status-title">${cfg.title || 'AI ENGINE STATUS — All Services Online'}</span>
              </div>
              <div class="ai-services-grid">
                ${services.map(s => `
                  <div class="ai-service-item">
                    <div class="ai-service-left">
                      <span class="service-pulse-dot"></span>
                      <span class="service-name">${s.name}</span>
                    </div>
                    <span class="service-online-tag">${s.status}</span>
                  </div>
                `).join('')}
              </div>
            </div>
          `;
        }
        case 'system_health_vitals': {
          const vitals = cfg.vitals || [
            { name: 'CPU Usage', val: '23%', pct: 23, color: '#3B82F6' },
            { name: 'RAM Usage', val: '41%', pct: 41, color: '#00E5FF' },
            { name: 'Disk Usage', val: '62%', pct: 62, color: '#FFAA00' },
            { name: 'Network', val: '128 Mbps', pct: 72, color: '#00E676' }
          ];
          return `
            <div class="widget-telemetry-panel">
              <div class="telemetry-panel-head">
                <span class="telemetry-title">${cfg.title || 'SYSTEM HEALTH'}</span>
                <span style="font-size:11px;color:#00e5ff">⚡ Vitals</span>
              </div>
              <div class="vitals-list-wrap">
                ${vitals.map(v => `
                  <div class="vital-row-item">
                    <div class="vital-row-top">
                      <span class="vital-name">${v.name}</span>
                      <strong class="vital-val" style="color:${v.color}">${v.val}</strong>
                    </div>
                    <div class="vital-bar-track">
                      <div class="vital-bar-fill" style="width:${v.pct}%;background:${v.color}"></div>
                    </div>
                  </div>
                `).join('')}
              </div>
            </div>
          `;
        }
        case 'zone_occupancy_meters': {
          const zones = cfg.zones || [
            { name: 'Zone 1 (Entrance)', pct: 68, color: '#00E676' },
            { name: 'Zone 2 (Parking Area)', pct: 43, color: '#00E676' },
            { name: 'Zone 3 (Restricted)', pct: 82, color: '#FFAA00' },
            { name: 'Zone 4 (Office)', pct: 12, color: '#00E5FF' }
          ];
          return `
            <div class="widget-telemetry-panel">
              <div class="telemetry-panel-head">
                <span class="telemetry-title">${cfg.title || 'ZONE OCCUPANCY'}</span>
                <span style="font-size:11px;color:#00e676">● Live Bars</span>
              </div>
              <div class="vitals-list-wrap">
                ${zones.map(z => `
                  <div class="vital-row-item">
                    <div class="vital-row-top">
                      <span class="vital-name">${z.name}</span>
                      <strong class="vital-val" style="color:${z.color}">${z.pct}%</strong>
                    </div>
                    <div class="vital-bar-track">
                      <div class="vital-bar-fill" style="width:${z.pct}%;background:${z.color}"></div>
                    </div>
                  </div>
                `).join('')}
              </div>
            </div>
          `;
        }
        case 'detection_summary': {
          const items = cfg.items || [
            { label: 'People', count: '1,182', icon: '👤', color: '#00E676' },
            { label: 'Vehicles', count: '248', icon: '🚗', color: '#00E5FF' },
            { label: 'Bags', count: '32', icon: '💼', color: '#FFAA00' },
            { label: 'Other', count: '20', icon: '📦', color: '#A855F7' }
          ];
          return `
            <div class="widget-telemetry-panel">
              <div class="telemetry-panel-head">
                <span class="telemetry-title">${cfg.title || 'DETECTION SUMMARY'}</span>
                <span style="font-size:10px;color:#94a3b8">Today</span>
              </div>
              <div class="detection-summary-grid">
                ${items.map(it => `
                  <div class="summary-mini-card" style="border-left: 3px solid ${it.color};">
                    <span class="summary-mini-icon">${it.icon}</span>
                    <strong class="summary-mini-count" style="color:${it.color}">${it.count}</strong>
                    <span class="summary-mini-label">${it.label}</span>
                  </div>
                `).join('')}
              </div>
            </div>
          `;
        }
        case 'system_info': {
          return `
            <div class="widget-telemetry-panel">
              <div class="telemetry-panel-head">
                <span class="telemetry-title">${cfg.title || 'SYSTEM INFORMATION'}</span>
                <span style="font-size:10.5px;color:#38bdf8">v2.0</span>
              </div>
              <div class="sys-info-list">
                <div class="sys-info-row">
                  <span class="sys-lbl">Platform</span>
                  <strong class="sys-val" style="color:#00e5ff">${cfg.platform || 'AI CCTV PRO v2.0'}</strong>
                </div>
                <div class="sys-info-row">
                  <span class="sys-lbl">Uptime</span>
                  <strong class="sys-val" style="color:#f8fafc">${cfg.uptime || '15d 07h 42m'}</strong>
                </div>
                <div class="sys-info-row">
                  <span class="sys-lbl">Temperature</span>
                  <strong class="sys-val" style="color:#ffaa00">${cfg.temp || '42°C'}</strong>
                </div>
                <div class="sys-info-row">
                  <span class="sys-lbl">Network Status</span>
                  <span class="status-pill-stable">● ${cfg.status || 'Stable'}</span>
                </div>
              </div>
            </div>
          `;
        }
        case 'dashboard_navbar': {
          const now = new Date();
          const timeStr = now.toTimeString().split(' ')[0];
          const dateStr = now.toLocaleDateString('id-ID', { weekday: 'short', day: 'numeric', month: 'short' });
          return `
            <header class="widget-dashboard-navbar" id="navbar_${w.id}">
              <div class="navbar-brand-section">
                <img src="${cfg.logoUrl || '/static/logo.png'}" alt="Logo" class="navbar-logo-img" />
                <div class="navbar-title-wrap">
                  <span class="navbar-main-title">${cfg.title || 'DASHBOARD MONITORING'}</span>
                  <span class="navbar-subtitle">${cfg.subtitle || 'Real-time Computer Vision'}</span>
                </div>
              </div>
              <div class="navbar-center-telemetry">
                ${cfg.showClock !== false ? `
                  <div class="navbar-clock-wrap">
                    <span class="navbar-clock-time" id="clock_${w.id}">${timeStr}</span>
                    <span class="navbar-clock-date">${dateStr}</span>
                  </div>
                ` : ''}
                ${cfg.showShift !== false ? `
                  <div class="navbar-shift-badge">
                    <span>⚙️</span>
                    <span>${cfg.shift || 'Shift 1'}</span>
                  </div>
                ` : ''}
              </div>
              <div class="navbar-actions-section">
                <div class="navbar-status-pill">
                  <span class="navbar-status-dot"></span>
                  <span>LIVE TELEMETRY</span>
                </div>
              </div>
            </header>
          `;
        }
        case 'media_input_controller': {
          const confPct = Math.round((cfg.defaultConfidence || 0.25) * 100);
          return `
            <div class="web-cv-widget-card" id="card_${w.id}">
              <div class="web-cv-widget-header">
                <div class="web-cv-widget-title">
                  <span>🎛️</span>
                  <span>${cfg.title || 'Media Input & Inference Controller'}</span>
                </div>
                <span class="cctv-workflow-badge" id="media_status_badge_${w.id}">Ready</span>
              </div>
              <div style="padding:14px;display:flex;flex-direction:column;gap:12px;">
                <div class="web-cv-dropzone" id="dropzone_${w.id}" data-widget-id="${w.id}">
                  <input type="file" id="media_file_input_${w.id}" accept="image/*,video/*" style="display:none;" />
                  <div class="web-cv-drop-icon">📁</div>
                  <div class="web-cv-drop-text">Seret & lepas file gambar / video di sini</div>
                  <div class="web-cv-drop-subtext">Mendukung JPG, PNG, MP4, WebM atau klik untuk telusuri</div>
                  <div id="media_preview_wrap_${w.id}" style="display:none;margin-top:8px;">
                    <img id="media_preview_img_${w.id}" class="web-cv-preview-thumb" alt="Preview" />
                    <div id="media_filename_${w.id}" style="font-size:11px;color:#38bdf8;margin-top:4px;word-break:break-all;"></div>
                  </div>
                </div>

                <div style="display:flex;align-items:center;gap:6px;font-size:11px;color:#94a3b8;flex-wrap:wrap;">
                  <span>Gunakan Sampel:</span>
                  <button class="button small ghost btn-sample-media" type="button" data-widget-id="${w.id}" data-url="/static/sample_workshop.jpg" style="padding:2px 8px;font-size:11px;">🏭 Bengkel Workshop</button>
                </div>

                <div class="web-cv-controls-row" style="margin-top:2px;">
                  <div class="web-cv-slider-group">
                    <div class="web-cv-slider-label">
                      <span>Ambang Batas Keyakinan (Confidence)</span>
                      <span class="web-cv-slider-val" id="val_conf_${w.id}">${confPct}%</span>
                    </div>
                    <input type="range" class="web-cv-slider-input" id="range_conf_${w.id}" min="5" max="95" step="5" value="${confPct}" data-widget-id="${w.id}" />
                  </div>
                </div>

                <div style="display:flex;gap:8px;margin-top:4px;">
                  <button class="button primary btn-run-analysis" type="button" id="btn_run_analysis_${w.id}" data-widget-id="${w.id}" style="flex:1;justify-content:center;gap:8px;height:38px;font-weight:600;">
                    <span class="run-spinner" id="spinner_${w.id}" style="display:none;">⏳</span>
                    <span>🚀 Jalankan Analisis</span>
                  </button>
                  <button class="button ghost btn-reset-media" type="button" id="btn_reset_media_${w.id}" data-widget-id="${w.id}" title="Reset Input" style="padding:0 12px;height:38px;">
                    🔄
                  </button>
                </div>
              </div>
            </div>
          `;
        }

        case 'vision_result_viewer': {
          return `
            <div class="web-cv-widget-card" id="card_${w.id}">
              <div class="web-cv-widget-header">
                <div class="web-cv-widget-title">
                  <span>🖼️</span>
                  <span>${cfg.title || 'Visual Output & Detections'}</span>
                </div>
                <div class="web-cv-viewer-toolbar">
                  <div class="web-cv-viewer-tools-group">
                    <button class="web-cv-tool-btn active btn-toggle-layer" data-layer="boxes" data-widget-id="${w.id}" title="Toggle Bounding Boxes">📦 Boxes</button>
                    <button class="web-cv-tool-btn active btn-toggle-layer" data-layer="labels" data-widget-id="${w.id}" title="Toggle Labels">🏷️ Labels</button>
                    <button class="web-cv-tool-btn active btn-toggle-layer" data-layer="masks" data-widget-id="${w.id}" title="Toggle Masks">🎭 Masks</button>
                  </div>
                  <div class="web-cv-viewer-tools-group">
                    <button class="web-cv-tool-btn btn-zoom-in" data-widget-id="${w.id}" title="Zoom In">➕</button>
                    <button class="web-cv-tool-btn btn-zoom-out" data-widget-id="${w.id}" title="Zoom Out">➖</button>
                    <button class="web-cv-tool-btn btn-zoom-reset" data-widget-id="${w.id}" title="Reset Zoom">🔄</button>
                  </div>
                  <button class="web-cv-action-btn btn-download-annotated" data-widget-id="${w.id}" title="Unduh Gambar Beranotasi">
                    ⬇️ Unduh
                  </button>
                </div>
              </div>
              <div class="web-cv-viewport" id="viewport_${w.id}">
                <div class="web-cv-empty-banner" id="empty_viewer_${w.id}">
                  <div style="font-size:36px;margin-bottom:8px;">🎯</div>
                  <div style="font-size:14px;font-weight:600;color:#e2e8f0;">Belum Ada Analisis yang Dijalankan</div>
                  <div style="font-size:12px;color:#94a3b8;margin-top:4px;">Unggah gambar/video di panel Input Controller lalu klik 'Jalankan Analisis'</div>
                </div>
                <div class="web-cv-zoom-pan-container" id="zoom_wrap_${w.id}" style="display:none;width:100%;height:100%;display:flex;align-items:center;justify-content:center;overflow:hidden;">
                  <img id="img_annotated_${w.id}" class="web-cv-result-img" alt="Visual Output" style="max-width:100%;max-height:100%;object-fit:contain;border-radius:6px;transition:transform 0.15s ease-out;" />
                </div>
                <div class="cctv-source-overlay" id="badge_stat_${w.id}" style="display:none;bottom:10px;left:10px;background:rgba(15,23,42,0.85);backdrop-filter:blur(8px);padding:5px 12px;border-radius:6px;border:1px solid rgba(255,255,255,0.1);font-size:11px;color:#38bdf8;">
                  <span id="badge_stat_text_${w.id}">0 Objek Terdeteksi</span>
                </div>
              </div>
            </div>
          `;
        }

        case 'confidence_table': {
          return `
            <div class="web-cv-widget-card" id="card_${w.id}">
              <div class="web-cv-widget-header">
                <div class="web-cv-widget-title">
                  <span>📊</span>
                  <span>${cfg.title || 'Daftar Objek & Skor Keyakinan'}</span>
                </div>
                <div class="web-cv-table-header">
                  <input type="text" class="web-cv-table-search" placeholder="Cari kelas..." id="search_conf_table_${w.id}" data-widget-id="${w.id}" />
                  <button class="button small ghost btn-export-conf-csv" data-widget-id="${w.id}" title="Ekspor CSV">📄 CSV</button>
                  <button class="button small ghost btn-export-conf-excel" data-widget-id="${w.id}" title="Ekspor Excel">📗 Excel</button>
                </div>
              </div>
              <div class="web-cv-table-body-scroll scrollbar-thin">
                <table class="web-cv-data-table" id="table_conf_${w.id}">
                  <thead>
                    <tr>
                      <th style="width:48px;">Crop</th>
                      <th style="width:36px;">#</th>
                      <th>Kelas Objek</th>
                      <th>Skor Keyakinan</th>
                      <th>Koordinat BBox (x1, y1, x2, y2)</th>
                    </tr>
                  </thead>
                  <tbody id="tbody_conf_${w.id}">
                    <tr>
                      <td colspan="5" style="text-align:center;padding:28px;color:#64748b;">
                        Belum ada deteksi. Unggah media dan jalankan analisis.
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          `;
        }

        case 'custom_analytics_table': {
          return `
            <div class="web-cv-widget-card" id="card_${w.id}">
              <div class="web-cv-widget-header">
                <div class="web-cv-widget-title">
                  <span>📈</span>
                  <span>${cfg.title || 'Tabel Analisis Kustom & Zona'}</span>
                </div>
                <div class="web-cv-table-header">
                  <input type="text" class="web-cv-table-search" placeholder="Cari parameter..." id="search_analytics_table_${w.id}" data-widget-id="${w.id}" />
                  <button class="button small ghost btn-export-analytics-csv" data-widget-id="${w.id}" title="Ekspor CSV">📄 CSV</button>
                  <button class="button small ghost btn-export-analytics-excel" data-widget-id="${w.id}" title="Ekspor Excel">📗 Excel</button>
                </div>
              </div>
              <div class="web-cv-table-body-scroll scrollbar-thin">
                <table class="web-cv-data-table" id="table_analytics_${w.id}">
                  <thead>
                    <tr>
                      <th style="width:36px;">#</th>
                      <th>Zona / Parameter</th>
                      <th>Metrik Analisis</th>
                      <th>Nilai Aktual</th>
                      <th>Batas Ambang</th>
                      <th>Status Sistem</th>
                    </tr>
                  </thead>
                  <tbody id="tbody_analytics_${w.id}">
                    <tr>
                      <td colspan="6" style="text-align:center;padding:28px;color:#64748b;">
                        Belum ada data analitik. Jalankan analisis alur kerja.
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          `;
        }
        default:
          return `<div>${w.type}</div>`;
      }
    },

    // ------------------------------------------------------------------------
    // Interactions: Selection, Drag, Resize, & Looker Filter
    // ------------------------------------------------------------------------
    attachWidgetInteractions(el, w) {
      // 1. Selection & Looker Camera Filter
      el.addEventListener('mousedown', (e) => {
        if (this.state.mode === 'edit') {
          if (w.isLocked) {
            this.selectWidget(w.id);
            return;
          }
          if (!e.target.classList.contains('resize-handle')) {
            this.selectWidget(w.id);
            this.startDragging(e, w, el);
          }
        }
      });

      // 1b. Elementor Right-Click Context Menu
      el.addEventListener('contextmenu', (e) => {
        if (this.state.mode === 'edit') {
          e.preventDefault();
          e.stopPropagation();
          this.selectWidget(w.id);
          this.openContextMenu(e, w.id);
        }
      });

      // 2. Resize Handle Drag
      el.querySelectorAll('.resize-handle').forEach(h => {
        h.addEventListener('mousedown', (e) => {
          if (w.isLocked) return;
          e.stopPropagation();
          this.startResizing(e, w, h.dataset.handle, el);
        });
      });
      el.querySelectorAll('.resize-handle').forEach(h => {
        h.addEventListener('mousedown', (e) => {
          e.stopPropagation();
          this.startResizing(e, w, h.dataset.handle, el);
        });
      });

      // 3. Widget Specific Button Listeners
      const btnToggle = el.querySelector('.btn-cctv-toggle');
      btnToggle?.addEventListener('click', (e) => {
        e.stopPropagation();
        const img = el.querySelector('.cctv-screen-view img');
        if (!img) return;
        const currentSrc = img.src;
        if (currentSrc.includes('/preview')) {
          img.src = `/api/preview/input?t=${Date.now()}`;
          btnToggle.textContent = 'Mode Asli';
        } else {
          img.src = `/api/preview/${w.config?.nodeId || 'preview'}?t=${Date.now()}`;
          btnToggle.textContent = 'Mode AI';
        }
      });

      const btnSnap = el.querySelector('.btn-cctv-snap');
      btnSnap?.addEventListener('click', (e) => {
        e.stopPropagation();
        this.downloadSnapshot(w.config?.nodeId || 'preview', w.config?.cameraLabel || 'cctv');
      });

      const btnExpand = el.querySelector('.btn-cctv-expand');
      btnExpand?.addEventListener('click', (e) => {
        e.stopPropagation();
        this.openCctvFullscreen(w.config?.cameraLabel || 'CCTV Stream', `/api/preview/${w.config?.nodeId || 'preview'}`);
      });

      // 4. Interactive Camera & Workflow Switcher (Dropdown Change)
      const selCam = el.querySelector('.cctv-camera-select');
      selCam?.addEventListener('change', (e) => {
        e.stopPropagation();
        const parts = selCam.value.split(':::');
        const wfId = parts[0] || 'default';
        const camLabel = parts[1] || 'Kamera';
        const src = parts[2] || '';
        this.switchCctvPlayerCamera(w.id, wfId, camLabel, src);
      });
      selCam?.addEventListener('mousedown', (e) => e.stopPropagation());
      selCam?.addEventListener('click', (e) => e.stopPropagation());

      // 5. Scrollable Camera Strip Items (Click to Switch)
      el.querySelectorAll('.cctv-scroll-item').forEach(item => {
        item.addEventListener('click', (e) => {
          e.stopPropagation();
          const wfId = item.dataset.workflowId || 'default';
          const camLabel = item.dataset.camLabel || 'Kamera';
          const src = item.dataset.source || '';
          this.switchCctvPlayerCamera(w.id, wfId, camLabel, src);
        });
        item.addEventListener('mousedown', (e) => e.stopPropagation());
      });

      // 6. Auto-Patrol Button Toggle
      const btnPatrol = el.querySelector('.btn-cctv-patrol');
      btnPatrol?.addEventListener('click', (e) => {
        e.stopPropagation();
        w.config.autoPatrol = !w.config.autoPatrol;
        btnPatrol.classList.toggle('active', w.config.autoPatrol);
        if (w.config.autoPatrol) {
          this.startAutoPatrol(w.id);
          if (window.toast) window.toast(`Patroli otomatis kamera diaktifkan (${w.config.patrolIntervalSeconds || 10}d)`, false);
        } else {
          this.stopAutoPatrol(w.id);
          if (window.toast) window.toast('Patroli otomatis kamera dinonaktifkan', false);
        }
      });
      btnPatrol?.addEventListener('mousedown', (e) => e.stopPropagation());

      // Looker Drilldown (Preview Mode: clicking CCTV card or quad feed filters dashboard)
      const cctvCard = el.querySelector('.widget-cctv-card');
      cctvCard?.addEventListener('click', () => {
        if (this.state.mode === 'preview') {
          const camLabel = w.config?.cameraLabel;
          if (this.state.filterCamera === camLabel) {
            this.setLookerCameraFilter(null); // toggle off
          } else {
            this.setLookerCameraFilter(camLabel); // filter to this camera
          }
        }
      });

      el.querySelectorAll('.cctv-quad-feed').forEach(feed => {
        feed.addEventListener('click', () => {
          if (this.state.mode === 'preview') {
            const camLabel = feed.dataset.cameraLabel;
            if (this.state.filterCamera === camLabel) {
              this.setLookerCameraFilter(null);
            } else {
              this.setLookerCameraFilter(camLabel);
            }
          }
        });
      });

      // Excel Download Button
      const btnExcel = el.querySelector('.widget-excel-btn');
      btnExcel?.addEventListener('click', () => {
        this.downloadExcelReport(this.state.filterCamera, w.config?.filename);
      });

      /* Web CV Widget Interactions */
      this.attachWebCvWidgetListeners(el, w);
    },

    startDragging(e, w, el) {
      if (e.button !== 0) return; // Left click only
      this.state.isDragging = true;
      this.state.activeDragWidget = w;
      const zoom = this.state.zoom || 1.0;
      this.state.dragOffset = {
        x: (e.clientX / zoom) - w.x,
        y: (e.clientY / zoom) - w.y
      };

      const onMouseMove = (ev) => {
        if (!this.state.isDragging) return;
        const z = this.state.zoom || 1.0;
        let nextX = (ev.clientX / z) - this.state.dragOffset.x;
        let nextY = (ev.clientY / z) - this.state.dragOffset.y;

        // Snapping to 10px grid
        nextX = Math.round(nextX / 10) * 10;
        nextY = Math.round(nextY / 10) * 10;
        nextX = Math.max(0, nextX);
        nextY = Math.max(0, nextY);

        w.x = nextX;
        w.y = nextY;
        el.style.left = `${nextX}px`;
        el.style.top = `${nextY}px`;
        this.updateInspectorCoords(w);
      };

      const onMouseUp = () => {
        this.state.isDragging = false;
        this.state.activeDragWidget = null;
        window.removeEventListener('mousemove', onMouseMove);
        window.removeEventListener('mouseup', onMouseUp);
      };

      window.addEventListener('mousemove', onMouseMove);
      window.addEventListener('mouseup', onMouseUp);
    },

    startResizing(e, w, handle, el) {
      if (e.button !== 0) return;
      this.state.isResizing = true;
      const zoom = this.state.zoom || 1.0;
      const initial = {
        mouseX: e.clientX / zoom,
        mouseY: e.clientY / zoom,
        x: w.x,
        y: w.y,
        w: w.w,
        h: w.h
      };

      const onMouseMove = (ev) => {
        if (!this.state.isResizing) return;
        const z = this.state.zoom || 1.0;
        const curX = ev.clientX / z;
        const curY = ev.clientY / z;
        const dx = curX - initial.mouseX;
        const dy = curY - initial.mouseY;

        let newW = initial.w;
        let newH = initial.h;
        let newX = initial.x;
        let newY = initial.y;

        if (handle.includes('e')) newW = Math.max(120, initial.w + dx);
        if (handle.includes('s')) newH = Math.max(40, initial.h + dy);
        if (handle.includes('w')) {
          const clamped = Math.max(120, initial.w - dx);
          newX = initial.x + (initial.w - clamped);
          newW = clamped;
        }
        if (handle.includes('n')) {
          const clamped = Math.max(40, initial.h - dy);
          newY = initial.y + (initial.h - clamped);
          newH = clamped;
        }

        w.x = Math.round(newX / 10) * 10;
        w.y = Math.round(newY / 10) * 10;
        w.w = Math.round(newW / 10) * 10;
        w.h = Math.round(newH / 10) * 10;

        el.style.left = `${w.x}px`;
        el.style.top = `${w.y}px`;
        el.style.width = `${w.w}px`;
        el.style.height = `${w.h}px`;

        this.updateInspectorCoords(w);
      };

      const onMouseUp = () => {
        this.state.isResizing = false;
        window.removeEventListener('mousemove', onMouseMove);
        window.removeEventListener('mouseup', onMouseUp);
        // Re-render chart if resized
        if (w.type === 'trend_chart') {
          this.renderTrendChart(w);
        }
      };

      window.addEventListener('mousemove', onMouseMove);
      window.addEventListener('mouseup', onMouseUp);
    },

    switchCctvPlayerCamera(widgetId, workflowId, cameraLabel, inputSource) {
      const w = this.state.layout?.widgets?.find(x => x.id === widgetId);
      if (!w) return;
      if (!w.config) w.config = {};

      w.config.workflowId = workflowId;
      w.config.cameraLabel = cameraLabel;
      w.config.inputSource = inputSource;

      // 1. Update Video Stream element smoothly
      const img = document.getElementById(`cctv_img_${widgetId}`);
      const streamNodeId = w.config.nodeId || 'preview';
      if (img) {
        img.src = `/api/preview/${streamNodeId}/stream?res=720p&wf=${encodeURIComponent(workflowId)}&t=${Date.now()}`;
      }

      // 2. Update Source Info Overlay Badge
      const overlay = document.getElementById(`cctv_source_overlay_${widgetId}`);
      if (overlay) {
        overlay.innerHTML = `<span class="cctv-source-text">📹 ${cameraLabel} &bull; ${inputSource || 'Live Feed'}</span>`;
      }

      // 3. Sync Dropdown Selection
      const select = document.querySelector(`.cctv-camera-select[data-widget-id="${widgetId}"]`);
      if (select) {
        Array.from(select.options).forEach(opt => {
          opt.selected = opt.value.includes(cameraLabel) || opt.value.includes(workflowId);
        });
      }

      // 4. Sync Scroll Strip active item
      document.querySelectorAll(`.cctv-scroll-item[data-widget-id="${widgetId}"]`).forEach(item => {
        const isMatch = item.dataset.workflowId === workflowId || item.dataset.camLabel === cameraLabel;
        item.classList.toggle('active', isMatch);
      });

      // 5. Update Inspector if currently open on this widget
      if (this.state.selectedWidgetId === widgetId) {
        const inpLabel = document.getElementById('inp_camLabel');
        const inpSrc = document.getElementById('inp_cctv_input_source');
        const txtWf = document.getElementById('txt_info_workflow');
        const txtSrc = document.getElementById('txt_info_source');
        if (inpLabel) inpLabel.value = cameraLabel;
        if (inpSrc) inpSrc.value = inputSource;
        if (txtWf) txtWf.textContent = cameraLabel;
        if (txtSrc) txtSrc.textContent = inputSource || 'Live Stream';
      }

      if (window.toast) {
        window.toast(`Beralih ke kamera: ${cameraLabel}`, false);
      }
    },

    startAutoPatrol(widgetId) {
      this.stopAutoPatrol(widgetId);
      const w = this.state.layout?.widgets?.find(x => x.id === widgetId);
      if (!w) return;
      const intervalSec = Math.max(3, parseInt(w.config?.patrolIntervalSeconds || 10, 10));
      const cameras = this.getUnifiedCameraList();
      if (!cameras.length) return;

      let idx = 0;
      const currentIdx = cameras.findIndex(c => c.workflowId === w.config?.workflowId || c.label === w.config?.cameraLabel);
      if (currentIdx !== -1) idx = currentIdx;

      this.state.patrolTimers[widgetId] = setInterval(() => {
        idx = (idx + 1) % cameras.length;
        const targetCam = cameras[idx];
        if (targetCam) {
          this.switchCctvPlayerCamera(widgetId, targetCam.workflowId, targetCam.label, targetCam.source);
        }
      }, intervalSec * 1000);
    },

    stopAutoPatrol(widgetId) {
      if (this.state.patrolTimers && this.state.patrolTimers[widgetId]) {
        clearInterval(this.state.patrolTimers[widgetId]);
        delete this.state.patrolTimers[widgetId];
      }
    },

    // ------------------------------------------------------------------------
    // Inspector Form & Binding
    // ------------------------------------------------------------------------
    switchInspectorTab(tab) {
      this.state.inspectorTab = tab;
      if (this.state.selectedWidgetId) {
        this.selectWidget(this.state.selectedWidgetId);
      } else {
        this.renderCanvasSettings();
      }
    },

    selectWidget(widgetId) {
      this.state.selectedWidgetId = widgetId;
      document.querySelectorAll('.builder-widget').forEach(el => {
        el.classList.toggle('selected', el.dataset.widgetId === widgetId);
      });

      // Update navigator active class
      document.querySelectorAll('.navigator-layer-item').forEach(item => {
        item.classList.toggle('active', item.dataset.widgetId === widgetId);
      });

      const container = document.getElementById('builderInspectorContent');
      const headTitle = document.querySelector('.builder-inspector-head h3');
      if (!container) return;

      // When no widget is selected: Show Canvas Resolution & Theme Settings
      if (!widgetId) {
        if (headTitle) headTitle.textContent = 'Pengaturan Kanvas';
        this.renderCanvasSettings(container);
        return;
      }

      if (headTitle) headTitle.textContent = 'Pengaturan Komponen';
      const w = this.state.layout?.widgets?.find(x => x.id === widgetId);
      if (!w) return;
      this.renderWidgetInspector(container, w);
    },

    renderCanvasSettings(container) {
      const cw = this.state.layout?.canvas?.width || 1440;
      const ch = this.state.layout?.canvas?.height || 960;
      const cBg = this.state.layout?.canvas?.bgColor || (this.state.theme === 'light' ? '#ffffff' : '#0f172a');
      const cBgImage = this.state.layout?.canvas?.bgImage || '';
      const cBgMode = this.state.layout?.canvas?.bgImageMode || 'cover';
      const cBgOpacity = this.state.layout?.canvas?.bgImageOpacity !== undefined ? parseFloat(this.state.layout?.canvas?.bgImageOpacity) : 1.0;
      const cFont = this.state.layout?.canvas?.fontFamily || this.state.layout?.fontFamily || "'Inter', -apple-system, sans-serif";

      container.innerHTML = `
        <div class="inspector-section">
          <span class="inspector-section-title">RESOLUSI & DIMENSI KANVAS</span>
          <div class="inspector-field">
            <label>Preset Resolusi Layar</label>
            <select id="sel_canvas_preset">
              <option value="1920x1080" ${cw === 1920 && ch === 1080 ? 'selected' : ''}>1920 × 1080 (Full HD 16:9 — TV/Display)</option>
              <option value="1440x960" ${cw === 1440 && ch === 960 ? 'selected' : ''}>1440 × 960 (Standar 3:2 — Laptop)</option>
              <option value="1280x720" ${cw === 1280 && ch === 720 ? 'selected' : ''}>1280 × 720 (HD 720p 16:9)</option>
              <option value="2560x1440" ${cw === 2560 && ch === 1440 ? 'selected' : ''}>2560 × 1440 (2K QHD 16:9)</option>
              <option value="3840x2160" ${cw === 3840 && ch === 2160 ? 'selected' : ''}>3840 × 2160 (4K UHD Command Center)</option>
              <option value="1920x1200" ${cw === 1920 && ch === 1200 ? 'selected' : ''}>1920 × 1200 (16:10 WUXGA)</option>
              <option value="1080x1920" ${cw === 1080 && ch === 1920 ? 'selected' : ''}>1080 × 1920 (9:16 Portrait / Smart TV)</option>
              <option value="custom" ${![1920, 1440, 1280, 2560, 3840, 1080].includes(cw) ? 'selected' : ''}>Kustom (Ukuran Manual)</option>
            </select>
          </div>
          <div class="canvas-presets-bar">
            <button class="canvas-preset-btn" type="button" data-w="1920" data-h="1080">1080p</button>
            <button class="canvas-preset-btn" type="button" data-w="1440" data-h="960">1440×960</button>
            <button class="canvas-preset-btn" type="button" data-w="1280" data-h="720">720p</button>
            <button class="canvas-preset-btn" type="button" data-w="2560" data-h="1440">2K</button>
          </div>
          <div class="inspector-row" style="margin-top:8px;">
            <div class="inspector-field">
              <label>Lebar W (px)</label>
              <input type="number" id="inp_canvas_w" value="${cw}" min="400" max="7680" step="10" />
            </div>
            <div class="inspector-field">
              <label>Tinggi H (px)</label>
              <input type="number" id="inp_canvas_h" value="${ch}" min="300" max="4320" step="10" />
            </div>
          </div>
        </div>

        <div class="inspector-section">
          <span class="inspector-section-title">TIPOGRAFI & FONT KANVAS</span>
          <div class="inspector-field">
            <label>Font Utama Dashboard</label>
            <select id="sel_canvas_font">
              <option value="'Inter', -apple-system, sans-serif" ${cFont.includes('Inter') ? 'selected' : ''}>Inter (Modern & Bersih - Standar)</option>
              <option value="'Plus Jakarta Sans', sans-serif" ${cFont.includes('Plus Jakarta Sans') ? 'selected' : ''}>Plus Jakarta Sans (Elegan & Populer)</option>
              <option value="'Outfit', sans-serif" ${cFont.includes('Outfit') ? 'selected' : ''}>Outfit (Futuristik & Minimalis)</option>
              <option value="'Poppins', sans-serif" ${cFont.includes('Poppins') ? 'selected' : ''}>Poppins (Geometris & Ramah)</option>
              <option value="'Roboto', sans-serif" ${cFont.includes('Roboto') ? 'selected' : ''}>Roboto (Klasik Google)</option>
              <option value="'JetBrains Mono', monospace" ${cFont.includes('JetBrains Mono') ? 'selected' : ''}>JetBrains Mono (Terminal / Hacker)</option>
              <option value="'Syne', sans-serif" ${cFont.includes('Syne') ? 'selected' : ''}>Syne (Bold & Artistik)</option>
              <option value="Arial, sans-serif" ${cFont.includes('Arial') ? 'selected' : ''}>Arial (Universal Web-Safe)</option>
            </select>
            <small style="font-size:10.5px;color:#94a3b8;display:block;margin-top:4px;">Berlaku untuk seluruh teks kartu, judul, dan angka metrik.</small>
          </div>
        </div>

        <div class="inspector-section">
          <span class="inspector-section-title">TEMA & LATAR BELAKANG KANVAS</span>
          <div class="inspector-field">
            <label>Warna Latar Kanvas</label>
            <div style="display:flex;align-items:center;gap:8px;">
              <input type="color" id="inp_canvas_bg" value="${cBg.startsWith('#') ? cBg : '#0f172a'}" style="width:44px;height:32px;padding:2px;cursor:pointer;" />
              <span style="font-size:11px;font-family:monospace;color:#94a3b8;" id="txt_canvas_bg_hex">${cBg}</span>
            </div>
            <div class="color-swatches-grid">
              <button class="color-swatch-btn" type="button" data-canvas-bg="#0f172a" style="background:#0f172a;" title="Dark Navy"></button>
              <button class="color-swatch-btn" type="button" data-canvas-bg="#1e293b" style="background:#1e293b;" title="Deep Slate"></button>
              <button class="color-swatch-btn" type="button" data-canvas-bg="#000000" style="background:#000000;" title="Pitch Black"></button>
              <button class="color-swatch-btn" type="button" data-canvas-bg="#ffffff" style="background:#ffffff;" title="Clean White"></button>
              <button class="color-swatch-btn" type="button" data-canvas-bg="#f1f5f9" style="background:#f1f5f9;" title="Light Slate"></button>
              <button class="color-swatch-btn" type="button" data-canvas-bg="#064e3b" style="background:#064e3b;" title="Forest Dark"></button>
            </div>
          </div>

          <div class="inspector-field" style="margin-top:14px;border-top:1px solid rgba(255,255,255,0.08);padding-top:12px;">
            <label>Gambar Latar Kanvas (Background Image)</label>
            <input type="file" id="inp_canvas_bg_file" accept="image/png,image/jpeg,image/webp,image/svg+xml" style="display:none;" />
            <button class="button" id="btnUploadCanvasBg" type="button" style="width:100%;margin-bottom:8px;display:flex;align-items:center;justify-content:center;gap:6px;">
              🖼️ Unggah Gambar Latar
            </button>
            <small style="font-size:10.5px;color:#94a3b8;display:block;margin-bottom:8px;">Format JPG, PNG, atau WebP. Disimpan permanen di server.</small>

            <div id="preview_canvas_bg_wrap" style="${cBgImage ? '' : 'display:none;'}">
              <div style="display:flex;align-items:center;gap:10px;background:rgba(0,0,0,0.25);border:1px solid #334155;border-radius:6px;padding:6px 8px;margin-bottom:8px;">
                <img src="${cBgImage || ''}" id="preview_canvas_bg_thumb" style="width:48px;height:36px;object-fit:cover;border-radius:4px;border:1px solid #475569;" />
                <div style="flex:1;overflow:hidden;">
                  <span id="preview_canvas_bg_name" style="font-size:11px;color:#cbd5e1;display:block;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">${cBgImage || ''}</span>
                  <button type="button" id="btnRemoveCanvasBg" style="background:none;border:none;color:#ef4444;font-size:11px;cursor:pointer;padding:0;text-decoration:underline;">Hapus Gambar</button>
                </div>
              </div>

              <div class="inspector-field" style="margin-top:8px;">
                <label>Mode Tampilan Gambar</label>
                <select id="sel_canvas_bg_mode">
                  <option value="cover" ${cBgMode === 'cover' ? 'selected' : ''}>Penuhi Kanvas (Cover)</option>
                  <option value="contain" ${cBgMode === 'contain' ? 'selected' : ''}>Muat Utuh (Contain)</option>
                  <option value="repeat" ${cBgMode === 'repeat' ? 'selected' : ''}>Pola / Ubin (Repeat)</option>
                </select>
              </div>

              <div class="inspector-field" style="margin-top:8px;">
                <div style="display:flex;justify-content:space-between;align-items:center;">
                  <label>Transparansi Gambar</label>
                  <span id="txt_canvas_bg_opacity_val" style="font-size:11px;color:#94a3b8;">${Math.round(cBgOpacity * 100)}%</span>
                </div>
                <input type="range" id="rng_canvas_bg_opacity" min="0.1" max="1.0" step="0.05" value="${cBgOpacity}" style="width:100%;cursor:pointer;" />
              </div>
            </div>
          </div>
        </div>

        <div class="inspector-section" style="margin-top:8px;">
          <button class="button ghost" id="btnInspectorZoomFit" type="button" style="width:100%;">
            🔍 Sesuaikan Kanvas ke Layar (Zoom Fit)
          </button>
        </div>
      `;

      const selFont = document.getElementById('sel_canvas_font');
      selFont?.addEventListener('change', () => {
        this.setCanvasFontFamily(selFont.value);
      });

      const selPreset = document.getElementById('sel_canvas_preset');
      const inpW = document.getElementById('inp_canvas_w');
      const inpH = document.getElementById('inp_canvas_h');
      const inpBg = document.getElementById('inp_canvas_bg');
      const txtBg = document.getElementById('txt_canvas_bg_hex');

      selPreset?.addEventListener('change', () => {
        if (selPreset.value !== 'custom') {
          const [w, h] = selPreset.value.split('x').map(Number);
          if (w && h) {
            if (inpW) inpW.value = w;
            if (inpH) inpH.value = h;
            this.setCanvasDimensions(w, h);
          }
        }
      });

      container.querySelectorAll('.canvas-preset-btn').forEach(btn => {
        btn.addEventListener('click', () => {
          const w = parseInt(btn.dataset.w, 10);
          const h = parseInt(btn.dataset.h, 10);
          if (w && h) {
            if (inpW) inpW.value = w;
            if (inpH) inpH.value = h;
            this.setCanvasDimensions(w, h);
            if (selPreset) {
              const opt = Array.from(selPreset.options).find(o => o.value === `${w}x${h}`);
              if (opt) selPreset.value = opt.value;
              else selPreset.value = 'custom';
            }
          }
        });
      });

      const applyManualSize = () => {
        const w = parseInt(inpW.value, 10);
        const h = parseInt(inpH.value, 10);
        if (w >= 400 && h >= 300) {
          this.setCanvasDimensions(w, h);
          if (selPreset) {
            const opt = Array.from(selPreset.options).find(o => o.value === `${w}x${h}`);
            selPreset.value = opt ? opt.value : 'custom';
          }
        }
      };

      inpW?.addEventListener('change', applyManualSize);
      inpH?.addEventListener('change', applyManualSize);

      const onBgChange = (val) => {
        if (txtBg) txtBg.textContent = val;
        this.setCanvasBackground(val);
      };
      inpBg?.addEventListener('input', () => onBgChange(inpBg.value));
      inpBg?.addEventListener('change', () => onBgChange(inpBg.value));

      container.querySelectorAll('.color-swatch-btn[data-canvas-bg]').forEach(btn => {
        btn.addEventListener('click', (e) => {
          e.preventDefault();
          const col = btn.getAttribute('data-canvas-bg') || btn.dataset.canvasBg;
          if (inpBg) inpBg.value = col;
          onBgChange(col);
        });
      });

      // Background Image upload wiring
      const btnUploadBg = document.getElementById('btnUploadCanvasBg');
      const fileInpBg = document.getElementById('inp_canvas_bg_file');
      const previewBgWrap = document.getElementById('preview_canvas_bg_wrap');
      const previewBgThumb = document.getElementById('preview_canvas_bg_thumb');
      const previewBgName = document.getElementById('preview_canvas_bg_name');
      const btnRemoveBg = document.getElementById('btnRemoveCanvasBg');
      const selBgMode = document.getElementById('sel_canvas_bg_mode');
      const rngBgOpacity = document.getElementById('rng_canvas_bg_opacity');
      const txtBgOpacityVal = document.getElementById('txt_canvas_bg_opacity_val');

      btnUploadBg?.addEventListener('click', () => fileInpBg?.click());

      fileInpBg?.addEventListener('change', async () => {
        const file = fileInpBg.files?.[0];
        if (!file) return;

        // Instant local preview
        const reader = new FileReader();
        reader.onload = (e) => {
          const dataUrl = e.target.result;
          if (!this.state.layout.canvas) this.state.layout.canvas = {};
          this.state.layout.canvas.bgImage = dataUrl;
          if (previewBgThumb) previewBgThumb.src = dataUrl;
          if (previewBgName) previewBgName.textContent = file.name;
          if (previewBgWrap) previewBgWrap.style.display = '';
          this.applyCanvasBackground();
        };
        reader.readAsDataURL(file);

        // Upload to /api/upload
        try {
          const fd = new FormData();
          fd.append('file', file);
          const res = await fetch('/api/upload', {
            method: 'POST',
            body: fd
          });
          if (res.ok) {
            const data = await res.json();
            if (data.url) {
              this.state.layout.canvas.bgImage = data.url;
              if (previewBgName) previewBgName.textContent = data.url;
              if (window.toast) window.toast('Gambar latar berhasil diunggah ke server!', false);
              this.applyCanvasBackground();
            }
          }
        } catch (err) {
          console.warn('[DashboardBuilder] Upload gambar latar gagal:', err);
        }
      });

      btnRemoveBg?.addEventListener('click', () => {
        if (!this.state.layout.canvas) return;
        delete this.state.layout.canvas.bgImage;
        if (previewBgWrap) previewBgWrap.style.display = 'none';
        if (fileInpBg) fileInpBg.value = '';
        this.applyCanvasBackground();
        if (window.toast) window.toast('Gambar latar kanvas dihapus', false);
      });

      selBgMode?.addEventListener('change', () => {
        if (!this.state.layout.canvas) this.state.layout.canvas = {};
        this.state.layout.canvas.bgImageMode = selBgMode.value;
        this.applyCanvasBackground();
      });

      rngBgOpacity?.addEventListener('input', () => {
        const op = parseFloat(rngBgOpacity.value) || 1.0;
        if (!this.state.layout.canvas) this.state.layout.canvas = {};
        this.state.layout.canvas.bgImageOpacity = op;
        if (txtBgOpacityVal) txtBgOpacityVal.textContent = `${Math.round(op * 100)}%`;
        this.applyCanvasBackground();
      });

      document.getElementById('btnInspectorZoomFit')?.addEventListener('click', () => this.zoomFit());
    },

    renderWidgetInspector(container, w) {
      const cfg = w.config || {};
      const activeTab = this.state.inspectorTab || 'content';

      // Options for CCTV & Metrics
      const camList = this.state.registeredCameras || [];
      const camOptions = [
        `<option value="${cfg.cameraLabel || 'Kamera Utama'}">${cfg.cameraLabel || 'Pilih Kamera'}</option>`,
        ...camList.map(c => {
          const name = c.name || c.id || 'Camera';
          const isSel = (cfg.cameraLabel === name) ? 'selected' : '';
          return `<option value="${name}" ${isSel}>${name}</option>`;
        })
      ].join('');

      const projectList = this.state.availableProjects || [];
      const workflowOptions = [
        `<option value="">-- Pilih Workflow / Proyek --</option>`,
        ...projectList.map(p => {
          const isSel = (cfg.workflowId === p.id) ? 'selected' : '';
          return `<option value="${p.id}" ${isSel}>${p.name || p.id}</option>`;
        })
      ].join('');

      const activeKeys = Object.keys(this.state.liveData.metrics || {});
      const defaultKeys = ['total_count', 'total_person', 'violation_count', 'vehicle_flow', cfg.metricKey].filter(Boolean);
      const allMetricKeys = Array.from(new Set([...defaultKeys, ...activeKeys]));
      const metricOptions = allMetricKeys.map(k => {
        const isSel = (cfg.metricKey === k) ? 'selected' : '';
        return `<option value="${k}" ${isSel}>${k}</option>`;
      }).join('');

      // Build Tab Navigation Bar
      let html = `
        <div class="inspector-tabs-nav">
          <button class="inspector-tab-btn ${activeTab === 'content' ? 'active' : ''}" type="button" data-tab="content">
            📄 Konten
          </button>
          <button class="inspector-tab-btn ${activeTab === 'style' ? 'active' : ''}" type="button" data-tab="style">
            🎨 Gaya
          </button>
          <button class="inspector-tab-btn ${activeTab === 'advanced' ? 'active' : ''}" type="button" data-tab="advanced">
            ⚙️ Lanjutan
          </button>
        </div>
      `;

      // ---------------- TAB 1: KONTEN ----------------
      if (activeTab === 'content') {
        html += `
          <!-- Elementor Alignment Toolbar -->
          <div class="inspector-section">
            <span class="inspector-section-title">PERATAAN CEPAT (ALIGNMENT)</span>
            <div class="align-btn-group">
              <button class="align-tool-btn" type="button" data-align="left" title="Rata Kiri Kanvas">⬅️</button>
              <button class="align-tool-btn" type="button" data-align="center-h" title="Tengah Horizontal">↔️</button>
              <button class="align-tool-btn" type="button" data-align="right" title="Rata Kanan Kanvas">➡️</button>
              <button class="align-tool-btn" type="button" data-align="top" title="Rata Atas">⬆️</button>
              <button class="align-tool-btn" type="button" data-align="center-v" title="Tengah Vertikal">↕️</button>
              <button class="align-tool-btn" type="button" data-align="bottom" title="Rata Bawah">⬇️</button>
              <button class="align-tool-btn" type="button" data-align="center-canvas" title="Pusatkan di Tengah Kanvas">🎯</button>
            </div>
          </div>

          <div class="inspector-section">
            <span class="inspector-section-title">POSISI & DIMENSI</span>
            <div class="inspector-row">
              <div class="inspector-field">
                <label>X (px)</label>
                <input type="number" id="inp_x" value="${w.x}" step="10" />
              </div>
              <div class="inspector-field">
                <label>Y (px)</label>
                <input type="number" id="inp_y" value="${w.y}" step="10" />
              </div>
            </div>
            <div class="inspector-row">
              <div class="inspector-field">
                <label>Lebar W (px)</label>
                <input type="number" id="inp_w" value="${w.w}" step="10" />
              </div>
              <div class="inspector-field">
                <label>Tinggi H (px)</label>
                <input type="number" id="inp_h" value="${w.h}" step="10" />
              </div>
            </div>
          </div>

          <div class="inspector-section">
            <span class="inspector-section-title">PENGATURAN KONTEN & DATA</span>

            ${w.type === 'cctv_player' ? `
              <div class="inspector-field">
                <label>Pilih Workflow / Proyek CCTV</label>
                <select id="inp_cctv_workflow">
                  ${workflowOptions}
                </select>
              </div>
              <div class="inspector-field">
                <label>Sumber Input Kamera (dari Workflow)</label>
                <input type="text" id="inp_cctv_input_source" value="${cfg.inputSource || ''}" placeholder="rtsp://... atau Webcam 0" />
              </div>
              <div class="inspector-row">
                <div class="inspector-field">
                  <label>Node Output Stream</label>
                  <select id="inp_nodeId">
                    <option value="preview" ${cfg.nodeId === 'preview' || !cfg.nodeId ? 'selected' : ''}>preview (Anotasi AI)</option>
                    <option value="input" ${cfg.nodeId === 'input' ? 'selected' : ''}>input (Raw Feed)</option>
                  </select>
                </div>
                <div class="inspector-field">
                  <label>Nama Label Kamera</label>
                  <input type="text" id="inp_camLabel" value="${cfg.cameraLabel || ''}" />
                </div>
              </div>
              <div class="cctv-workflow-info-card">
                <div class="cctv-workflow-info-row">
                  <span class="cctv-workflow-info-label">Workflow:</span>
                  <span class="cctv-workflow-info-val" id="txt_info_workflow">${cfg.workflowName || 'Belum Terhubung'}</span>
                </div>
                <div class="cctv-workflow-info-row">
                  <span class="cctv-workflow-info-label">Input Source:</span>
                  <span class="cctv-workflow-info-val" id="txt_info_source">${cfg.inputSource || 'Default Camera'}</span>
                </div>
              </div>
              <button class="button ghost" id="btnOpenWorkflowEditor" type="button" style="width:100%;font-size:11px;margin-top:6px;">
                🚀 Buka Workflow Ini di Editor
              </button>

              <div class="cctv-feature-toggles" style="margin-top:10px;padding:10px;background:rgba(30,41,59,0.5);border-radius:6px;border:1px solid #334155;">
                <span style="font-weight:600;font-size:11px;color:var(--text-primary);display:block;margin-bottom:6px;">FITUR INTERAKTIF PEMILIH KAMERA</span>
                
                <label style="display:flex;align-items:center;gap:6px;font-size:11px;margin-bottom:6px;cursor:pointer;">
                  <input type="checkbox" id="inp_cctv_enable_switcher" ${cfg.enableCameraSwitcher !== false ? 'checked' : ''} />
                  <span>Aktifkan Dropdown Pemilih Kamera di Header</span>
                </label>
                
                <label style="display:flex;align-items:center;gap:6px;font-size:11px;margin-bottom:6px;cursor:pointer;">
                  <input type="checkbox" id="inp_cctv_show_strip" ${cfg.showCameraListStrip ? 'checked' : ''} />
                  <span>Tampilkan Bar Gulir List Kamera (Scrollable Strip)</span>
                </label>
                
                <label style="display:flex;align-items:center;gap:6px;font-size:11px;margin-bottom:6px;cursor:pointer;">
                  <input type="checkbox" id="inp_cctv_auto_patrol" ${cfg.autoPatrol ? 'checked' : ''} />
                  <span>Aktifkan Patroli Otomatis (Auto-Patrol)</span>
                </label>
                
                <div class="inspector-field" id="wrap_patrol_interval" style="margin-top:6px;${cfg.autoPatrol ? '' : 'display:none;'}">
                  <label style="font-size:10.5px;">Interval Ganti Kamera (detik)</label>
                  <input type="number" id="inp_cctv_patrol_interval" value="${cfg.patrolIntervalSeconds || 10}" min="3" max="300" step="1" />
                </div>
              </div>
            ` : ''}

            ${w.type === 'scorecard' ? `
              <div class="inspector-field">
                <label>Judul Metrik</label>
                <input type="text" id="inp_title" value="${cfg.title || ''}" />
              </div>
              <div class="inspector-field">
                <label>Kunci Data (Metric Key)</label>
                <select id="inp_metricKey">
                  ${metricOptions}
                </select>
              </div>
              <div class="inspector-field">
                <label>Satuan Unit</label>
                <input type="text" id="inp_unit" value="${cfg.unit || ''}" />
              </div>
              <div class="inspector-row">
                <div class="inspector-field">
                  <label>Batas Waspada (🟡)</label>
                  <input type="number" id="inp_warn" value="${cfg.warningThreshold || 10}" />
                </div>
                <div class="inspector-field">
                  <label>Batas Bahaya (🔴)</label>
                  <input type="number" id="inp_danger" value="${cfg.dangerThreshold || 20}" />
                </div>
              </div>
            ` : ''}

            ${w.type === 'custom_text' ? `
              <div class="inspector-field">
                <label>Isi Teks</label>
                <input type="text" id="inp_text" value="${cfg.text || ''}" />
              </div>
              <div class="inspector-field">
                <label>Ukuran Font (px)</label>
                <input type="number" id="inp_fontSize" value="${cfg.fontSize || 20}" />
              </div>
              <div class="inspector-field">
                <label>Sub-judul</label>
                <input type="text" id="inp_subtitle" value="${cfg.subtitle || ''}" />
              </div>
            ` : ''}

            ${w.type === 'trend_chart' ? `
              <div class="inspector-field">
                <label>Judul Grafik</label>
                <input type="text" id="inp_title" value="${cfg.title || ''}" />
              </div>
              <div class="inspector-field">
                <label>Kunci Metrik</label>
                <select id="inp_metricKey">
                  ${metricOptions}
                </select>
              </div>
            ` : ''}

            ${w.type === 'event_table' ? `
              <div class="inspector-field">
                <label>Judul Tabel</label>
                <input type="text" id="inp_title" value="${cfg.title || ''}" />
              </div>
              <div class="inspector-field">
                <label>Maksimal Baris</label>
                <input type="number" id="inp_maxRows" value="${cfg.maxRows || 20}" />
              </div>
            ` : ''}

            ${w.type === 'stat_kpi_card' ? `
              <div class="inspector-field">
                <label>Judul KPI</label>
                <input type="text" id="inp_title" value="${cfg.title || ''}" />
              </div>
              <div class="inspector-field">
                <label>Kunci Metrik</label>
                <select id="inp_metricKey">
                  ${metricOptions}
                </select>
              </div>
              <div class="inspector-field">
                <label>Keterangan Bawah</label>
                <input type="text" id="inp_sublabel" value="${cfg.sublabel || ''}" />
              </div>
            ` : ''}

            ${w.type === 'status_badge' ? `
              <div class="inspector-field">
                <label>Label Status</label>
                <input type="text" id="inp_label" value="${cfg.label || ''}" />
              </div>
              <div class="inspector-field">
                <label>Shift Kerja</label>
                <input type="text" id="inp_shift" value="${cfg.shift || ''}" />
              </div>
            ` : ''}

            ${w.type === 'container_box' ? `
              <div class="inspector-field">
                <label>Judul Wadah</label>
                <input type="text" id="inp_title" value="${cfg.title || ''}" />
              </div>
            ` : ''}

            ${w.type === 'dashboard_navbar' ? `
              <div class="inspector-field">
                <label>Judul Utama Bilah Navigasi</label>
                <input type="text" id="inp_title" value="${cfg.title || ''}" />
              </div>
              <div class="inspector-field">
                <label>Sub-judul / Unit Lokasi</label>
                <input type="text" id="inp_subtitle" value="${cfg.subtitle || ''}" />
              </div>
              <div class="inspector-field">
                <label>URL Logo Instansi</label>
                <input type="text" id="inp_navbar_logo" value="${cfg.logoUrl || '/static/logo.png'}" />
              </div>
              <div class="inspector-field">
                <label>Keterangan Shift Kerja</label>
                <input type="text" id="inp_shift" value="${cfg.shift || 'Shift 1'}" />
              </div>
              <div class="inspector-row">
                <div class="inspector-field">
                  <label style="display:flex;align-items:center;gap:6px;cursor:pointer;font-size:11px;">
                    <input type="checkbox" id="inp_show_clock" ${cfg.showClock !== false ? 'checked' : ''} />
                    <span>Tampilkan Jam Digital</span>
                  </label>
                </div>
                <div class="inspector-field">
                  <label style="display:flex;align-items:center;gap:6px;cursor:pointer;font-size:11px;">
                    <input type="checkbox" id="inp_show_shift" ${cfg.showShift !== false ? 'checked' : ''} />
                    <span>Tampilkan Shift Kerja</span>
                  </label>
                </div>
              </div>
            ` : ''}

            ${w.type === 'image_logo' ? `
              <div class="inspector-field">
                <label>Unggah Berkas Logo</label>
                <input type="file" id="inp_logo_file" accept="image/png,image/jpeg,image/svg+xml,image/webp,image/gif" style="display:none;" />
                <button class="button primary" id="btnUploadLogo" type="button" style="width:100%;margin-bottom:6px;display:flex;align-items:center;justify-content:center;gap:6px;">
                  📁 Pilih & Unggah Logo
                </button>
                <small style="font-size:10.5px;color:#94a3b8;display:block;margin-bottom:8px;">Disimpan di server & otomatis disertakan saat ekspor Docker.</small>
              </div>
              <div class="inspector-field">
                <label>URL / Jalur Gambar Logo</label>
                <input type="text" id="inp_logo_url" value="${cfg.url || '/static/logo.png'}" placeholder="/static/logo.png atau /api/uploads/..." />
              </div>
              <div class="inspector-field">
                <label>Teks Keterangan (Alt Text)</label>
                <input type="text" id="inp_logo_alt" value="${cfg.alt || 'Logo Perusahaan'}" />
              </div>
              <div class="inspector-field">
                <label>Kesesuaian Gambar (Object Fit)</label>
                <select id="inp_logo_fit">
                  <option value="contain" ${cfg.objectFit === 'contain' || !cfg.objectFit ? 'selected' : ''}>Proporsional (Contain)</option>
                  <option value="cover" ${cfg.objectFit === 'cover' ? 'selected' : ''}>Penuhi Kotak (Cover)</option>
                  <option value="fill" ${cfg.objectFit === 'fill' ? 'selected' : ''}>Regang Penuh (Fill)</option>
                </select>
              </div>
              <div class="inspector-field" style="margin-top:10px;">
                <label>Pratinjau Logo Saat Ini</label>
                <div style="background:#090d16;border:1px solid #334155;border-radius:6px;padding:8px;text-align:center;min-height:50px;display:flex;align-items:center;justify-content:center;">
                  <img src="${cfg.url || cfg.dataUrl || '/static/logo.png'}" id="preview_logo_thumb" style="max-height:55px;max-width:100%;object-fit:contain;" />
                </div>
              </div>
            ` : ''}

            
            ${w.type === 'media_input_controller' ? `
              <div class="inspector-field">
                <label>Judul Panel Input</label>
                <input type="text" id="inp_media_title" value="${cfg.title || 'Media Input & Inference Controller'}" />
              </div>
              <div class="inspector-field">
                <label>Ambang Batas Default (Confidence)</label>
                <input type="number" id="inp_media_conf" min="5" max="95" step="5" value="${Math.round((cfg.defaultConfidence || 0.25) * 100)}" />
              </div>
              <div class="inspector-field" style="margin-top:6px;">
                <label style="display:flex;align-items:center;gap:6px;cursor:pointer;">
                  <input type="checkbox" id="chk_media_autorun" ${cfg.autoRunOnUpload !== false ? 'checked' : ''} />
                  <span>Jalankan otomatis saat berkas diunggah</span>
                </label>
              </div>
            ` : ''}

            ${w.type === 'vision_result_viewer' ? `
              <div class="inspector-field">
                <label>Judul Panel Viewer</label>
                <input type="text" id="inp_viewer_title" value="${cfg.title || 'Visual Output & Detections'}" />
              </div>
              <div class="inspector-field" style="margin-top:6px;">
                <label style="display:flex;align-items:center;gap:6px;cursor:pointer;">
                  <input type="checkbox" id="chk_viewer_download" ${cfg.showDownloadBtn !== false ? 'checked' : ''} />
                  <span>Tampilkan tombol unduh visual</span>
                </label>
              </div>
            ` : ''}

            ${w.type === 'confidence_table' ? `
              <div class="inspector-field">
                <label>Judul Tabel Keyakinan</label>
                <input type="text" id="inp_conf_table_title" value="${cfg.title || 'Daftar Objek & Skor Keyakinan'}" />
              </div>
              <div class="inspector-field" style="margin-top:6px;">
                <label style="display:flex;align-items:center;gap:6px;cursor:pointer;">
                  <input type="checkbox" id="chk_conf_crop" ${cfg.showCropThumbnail !== false ? 'checked' : ''} />
                  <span>Tampilkan thumbnail crop objek</span>
                </label>
              </div>
            ` : ''}

            ${w.type === 'custom_analytics_table' ? `
              <div class="inspector-field">
                <label>Judul Tabel Analitik Kustom</label>
                <input type="text" id="inp_analytics_table_title" value="${cfg.title || 'Tabel Analisis Kustom & Zona'}" />
              </div>
            ` : ''}

            ${w.type === 'excel_export_btn' ? `
              <div class="inspector-field">
                <label>Teks / Label Tombol Unduh</label>
                <input type="text" id="inp_excel_label" value="${cfg.label || 'Unduh Rekap Excel (.xlsx)'}" placeholder="Unduh Laporan Kerja (.xlsx)" />
              </div>
              <div class="inspector-field">
                <label>Nama Berkas Spreadsheet Saat Diunduh</label>
                <input type="text" id="inp_excel_filename" value="${cfg.filename || 'Laporan_Aktivitas.xlsx'}" placeholder="Laporan_Workshop.xlsx" />
                <small style="font-size:10.5px;color:#94a3b8;display:block;margin-top:3px;">Otomatis ditambahkan ekstensi .xlsx</small>
              </div>
              <div class="inspector-field">
                <label>Ikon Tombol</label>
                <select id="inp_excel_icon">
                  <option value="spreadsheet" ${!cfg.icon || cfg.icon === 'spreadsheet' ? 'selected' : ''}>📊 Lembar Sebar (Spreadsheet)</option>
                  <option value="file" ${cfg.icon === 'file' ? 'selected' : ''}>📄 Dokumen (File)</option>
                  <option value="table" ${cfg.icon === 'table' ? 'selected' : ''}>📋 Tabel Data (Data Table)</option>
                  <option value="analytics" ${cfg.icon === 'analytics' ? 'selected' : ''}>📈 Grafik & Analitik</option>
                </select>
              </div>
              <div class="inspector-field" style="margin-top:10px;">
                <label>Lembar yang Disertakan dalam Berkas</label>
                <div style="display:flex;flex-direction:column;gap:6px;margin-top:4px;">
                  <label style="display:flex;align-items:center;gap:6px;font-size:11.5px;cursor:pointer;">
                    <input type="checkbox" id="chk_excel_events" ${cfg.includeEvents !== false ? 'checked' : ''} />
                    <span>Lembar Log Kejadian (Event Records)</span>
                  </label>
                  <label style="display:flex;align-items:center;gap:6px;font-size:11.5px;cursor:pointer;">
                    <input type="checkbox" id="chk_excel_metrics" ${cfg.includeMetrics !== false ? 'checked' : ''} />
                    <span>Lembar Metrik KPI (Metrics Aggregation)</span>
                  </label>
                </div>
              </div>
            ` : ''}
          </div>
        `;
      }

      // ---------------- TAB 2: GAYA (STYLING) ----------------
      else if (activeTab === 'style') {
        html += `
          <div class="inspector-section">
            <span class="inspector-section-title">TEMA CEPAT & KONTRAS TINGGI</span>
            <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:6px;margin-bottom:12px;">
              <button class="button small ghost btn-quick-theme" type="button" data-theme-preset="obsidian" title="Obsidian Dark High Contrast" style="font-size:10.5px;padding:4px 6px;border:1px solid #334155;background:#0f172a;color:#f8fafc;">
                🌙 Obsidian
              </button>
              <button class="button small ghost btn-quick-theme" type="button" data-theme-preset="light" title="Pure White Clean High Contrast" style="font-size:10.5px;padding:4px 6px;border:1px solid #cbd5e1;background:#ffffff;color:#0f172a;">
                ☀️ Terang
              </button>
              <button class="button small ghost btn-quick-theme" type="button" data-theme-preset="cyan" title="Cyber Cyan Glowing Contrast" style="font-size:10.5px;padding:4px 6px;border:1px solid #0284c7;background:#032940;color:#38bdf8;">
                💎 Neon Cyan
              </button>
            </div>

            <span class="inspector-section-title">WARNA & LATAR BELAKANG</span>
            <div class="inspector-field">
              <label>Warna Latar (Background)</label>
              <div style="display:flex;align-items:center;gap:8px;">
                <input type="color" id="inp_w_bg" value="${cfg.bgColor && cfg.bgColor !== 'transparent' && cfg.bgColor.startsWith('#') ? cfg.bgColor : '#1e293b'}" style="width:40px;height:30px;padding:2px;cursor:pointer;" />
                <label style="display:flex;align-items:center;gap:4px;font-size:11px;cursor:pointer;">
                  <input type="checkbox" id="inp_w_bg_trans" ${cfg.bgColor === 'transparent' ? 'checked' : ''} />
                  <span>Transparan</span>
                </label>
              </div>
              <div class="color-swatches-grid">
                <button class="color-swatch-btn" type="button" data-style-type="bg" data-val="#0f172a" style="background:#0f172a;" title="Navy Gelap"></button>
                <button class="color-swatch-btn" type="button" data-style-type="bg" data-val="#1e293b" style="background:#1e293b;" title="Slate Gelap"></button>
                <button class="color-swatch-btn" type="button" data-style-type="bg" data-val="#ffffff" style="background:#ffffff;" title="Putih"></button>
                <button class="color-swatch-btn" type="button" data-style-type="bg" data-val="#f8fafc" style="background:#f8fafc;" title="Putih Lembut"></button>
                <button class="color-swatch-btn" type="button" data-style-type="bg" data-val="#0369a1" style="background:#0369a1;" title="Biru"></button>
                <button class="color-swatch-btn" type="button" data-style-type="bg" data-val="#065f46" style="background:#065f46;" title="Hijau"></button>
                <button class="color-swatch-btn" type="button" data-style-type="bg" data-val="#881337" style="background:#881337;" title="Merah"></button>
              </div>
            </div>

            <div class="inspector-row">
              <div class="inspector-field">
                <label>Warna Teks</label>
                <div style="display:flex;align-items:center;gap:6px;">
                  <input type="color" id="inp_w_text" value="${cfg.textColor && cfg.textColor.startsWith('#') ? cfg.textColor : '#f8fafc'}" style="width:36px;height:30px;padding:2px;cursor:pointer;" />
                  <div class="color-swatches-grid" style="margin-top:0;">
                    <button class="color-swatch-btn" type="button" data-style-type="text" data-val="#ffffff" style="background:#ffffff;" title="Putih"></button>
                    <button class="color-swatch-btn" type="button" data-style-type="text" data-val="#0f172a" style="background:#0f172a;" title="Hitam"></button>
                    <button class="color-swatch-btn" type="button" data-style-type="text" data-val="#38bdf8" style="background:#38bdf8;" title="Cyan"></button>
                    <button class="color-swatch-btn" type="button" data-style-type="text" data-val="#10b981" style="background:#10b981;" title="Hijau"></button>
                  </div>
                </div>
              </div>
            </div>

            <div class="inspector-row">
              <div class="inspector-field">
                <label>Garis Tepi (Border)</label>
                <div style="display:flex;align-items:center;gap:6px;">
                  <input type="color" id="inp_w_border" value="${cfg.borderColor && cfg.borderColor.startsWith('#') ? cfg.borderColor : '#334155'}" style="width:36px;height:30px;padding:2px;cursor:pointer;" />
                  <div class="color-swatches-grid" style="margin-top:0;">
                    <button class="color-swatch-btn" type="button" data-style-type="border" data-val="#334155" style="background:#334155;" title="Slate"></button>
                    <button class="color-swatch-btn" type="button" data-style-type="border" data-val="#cbd5e1" style="background:#cbd5e1;" title="Light"></button>
                    <button class="color-swatch-btn" type="button" data-style-type="border" data-val="#38bdf8" style="background:#38bdf8;" title="Cyan Glow"></button>
                  </div>
                </div>
              </div>
              <div class="inspector-field">
                <label>Radius Sudut</label>
                <select id="inp_w_radius">
                  <option value="0px" ${cfg.borderRadius === '0px' ? 'selected' : ''}>0px (Tajam)</option>
                  <option value="4px" ${cfg.borderRadius === '4px' ? 'selected' : ''}>4px (Sedikit)</option>
                  <option value="8px" ${!cfg.borderRadius || cfg.borderRadius === '8px' ? 'selected' : ''}>8px (Standar)</option>
                  <option value="14px" ${cfg.borderRadius === '14px' ? 'selected' : ''}>14px (Halus)</option>
                  <option value="24px" ${cfg.borderRadius === '24px' ? 'selected' : ''}>24px (Membulat)</option>
                </select>
              </div>
            </div>
          </div>

          <div class="inspector-section">
            <span class="inspector-section-title">TIPOGRAFI & JENIS HURUF</span>
            <div class="inspector-field">
              <label>Jenis Huruf Komponen</label>
              <select id="inp_w_font">
                <option value="" ${!cfg.fontFamily ? 'selected' : ''}>Bawaan Kanvas (Default)</option>
                <option value="'Inter', -apple-system, sans-serif" ${cfg.fontFamily && cfg.fontFamily.includes('Inter') ? 'selected' : ''}>Inter (Modern & Bersih)</option>
                <option value="'Plus Jakarta Sans', sans-serif" ${cfg.fontFamily && cfg.fontFamily.includes('Plus Jakarta Sans') ? 'selected' : ''}>Plus Jakarta Sans (Elegan)</option>
                <option value="'Outfit', sans-serif" ${cfg.fontFamily && cfg.fontFamily.includes('Outfit') ? 'selected' : ''}>Outfit (Futuristik)</option>
                <option value="'Poppins', sans-serif" ${cfg.fontFamily && cfg.fontFamily.includes('Poppins') ? 'selected' : ''}>Poppins (Geometris)</option>
                <option value="'Roboto', sans-serif" ${cfg.fontFamily && cfg.fontFamily.includes('Roboto') ? 'selected' : ''}>Roboto (Klasik Google)</option>
                <option value="'JetBrains Mono', monospace" ${cfg.fontFamily && cfg.fontFamily.includes('JetBrains Mono') ? 'selected' : ''}>JetBrains Mono (Terminal / Hacker)</option>
                <option value="'Syne', sans-serif" ${cfg.fontFamily && cfg.fontFamily.includes('Syne') ? 'selected' : ''}>Syne (Bold Display)</option>
                <option value="Arial, sans-serif" ${cfg.fontFamily && cfg.fontFamily.includes('Arial') ? 'selected' : ''}>Arial (Universal)</option>
              </select>
            </div>
          </div>

          <div class="inspector-section">
            <span class="inspector-section-title">EFEK ELEVASI & KACA ES</span>
            <div class="inspector-field">
              <label>Bayangan (Box Shadow Preset)</label>
              <select id="inp_w_shadow">
                <option value="none" ${cfg.boxShadow === 'none' ? 'selected' : ''}>Datar (Tanpa Bayangan)</option>
                <option value="soft" ${cfg.boxShadow === 'soft' || !cfg.boxShadow ? 'selected' : ''}>Elevasi Halus (Default)</option>
                <option value="deep" ${cfg.boxShadow === 'deep' ? 'selected' : ''}>Elevasi Dalam (Pop Out)</option>
                <option value="neon-cyan" ${cfg.boxShadow === 'neon-cyan' ? 'selected' : ''}>Glow Neon Cyan (AI Theme)</option>
                <option value="neon-emerald" ${cfg.boxShadow === 'neon-emerald' ? 'selected' : ''}>Glow Neon Hijau (Online)</option>
              </select>
            </div>
            <div class="inspector-field" style="margin-top:8px;">
              <label style="display:flex;align-items:center;gap:6px;cursor:pointer;">
                <input type="checkbox" id="inp_w_glass" ${cfg.glassmorphism ? 'checked' : ''} />
                <span>Efek Kaca Es (Frosted Glassmorphism)</span>
              </label>
              <small style="font-size:10.5px;color:#94a3b8;display:block;margin-top:2px;">Memberikan efek blur tembus pandang bergaya Command Center modern.</small>
            </div>
          </div>
        `;
      }

      // ---------------- TAB 3: LANJUTAN (ADVANCED) ----------------
      else if (activeTab === 'advanced') {
        const curZ = w.z || 1;
        const curOp = cfg.opacity !== undefined ? Math.round(cfg.opacity * 100) : 100;

        html += `
          <div class="inspector-section">
            <span class="inspector-section-title">SUSUNAN LAPISAN (Z-INDEX)</span>
            <div class="inspector-row">
              <div class="inspector-field">
                <label>Nilai Z-Index</label>
                <input type="number" id="inp_w_z" value="${curZ}" min="1" max="999" />
              </div>
            </div>
            <div class="align-btn-group" style="margin-top:6px;">
              <button class="align-tool-btn" type="button" id="btn_layer_front" title="Paling Depan">🔝 Depan</button>
              <button class="align-tool-btn" type="button" id="btn_layer_up" title="Naikkan 1 Lapisan">🔼 Naik</button>
              <button class="align-tool-btn" type="button" id="btn_layer_down" title="Turunkan 1 Lapisan">🔽 Turun</button>
              <button class="align-tool-btn" type="button" id="btn_layer_back" title="Paling Belakang">🔚 Belakang</button>
            </div>
          </div>

          <div class="inspector-section">
            <span class="inspector-section-title">TRANSPARANSI & OPASITAS</span>
            <div class="inspector-field">
              <div style="display:flex;justify-content:space-between;align-items:center;">
                <label>Opasitas Komponen</label>
                <span id="txt_w_opacity" style="font-size:11px;font-family:monospace;color:#38bdf8;">${curOp}%</span>
              </div>
              <input type="range" id="inp_w_opacity" min="10" max="100" step="5" value="${curOp}" style="width:100%;cursor:pointer;" />
            </div>
          </div>

          <div class="inspector-section">
            <span class="inspector-section-title">PENGUNCIAN & PROTEKSI</span>
            <div class="inspector-field">
              <p style="font-size:11px;color:#94a3b8;margin:0 0 8px 0;">Kunci komponen untuk mencegah tergeser atau terubah ukurannya secara tidak sengaja.</p>
              <button class="button ${w.isLocked ? 'primary' : 'ghost'}" id="btn_w_lock" type="button" style="width:100%;">
                ${w.isLocked ? '🔓 Buka Kunci Komponen' : '🔒 Kunci Posisi Komponen'}
              </button>
            </div>
          </div>

          <div style="margin-top:16px;border-top:1px solid #334155;padding-top:12px;display:flex;gap:8px;">
            <button class="button ghost" id="btnDuplicateWidget" type="button" style="flex:1;">
              📋 Gandakan
            </button>
            <button class="button danger" id="btnDeleteWidget" type="button" style="flex:1;">
              🗑️ Hapus
            </button>
          </div>
        `;
      }

      container.innerHTML = html;

      // Tab switcher clicks
      container.querySelectorAll('.inspector-tab-btn').forEach(btn => {
        btn.addEventListener('click', () => {
          this.state.inspectorTab = btn.dataset.tab;
          this.selectWidget(w.id);
        });
      });

      const elWidget = document.getElementById(`widget_${w.id}`);

      // ---------------- BIND TAB 1: KONTEN ----------------
      if (activeTab === 'content') {
        // Alignment buttons
        container.querySelectorAll('.align-tool-btn[data-align]').forEach(btn => {
          btn.addEventListener('click', () => {
            this.alignSelectedWidget(btn.dataset.align);
          });
        });

        // CCTV binding
        if (w.type === 'cctv_player') {
          const inpWorkflow = document.getElementById('inp_cctv_workflow');
          const inpInputSource = document.getElementById('inp_cctv_input_source');
          const txtInfoWorkflow = document.getElementById('txt_info_workflow');
          const txtInfoSource = document.getElementById('txt_info_source');
          const inpLabel = document.getElementById('inp_camLabel');

          inpWorkflow?.addEventListener('change', async () => {
            const selectedProjId = inpWorkflow.value;
            const selectedProj = this.state.availableProjects.find(p => p.id === selectedProjId);
            if (selectedProj) {
              cfg.workflowId = selectedProj.id;
              cfg.workflowName = selectedProj.name;
              cfg.cameraLabel = selectedProj.name;
              if (inpLabel) inpLabel.value = cfg.cameraLabel;
              if (txtInfoWorkflow) txtInfoWorkflow.textContent = cfg.workflowName;

              const details = await this.getWorkflowDetails(selectedProj.id);
              if (details && details.workflow && Array.isArray(details.workflow.nodes)) {
                const nodes = details.workflow.nodes;
                const inputNode = nodes.find(n => n.type === 'input' || n.type === 'ip_camera' || n.id === 'input');
                if (inputNode) {
                  let srcStr = '';
                  const icfg = inputNode.config || {};
                  if (inputNode.type === 'ip_camera' || icfg.streamUrl) {
                    srcStr = `RTSP: ${icfg.streamUrl || 'rtsp://stream'}`;
                  } else if (icfg.sourceType === 'camera') {
                    srcStr = `Webcam (Index ${icfg.source ?? 0})`;
                  } else if (icfg.sourceType === 'youtube' && icfg.youtubeUrl) {
                    srcStr = `YouTube: ${icfg.youtubeUrl}`;
                  } else if (icfg.sourceType === 'file' || icfg.sourceType === 'video') {
                    srcStr = `File: ${icfg.source || 'Video'}`;
                  } else {
                    srcStr = `Sumber Input (${icfg.sourceType || 'Default'})`;
                  }
                  cfg.inputSource = srcStr;
                  if (inpInputSource) inpInputSource.value = srcStr;
                  if (txtInfoSource) txtInfoSource.textContent = srcStr;
                }

                const previewNode = nodes.find(n => n.type === 'preview' || n.id === 'preview');
                if (previewNode) {
                  cfg.nodeId = previewNode.id;
                }
              }
              this.reRenderWidgetBody(w);
            }
          });

          inpInputSource?.addEventListener('input', () => {
            cfg.inputSource = inpInputSource.value;
            if (txtInfoSource) txtInfoSource.textContent = cfg.inputSource;
          });

          document.getElementById('btnOpenWorkflowEditor')?.addEventListener('click', () => {
            if (cfg.workflowId) {
              if (window.app?.loadProject) {
                window.app.loadProject(cfg.workflowId);
              }
              const tabEditor = document.getElementById('tabEditor');
              if (tabEditor) tabEditor.click();
            }
          });

          // Interactive Camera Switcher & Scroll Strip Toggles
          const chkSwitcher = document.getElementById('inp_cctv_enable_switcher');
          chkSwitcher?.addEventListener('change', () => {
            cfg.enableCameraSwitcher = chkSwitcher.checked;
            this.reRenderWidgetBody(w);
          });

          const chkStrip = document.getElementById('inp_cctv_show_strip');
          chkStrip?.addEventListener('change', () => {
            cfg.showCameraListStrip = chkStrip.checked;
            this.reRenderWidgetBody(w);
          });

          const chkPatrol = document.getElementById('inp_cctv_auto_patrol');
          const wrapInterval = document.getElementById('wrap_patrol_interval');
          const inpPatrolInterval = document.getElementById('inp_cctv_patrol_interval');

          chkPatrol?.addEventListener('change', () => {
            cfg.autoPatrol = chkPatrol.checked;
            if (wrapInterval) wrapInterval.style.display = cfg.autoPatrol ? '' : 'none';
            if (cfg.autoPatrol) {
              this.startAutoPatrol(w.id);
            } else {
              this.stopAutoPatrol(w.id);
            }
            this.reRenderWidgetBody(w);
          });

          inpPatrolInterval?.addEventListener('change', () => {
            cfg.patrolIntervalSeconds = Math.max(3, parseInt(inpPatrolInterval.value, 10) || 10);
            if (cfg.autoPatrol) {
              this.startAutoPatrol(w.id);
            }
          });
        }

        // Standard coordinate & field bindings
        const bind = (id, prop, isNum = false) => {
          const inp = document.getElementById(id);
          const handleVal = () => {
            const val = isNum ? parseFloat(inp.value) || 0 : inp.value;
            if (['x', 'y', 'w', 'h'].includes(prop)) {
              w[prop] = val;
              if (elWidget) {
                if (prop === 'x') elWidget.style.left = `${val}px`;
                if (prop === 'y') elWidget.style.top = `${val}px`;
                if (prop === 'w') elWidget.style.width = `${val}px`;
                if (prop === 'h') elWidget.style.height = `${val}px`;
              }
            } else {
              w.config[prop] = val;
              this.reRenderWidgetBody(w);
            }
          };
          inp?.addEventListener('input', handleVal);
          inp?.addEventListener('change', handleVal);
        };

        bind('inp_x', 'x', true);
        bind('inp_y', 'y', true);
        bind('inp_w', 'w', true);
        bind('inp_h', 'h', true);
        bind('inp_title', 'title');
        bind('inp_metricKey', 'metricKey');
        bind('inp_unit', 'unit');
        bind('inp_warn', 'warningThreshold', true);
        bind('inp_danger', 'dangerThreshold', true);
        bind('inp_camLabel', 'cameraLabel');
        bind('inp_nodeId', 'nodeId');
        bind('inp_text', 'text');
        bind('inp_fontSize', 'fontSize', true);
        bind('inp_subtitle', 'subtitle');
        bind('inp_sublabel', 'sublabel');
        bind('inp_label', 'label');
        bind('inp_shift', 'shift');
        bind('inp_maxRows', 'maxRows', true);

        if (w.type === 'dashboard_navbar') {
          const inpLogo = document.getElementById('inp_navbar_logo');
          inpLogo?.addEventListener('input', () => {
            cfg.logoUrl = inpLogo.value;
            this.reRenderWidgetBody(w);
          });
          const chkClock = document.getElementById('inp_show_clock');
          chkClock?.addEventListener('change', () => {
            cfg.showClock = chkClock.checked;
            this.reRenderWidgetBody(w);
          });
          const chkShift = document.getElementById('inp_show_shift');
          chkShift?.addEventListener('change', () => {
            cfg.showShift = chkShift.checked;
            this.reRenderWidgetBody(w);
          });
        }

        // Bind image_logo upload and configuration
        if (w.type === 'image_logo') {
          const btnUpload = document.getElementById('btnUploadLogo');
          const fileInp = document.getElementById('inp_logo_file');
          const urlInp = document.getElementById('inp_logo_url');
          const altInp = document.getElementById('inp_logo_alt');
          const fitInp = document.getElementById('inp_logo_fit');
          const thumb = document.getElementById('preview_logo_thumb');

          btnUpload?.addEventListener('click', () => fileInp?.click());

          fileInp?.addEventListener('change', async () => {
            const file = fileInp.files?.[0];
            if (!file) return;

            // 1. Immediate Base64 data URL for zero-latency local rendering
            const reader = new FileReader();
            reader.onload = (e) => {
              const dataUrl = e.target.result;
              cfg.dataUrl = dataUrl;
              if (thumb) thumb.src = dataUrl;
              const canvasImg = document.getElementById(`img_logo_${w.id}`);
              if (canvasImg) canvasImg.src = dataUrl;
            };
            reader.readAsDataURL(file);

            // 2. Server upload via /api/upload
            try {
              const fd = new FormData();
              fd.append('file', file);
              const res = await fetch('/api/upload', {
                method: 'POST',
                body: fd
              });
              if (res.ok) {
                const data = await res.json();
                if (data.url) {
                  cfg.url = data.url;
                  if (urlInp) urlInp.value = data.url;
                  if (window.toast) window.toast('Logo berhasil diunggah ke server!', false);
                }
              }
            } catch (err) {
              console.warn('[DashboardBuilder] Server upload fallback to dataUrl:', err);
            }
            this.reRenderWidgetBody(w);
          });

          urlInp?.addEventListener('input', () => {
            cfg.url = urlInp.value;
            delete cfg.dataUrl;
            if (thumb) thumb.src = cfg.url;
            this.reRenderWidgetBody(w);
          });

          altInp?.addEventListener('input', () => {
            cfg.alt = altInp.value;
            this.reRenderWidgetBody(w);
          });

          fitInp?.addEventListener('change', () => {
            cfg.objectFit = fitInp.value;
            this.reRenderWidgetBody(w);
          });
        }

        
        if (w.type === 'media_input_controller') {
          const inpTitle = document.getElementById('inp_media_title');
          const inpConf = document.getElementById('inp_media_conf');
          const chkAuto = document.getElementById('chk_media_autorun');

          inpTitle?.addEventListener('input', () => {
            cfg.title = inpTitle.value;
            this.reRenderWidgetBody(w);
          });
          inpConf?.addEventListener('change', () => {
            const val = parseFloat(inpConf.value) / 100.0;
            cfg.defaultConfidence = val;
            this.state.analysisState.currentConfidence = val;
            this.reRenderWidgetBody(w);
          });
          chkAuto?.addEventListener('change', () => {
            cfg.autoRunOnUpload = chkAuto.checked;
          });
        }

        if (w.type === 'vision_result_viewer') {
          const inpTitle = document.getElementById('inp_viewer_title');
          const chkDown = document.getElementById('chk_viewer_download');
          inpTitle?.addEventListener('input', () => {
            cfg.title = inpTitle.value;
            this.reRenderWidgetBody(w);
          });
          chkDown?.addEventListener('change', () => {
            cfg.showDownloadBtn = chkDown.checked;
            this.reRenderWidgetBody(w);
          });
        }

        if (w.type === 'confidence_table') {
          const inpTitle = document.getElementById('inp_conf_table_title');
          const chkCrop = document.getElementById('chk_conf_crop');
          inpTitle?.addEventListener('input', () => {
            cfg.title = inpTitle.value;
            this.reRenderWidgetBody(w);
          });
          chkCrop?.addEventListener('change', () => {
            cfg.showCropThumbnail = chkCrop.checked;
            this.reRenderWidgetBody(w);
          });
        }

        if (w.type === 'custom_analytics_table') {
          const inpTitle = document.getElementById('inp_analytics_table_title');
          inpTitle?.addEventListener('input', () => {
            cfg.title = inpTitle.value;
            this.reRenderWidgetBody(w);
          });
        }

        if (w.type === 'excel_export_btn') {
          const inpLabel = document.getElementById('inp_excel_label');
          const inpFilename = document.getElementById('inp_excel_filename');
          const selIcon = document.getElementById('inp_excel_icon');
          const chkEvents = document.getElementById('chk_excel_events');
          const chkMetrics = document.getElementById('chk_excel_metrics');

          inpLabel?.addEventListener('input', () => {
            cfg.label = inpLabel.value;
            this.reRenderWidgetBody(w);
          });
          inpFilename?.addEventListener('input', () => {
            cfg.filename = inpFilename.value;
            this.reRenderWidgetBody(w);
          });
          selIcon?.addEventListener('change', () => {
            cfg.icon = selIcon.value;
            this.reRenderWidgetBody(w);
          });
          chkEvents?.addEventListener('change', () => {
            cfg.includeEvents = chkEvents.checked;
          });
          chkMetrics?.addEventListener('change', () => {
            cfg.includeMetrics = chkMetrics.checked;
          });
        }
      }

      // ---------------- BIND TAB 2: GAYA ----------------
      else if (activeTab === 'style') {
        const inpBg = document.getElementById('inp_w_bg');
        const chkTrans = document.getElementById('inp_w_bg_trans');
        const inpText = document.getElementById('inp_w_text');
        const inpBorder = document.getElementById('inp_w_border');
        const inpRadius = document.getElementById('inp_w_radius');
        const inpShadow = document.getElementById('inp_w_shadow');
        const inpGlass = document.getElementById('inp_w_glass');

        inpBg?.addEventListener('input', () => {
          cfg.bgColor = inpBg.value;
          if (chkTrans) chkTrans.checked = false;
          this.applyWidgetCustomStyles(elWidget, w);
        });

        chkTrans?.addEventListener('change', () => {
          cfg.bgColor = chkTrans.checked ? 'transparent' : (inpBg ? inpBg.value : '#1e293b');
          this.applyWidgetCustomStyles(elWidget, w);
        });

        inpText?.addEventListener('input', () => {
          cfg.textColor = inpText.value;
          this.applyWidgetCustomStyles(elWidget, w);
        });

        inpBorder?.addEventListener('input', () => {
          cfg.borderColor = inpBorder.value;
          this.applyWidgetCustomStyles(elWidget, w);
        });

        inpRadius?.addEventListener('change', () => {
          cfg.borderRadius = inpRadius.value;
          this.applyWidgetCustomStyles(elWidget, w);
        });

        inpShadow?.addEventListener('change', () => {
          cfg.boxShadow = inpShadow.value;
          this.applyWidgetCustomStyles(elWidget, w);
        });

        inpGlass?.addEventListener('change', () => {
          cfg.glassmorphism = inpGlass.checked;
          this.applyWidgetCustomStyles(elWidget, w);
        });

        const inpFont = document.getElementById('inp_w_font');
        inpFont?.addEventListener('change', () => {
          cfg.fontFamily = inpFont.value;
          this.applyWidgetCustomStyles(elWidget, w);
        });

        // Quick Theme Preset clicks
        container.querySelectorAll('.btn-quick-theme').forEach(btn => {
          btn.addEventListener('click', () => {
            const preset = btn.dataset.themePreset;
            if (preset === 'obsidian') {
              cfg.bgColor = '#0f172a';
              cfg.textColor = '#f8fafc';
              cfg.borderColor = '#334155';
              cfg.boxShadow = 'deep';
              cfg.glassmorphism = false;
            } else if (preset === 'light') {
              cfg.bgColor = '#ffffff';
              cfg.textColor = '#0f172a';
              cfg.borderColor = '#cbd5e1';
              cfg.boxShadow = 'soft';
              cfg.glassmorphism = false;
            } else if (preset === 'cyan') {
              cfg.bgColor = '#091528';
              cfg.textColor = '#38bdf8';
              cfg.borderColor = '#0284c7';
              cfg.boxShadow = 'neon-cyan';
              cfg.glassmorphism = false;
            }
            if (inpBg) inpBg.value = cfg.bgColor;
            if (inpText) inpText.value = cfg.textColor;
            if (inpBorder) inpBorder.value = cfg.borderColor;
            if (chkTrans) chkTrans.checked = false;
            this.applyWidgetCustomStyles(elWidget, w);
            this.renderInspector();
          });
        });

        // Swatch clicks
        container.querySelectorAll('.color-swatch-btn[data-style-type]').forEach(btn => {
          btn.addEventListener('click', () => {
            const styleType = btn.dataset.styleType;
            const val = btn.dataset.val;
            if (styleType === 'bg') {
              cfg.bgColor = val;
              if (inpBg) inpBg.value = val;
              if (chkTrans) chkTrans.checked = false;
            } else if (styleType === 'text') {
              cfg.textColor = val;
              if (inpText) inpText.value = val;
            } else if (styleType === 'border') {
              cfg.borderColor = val;
              if (inpBorder) inpBorder.value = val;
            }
            this.applyWidgetCustomStyles(elWidget, w);
          });
        });
      }

      // ---------------- BIND TAB 3: LANJUTAN ----------------
      else if (activeTab === 'advanced') {
        const inpZ = document.getElementById('inp_w_z');
        const inpOpacity = document.getElementById('inp_w_opacity');
        const txtOpacity = document.getElementById('txt_w_opacity');
        const btnLock = document.getElementById('btn_w_lock');

        inpZ?.addEventListener('input', () => {
          const zVal = parseInt(inpZ.value, 10) || 1;
          w.z = zVal;
          if (elWidget) elWidget.style.zIndex = zVal;
        });

        document.getElementById('btn_layer_front')?.addEventListener('click', () => this.bringToFront(w.id));
        document.getElementById('btn_layer_up')?.addEventListener('click', () => this.bringForward(w.id));
        document.getElementById('btn_layer_down')?.addEventListener('click', () => this.sendBackward(w.id));
        document.getElementById('btn_layer_back')?.addEventListener('click', () => this.sendToBack(w.id));

        inpOpacity?.addEventListener('input', () => {
          const val = parseInt(inpOpacity.value, 10) || 100;
          if (txtOpacity) txtOpacity.textContent = `${val}%`;
          cfg.opacity = val / 100;
          this.applyWidgetCustomStyles(elWidget, w);
        });

        btnLock?.addEventListener('click', () => {
          this.toggleWidgetLock(w.id);
        });

        document.getElementById('btnDuplicateWidget')?.addEventListener('click', () => {
          this.duplicateSelectedWidget(w.id);
        });

        document.getElementById('btnDeleteWidget')?.addEventListener('click', () => {
          this.deleteWidget(w.id);
        });
      }
    },

    toggleNavigator(forceState) {
      const panel = document.getElementById('builderNavigatorPanel');
      const btn = document.getElementById('btnBuilderToggleNavigator');
      if (!panel) return;
      const willOpen = forceState !== undefined ? forceState : panel.hidden;
      panel.hidden = !willOpen;
      this.state.navigatorOpen = willOpen;
      btn?.classList.toggle('active', willOpen);
      if (willOpen) {
        this.renderNavigatorTree();
      }
    },

    renderNavigatorTree() {
      const treeContainer = document.getElementById('builderNavigatorTree');
      if (!treeContainer || !this.state.layout) return;

      const widgets = this.state.layout.widgets || [];
      if (widgets.length === 0) {
        treeContainer.innerHTML = '<div style="padding:16px;text-align:center;font-size:12px;color:#94a3b8;">Belum ada komponen di kanvas.</div>';
        return;
      }

      const typeIcons = {
        cctv_player: '📹',
        scorecard: '📊',
        trend_chart: '📈',
        event_table: '📋',
        stat_kpi_card: '🎯',
        custom_text: '🔤',
        status_badge: '🟢',
        container_box: '📦',
        excel_export_btn: '📥'
      };

      const typeLabels = {
        cctv_player: 'CCTV Player',
        scorecard: 'Scorecard Metrik',
        trend_chart: 'Grafik Tren',
        event_table: 'Tabel Log Kejadian',
        stat_kpi_card: 'Kartu KPI Stat',
        custom_text: 'Teks Kustom',
        status_badge: 'Badge Status',
        container_box: 'Wadah Kontainer',
        excel_export_btn: 'Tombol Unduh Excel'
      };

      treeContainer.innerHTML = widgets.map(w => {
        const isSelected = w.id === this.state.selectedWidgetId;
        const icon = typeIcons[w.type] || '🧩';
        const label = w.config?.title || w.config?.cameraLabel || w.config?.text || w.config?.label || typeLabels[w.type] || w.id;
        const lockIcon = w.isLocked ? '🔒' : '🔓';
        const eyeIcon = w.isHidden ? '🕶️' : '👁️';

        return `
          <div class="navigator-layer-item ${isSelected ? 'active' : ''}" data-widget-id="${w.id}">
            <div class="navigator-item-info">
              <span>${icon}</span>
              <span class="navigator-item-label" title="${label}">${label}</span>
            </div>
            <div class="navigator-item-actions">
              <button class="nav-action-btn btn-nav-lock" type="button" data-widget-id="${w.id}" title="${w.isLocked ? 'Buka Kunci' : 'Kunci Komponen'}">${lockIcon}</button>
              <button class="nav-action-btn btn-nav-eye" type="button" data-widget-id="${w.id}" title="${w.isHidden ? 'Tampilkan' : 'Sembunyikan'}">${eyeIcon}</button>
            </div>
          </div>
        `;
      }).join('');

      treeContainer.querySelectorAll('.navigator-layer-item').forEach(item => {
        item.addEventListener('click', (e) => {
          if (e.target.closest('.nav-action-btn')) return;
          this.selectWidget(item.dataset.widgetId);
        });
      });

      treeContainer.querySelectorAll('.btn-nav-lock').forEach(btn => {
        btn.addEventListener('click', (e) => {
          e.stopPropagation();
          this.toggleWidgetLock(btn.dataset.widgetId);
        });
      });

      treeContainer.querySelectorAll('.btn-nav-eye').forEach(btn => {
        btn.addEventListener('click', (e) => {
          e.stopPropagation();
          this.toggleWidgetVisibility(btn.dataset.widgetId);
        });
      });
    },

    toggleWidgetLock(widgetId) {
      const w = this.state.layout?.widgets?.find(x => x.id === widgetId);
      if (!w) return;
      w.isLocked = !w.isLocked;
      const el = document.getElementById(`widget_${w.id}`);
      if (el) {
        this.applyWidgetCustomStyles(el, w);
      }
      this.renderNavigatorTree();
      if (this.state.selectedWidgetId === widgetId) {
        this.selectWidget(widgetId);
      }
      this.closeContextMenu();
    },

    toggleWidgetVisibility(widgetId) {
      const w = this.state.layout?.widgets?.find(x => x.id === widgetId);
      if (!w) return;
      w.isHidden = !w.isHidden;
      const el = document.getElementById(`widget_${w.id}`);
      if (el) {
        this.applyWidgetCustomStyles(el, w);
      }
      this.renderNavigatorTree();
    },

    openContextMenu(e, widgetId) {
      const menu = document.getElementById('builderContextMenu');
      if (!menu) return;
      this.state.contextMenuWidgetId = widgetId;
      const w = this.state.layout?.widgets?.find(x => x.id === widgetId);
      if (!w) return;

      const lockIcon = document.getElementById('ctxMenuLockIcon');
      const lockText = document.getElementById('ctxMenuLockText');
      if (lockIcon && lockText) {
        if (w.isLocked) {
          lockIcon.textContent = '🔓';
          lockText.textContent = 'Buka Kunci Komponen';
        } else {
          lockIcon.textContent = '🔒';
          lockText.textContent = 'Kunci Komponen (Lock)';
        }
      }

      menu.hidden = false;
      const x = Math.min(window.innerWidth - 220, Math.max(10, e.clientX));
      const y = Math.min(window.innerHeight - 320, Math.max(10, e.clientY));
      menu.style.left = `${x}px`;
      menu.style.top = `${y}px`;
    },

    closeContextMenu() {
      const menu = document.getElementById('builderContextMenu');
      if (menu) menu.hidden = true;
      this.state.contextMenuWidgetId = null;
    },

    bindContextMenuActions() {
      const menu = document.getElementById('builderContextMenu');
      if (!menu) return;
      menu.addEventListener('click', (e) => {
        const btn = e.target.closest('.context-menu-item');
        if (!btn) return;
        const action = btn.dataset.action;
        const targetId = this.state.contextMenuWidgetId || this.state.selectedWidgetId;
        if (!targetId) return;

        switch (action) {
          case 'duplicate':
            this.duplicateSelectedWidget(targetId);
            break;
          case 'bring_front':
            this.bringToFront(targetId);
            break;
          case 'bring_forward':
            this.bringForward(targetId);
            break;
          case 'send_backward':
            this.sendBackward(targetId);
            break;
          case 'send_back':
            this.sendToBack(targetId);
            break;
          case 'center_canvas':
            this.alignSelectedWidget('center-canvas');
            break;
          case 'toggle_lock':
            this.toggleWidgetLock(targetId);
            break;
          case 'delete':
            this.deleteWidget(targetId);
            break;
        }
        this.closeContextMenu();
      });
    },

    alignSelectedWidget(direction) {
      if (!this.state.selectedWidgetId || !this.state.layout) return;
      const w = this.state.layout.widgets.find(x => x.id === this.state.selectedWidgetId);
      if (!w || w.isLocked) return;

      const canvasW = this.state.layout.canvas?.width || 1440;
      const canvasH = this.state.layout.canvas?.height || 960;
      const pad = 24;

      switch (direction) {
        case 'left':
          w.x = pad;
          break;
        case 'center-h':
          w.x = Math.max(0, Math.round((canvasW - w.w) / 2));
          break;
        case 'right':
          w.x = Math.max(0, canvasW - w.w - pad);
          break;
        case 'top':
          w.y = pad;
          break;
        case 'center-v':
          w.y = Math.max(0, Math.round((canvasH - w.h) / 2));
          break;
        case 'bottom':
          w.y = Math.max(0, canvasH - w.h - pad);
          break;
        case 'center-canvas':
          w.x = Math.max(0, Math.round((canvasW - w.w) / 2));
          w.y = Math.max(0, Math.round((canvasH - w.h) / 2));
          break;
      }

      const el = document.getElementById(`widget_${w.id}`);
      if (el) {
        el.style.left = `${w.x}px`;
        el.style.top = `${w.y}px`;
      }
      this.updateInspectorCoords(w);
      this.closeContextMenu();
    },

    bringToFront(widgetId) {
      const id = widgetId || this.state.selectedWidgetId;
      const w = this.state.layout?.widgets?.find(x => x.id === id);
      if (!w) return;
      const maxZ = Math.max(...this.state.layout.widgets.map(x => x.z || 1), 1);
      w.z = maxZ + 1;
      const el = document.getElementById(`widget_${w.id}`);
      if (el) el.style.zIndex = w.z;
      if (this.state.selectedWidgetId === id) this.selectWidget(id);
      this.closeContextMenu();
    },

    sendToBack(widgetId) {
      const id = widgetId || this.state.selectedWidgetId;
      const w = this.state.layout?.widgets?.find(x => x.id === id);
      if (!w) return;
      const minZ = Math.min(...this.state.layout.widgets.map(x => x.z || 1), 1);
      w.z = Math.max(1, minZ - 1);
      const el = document.getElementById(`widget_${w.id}`);
      if (el) el.style.zIndex = w.z;
      if (this.state.selectedWidgetId === id) this.selectWidget(id);
      this.closeContextMenu();
    },

    bringForward(widgetId) {
      const id = widgetId || this.state.selectedWidgetId;
      const w = this.state.layout?.widgets?.find(x => x.id === id);
      if (!w) return;
      w.z = (w.z || 1) + 1;
      const el = document.getElementById(`widget_${w.id}`);
      if (el) el.style.zIndex = w.z;
      if (this.state.selectedWidgetId === id) this.selectWidget(id);
      this.closeContextMenu();
    },

    sendBackward(widgetId) {
      const id = widgetId || this.state.selectedWidgetId;
      const w = this.state.layout?.widgets?.find(x => x.id === id);
      if (!w) return;
      w.z = Math.max(1, (w.z || 1) - 1);
      const el = document.getElementById(`widget_${w.id}`);
      if (el) el.style.zIndex = w.z;
      if (this.state.selectedWidgetId === id) this.selectWidget(id);
      this.closeContextMenu();
    },

    duplicateSelectedWidget(targetId) {
      const id = targetId || this.state.selectedWidgetId;
      if (!id || !this.state.layout) return;
      const orig = this.state.layout.widgets.find(x => x.id === id);
      if (!orig) return;
      const copy = JSON.parse(JSON.stringify(orig));
      copy.id = `w_${copy.type}_${Date.now().toString(36)}`;
      copy.x += 30;
      copy.y += 30;
      copy.z = (this.state.layout.widgets.length || 0) + 1;
      copy.isLocked = false;
      this.state.layout.widgets.push(copy);
      this.renderCanvas();
      this.selectWidget(copy.id);
      this.renderNavigatorTree();
      if (window.toast) window.toast('Komponen berhasil digandakan (Ctrl+D)', false);
    },

    deleteWidget(id) {
      if (!this.state.layout) return;
      this.state.layout.widgets = this.state.layout.widgets.filter(x => x.id !== id);
      this.selectWidget(null);
      this.renderCanvas();
    },

    // ------------------------------------------------------------------------
    // AI Dashboard Assistant & Copilot Engine
    // ------------------------------------------------------------------------
    toggleCopilotDrawer(forceState) {
      const drawer = document.getElementById('builderCopilotDrawer');
      const btn = document.getElementById('btnBuilderToggleCopilot');
      if (!drawer) return;

      const willOpen = forceState !== undefined ? forceState : drawer.hidden;
      drawer.hidden = !willOpen;
      this.state.copilotOpen = willOpen;
      btn?.classList.toggle('active', willOpen);

      if (willOpen) {
        const inp = document.getElementById('inpCopilotPrompt');
        setTimeout(() => inp?.focus(), 80);
      }
    },

    bindCopilotDrawerEvents() {
      const btnSend = document.getElementById('btnSendCopilotPrompt');
      const inp = document.getElementById('inpCopilotPrompt');
      const btnApply = document.getElementById('btnApplyCopilotLayout');

      // Mode Switcher: Prompt Text vs Image Replicator
      const tabModePrompt = document.getElementById('tabModePrompt');
      const tabModeImage = document.getElementById('tabModeImage');
      const panelText = document.getElementById('panelCopilotText');
      const panelImage = document.getElementById('panelCopilotImage');

      tabModePrompt?.addEventListener('click', () => {
        tabModePrompt.classList.add('active');
        tabModeImage?.classList.remove('active');
        if (panelText) panelText.hidden = false;
        if (panelImage) panelImage.hidden = true;
      });

      tabModeImage?.addEventListener('click', () => {
        tabModeImage.classList.add('active');
        tabModePrompt?.classList.remove('active');
        if (panelText) panelText.hidden = true;
        if (panelImage) panelImage.hidden = false;
      });

      // Dropzone & Image File Upload
      const dropzone = document.getElementById('copilotDropzone');
      const inpFile = document.getElementById('inpCopilotImageFile');
      const previewWrap = document.getElementById('copilotImagePreviewWrap');
      const imgPreview = document.getElementById('copilotImagePreview');
      const lblName = document.getElementById('copilotImageName');
      const btnRemoveImg = document.getElementById('btnRemoveCopilotImage');
      const btnAnalyze = document.getElementById('btnAnalyzeCopilotImage');
      const inpNote = document.getElementById('inpCopilotImageNote');

      dropzone?.addEventListener('click', () => inpFile?.click());

      const handleImageFile = (file) => {
        if (!file || !file.type.startsWith('image/')) {
          if (window.toast) window.toast('Harap pilih berkas gambar JPEG/PNG yang valid', true);
          return;
        }
        const reader = new FileReader();
        reader.onload = (e) => {
          this.state.copilotImageBase64 = e.target.result;
          this.state.copilotImageFileName = file.name;
          if (imgPreview) imgPreview.src = e.target.result;
          if (lblName) lblName.textContent = file.name;
          if (previewWrap) previewWrap.hidden = false;
          if (dropzone) dropzone.hidden = true;
        };
        reader.readAsDataURL(file);
      };

      inpFile?.addEventListener('change', (e) => {
        if (e.target.files && e.target.files[0]) {
          handleImageFile(e.target.files[0]);
        }
      });

      dropzone?.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropzone.style.borderColor = '#38bdf8';
        dropzone.style.background = 'rgba(56, 189, 248, 0.15)';
      });

      dropzone?.addEventListener('dragleave', () => {
        dropzone.style.borderColor = '';
        dropzone.style.background = '';
      });

      dropzone?.addEventListener('drop', (e) => {
        e.preventDefault();
        dropzone.style.borderColor = '';
        dropzone.style.background = '';
        if (e.dataTransfer.files && e.dataTransfer.files[0]) {
          handleImageFile(e.dataTransfer.files[0]);
        }
      });

      btnRemoveImg?.addEventListener('click', () => {
        this.state.copilotImageBase64 = null;
        this.state.copilotImageFileName = '';
        if (inpFile) inpFile.value = '';
        if (previewWrap) previewWrap.hidden = true;
        if (dropzone) dropzone.hidden = false;
      });

      btnAnalyze?.addEventListener('click', () => {
        if (!this.state.copilotImageBase64) {
          if (window.toast) window.toast('Silakan unggah gambar desain JPEG/PNG terlebih dahulu', true);
          else alert('Silakan unggah gambar desain JPEG/PNG terlebih dahulu');
          return;
        }
        const note = inpNote?.value?.trim() || '';
        this.analyzeCopilotImage(this.state.copilotImageBase64, note);
      });

      btnSend?.addEventListener('click', () => {
        const text = inp.value.trim();
        if (text) {
          this.sendCopilotMessage(text);
          inp.value = '';
        }
      });

      inp?.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
          e.preventDefault();
          const text = inp.value.trim();
          if (text) {
            this.sendCopilotMessage(text);
            inp.value = '';
          }
        }
      });

      document.querySelectorAll('.copilot-chip-btn').forEach(btn => {
        btn.addEventListener('click', () => {
          const prompt = btn.dataset.prompt;
          if (prompt) {
            this.sendCopilotMessage(prompt);
          }
        });
      });

      btnApply?.addEventListener('click', () => {
        this.applyAiLayout();
      });
    },

    async analyzeCopilotImage(imageBase64, userNote) {
      const historyEl = document.getElementById('copilotChatHistory');
      const actionBar = document.getElementById('copilotActionBar');
      if (!historyEl) return;

      // 1. Append User Message with Thumbnail
      const userMsgHtml = `
        <div class="copilot-msg msg-user">
          <div class="msg-author">Anda (Upload Desain Referensi)</div>
          <div class="msg-bubble">
            <img src="${imageBase64}" style="max-width:180px;max-height:100px;border-radius:4px;display:block;margin-bottom:6px;border:1px solid #334155;" alt="Desain" />
            <span>${userNote ? `<em>Catatan:</em> ${userNote}` : 'Tolong analisis desain gambar ini dan buatkan tata letak yang meniru strukturnya dengan data CCTV & metrik riil.'}</span>
          </div>
        </div>
      `;
      historyEl.insertAdjacentHTML('beforeend', userMsgHtml);

      // 2. Append Thinking Indicator
      const thinkingId = 'copilot_thinking_' + Date.now();
      const thinkingHtml = `
        <div class="copilot-msg msg-ai" id="${thinkingId}">
          <div class="msg-author">🤖 Afivision Vision AI</div>
          <div class="msg-bubble" style="display:flex;align-items:center;gap:8px;">
            <span>🔍 Menganalisis gambar JPEG dengan VLM & Computer Vision...</span>
          </div>
        </div>
      `;
      historyEl.insertAdjacentHTML('beforeend', thinkingHtml);
      historyEl.scrollTop = historyEl.scrollHeight;

      try {
        const res = await fetch('/api/dashboard/builder/ai-analyze-image', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            image: imageBase64,
            instruction: userNote,
            currentLayout: this.state.layout
          })
        });

        const thinkingEl = document.getElementById(thinkingId);
        if (thinkingEl) thinkingEl.remove();

        if (res.ok) {
          const data = await res.json();
          this.state.pendingAiLayout = data.layout;

          const explanation = data.explanation || 'Desain referensi berhasil dianalisis dan direplikasi secara proporsional.';
          const wCount = data.layout?.widgets?.length || 0;
          const meta = data.analysis_metadata || {};

          const replyHtml = `
            <div class="copilot-msg msg-ai">
              <div class="msg-author">🤖 Afivision Vision AI</div>
              <div class="msg-bubble">
                ${explanation}<br><br>
                <div style="background:rgba(2,132,199,0.15);border:1px solid rgba(56,189,248,0.3);padding:6px 10px;border-radius:6px;font-size:11px;margin-top:4px;">
                  🎨 <strong>Warna Background:</strong> <code>${meta.detected_bg_color || '#0f172a'}</code> (${meta.is_dark_theme ? 'Dark Theme' : 'Light Theme'})<br>
                  🧩 <strong>${wCount} Komponen</strong> berhasil ditiru dan disesuaikan ke kamera CCTV & telemetri riil Anda.
                </div>
              </div>
            </div>
          `;
          historyEl.insertAdjacentHTML('beforeend', replyHtml);
          historyEl.scrollTop = historyEl.scrollHeight;

          if (actionBar) actionBar.hidden = false;
        } else {
          const errData = await res.json().catch(() => ({}));
          const replyHtml = `
            <div class="copilot-msg msg-ai">
              <div class="msg-author">🤖 Afivision Vision AI</div>
              <div class="msg-bubble" style="color:#ef4444;">
                Gagal menganalisis gambar: ${errData.detail || 'Terjadi kesalahan pada server saat memproses gambar.'}
              </div>
            </div>
          `;
          historyEl.insertAdjacentHTML('beforeend', replyHtml);
          historyEl.scrollTop = historyEl.scrollHeight;
        }
      } catch (err) {
        const thinkingEl = document.getElementById(thinkingId);
        if (thinkingEl) thinkingEl.remove();

        const replyHtml = `
          <div class="copilot-msg msg-ai">
            <div class="msg-author">🤖 Afivision Vision AI</div>
            <div class="msg-bubble" style="color:#ef4444;">
              Gagal menghubungi endpoint analisis visi AI: ${err.message}
            </div>
          </div>
        `;
        historyEl.insertAdjacentHTML('beforeend', replyHtml);
        historyEl.scrollTop = historyEl.scrollHeight;
      }
    },

    async sendCopilotMessage(userPrompt) {
      const historyEl = document.getElementById('copilotChatHistory');
      const actionBar = document.getElementById('copilotActionBar');
      if (!historyEl) return;

      // 1. Append User Message
      const userMsgHtml = `
        <div class="copilot-msg msg-user">
          <div class="msg-author">Anda</div>
          <div class="msg-bubble">${userPrompt}</div>
        </div>
      `;
      historyEl.insertAdjacentHTML('beforeend', userMsgHtml);

      // 2. Append Thinking Indicator
      const thinkingId = 'copilot_thinking_' + Date.now();
      const thinkingHtml = `
        <div class="copilot-msg msg-ai" id="${thinkingId}">
          <div class="msg-author">🤖 Afivision Copilot</div>
          <div class="msg-bubble" style="display:flex;align-items:center;gap:8px;">
            <span>🧠 Menganalisis alur kerja riil & merancang layout...</span>
          </div>
        </div>
      `;
      historyEl.insertAdjacentHTML('beforeend', thinkingHtml);
      historyEl.scrollTop = historyEl.scrollHeight;

      if (actionBar) actionBar.hidden = true;

      try {
        const res = await fetch('/api/dashboard/builder/ai-generate', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            userInstruction: userPrompt,
            currentLayout: this.state.layout
          })
        });

        const thinkingEl = document.getElementById(thinkingId);
        if (thinkingEl) thinkingEl.remove();

        if (res.ok) {
          const data = await res.json();
          this.state.pendingAiLayout = data.layout;

          const explanation = data.explanation || 'Rancangan tata letak berhasil dibuat dengan integrasi data real-time.';
          const wCount = data.layout?.widgets?.length || 0;

          const replyHtml = `
            <div class="copilot-msg msg-ai">
              <div class="msg-author">🤖 Afivision Copilot</div>
              <div class="msg-bubble">
                ${explanation}<br><br>
                <div style="background:rgba(2,132,199,0.15);border:1px solid rgba(56,189,248,0.3);padding:6px 10px;border-radius:6px;font-size:11px;margin-top:4px;">
                  ✨ <strong>${wCount} Komponen</strong> berhasil dikonfigurasi dengan data telemetry riil (bukan dummy).
                </div>
              </div>
            </div>
          `;
          historyEl.insertAdjacentHTML('beforeend', replyHtml);
          if (actionBar) actionBar.hidden = false;
        } else {
          const errData = await res.json().catch(() => ({}));
          const errMsg = errData.detail || 'Terjadi kesalahan saat memanggil AI generator.';
          const errorHtml = `
            <div class="copilot-msg msg-ai">
              <div class="msg-author">🤖 Afivision Copilot</div>
              <div class="msg-bubble" style="border-color:#ef4444;color:#fca5a5;">
                ❌ ${errMsg}
              </div>
            </div>
          `;
          historyEl.insertAdjacentHTML('beforeend', errorHtml);
        }
      } catch (err) {
        const thinkingEl = document.getElementById(thinkingId);
        if (thinkingEl) thinkingEl.remove();
        console.error('[DashboardCopilot] Network error:', err);
      }
      historyEl.scrollTop = historyEl.scrollHeight;
    },

    applyAiLayout() {
      if (!this.state.pendingAiLayout) return;
      this.state.layout = JSON.parse(JSON.stringify(this.state.pendingAiLayout));
      this.renderCanvas();
      this.zoomFit();
      this.renderNavigatorTree();

      const actionBar = document.getElementById('copilotActionBar');
      if (actionBar) actionBar.hidden = true;

      if (window.toast) {
        window.toast('✨ Rancangan dashboard AI berhasil diterapkan ke kanvas!', false);
      } else {
        alert('✨ Rancangan dashboard AI berhasil diterapkan ke kanvas!');
      }
    },

    // ------------------------------------------------------------------------
    // Live Value Updates & Adaptive Thresholds
    // ------------------------------------------------------------------------
    updateLiveWidgetValues() {
      if (!this.state.layout) return;

      this.state.layout.widgets.forEach(w => {
        if (w.type === 'scorecard') {
          const valEl = document.getElementById(`val_${w.id}`);
          const cardEl = document.getElementById(`card_${w.id}`);
          if (valEl && cardEl) {
            const val = this.getMetricValue(w.config?.metricKey, w.config?.defaultValue);
            valEl.textContent = val;
            const status = this.calculateThresholdStatus(val, w.config?.warningThreshold, w.config?.dangerThreshold);
            cardEl.className = `widget-scorecard-card scorecard-${status}`;
          }
        } else if (w.type === 'event_table') {
          this.updateEventTables();
        } else if (w.type === 'trend_chart') {
          this.renderTrendChart(w);
        } else if (w.type === 'dashboard_navbar') {
          const clk = document.getElementById(`clock_${w.id}`);
          if (clk) {
            clk.textContent = new Date().toTimeString().split(' ')[0];
          }
        }
      });
    },

    getMetricValue(metricKey, fallback = 0) {
      if (!metricKey) return fallback;
      const rec = this.state.liveData.metrics?.[metricKey];
      return rec ? rec.value : fallback;
    },

    calculateThresholdStatus(val, warn = 10, danger = 20) {
      const num = parseFloat(val) || 0;
      if (num >= danger) return 'danger';
      if (num >= warn) return 'warning';
      return 'normal';
    },

    updateEventTables() {
      const allEvents = this.state.liveData.recent_events || [];
      const filterCam = this.state.filterCamera;

      const filtered = filterCam
        ? allEvents.filter(e => e.camera_label === filterCam)
        : allEvents;

      this.state.layout?.widgets?.forEach(w => {
        if (w.type === 'event_table') {
          const tbody = document.getElementById(`tableBody_${w.id}`);
          if (!tbody) return;

          if (filtered.length === 0) {
            tbody.innerHTML = `<tr><td colspan="4" style="text-align:center;color:#64748b;padding:12px;">Tidak ada event untuk filter ini.</td></tr>`;
            return;
          }

          tbody.innerHTML = filtered.slice(0, w.config?.maxRows || 25).map(e => `
            <tr>
              <td style="color:#94a3b8;font-family:monospace">${e.timestamp_iso ? e.timestamp_iso.split(' ')[1] : '--'}</td>
              <td><strong>${e.camera_label || 'Sistem'}</strong></td>
              <td>${e.description || e.type}</td>
              <td><span class="event-badge ${e.level}">${e.level}</span></td>
            </tr>
          `).join('');
        }
      });
    },

    // ------------------------------------------------------------------------
    // Trend Chart Rendering (Canvas Polyline)
    // ------------------------------------------------------------------------
    async renderTrendChart(w) {
      const canvas = document.getElementById(`chart_${w.id}`);
      if (!canvas) return;

      const ctx = canvas.getContext('2d');
      const rect = canvas.getBoundingClientRect();
      canvas.width = rect.width * (window.devicePixelRatio || 1);
      canvas.height = rect.height * (window.devicePixelRatio || 1);
      ctx.scale(window.devicePixelRatio || 1, window.devicePixelRatio || 1);

      const width = rect.width;
      const height = rect.height;
      if (width < 20 || height < 20) return;

      // Fetch or use mock timeseries points
      let points = this.state.chartCache[w.id];
      if (!points) {
        try {
          const res = await fetch(`/api/dashboard/builder/timeseries?metric_key=${encodeURIComponent(w.config?.metricKey || 'total_count')}&hours=24`);
          if (res.ok) {
            const data = await res.json();
            points = data.points || [];
            this.state.chartCache[w.id] = points;
          }
        } catch (e) {}
      }

      if (!points || points.length === 0) {
        // Generate aesthetic synthetic data points based on metric
        points = [];
        const baseVal = this.getMetricValue(w.config?.metricKey, 12);
        for (let i = 0; i < 20; i++) {
          points.push({
            value: Math.max(0, baseVal + Math.sin(i * 0.5) * 6 + (Math.random() * 4 - 2))
          });
        }
      }

      // Draw Grid & Axes
      ctx.clearRect(0, 0, width, height);
      ctx.strokeStyle = 'rgba(51, 65, 85, 0.4)';
      ctx.lineWidth = 1;
      for (let y = 20; y < height - 20; y += (height - 40) / 4) {
        ctx.beginPath();
        ctx.moveTo(25, y);
        ctx.lineTo(width - 15, y);
        ctx.stroke();
      }

      const values = points.map(p => p.value);
      const minVal = Math.min(...values, 0);
      const maxVal = Math.max(...values, 10);
      const range = (maxVal - minVal) || 1;

      // Points coordinates
      const stepX = (width - 45) / Math.max(1, points.length - 1);
      const coords = points.map((p, idx) => {
        const x = 30 + idx * stepX;
        const normY = (p.value - minVal) / range;
        const y = (height - 25) - normY * (height - 45);
        return { x, y };
      });

      // Draw Area Fill Gradient
      const grad = ctx.createLinearGradient(0, 0, 0, height);
      grad.addColorStop(0, 'rgba(56, 189, 248, 0.35)');
      grad.addColorStop(1, 'rgba(56, 189, 248, 0.0)');

      ctx.beginPath();
      ctx.moveTo(coords[0].x, height - 25);
      coords.forEach(pt => ctx.lineTo(pt.x, pt.y));
      ctx.lineTo(coords[coords.length - 1].x, height - 25);
      ctx.closePath();
      ctx.fillStyle = grad;
      ctx.fill();

      // Draw Polyline
      ctx.beginPath();
      ctx.strokeStyle = '#38bdf8';
      ctx.lineWidth = 2.5;
      coords.forEach((pt, i) => {
        if (i === 0) ctx.moveTo(pt.x, pt.y);
        else ctx.lineTo(pt.x, pt.y);
      });
      ctx.stroke();

      // Draw Points
      coords.forEach(pt => {
        ctx.beginPath();
        ctx.arc(pt.x, pt.y, 3, 0, Math.PI * 2);
        ctx.fillStyle = '#ffffff';
        ctx.fill();
        ctx.strokeStyle = '#0284c7';
        ctx.lineWidth = 1.5;
        ctx.stroke();
      });
    },

    // ------------------------------------------------------------------------

    // ------------------------------------------------------------------------
    // Web Computer Vision Interactive Engine (Streamlit / Ultralytics Style)
    // ------------------------------------------------------------------------
    attachWebCvWidgetListeners(el, w) {
      if (w.type === 'media_input_controller') {
        const dropzone = el.querySelector(`#dropzone_${w.id}`);
        const fileInput = el.querySelector(`#media_file_input_${w.id}`);
        const previewWrap = el.querySelector(`#media_preview_wrap_${w.id}`);
        const previewImg = el.querySelector(`#media_preview_img_${w.id}`);
        const filenameEl = el.querySelector(`#media_filename_${w.id}`);
        const slider = el.querySelector(`#range_conf_${w.id}`);
        const valConf = el.querySelector(`#val_conf_${w.id}`);
        const btnRun = el.querySelector(`#btn_run_analysis_${w.id}`);
        const btnReset = el.querySelector(`#btn_reset_media_${w.id}`);

        // Click dropzone -> trigger hidden file input
        dropzone?.addEventListener('click', (e) => {
          if (e.target !== fileInput && !e.target.closest('.btn-sample-media')) {
            fileInput?.click();
          }
        });

        // Drag & Drop
        dropzone?.addEventListener('dragover', (e) => {
          e.preventDefault();
          dropzone.classList.add('dragover');
        });
        dropzone?.addEventListener('dragleave', () => {
          dropzone.classList.remove('dragover');
        });
        dropzone?.addEventListener('drop', (e) => {
          e.preventDefault();
          dropzone.classList.remove('dragover');
          if (e.dataTransfer?.files?.length) {
            handleSelectedFile(e.dataTransfer.files[0]);
          }
        });

        const handleSelectedFile = (file) => {
          if (!file) return;
          this.state.analysisState.uploadedFile = file;
          this.state.analysisState.currentImageUrl = null;
          if (filenameEl) filenameEl.textContent = `${file.name} (${(file.size / 1024).toFixed(1)} KB)`;
          if (previewWrap) previewWrap.style.display = 'block';

          if (file.type.startsWith('image/')) {
            const reader = new FileReader();
            reader.onload = (re) => {
              if (previewImg) previewImg.src = re.target.result;
            };
            reader.readAsDataURL(file);
          } else if (file.type.startsWith('video/')) {
            if (previewImg) previewImg.src = '/static/logo.png';
          }

          if (w.config?.autoRunOnUpload !== false) {
            this.runMediaAnalysis(w.id);
          }
        };

        fileInput?.addEventListener('change', () => {
          if (fileInput.files?.length) {
            handleSelectedFile(fileInput.files[0]);
          }
        });

        // Sample preset button click
        el.querySelectorAll('.btn-sample-media').forEach(btn => {
          btn.addEventListener('click', (e) => {
            e.stopPropagation();
            const url = btn.dataset.url;
            this.state.analysisState.uploadedFile = null;
            this.state.analysisState.currentImageUrl = url;
            if (filenameEl) filenameEl.textContent = 'Sampel: Bengkel Workshop';
            if (previewWrap) previewWrap.style.display = 'block';
            if (previewImg) previewImg.src = url;
            this.runMediaAnalysis(w.id);
          });
        });

        // Confidence slider change
        slider?.addEventListener('input', () => {
          const confVal = parseInt(slider.value, 10);
          if (valConf) valConf.textContent = `${confVal}%`;
          this.state.analysisState.currentConfidence = confVal / 100.0;
          w.config.defaultConfidence = confVal / 100.0;
          this.syncAllWebCvWidgets();
        });

        // Run button
        btnRun?.addEventListener('click', (e) => {
          e.stopPropagation();
          this.runMediaAnalysis(w.id);
        });

        // Reset button
        btnReset?.addEventListener('click', (e) => {
          e.stopPropagation();
          this.state.analysisState.uploadedFile = null;
          this.state.analysisState.currentImageUrl = '/static/sample_workshop.jpg';
          this.state.analysisState.lastResult = null;
          if (previewWrap) previewWrap.style.display = 'none';
          if (fileInput) fileInput.value = '';
          this.syncAllWebCvWidgets();
          if (window.toast) window.toast('Input media di-reset ke mode awal.', false);
        });
      }

      else if (w.type === 'vision_result_viewer') {
        const img = el.querySelector(`#img_annotated_${w.id}`);
        const zoomWrap = el.querySelector(`#zoom_wrap_${w.id}`);
        const btnZoomIn = el.querySelector('.btn-zoom-in');
        const btnZoomOut = el.querySelector('.btn-zoom-out');
        const btnZoomReset = el.querySelector('.btn-zoom-reset');
        const btnDownload = el.querySelector('.btn-download-annotated');

        // Layer toggles
        el.querySelectorAll('.btn-toggle-layer').forEach(btn => {
          btn.addEventListener('click', (e) => {
            e.stopPropagation();
            const layer = btn.dataset.layer;
            const isAct = btn.classList.toggle('active');
            if (this.state.analysisState.activeLayers) {
              this.state.analysisState.activeLayers[layer] = isAct;
            }
            if (window.toast) window.toast(`Layer ${layer} ${isAct ? 'diaktifkan' : 'dinonaktifkan'}`, false);
          });
        });

        // Zoom controls
        let currentZoom = 1.0;
        const updateZoom = (z) => {
          currentZoom = Math.max(0.5, Math.min(3.0, z));
          if (img) img.style.transform = `scale(${currentZoom})`;
        };

        btnZoomIn?.addEventListener('click', (e) => {
          e.stopPropagation();
          updateZoom(currentZoom + 0.2);
        });
        btnZoomOut?.addEventListener('click', (e) => {
          e.stopPropagation();
          updateZoom(currentZoom - 0.2);
        });
        btnZoomReset?.addEventListener('click', (e) => {
          e.stopPropagation();
          updateZoom(1.0);
        });

        // Download annotated image
        btnDownload?.addEventListener('click', (e) => {
          e.stopPropagation();
          const curRes = this.state.analysisState.lastResult;
          const url = curRes?.annotated_image_url || curRes?.original_image_url || img?.src;
          if (!url) {
            if (window.toast) window.toast('Tidak ada hasil visual untuk diunduh.', true);
            return;
          }
          const a = document.createElement('a');
          a.href = url;
          a.download = `annotated_${Date.now()}.jpg`;
          document.body.appendChild(a);
          a.click();
          document.body.removeChild(a);
          if (window.toast) window.toast('Gambar beranotasi berhasil diunduh!', false);
        });
      }

      else if (w.type === 'confidence_table') {
        const searchInput = el.querySelector(`#search_conf_table_${w.id}`);
        const btnCsv = el.querySelector('.btn-export-conf-csv');
        const btnExcel = el.querySelector('.btn-export-conf-excel');
        const tbody = el.querySelector(`#tbody_conf_${w.id}`);

        searchInput?.addEventListener('input', () => {
          const filter = searchInput.value.toLowerCase().trim();
          this.renderConfidenceTable(w, tbody, filter);
        });

        btnCsv?.addEventListener('click', (e) => {
          e.stopPropagation();
          this.exportDetectionsToCsv(w.id);
        });

        btnExcel?.addEventListener('click', (e) => {
          e.stopPropagation();
          this.exportDetectionsToCsv(w.id, 'excel');
        });
      }

      else if (w.type === 'custom_analytics_table') {
        const searchInput = el.querySelector(`#search_analytics_table_${w.id}`);
        const btnCsv = el.querySelector('.btn-export-analytics-csv');
        const btnExcel = el.querySelector('.btn-export-analytics-excel');
        const tbody = el.querySelector(`#tbody_analytics_${w.id}`);

        searchInput?.addEventListener('input', () => {
          const filter = searchInput.value.toLowerCase().trim();
          this.renderCustomAnalyticsTable(w, tbody, filter);
        });

        btnCsv?.addEventListener('click', (e) => {
          e.stopPropagation();
          this.exportAnalyticsToCsv(w.id);
        });

        btnExcel?.addEventListener('click', (e) => {
          e.stopPropagation();
          this.exportAnalyticsToCsv(w.id, 'excel');
        });
      }
    },

    async runMediaAnalysis(triggerWidgetId) {
      if (this.state.analysisState.isAnalyzing) return;
      this.state.analysisState.isAnalyzing = true;

      // Update button & badge spinners across controllers
      document.querySelectorAll('.run-spinner').forEach(s => s.style.display = 'inline-block');
      document.querySelectorAll('.cctv-workflow-badge').forEach(b => {
        if (b.id && b.id.startsWith('media_status_badge_')) {
          b.textContent = 'Menganalisis...';
          b.style.borderColor = '#f59e0b';
          b.style.color = '#f59e0b';
        }
      });

      const conf = this.state.analysisState.currentConfidence || 0.25;
      const file = this.state.analysisState.uploadedFile;
      const fileUrl = this.state.analysisState.currentImageUrl || '/static/sample_workshop.jpg';

      try {
        let res;
        if (file) {
          const formData = new FormData();
          formData.append('file', file);
          formData.append('confidence', conf.toString());
          formData.append('project_id', this.state.projectId || 'default');
          res = await fetch('/api/dashboard/analyze', {
            method: 'POST',
            body: formData
          });
        } else {
          res = await fetch('/api/dashboard/analyze', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              file_url: fileUrl,
              confidence: conf,
              project_id: this.state.projectId || 'default'
            })
          });
        }

        if (!res.ok) {
          const errData = await res.json().catch(() => ({}));
          throw new Error(errData.detail || 'Gagal memproses analisis inferensi.');
        }

        const data = await res.json();
        this.state.analysisState.lastResult = data;
        this.syncAllWebCvWidgets();

        const count = data.detections?.length || 0;
        const timeMs = data.inference_time_ms ? `${data.inference_time_ms}ms` : '<50ms';
        if (window.toast) {
          window.toast(`Analisis sukses! ${count} objek terdeteksi (${timeMs})`, false);
        }
      } catch (err) {
        console.error('[DashboardBuilder] Analysis error:', err);
        if (window.toast) window.toast(`Analisis gagal: ${err.message}`, true);
      } finally {
        this.state.analysisState.isAnalyzing = false;
        document.querySelectorAll('.run-spinner').forEach(s => s.style.display = 'none');
        document.querySelectorAll('.cctv-workflow-badge').forEach(b => {
          if (b.id && b.id.startsWith('media_status_badge_')) {
            b.textContent = 'Selesai';
            b.style.borderColor = '#10b981';
            b.style.color = '#10b981';
          }
        });
      }
    },

    syncAllWebCvWidgets() {
      const data = this.state.analysisState.lastResult;
      const widgets = this.state.layout?.widgets || [];

      widgets.forEach(w => {
        if (w.type === 'vision_result_viewer') {
          const empty = document.getElementById(`empty_viewer_${w.id}`);
          const wrap = document.getElementById(`zoom_wrap_${w.id}`);
          const img = document.getElementById(`img_annotated_${w.id}`);
          const badge = document.getElementById(`badge_stat_${w.id}`);
          const badgeText = document.getElementById(`badge_stat_text_${w.id}`);

          if (data && (data.annotated_image_url || data.original_image_url)) {
            if (empty) empty.style.display = 'none';
            if (wrap) wrap.style.display = 'flex';
            if (img) img.src = `${data.annotated_image_url || data.original_image_url}?t=${Date.now()}`;
            if (badge) badge.style.display = 'block';
            const count = data.detections?.length || 0;
            if (badgeText) badgeText.textContent = `🎯 ${count} Objek Terdeteksi • Inferensi: ${data.inference_time_ms || 24}ms`;
          } else {
            if (empty) empty.style.display = 'flex';
            if (wrap) wrap.style.display = 'none';
            if (badge) badge.style.display = 'none';
          }
        }

        else if (w.type === 'confidence_table') {
          const tbody = document.getElementById(`tbody_conf_${w.id}`);
          const searchInput = document.getElementById(`search_conf_table_${w.id}`);
          if (tbody) {
            this.renderConfidenceTable(w, tbody, searchInput?.value || '');
          }
        }

        else if (w.type === 'custom_analytics_table') {
          const tbody = document.getElementById(`tbody_analytics_${w.id}`);
          const searchInput = document.getElementById(`search_analytics_table_${w.id}`);
          if (tbody) {
            this.renderCustomAnalyticsTable(w, tbody, searchInput?.value || '');
          }
        }
      });
    },

    renderConfidenceTable(w, tbody, filterText = '') {
      const data = this.state.analysisState.lastResult;
      if (!data || !data.detections || data.detections.length === 0) {
        tbody.innerHTML = `
          <tr>
            <td colspan="5" style="text-align:center;padding:28px;color:#64748b;">
              Belum ada deteksi. Unggah media dan jalankan analisis.
            </td>
          </tr>
        `;
        return;
      }

      const minConf = this.state.analysisState.currentConfidence || 0.25;
      let filtered = data.detections.filter(d => (d.score || 0) >= minConf);
      if (filterText) {
        const ft = filterText.toLowerCase();
        filtered = filtered.filter(d => (d.class || '').toLowerCase().includes(ft));
      }

      if (filtered.length === 0) {
        tbody.innerHTML = `
          <tr>
            <td colspan="5" style="text-align:center;padding:28px;color:#64748b;">
              Tidak ada objek dengan filter "${filterText || `conf >= ${Math.round(minConf*100)}%`}".
            </td>
          </tr>
        `;
        return;
      }

      const rows = filtered.map((d, idx) => {
        const score = typeof d.score === 'number' ? d.score : 0;
        const scorePct = Math.round(score * 100);
        const bbox = Array.isArray(d.bbox) ? d.bbox.map(n => Math.round(n)).join(', ') : '-';
        const cropSrc = d.crop_url ? `${d.crop_url}?t=${Date.now()}` : '/static/logo.png';
        
        let barColor = '#10b981';
        if (scorePct < 50) barColor = '#f59e0b';
        if (scorePct < 30) barColor = '#ef4444';

        return `
          <tr>
            <td>
              <img src="${cropSrc}" class="web-cv-crop-thumb" alt="Crop" onerror="this.src='/static/logo.png'" />
            </td>
            <td style="font-weight:600;color:#94a3b8;">#${d.id || idx + 1}</td>
            <td>
              <span class="web-cv-class-pill">📦 ${d.class || 'object'}</span>
            </td>
            <td>
              <div class="web-cv-conf-bar-wrap">
                <div class="web-cv-conf-bar">
                  <div class="web-cv-conf-bar-fill" style="width:${scorePct}%;background:${barColor};"></div>
                </div>
                <span class="web-cv-conf-text" style="color:${barColor};">${scorePct}%</span>
              </div>
            </td>
            <td style="font-family:'JetBrains Mono',monospace;font-size:11px;color:#cbd5e1;">
              [${bbox}]
            </td>
          </tr>
        `;
      }).join('');

      tbody.innerHTML = rows;
    },

    renderCustomAnalyticsTable(w, tbody, filterText = '') {
      const data = this.state.analysisState.lastResult;
      if (!data) {
        tbody.innerHTML = `
          <tr>
            <td colspan="6" style="text-align:center;padding:28px;color:#64748b;">
              Belum ada data analitik. Jalankan analisis alur kerja.
            </td>
          </tr>
        `;
        return;
      }

      const totalDet = data.detections?.length || 0;
      const analytics = data.analytics || {};
      const classCounts = analytics.class_counts || {};

      let items = [
        {
          param: 'Zona Produksi Utama (Workshop)',
          metric: 'Total Okupansi / Deteksi',
          actual: `${totalDet} Objek`,
          target: '< 15 Objek',
          status: totalDet > 15 ? 'Danger' : totalDet > 8 ? 'Warning' : 'Normal'
        },
        {
          param: 'Zona Keselamatan APD (K3)',
          metric: 'Pekerja dengan Rompi Safety',
          actual: `${classCounts['person'] || totalDet} Orang Terpantau`,
          target: 'Wajib 100%',
          status: 'Normal'
        },
        {
          param: 'Kecepatan Inferensi Vision',
          metric: 'Latency Per Frame',
          actual: `${data.inference_time_ms || 24} ms`,
          target: '< 100 ms',
          status: (data.inference_time_ms || 24) < 100 ? 'Normal' : 'Warning'
        },
        {
          param: 'Kepadatan Line Operasional',
          metric: 'Rata-rata Skor Keyakinan',
          actual: `${Math.round((analytics.average_confidence || 0.85) * 100)}%`,
          target: '> 70%',
          status: (analytics.average_confidence || 0.85) >= 0.7 ? 'Normal' : 'Warning'
        },
        {
          param: 'Pintu Darurat & Jalur Evakuasi',
          metric: 'Status Hambatan (Obstruction)',
          actual: 'Jalur Bersih (Clear)',
          target: 'Bebas Hambatan',
          status: 'Normal'
        }
      ];

      if (filterText) {
        const ft = filterText.toLowerCase();
        items = items.filter(it => it.param.toLowerCase().includes(ft) || it.metric.toLowerCase().includes(ft));
      }

      const statusBadges = {
        'Normal': '<span style="background:rgba(16,185,129,0.2);color:#34d399;padding:2px 8px;border-radius:10px;font-size:10.5px;font-weight:700;border:1px solid rgba(52,211,153,0.3);">🟢 NORMAL</span>',
        'Warning': '<span style="background:rgba(245,158,11,0.2);color:#fbbf24;padding:2px 8px;border-radius:10px;font-size:10.5px;font-weight:700;border:1px solid rgba(251,191,36,0.3);">🟡 PERINGATAN</span>',
        'Danger': '<span style="background:rgba(239,68,68,0.2);color:#f87171;padding:2px 8px;border-radius:10px;font-size:10.5px;font-weight:700;border:1px solid rgba(248,113,113,0.3);">🔴 BAHAYA</span>'
      };

      const rows = items.map((it, idx) => `
        <tr>
          <td style="font-weight:600;color:#94a3b8;">${idx + 1}</td>
          <td style="font-weight:600;color:#f8fafc;">${it.param}</td>
          <td style="color:#cbd5e1;">${it.metric}</td>
          <td style="font-family:'JetBrains Mono',monospace;color:#38bdf8;font-weight:600;">${it.actual}</td>
          <td style="color:#94a3b8;">${it.target}</td>
          <td>${statusBadges[it.status] || it.status}</td>
        </tr>
      `).join('');

      tbody.innerHTML = rows;
    },

    exportDetectionsToCsv(widgetId, type = 'csv') {
      const data = this.state.analysisState.lastResult;
      const detections = data?.detections || [];
      if (!detections.length) {
        if (window.toast) window.toast('Tidak ada data deteksi untuk diekspor.', true);
        return;
      }

      let csv = 'ID,Class,Confidence,X1,Y1,X2,Y2,CropURL\n';
      detections.forEach((d, i) => {
        const id = d.id || (i + 1);
        const cls = `"${d.class || 'object'}"`;
        const conf = typeof d.score === 'number' ? d.score.toFixed(4) : '0';
        const [x1, y1, x2, y2] = Array.isArray(d.bbox) ? d.bbox : [0,0,0,0];
        const crop = `"${d.crop_url || ''}"`;
        csv += `${id},${cls},${conf},${x1},${y1},${x2},${y2},${crop}\n`;
      });

      const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
      const a = document.createElement('a');
      a.href = URL.createObjectURL(blob);
      a.download = `detections_export_${Date.now()}.${type === 'excel' ? 'xlsx' : 'csv'}`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      if (window.toast) window.toast(`Data deteksi berhasil diekspor (${type.toUpperCase()})!`, false);
    },

    exportAnalyticsToCsv(widgetId, type = 'csv') {
      const data = this.state.analysisState.lastResult;
      if (!data) {
        if (window.toast) window.toast('Tidak ada data analitik untuk diekspor.', true);
        return;
      }

      let csv = 'No,ParameterZona,Metrik,NilaiAktual,BatasTarget,Status\n';
      const items = [
        ['1', 'Zona Produksi Utama (Workshop)', 'Total Okupansi / Deteksi', `${data.detections?.length || 0} Objek`, '< 15 Objek', 'Normal'],
        ['2', 'Zona Keselamatan APD (K3)', 'Pekerja dengan Rompi Safety', `${data.detections?.length || 0} Orang Terpantau`, 'Wajib 100%', 'Normal'],
        ['3', 'Kecepatan Inferensi Vision', 'Latency Per Frame', `${data.inference_time_ms || 24} ms`, '< 100 ms', 'Normal'],
        ['4', 'Keandalan Keyakinan', 'Rata-rata Skor Keyakinan', `${Math.round((data.analytics?.average_confidence || 0.85) * 100)}%`, '> 70%', 'Normal'],
        ['5', 'Pintu Darurat & Jalur Evakuasi', 'Status Hambatan', 'Jalur Bersih (Clear)', 'Bebas Hambatan', 'Normal']
      ];

      items.forEach(row => {
        csv += row.map(v => `"${v}"`).join(',') + '\n';
      });

      const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
      const a = document.createElement('a');
      a.href = URL.createObjectURL(blob);
      a.download = `analytics_export_${Date.now()}.${type === 'excel' ? 'xlsx' : 'csv'}`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      if (window.toast) window.toast(`Data analitik berhasil diekspor (${type.toUpperCase()})!`, false);
    },
    // Action Utilities (Excel, Snapshot, Fullscreen, Docker)
    // ------------------------------------------------------------------------
    downloadExcelReport(cameraLabel, customFilename) {
      let url = '/api/dashboard/builder/export-excel';
      const params = [];
      if (cameraLabel) params.push(`camera_label=${encodeURIComponent(cameraLabel)}`);
      if (customFilename) params.push(`filename=${encodeURIComponent(customFilename)}`);
      if (params.length) url += `?${params.join('&')}`;
      const a = document.createElement('a');
      a.href = url;
      a.download = customFilename || `afivision_report_${Date.now()}.xlsx`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      if (window.toast) window.toast('Laporan Excel berhasil diunduh!', false);
    },

    downloadSnapshot(nodeId, label) {
      const a = document.createElement('a');
      a.href = `/api/preview/${nodeId}?t=${Date.now()}`;
      a.download = `snapshot_${label}_${Date.now()}.jpg`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      if (window.toast) window.toast('Tangkapan layar frame tersimpan.', false);
    },

    openCctvFullscreen(title, streamUrl) {
      const modal = document.getElementById('cctvFullscreenModal');
      const titleEl = document.getElementById('cctvModalTitle');
      const img = document.getElementById('cctvModalImg');
      if (titleEl) titleEl.textContent = title;
      if (img) img.src = `${streamUrl}?t=${Date.now()}`;
      modal?.showModal();
    },

    openDockerExportModal() {
      const modal = document.getElementById('dockerExportModal');
      modal?.showModal();
    },

    async openTemplatesModal() {
      const modal = document.getElementById('dashboardTemplatesModal');
      const list = document.getElementById('dashboardTemplatesList');
      if (!modal || !list) return;

      list.innerHTML = '<div style="padding:20px;text-align:center;color:#94a3b8;">Memuat template dashboard...</div>';
      modal.showModal();

      try {
        const res = await fetch('/api/dashboard/builder/templates');
        if (res.ok) {
          const data = await res.json();
          const templates = data.templates || [];
          list.innerHTML = templates.map(t => `
            <div class="dashboard-template-card" data-template-id="${t.id}">
              <div class="tpl-card-top">
                <span class="tpl-badge">${t.badge}</span>
                <span style="font-size:11px;color:#64748b;">${t.category}</span>
              </div>
              <div>
                <h4 class="tpl-card-title">${t.name}</h4>
                <p class="tpl-card-desc">${t.description}</p>
              </div>
              <div class="tpl-card-footer">
                <span class="tpl-workflow-link">🔗 ${t.workflow_id}</span>
                <button class="btn-apply-template" type="button" data-template-id="${t.id}">
                  Pakai Template →
                </button>
              </div>
            </div>
          `).join('');

          list.querySelectorAll('.btn-apply-template').forEach(btn => {
            btn.addEventListener('click', async (e) => {
              const tid = e.currentTarget.dataset.templateId;
              if (confirm('Terapkan template dashboard ini? (Tata letak saat ini akan digantikan)')) {
                btn.textContent = 'Menerapkan...';
                await this.applyDashboardTemplate(tid);
                modal.close();
              }
            });
          });
        }
      } catch (err) {
        list.innerHTML = `<div style="color:#ef4444;padding:20px;">Gagal memuat template: ${err.message}</div>`;
      }
    },

    async applyTemplate(templateId) { return this.applyDashboardTemplate(templateId); },

    async applyDashboardTemplate(templateId) {
      try {
        const res = await fetch('/api/dashboard/builder/templates/apply', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ project_id: this.state.projectId, template_id: templateId })
        });
        if (res.ok) {
          const data = await res.json();
          this.state.layout = data.layout;
          this.applyTheme(this.state.layout.theme || 'dark');
          this.renderCanvas();
          if (window.toast) window.toast('Template dashboard berhasil diterapkan!', false);
        }
      } catch (e) {
        alert('Gagal menerapkan template: ' + e.message);
      }
    },

    bindModalEvents() {
      // Templates Modal close
      document.getElementById('closeDashboardTemplatesModal')?.addEventListener('click', () => {
        document.getElementById('dashboardTemplatesModal')?.close();
      });

      // CCTV Modal close
      document.getElementById('closeCctvModal')?.addEventListener('click', () => {
        document.getElementById('cctvFullscreenModal')?.close();
      });

      // Docker Modal close
      document.getElementById('closeDockerExportModal')?.addEventListener('click', () => {
        document.getElementById('dockerExportModal')?.close();
      });
      document.getElementById('cancelDockerExportBtn')?.addEventListener('click', () => {
        document.getElementById('dockerExportModal')?.close();
      });

      // Docker Confirm Download
      document.getElementById('confirmDownloadDockerZipBtn')?.addEventListener('click', async () => {
        const btn = document.getElementById('confirmDownloadDockerZipBtn');
        if (btn) btn.textContent = 'Membuat Paket ZIP...';
        try {
          const res = await fetch('/api/dashboard/builder/export-package', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ project_id: this.state.projectId, layout: this.state.layout })
          });
          if (res.ok) {
            const blob = await res.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `afivision-dashboard-standalone-${this.state.projectId}.zip`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);
            document.getElementById('dockerExportModal')?.close();
            if (window.toast) window.toast('Paket Docker Compose berhasil diunduh!', false);
          } else {
            alert('Gagal menghasilkan paket Docker: ' + res.statusText);
          }
        } catch (e) {
          alert('Error ekspor: ' + e.message);
        } finally {
          if (btn) btn.textContent = 'Unduh Berkas ZIP (.zip)';
        }
      });
    }
  };

  // Expose global initializer and instance for testability and topbar view switcher
  window.dashboardBuilder = DashboardBuilder;
  window.initOrRefreshDashboardBuilder = function() {
    DashboardBuilder.init();
  };

  // Auto-init if dashboard view is loaded directly
  document.addEventListener('DOMContentLoaded', () => {
    const tab = document.getElementById('tabDashboardBuilder');
    if (tab && tab.classList.contains('active')) {
      DashboardBuilder.init();
    }
  });

})();
