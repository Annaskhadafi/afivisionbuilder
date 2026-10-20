(() => {
  const $ = (s) => document.querySelector(s);
  const $$ = (s) => document.querySelectorAll(s);
  const PANEL_LAYOUT_KEY = 'afiVisionBuilder.panelLayout';

  function readPanelLayout() {
    try {
      return JSON.parse(localStorage.getItem(PANEL_LAYOUT_KEY) || '{}');
    } catch {
      return {};
    }
  }

  // --- Vector SVG Icon Library (Lucide style) ---
  const ICONS = {
    // Sources
    input: '<svg class="icon-svg" viewBox="0 0 24 24"><path d="M14.5 4h-5L7 7H4a2 2 0 0 0-2 2v9a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2h-3l-2.5-3z"/><circle cx="12" cy="13" r="3"/></svg>',
    camera: '<svg class="icon-svg" viewBox="0 0 24 24"><path d="M14.5 4h-5L7 7H4a2 2 0 0 0-2 2v9a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2h-3l-2.5-3z"/><circle cx="12" cy="13" r="3"/></svg>',
    ip_camera: '<svg class="icon-svg" viewBox="0 0 24 24"><circle cx="12" cy="12" r="9"/><path d="m15 10-3 3-3-3"/><path d="M12 13V7"/><circle cx="12" cy="12" r="3"/><path d="M4.93 4.93 3 3"/><path d="M19.07 4.93 21 3"/></svg>',

    // AI Vision Models
    detector: '<svg class="icon-svg" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><line x1="22" y1="12" x2="18" y2="12"/><line x1="6" y1="12" x2="2" y2="12"/><line x1="12" y1="6" x2="12" y2="2"/><line x1="12" y1="22" x2="12" y2="18"/></svg>',
    segmenter: '<svg class="icon-svg" viewBox="0 0 24 24"><path d="m12 3 8 4.5v9L12 21l-8-4.5v-9L12 3z"/><path d="M12 12v9"/><path d="m12 12 8-4.5"/><path d="M12 12 4 7.5"/></svg>',
    classifier: '<svg class="icon-svg" viewBox="0 0 24 24"><path d="M20.59 13.41l-7.17 7.17a2 2 0 0 1-2.83 0L2 12V2h10l8.59 8.59a2 2 0 0 1 0 2.82z"/><line x1="7" y1="7" x2="7.01" y2="7"/></svg>',
    efficientad: '<svg class="icon-svg" viewBox="0 0 24 24"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>',
    detection_crop: '<svg class="icon-svg" viewBox="0 0 24 24"><rect width="14" height="14" x="5" y="5" rx="2"/><circle cx="12" cy="12" r="3"/></svg>',
    barcode_reader: '<svg class="icon-svg" viewBox="0 0 24 24"><rect width="5" height="5" x="3" y="3" rx="1"/><rect width="5" height="5" x="16" y="3" rx="1"/><rect width="5" height="5" x="3" y="16" rx="1"/><path d="M21 16h-3a2 2 0 0 0-2 2v3"/><path d="M21 21v.01"/><path d="M12 7v3a2 2 0 0 1-2 2H7"/><path d="M3 12h.01"/><path d="M12 3h.01"/><path d="M12 16v.01"/><path d="M16 12h1"/><path d="M21 12v.01"/><path d="M12 21v-1"/></svg>',

    // Tracking & Analysis
    tracker: '<svg class="icon-svg" viewBox="0 0 24 24"><path d="M2 12h5l2-5 6 10 3-5h4"/></svg>',
    track_snapshot: '<svg class="icon-svg" viewBox="0 0 24 24"><rect width="18" height="18" x="3" y="3" rx="2"/><circle cx="9" cy="9" r="2"/><path d="m21 15-3.086-3.086a2 2 0 0 0-2.828 0L6 21"/></svg>',
    object_counter: '<svg class="icon-svg" viewBox="0 0 24 24"><line x1="4" y1="9" x2="20" y2="9"/><line x1="4" y1="15" x2="20" y2="15"/><line x1="10" y1="3" x2="8" y2="21"/><line x1="16" y1="3" x2="14" y2="21"/></svg>',
    line_counter: '<svg class="icon-svg" viewBox="0 0 24 24"><line x1="2" y1="12" x2="22" y2="12"/><polyline points="8 8 12 4 16 8"/><polyline points="8 16 12 20 16 16"/></svg>',
    dwell_time: '<svg class="icon-svg" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/><path d="M12 2a10 10 0 0 0-7.07 2.93"/></svg>',
    filter: '<svg class="icon-svg" viewBox="0 0 24 24"><polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3"/></svg>',
    detections_consensus: '<svg class="icon-svg" viewBox="0 0 24 24"><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>',
    distance_measurement: '<svg class="icon-svg" viewBox="0 0 24 24"><path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>',
    size_measurement: '<svg class="icon-svg" viewBox="0 0 24 24"><path d="M21 3H3v18h18V3z"/><path d="M7 3v4"/><path d="M17 3v4"/><path d="M3 7h18"/><path d="M3 17h18"/></svg>',
    camera_focus: '<svg class="icon-svg" viewBox="0 0 24 24"><circle cx="12" cy="12" r="3"/><circle cx="12" cy="12" r="8"/><line x1="12" y1="2" x2="12" y2="6"/><line x1="12" y1="18" x2="12" y2="22"/><line x1="2" y1="12" x2="6" y2="12"/><line x1="18" y1="12" x2="22" y2="12"/></svg>',
    auto_rotate_edges: '<svg class="icon-svg" viewBox="0 0 24 24"><path d="M21 12a9 9 0 1 1-9-9c2.52 0 4.8 1.04 6.43 2.72L21 8"/><path d="M21 3v5h-5"/></svg>',
    overlap_analysis: '<svg class="icon-svg" viewBox="0 0 24 24"><rect width="12" height="12" x="2" y="2" rx="2"/><rect width="12" height="12" x="10" y="10" rx="2"/></svg>',
    velocity_calculator: '<svg class="icon-svg" viewBox="0 0 24 24"><path d="m12 14 4-4"/><path d="M3.34 19a10 10 0 1 1 17.32 0"/></svg>',
    path_deviation: '<svg class="icon-svg" viewBox="0 0 24 24"><path d="M4 19h16"/><path d="M4 5h16"/><line x1="6" y1="12" x2="18" y2="12" stroke-dasharray="2 2"/><circle cx="12" cy="8" r="2"/></svg>',
    delta_filter: '<svg class="icon-svg" viewBox="0 0 24 24"><polygon points="11 19 2 12 11 5 11 19"/><polygon points="22 19 13 12 22 5 22 19"/></svg>',
    switch_case: '<svg class="icon-svg" viewBox="0 0 24 24"><path d="M6 3v12"/><circle cx="18" cy="6" r="3"/><circle cx="6" cy="18" r="3"/><path d="M18 9a9 9 0 0 1-9 9"/></svg>',
    model_comparison: '<svg class="icon-svg" viewBox="0 0 24 24"><rect width="18" height="18" x="3" y="3" rx="2"/><path d="M12 3v18"/><path d="m8 9-2 3 2 3"/><path d="m16 9 2 3-2 3"/></svg>',
    detections_difference: '<svg class="icon-svg" viewBox="0 0 24 24"><circle cx="9" cy="12" r="6"/><circle cx="15" cy="12" r="6"/><path d="M12 7.5v9"/></svg>',
    data_aggregator: '<svg class="icon-svg" viewBox="0 0 24 24"><path d="M3 3v18h18"/><path d="m19 9-5 5-4-4-3 3"/></svg>',
    csv_formatter: '<svg class="icon-svg" viewBox="0 0 24 24"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="8" y1="13" x2="16" y2="13"/><line x1="8" y1="17" x2="16" y2="17"/></svg>',
    s3_sink: '<svg class="icon-svg" viewBox="0 0 24 24"><path d="M17.5 19H9a7 7 0 1 1 6.71-9h1.79a4.5 4.5 0 1 1 0 9Z"/><path d="m12 12 3 3m-3-3-3 3m3-3v7"/></svg>',
    notification_dispatcher: '<svg class="icon-svg" viewBox="0 0 24 24"><path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9"/><path d="M10.3 21a1.94 1.94 0 0 0 3.4 0"/></svg>',
    screenshot_capture: '<svg class="icon-svg" viewBox="0 0 24 24"><path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"/><circle cx="12" cy="13" r="4"/></svg>',
    telegram_notification: '<svg class="icon-svg" viewBox="0 0 24 24"><path d="m22 2-7 20-4-9-9-4Z"/><path d="M22 2 11 13"/></svg>',
    ptz_controller: '<svg class="icon-svg" viewBox="0 0 24 24"><circle cx="12" cy="12" r="3"/><path d="M12 2v4"/><path d="M12 18v4"/><path d="M2 12h4"/><path d="M18 12h4"/></svg>',
    ocr_reader: '<svg class="icon-svg" viewBox="0 0 24 24"><path d="M4 7V4h16v3"/><path d="M9 20h6"/><path d="M12 4v16"/><rect width="20" height="16" x="2" y="4" rx="2" stroke-dasharray="2 2"/></svg>',
    object_timer: '<svg class="icon-svg" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>',
    face_detector: '<svg class="icon-svg" viewBox="0 0 24 24"><path d="M9 10h.01"/><path d="M15 10h.01"/><path d="M10 16c.5.5 1.5 1 2 1s1.5-.5 2-1"/><path d="M3 7V5a2 2 0 0 1 2-2h2"/><path d="M17 3h2a2 2 0 0 1 2 2v2"/><path d="M21 17v2a2 2 0 0 1-2 2h-2"/><path d="M7 21H5a2 2 0 0 1-2-2v-2"/></svg>',
    face_tracker: '<svg class="icon-svg" viewBox="0 0 24 24"><path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/><path d="M12 14v7"/><polyline points="9 18 12 21 15 18"/></svg>',

    // Preprocessing
    slicer: '<svg class="icon-svg" viewBox="0 0 24 24"><rect width="7" height="7" x="3" y="3" rx="1"/><rect width="7" height="7" x="14" y="3" rx="1"/><rect width="7" height="7" x="14" y="14" rx="1"/><rect width="7" height="7" x="3" y="14" rx="1"/></svg>',
    resize: '<svg class="icon-svg" viewBox="0 0 24 24"><polyline points="15 3 21 3 21 9"/><polyline points="9 21 3 21 3 15"/><line x1="21" y1="3" x2="14" y2="10"/><line x1="3" y1="21" x2="10" y2="14"/></svg>',
    frame_sampler: '<svg class="icon-svg" viewBox="0 0 24 24"><circle cx="12" cy="12" r="9"/><polyline points="12 7 12 12 15 14"/><path d="M5 4 3 6"/><path d="m19 4 2 2"/></svg>',
    crop: '<svg class="icon-svg" viewBox="0 0 24 24"><path d="M6 2v14a2 2 0 0 0 2 2h14"/><path d="M18 22V8a2 2 0 0 0-2-2H2"/></svg>',
    rotate_flip: '<svg class="icon-svg" viewBox="0 0 24 24"><path d="M21 12a9 9 0 0 0-9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/><path d="M3 3v5h5"/><path d="M3 12a9 9 0 0 0 9 9 9.75 9.75 0 0 0 6.74-2.74L21 16"/><path d="M16 21h5v-5"/></svg>',
    color_convert: '<svg class="icon-svg" viewBox="0 0 24 24"><circle cx="13.5" cy="6.5" r=".5" fill="currentColor"/><circle cx="17.5" cy="10.5" r=".5" fill="currentColor"/><circle cx="8.5" cy="7.5" r=".5" fill="currentColor"/><circle cx="6.5" cy="12.5" r=".5" fill="currentColor"/><path d="M12 2C6.5 2 2 6.5 2 12s4.5 10 10 10c.926 0 1.648-.746 1.648-1.688 0-.437-.18-.835-.437-1.125-.29-.289-.438-.652-.438-1.125a1.64 1.64 0 0 1 1.668-1.668h1.996c3.051 0 5.555-2.503 5.555-5.554C21.965 6.012 17.461 2 12 2z"/></svg>',
    brightness_contrast: '<svg class="icon-svg" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><path d="M12 2a10 10 0 0 1 0 20z"/></svg>',
    blur_sharpen: '<svg class="icon-svg" viewBox="0 0 24 24"><path d="M12 22a7 7 0 0 0 7-7c0-2-1-3.9-3-5.5s-3.5-4-4-6.5c-.5 2.5-2 4.9-4 6.5C6 11.1 5 13 5 15a7 7 0 0 0 7 7z"/></svg>',
    perspective: '<svg class="icon-svg" viewBox="0 0 24 24"><path d="m2 4 6 3v10l-6 3V4z"/><path d="m22 4-6 3v10l6 3V4z"/><path d="M8 7h8"/><path d="M8 17h8"/></svg>',
    undistort: '<svg class="icon-svg" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><path d="M12 2a14.5 14.5 0 0 0 0 20 14.5 14.5 0 0 0 0-20"/><path d="M2 12h20"/></svg>',
    background_subtract: '<svg class="icon-svg" viewBox="0 0 24 24"><rect width="18" height="18" x="3" y="3" rx="2"/><path d="m9 18 6-6-6-6"/></svg>',
    python_script: '<svg class="icon-svg" viewBox="0 0 24 24"><path d="m8 9-4 3 4 3M16 9l4 3-4 3M14 5l-4 14"/></svg>',
    blur_anonymizer: '<svg class="icon-svg" viewBox="0 0 24 24"><path d="M9.88 9.88a3 3 0 1 0 4.24 4.24"/><path d="M10.73 5.08A10.43 10.43 0 0 1 12 5c7 0 10 7 10 7a13.16 13.16 0 0 1-1.67 2.68"/><path d="M6.61 6.61A13.526 13.526 0 0 0 2 12s3 7 10 7a9.74 9.74 0 0 0 5.39-1.61"/><line x1="2" y1="2" x2="22" y2="22"/></svg>',

    // Drawing & Annotation
    overlay_annotate: '<svg class="icon-svg" viewBox="0 0 24 24"><polygon points="12 2 2 7 12 12 22 7 12 2"/><polyline points="2 17 12 22 22 17"/><polyline points="2 12 12 17 22 12"/></svg>',
    draw_boxes: '<svg class="icon-svg" viewBox="0 0 24 24"><rect width="18" height="18" x="3" y="3" rx="2"/></svg>',
    draw_text: '<svg class="icon-svg" viewBox="0 0 24 24"><polyline points="4 7 4 4 20 4 20 7"/><line x1="9" y1="20" x2="15" y2="20"/><line x1="12" y1="4" x2="12" y2="20"/></svg>',

    // Logic & Flow
    if_else: '<svg class="icon-svg" viewBox="0 0 24 24"><line x1="6" y1="3" x2="6" y2="15"/><circle cx="18" cy="6" r="3"/><circle cx="6" cy="18" r="3"/><path d="M18 9a9 9 0 0 1-9 9"/></svg>',
    compare_value: '<svg class="icon-svg" viewBox="0 0 24 24"><line x1="5" y1="9" x2="19" y2="9"/><line x1="5" y1="15" x2="19" y2="15"/></svg>',
    roi_filter: '<svg class="icon-svg" viewBox="0 0 24 24"><rect width="14" height="14" x="5" y="5" rx="2"/><path d="M9 5v14"/><path d="M15 5v14"/></svg>',
    object_count_condition: '<svg class="icon-svg" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><path d="m9 12 2 2 4-4"/></svg>',
    class_detected_condition: '<svg class="icon-svg" viewBox="0 0 24 24"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>',
    confidence_threshold: '<svg class="icon-svg" viewBox="0 0 24 24"><path d="M12 20v-6"/><path d="M6 20V10"/><path d="M18 20V4"/></svg>',
    timer_delay: '<svg class="icon-svg" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>',
    debounce: '<svg class="icon-svg" viewBox="0 0 24 24"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>',
    rate_limiter: '<svg class="icon-svg" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 8 14"/></svg>',
    and_or_logic: '<svg class="icon-svg" viewBox="0 0 24 24"><circle cx="18" cy="18" r="3"/><circle cx="6" cy="6" r="3"/><path d="M6 21V9a9 9 0 0 0 9 9"/></svg>',
    trigger_once: '<svg class="icon-svg" viewBox="0 0 24 24"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>',

    // Outputs
    preview: '<svg class="icon-svg" viewBox="0 0 24 24"><rect width="20" height="14" x="2" y="3" rx="2"/><line x1="8" y1="21" x2="16" y2="21"/><line x1="12" y1="17" x2="12" y2="21"/></svg>',
    alert: '<svg class="icon-svg" viewBox="0 0 24 24"><path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9"/><path d="M10.3 21a1.94 1.94 0 0 0 3.4 0"/></svg>',
    image_output: '<svg class="icon-svg" viewBox="0 0 24 24"><rect width="18" height="18" x="3" y="3" rx="2"/><circle cx="9" cy="9" r="2"/><path d="m21 15-3.086-3.086a2 2 0 0 0-2.828 0L6 21"/></svg>',
    webhook_output: '<svg class="icon-svg" viewBox="0 0 24 24"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/><polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/></svg>',
    database_output: '<svg class="icon-svg" viewBox="0 0 24 24"><ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/><path d="M3 12c0 1.66 4 3 9 3s9-1.34 9-3"/></svg>',

    // Generic Categories
    catSources: '<svg class="icon-svg" viewBox="0 0 24 24"><path d="M14.5 4h-5L7 7H4a2 2 0 0 0-2 2v9a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2h-3l-2.5-3z"/><circle cx="12" cy="13" r="3"/></svg>',
    catAI: '<svg class="icon-svg" viewBox="0 0 24 24"><rect width="16" height="16" x="4" y="4" rx="2"/><circle cx="12" cy="12" r="3"/></svg>',
    catTracking: '<svg class="icon-svg" viewBox="0 0 24 24"><path d="M2 12h5l2-5 6 10 3-5h4"/></svg>',
    catProcessing: '<svg class="icon-svg" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><path d="M12 2a10 10 0 0 1 0 20z"/></svg>',
    catDrawing: '<svg class="icon-svg" viewBox="0 0 24 24"><polygon points="12 2 2 7 12 12 22 7 12 2"/><polyline points="2 17 12 22 22 17"/></svg>',
    catLogic: '<svg class="icon-svg" viewBox="0 0 24 24"><line x1="6" y1="3" x2="6" y2="15"/><circle cx="18" cy="6" r="3"/><circle cx="6" cy="18" r="3"/><path d="M18 9a9 9 0 0 1-9 9"/></svg>',
    catOutputs: '<svg class="icon-svg" viewBox="0 0 24 24"><rect width="20" height="14" x="2" y="3" rx="2"/><line x1="8" y1="21" x2="16" y2="21"/></svg>',
  };

  function getIcon(name, extraClass = '') {
    const raw = ICONS[name] || ICONS['input'];
    if (!extraClass) return raw;
    return raw.replace('class="icon-svg"', `class="icon-svg ${extraClass}"`);
  }

  const state = {
    panelLayout: {
      sidebarWidth: 236,
      inspectorWidth: 300,
      bottomHeight: 320,
      sidebarHidden: false,
      inspectorHidden: false,
      bottomHidden: false,
      ...readPanelLayout(),
    },
    zoom: 1,
    panX: 0,
    panY: 0,
    isPanning: false,
    spacePan: false,
    panStart: { x: 0, y: 0 },
    catalog: {},
    projects: [],
    project: null,
    workflow: { nodes: [], edges: [] },
    selected: null,
    dirty: false,
    connecting: null,
    status: null,
    poll: null,
    previewNode: '',
    defaults: null,
    pollBusy: false,
    lastError: null,
    clearedSeq: 0,
    logFilter: 'all',
    models: [],
    modelEngines: [],
    cameras: [],
    uploads: [],
    templates: [],
    inspectorTab: 'basic', // 'basic' | 'advanced'
    autoConnect: true,
    reconnectingEdge: null, // { index, fixedNode, mode: 'target' | 'source' }
  };

  function applyPanelLayout() {
    const layout = state.panelLayout;
    const shell = $('.app-shell');
    if (!shell) return;
    shell.dataset.sidebarHidden = String(layout.sidebarHidden);
    shell.dataset.inspectorHidden = String(layout.inspectorHidden);
    shell.dataset.bottomHidden = String(layout.bottomHidden);
    shell.style.setProperty('--sidebar-width', `${layout.sidebarWidth}px`);
    shell.style.setProperty('--inspector-width', `${layout.inspectorWidth}px`);
    shell.style.setProperty('--bottom-height', `${layout.bottomHeight}px`);

    for (const [id, key, label] of [
      ['toggleSidebar', 'sidebarHidden', 'panel kiri'],
      ['toggleBottom', 'bottomHidden', 'panel bawah'],
      ['toggleInspector', 'inspectorHidden', 'panel kanan'],
    ]) {
      const button = $(`#${id}`);
      if (!button) continue;
      const hidden = layout[key];
      const action = hidden ? 'Tampilkan' : 'Sembunyikan';
      button.setAttribute('aria-label', `${action} ${label}`);
      button.title = `${action} ${label}`;
      button.setAttribute('aria-pressed', String(hidden));
    }
  }

  const api = async (url, options) => {
    const res = await fetch(url, options);
    let data = null;
    try {
      data = await res.json();
    } catch {}
    if (!res.ok) {
      throw new Error(data?.detail || data?.error || `Request failed (${res.status})`);
    }
    return data;
  };

  const toast = (message, error = false) => {
    const el = $('#toast');
    if (!el) return;
    el.textContent = message;
    el.className = `toast show${error ? ' error' : ''}`;
    clearTimeout(toast.timer);
    toast.timer = setTimeout(() => el.className = 'toast', 3200);
  };
  window.toast = toast;

  const titleFor = (type) => state.catalog[type]?.title || type.replaceAll('_', ' ').replace(/\b\w/g, c => c.toUpperCase());
  const nodeFor = (id) => state.workflow.nodes.find(n => n.id === id);
  const markDirty = () => {
    state.dirty = true;
    const dirtyEl = $('#dirty');
    if (dirtyEl) dirtyEl.hidden = false;
  };
  const clone = (value) => JSON.parse(JSON.stringify(value));

  // --- Category Mapping ---
  function categoryFor(type) {
    if (type === 'input' || type === 'ip_camera') return 'Sources';
    if (['detector', 'segmenter', 'classifier', 'efficientad', 'detection_crop', 'barcode_reader', 'ocr_reader', 'ai_agent', 'model_comparison', 'face_detector'].includes(type)) return 'AI Vision Models';
    if (['tracker', 'detections_consensus', 'detections_difference', 'distance_measurement', 'size_measurement', 'overlap_analysis', 'velocity_calculator', 'path_deviation', 'track_snapshot', 'object_counter', 'line_counter', 'dwell_time', 'zone_activity_timer', 'zone_exit_event', 'multi_zone_occupancy', 'vlm_box_tracker', 'filter', 'ptz_controller', 'object_timer', 'face_tracker'].includes(type)) return 'Tracking & Analysis';
    if (['resize', 'frame_sampler', 'crop', 'rotate_flip', 'color_convert', 'brightness_contrast', 'blur_sharpen', 'perspective', 'undistort', 'background_subtract', 'python_script', 'slicer', 'camera_focus', 'auto_rotate_edges', 'delta_filter'].includes(type)) return 'Image Preprocessing';
    if (['overlay_annotate', 'draw_boxes', 'draw_text', 'blur_anonymizer'].includes(type)) return 'Annotations & Drawing';
    if (['if_else', 'compare_value', 'roi_filter', 'object_count_condition', 'class_detected_condition', 'confidence_threshold', 'timer_delay', 'debounce', 'rate_limiter', 'and_or_logic', 'trigger_once', 'switch_case'].includes(type)) return 'Logic & Flow Control';
    return 'Outputs & Export';
  }

  const CATEGORY_ICONS = {
    'Sources': 'catSources',
    'AI Vision Models': 'catAI',
    'Tracking & Analysis': 'catTracking',
    'Image Preprocessing': 'catProcessing',
    'Annotations & Drawing': 'catDrawing',
    'Logic & Flow Control': 'catLogic',
    'Outputs & Export': 'catOutputs'
  };

  const CATEGORY_ORDER = [
    'Sources',
    'AI Vision Models',
    'Tracking & Analysis',
    'Image Preprocessing',
    'Annotations & Drawing',
    'Logic & Flow Control',
    'Outputs & Export'
  ];

  // Technical / Performance keys partitioned into "Advanced" tab
  const ADVANCED_KEYS = new Set([
    'device',
    'batchSize',
    'detectEveryNFrames',
    'maxDetectionFps',
    'rfdetrHalfPrecision',
    'rfdetrTensorRTCudaGraph',
    'rfdetrTensorRTProcess',
    'dropFrames',
    'frameQueueSize',
    'torchCpuThreads',
    'asyncPreview',
    'dahengTimeoutMs',
    'dahengOpenMode',
    'topK',
    'useModelThreshold'
  ]);

  const FIELD_HELP = {
    // Logika Tingkat Lanjut & Kinematika Video (Fase 3)
    parentClass: {
      text: 'Label nama kelas objek induk yang akan diperiksa kelengkapannya.',
      guide: 'Contoh: person, operator, driver. Objek ini menjadi acuan utama pemeriksaan APD.'
    },
    childClass: {
      text: 'Label nama kelas objek anak yang wajib berada di dalam area objek induk.',
      guide: 'Contoh: helmet, safety_vest, seatbelt. Sistem akan memverifikasi keberadaannya di sub-region induk.'
    },
    minOverlapRatio: {
      text: 'Rasio minimal luas tumpang tindih (overlap) objek anak terhadap area sub-region induk.',
      guide: 'Rentang 0.0 s/d 1.0 (default: 0.5 = 50% area helmet harus berada di dalam kepala person).'
    },
    parentRegion: {
      text: 'Bagian sub-area tubuh/objek induk yang diperiksa.',
      guide: 'top_half (separuh atas, untuk helm/kacamata), bottom_half (separuh bawah, untuk sepatu safety), full (seluruh tubuh, untuk rompi).'
    },
    triggerAlarmOnNonCompliance: {
      text: 'Otomatis kirimkan event pelanggaran jika objek induk tidak memiliki objek anak pelengkap.',
      guide: 'Event compliance_violation akan langsung diteruskan ke Alert, Webhook, atau Database.'
    },
    deltaThreshold: {
      text: 'Ambang batas persentase perubahan visual piksel untuk memicu pemrosesan inferensi AI.',
      guide: 'Default: 0.03 (3% piksel berubah). Jika perubahan visual di bawah nilai ini, inferensi model AI dilewati untuk menghemat CPU/GPU.'
    },
    heartbeatIntervalSeconds: {
      text: 'Batas waktu interval detak jantung untuk memaksa inferensi frame tetap berjalan berkala.',
      guide: 'Default: 15 detik. Menjamin status sistem tetap terbarui meskipun suasana di depan kamera diam.'
    },
    minContourArea: {
      text: 'Luas area kontur gerakan minimal dalam piksel untuk dihitung sebagai pergerakan nyata.',
      guide: 'Mencegah noise sensor kamera atau kedipan cahaya kecil memicu inferensi model.'
    },
    evaluationField: {
      text: 'Nama bidang metadata yang dievaluasi untuk menentukan cabang port keluaran.',
      guide: 'Pilihan: class (nama kelas deteksi), status, event_type, atau custom attribute.'
    },
    cases: {
      text: 'Daftar pemetaan nilai evaluasi ke nomor/nama port keluaran.',
      guide: 'Format: nilai1:port_1, nilai2:port_2. Contoh: person:port_1, forklift:port_2'
    },
    defaultPort: {
      text: 'Nama port keluaran fallback jika nilai evaluasi tidak cocok dengan daftar kasus mana pun.',
      guide: 'Default: default.'
    },
    speedLimitKmh: {
      text: 'Batas kecepatan maksimal kendaraan atau objek di workshop/gudang (km/jam).',
      guide: 'Default: 15.0 km/jam. Jika kecepatan melebihi ambang batas ini, alarm overspeed akan dipicu.'
    },
    speedUnit: {
      text: 'Satuan tampilan kecepatan objek di layar inspeksi.',
      guide: 'Pilihan: kmh (kilometer per jam) atau mps (meter per detik).'
    },
    smoothingWindow: {
      text: 'Jumlah frame riwayat pergerakan yang digunakan untuk meredam fluktuasi kecepatan (EMA).',
      guide: 'Rentang 2 s/d 10 frame. Default: 5 frame.'
    },
    triggerAlarmOnSpeeding: {
      text: 'Otomatis kirimkan event bahaya saat objek bergerak melebihi batas kecepatan.',
      guide: 'Event overspeed_detected akan diteruskan ke node Alert, Webhook, atau Database.'
    },
    guidePathPoints: {
      text: 'Titik-titik koordinat polyline rute lintasan baku kendaraan (virtual corridor).',
      guide: 'Format x,y; x,y; ... Contoh: 0.1,0.5; 0.5,0.5; 0.9,0.5'
    },
    maxAllowedDeviationMeters: {
      text: 'Batas jarak penyimpangan tegak lurus maksimal dari koridor lintasan (meter).',
      guide: 'Default: 1.5 meter. Jika objek keluar melebihi batas ini, alarm deviasi akan dipicu.'
    },
    targetClasses: {
      text: 'Daftar nama kelas kendaraan atau orang yang dipantau rute lintasannya.',
      guide: 'Pisahkan dengan koma. Contoh: forklift, agv, vehicle'
    },
    triggerAlarmOnDeviation: {
      text: 'Otomatis kirimkan event saat objek menyimpang keluar dari koridor jalur aman.',
      guide: 'Event path_deviation_detected akan diteruskan ke node Alert, Webhook, atau Database.'
    },
    // Pengukuran Spasial & Klasikal CV (Fase 2)
    objectAClass: {
      text: 'Label nama kelas objek pertama yang akan diukur jaraknya.',
      guide: 'Contoh: person, pedestrian. Harus sesuai dengan nama kelas yang dihasilkan oleh model detektor.'
    },
    objectBClass: {
      text: 'Label nama kelas objek kedua yang akan diukur jaraknya terhadap objek pertama.',
      guide: 'Contoh: forklift, truck, machine. Jika sama dengan Kelas A, sistem akan mengukur jarak antar objek sejenis (misal social distancing).'
    },
    measurementAxis: {
      text: 'Sumbu proyeksi pengukuran jarak fisik.',
      guide: 'Pilihan: euclidean (jarak diagonal 2D langsung), horizontal (selisih sumbu X saja), vertical (selisih sumbu Y saja).'
    },
    pixelRatio: {
      text: 'Faktor konversi kalibrasi kamera (jumlah piksel per 1 sentimeter fisik).',
      guide: 'Hitung dengan mengukur panjang objek referensi di layar dalam piksel dibagi panjang aktualnya dalam cm (default: 10.0 piksel = 1 cm).'
    },
    minDistanceThreshold: {
      text: 'Batas jarak aman minimum (dalam cm) sebelum alarm peringatan dipicu.',
      guide: 'Contoh: 150.0 (1.5 meter). Jika jarak objek A dan B lebih dekat dari nilai ini, alarm bahaya akan terpicu.'
    },
    anchorMode: {
      text: 'Titik acuan koordinat bounding box yang digunakan untuk menghitung jarak.',
      guide: 'bottom_center (tapak kaki/titik kontak lantai, paling akurat untuk kamera miring) atau centroid (pusat kotak).'
    },
    triggerAlarmOnProximity: {
      text: 'Otomatis kirimkan event bahaya saat jarak antar objek melanggar batas ambang.',
      guide: 'Event proximity_violation akan diteruskan ke node Alert, Webhook, atau Database.'
    },
    alarmCooldownSeconds: {
      text: 'Jeda waktu minimum antar alarm proximity berulang (detik).',
      guide: 'Mencegah spam notifikasi terus-menerus saat kedua objek masih berada di zona bahaya.'
    },
    targetClass: {
      text: 'Label kelas objek yang akan diukur dimensi fisik lebar dan tingginya.',
      guide: 'Isi "all" untuk mengukur seluruh deteksi, atau sebutkan kelas spesifik seperti "box", "tire", "bottle".'
    },
    pixelPerUnit: {
      text: 'Jumlah piksel kamera yang merepresentasikan 1 satuan dimensi fisik.',
      guide: 'Misal jika 100 piksel = 10 cm, maka nilai pixelPerUnit adalah 10.0 piksel per cm.'
    },
    unitName: {
      text: 'Satuan ukuran fisik yang ingin ditampilkan pada label inspeksi.',
      guide: 'Pilihan: mm, cm, m, inch.'
    },
    minAllowedWidth: {
      text: 'Batas toleransi lebar minimum objek dalam satuan yang dipilih.',
      guide: 'Nilai 0 menonaktifkan pemeriksaan batas bawah lebar.'
    },
    maxAllowedWidth: {
      text: 'Batas toleransi lebar maksimum objek dalam satuan yang dipilih.',
      guide: 'Nilai 0 menonaktifkan pemeriksaan batas atas lebar.'
    },
    minAllowedHeight: {
      text: 'Batas toleransi tinggi minimum objek dalam satuan yang dipilih.',
      guide: 'Nilai 0 menonaktifkan pemeriksaan batas bawah tinggi.'
    },
    maxAllowedHeight: {
      text: 'Batas toleransi tinggi maksimum objek dalam satuan yang dipilih.',
      guide: 'Nilai 0 menonaktifkan pemeriksaan batas atas tinggi.'
    },
    triggerAlarmOnToleranceViolation: {
      text: 'Picu event alarm jika dimensi fisik objek berada di luar rentang toleransi.',
      guide: 'Berguna untuk QA/QC penyortiran otomatis produk cacat atau ukuran tidak standar.'
    },
    blurThreshold: {
      text: 'Ambang batas nilai variansi Laplacian untuk mendeteksi kamera buram.',
      guide: 'Nilai di bawah ambang batas (default: 100.0) menandakan frame gambar tidak fokus, lensa kotor, atau tertutup kabut.'
    },
    checkIntervalSeconds: {
      text: 'Interval jeda waktu evaluasi kesehatan lensa kamera (detik).',
      guide: 'Pemeriksaan ketajaman dilakukan secara berkala tanpa membebani CPU di setiap frame.'
    },
    maxAngleLimit: {
      text: 'Batas sudut rotasi maksimal yang diizinkan untuk meluruskan gambar (derajat).',
      guide: 'Default: 45.0 derajat. Sudut kemiringan ekstrem di atas batas ini tidak akan dirotasi untuk mencegah distorsi.'
    },
    minAngleThreshold: {
      text: 'Ambang batas sudut kemiringan minimum sebelum rotasi dieksekusi (derajat).',
      guide: 'Default: 0.5 derajat. Mencegah rotasi mikro yang tidak perlu jika objek sudah cukup tegak.'
    },
    borderMode: {
      text: 'Perlakuan piksel pada area kosong hasil rotasi gambar.',
      guide: 'black_constant (isi area kosong dengan warna hitam pekat) atau replicate (duplikasi piksel tepi).'
    },
    // Model Comparison & Detections Difference (Fase 4)
    modelAName: {
      text: 'Nama identitas model AI pertama untuk komparasi (Model A).',
      guide: 'Contoh: Model A (YOLOv11). Deteksi model ini diberi warna Cyan.'
    },
    modelBName: {
      text: 'Nama identitas model AI kedua untuk komparasi (Model B).',
      guide: 'Contoh: Model B (RF-DETR). Deteksi model ini diberi warna Magenta.'
    },
    renderMode: {
      text: 'Mode visualisasi perbandingan dua model.',
      guide: 'Pilihan: side_by_side (tampilan 2 layar kiri-kanan) atau diff_overlay (satu layar dengan warna diff hijau/cyan/magenta).'
    },
    showStatsHeader: {
      text: 'Tampilkan kartu statistik perbandingan dan rasio kesepakatan (Agreement Ratio) di bagian atas frame.',
      guide: 'Menampilkan jumlah deteksi model A, model B, konsensus, dan persentase kesepakatan.'
    },
    matchIoU: {
      text: 'Ambang batas IoU untuk mencocokkan deteksi saat ini dengan baseline.',
      guide: 'Default: 0.50. Jika IoU >= nilai ini dan kelas sama, objek dianggap tidak berubah.'
    },
    triggerSnapshot: {
      text: 'Ambil snapshot baseline baru dari frame saat ini.',
      guide: 'Aktifkan untuk memperbarui kondisi acuan awal (baseline).'
    },
    alarmOnDifference: {
      text: 'Picu alarm peringatan jika terdeteksi ada objek baru muncul atau hilang.',
      guide: 'Event detections_diff akan dikirimkan ke downstream jika ada perbedaan.'
    },
    historyLen: {
      text: 'Panjang riwayat titik koordinat ekor lintasan objek bergerak.',
      guide: 'Default: 20 frame. Menentukan seberapa panjang jejak pergerakan yang digambar.'
    },
    fadeAlpha: {
      text: 'Efek transparansi memudar (fading) dari titik ekor lama ke posisi objek terbaru.',
      guide: 'Membuat tampilan garis lintasan terlihat profesional dan elegan.'
    },
    bracketLength: {
      text: 'Panjang garis siku pada setiap sudut kotak bounding box (piksel).',
      guide: 'Default: 16 piksel. Memberikan gaya corner-bracket modern ala antarmuka sci-fi/Roboflow.'
    },
    glow: {
      text: 'Efek pencahayaan lembut (halo glow) di sekeliling kotak deteksi.',
      guide: 'Menambahkan bayangan berpendar semi-transparan untuk meningkatkan estetika visual.'
    },
    // Fase 5: Agregasi Data, Cloud Sinks & Notifikasi, PTZ
    windowMinutes: {
      text: 'Durasi jendela waktu (menit) untuk akumulasi metrik analitik sesi.',
      guide: 'Default: 60 menit (1 jam). Data di-rollup secara berkala untuk laporan shift operasional.'
    },
    metricTypes: {
      text: 'Daftar jenis kalkulasi metrik ringkasan yang dihasilkan.',
      guide: 'Pilihan: count (total kemunculan), sum_duration (total detik kerja), avg_duration (rata-rata durasi), max_occupancy (kapasitas puncak).'
    },
    columns: {
      text: 'Daftar nama kolom data yang diekspor ke dalam baris file CSV.',
      guide: 'Dipisahkan koma. Contoh: timestamp,zone_name,type,working_seconds,item_count'
    },
    delimiter: {
      text: 'Karakter pemisah antar kolom dalam file CSV.',
      guide: 'Gunakan koma (,) untuk format standar internasional atau titik koma (;) untuk kompatibilitas Excel regional.'
    },
    outputFilePath: {
      text: 'Path lokasi penyimpanan file CSV pada server lokal.',
      guide: 'Contoh: data/exports/shift_report.csv. Jika dikosongkan, baris CSV tetap disalurkan lewat payload downstream.'
    },
    endpointUrl: {
      text: 'URL endpoint layanan S3 atau MinIO Object Storage.',
      guide: 'Gunakan https://s3.amazonaws.com untuk AWS S3, atau http://localhost:9000 untuk MinIO lokal.'
    },
    bucketName: {
      text: 'Nama bucket tempat penyimpanan berkas foto snapshot / crop event.',
      guide: 'Contoh: afi-vision-records. Pastikan bucket telah dibuat di server storage Anda.'
    },
    objectPrefix: {
      text: 'Folder awalan (prefix) path objek di dalam bucket.',
      guide: 'Contoh: events/ atau cctv-alerts/2026/. Memudahkan pengelompokan file berdasarkan kategori.'
    },
    credentialsSecretRef: {
      text: 'Nama variabel environment penyimpan kredensial akses S3.',
      guide: 'Default: AWS_ACCESS_KEY_ID (sistem otomatis membaca Secret Key pasangannya).'
    },
    imageQuality: {
      text: 'Kualitas kompresi gambar JPEG yang diunggah ke cloud (0-100).',
      guide: 'Default: 85. Keseimbangan sempurna antara ketajaman visual dan efisiensi kuota bandwidth.'
    },
    channel: {
      text: 'Saluran perpesanan instan tujuan pengiriman peringatan.',
      guide: 'Pilihan: telegram, slack, whatsapp, atau generic_webhook.'
    },
    destinationId: {
      text: 'ID Chat, Channel, atau nomor penerima pesan notifikasi.',
      guide: 'Untuk Telegram: Chat ID (misal: -100123456). Untuk Slack: Channel Name. Untuk WhatsApp: Nomor telepon dengan kode negara.'
    },
    botToken: {
      text: 'Token autentikasi Bot API untuk pengiriman pesan otomatis.',
      guide: 'Contoh: 123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11 untuk Telegram BotFather.'
    },
    messageTemplate: {
      text: 'Format template teks pesan peringatan dengan placeholder dinamis.',
      guide: 'Gunakan tag seperti {event.type}, {event.zoneName}, {timestamp} untuk menyisipkan data secara realtime.'
    },
    attachImage: {
      text: 'Kirimkan tangkapan layar frame kejadian sebagai lampiran foto notifikasi.',
      guide: 'Foto kejadian membantu operator memverifikasi alarm langsung dari smartphone.'
    },
    cameraIp: {
      text: 'Alamat IP kamera fisik PTZ di jaringan lokal.',
      guide: 'Contoh: 192.168.1.100. Pastikan kamera mendukung profil ONVIF PTZ.'
    },
    onvifPort: {
      text: 'Port layanan protokol ONVIF kamera pengawas.',
      guide: 'Default port standar: 80, 8080, atau 5000 tergantung merek kamera (Hikvision/Dahua/Axis).'
    },
    targetTrackId: {
      text: 'Kunci pelacakan pada satu Track ID spesifik secara permanen.',
      guide: 'Kosongkan jika ingin auto-follow objek pertama dari targetClass yang terdeteksi.'
    },
    deadzonePercent: {
      text: 'Radius batas toleransi tengah frame tanpa pergerakan motor kamera.',
      guide: 'Default: 0.15 (15%). Mencegah motor kamera jitter bergetar saat objek hanya bergeser tipis di tengah.'
    },
    panSpeed: {
      text: 'Faktor kecepatan perputaran horizontal kamera PTZ (0.0 s/d 1.0).',
      guide: 'Nilai lebih tinggi membuat kamera bergerak lebih agresif mengejar objek yang melintas cepat.'
    },
    tiltSpeed: {
      text: 'Faktor kecepatan kemiringan vertikal kamera PTZ (0.0 s/d 1.0).',
      guide: 'Nilai lebih tinggi mempercepat penyesuaian sudut pandang kamera ke atas/bawah.'
    },
    // OCR Text Reader (ONNX)
    recModelPath: {
      text: 'Lokasi path model ONNX pengenal karakter teks (Text Recognition).',
      guide: 'Default: data/models/ocr/ppocrv3_en_rec.onnx (~7.8 MB). Model ultra-ringan PP-OCRv3/v4 berkecepatan tinggi.'
    },
    detModelPath: {
      text: 'Lokasi path model ONNX pendeteksi kotak teks (Text Detection).',
      guide: 'Default: data/models/ocr/ppocrv3_det.onnx (~2.4 MB). Mendeteksi area teks baris secara presisi.'
    },
    dictPath: {
      text: 'Lokasi berkas kamus daftar karakter decoding CTC.',
      guide: 'Default: data/models/ocr/en_dict.txt. Memetakan index kelas model ke huruf dan angka.'
    },
    cropFromDetections: {
      text: 'Ekstraksi teks hanya dari dalam kotak deteksi objek upstream (misal plat nomor / label).',
      guide: 'True: Hanya membaca teks di dalam deteksi (menghemat komputasi). False: Memindai teks di seluruh frame gambar.'
    },
    characterWhitelist: {
      text: 'Filter karakter yang diizinkan untuk dibaca (Whitelist).',
      guide: 'Contoh: 0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ untuk nomor plat kendaraan atau nomor resi container.'
    },
    emitEvents: {
      text: 'Kirim event ocr_text_read ke pipeline downstream saat teks berhasil terbaca.',
      guide: 'Dapat diteruskan ke node Alert, Webhook, atau Database SQLite untuk pencatatan otomatis.'
    },
    // Sumber Input (Sources)
    sourceType: {
      text: 'Pilih jenis sumber input video atau gambar.',
      guide: 'Pilihan: Webcam (kamera laptop/USB bawaan), Daheng (kamera industri gigE/USB3), Image (gambar statis), Video (rekaman video).'
    },
    source: {
      text: 'Indeks kamera perangkat keras yang terhubung ke sistem.',
      guide: 'Default: 0 (webcam utama). Jika memiliki lebih dari 1 kamera USB, gunakan 1, 2, dst.'
    },
    streamUrl: {
      text: 'Alamat URL streaming langsung kamera CCTV / IP Camera.',
      guide: 'Mendukung RTSP (rtsp://ip:port/stream) & HTTP MJPEG (http://ip:port/video). Contoh: rtsp://192.168.1.100:554/stream1'
    },
    username: {
      text: 'Username otentikasi login perangkat IP Camera / CCTV.',
      guide: 'Kosongkan jika kamera CCTV tidak memerlukan otentikasi password.'
    },
    password: {
      text: 'Password otentikasi login perangkat IP Camera / CCTV.',
      guide: 'Kredensial akan otomatis digabungkan secara aman ke URL RTSP.'
    },
    transport: {
      text: 'Protokol transmisi paket video stream RTSP.',
      guide: 'TCP (Sangat direkomendasikan): Bebas korupsi frame dan artefak. UDP: Latensi ultra-rendah namun rentan frame robek jika sinyal Wi-Fi lemah.'
    },
    autoReconnect: {
      text: 'Otomatis menyambungkan kembali stream jika sinyal CCTV terputus.',
      guide: 'Aktifkan (True) agar pipeline tidak berhenti saat koneksi jaringan kamera berkedip atau restart.'
    },
    reconnectDelaySeconds: {
      text: 'Jeda waktu sebelum mencoba menyambungkan ulang kamera saat koneksi putus.',
      guide: 'Rentang: 0.5 s/d 10.0 detik. Nilai ideal: 2.0 detik agar tidak membebani router jaringan.'
    },
    filePath: {
      text: 'Lokasi file gambar (.jpg, .png) atau rekaman video (.mp4, .avi) lokal.',
      guide: 'Gunakan tombol Upload di samping untuk memilih file langsung dari komputer Anda.'
    },
    loop: {
      text: 'Putar ulang video secara otomatis dari awal setelah durasi video habis.',
      guide: 'Sangat berguna untuk pengujian workflow berulang kali tanpa harus me-restart pipeline.'
    },
    width: {
      text: 'Lebar resolusi frame kamera yang diminta ke driver kamera.',
      guide: 'Nilai 0 = resolusi asli sensor kamera. Contoh nilai lain: 1280, 1920. Semakin tinggi resolusi, semakin detail namun konsumsi CPU bertambah.'
    },
    height: {
      text: 'Tinggi resolusi frame kamera yang diminta ke driver kamera.',
      guide: 'Nilai 0 = resolusi asli sensor kamera. Contoh nilai lain: 720, 1080.'
    },
    targetFps: {
      text: 'Batas FPS frame yang diproses oleh node-node downstream; FPS sumber capture tetap berjalan sendiri.',
      guide: 'Nilai 0 berarti tanpa batas. Contoh: 10 membatasi pemrosesan cabang ini hingga 10 FPS.'
    },
    frameQueueSize: {
      text: 'Kapasitas buffer antrean frame di memori antar thread pemrosesan.',
      guide: 'Rentang: 1 s/d 64 frame. Nilai lebih kecil (2 - 8) menghasilkan latensi lebih rendah (real-time). Nilai lebih besar (16 - 32) mencegah frame tersendat jika AI model berat.'
    },
    dropFrames: {
      text: 'Buang frame lama jika pemrosesan AI lebih lambat dari FPS kamera.',
      guide: 'Sangat disarankan Aktif (True) untuk kamera Live CCTV agar preview tidak tertinggal (lagging).'
    },
    asyncPreview: {
      text: 'Jalankan rendering tampilan preview secara asinkron (multi-thread).',
      guide: 'Aktif (True) mencegah antarmuka web tersendat saat beban inferensi GPU/CPU mencapai 100%.'
    },

    // Model AI & Inferensi (Detection, Segmentation, Classification)
    engine: {
      text: 'Framework / runtime engine yang mengeksekusi model AI.',
      guide: 'Ultralytics YOLO: Paling populer & cepat (.pt). ONNX Runtime: Teroptimasi CPU & GPU umum. TensorRT: Akselerasi maksimal pada GPU NVIDIA. PyTorch: Standar riset.'
    },
    threshold: {
      text: 'Batas minimum skor keyakinan (confidence score) deteksi objek.',
      guide: 'Rentang: 0.00 s/d 1.00 (Nilai standar: 0.40 - 0.55). Semakin TINGGI: Deteksi semakin akurat & bersih dari false positive (salah deteksi). Semakin RENDAH: Lebih sensitif mendeteksi objek samar atau jauh.'
    },
    minimumConfidence: {
      text: 'Ambang batas keyakinan minimum agar objek disimpan atau di-event.',
      guide: 'Rentang: 0.00 s/d 1.00. Semakin tinggi hanya objek dengan deteksi sangat jelas yang dicatat.'
    },
    device: {
      text: 'Perangkat keras pemrosesan komputasi model AI.',
      guide: 'Auto: Otomatis mendeteksi GPU NVIDIA CUDA jika ada, atau CPU jika tidak ada. CUDA: Memaksimalkan GPU (FPS jauh lebih tinggi).'
    },
    customModelPath: {
      text: 'Path atau nama file model custom (YOLO .pt, ONNX, TFLite).',
      guide: 'Klik Upload di samping kolom Model Path, atau Upload Model di toolbar atas. Model akan disimpan di data/models dan diterapkan ke node yang sedang dipilih.'
    },
    modelPath: {
      text: 'File bobot model AI yang akan dimuat ke memori.',
      guide: 'Mendukung format .pt, .onnx, .tflite, .keras, .h5.'
    },
    classes: {
      text: 'Filter nama kelas objek yang ingin dideteksi (dipisah koma).',
      guide: 'Contoh: "person, car, motorcycle". Kosongkan jika ingin mendeteksi SEMUA 80 kelas COCO bawaan.'
    },
    customClasses: {
      text: 'Daftar nama label kelas khusus atau teks prompt deteksi open-vocabulary (dipisah koma).',
      guide: 'Untuk model kustom: urutkan sesuai index class. Untuk YOLO-World: ketik prompt objek yang dicari (misal: "forklift, safety vest, person, helmet").'
    },
    roboflowApiKey: {
      text: 'Roboflow API Private Key untuk autentikasi hosted inference Roboflow Universe.',
      guide: 'Dapatkan dari dashboard Roboflow Workspace Anda (Settings > API Keys).'
    },
    batchSize: {
      text: 'Jumlah frame yang diproses secara paralel dalam satu batch inferensi GPU.',
      guide: 'Nilai 1 = ideal untuk stream live kamera tunggal (latensi instan). Nilai 2 - 4 = throughput lebih tinggi jika banyak kamera atau input rekaman.'
    },
    detectEveryNFrames: {
      text: 'Lewati N-1 frame untuk menghemat beban daya CPU / GPU.',
      guide: 'Nilai 1 = Deteksi setiap frame (paling mulus). Nilai 2 = Deteksi tiap 2 frame sekali (menghemat 50% komputasi AI).'
    },
    maxDetectionFps: {
      text: 'Batas maksimal FPS pemrosesan AI (kecepatan inferensi).',
      guide: 'Nilai 0 = Tidak dibatasi (performa maksimal). Isi 15 atau 30 jika ingin mengunci konsumsi daya perangkat.'
    },
    iouThreshold: {
      text: 'Ambang batas Non-Maximum Suppression (NMS) tumpang-tindih kotak (IoU).',
      guide: 'Rentang: 0.10 s/d 0.95. Semakin RENDAH: Mencegah kotak ganda pada satu objek yang sama. Semakin TINGGI: Memungkinkan mendeteksi objek yang saling berhimpitan.'
    },
    imageSize: {
      text: 'Resolusi ukuran gambar (pixels) saat diumpankan ke model AI.',
      guide: 'Nilai standar: 640. Untuk foto resolusi tinggi dengan orang banyak / wajah kecil di baris belakang, naikkan ke 1024 atau 1280 agar semua orang terdeteksi jelas!'
    },
    topK: {
      text: 'Jumlah kelas probabilitas tertinggi yang diambil dari classifier.',
      guide: 'Default: 1 (hanya kelas dengan skor paling tinggi yang dimunculkan).'
    },

    // Pelacakan Objek (Tracking & Analysis)
    algorithm: {
      text: 'Algoritma asosiasi pelacakan objek (Object Tracking).',
      guide: 'ByteTrack: ringan untuk kamera statis. BoT-SORT: kompensasi gerak kamera. OC-SORT: arah gerak objek. C-BIoU: area pencocokan lebih luas untuk gerakan mendadak atau frame yang disampling.'
    },
    trackHighThreshold: {
      text: 'Pisahkan deteksi kuat untuk pencocokan utama dari deteksi lemah untuk pemulihan track.',
      guide: 'Default: 0.45. Ambang pembuatan ID baru diatur terpisah melalui New Track Threshold.'
    },
    trackLowThreshold: {
      text: 'Skor minimum untuk melanjutkan lintasan objek yang bergerak cepat/kabur (tahap 2).',
      guide: 'Rentang: 0.05 s/d 0.5 (Ideal: 0.1). Membantu menjaga ID tidak hilang saat objek terhalang sedikit.'
    },
    newTrackThreshold: {
      text: 'Skor deteksi untuk mengonfirmasi ID pelacakan permanen.',
      guide: 'Default: 0.5. Turunkan jika objek sulit mendapat ID; naikkan jika terlalu banyak track dari deteksi keliru.'
    },
    matchThreshold: {
      text: 'Batas toleransi jarak / IoU saat mencocokkan objek antar frame.',
      guide: 'Rentang: 0.1 s/d 0.8. Semakin rendah semakin fleksibel melacak objek berkecepatan tinggi.'
    },
    trackBuffer: {
      text: 'Batas jumlah frame riwayat ID disimpan sebelum dianggap keluar arena.',
      guide: 'Default: 90 pada skala 30 FPS. Frame yang sengaja dilewati sampler tidak dianggap deteksi kosong. Nilai besar memperpanjang memori tetapi bisa mencocokkan objek baru ke track lama.'
    },
    trackerFrameRate: {
      text: 'Skala FPS untuk buffer kehilangan track.',
      guide: 'Library menskalakan buffer dengan FPS ini / 30. Ini bukan batas kecepatan inferensi; gunakan Frame Sampler untuk membatasi FPS.'
    },
    classAgnostic: {
      text: 'Lacak objek tanpa membedakan jenis kelasnya.',
      guide: 'Aktifkan jika ingin ID pelacakan tidak berganti meski model sempat salah membaca kelas mobil menjadi bus di tengah jalan.'
    },
    showLostTracks: {
      text: 'Tetap gambar posisi prediksi objek yang sedang hilang/tertutup.',
      guide: 'Aktif (True) menampilkan kotak putus-putus pada posisi perkiraan objek saat terhalang.'
    },

    // Penghitung Objek (Counter & Filter)
    countOncePerTrack: {
      text: 'Hitung setiap objek ber-ID unik tepat 1 kali saja.',
      guide: 'Sangat direkomendasikan Aktif (True) agar objek yang diam di depan kamera tidak dihitung berkali-kali.'
    },
    showCounts: {
      text: 'Tampilkan widget ringkasan jumlah objek di pojok kanan atas preview.',
      guide: 'Aktifkan untuk melihat statistik akumulasi real-time (misal: "person: 5, car: 2").'
    },
    direction: {
      text: 'Arah pergerakan garis batas untuk penambahan hitungan.',
      guide: 'Pilihan: Both (semua arah), In / Enter (hanya saat masuk), Out / Exit (hanya saat keluar).'
    },
    minCount: {
      text: 'Jumlah minimum objek terdeteksi untuk meneruskan sinyal/event.',
      guide: 'Contoh: 3 = Hanya kirim alert jika ada minimal 3 orang terdeteksi bersamaan.'
    },
    retentionSeconds: {
      text: 'Durasi memori penyimpanan ID objek yang sudah terhitung (dalam detik).',
      guide: 'Default: 3600 detik (1 jam). Setelah waktu ini berlalu, ID lama yang masuk kembali akan dianggap objek baru.'
    },

    // Preprocessing & Transformasi Citra
    operation: {
      text: 'Operasi filter penyaringan matriks gambar OpenCV.',
      guide: 'Blur: Menghilangkan noise/bintik. Sharpen: Mempertegas tepian garis objek. Bilateral: Menghaluskan permukaan tanpa mengaburkan garis tepi.'
    },
    kernel: {
      text: 'Ukuran matriks konvolusi filter gambar (harus bilangan ganjil).',
      guide: 'Rentang: 3, 5, 7, 9, 11. Semakin BESAR nilainya, efek blur atau penajaman akan semakin drastis.'
    },
    mode: {
      text: 'Ruang warna target konversi citra.',
      guide: 'Grayscale: Hitam-putih (1 channel, sangat cepat untuk deteksi tepi). HSV: Mempermudah filter warna berdasarkan Hue (corak warna spesifik).'
    },
    rotation: {
      text: 'Rotasi orientasi sudut gambar kamera.',
      guide: 'Gunakan 90° atau 270° jika kamera dipasang posisi vertikal (portrait).'
    },
    method: {
      text: 'Algoritma pemisah latar belakang gerak (Background Subtraction).',
      guide: 'MOG2: Menyesuaikan bayangan secara dinamis. KNN: Sangat efisien untuk deteksi benda yang bergerak meninggalkan latar belakang statis.'
    },

    // Tampilan & Live Preview
    showBoxes: {
      text: 'Tampilkan kotak pembatas (Bounding Box) di sekitar objek.',
      guide: 'Aktif (True) untuk memperlihatkan lokasi presisi setiap objek yang terdeteksi.'
    },
    showLabels: {
      text: 'Tampilkan teks nama kelas dan persentase skor keyakinan.',
      guide: 'Menampilkan label nama (misal: "person 92%") di atas bounding box.'
    },
    showMasks: {
      text: 'Tampilkan poligon masker segmentasi transparan pada objek.',
      guide: 'Khusus node Object Segmentation: mewarnai bentuk kontur presisi dari objek yang ditemukan.'
    },
    showTrackIds: {
      text: 'Tampilkan nomor ID unik pelacakan pada label objek.',
      guide: 'Menampilkan tag ID (misal: "#1 person") agar Anda dapat memantau pergerakan individu objek.'
    },
    showTrails: {
      text: 'Tampilkan jejak garis riwayat pergerakan lintasan objek.',
      guide: 'Menggambar garis lintasan masa lalu yang dilalui oleh objek yang sedang bergerak.'
    },
    maskOpacity: {
      text: 'Tingkat kepekatan / transparansi warna masker segmentasi.',
      guide: 'Rentang: 0.05 (sangat transparan) s/d 0.85 (sangat pekat). Nilai standar yang nyaman: 0.35.'
    },

    // Output, Event & Alert
    url: {
      text: 'Endpoint URL server HTTP tujuan untuk pengiriman Webhook JSON.',
      guide: 'Contoh: http://192.168.1.50:8000/api/event. Server target akan menerima payload data deteksi secara real-time.'
    },
    cooldownSeconds: {
      text: 'Waktu jeda minimal antar pengiriman alert / notifikasi beruntun.',
      guide: 'Rentang: 1 s/d 300 detik. Mencegah banjir notifikasi saat objek berada lama di depan kamera.'
    },
    message: {
      text: 'Pesan kustom yang dicatat saat kondisi deteksi terpenuhi.',
      guide: 'Teks ini akan muncul di jendela terminal event dan dikirimkan ke webhook output.'
    },
    sendImage: {
      text: 'Sertakan gambar cuplikan frame kejadian dalam format Base64 JPEG.',
      guide: 'Berguna jika backend penerima webhook ingin langsung menyimpan atau menampilkan foto barang/orang yang terdeteksi.'
    },
    imageQuality: {
      text: 'Kualitas kompresi foto JPEG thumbnail Base64 (1 - 100).',
      guide: 'Nilai 80 = Keseimbangan ideal antara kejernihan gambar dan ukuran bandwidth transmisi yang ringan.'
    },
    databasePath: {
      text: 'Lokasi file database SQLite untuk penyimpanan rekaman log.',
      guide: 'Kosongkan untuk menggunakan database internal default sistem (data/database.sqlite).'
    },
    startPoint: {
      text: 'Titik koordinat awal garis pelintasan (x1, y1).',
      guide: 'Format: x,y (misal: 0.1, 0.5 untuk rasio). Gunakan tombol Draw Line di bawah untuk menggambar langsung di Live Preview.'
    },
    endPoint: {
      text: 'Titik koordinat akhir garis pelintasan (x2, y2).',
      guide: 'Format: x,y (misal: 0.9, 0.5 untuk rasio). Gunakan tombol Draw Line di bawah untuk menggambar langsung di Live Preview.'
    },
    triggerAnchor: {
      text: 'Titik acuan bounding box objek untuk deteksi pelintasan.',
      guide: 'bottom_center (kaki/dasar objek, sangat cocok untuk orang & mobil), center (tengah), top_center (atas).'
    },
    inLabel: {
      text: 'Label teks untuk arah masuk (IN).',
      guide: 'Default: IN. Contoh lain: MASUK, NAIK.'
    },
    outLabel: {
      text: 'Label teks untuk arah keluar (OUT).',
      guide: 'Default: OUT. Contoh lain: KELUAR, TURUN.'
    },
    invertDirection: {
      text: 'Tukar / balik arah pelintasan IN dan OUT.',
      guide: 'Aktifkan jika arah deteksi masuk/keluar terbalik dari orientasi garis yang Anda gambar.'
    },
    countMode: {
      text: 'Mode arah penghitungan pelintasan objek.',
      guide: 'both (hitung dua arah IN dan OUT), in_only (hanya hitung IN), out_only (hanya hitung OUT).'
    },
    thresholdSeconds: {
      text: 'Batas durasi waktu maksimum di dalam zona sebelum memicu status loitering.',
      guide: 'Satuan detik. Contoh: 5.0 detik. Jika objek berdiam di area lebih lama dari nilai ini, status LOITERING akan aktif.'
    },
    zoneName: {
      text: 'Nama area untuk label overlay dan event.',
      guide: 'Gunakan nama yang mudah dikenali operator, misalnya Workshop Area atau Warehouse Exit.'
    },
    requiredClasses: {
      text: 'Kelas objek yang wajib ada di dalam zona.',
      guide: 'Pisahkan beberapa kelas dengan koma, misalnya tire, pallet.'
    },
    requiredCount: {
      text: 'Jumlah minimum objek kelas wajib yang harus teramati.',
      guide: 'Gunakan 1 untuk memastikan setidaknya satu objek kelas wajib ada.'
    },
    triggerClasses: {
      text: 'Kelas objek yang memulai pengukuran aktivitas zona.',
      guide: 'Pisahkan beberapa kelas dengan koma, misalnya person, forklift.'
    },
    triggerCount: {
      text: 'Jumlah minimum objek kelas pemicu yang harus teramati.',
      guide: 'Gunakan 1 untuk aktivitas yang dipicu oleh satu objek.'
    },
    confirmationSeconds: {
      text: 'Durasi kondisi aktivitas harus bertahan sebelum event diterbitkan.',
      guide: 'Naikkan nilai ini jika deteksi sesaat terlalu sering memicu event.'
    },
    countFromStart: {
      text: 'Menentukan kapan timer aktivitas mulai dihitung.',
      guide: 'Aktifkan untuk menghitung durasi sejak observasi aktivitas pertama.'
    },
    personGraceSeconds: {
      text: 'Toleransi ketika kelas pemicu tidak terlihat sesaat.',
      guide: 'Gunakan nilai kecil untuk menahan kedipan deteksi tanpa menahan event terlalu lama.'
    },
    requiredGraceSeconds: {
      text: 'Toleransi ketika kelas wajib tidak terlihat sesaat.',
      guide: 'Objek yang hilang dalam durasi ini masih dianggap memenuhi syarat.'
    },
    absenceGraceSeconds: {
      text: 'Durasi observasi luar zona sebelum event keluar diterbitkan.',
      guide: 'Objek harus benar-benar teramati di luar zona; track yang hilang tidak dihitung sebagai keluar.'
    },
    maxObservationGapSeconds: {
      text: 'Jeda maksimum antar observasi yang masih dianggap berkesinambungan.',
      guide: 'Jika jeda lebih besar, status observasi perlu dibangun kembali dari data baru.'
    },
    maxSessionDurationSeconds: {
      text: 'Batas durasi sesi (0 = nonaktif).',
      guide: 'Menandai sesi yang terlalu panjang dan tetap membiarkannya berjalan; gunakan 0 untuk menonaktifkan.'
    },
    points: {
      text: 'Daftar titik koordinat poligon zona (x1,y1; x2,y2; ...).',
      guide: 'Format: x1,y1; x2,y2... Gunakan tombol Draw Zone di bawah untuk klik 4 titik langsung di Live Preview.'
    },
    showTimer: {
      text: 'Tampilkan label durasi detik di atas objek.',
      guide: 'Aktifkan (True) untuk melihat timer waktu berjalan di atas bounding box setiap objek secara real-time.'
    },
    sliceWidth: {
      text: 'Lebar petak tile pemotongan frame resolusi tinggi (SAHI).',
      guide: 'Default: 640 pixel. Menjaga ketajaman deteksi objek kecil pada kamera 4K/1080p.'
    },
    sliceHeight: {
      text: 'Tinggi petak tile pemotongan frame resolusi tinggi (SAHI).',
      guide: 'Default: 640 pixel.'
    },
    overlapRatio: {
      text: 'Rasio tumpang tindih antar petak (tile overlap).',
      guide: 'Rentang 0.0 s/d 0.5 (Default: 0.2 atau 20%). Mencegah objek yang berada di perbatasan petak terpotong.'
    },
    pixelateBlock: {
      text: 'Ukuran blok pikselasi untuk sensor privasi.',
      guide: 'Rentang 4 s/d 32 pixel. Semakin besar nilai, semakin buram sensor kotaknya.'
    },
    perClassThresholds: {
      text: 'Ambang batas confidence per-kelas (contoh: person:0.35, car:0.60).',
      guide: 'Memungkinkan filter sensitivitas berbeda untuk setiap tipe objek tanpa mengubah threshold global.'
    },
    classRemap: {
      text: 'Pemetaan ulang nama label kelas (contoh: person->visitor, truck->heavy_vehicle).',
      guide: 'Ganti nama tampilan label secara langsung untuk kebutuhan pelaporan atau klasifikasi bisnis khusus.'
    },
    recordClip: {
      text: 'Otomatis simpan rekaman video MP4 insiden kejadian ke folder data/outputs/events/.',
      guide: 'Menyimpan klip video melingkar 5 detik saat alert deteksi atau loitering terpicu.'
    },
    clipDurationSeconds: {
      text: 'Durasi klip rekaman video insiden (dalam detik).',
      guide: 'Default: 5 detik. Klip disimpan dalam format MP4 standar yang dapat diputar langsung di browser.'
    },
    minArea: {
      text: 'Luas minimum kotak bounding box (pixel: lebar x tinggi).',
      guide: 'Nilai 0 = Nonaktif. Berguna menyaring noise bintik kecil, serangga terbang, atau false positive berukuran mikro.'
    },
    maxArea: {
      text: 'Luas maksimum kotak bounding box (pixel: lebar x tinggi).',
      guide: 'Nilai 0 = Nonaktif. Mengabaikan objek yang menutupi seluruh layar atau terlalu dekat dengan lensa kamera.'
    },
    minAspectRatio: {
      text: 'Rasio aspek minimum (lebar dibagi tinggi).',
      guide: 'Nilai 0.0 = Nonaktif. Contoh: 0.2 untuk menyaring objek vertikal tegak (seperti orang berdiri).'
    },
    maxAspectRatio: {
      text: 'Rasio aspek maksimum (lebar dibagi tinggi).',
      guide: 'Nilai 0.0 = Nonaktif. Contoh: 3.0 untuk menyaring objek memanjang horizontal (seperti mobil/truk).'
    },
    excludeBorderMargin: {
      text: 'Batas jarak aman dari tepi frame kamera (dalam pixel).',
      guide: 'Nilai 0 = Nonaktif. Isi 10 - 20 jika ingin mengabaikan objek yang baru muncul setengah badan di pinggir layar.'
    },
    perClassConfidence: {
      text: 'Ambang batas akurasi spesifik per-kelas objek (format: person:0.75, tire:0.40, truck:0.60).',
      guide: 'Memungkinkan threshold fleksibel untuk objek sulit (seperti ban) tanpa membiarkan noise untuk objek umum.'
    },
    defaultConfidence: {
      text: 'Ambang batas akurasi default untuk kelas yang tidak terdaftar di perClassConfidence.',
      guide: 'Nilai 0.0 = menggunakan confidence bawaan detector.'
    },
    paddingPercent: {
      text: 'Persentase ekspansi kotak pembatas (bounding box padding) sebesar 0 - 100%.',
      guide: 'Memperluas area kotak pembatas agar seluruh kontur objek tercakup sebelum dipotong untuk inspeksi sekunder.'
    },
    paddingMode: {
      text: 'Metode penyesuaian rasio ekspansi kotak pembatas.',
      guide: 'aspect_ratio_preserve mempertahankan bentuk rasio asli kotak objek.'
    },
    requiredVotes: {
      text: 'Jumlah suara/model minimal yang harus sepakat atas deteksi objek yang sama.',
      guide: 'Contoh: 2 jika menghubungkan YOLO dan RF-DETR untuk memangkas false alarm.'
    },
    confidenceAggregation: {
      text: 'Metode kalkulasi nilai akurasi konsensus.',
      guide: 'Average: Rata-rata nilai confidence seluruh model yang sepakat. Max: Ambil nilai tertinggi. Min: Nilai paling konservatif.'
    },
    boxAggregation: {
      text: 'Metode penentuan koordinat kotak konsensus.',
      guide: 'highest_confidence: Menggunakan koordinat dari model dengan akurasi tertinggi. average: Rata-rata koordinat.'
    },
    classAware: {
      text: 'Wajibkan kelas objek identik saat mencocokkan deteksi antar-model.',
      guide: 'True: Hanya sepakat jika kedua model mendeteksi label kelas yang sama (misal sama-sama person).'
    },
    mode: {
      text: 'Mode perhitungan jumlah objek pada kamera.',
      guide: 'Occupancy: Jumlah objek yang sedang aktif di frame saat ini. Cumulative: Total unik objek yang pernah lewat sejak awal.'
    },
    maxCapacity: {
      text: 'Batas kapasitas kuota maksimum area atau ruangan.',
      guide: 'Nilai 0 = Nonaktif. Jika jumlah orang di area melebihi batas ini, sistem akan memicu alarm status OVERFLOW!'
    },
    alertOnCapacityExceeded: {
      text: 'Pemicu alarm saat kuota kapasitas terlampaui.',
      guide: 'Aktifkan (True) untuk mencatat kejadian overcapacity ke log event dan webhook secara otomatis.'
    },
    captureMode: {
      text: 'Format cuplikan gambar inspeksi yang disimpan.',
      guide: 'crop_only: Hanya potongan objek target. full_frame_clean: Frame kamera utuh. full_frame_annotated: Frame utuh lengkap kotak AI.'
    },
    maxFilesRetention: {
      text: 'Batas maksimum jumlah file gambar di folder (FIFO Cleanup).',
      guide: 'Default: 1000 file. Foto paling lama otomatis dihapus jika kuota tercapai agar hard disk Dokploy/server tidak jebol (Disk Full).'
    },
    burnWatermark: {
      text: 'Sematkan cap tanggal, jam, dan ID deteksi di pojok foto.',
      guide: 'Sangat direkomendasikan Aktif (True) sebagai bukti otentik inspeksi visual dan kepatuhan audit keamanan.'
    },
    payloadTemplate: {
      text: 'Format template JSON kustom untuk pengiriman webhook API.',
      guide: 'Mendukung variabel dinamis: {timestamp}, {matches}, {detection.class}, {detection.confidence}, {track.id}. Kosongkan untuk JSON standar.'
    },
    retryCount: {
      text: 'Jumlah percobaan pengiriman ulang otomatis jika server tujuan gagal/timeout.',
      guide: 'Rentang 0 s/d 5 kali percobaan (Default: 2) dengan interval exponential backoff.'
    },
    timeoutSeconds: {
      text: 'Batas waktu tunggu respon HTTP dari server webhook (dalam detik).',
      guide: 'Default: 5.0 detik. Mencegah pipeline tersendat jika server penerima webhook lambat.'
    },
    contextPaddingPercent: {
      text: 'Persentase padding tambahan di sekeliling kotak objek target.',
      guide: 'Contoh: 0.15 (15%) memberikan konteks visual ekstra di sekitar objek agar pemrosesan lanjutan (seperti classifier/OCR) tidak terpotong ketat di tepi.'
    },
    square: {
      text: 'Potong frame menjadi rasio kotak sempurna (1:1) dengan letterbox padding.',
      guide: 'Aktifkan (True) untuk menstabilkan input model klasifikasi/inspeksi sekunder tanpa distorsi regangan atau perubahan aspect ratio.'
    },
    padColor: {
      text: 'Warna latar belakang padding letterbox jika mode Square aktif.',
      guide: 'Default: #000000 (Hitam). Format hex RGB (#000000 s/d #ffffff).'
    },
    minCropWidth: {
      text: 'Lebar minimum hasil crop objek (pixel).',
      guide: 'Objek dengan lebar lebih kecil dari batas ini akan diabaikan agar tidak menghasilkan potongan gambar buram/terlalu kecil.'
    },
    minCropHeight: {
      text: 'Tinggi minimum hasil crop objek (pixel).',
      guide: 'Objek dengan tinggi lebih kecil dari batas ini akan diabaikan.'
    },
    invertZone: {
      text: 'Mode pantau area luar (zona eksklusi / perimeter terbalik).',
      guide: 'Jika Aktif (True), hanya objek yang berada di LUAR polygon/kotak yang akan diteruskan (misal: perimeter luar gudang atau area terlarang).'
    },
    useClahe: {
      text: 'Tingkatkan kontras lokal adaptif (Night Vision CLAHE).',
      guide: 'Menggunakan Contrast Limited Adaptive Histogram Equalization pada kanal luminansi (L*) ruang warna LAB tanpa merusak warna asli.'
    },
    autoLowLight: {
      text: 'Otomatis aktifkan peningkatan malam hanya saat frame gelap.',
      guide: 'Mendeteksi rata-rata kecerahan sensor CCTV dan mengaktifkan CLAHE otomatis saat malam atau kondisi redup.'
    },
    lowLightThreshold: {
      text: 'Batas rata-rata kecerahan untuk memicu mode low-light.',
      guide: 'Rentang 0 - 255. Default: 65.0. Nilai di bawah ini akan memicu CLAHE otomatis.'
    },
    clipLimit: {
      text: 'Batas amplifikasi kontras CLAHE untuk mencegah peningkatan noise.',
      guide: 'Default: 2.5 (Rentang 1.0 - 5.0). Nilai lebih tinggi memberi kontras lebih tajam namun dapat memperjelas noise kamera.'
    },
    tileGridSize: {
      text: 'Ukuran grid blok lokal histogram CLAHE.',
      guide: 'Default: 8 (Grid 8x8). Mengontrol pembagian area lokal untuk perataan kontras adaptif.'
    },
    detectFreeze: {
      text: 'Deteksi video streaming CCTV yang membeku / macet (Stream Watchdog).',
      guide: 'Mendeteksi jika frame RTSP identik terus-menerus tanpa ada perubahan selama beberapa detik akibat gangguan decoder atau kamera hang.'
    },
    freezeThresholdSeconds: {
      text: 'Ambang batas durasi diam sebelum dinyatakan macet / beku (dalam detik).',
      guide: 'Default: 3.0 detik. Jika video tidak bergerak melampaui waktu ini, alarm peringatan stream freeze akan dipicu.'
    },
    detectTamper: {
      text: 'Deteksi sabotase lensa kamera CCTV (tertutup atau silau laser).',
      guide: 'Mendeteksi perubahan ekstrem jika lensa ditutup kain/cat semprot (gelap total) atau disorot laser/senter kuat (terang benderang).'
    },
    tamperDarkThreshold: {
      text: 'Batas luminansi minimum sabotase lensa tertutup / gelap.',
      guide: 'Default: 6.0 (Sangat gelap mendekati hitam pekat).'
    },
    tamperBrightThreshold: {
      text: 'Batas luminansi maksimum sabotase lensa disorot cahaya kuat.',
      guide: 'Default: 248.0 (Putih menyilaukan mendekati 255).'
    },
    retentionDays: {
      text: 'Masa retensi penyimpanan rekaman deteksi lokal SQLite (dalam hari).',
      guide: 'Default: 14 hari. Data deteksi dan frame debug yang lebih lama otomatis dibersihkan dengan VACUUM agar disk Dokploy tidak penuh.'
    },
    aggregateHourly: {
      text: 'Ringkas otomatis data ke tabel analitik agregasi per jam.',
      guide: 'Aktifkan (True) untuk mempercepat query dashboard dan pelaporan tren tanpa harus membaca jutaan baris deteksi mentah.'
    },
    metric: {
      text: 'Jenis metrik / nilai data yang ingin dievaluasi untuk percabangan alur.',
      guide: 'Pilihan: Jumlah Objek (Live Count), Hitungan Masuk (IN) Line Counter, Hitungan Keluar (OUT), Total Hitungan, Ada Objek Melintas (Event Frame), Jumlah Kelas Tertentu, Akurasi Tertinggi, atau Skor Anomali.'
    },
    operator: {
      text: 'Operator logika pembanding antara nilai aktual dengan nilai acuan (threshold).',
      guide: 'Pilihan: >= (Lebih dari sama dengan), > (Lebih dari), <= (Kurang dari sama dengan), < (Kurang dari), == (Sama dengan), != (Tidak sama dengan).'
    },
    value: {
      text: 'Nilai angka acuan pembanding (threshold) untuk evaluasi kondisi logika.',
      guide: 'Contoh: 1 (jika ada minimal 1 objek), 5 (jika antrean mencapai 5), 10 (target hitungan masuk Line Counter), atau 0.85 (untuk confidence/akurasi).'
    },
    passWhen: {
      text: 'Pilihan cabang eksekusi alur logika (IF atau ELSE).',
      guide: 'Cabang IF (True): Meneruskan deteksi/frame ke node berikutnya hanya jika kondisi TERPENUHI. Cabang ELSE (False): Meneruskan ke node berikutnya jika kondisi TIDAK TERPENUHI (kebalikannya).'
    },
    alertOnExceed: {
      text: 'Kirim sinyal alarm atau event peringatan jika objek melampaui batas waktu dwell time.',
      guide: 'Aktifkan untuk memantau kendaraan yang parkir terlalu lama atau orang yang berdiam mencurigakan.'
    },
    alpha: {
      text: 'Faktor skala cropping gambar kalibrasi (0.0 s/d 1.0).',
      guide: '0.0 = potong seluruh area hitam di pinggir, 1.0 = pertahankan seluruh piksel sensor.'
    },
    anomalyThreshold: {
      text: 'Nilai batas skor cacat (anomaly score) untuk menentukan status NG / OK.',
      guide: 'Deteksi dengan skor di atas batas ini akan ditandai sebagai produk cacat (NG).'
    },
    apiKey: {
      text: 'Kunci otentikasi API penyedia layanan (OpenAI, OpenRouter, Jev).',
      guide: 'Kosongkan di antarmuka jika sudah disetel di file .env server untuk keamanan kredensial.'
    },
    background: {
      text: 'Gambarkan kotak latar belakang gelap di belakang teks agar mudah dibaca.',
      guide: 'Sangat disarankan aktif (True) agar teks selalu kontras di latar terang maupun gelap.'
    },
    backgroundColor: {
      text: 'Warna latar belakang teks anotasi.',
      guide: 'Default: #111827 (abu-abu gelap pekat).'
    },
    baseUrl: {
      text: 'Alamat endpoint URL basis API (contoh untuk OpenAI, OpenRouter, atau Ollama lokal).',
      guide: 'Default: https://api.openai.com/v1 atau http://localhost:11434/v1 untuk server Ollama lokal.'
    },
    botSortCmcDownscale: {
      text: 'Faktor downscale gambar saat menghitung kompensasi gerakan kamera.',
      guide: 'Default 2. Mempercepat kalkulasi optical flow hingga 4x tanpa mengurangi akurasi tracking.'
    },
    botSortCmcMethod: {
      text: 'Metode estimasi gerakan kamera untuk BoT-SORT.',
      guide: 'Pilihan: sparseOptFlow (cepat dan efisien), orb, sift, atau ecc.'
    },
    botSortFirstIouThreshold: {
      text: 'Ambang batas IoU pencocokan tahap pertama pada BoT-SORT.',
      guide: 'Default 0.2. Digunakan untuk mencocokkan deteksi berakurasi tinggi dengan jejak yang ada.'
    },
    botSortGmc: {
      text: 'Aktifkan kompensasi gerakan kamera (Global Motion Compensation).',
      guide: 'Wajib aktif jika kamera bergetar atau digerakkan (PTZ) agar jejak objek tidak lepas.'
    },
    botSortSecondIouThreshold: {
      text: 'Ambang batas IoU pencocokan tahap kedua pada deteksi yang lebih lemah.',
      guide: 'Default 0.5. Memulihkan jejak saat objek tertutup bayangan atau mengalami blur sesaat.'
    },
    botSortUnconfirmedIouThreshold: {
      text: 'Ambang batas pencocokan untuk jejak yang baru dibuat dan belum terkonfirmasi.',
      guide: 'Default 0.3.'
    },
    brightness: {
      text: 'Tingkat penambahan kecerahan gambar.',
      guide: 'Rentang: -100 s/d +100. Nilai positif mencerahkan frame yang gelap.'
    },
    calibrationPath: {
      text: 'Lokasi file matriks kalibrasi lensa kamera (.yml atau .xml).',
      guide: 'Digunakan untuk menghilangkan efek lengkung cembung lensa fisheye atau sudut lebar (wide-angle).'
    },
    code: {
      text: 'Script kode Python yang dieksekusi per frame video.',
      guide: 'Wajib memiliki fungsi def process(frame, state): dan mengembalikan objek frame uint8 HxWx3 BGR.'
    },
    color: {
      text: 'Warna garis kotak atau teks anotasi.',
      guide: 'Gunakan kode warna Hex (contoh: #2563eb untuk biru, #22c55e untuk hijau).'
    },
    concepts: {
      text: 'Daftar konsep teks yang ingin disegmentasi oleh SAM 3.',
      guide: 'Contoh: person, tire, helmet, forklift.'
    },
    contrast: {
      text: 'Faktor pengali kontras gambar.',
      guide: 'Rentang: 0.1 s/d 3.0. Nilai 1.0 berarti kontras normal.'
    },
    convnextCheckpoint: {
      text: 'File bobot model ConvNeXt kustom.',
      guide: 'Kosongkan untuk menggunakan pretrained model bawaan torchvision/timm.'
    },
    convnextClasses: {
      text: 'Daftar label kelas output untuk model klasifikasi ConvNeXt.',
      guide: 'Pisahkan dengan koma sesuai urutan indeks kelas hasil training.'
    },
    convnextHalfPrecision: {
      text: 'Gunakan presisi FP16 pada model ConvNeXt untuk efisiensi GPU.',
      guide: 'Menghemat memori VRAM GPU hingga 50%.'
    },
    convnextImageSize: {
      text: 'Ukuran resolusi gambar input model ConvNeXt.',
      guide: 'Default 224 piksel untuk arsitektur standar ConvNeXt.'
    },
    convnextModel: {
      text: 'Arsitektur model klasifikasi ConvNeXt.',
      guide: 'Pilihan: Tiny, Small, Base, atau Large tergantung kebutuhan akurasi vs kecepatan.'
    },
    count: {
      text: 'Jumlah minimal objek yang harus ada untuk memenuhi kondisi.',
      guide: 'Contoh: 1 jika mencari setidaknya satu orang, atau 4 untuk mendeteksi kerumunan.'
    },
    cropFromDetections: {
      text: 'Potong area kotak deteksi terlebih dahulu sebelum memindai QR / Barcode.',
      guide: 'Meningkatkan kecepatan dan keberhasilan membaca kode kecil pada resolusi tinggi.'
    },
    cropGridColumns: {
      text: 'Jumlah kolom grid penataan potongan objek (0 = otomatis).',
      guide: 'Pilih 2, 3, atau 4 kolom untuk tata letak yang sesuai dengan rasio layar Anda.'
    },
    cropGridGap: {
      text: 'Jarak spasi renggang antar potongan objek pada grid preview (piksel).',
      guide: 'Default 8 piksel.'
    },
    cropGridMaxItems: {
      text: 'Maksimal jumlah potongan objek yang ditampilkan secara bersamaan pada grid preview.',
      guide: 'Default 16 objek untuk menjaga kerapian tampilan antarmuka monitor.'
    },
    crossingDirection: {
      text: 'Arah perlintasan objek terhadap batas area zona ROI.',
      guide: 'enter: Memicu saat objek MASUK ke dalam area. exit: Memicu saat objek KELUAR dari area. both: Dua arah.'
    },
    customHeaders: {
      text: 'Header HTTP kustom untuk otentikasi webhook (REST API).',
      guide: 'Contoh: Authorization: Bearer token123 atau X-API-Key: secret.'
    },
    dahengExposureUs: {
      text: 'Waktu bukaan rana eksposur sensor kamera Daheng dalam mikrodetik (µs).',
      guide: 'Nilai 0 = otomatis. Nilai manual rendah (misal 5000µs) menghilangkan blur pada objek berkecepatan tinggi.'
    },
    dahengFrameRate: {
      text: 'Target batasan FPS kamera Daheng (0 = kecepatan maksimal sensor).',
      guide: 'Sesuaikan dengan kemampuan prosesor dan pencahayaan pabrik Anda.'
    },
    dahengGain: {
      text: 'Penguatan sinyal sensor kamera Daheng dalam desibel (Gain dB).',
      guide: 'Gunakan penguatan tambahan jika lingkungan pencahayaan workshop redup.'
    },
    dahengIdentifier: {
      text: 'Identifier nomor urut (1, 2) atau Serial Number kamera Daheng.',
      guide: 'Masukkan sesuai nomor seri yang tertera pada badan kamera industri Anda.'
    },
    dahengOpenMode: {
      text: 'Metode pendeteksian kamera Daheng Galaxy GXI.',
      guide: 'index: Berdasarkan nomor urut kamera. sn: Berdasarkan nomor seri hardware. ip: Berdasarkan IP Address.'
    },
    dahengTimeoutMs: {
      text: 'Batas waktu maksimal menunggu frame dari kamera Daheng dalam milidetik.',
      guide: 'Default 1000ms. Menghindari sistem terhenti jika kabel USB/Ethernet kamera terlepas.'
    },
    detectShadows: {
      text: 'Deteksi dan tandai bayangan objek bergerak secara terpisah.',
      guide: 'Membantu memisahkan bayangan di lantai dari bentuk fisik tubuh objek sesungguhnya.'
    },
    efficientadModel: {
      text: 'File bobot model deteksi cacat EfficientAD (.pth).',
      guide: 'Dilatih khusus menggunakan foto sampel produk normal (good samples) tanpa perlu sampel cacat.'
    },
    enabledValue: {
      text: 'Nilai status logika yang dianggap aktif (True atau False).',
      guide: 'Digunakan oleh node gerbang logika AND / OR untuk menentukan kondisi output.'
    },
    eventObjectsOnly: {
      text: 'Hanya simpan objek yang memicu kejadian event (bukan seluruh frame biasa).',
      guide: 'Sangat disarankan aktif (True) agar kapasitas database tetap hemat dan tidak bengkak.'
    },
    filenameTemplate: {
      text: 'Pola penamaan otomatis file gambar yang disimpan.',
      guide: 'Dukung variabel: {timestamp}, {track_id}, {class}, {index}. Contoh: {timestamp}_{class}_{track_id}.'
    },
    fillOpacity: {
      text: 'Tingkat transparansi warna isian di dalam kotak bounding box (0.0 s/d 1.0).',
      guide: '0.0 = kotak transparan berongga, 0.2 = sentuhan warna transparan tipis.'
    },
    flip: {
      text: 'Arah pembalikan cermin gambar (flip).',
      guide: 'none: Tanpa pembalikan. horizontal: Cermin kiri-kanan. vertical: Terbalik atas-bawah.'
    },
    flushIntervalMs: {
      text: 'Interval penulisan buffer transaksi database ke disk dalam milidetik.',
      guide: 'Default 500ms untuk performa write I/O yang optimal tanpa memblokir pipeline.'
    },
    fontScale: {
      text: 'Skala perbesaran ukuran huruf teks (font scale).',
      guide: 'Rentang: 0.3 s/d 3.0. Nilai ideal: 0.6 untuk teks ringkas, 1.0 untuk teks judul.'
    },
    format: {
      text: 'Format kompresi file gambar yang disimpan.',
      guide: 'Pilihan: jpg (ukuran kecil), png (lossless), webp (modern dan efisien).'
    },
    heatmapOpacity: {
      text: 'Tingkat transparansi lapisan peta panas cacat visual (0.0 s/d 1.0).',
      guide: 'Default 0.35 agar detail fisik produk asli di bawah heatmap tetap terlihat jelas.'
    },
    history: {
      text: 'Jumlah frame riwayat yang dipelajari sebagai latar belakang diam.',
      guide: 'Rentang: 100 s/d 2000 frame. Nilai lebih besar membuat model latar lebih stabil terhadap angin/bayangan.'
    },
    historySeconds: {
      text: 'Durasi memori riwayat posisi objek untuk fitur rewind-replay Kalman Filter.',
      guide: 'Default 5.0 detik. Memungkinkan rekonsiliasi posisi saat respon API VLM tiba.'
    },
    holdLastEvent: {
      text: 'Tahan gambar event terakhir pada layar preview hingga ada event baru.',
      guide: 'Memudahkan operator melihat bukti visual kejadian yang baru saja terjadi.'
    },
    imageMaxDimension: {
      text: 'Batas resolusi maksimal gambar yang dikirim ke AI Agent.',
      guide: 'Default 720 piksel. Nilai lebih rendah mempercepat transmisi dan menghemat token vision.'
    },
    imgsz: {
      text: 'Ukuran dimensi gambar input untuk inferensi segmenter.',
      guide: 'Default 1008 piksel untuk SAM 3; 640 untuk model YOLO bawaan.'
    },
    includeImage: {
      text: 'Sertakan gambar visual snapshot frame kamera saat memanggil AI Agent.',
      guide: 'Wajib aktif jika model membutuhkan kemampuan penglihatan multimodal (VLM).'
    },
    insideBbox: {
      text: 'Terapkan sensor privasi (blur/pixelate) hanya di dalam area kotak objek.',
      guide: 'Jika aktif, hanya wajah atau plat nomor yang disensor, lingkungan sekitar tetap jernih.'
    },
    interpolation: {
      text: 'Metode algoritma interpolasi perubahan resolusi (resize).',
      guide: 'linear: Cepat dan halus (default). area: Terbaik untuk pengecilan gambar (downsampling). cubic: Tajam.'
    },
    jpegQuality: {
      text: 'Kualitas kompresi file gambar JPEG dalam persentase (1 s/d 100).',
      guide: 'Default 95% untuk detail gambar maksimal tanpa artefak kompresi.'
    },
    jsonSchema: {
      text: 'Skema JSON opsional untuk validasi ketat struktur output AI Agent.',
      guide: 'Kosongkan jika menggunakan format prompt standar.'
    },
    kernelSize: {
      text: 'Ukuran kernel efek blur sensor privasi (wajib angka ganjil).',
      guide: 'Rentang: 5 s/d 99 piksel. Semakin besar angka, semakin buram sensornya.'
    },
    labelTemplate: {
      text: 'Format teks label di atas bounding box deteksi.',
      guide: 'Default: {detection.class} {detection.confidence}.'
    },
    layers: {
      text: 'Daftar tumpukan lapisan visual anotasi (kotak, label, akurasi, status badge, heatmap).',
      guide: 'Dapat ditata ulang urutannya dan diaktifkan/dinonaktifkan per lapisan secara fleksibel.'
    },
    lineColor: {
      text: 'Warna visual garis counter pada video preview.',
      guide: 'Gunakan kode Hex, misalnya #22c55e (hijau terang).'
    },
    lineWidth: {
      text: 'Ketebalan garis visual counter di layar.',
      guide: 'Rentang: 1 hingga 8 piksel. Nilai ideal: 2 atau 3 piksel.'
    },
    lines: {
      text: 'Daftar konfigurasi garis perlintasan multi-garis.',
      guide: 'Mendukung penamaan garis terpisah, koordinat titik awal/akhir, dan label arah masuk/keluar.'
    },
    match: {
      text: 'Kriteria pencocokan evaluasi kondisi objek.',
      guide: 'any: Setidaknya salah satu objek memenuhi syarat. all: Seluruh objek wajib memenuhi syarat.'
    },
    maxCrops: {
      text: 'Maksimal jumlah potongan objek yang dihasilkan per frame video.',
      guide: 'Default 32 potongan untuk menjaga performa memori sistem.'
    },
    maxPreviewFps: {
      text: 'Batas maksimal FPS tampilan live preview di peramban web (0 = tanpa batas).',
      guide: 'Sangat berguna untuk menghemat penggunaan CPU/GPU browser operator.'
    },
    maxQueue: {
      text: 'Kapasitas antrean antrean query database sebelum frame dibuang jika disk lambat.',
      guide: 'Default 10000 item untuk mencegah lonjakan pemakaian memori RAM.'
    },
    maxTokens: {
      text: 'Batas maksimal panjang token jawaban dari AI Agent.',
      guide: 'Default 500 token, cukup untuk keputusan terstruktur dan alasan singkat.'
    },
    minConfidence: {
      text: 'Ambang batas akurasi minimal hasil deteksi VLM sebelum dimasukkan ke tracker.',
      guide: 'Rentang: 0.0 s/d 1.0. Nilai umum: 0.40 - 0.60.'
    },
    minSize: {
      text: 'Ukuran minimal sisi objek dalam piksel agar tidak dibuang sebagai noise.',
      guide: 'Membantu membersihkan partikel debu atau serangga kecil yang tertangkap kamera.'
    },
    minimumConsecutiveFrames: {
      text: 'Jumlah frame berturut-turut minimal untuk mengonfirmasi jejak baru.',
      guide: 'Default 1. Meningkatkan nilai ini mencegah deteksi berkedip (false positive) menjadi jejak.'
    },
    minimumTrackAgeFrames: {
      text: 'Jumlah frame minimal objek harus terlacak sebelum event sekali diambil.',
      guide: 'Mencegah event terpicu dari deteksi sesaat (flicker) yang belum terkonfirmasi stabil.'
    },
    model: {
      text: 'Nama arsitektur model vision / AI yang dipanggil.',
      guide: 'Contoh: gpt-4o-mini, gpt-4o, google/gemini-2.0-flash-001, atau qwen/qwen-2.5-vl-72b-instruct.'
    },
    objectPrompt: {
      text: 'Daftar kata kunci kelas target objek yang dilacak oleh VLM.',
      guide: 'Pisahkan dengan koma, contoh: tire, worker, forklift, truck.'
    },
    ocSortDeltaT: {
      text: 'Langkah jeda waktu pengamatan arah momentum pada OC-SORT.',
      guide: 'Default 3. Membantu memprediksi arah gerak objek saat berbelok tajam.'
    },
    ocSortDetectionThreshold: {
      text: 'Ambang batas akurasi deteksi awal sebelum diproses oleh OC-SORT.',
      guide: 'Default 0.45.'
    },
    ocSortInertia: {
      text: 'Bobot inersia momentum pergerakan pada kalkulasi filter arah OC-SORT.',
      guide: 'Default 0.2.'
    },
    ocSortIouThreshold: {
      text: 'Ambang batas tumpang tindih asosiasi IoU pada OC-SORT.',
      guide: 'Default 0.3.'
    },
    ocSortMaxAge: {
      text: 'Jumlah frame maksimal jejak dipertahankan saat objek tertutup rintangan (occlusion).',
      guide: 'Default 90 frame (sekitar 3 detik pada 30 FPS) sebelum jejak dinyatakan hilang.'
    },
    ocSortMinHits: {
      text: 'Jumlah deteksi sukses berturut-turut sebelum jejak dianggap valid dan terkonfirmasi.',
      guide: 'Default 1 frame.'
    },
    onError: {
      text: 'Tindakan saat script Python mengalami kesalahan / error.',
      guide: 'stop: Hentikan alur workflow. pass: Abaikan error dan teruskan frame asli tanpa modifikasi.'
    },
    opticalFlowEnabled: {
      text: 'Aktifkan pelacakan pergerakan mulus berbasis Lucas-Kanade Optical Flow.',
      guide: 'Menghasilkan tracking real-time 30+ FPS tanpa membebani model vision di setiap frame.'
    },
    outputDirectory: {
      text: 'Lokasi folder penyimpanan file gambar di komputer server.',
      guide: 'Kosongkan untuk menyimpan di folder data/images bawaan proyek.'
    },
    outputFps: {
      text: 'Frame rate target untuk file video rekaman (0 = ikuti FPS sumber).',
      guide: 'Nilai umum: 25 atau 30 FPS.'
    },
    outputPath: {
      text: 'Alamat path file video rekaman yang dihasilkan (.mp4).',
      guide: 'Contoh: data/recordings/output_bay1.mp4.'
    },
    paddingPercent: {
      text: 'Persentase penambahan ruang batas di sekitar kotak objek yang dipotong.',
      guide: 'Contoh 0.10 (10%) memberikan konteks visual tambahan di sekeliling produk.'
    },
    passDownstreamOn: {
      text: 'Aturan penerusan data hasil AI Agent ke node hilir (Alert/Webhook/DB).',
      guide: 'decision_true: Hanya teruskan jika keputusan bernilai True. always: Teruskan semua hasil.'
    },
    periodicIntervalSeconds: {
      text: 'Interval waktu pengecekan rutin AI Agent saat menggunakan mode periodic.',
      guide: 'Contoh: 10.0 detik untuk melakukan audit kepatuhan lingkungan kerja secara berkala.'
    },
    provider: {
      text: 'Penyedia model kecerdasan buatan yang digunakan.',
      guide: 'Pilihan: openai (model resmi), openrouter (beragam model vision mutakhir), atau custom/local (Ollama/vLLM).'
    },
    queryIntervalSeconds: {
      text: 'Interval jeda waktu pengiriman frame ke VLM untuk efisiensi kuota API.',
      guide: 'Default 1.0 detik. Di antara jeda ini, pergerakan objek dilacak secara mulus oleh Optical Flow.'
    },
    resetOnClear: {
      text: 'Reset kondisi trigger once secara otomatis saat kondisi lingkungan kembali normal.',
      guide: 'Memungkinkan pemicu bekerja kembali ketika insiden baru terjadi di kemudian waktu.'
    },
    rfdetrCheckpoint: {
      text: 'File bobot model PyTorch RF-DETR kustom (.pth).',
      guide: 'Kosongkan untuk mengunduh bobot resmi bawaan secara otomatis.'
    },
    rfdetrHalfPrecision: {
      text: 'Gunakan komputasi presisi FP16 (Half Precision).',
      guide: 'Mempercepat inferensi hingga 2x pada kartu grafis NVIDIA yang mendukung Tensor Core.'
    },
    rfdetrImageSize: {
      text: 'Dimensi resolusi inferensi model RF-DETR.',
      guide: 'Nilai 0 berarti menggunakan resolusi bawaan arsitektur model.'
    },
    rfdetrModel: {
      text: 'Pilihan ukuran arsitektur model RF-DETR.',
      guide: 'Pilihan: rfdetr-nano (tercepat untuk CPU/Edge), small, medium, hingga large (akurasi maksimal).'
    },
    rfdetrOnnxClasses: {
      text: 'Daftar nama label kelas untuk model ONNX.',
      guide: 'Pisahkan dengan koma atau baris baru.'
    },
    rfdetrOnnxModel: {
      text: 'File model RF-DETR dalam format ONNX (.onnx).',
      guide: 'Mendukung eksekusi lintas platform menggunakan CPU OpenVINO, DirectML, atau CUDA.'
    },
    rfdetrTensorRTClasses: {
      text: 'Daftar nama kelas untuk engine TensorRT.',
      guide: 'Pisahkan dengan koma sesuai urutan output label model saat diekspor.'
    },
    rfdetrTensorRTCudaGraph: {
      text: 'Gunakan CUDA Graph untuk eksekusi TensorRT ultra-rendah overhead.',
      guide: 'Sangat efektif untuk stream frame berkecepatan tinggi dengan dimensi input tetap.'
    },
    rfdetrTensorRTEngine: {
      text: 'Lokasi file model terkompilasi TensorRT (.engine).',
      guide: 'Menghasilkan kecepatan inferensi paling kencang dengan akselerasi perangkat keras GPU NVIDIA.'
    },
    rfdetrTensorRTProcess: {
      text: 'Jalankan inferensi TensorRT di proses terpisah untuk kestabilan driver.',
      guide: 'Isolasi memori GPU agar tidak terganggu oleh operasi I/O video utama.'
    },
    samCheckpoint: {
      text: 'File bobot model Segment Anything 3 (SAM 3).',
      guide: 'Digunakan untuk segmentasi visual zero-shot berbasis konsep teks.'
    },
    sampleEvery: {
      text: 'Frekuensi penyimpanan sampel data (simpan setiap N frame).',
      guide: 'Default 1 (simpan setiap frame pemicu). Nilai 5 berarti hanya simpan 1 dari 5 frame.'
    },
    saveDebug: {
      text: 'Simpan informasi log performa teknis (FPS, waktu eksekusi) ke database.',
      guide: 'Sangat berguna saat melakukan profiling beban server di lapangan.'
    },
    saveDetections: {
      text: 'Simpan data koordinat bounding box setiap objek terdeteksi ke database SQLite.',
      guide: 'Memungkinkan query analitik historis posisi dan pergerakan objek.'
    },
    saveEvents: {
      text: 'Simpan log ringkasan setiap kejadian pemicu (event log) ke tabel events.',
      guide: 'Digunakan oleh laporan analitik insiden dan log audit operasional.'
    },
    saveFrames: {
      text: 'Simpan data frame gambar utuh dalam bentuk binary blob ke dalam database.',
      guide: 'Gunakan dengan hati-hati karena dapat membuat ukuran database membesar sangat cepat.'
    },
    saveVideo: {
      text: 'Rekam video hasil pemrosesan secara kontinu ke dalam file lokal.',
      guide: 'Aktifkan hanya jika Anda membutuhkan arsip rekaman video utuh di disk.'
    },
    seconds: {
      text: 'Durasi waktu penahanan sinyal logika dalam detik.',
      guide: 'Digunakan untuk debounce (mencegah kedipan) atau jeda waktu tunda (delay).'
    },
    sendWidth: {
      text: 'Lebar resolusi frame yang dikompres dan dikirim ke API VLM.',
      guide: 'Default 640 piksel untuk keseimbangan detail visual dan konsumsi kuota bandwidth.'
    },
    shape: {
      text: 'Bentuk geometri area zona ROI.',
      guide: 'Pilihan: rectangle (persegi panjang sederhana) atau polygon (bidang multi-titik fleksibel).'
    },
    showHeatmap: {
      text: 'Tampilkan visualisasi peta panas area anomali pada gambar hasil inspeksi.',
      guide: 'Membantu operator melihat secara persis di bagian mana cacat visual terdeteksi.'
    },
    showLabel: {
      text: 'Tampilkan teks nama kelas dan akurasi di atas kotak bounding box.',
      guide: 'Nonaktifkan jika Anda hanya menginginkan garis kotak tanpa teks label.'
    },
    showOpticalFlowPoints: {
      text: 'Tampilkan titik-titik fitur optik yang dilacak pada layar preview.',
      guide: 'Sangat berguna untuk kalibrasi visual dan debugging kestabilan fitur.'
    },
    showOverlay: {
      text: 'Gambarkan visualisasi area zona atau garis secara langsung pada video preview.',
      guide: 'Aktifkan agar operator dapat melihat batas area pemantauan di layar monitor.'
    },
    strength: {
      text: 'Kekuatan penajaman gambar (sharpening strength).',
      guide: 'Rentang: 0.1 s/d 5.0. Nilai ideal: 1.0 - 1.5 untuk meningkatkan kontras tepi objek.'
    },
    systemPrompt: {
      text: 'Instruksi peran dan persona dasar sistem AI Agent.',
      guide: 'Definisikan aturan baku seperti: \'Anda adalah auditor keselamatan kerja profesional...\''
    },
    taskMode: {
      text: 'Format dan fungsi tugas yang dijalankan oleh AI Agent.',
      guide: 'decision: Evaluasi ya/tidak (True/False). analysis: Ringkasan narasi insiden. structured_json: Ekstraksi data terstruktur.'
    },
    temperature: {
      text: 'Tingkat variasi dan kreativitas respon AI Agent.',
      guide: 'Rentang 0.0 (deterministik/konsisten) hingga 1.0 (kreatif). Nilai ideal audit: 0.1 - 0.2.'
    },
    textTemplate: {
      text: 'Format teks yang digambar ke dalam frame gambar.',
      guide: 'Dukung variabel seperti {detection.count}, {detection.class}, {detection.confidence}, {track.id}.'
    },
    thickness: {
      text: 'Ketebalan garis bounding box atau huruf teks dalam piksel.',
      guide: 'Rentang: 1 s/d 10 piksel. Nilai standar: 2 piksel.'
    },
    timeoutMs: {
      text: 'Batas waktu maksimal eksekusi script Python dalam milidetik.',
      guide: 'Default 500ms. Mencegah freeze atau loop tak terbatas jika script mengalami hang.'
    },
    torchCpuThreads: {
      text: 'Jumlah thread CPU yang dialokasikan khusus untuk inferensi PyTorch (0 = otomatis).',
      guide: 'Atur sesuai jumlah inti prosesor CPU server Anda untuk menghindari CPU spike 100%.'
    },
    trackIds: {
      text: 'Filter nomor ID pelacakan objek tertentu.',
      guide: 'Kosongkan untuk memproses seluruh ID objek yang terlacak.'
    },
    trackWidth: {
      text: 'Lebar resolusi frame yang digunakan oleh proses optical flow.',
      guide: 'Default 480 piksel untuk kecepatan komputasi optimal pada CPU.'
    },
    triggerMode: {
      text: 'Kondisi pemicu eksekusi AI Agent.',
      guide: 'on_event: Hanya berjalan saat ada event deteksi (hemat token). periodic: Berjalan rutin per interval detik. always: Berjalan terus menerus.'
    },
    useModelThreshold: {
      text: 'Gunakan ambang batas keputusan anomali bawaan dari file model.',
      guide: 'Jika dinonaktifkan, ambang batas ditentukan manual lewat parameter anomalyThreshold.'
    },
    userPrompt: {
      text: 'Template prompt pertanyaan yang dievaluasi oleh AI Agent.',
      guide: 'Dukung variabel dinamis seperti {{detections}}, {{event}}, {{timestamp}}, dan {{detection_count}}.'
    },
    zoneColor: {
      text: 'Warna garis pembatas area zona pemantauan.',
      guide: 'Gunakan kode warna Hex (contoh: #f59e0b untuk kuning oranye atau #22c55e untuk hijau).'
    },
    x: {
      text: 'Posisi koordinat horizontal (X) piksel dari sudut kiri atas.',
      guide: 'Menentukan posisi awal penempatan teks, area crop, atau titik ROI.'
    },
    y: {
      text: 'Posisi koordinat vertikal (Y) piksel dari sudut kiri atas.',
      guide: 'Menentukan posisi vertikal teks, area crop, atau titik ROI.'
    },
    trackerConfigVersion: {
      text: 'Versi internal konfigurasi modul pelacakan (tracker).',
      guide: 'Digunakan untuk migrasi otomatis skema parameter pelacak.'
    },
    enableClassLock: {
      text: 'Mencegah kedipan deteksi kelas (flickering) dengan mengunci kelas mayoritas sepanjang track ID.',
      guide: 'Sangat disarankan aktif terutama saat objek mengalami oklusi sebagian.'
    },
    classLockWindow: {
      text: 'Jumlah frame riwayat kelas untuk voting mayoritas label objek.',
      guide: 'Nilai default 10 frame memberikan stabilitas tinggi tanpa mengorbankan adaptabilitas.'
    },
    enableSmoothing: {
      text: 'Stabilisasi getaran bounding box objek menggunakan Exponential Moving Average (EMA).',
      guide: 'Menghaluskan kalkulasi koordinat, dwell time, dan pergerakan objek.'
    },
    smoothingAlpha: {
      text: 'Faktor kehalusan filter EMA (0.01 - 1.0).',
      guide: 'Nilai 0.7 memberikan respons cepat dengan getaran minimal. Nilai lebih rendah lebih halus namun ada lag.'
    }
  };

  const INDO_FIELD_LABELS = {
    recModelPath: 'Path Model Pengenal Teks (Rec ONNX)',
    detModelPath: 'Path Model Pendeteksi Teks (Det ONNX)',
    dictPath: 'Path Berkas Kamus Karakter CTC',
    cropFromDetections: 'Ekstraksi dari Kotak Deteksi',
    characterWhitelist: 'Filter Karakter (Whitelist)',
    emitEvents: 'Kirim Event Deteksi Teks',
    windowMinutes: 'Jendela Waktu Agregasi (Menit)',
    metricTypes: 'Jenis Metrik Analisis',
    columns: 'Kolom Data CSV',
    delimiter: 'Karakter Pemisah CSV',
    outputFilePath: 'Lokasi Simpan Berkas CSV',
    endpointUrl: 'Endpoint URL S3 / MinIO',
    bucketName: 'Nama Bucket S3 Cloud',
    objectPrefix: 'Prefix Folder Penyimpanan',
    credentialsSecretRef: 'Referensi Kredensial Akses',
    imageQuality: 'Kualitas Kompresi Foto (0-100)',
    channel: 'Saluran Notifikasi Peringatan',
    destinationId: 'ID / Alamat Tujuan Pengiriman',
    botToken: 'Token Autentikasi Bot',
    messageTemplate: 'Format Template Pesan',
    attachImage: 'Sertakan Foto Tangkapan Layar',
    cameraIp: 'Alamat IP Kamera PTZ',
    onvifPort: 'Port Layanan ONVIF PTZ',
    targetTrackId: 'Target Kunci Track ID Tertentu',
    deadzonePercent: 'Toleransi Area Tengah (Deadzone %)',
    panSpeed: 'Kecepatan Gerak Pan Horizontal',
    tiltSpeed: 'Kecepatan Gerak Tilt Vertikal',
    modelAName: 'Nama Model AI A',
    modelBName: 'Nama Model AI B',
    renderMode: 'Mode Visualisasi Evaluasi',
    iouThreshold: 'Ambang Batas Kesamaan IoU',
    showStatsHeader: 'Tampilkan Header Statistik',
    matchIoU: 'Ambang Batas Pencocokan IoU',
    filterClasses: 'Filter Kelas Tertentu',
    triggerSnapshot: 'Ambil Snapshot Baseline Baru',
    alarmOnDifference: 'Picu Alarm Saat Ada Perubahan',
    historyLen: 'Panjang Jejak Ekor (Frames)',
    fadeAlpha: 'Efek Transparansi Gradasi',
    bracketLength: 'Panjang Siku Sudut (Piksel)',
    glow: 'Efek Pijar Halo Modern',
    parentClass: 'Kelas Induk (Parent Class)',
    childClass: 'Kelas Anak (Child Class)',
    minOverlapRatio: 'Rasio Minimal Tumpang Tindih',
    parentRegion: 'Area Bagian Induk',
    triggerAlarmOnNonCompliance: 'Picu Alarm Ketidakpatuhan APD',
    deltaThreshold: 'Ambang Batas Gerakan Delta',
    targetClasses: 'Target Kelas Objek (Pisah Koma atau *)',
    alertThresholdSeconds: 'Batas Alarm Durasi (Detik, 0 = Nonaktif)',
    timerFormat: 'Format Tampilan Timer',
    showTrackId: 'Sertakan ID Objek (#ID)',
    badgePosition: 'Posisi Badge Timer',
    minDurationSeconds: 'Durasi Minimal Muncul (Detik)',
    heartbeatIntervalSeconds: 'Interval Detak Jantung (Detik)',
    minContourArea: 'Luas Kontur Minimum (Piksel)',
    evaluationField: 'Bidang Evaluasi Routing',
    cases: 'Daftar Kasus Percabangan (Nilai:Port)',
    defaultPort: 'Port Keluaran Default',
    speedLimitKmh: 'Batas Kecepatan Maksimal (km/jam)',
    speedUnit: 'Satuan Kecepatan',
    smoothingWindow: 'Jendela Peredam Kecepatan (Frames)',
    triggerAlarmOnSpeeding: 'Picu Alarm Kecepatan Berlebih',
    guidePathPoints: 'Titik Jalur Baku (Virtual Corridor)',
    maxAllowedDeviationMeters: 'Batas Maksimal Penyimpangan (Meter)',
    targetClasses: 'Target Kelas Kendaraan / Objek',
    triggerAlarmOnDeviation: 'Picu Alarm Keluar Jalur',
    recognitionModel: 'Model Ekstraksi Fitur Wajah (Re-ID)',
    similarityThreshold: 'Ambang Kemiripan Cosine (Threshold)',
    drawLandmarks: 'Gambarkan 5 Titik Landmark Wajah',
    drawFaceBox: 'Gambarkan Kotak Deteksi Wajah',
    showIdentityBadge: 'Tampilkan Badge Nama & Skor %',
    showUnknownFaces: 'Lacak & Beri ID Wajah Tak Dikenal',
    unknownPrefix: 'Awalan Nama Wajah Asing (Prefix)',
    objectAClass: 'Kelas Objek A',
    objectBClass: 'Kelas Objek B',
    measurementAxis: 'Sumbu Pengukuran Jarak',
    pixelRatio: 'Rasio Kalibrasi (Piksel per cm)',
    minDistanceThreshold: 'Batas Jarak Bahaya (cm)',
    anchorMode: 'Titik Acuan Posisi Objek',
    triggerAlarmOnProximity: 'Picu Alarm Saat Terlalu Dekat',
    alarmCooldownSeconds: 'Jeda Waktu Alarm (Detik)',
    targetClass: 'Target Kelas Inspeksi Dimensi',
    pixelPerUnit: 'Rasio Piksel per Satuan Fisik',
    unitName: 'Satuan Dimensi Fisik',
    minAllowedWidth: 'Batas Minimum Lebar',
    maxAllowedWidth: 'Batas Maksimum Lebar (0 = Bebas)',
    minAllowedHeight: 'Batas Minimum Tinggi',
    maxAllowedHeight: 'Batas Maksimum Tinggi (0 = Bebas)',
    triggerAlarmOnToleranceViolation: 'Picu Alarm Pelanggaran Toleransi',
    blurThreshold: 'Ambang Batas Skor Ketajaman (Blur)',
    checkIntervalSeconds: 'Interval Pengecekan Ketajaman (Detik)',
    maxAngleLimit: 'Batas Maksimal Sudut Rotasi (Derajat)',
    minAngleThreshold: 'Batas Sudut Minimum Rotasi (Derajat)',
    borderMode: 'Mode Batas Tepi Rotasi',
    trackerConfigVersion: 'Versi Konfigurasi Tracker',
    enableClassLock: 'Kunci Kelas Objek (Class Lock)',
    classLockWindow: 'Jendela Voting Kelas (Frames)',
    enableSmoothing: 'Stabilisasi Kotak Objek (EMA)',
    smoothingAlpha: 'Faktor Kehalusan EMA',
    absenceGraceSeconds: 'Toleransi Hilang Sebelum Event Keluar (Detik)',
    aggregateHourly: 'Agregasi Rekap per Jam (Hourly)',
    alertOnCapacityExceeded: 'Beri Peringatan Jika Melebihi Kapasitas',
    alertOnExceed: 'Beri Peringatan Jika Melebihi Batas',
    algorithm: 'Algoritma Pelacakan (Tracker)',
    alpha: 'Faktor Skala Kalibrasi (Alpha)',
    anomalyThreshold: 'Ambang Batas Skor Cacat (Anomaly)',
    apiKey: 'API Key (Kunci Otentikasi)',
    asyncPreview: 'Preview Asinkron (Non-blocking)',
    autoLowLight: 'Otomatis Nyalakan di Cahaya Redup',
    autoReconnect: 'Otomatis Sambung Ulang CCTV',
    background: 'Gunakan Latar Belakang Teks',
    backgroundColor: 'Warna Latar Belakang Teks',
    baseUrl: 'URL Basis API (Base URL)',
    batchSize: 'Ukuran Batch Tulis SQLite',
    botSortCmcDownscale: 'Faktor Skala CMC BoT-SORT',
    botSortCmcMethod: 'Metode Kompensasi Kamera (CMC)',
    botSortFirstIouThreshold: 'Ambang Pencocokan Tahap Pertama',
    botSortGmc: 'Aktifkan Kompensasi Gerakan Kamera (GMC)',
    botSortSecondIouThreshold: 'Ambang Pencocokan Deteksi Lemah',
    botSortUnconfirmedIouThreshold: 'Ambang Pencocokan Track Baru',
    brightness: 'Kecerahan Gambar (Brightness)',
    burnWatermark: 'Bakar Label & Waktu ke Foto (Watermark)',
    calibrationPath: 'File Kalibrasi Kamera (.yml / .xml)',
    captureMode: 'Mode Pengambilan Gambar (Capture)',
    addTimestampWatermark: 'Sematkan Cap Waktu (Timestamp Watermark)',
    saveToDisk: 'Simpan File Arsip ke Harddisk (Save to Disk)',
    botToken: 'Token Bot Telegram (Bot Token)',
    chatId: 'ID Obrolan / Chat ID Telegram',
    messageCaption: 'Teks Keterangan / Caption Notifikasi',
    parseMode: 'Mode Format Teks (Parse Mode)',
    disableNotification: 'Kirim Senyap (Silent Notification)',
    classAgnostic: 'Pelacakan Tanpa Memandang Kelas',
    classRemap: 'Pemetaan Ulang Nama Kelas',
    classes: 'Target Kelas Objek (Classes)',
    clipDurationSeconds: 'Durasi Rekaman Klip Video (Detik)',
    clipLimit: 'Batas Kontras CLAHE (Clip Limit)',
    code: 'Kode Python process(frame, state)',
    color: 'Warna Garis / Kotak (Hex/RGB)',
    concepts: 'Target Konsep Objek SAM 3',
    confirmationSeconds: 'Durasi Konfirmasi Aktivitas (Detik)',
    contextPaddingPercent: 'Bantalan Konteks Tambahan (%)',
    contrast: 'Kontras Gambar (Contrast)',
    convnextCheckpoint: 'File Bobot Model ConvNeXt',
    convnextClasses: 'Daftar Kelas Model ConvNeXt',
    convnextHalfPrecision: 'Presisi Setengah FP16 ConvNeXt',
    convnextImageSize: 'Dimensi Input ConvNeXt (px)',
    convnextModel: 'Arsitektur Model ConvNeXt',
    cooldownSeconds: 'Jeda Waktu Pendinginan (Cooldown Detik)',
    count: 'Jumlah Objek Target (Count)',
    countFromStart: 'Hitung Durasi dari Awal Aktivitas',
    countMode: 'Mode Hitungan Garis',
    countOncePerTrack: 'Hanya Hitung Sekali per Objek Terlacak',
    cropFromDetections: 'Pindai Kode dari Hasil Potongan Objek',
    cropGridColumns: 'Jumlah Kolom Grid Potongan Objek',
    cropGridGap: 'Jarak Spasi Antar Potongan (px)',
    cropGridMaxItems: 'Maksimal Tampilan Potongan Objek',
    crossingDirection: 'Arah Perlintasan Garis / Zona',
    customClasses: 'Daftar Kelas Model Kustom',
    customHeaders: 'Header HTTP Tambahan (JSON/Header)',
    customModelPath: 'Path File Model Kustom (.pt / .onnx)',
    roboflowApiKey: 'Roboflow API Key (Private)',
    dahengExposureUs: 'Waktu Eksposur Daheng (µs)',
    dahengFrameRate: 'Target Frame Rate Daheng (FPS)',
    dahengGain: 'Penguatan Sinyal Daheng (Gain dB)',
    dahengIdentifier: 'Nomor Seri / ID Daheng',
    dahengOpenMode: 'Metode Buka Kamera Daheng',
    dahengTimeoutMs: 'Batas Waktu Kamera Daheng (ms)',
    databasePath: 'Lokasi File Database SQLite (.db)',
    detectEveryNFrames: 'Jeda Inferensi (Setiap N Frame)',
    detectFreeze: 'Deteksi Kamera Macet / Freeze',
    detectShadows: 'Deteksi Bayangan Latar Belakang',
    detectTamper: 'Deteksi Sabotase / Kamera Tertutup',
    device: 'Perangkat Komputasi (Device)',
    direction: 'Arah Perhitungan Objek',
    dropFrames: 'Buang Frame Tertunda (Cegah Lag)',
    efficientadModel: 'File Model Cacat EfficientAD',
    enabledValue: 'Nilai Logika Pengaktif (True / False)',
    endPoint: 'Titik Akhir Garis (X, Y 0-1)',
    engine: 'Mesin Inferensi AI (Engine)',
    eventObjectsOnly: 'Hanya Simpan Objek Pemicu Event',
    excludeBorderMargin: 'Abaikan Margin Tepi Layar (Pixel)',
    perClassConfidence: 'Akurasi Spesifik per Kelas (Per-Class Confidence)',
    defaultConfidence: 'Akurasi Minimal Default',
    paddingPercent: 'Ekspansi Bounding Box Padding (%)',
    paddingMode: 'Mode Padding Kotak',
    filePath: 'Lokasi File Video / Gambar Lokal',
    filenameTemplate: 'Pola Penamaan File Gambar',
    fillOpacity: 'Transparansi Isi Kotak (Fill)',
    flip: 'Balik Arah Gambar (Flip)',
    flushIntervalMs: 'Interval Tulis ke Disk (ms)',
    fontScale: 'Skala Ukuran Huruf (Font Scale)',
    format: 'Format File Gambar (JPG/PNG/WebP)',
    frameQueueSize: 'Ukuran Antrean Buffer Frame',
    freezeThresholdSeconds: 'Batas Waktu Macet (Detik)',
    heatmapOpacity: 'Transparansi Peta Panas (Heatmap)',
    height: 'Tinggi Resolusi (Height px)',
    history: 'Jumlah Frame Memori Latar Belakang',
    historySeconds: 'Jeda Riwayat Cache Pelacakan (Detik)',
    holdLastEvent: 'Tahan Tampilan Event Terakhir di Preview',
    imageMaxDimension: 'Resolusi Maksimal Gambar (px)',
    imageQuality: 'Kualitas Gambar JPEG (%)',
    imgsz: 'Dimensi Input Model (Image Size)',
    inLabel: 'Teks Label Masuk (IN)',
    includeImage: 'Sertakan Gambar Frame Visual',
    insideBbox: 'Sensor Hanya di Dalam Kotak Objek',
    interpolation: 'Metode Interpolasi Skala Gambar',
    invertDirection: 'Balik Arah IN / OUT',
    invertZone: 'Zona Luar / Terbalik (Invert)',
    iouThreshold: 'Ambang Batas Tumpang Tindih (IoU)',
    jpegQuality: 'Kualitas Kompresi JPEG (%)',
    jsonSchema: 'Format Validasi Skema JSON',
    kernel: 'Ukuran Kernel Filter (Ganjil)',
    kernelSize: 'Ukuran Kernel Sensor (Ganjil)',
    labelTemplate: 'Pola Format Teks Label Objek',
    layers: 'Lapisan Visual Anotasi (Layers)',
    lineColor: 'Warna Garis Counter',
    lineWidth: 'Ketebalan Garis (Pixel)',
    lines: 'Daftar Konfigurasi Garis Perhitungan',
    loop: 'Putar Ulang Video Otomatis',
    lowLightThreshold: 'Ambang Batas Cahaya Redup (Lux)',
    maskOpacity: 'Transparansi Masker Segmentasi',
    match: 'Kriteria Pencocokan Deteksi',
    matchThreshold: 'Ambang Pencocokan Objek',
    maxArea: 'Luas Area Maksimal (Pixel)',
    maxAspectRatio: 'Aspek Rasio Maksimal (Lebar/Tinggi)',
    maxCapacity: 'Kapasitas Maksimal Objek (0 = Tak Terbatas)',
    maxCrops: 'Maksimal Jumlah Objek Dipotong',
    maxDetectionFps: 'Batas Maksimal FPS Inferensi',
    maxFilesRetention: 'Maksimal Jumlah File Gambar Disimpan',
    maxObservationGapSeconds: 'Maksimal Jeda Observasi (Detik)',
    maxPreviewFps: 'Batas Maksimal FPS Live Preview',
    maxQueue: 'Batas Maksimal Antrean Event',
    maxSessionDurationSeconds: 'Batas Durasi Sesi (Detik, 0 = Nonaktif)',
    maxTokens: 'Batas Maksimal Token Respon AI',
    message: 'Pesan Teks Notifikasi Alarm',
    method: 'Metode Pengurangan Latar Belakang',
    metric: 'Metrik Kondisi Evaluasi (Metric)',
    minArea: 'Luas Area Minimal (Pixel)',
    minAspectRatio: 'Aspek Rasio Minimal (Lebar/Tinggi)',
    minConfidence: 'Akurasi Minimal yang Diterima',
    minCount: 'Minimal Jumlah Objek',
    minCropHeight: 'Tinggi Minimal Potongan Objek (px)',
    minCropWidth: 'Lebar Minimal Potongan Objek (px)',
    minSize: 'Ukuran Minimal Objek Valid (px)',
    minimumConfidence: 'Akurasi Minimal Pelacakan',
    minimumConsecutiveFrames: 'Minimal Frame Berturut-turut',
    minimumTrackAgeFrames: 'Minimal Umur Jejak Objek (Frame)',
    mode: 'Mode Pemrosesan Warna / Sensor',
    model: 'Nama Model AI / LLM / VLM',
    newTrackThreshold: 'Ambang Pembuatan Track Baru',
    objectPrompt: 'Target Kelas Objek VLM (Koma)',
    ocSortDeltaT: 'Jeda Langkah Waktu OC-SORT',
    ocSortDetectionThreshold: 'Ambang Deteksi Awal OC-SORT',
    ocSortInertia: 'Bobot Inersia Gerakan OC-SORT',
    ocSortIouThreshold: 'Ambang Batas Asosiasi IoU OC-SORT',
    ocSortMaxAge: 'Maksimal Umur Jejak Hilang OC-SORT',
    ocSortMinHits: 'Minimal Deteksi Sukses OC-SORT',
    onError: 'Perilaku Saat Script Error',
    operation: 'Operasi Pemrosesan (Filter)',
    operator: 'Operator Logika Pembanding',
    opticalFlowEnabled: 'Gunakan Optical Flow (Gerak Mulus)',
    outLabel: 'Teks Label Keluar (OUT)',
    outputDirectory: 'Folder Penyimpanan File Gambar',
    outputFps: 'FPS Output Rekaman Video',
    outputPath: 'Path File Output Video (.mp4)',
    overlapRatio: 'Rasio Tumpang Tindih Irisan SAHI',
    padColor: 'Warna Bantalan Area Luar',
    paddingPercent: 'Persentase Bantalan Crop (%)',
    passDownstreamOn: 'Aturan Penerusan Hasil ke Hilir',
    passWhen: 'Arah Cabang Alur (Pass When)',
    password: 'Kata Sandi RTSP / CCTV',
    payloadTemplate: 'Pola Format Payload Webhook JSON',
    perClassThresholds: 'Ambang Akurasi per Kelas Objek',
    periodicIntervalSeconds: 'Interval Audit AI Rutin (Detik)',
    personGraceSeconds: 'Toleransi Hilang Kelas Pemicu (Detik)',
    pixelateBlock: 'Ukuran Kotak Pixelate Sensor',
    points: 'Titik Koordinat Area / Poligon (Points)',
    provider: 'Penyedia Layanan API (Provider)',
    queryIntervalSeconds: 'Interval Query API VLM (Detik)',
    reconnectDelaySeconds: 'Jeda Sambung Ulang CCTV (Detik)',
    recordClip: 'Rekam Klip Video Singkat Saat Alarm',
    requiredVotes: 'Jumlah Model Sepakat (Required Votes)',
    confidenceAggregation: 'Agregasi Akurasi (Confidence)',
    boxAggregation: 'Penentuan Kotak Konsensus (Bbox)',
    classAware: 'Cocokkan Berdasarkan Kelas (Class-Aware)',
    requiredClasses: 'Kelas Wajib di Zona (Wajib Ada)',
    requiredCount: 'Jumlah Minimal Kelas Wajib',
    requiredGraceSeconds: 'Toleransi Hilang Kelas Wajib (Detik)',
    resetOnClear: 'Reset Otomatis Jika Area Bersih',
    retentionDays: 'Lama Penyimpanan Data (Hari)',
    retentionSeconds: 'Lama Memori Jejak Objek (Detik)',
    retryCount: 'Jumlah Percobaan Ulang Jika Gagal',
    rfdetrCheckpoint: 'File Bobot Model RF-DETR (.pth)',
    rfdetrHalfPrecision: 'Presisi Setengah FP16 (Cepat)',
    rfdetrImageSize: 'Resolusi Input RF-DETR (px)',
    rfdetrModel: 'Arsitektur Model RF-DETR',
    rfdetrOnnxClasses: 'Daftar Kelas RF-DETR ONNX',
    rfdetrOnnxModel: 'File Model RF-DETR ONNX (.onnx)',
    rfdetrTensorRTClasses: 'Daftar Kelas TensorRT',
    rfdetrTensorRTCudaGraph: 'Gunakan CUDA Graph TensorRT',
    rfdetrTensorRTEngine: 'File Engine TensorRT (.engine)',
    rfdetrTensorRTProcess: 'Jalankan TensorRT di Proses Terpisah',
    rotation: 'Sudut Putar & Balik Gambar',
    samCheckpoint: 'File Bobot Model SAM 3',
    sampleEvery: 'Simpan Setiap N Deteksi (Sampling)',
    saveDebug: 'Simpan Log Debug Performa',
    saveDetections: 'Simpan Data Seluruh Kotak Deteksi',
    saveEvents: 'Simpan Data Kejadian Pemicu (Event)',
    saveFrames: 'Simpan Gambar Frame Utuh ke DB',
    saveVideo: 'Simpan Rekaman Video ke File',
    seconds: 'Durasi Waktu Tahan (Detik)',
    sendImage: 'Kirimkan Lampiran Gambar Frame',
    sendWidth: 'Lebar Gambar Dikirim ke VLM (px)',
    shape: 'Bentuk Area Pemantauan (Shape)',
    showBoxes: 'Tampilkan Kotak Bounding Box',
    showCounts: 'Tampilkan Ringkasan Hitungan',
    showHeatmap: 'Tampilkan Peta Panas Anomali',
    showLabel: 'Tampilkan Teks Label di Kotak',
    showLabels: 'Tampilkan Teks Label Kelas',
    showLostTracks: 'Tampilkan Objek yang Hilang Sementara',
    showMasks: 'Tampilkan Masker Poligon Segmentasi',
    showOpticalFlowPoints: 'Tampilkan Titik Pelacakan Optik',
    showOverlay: 'Tampilkan Overlay Visual di Layar',
    showTimer: 'Tampilkan Timer Detik di Layar',
    showTrackIds: 'Tampilkan Nomor ID Pelacakan',
    showTrails: 'Tampilkan Jejak Gerakan (Trail)',
    sliceHeight: 'Tinggi Irisan Deteksi Objek Kecil',
    sliceWidth: 'Lebar Irisan Deteksi Objek Kecil',
    source: 'Nomor Indeks Kamera (USB)',
    sourceType: 'Jenis Sumber Video/Kamera',
    square: 'Bentuk Potongan Persegi (1:1)',
    startPoint: 'Titik Awal Garis (X, Y 0-1)',
    streamUrl: 'Alamat URL Stream CCTV (RTSP / HTTP)',
    strength: 'Kekuatan Ketajaman (Sharpen Strength)',
    systemPrompt: 'Prompt Sistem / Peran AI Agent',
    tamperBrightThreshold: 'Ambang Terang Sabotase (Lux)',
    tamperDarkThreshold: 'Ambang Gelap Sabotase (Lux)',
    targetFps: 'Target FPS Pemrosesan Cabang',
    taskMode: 'Mode Tugas AI Agent',
    temperature: 'Tingkat Kreativitas AI (0-1)',
    textTemplate: 'Pola Format Teks yang Ditampilkan',
    thickness: 'Ketebalan Garis / Kotak (Pixel)',
    threshold: 'Ambang Batas Akurasi (Threshold)',
    thresholdSeconds: 'Waktu Diam Maksimal (Dwell Time)',
    tileGridSize: 'Ukuran Grid CLAHE',
    timeoutMs: 'Batas Waktu Eksekusi Script (ms)',
    timeoutSeconds: 'Batas Waktu Menunggu Respon (Detik)',
    topK: 'Jumlah Prediksi Teratas Diambil',
    torchCpuThreads: 'Jumlah Thread CPU PyTorch',
    trackBuffer: 'Memori Jejak Track (Buffer Frame)',
    trackHighThreshold: 'Ambang Deteksi Tinggi (High Thresh)',
    trackIds: 'Filter Nomor ID Objek Tertentu',
    trackLowThreshold: 'Ambang Deteksi Rendah (Low Thresh)',
    trackWidth: 'Lebar Resolusi Pelacakan Optik (px)',
    trackerFrameRate: 'Skala FPS Buffer Tracking',
    transport: 'Protokol Transmisi CCTV (TCP/UDP)',
    triggerAnchor: 'Titik Acuan Objek (Anchor)',
    triggerClasses: 'Kelas Pemicu Aktivitas',
    triggerCount: 'Jumlah Minimal Kelas Pemicu',
    triggerMode: 'Metode Pemicu Panggilan AI Agent',
    url: 'Alamat URL Endpoint Webhook Tujuan',
    useClahe: 'Gunakan Night-Vision CLAHE',
    useModelThreshold: 'Gunakan Ambang Bawaan Model',
    userPrompt: 'Prompt Pengguna / Template Pertanyaan',
    username: 'Nama Pengguna RTSP / CCTV',
    value: 'Nilai Acuan Pembanding (Threshold)',
    width: 'Lebar Resolusi (Width px)',
    x: 'Posisi Horizontal X (Pixel)',
    y: 'Posisi Vertikal Y (Pixel)',
    zoneColor: 'Warna Garis / Area Zona',
    zoneName: 'Nama Zona Pemantauan',
    youtubeUrl: 'URL Video / Live Stream YouTube',
    youtubeQuality: 'Kualitas / Resolusi Stream',
  };


  // --- Projects Rendering & Management ---
  function renderProjects() {
    const root = $('#projects');
    if (!root) return;
    root.replaceChildren();
    if (!state.projects.length) {
      root.textContent = 'No projects yet';
      return;
    }
    state.projects.forEach(p => {
      const b = document.createElement('div');
      b.className = `project-item${state.project?.id === p.id ? ' active' : ''}`;

      const labelWrap = document.createElement('div');
      labelWrap.className = 'proj-label';
      labelWrap.innerHTML = '<span class="project-dot"></span>';
      const label = document.createElement('span');
      label.textContent = p.name || 'Untitled project';
      labelWrap.append(label);
      labelWrap.onclick = () => switchProject(p.id);

      const delBtn = document.createElement('button');
      delBtn.className = 'delete-proj';
      delBtn.title = 'Delete project';
      delBtn.innerHTML = '<svg class="icon-svg icon-sm" viewBox="0 0 24 24"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>';
      delBtn.onclick = (e) => {
        e.stopPropagation();
        deleteProject(p.id, p.name || 'Untitled project');
      };

      b.append(labelWrap, delBtn);
      root.append(b);
    });
  }

  function openProjectRenameModal(projectId, currentName) {
    const modal = $('#projectRenameModal');
    if (!modal) return;
    $('#renameProjectId').value = projectId;
    const input = $('#renameProjectInput');
    input.value = currentName || '';
    modal.showModal();
    setTimeout(() => { input.focus(); input.select(); }, 50);
  }

  function closeProjectRenameModal() {
    const modal = $('#projectRenameModal');
    if (modal) modal.close();
  }

  function openProjectDeleteModal(projectId, currentName) {
    const modal = $('#projectDeleteModal');
    if (!modal) return;
    $('#deleteProjectIdTarget').value = projectId;
    $('#deleteProjectNameTarget').textContent = `"${currentName || 'Untitled'}"`;
    modal.showModal();
  }

  function closeProjectDeleteModal() {
    const modal = $('#projectDeleteModal');
    if (modal) modal.close();
  }

  async function renameProject() {
    if (!state.project) return;
    openProjectRenameModal(state.project.id, state.project.name);
  }

  async function deleteProject(id, name) {
    openProjectDeleteModal(id, name);
  }

  function showProjectContextMenu(anchorBtn, project) {
    document.querySelectorAll('.hub-project-dropdown-menu').forEach(el => el.remove());

    const menu = document.createElement('div');
    menu.className = 'hub-project-dropdown-menu';
    menu.innerHTML = `
      <button class="hub-dropdown-item open-opt" type="button">
        <svg class="icon-svg icon-xs" viewBox="0 0 24 24"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/><polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/></svg>
        <span>Buka alur kerja (Open)</span>
      </button>
      <button class="hub-dropdown-item rename-opt" type="button">
        <svg class="icon-svg icon-xs" viewBox="0 0 24 24"><path d="M17 3a2.85 2.83 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5Z"/><path d="m15 5 4 4"/></svg>
        <span>Ubah nama (Edit)</span>
      </button>
      <div class="hub-dropdown-divider"></div>
      <button class="hub-dropdown-item delete-opt danger" type="button">
        <svg class="icon-svg icon-xs" viewBox="0 0 24 24"><path d="M3 6h18"/><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"/><path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"/><line x1="10" y1="11" x2="10" y2="17"/><line x1="14" y1="11" x2="14" y2="17"/></svg>
        <span>Hapus proyek (Delete)</span>
      </button>
    `;

    menu.querySelector('.open-opt').onclick = (e) => {
      e.stopPropagation();
      menu.remove();
      openProjectWorkflow(project.id);
    };

    menu.querySelector('.rename-opt').onclick = (e) => {
      e.stopPropagation();
      menu.remove();
      openProjectRenameModal(project.id, project.name);
    };

    menu.querySelector('.delete-opt').onclick = (e) => {
      e.stopPropagation();
      menu.remove();
      openProjectDeleteModal(project.id, project.name);
    };

    document.body.appendChild(menu);

    const rect = anchorBtn.getBoundingClientRect();
    const menuWidth = 190;
    let left = rect.right - menuWidth;
    if (left < 10) left = rect.left;
    let top = rect.bottom + 6;
    if (top + 130 > window.innerHeight) {
      top = Math.max(10, rect.top - 130);
    }
    menu.style.left = `${left + window.scrollX}px`;
    menu.style.top = `${top + window.scrollY}px`;

    const closeHandler = (evt) => {
      if (!menu.contains(evt.target) && evt.target !== anchorBtn) {
        menu.remove();
        document.removeEventListener('click', closeHandler);
        document.removeEventListener('keydown', escHandler);
      }
    };
    const escHandler = (evt) => {
      if (evt.key === 'Escape') {
        menu.remove();
        document.removeEventListener('click', closeHandler);
        document.removeEventListener('keydown', escHandler);
      }
    };
    setTimeout(() => {
      document.addEventListener('click', closeHandler);
      document.addEventListener('keydown', escHandler);
    }, 10);
  }

  function escapeHtml(str) {
    if (str === null || str === undefined) return '';
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  }

  async function loadProjects(autoOpen = false) {
    try {
      const data = await api('/api/projects');
      state.projects = data.projects || [];
      if (!state.projects.length) {
        const created = await api('/api/projects', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ name: 'Integration', workflow: { nodes: [], edges: [] } })
        });
        state.projects = [created.project];
      }
      if (autoOpen && !state.project && state.projects[0]) {
        await switchProject(state.projects[0].id, true);
      }
      renderProjects();
      renderProjectsHub();
      renderProjectSwitcherList($('#projectSwitcherSearch')?.value || '');
    } catch (e) {
      toast('Failed to load projects: ' + e.message, true);
    }
  }

  function renderProjectSwitcherList(filterText = '') {
    const listEl = $('#projectSwitcherList');
    const countEl = $('#projectSwitcherCount');
    if (!listEl) return;

    listEl.replaceChildren();
    const query = (filterText || '').trim().toLowerCase();
    const projects = (state.projects || []).filter(p => {
      if (!query) return true;
      return (p.name || '').toLowerCase().includes(query) || (p.id || '').toLowerCase().includes(query);
    });

    if (countEl) {
      countEl.textContent = `${projects.length} proyek`;
    }

    if (!projects.length) {
      const empty = document.createElement('div');
      empty.className = 'project-switcher-empty';
      empty.textContent = query ? 'Tidak ada proyek yang cocok' : 'Belum ada proyek';
      listEl.appendChild(empty);
      return;
    }

    projects.forEach(p => {
      const isCurrent = (state.project && state.project.id === p.id);
      const item = document.createElement('div');
      item.className = 'project-switcher-item' + (isCurrent ? ' is-active' : '');
      item.setAttribute('role', 'button');
      item.setAttribute('tabindex', '0');
      item.dataset.projectId = p.id;

      const mtime = p.modified_at ? new Date(p.modified_at).toLocaleDateString('id-ID', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' }) : 'Tersimpan';

      item.innerHTML = `
        <div class="project-switcher-item-icon">
          <svg class="icon-svg icon-sm" viewBox="0 0 24 24"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/></svg>
        </div>
        <div class="project-switcher-item-info">
          <div class="project-switcher-item-name" title="${escapeHtml(p.name || 'Untitled')}">${escapeHtml(p.name || 'Untitled')}</div>
          <div class="project-switcher-item-meta">Diperbarui ${mtime}</div>
        </div>
        ${isCurrent ? '<span class="project-switcher-item-badge">Aktif</span>' : ''}
      `;

      item.addEventListener('click', async (e) => {
        e.stopPropagation();
        closeProjectSwitcherDropdown();
        if (isCurrent) {
          switchMainView('studio');
          return;
        }
        await openProjectWorkflow(p.id);
        toast(`Berpindah ke proyek: ${p.name || 'Untitled'}`);
      });

      item.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          item.click();
        }
      });

      listEl.appendChild(item);
    });
  }

  function toggleProjectSwitcherDropdown(forceOpen) {
    const dropdown = $('#projectSwitcherDropdown');
    const btn = $('#projectSwitcherBtn');
    if (!dropdown || !btn) return;

    const willOpen = (typeof forceOpen === 'boolean') ? forceOpen : dropdown.hidden;
    dropdown.hidden = !willOpen;
    btn.setAttribute('aria-expanded', willOpen ? 'true' : 'false');

    if (willOpen) {
      const searchInput = $('#projectSwitcherSearch');
      if (searchInput) {
        searchInput.value = '';
        setTimeout(() => searchInput.focus(), 60);
      }
      renderProjectSwitcherList('');
    }
  }

  function closeProjectSwitcherDropdown() {
    toggleProjectSwitcherDropdown(false);
  }

  function initProjectSwitcher() {
    const btn = $('#projectSwitcherBtn');
    const dropdown = $('#projectSwitcherDropdown');
    const searchInput = $('#projectSwitcherSearch');
    const newBtn = $('#projectSwitcherNewBtn');
    const hubBtn = $('#projectSwitcherHubBtn');

    if (btn) {
      btn.addEventListener('click', (e) => {
        e.stopPropagation();
        toggleProjectSwitcherDropdown();
      });
    }

    if (dropdown) {
      dropdown.addEventListener('click', (e) => {
        e.stopPropagation();
      });
    }

    if (searchInput) {
      searchInput.addEventListener('input', (e) => {
        renderProjectSwitcherList(e.target.value);
      });
      searchInput.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
          closeProjectSwitcherDropdown();
        }
      });
    }

    if (newBtn) {
      newBtn.addEventListener('click', () => {
        closeProjectSwitcherDropdown();
        newProject();
      });
    }

    if (hubBtn) {
      hubBtn.addEventListener('click', () => {
        closeProjectSwitcherDropdown();
        switchMainView('projectsHub');
      });
    }

    document.addEventListener('click', (e) => {
      const wrap = $('#projectSwitcherWrap');
      if (wrap && !wrap.contains(e.target)) {
        closeProjectSwitcherDropdown();
      }
    });

    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') {
        closeProjectSwitcherDropdown();
      }
    });
  }

  function renderProjectsHub() {
    // 1. Update Quick Overview Stats
    const statProjects = $('#hubStatProjectsCount');
    const statTemplates = $('#hubStatTemplatesCount');
    const statCameras = $('#hubStatCamerasCount');
    const statNodes = $('#hubStatNodesCount');

    if (statProjects) statProjects.textContent = (state.projects || []).length;
    if (statTemplates) statTemplates.textContent = (state.templates || []).length ? `${state.templates.length}+` : '24+';
    if (statCameras) statCameras.textContent = '8';
    if (statNodes) statNodes.textContent = '27+';

    // 2. Render Projects Grid with Filter
    const projGrid = $('#hubRecentProjectsGrid');
    if (projGrid) {
      projGrid.replaceChildren();
      const projQuery = ($('#hubProjectFilterInput')?.value || '').trim().toLowerCase();
      const allProjects = state.projects || [];
      const filteredProjects = allProjects.filter(p => {
        if (!projQuery) return true;
        return (p.name || '').toLowerCase().includes(projQuery) || (p.id || '').toLowerCase().includes(projQuery);
      });

      if (!filteredProjects.length) {
        projGrid.innerHTML = `
          <div class="empty-hint" style="grid-column: 1 / -1; padding: 36px 20px; text-align: center; color: #64748b; background: #ffffff; border: 1px dashed #cbd5e1; border-radius: 12px;">
            <svg class="icon-svg icon-lg" style="margin-bottom: 8px; color: #94a3b8;" viewBox="0 0 24 24"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/></svg>
            <div style="font-weight: 600; color: #1e293b; font-size: 14px;">${projQuery ? 'Tidak ada proyek yang sesuai pencarian' : 'Belum ada proyek tersimpan'}</div>
            <div style="font-size: 12px; margin-top: 4px;">${projQuery ? 'Coba gunakan kata kunci nama proyek lain.' : 'Buat proyek baru atau pilih salah satu template di bawah untuk memulai!'}</div>
          </div>
        `;
      } else {
        filteredProjects.forEach(p => {
          const card = document.createElement('div');
          card.className = 'hub-project-card';

          const mtime = p.modified_at ? new Date(p.modified_at).toLocaleString('id-ID', { month: 'short', day: 'numeric', year: 'numeric', hour: '2-digit', minute: '2-digit' }) : 'Baru disimpan';

          card.innerHTML = `
            <div class="hub-project-top">
              <div class="hub-project-icon">
                <svg class="icon-svg icon-md" viewBox="0 0 24 24"><circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/><line x1="8.59" y1="13.51" x2="15.42" y2="17.49"/><line x1="15.41" y1="6.51" x2="8.59" y2="10.49"/></svg>
              </div>
              <div class="hub-project-info">
                <h3 class="hub-project-title" title="${escapeHtml(p.name)}">${escapeHtml(p.name || 'Untitled project')}</h3>
                <div class="hub-project-meta">Diperbarui: ${mtime}</div>
              </div>
              <button class="hub-card-menu-btn" title="Opsi Proyek" type="button">
                <svg class="icon-svg icon-sm" viewBox="0 0 24 24"><circle cx="12" cy="12" r="1"/><circle cx="19" cy="12" r="1"/><circle cx="5" cy="12" r="1"/></svg>
              </button>
            </div>
            <div class="hub-project-foot">
              <button class="hub-open-workflow-btn" type="button">
                <span>Buka Workflow &rarr;</span>
              </button>
            </div>
          `;

          card.querySelector('.hub-open-workflow-btn').onclick = () => openProjectWorkflow(p.id);
          card.querySelector('.hub-project-title').onclick = () => openProjectWorkflow(p.id);
          card.querySelector('.hub-card-menu-btn').onclick = (e) => {
            e.stopPropagation();
            showProjectContextMenu(e.currentTarget, p);
          };

          projGrid.append(card);
        });
      }
    }

    // 3. Render Templates Grid with Category & Search Filters
    const tplGrid = $('#hubTemplatesGrid');
    if (tplGrid) {
      tplGrid.replaceChildren();
      const allTemplates = state.templates || [];
      const activeCat = state.activeTemplateCategory || 'all';
      document.querySelectorAll('.hub-cat-pill').forEach(p => {
        p.classList.toggle('active', (p.dataset.category || 'all') === activeCat);
      });
      const tplQuery = ($('#hubTemplateSearchInput')?.value || '').trim().toLowerCase();

      const filteredTemplates = allTemplates.filter(t => {
        // Category check
        if (activeCat !== 'all') {
          const badgeStr = (t.badge || '').toLowerCase();
          const tagsStr = (t.tags || []).join(' ').toLowerCase();
          const catLower = activeCat.toLowerCase();
          const matchCat = badgeStr.includes(catLower) || tagsStr.includes(catLower);
          if (!matchCat) return false;
        }

        // Search text check
        if (tplQuery) {
          const combined = `${t.name} ${t.description} ${t.purpose || ''} ${(t.tags || []).join(' ')} ${t.badge || ''}`.toLowerCase();
          if (!combined.includes(tplQuery)) return false;
        }

        return true;
      });

      if (!filteredTemplates.length) {
        tplGrid.innerHTML = `
          <div class="empty-hint" style="grid-column: 1 / -1; padding: 40px 20px; text-align: center; color: #64748b; background: #ffffff; border: 1px dashed #cbd5e1; border-radius: 12px;">
            <svg class="icon-svg icon-lg" style="margin-bottom: 8px; color: #94a3b8;" viewBox="0 0 24 24"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
            <div style="font-weight: 600; color: #1e293b; font-size: 14.5px;">Tidak ada template yang cocok</div>
            <div style="font-size: 12.5px; margin-top: 4px;">Coba pilih kategori lain di atas atau bersihkan kata kunci pencarian.</div>
            <button class="button secondary" style="margin-top: 14px;" type="button" id="resetTemplateFilterBtn">Tampilkan Semua Solusi</button>
          </div>
        `;
        $('#resetTemplateFilterBtn')?.addEventListener('click', () => {
          state.activeTemplateCategory = 'all';
          const pills = document.querySelectorAll('.hub-cat-pill');
          pills.forEach(p => p.classList.toggle('active', p.dataset.category === 'all'));
          const searchInp = $('#hubTemplateSearchInput');
          if (searchInp) searchInp.value = '';
          renderProjectsHub();
        });
      } else {
        filteredTemplates.forEach(t => {
          const card = document.createElement('div');
          card.className = 'hub-template-card';

          const badgeText = t.badge || 'AI Vision';
          const tagsHtml = (t.tags || [badgeText]).map(tg => `<span class="hub-tag-badge">${escapeHtml(tg)}</span>`).join(' ');
          const modelMeta = t.modelSize || 'Includes pre-trained weights';
          const purposeText = t.purpose || t.description || 'Solusi computer vision siap pakai untuk analitik video otomatis.';

          // Color accents based on badge
          let badgeThemeClass = 'badge-blue';
          if (badgeText.includes('Manufaktur') || badgeText.includes('QC') || badgeText.includes('Zero')) badgeThemeClass = 'badge-amber';
          else if (badgeText.includes('Retail') || badgeText.includes('Publik') || badgeText.includes('Restoran')) badgeThemeClass = 'badge-emerald';
          else if (badgeText.includes('Keamanan') || badgeText.includes('Privasi') || badgeText.includes('Akses')) badgeThemeClass = 'badge-indigo';
          else if (badgeText.includes('Gudang') || badgeText.includes('Logistik')) badgeThemeClass = 'badge-cyan';
          else if (badgeText.includes('Agent') || badgeText.includes('VLM')) badgeThemeClass = 'badge-purple';

          // Decorative SVG graphics per template
          let bannerGraphic = `
            <g stroke="#38bdf8" stroke-width="1.5" fill="none" opacity="0.6">
              <rect x="30" y="25" width="60" height="90" rx="6" stroke-dasharray="4 2"/>
              <line x1="60" y1="20" x2="60" y2="120" stroke="#22c55e" stroke-width="2"/>
              <rect x="110" y="25" width="60" height="90" rx="6" stroke="#22c55e"/>
              <line x1="140" y1="20" x2="140" y2="120" stroke="#22c55e" stroke-width="2"/>
              <rect x="190" y="35" width="60" height="80" rx="6" stroke="#ef4444"/>
              <line x1="220" y1="20" x2="220" y2="120" stroke="#ef4444" stroke-width="2"/>
              <rect x="270" y="25" width="60" height="90" rx="6" stroke-dasharray="4 2"/>
              <line x1="300" y1="20" x2="300" y2="120" stroke="#22c55e" stroke-width="2"/>
            </g>
          `;

          if (t.id === 'traffic_flow_counter') {
            bannerGraphic = `
              <g opacity="0.95">
                <rect x="25" y="15" width="145" height="110" rx="8" stroke="#38bdf8" stroke-width="1.5" stroke-dasharray="4 2" fill="#0284c718"/>
                <text x="35" y="35" fill="#38bdf8" font-size="11" font-weight="700">LAJUR 01 (UTARA)</text>
                <text x="35" y="55" fill="#bae6fd" font-size="16" font-weight="800">42 KENDARAAN</text>
                <text x="35" y="75" fill="#94a3b8" font-size="10">Mobil: 28 • Motor: 14</text>
                <rect x="35" y="90" width="70" height="20" rx="4" fill="#22c55e33" stroke="#22c55e"/>
                <text x="43" y="104" fill="#86efac" font-size="10" font-weight="700">LANCAR</text>

                <rect x="190" y="15" width="145" height="110" rx="8" stroke="#f59e0b" stroke-width="1.5" stroke-dasharray="4 2" fill="#d9770618"/>
                <text x="200" y="35" fill="#f59e0b" font-size="11" font-weight="700">LAJUR 02 (SELATAN)</text>
                <text x="200" y="55" fill="#fde68a" font-size="16" font-weight="800">78 KENDARAAN</text>
                <text x="200" y="75" fill="#94a3b8" font-size="10">Truk: 12 • Bus: 8 • Mobil: 58</text>
                <rect x="200" y="90" width="70" height="20" rx="4" fill="#ef444433" stroke="#ef4444"/>
                <text x="212" y="104" fill="#fca5a5" font-size="10" font-weight="700">PADAT ⚠</text>
              </g>
            `;
          } else if (t.id === 'assembly_workshop_cycle_timer') {
            bannerGraphic = `
              <g opacity="0.95">
                <rect x="30" y="22" width="140" height="96" rx="8" stroke="#22c55e" stroke-width="2" fill="#22c55e1a"/>
                <circle cx="48" cy="42" r="5" fill="#22c55e"/>
                <text x="60" y="46" fill="#86efac" font-size="11" font-weight="700">STASIUN 01 • ACTIVE</text>
                <text x="48" y="72" fill="#ffffff" font-size="18" font-weight="800">04m : 18s</text>
                <text x="48" y="95" fill="#94a3b8" font-size="10">Target Cycle: 05:00</text>

                <rect x="190" y="22" width="140" height="96" rx="8" stroke="#ef4444" stroke-width="1.5" stroke-dasharray="4 2" fill="#ef44441a"/>
                <circle cx="208" cy="42" r="5" fill="#ef4444"/>
                <text x="220" y="46" fill="#fca5a5" font-size="11" font-weight="700">STASIUN 02 • IDLE</text>
                <text x="208" y="72" fill="#f87171" font-size="18" font-weight="800">01m : 42s ⚠</text>
                <text x="208" y="95" fill="#94a3b8" font-size="10">Status: Tidak Terisi</text>
              </g>
            `;
          } else if (t.id === 'warehouse_forklift_safety_guard') {
            bannerGraphic = `
              <g opacity="0.95">
                <rect x="30" y="20" width="140" height="100" rx="8" stroke="#eab308" stroke-width="2" fill="#eab3081a"/>
                <text x="45" y="42" fill="#fde047" font-size="11" font-weight="800">DOCK 01 • LOADING</text>
                <text x="45" y="68" fill="#ffffff" font-size="16" font-weight="800">TRUK IN: 28m</text>
                <rect x="45" y="82" width="110" height="24" rx="4" fill="#0284c733" stroke="#38bdf8"/>
                <text x="53" y="98" fill="#7dd3fc" font-size="10" font-weight="700">GERBANG TERBUKA</text>

                <rect x="190" y="20" width="140" height="100" rx="8" stroke="#ef4444" stroke-width="2" fill="#ef444426"/>
                <text x="202" y="42" fill="#fca5a5" font-size="11" font-weight="800">FORKLIFT ZONE ⚠</text>
                <text x="202" y="68" fill="#ef4444" font-size="15" font-weight="800">PROXIMITY ALERT</text>
                <rect x="202" y="82" width="115" height="24" rx="4" fill="#ef444444" stroke="#f87171"/>
                <text x="210" y="98" fill="#fecaca" font-size="10" font-weight="700">JARAK AMAN: &lt; 2.5m</text>
              </g>
            `;
          } else if (t.id === 'retail_checkout_queue_monitor') {
            bannerGraphic = `
              <g opacity="0.95">
                <rect x="30" y="22" width="140" height="96" rx="8" stroke="#ef4444" stroke-width="2" fill="#ef444422"/>
                <text x="45" y="45" fill="#fca5a5" font-size="11" font-weight="800">KASIR 01 (UTAMA)</text>
                <text x="45" y="75" fill="#f87171" font-size="20" font-weight="900">4 ORANG ⚠</text>
                <text x="45" y="98" fill="#fecaca" font-size="10" font-weight="700">ALERT: BUKA KASIR +1</text>

                <rect x="190" y="22" width="140" height="96" rx="8" stroke="#22c55e" stroke-width="1.5" fill="#22c55e1a"/>
                <text x="205" y="45" fill="#86efac" font-size="11" font-weight="800">KASIR 02 (EXPRESS)</text>
                <text x="205" y="75" fill="#22c55e" font-size="20" font-weight="900">1 ORANG</text>
                <text x="205" y="98" fill="#bbf7d0" font-size="10" font-weight="700">STATUS: ANTRIAN NORMAL</text>
              </g>
            `;
          } else if (t.id === 'restaurant_table_occupancy') {
            bannerGraphic = `
              <g opacity="0.95">
                <rect x="35" y="20" width="130" height="42" rx="7" stroke="#10b981" stroke-width="2" fill="#10b98126"/>
                <circle cx="50" cy="41" r="4.5" fill="#10b981"/>
                <text x="62" y="45" fill="#6ee7b7" font-size="11" font-weight="700" font-family="system-ui, sans-serif">MEJA 01 • 34m</text>
                
                <rect x="195" y="20" width="130" height="42" rx="7" stroke="#38bdf8" stroke-width="2" fill="#38bdf826"/>
                <circle cx="210" cy="41" r="4.5" fill="#38bdf8"/>
                <text x="222" y="45" fill="#bae6fd" font-size="11" font-weight="700" font-family="system-ui, sans-serif">MEJA 02 • 15m</text>
                
                <rect x="35" y="78" width="130" height="42" rx="7" stroke="#f59e0b" stroke-width="2" fill="#f59e0b26"/>
                <circle cx="50" cy="99" r="4.5" fill="#f59e0b"/>
                <text x="62" y="103" fill="#fde68a" font-size="11" font-weight="700" font-family="system-ui, sans-serif">MEJA 03 • 52m ⚠</text>
                
                <rect x="195" y="78" width="130" height="42" rx="7" stroke="#94a3b8" stroke-width="1.5" stroke-dasharray="4 2" fill="#0f172a33"/>
                <circle cx="210" cy="99" r="4.5" fill="#64748b"/>
                <text x="222" y="103" fill="#cbd5e1" font-size="11" font-weight="600" font-family="system-ui, sans-serif">MEJA 04 • KOSONG</text>
              </g>
            `;
          } else if (t.id.includes('barcode')) {
            bannerGraphic = `
              <g opacity="0.9">
                <rect x="40" y="30" width="280" height="80" rx="8" fill="#0f172a44" stroke="#0284c7" stroke-width="1.5"/>
                <line x1="60" y1="45" x2="60" y2="95" stroke="#38bdf8" stroke-width="3"/>
                <line x1="72" y1="45" x2="72" y2="95" stroke="#38bdf8" stroke-width="5"/>
                <line x1="88" y1="45" x2="88" y2="95" stroke="#38bdf8" stroke-width="2"/>
                <line x1="100" y1="45" x2="100" y2="95" stroke="#38bdf8" stroke-width="6"/>
                <line x1="120" y1="45" x2="120" y2="95" stroke="#38bdf8" stroke-width="3"/>
                <line x1="135" y1="45" x2="135" y2="95" stroke="#38bdf8" stroke-width="7"/>
                <line x1="30" y1="70" x2="330" y2="70" stroke="#ef4444" stroke-width="2" stroke-dasharray="6 3"/>
                <rect x="230" y="45" width="50" height="50" rx="4" fill="#0284c722" stroke="#38bdf8" stroke-width="2"/>
                <text x="240" y="75" fill="#38bdf8" font-size="16" font-weight="bold">QR</text>
              </g>
            `;
          }

          card.innerHTML = `
            <div class="hub-template-banner">
              <svg width="100%" height="100%" viewBox="0 0 360 140" preserveAspectRatio="none" style="opacity: 0.9;">
                <defs>
                  <linearGradient id="grad-${t.id}" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" stop-color="#0f172a" stop-opacity="0.95"/>
                    <stop offset="100%" stop-color="#1e293b" stop-opacity="0.95"/>
                  </linearGradient>
                </defs>
                <rect width="360" height="140" fill="url(#grad-${t.id})"/>
                ${bannerGraphic}
              </svg>
              <span class="hub-template-category-badge ${badgeThemeClass}">${escapeHtml(badgeText)}</span>
            </div>
            <div class="hub-template-body">
              <h3 class="hub-template-title" title="${escapeHtml(t.name)}">${escapeHtml(t.name)}</h3>
              <div class="hub-template-tags">${tagsHtml}</div>
              <!-- Purpose & Function Box -->
              <div class="hub-template-purpose-box">
                <div class="purpose-header">
                  <svg class="icon-svg icon-xs" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/></svg>
                  <span>Fungsi & Kegunaan:</span>
                </div>
                <div class="purpose-text">${escapeHtml(purposeText)}</div>
              </div>

              <p class="hub-template-desc">${escapeHtml(t.description || '')}</p>
              <div class="hub-template-foot-meta">
                <span class="meta-tag">
                  <svg class="icon-svg icon-xs" viewBox="0 0 24 24"><path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg>
                  ${escapeHtml(modelMeta)}
                </span>
              </div>
              <button class="hub-template-btn" type="button">
                <span>Gunakan Template &rarr;</span>
              </button>
            </div>
          `;

          card.querySelector('.hub-template-btn').onclick = () => useTemplate(t.id);
          tplGrid.append(card);
        });
      }
    }
  }

  function initHubEvents() {
    // Category pills filter
    const pillContainer = $('#hubCategoryPills');
    if (pillContainer) {
      pillContainer.addEventListener('click', (e) => {
        const btn = e.target.closest('.hub-cat-pill');
        if (!btn) return;
        pillContainer.querySelectorAll('.hub-cat-pill').forEach(p => p.classList.remove('active'));
        btn.classList.add('active');
        state.activeTemplateCategory = btn.dataset.category || 'all';
        renderProjectsHub();
      });
    }

    // Projects search input
    $('#hubProjectFilterInput')?.addEventListener('input', () => {
      renderProjectsHub();
    });

    // Templates search input
    $('#hubTemplateSearchInput')?.addEventListener('input', () => {
      renderProjectsHub();
    });

    // Scroll to templates section
    $('#hubBrowseTemplatesBtn')?.addEventListener('click', () => {
      const section = $('#hubTemplatesSection');
      if (section) section.scrollIntoView({ behavior: 'smooth' });
    });
  }

  async function openProjectWorkflow(id) {
    await switchProject(id, true);
    switchMainView('studio');
    switchProjectRailTab('workflow');
  }
  window.openProjectWorkflow = openProjectWorkflow;

  async function useTemplate(templateId) {
    const tpl = (state.templates || []).find(t => t.id === templateId);
    if (!tpl) return;
    try {
      const created = await api('/api/projects', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: tpl.name, workflow: tpl.workflow })
      });
      await loadProjects();
      await switchProject(created.project.id, true);
      switchMainView('studio');
      switchProjectRailTab('workflow');
      toast(`Created project from "${tpl.name}"`);
    } catch (e) {
      toast('Failed to load template: ' + e.message, true);
    }
  }

  function switchProjectRailTab(railTabName) {
    state.activeRailTab = railTabName;
    const tabWorkflow = $('#railTabWorkflow');
    const tabModels = $('#railTabModels');
    const tabFaces = $('#railTabFaces');

    if (tabWorkflow) tabWorkflow.classList.toggle('active', railTabName === 'workflow');
    if (tabModels) tabModels.classList.toggle('active', railTabName === 'models');
    if (tabFaces) tabFaces.classList.toggle('active', railTabName === 'faces');

    const appShell = $('#viewStudio .app-shell');
    const modelManager = $('#viewModelManager');
    const faceRegistry = $('#viewFaceRegistry');

    if (railTabName === 'workflow') {
      if (appShell) {
        appShell.removeAttribute('hidden');
        appShell.style.display = '';
      }
      if (modelManager) {
        modelManager.setAttribute('hidden', '');
        modelManager.style.display = 'none';
      }
      if (faceRegistry) {
        faceRegistry.setAttribute('hidden', '');
        faceRegistry.style.display = 'none';
      }
      renderCanvas();
    } else if (railTabName === 'models') {
      if (appShell) {
        appShell.setAttribute('hidden', '');
        appShell.style.display = 'none';
      }
      if (faceRegistry) {
        faceRegistry.setAttribute('hidden', '');
        faceRegistry.style.display = 'none';
      }
      if (modelManager) {
        modelManager.removeAttribute('hidden');
        modelManager.style.display = 'flex';
        renderModelsManager();
      }
    } else if (railTabName === 'faces') {
      if (appShell) {
        appShell.setAttribute('hidden', '');
        appShell.style.display = 'none';
      }
      if (modelManager) {
        modelManager.setAttribute('hidden', '');
        modelManager.style.display = 'none';
      }
      if (faceRegistry) {
        faceRegistry.removeAttribute('hidden');
        faceRegistry.style.display = 'flex';
        renderFaceRegistry();
      }
    }
  }
  window.switchProjectRailTab = switchProjectRailTab;

  async function renderModelsManager() {
    await refreshModels();
    const tbody = $('#modelsTableBody');
    const empty = $('#modelsEmptyState');
    if (!tbody) return;
    tbody.replaceChildren();

    const allModels = state.models || [];
    if (!allModels.length) {
      if (empty) empty.hidden = false;
      return;
    }
    if (empty) empty.hidden = true;

    allModels.forEach(m => {
      const tr = document.createElement('tr');

      const typeLower = (m.type || 'detection').toLowerCase();
      let typeClass = 'type-detection';
      if (typeLower.includes('seg')) typeClass = 'type-segmentation';
      else if (typeLower.includes('cls') || typeLower.includes('class')) typeClass = 'type-classification';
      else if (typeLower.includes('pose')) typeClass = 'type-pose';
      else if (typeLower.includes('inspect') || typeLower.includes('defect')) typeClass = 'type-inspection';
      else if (typeLower.includes('vlm')) typeClass = 'type-vlm';

      const sizeStr = m.sizeFormatted || (m.sizeBytes ? `${(m.sizeBytes / (1024 * 1024)).toFixed(1)} MB` : '-');
      const addedStr = m.added || 'System';
      const engineStr = m.engine || 'Ultralytics YOLO';
      const formatStr = m.format || 'pt';

      tr.innerHTML = `
        <td class="model-name-cell">
          <svg class="icon-svg icon-sm" style="color: #0284c7;" viewBox="0 0 24 24"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/></svg>
          <span title="${escapeHtml(m.path || m.name)}">${escapeHtml(m.name)}</span>
        </td>
        <td><span class="model-type-pill ${typeClass}">${escapeHtml(m.type || 'Detection')}</span></td>
        <td>${escapeHtml(m.version || 'v8.0')}</td>
        <td>${escapeHtml(sizeStr)}</td>
        <td><span class="model-status-pill"><span class="model-status-dot"></span> Ready</span></td>
        <td>${escapeHtml(addedStr)}</td>
        <td>${escapeHtml(engineStr)}</td>
        <td><span class="model-format-badge">.${escapeHtml(formatStr)}</span></td>
        <td>
          <div style="display: flex; gap: 6px;">
            <button class="button ghost icon-btn-sm btn-inspect-model" title="Inspect model classes" type="button">
              <svg class="icon-svg icon-sm" viewBox="0 0 24 24"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
            </button>
            ${m.isCustom ? `
              <button class="button ghost icon-btn-sm btn-delete-model" title="Delete custom model" type="button" style="color: #dc2626;">
                <svg class="icon-svg icon-sm" viewBox="0 0 24 24"><path d="M3 6h18"/><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"/><path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"/></svg>
              </button>
            ` : ''}
          </div>
        </td>
      `;

      tr.querySelector('.btn-inspect-model')?.addEventListener('click', async () => {
        try {
          const res = await api(`/api/models/inspect?path=${encodeURIComponent(m.path || m.name)}`);
          alert(`Model: ${res.name}\nEngine: ${res.engine}\nClasses (${res.classesCount}):\n${(res.classes || []).slice(0, 30).join(', ')}${res.classesCount > 30 ? '...' : ''}`);
        } catch (e) {
          toast('Inspect error: ' + e.message, true);
        }
      });

      tr.querySelector('.btn-delete-model')?.addEventListener('click', async () => {
        if (!confirm(`Delete custom model "${m.name}"?`)) return;
        try {
          await api(`/api/models/${encodeURIComponent(m.contentId || m.name)}`, { method: 'DELETE' });
          toast(`Model ${m.name} deleted`);
          await refreshModels();
          renderModelsManager();
          renderInspector();
        } catch (e) {
          toast('Delete failed: ' + e.message, true);
        }
      });

      tbody.append(tr);
    });
  }
  window.renderModelsManager = renderModelsManager;
  window.switchProject = switchProject;
  window.newProject = newProject;

  async function switchProject(id, force = false) {
    if (!force && state.dirty && !confirm('You have unsaved changes. Switch project anyway?')) return;
    cancelActiveZoneEditor();
    invalidatePreview();
    try {
      const data = await api(`/api/projects/${encodeURIComponent(id)}`);
      state.project = data.project;
      state.workflow = data.workflow || { nodes: [], edges: [] };
      state.selected = null;
      state.dirty = false;
      $('#dirty').hidden = true;
      $('#projectName').textContent = state.project?.name || 'Untitled project';
      renderProjects();
      renderCanvas();
      renderInspector();
      updatePreviewSelect();
      renderProjectSwitcherList($('#projectSwitcherSearch')?.value || '');
    } catch (e) {
      toast('Failed to load project: ' + e.message, true);
    }
  }

  async function newProject() {
    const name = prompt('Project name', 'New vision workflow');
    if (!name?.trim()) return;
    if (state.dirty && !confirm('You have unsaved changes. Create a project anyway?')) return;
    try {
      const data = await api('/api/projects', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: name.trim(), workflow: { nodes: [], edges: [] } })
      });
      await loadProjects();
      await switchProject(data.project.id, true);
      switchMainView('studio');
      toast('Proyek baru dengan kanvas kosong berhasil dibuat');
    } catch (e) {
      toast(e.message, true);
    }
  }

  async function save() {
    if (!state.project) return false;
    const projectId = state.project.id;
    const snapshot = JSON.stringify(state.workflow);
    $('#saveBtn').disabled = true;
    try {
      const data = await api(`/api/projects/${encodeURIComponent(projectId)}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ workflow: state.workflow })
      });
      if (state.project?.id === projectId) {
        state.project = data.project;
        state.dirty = false;
        $('#dirty').hidden = true;
      }
      await loadProjects();
      toast('Changes saved');
      return true;
    } catch (e) {
      toast(e.message, true);
      return false;
    } finally {
      $('#saveBtn').disabled = false;
    }
  }

  // --- Node Library Rendering with Vector Icons ---
  function renderLibrary() {
    const q = ($('#nodeSearch')?.value || '').toLowerCase();
    const root = $('#library');
    if (!root) return;
    root.replaceChildren();

    const catalogItems = Object.entries(state.catalog);
    const items = catalogItems.filter(([type, bp]) => {
      const cat = categoryFor(type).toLowerCase();
      const concept = (NODE_GUIDES_ID[type]?.concept || '').toLowerCase();
      const searchable = `${type} ${bp.title || ''} ${bp.subtitle || ''} ${cat} ${concept}`.toLowerCase();
      return searchable.includes(q);
    });
    const count = $('#nodeCount');
    if (count) count.textContent = q ? `${items.length}/${catalogItems.length} nodes` : `${catalogItems.length} nodes`;

    const groups = {};
    items.forEach(([type, bp]) => {
      const cat = categoryFor(type);
      (groups[cat] ||= []).push([type, bp]);
    });

    CATEGORY_ORDER.forEach(groupName => {
      const groupItems = groups[groupName];
      if (!groupItems || !groupItems.length) return;

      const h = document.createElement('div');
      h.className = 'library-group';
      const catIconKey = CATEGORY_ICONS[groupName] || 'input';
      h.innerHTML = `${getIcon(catIconKey, 'icon-sm')} <span>${groupName.toUpperCase()} (${groupItems.length})</span>`;
      root.append(h);

      groupItems.forEach(([type, bp]) => {
        const b = document.createElement('button');
        b.className = 'library-item';
        b.dataset.cat = groupName;
        b.title = bp.subtitle || '';

        const icon = document.createElement('span');
        icon.className = 'node-icon';
        icon.innerHTML = getIcon(type, 'icon-sm');

        const text = document.createElement('span');
        text.className = 'library-text';
        text.innerHTML = `<strong></strong><small></small>`;
        text.firstChild.textContent = bp.title || titleFor(type);
        text.lastChild.textContent = bp.subtitle || type;

        const infoBtn = document.createElement('span');
        infoBtn.className = 'library-info-btn';
        infoBtn.title = 'Panduan & Cara Penggunaan (Bahasa Indonesia)';
        infoBtn.innerHTML = '<svg class="icon-svg icon-sm" viewBox="0 0 24 24" style="width:13px;height:13px;"><circle cx="12" cy="12" r="10"/><path d="M12 16v-4"/><path d="M12 8h.01"/></svg>';
        infoBtn.onclick = (e) => {
          e.stopPropagation();
          showNodeGuideModal(type);
        };

        b.append(icon, text, infoBtn);
        b.onclick = () => addNode(type);
        root.append(b);
      });
    });
  }

  // --- Canvas Zoom & Rendering ---
  function setZoom(val) {
    state.zoom = Math.max(0.3, Math.min(2.0, Number(val.toFixed(2))));
    $('#zoomLevel').textContent = `${Math.round(state.zoom * 100)}%`;
    renderCanvas();
  }

  function renderCanvas() {
    const canvas = $('#canvas');
    const root = $('#nodes');
    const svg = $('#edges');
    if (!canvas || !root || !svg) return;

    root.style.transform = `scale(${state.zoom}) translate(${state.panX}px, ${state.panY}px)`;
    root.style.transformOrigin = '0 0';
    svg.style.transform = `scale(${state.zoom}) translate(${state.panX}px, ${state.panY}px)`;
    svg.style.transformOrigin = '0 0';

    root.replaceChildren();
    $('#emptyCanvas').hidden = state.workflow.nodes.length > 0;

    const maxX = Math.max(2000, ...state.workflow.nodes.map(n => (n.x || 0) + 320));
    const maxY = Math.max(1200, ...state.workflow.nodes.map(n => (n.y || 0) + 240));

    root.style.minWidth = `${maxX}px`;
    root.style.minHeight = `${maxY}px`;
    svg.setAttribute('width', maxX);
    svg.setAttribute('height', maxY);
    svg.style.width = `${maxX}px`;
    svg.style.height = `${maxY}px`;
    svg.removeAttribute('viewBox');

    state.workflow.nodes.forEach(n => {
      const card = document.createElement('article');
      const cat = categoryFor(n.type);
      const isEnabled = n.enabled !== false;
      card.className = `node-card${state.selected === n.id ? ' selected' : ''}${!isEnabled ? ' node-disabled' : ''}`;
      card.dataset.cat = cat;
      card.style.left = `${Number(n.x) || 0}px`;
      card.style.top = `${Number(n.y) || 0}px`;
      card.dataset.id = n.id;

      const head = document.createElement('div');
      head.className = 'node-head';
      const badge = document.createElement('span');
      badge.className = 'node-badge';
      badge.innerHTML = getIcon(n.type, 'icon-sm');
      const strong = document.createElement('strong');
      strong.textContent = n.title || titleFor(n.type);

      const toggleLabel = document.createElement('label');
      toggleLabel.className = 'node-toggle-switch';
      toggleLabel.title = isEnabled ? 'Node Aktif (Klik untuk Bypass)' : 'Node Bypassed (Klik untuk Aktifkan)';
      toggleLabel.onpointerdown = (e) => e.stopPropagation();
      toggleLabel.onclick = (e) => e.stopPropagation();

      const toggleCheck = document.createElement('input');
      toggleCheck.type = 'checkbox';
      toggleCheck.checked = isEnabled;
      toggleCheck.onchange = (e) => {
        e.stopPropagation();
        n.enabled = e.target.checked;
        markDirty();
        renderCanvas();
        if (state.selected === n.id) renderInspector();
        liveUpdateWorkflow();
      };

      const toggleSlider = document.createElement('span');
      toggleSlider.className = 'toggle-slider';
      toggleSlider.onpointerdown = (e) => e.stopPropagation();
      toggleLabel.append(toggleCheck, toggleSlider);

      head.append(badge, strong, toggleLabel);

      const meta = document.createElement('div');
      meta.className = 'node-meta';
      let subtitleText = n.subtitle || state.catalog[n.type]?.subtitle || n.type;
      if (n.type === 'input') {
        if (n.config?.sourceType === 'youtube') {
          subtitleText = n.config?.youtubeUrl ? `YouTube: ${n.config.youtubeUrl.slice(0, 28)}...` : 'YouTube Stream Source';
        } else if (n.config?.sourceType === 'camera') {
          subtitleText = `Webcam / Camera #${n.config.source || 0}`;
        }
      }
      meta.textContent = subtitleText;

      if (!isEnabled) {
        const bypassTag = document.createElement('span');
        bypassTag.className = 'node-bypassed-badge';
        bypassTag.textContent = 'BYPASSED';
        meta.append(' ', bypassTag);
      }

      if (n.type === 'if_else') {
        const isElse = String(n.config?.passWhen).toLowerCase() === 'false';
        const tag = document.createElement('div');
        tag.style.fontSize = '10px';
        tag.style.fontWeight = '700';
        tag.style.marginTop = '4px';
        tag.style.padding = '2px 6px';
        tag.style.borderRadius = '4px';
        tag.style.display = 'inline-block';
        tag.style.backgroundColor = isElse ? 'rgba(239, 68, 68, 0.2)' : 'rgba(34, 197, 94, 0.2)';
        tag.style.color = isElse ? '#ef4444' : '#22c55e';
        tag.style.border = `1px solid ${isElse ? '#ef4444' : '#22c55e'}`;
        tag.textContent = isElse ? '🔴 CABANG ELSE (False)' : '🟢 CABANG IF (True)';
        meta.append(tag);
      }

      const input = document.createElement('button');
      input.className = 'port input';
      input.title = 'Connect input';
      input.setAttribute('aria-label', `Connect to ${n.title || n.type}`);

      const output = document.createElement('button');
      output.className = 'port output';
      output.title = 'Connect output';
      output.setAttribute('aria-label', `Connect from ${n.title || n.type}`);

      if (state.connecting) {
        if (n.id === state.connecting.from) {
          card.classList.add('connecting-source');
        } else {
          card.classList.add('connecting-target');
        }
      }

      const statusBar = document.createElement('div');
      statusBar.className = 'node-status-bar';
      statusBar.dataset.nodeId = n.id;
      renderNodeStatusBarContent(statusBar, n, state.status?.nodeTelemetry?.[n.id]);

      if (n.type === 'export_code') card.append(head, meta, statusBar);
      else card.append(head, meta, input, output, statusBar);

      card.onclick = (e) => {
        if (state.reconnectingEdge) {
          applyEdgeReconnect(n.id);
          return;
        }
        if (state.connecting) {
          e.stopPropagation();
          connectTo(n.id);
          return;
        }
        if (e.target.classList.contains('port')) return;
        selectNode(n.id);
      };

      input.onclick = (e) => {
        e.stopPropagation();
        if (state.reconnectingEdge) {
          applyEdgeReconnect(n.id);
          return;
        }
        connectTo(n.id);
      };

      output.onclick = (e) => {
        e.stopPropagation();
        if (state.reconnectingEdge) {
          applyEdgeReconnect(n.id);
          return;
        }
        if (state.connecting && state.connecting.from === n.id) {
          state.connecting = null;
          $('#canvasHint').textContent = 'Penyambungan garis dibatalkan';
          renderCanvas();
          return;
        }
        connectFrom(n.id);
      };

      // Support drag-to-connect from output port
      output.onpointerdown = (e) => {
        e.stopPropagation();
        connectFrom(n.id);
      };

      card.onpointerup = (e) => {
        if (state.connecting && state.connecting.from !== n.id) {
          e.stopPropagation();
          connectTo(n.id);
        }
      };

      enableDrag(card, n);
      root.append(card);
    });

    drawEdges();
  }

  function hideEdgeContextMenu() {
    const menu = $('#edgeContextMenu');
    if (menu) menu.hidden = true;
  }

  function showEdgeContextMenu(e, edge, index) {
    const menu = $('#edgeContextMenu');
    if (!menu) return;
    const a = nodeFor(edge[0]);
    const b = nodeFor(edge[1]);
    const titleA = a ? a.title : edge[0];
    const titleB = b ? b.title : edge[1];

    menu.replaceChildren();

    // Menu Header
    const header = document.createElement('div');
    header.className = 'edge-menu-header';
    header.innerHTML = `<span>${titleA} → ${titleB}</span>`;
    menu.append(header);

    // 1. Pindahkan Ujung Tujuan (Target)
    const btnMoveTarget = document.createElement('button');
    btnMoveTarget.className = 'edge-menu-item';
    btnMoveTarget.innerHTML = `
      <svg class="icon-svg icon-sm" viewBox="0 0 24 24"><path d="M5 12h14"/><path d="m12 5 7 7-7 7"/></svg>
      <span>Pindahkan Ujung Tujuan (Target)</span>
    `;
    btnMoveTarget.onclick = (evt) => {
      evt.stopPropagation();
      hideEdgeContextMenu();
      state.reconnectingEdge = {
        index,
        edge: [...edge],
        fixedNode: edge[0],
        mode: 'target'
      };
      $('#canvasHint').textContent = `⚡ Mode Pindah Garis: Klik node TUJUAN baru untuk menyambungkan dari "${titleA}"`;
      renderCanvas();
    };
    menu.append(btnMoveTarget);

    // 2. Pindahkan Ujung Sumber (Source)
    const btnMoveSource = document.createElement('button');
    btnMoveSource.className = 'edge-menu-item';
    btnMoveSource.innerHTML = `
      <svg class="icon-svg icon-sm" viewBox="0 0 24 24"><path d="M19 12H5"/><path d="m12 19-7-7 7-7"/></svg>
      <span>Pindahkan Ujung Sumber (Source)</span>
    `;
    btnMoveSource.onclick = (evt) => {
      evt.stopPropagation();
      hideEdgeContextMenu();
      state.reconnectingEdge = {
        index,
        edge: [...edge],
        fixedNode: edge[1],
        mode: 'source'
      };
      $('#canvasHint').textContent = `⚡ Mode Pindah Garis: Klik node SUMBER baru untuk menyambungkan ke "${titleB}"`;
      renderCanvas();
    };
    menu.append(btnMoveSource);

    // 3. Hapus Garis
    const btnDelete = document.createElement('button');
    btnDelete.className = 'edge-menu-item danger';
    btnDelete.innerHTML = `
      <svg class="icon-svg icon-sm" viewBox="0 0 24 24"><path d="M3 6h18"/><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"/><path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"/><line x1="10" y1="11" x2="10" y2="17"/><line x1="14" y1="11" x2="14" y2="17"/></svg>
      <span>Hapus Garis (Delete)</span>
    `;
    btnDelete.onclick = (evt) => {
      evt.stopPropagation();
      hideEdgeContextMenu();
      state.workflow.edges.splice(index, 1);
      markDirty();
      renderCanvas();
      toast(`Koneksi ${titleA} → ${titleB} dihapus`);
    };
    menu.append(btnDelete);

    // Position menu relative to canvas container
    const canvas = $('#canvas');
    const canvasRect = canvas.getBoundingClientRect();
    const mx = Math.max(10, Math.min(canvasRect.width - 230, (e.clientX - canvasRect.left) + canvas.scrollLeft));
    const my = Math.max(10, Math.min(canvasRect.height - 150, (e.clientY - canvasRect.top) + canvas.scrollTop));
    menu.style.left = `${mx}px`;
    menu.style.top = `${my}px`;
    menu.hidden = false;
  }

  function applyEdgeReconnect(nodeId) {
    if (!state.reconnectingEdge) return;
    const { index, fixedNode, mode } = state.reconnectingEdge;
    const targetNode = nodeFor(nodeId);
    const targetTitle = targetNode ? targetNode.title : nodeId;

    let newEdge = null;
    if (mode === 'target') {
      if (fixedNode === nodeId) {
        toast('Tidak bisa menyambungkan ke node yang sama (self-loop)');
        return;
      }
      newEdge = [fixedNode, nodeId];
    } else {
      if (nodeId === fixedNode) {
        toast('Tidak bisa menyambungkan dari node yang sama (self-loop)');
        return;
      }
      newEdge = [nodeId, fixedNode];
    }

    // Check duplicate
    const duplicate = state.workflow.edges.some((e, i) => i !== index && e[0] === newEdge[0] && e[1] === newEdge[1]);
    if (duplicate) {
      toast('Koneksi tersebut sudah ada');
      return;
    }

    state.workflow.edges[index] = newEdge;
    state.reconnectingEdge = null;
    $('#canvasHint').textContent = 'Select a node to inspect · drag to arrange · click port to connect';
    markDirty();
    renderCanvas();
    toast(`Koneksi berhasil dialihkan ke ${targetTitle}`);
  }

  function getNodePortPos(nodeId, type = 'output') {
    const n = nodeFor(nodeId);
    const nx = Number(n?.x) || 0;
    const ny = Number(n?.y) || 0;
    const card = document.querySelector(`.node-card[data-id="${nodeId}"]`);
    if (card) {
      const port = card.querySelector(`.port.${type}`);
      if (port) {
        const cRect = card.getBoundingClientRect();
        const pRect = port.getBoundingClientRect();
        if (cRect.width > 0 && pRect.width > 0) {
          const z = state.zoom || 1;
          const cx = (pRect.left + pRect.width / 2 - cRect.left) / z;
          const cy = (pRect.top + pRect.height / 2 - cRect.top) / z;
          return { x: nx + cx, y: ny + cy };
        }
      }
    }
    // High-precision fallback matching .node-card & .port CSS geometry
    // (card: 214px wide, border-left: 2px, border-right: 2px, border-top: 4px; port: 18x18, top: 42px, translateY(-50%))
    return {
      x: type === 'output' ? nx + 212 : nx + 2,
      y: ny + 46
    };
  }

  function drawEdges() {
    const svg = $('#edges');
    if (!svg) return;
    svg.replaceChildren();

    state.workflow.edges.forEach((edge, index) => {
      const a = nodeFor(edge[0]);
      const b = nodeFor(edge[1]);
      if (!a || !b) return;

      const p1 = getNodePortPos(edge[0], 'output');
      const p2 = getNodePortPos(edge[1], 'input');
      const x1 = p1.x;
      const y1 = p1.y;
      const x2 = p2.x;
      const y2 = p2.y;
      const bend = Math.max(45, Math.abs(x2 - x1) * 0.45);
      const d = `M ${x1} ${y1} C ${x1 + bend} ${y1}, ${x2 - bend} ${y2}, ${x2} ${y2}`;

      const g = document.createElementNS('http://www.w3.org/2000/svg', 'g');
      g.setAttribute('class', 'edge-group');
      if (state.selectedEdge === index) {
        g.classList.add('selected');
      }
      if (state.reconnectingEdge && state.reconnectingEdge.index === index) {
        g.classList.add('reconnecting');
      }

      // 1. Visible path (Vibrant, high-contrast colorful cable)
      const catA = categoryFor(a.type);
      const EDGE_COLORS = {
        'Sources': '#059669',
        'AI Vision Models': '#4f46e5',
        'Tracking & Analysis': '#0284c7',
        'Image Preprocessing': '#d97706',
        'Annotations & Drawing': '#e11d48',
        'Logic & Flow Control': '#7c3aed',
        'Outputs & Export': '#0d9488'
      };
      const isEdgeSelected = state.selectedEdge === index;
      const edgeStroke = isEdgeSelected ? '#f59e0b' : (EDGE_COLORS[catA] || '#2563eb');
      const edgeWidth = isEdgeSelected ? '4.5px' : '2.6px';
      const edgeFilter = isEdgeSelected ? 'drop-shadow(0 0 10px rgba(245, 158, 11, 0.75))' : 'drop-shadow(0 2px 4px rgba(0, 0, 0, 0.16))';

      const visiblePath = document.createElementNS('http://www.w3.org/2000/svg', 'path');
      visiblePath.setAttribute('d', d);
      visiblePath.setAttribute('class', 'edge-visible-path');
      visiblePath.setAttribute('fill', 'none');
      visiblePath.setAttribute('stroke', edgeStroke);
      visiblePath.setAttribute('stroke-width', isEdgeSelected ? '4.5' : '2.6');
      visiblePath.style.cssText = `fill: none !important; stroke: ${edgeStroke} !important; stroke-width: ${edgeWidth} !important; pointer-events: none !important; filter: ${edgeFilter} !important;`;

      // 2. Invisible hit area (strictly transparent, 18px click target)
      const hitPath = document.createElementNS('http://www.w3.org/2000/svg', 'path');
      hitPath.setAttribute('d', d);
      hitPath.setAttribute('class', 'edge-hit-area');
      hitPath.setAttribute('fill', 'none');
      hitPath.setAttribute('stroke', 'transparent');
      hitPath.setAttribute('style', 'fill: none !important; stroke: transparent !important; stroke-width: 18px !important; pointer-events: stroke !important; cursor: pointer !important;');
      hitPath.setAttribute('title', 'Klik garis untuk menu aksi, atau klik tombol [✕] merah untuk langsung menghapus');

      hitPath.onclick = (e) => {
        e.stopPropagation();
        if (state.connecting) return;
        state.selectedEdge = index;
        drawEdges();
        showEdgeContextMenu(e, edge, index);
      };

      // 3. Compact 1-Click Delete Button in the center of the wire (appears on hover)
      const x_mid = (x1 + x2) / 2;
      const y_mid = (y1 + y2) / 2;

      const delGroup = document.createElementNS('http://www.w3.org/2000/svg', 'g');
      delGroup.setAttribute('class', 'edge-del-btn-group');
      delGroup.setAttribute('transform', `translate(${x_mid}, ${y_mid})`);

      const delCircle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
      delCircle.setAttribute('r', '7.5');
      delCircle.setAttribute('class', 'edge-quick-del-circle');

      const delLine1 = document.createElementNS('http://www.w3.org/2000/svg', 'line');
      delLine1.setAttribute('x1', '-2.8');
      delLine1.setAttribute('y1', '-2.8');
      delLine1.setAttribute('x2', '2.8');
      delLine1.setAttribute('y2', '2.8');
      delLine1.setAttribute('stroke', '#ffffff');
      delLine1.setAttribute('stroke-width', '1.6');
      delLine1.setAttribute('stroke-linecap', 'round');

      const delLine2 = document.createElementNS('http://www.w3.org/2000/svg', 'line');
      delLine2.setAttribute('x1', '2.8');
      delLine2.setAttribute('y1', '-2.8');
      delLine2.setAttribute('x2', '-2.8');
      delLine2.setAttribute('y2', '2.8');
      delLine2.setAttribute('stroke', '#ffffff');
      delLine2.setAttribute('stroke-width', '1.6');
      delLine2.setAttribute('stroke-linecap', 'round');

      const delTitle = document.createElementNS('http://www.w3.org/2000/svg', 'title');
      delTitle.textContent = `Hapus koneksi ${a.title || a.id} → ${b.title || b.id}`;
      delGroup.append(delTitle, delCircle, delLine1, delLine2);

      delGroup.onclick = (e) => {
        e.stopPropagation();
        hideEdgeContextMenu();
        state.workflow.edges.splice(index, 1);
        state.selectedEdge = null;
        markDirty();
        renderCanvas();
        toast(`Koneksi ${a.title || a.id} → ${b.title || b.id} berhasil dihapus`);
      };

      g.append(visiblePath, hitPath, delGroup);
      svg.append(g);
    });

    // 4. Live interactive wire following mouse while pulling line (Thin 1.8px)
    if (state.connecting) {
      const fromNode = nodeFor(state.connecting.from);
      if (fromNode) {
        const p1 = getNodePortPos(state.connecting.from, 'output');
        const x1 = p1.x;
        const y1 = p1.y;
        let x2 = state.connecting.mouseX !== undefined ? state.connecting.mouseX : x1 + 80;
        let y2 = state.connecting.mouseY !== undefined ? state.connecting.mouseY : y1;

        // Snap seamlessly to target input port if cursor is hovering over another node card or input port
        if (state.connecting.targetHoverId && state.connecting.targetHoverId !== state.connecting.from) {
          const p2 = getNodePortPos(state.connecting.targetHoverId, 'input');
          x2 = p2.x;
          y2 = p2.y;
        }

        const bend = Math.max(45, Math.abs(x2 - x1) * 0.45);
        const previewD = `M ${x1} ${y1} C ${x1 + bend} ${y1}, ${x2 - bend} ${y2}, ${x2} ${y2}`;

        const previewPath = document.createElementNS('http://www.w3.org/2000/svg', 'path');
        previewPath.setAttribute('d', previewD);
        previewPath.setAttribute('class', 'edge-preview-wire');
        previewPath.setAttribute('fill', 'none');
        previewPath.setAttribute('stroke', '#0284c7');
        previewPath.setAttribute('stroke-width', '1.8');
        previewPath.style.cssText = 'fill: none !important; stroke: #0284c7 !important; stroke-width: 1.8px !important; pointer-events: none !important;';
        svg.append(previewPath);
      }
    }
  }

  function enableDrag(card, node) {
    let start;
    card.onpointerdown = (e) => {
      if (e.target.classList.contains('port') || e.target.closest('.node-toggle-switch')) return;
      start = { x: e.clientX, y: e.clientY, nx: node.x || 0, ny: node.y || 0 };
      card.setPointerCapture(e.pointerId);
    };
    card.onpointermove = (e) => {
      if (!start) return;
      node.x = Math.max(0, start.nx + (e.clientX - start.x) / state.zoom);
      node.y = Math.max(0, start.ny + (e.clientY - start.y) / state.zoom);
      card.style.left = `${node.x}px`;
      card.style.top = `${node.y}px`;
      drawEdges();
      markDirty();
    };
    card.onpointerup = () => {
      start = null;
    };
  }

  function selectNode(id) {
    state.selected = id;
    renderCanvas();
    renderInspector();
  }

  function connectFrom(id) {
    const fromNode = nodeFor(id);
    if (fromNode?.type === 'export_code') return;
    const p1 = getNodePortPos(id, 'output');
    state.connecting = {
      from: id,
      mouseX: p1.x,
      mouseY: p1.y,
      targetHoverId: null
    };
    $('#canvasHint').innerHTML = `⚡ <b>Sedang menarik garis dari "${fromNode?.title || id}":</b> Klik kartu node tujuan untuk menghubungkan cabang (atau tekan Esc untuk batal)`;
    renderCanvas();
  }

  function connectTo(id) {
    if (!state.connecting || state.connecting.from === id) {
      state.connecting = null;
      renderCanvas();
      return;
    }
    const fromId = state.connecting.from;
    const fromNode = nodeFor(fromId);
    const toNode = nodeFor(id);
    if (fromNode?.type === 'export_code' || toNode?.type === 'export_code') {
      state.connecting = null;
      toast('Export Code tidak memakai koneksi graph', true);
      renderCanvas();
      return;
    }
    const edge = [fromId, id];

    if (state.workflow.edges.some(e => e[0] === edge[0] && e[1] === edge[1])) {
      toast('Koneksi tersebut sudah ada');
      state.connecting = null;
      renderCanvas();
      return;
    }

    state.workflow.edges.push(edge);
    markDirty();
    toast(`Tersambung: ${fromNode?.title || fromId} ➔ ${toNode?.title || id}`);
    state.connecting = null;
    $('#canvasHint').textContent = 'Pilih node untuk konfigurasi · geser untuk atur posisi · klik port untuk sambungkan garis';
    renderCanvas();
  }

  // Node types that are "terminal" outputs — we connect INTO them, not FROM them as tail
  const OUTPUT_NODE_TYPES = new Set([
    'preview', 'alert', 'webhook_output', 'image_output', 'database_output', 'export_code'
  ]);

  // Find the best "tail" node to auto-connect from when adding a new node.
  // Returns the last node that has no outgoing edge, preferring non-output nodes.
  function findAutoConnectTail(excludeType) {
    const nodes = state.workflow.nodes.filter(n => n.type !== 'export_code');
    if (nodes.length === 0) return null;

    const edges = state.workflow.edges;
    const nodesWithOutgoing = new Set(edges.map(e => e[0]));

    // Candidate: nodes without outgoing edges (true "tails")
    const tails = nodes.filter(n => !nodesWithOutgoing.has(n.id));

    if (tails.length === 0) {
      // All nodes have outgoing edges — pick the last non-output node in the list
      const nonOutputs = nodes.filter(n => !OUTPUT_NODE_TYPES.has(n.type));
      return nonOutputs.length > 0 ? nonOutputs[nonOutputs.length - 1] : nodes[nodes.length - 1];
    }

    // Prefer the last non-output tail
    const nonOutputTails = tails.filter(n => !OUTPUT_NODE_TYPES.has(n.type));
    if (nonOutputTails.length > 0) return nonOutputTails[nonOutputTails.length - 1];

    // If only output tails remain, fall back to last node that feeds INTO those outputs
    const outputTailIds = new Set(tails.map(n => n.id));
    const feedsIntoOutput = nodes.filter(n =>
      !outputTailIds.has(n.id) &&
      edges.some(e => e[0] === n.id && outputTailIds.has(e[1]))
    );
    if (feedsIntoOutput.length > 0) return feedsIntoOutput[feedsIntoOutput.length - 1];

    return tails[tails.length - 1];
  }

  const PIPELINE_RANK = {
    // 1. Sources (Inputs)
    'input': 10,
    'image_input': 10,
    'video_input': 10,
    'webcam_input': 10,
    'cctv_input': 10,
    'rtsp_input': 10,
    'folder_input': 10,

    // 2. Preprocessing / ROI
    'preprocessing': 20,
    'crop': 20,
    'filter': 20,
    'resize': 20,
    'roi': 20,

    // 3. Vision Models (Detection / Segmentation / Classification / Pose)
    'detector': 30,
    'segmenter': 30,
    'classifier': 30,
    'pose_estimation': 30,
    'ocr': 30,
    'face_detection': 30,

    // 4. Tracking
    'tracker': 40,
    'tracking': 40,
    'roboflow_tracker': 40,
    'bytetrack': 40,

    // 5. Counters / Logic / Analysis
    'object_counter': 50,
    'counter': 50,
    'zone_counter': 50,
    'speed_estimator': 50,
    'dwell_time': 50,
    'logic': 50,
    'filter_class': 50,

    // 6. Outputs / Sinks / Alerts
    'preview': 60,
    'live': 60,
    'alert': 60,
    'webhook_output': 60,
    'database_output': 60,
    'image_output': 60,
    'video_output': 60
  };

  function getPipelineRank(node) {
    if (!node) return 35;
    if (PIPELINE_RANK[node.type]) return PIPELINE_RANK[node.type];
    const bp = state.catalog[node.type] || {};
    const cat = (bp.category || '').toLowerCase();
    if (cat.includes('input')) return 10;
    if (cat.includes('preproc') || cat.includes('filter')) return 20;
    if (cat.includes('detect') || cat.includes('model')) return 30;
    if (cat.includes('track')) return 40;
    if (cat.includes('count') || cat.includes('analytic') || cat.includes('logic')) return 50;
    if (cat.includes('output') || OUTPUT_NODE_TYPES.has(node.type)) return 60;
    return 35;
  }

  function autoAssembleWorkflow() {
    if (!state.workflow.nodes || state.workflow.nodes.length === 0) {
      toast('Tidak ada node di canvas untuk dirangkai');
      return;
    }

    if (state.workflow.nodes.length === 1) {
      toast('Minimal butuh 2 node untuk merangkai alur kerja');
      return;
    }

    // Urutkan node sesuai hierarki pipeline computer vision standar
    const sorted = state.workflow.nodes.filter(n => n.type !== 'export_code').sort((a, b) => {
      const rankDiff = getPipelineRank(a) - getPipelineRank(b);
      if (rankDiff !== 0) return rankDiff;
      return (a.x || 0) - (b.x || 0);
    });

    state.workflow.nodes = sorted;

    // Tata letak posisi secara horizontal proporsional
    const startX = 80;
    const startY = 100;
    const spacingX = 260;

    sorted.forEach((node, idx) => {
      node.x = startX + idx * spacingX;
      node.y = startY;
    });

    // Rangkai koneksi berurutan: Node[0] → Node[1] → ... → Node[N-1]
    state.workflow.edges = [];
    for (let i = 0; i < sorted.length - 1; i++) {
      state.workflow.edges.push([sorted[i].id, sorted[i + 1].id]);
    }

    markDirty();
    renderCanvas();
    updatePreviewSelect();

    const sequenceSummary = sorted.map(n => n.title).join(' → ');
    toast(`⚡ Alur kerja berhasil dirangkai: ${sequenceSummary}`);
  }

  function addNode(type) {
    const bp = state.catalog[type];
    if (!bp) return;
    if (type === 'export_code' && state.workflow.nodes.some(n => n.type === 'export_code')) {
      toast('Satu workflow hanya memerlukan satu Export Code', true);
      return;
    }
    const used = new Set(state.workflow.nodes.map(n => n.id));
    let id = type, i = 2;
    while (used.has(id)) id = `${type}-${i++}`;

    // Find a tail node to connect from (before pushing the new node)
    const tail = state.autoConnect && type !== 'export_code' ? findAutoConnectTail(type) : null;

    // Check if tail currently connects directly into an output node
    // e.g. Detector -> Preview. If we add Tracker, rewire to: Detector -> Tracker -> Preview
    let outputToRewire = null;
    if (state.autoConnect && tail && !OUTPUT_NODE_TYPES.has(type)) {
      const existingOutEdge = state.workflow.edges.find(e => {
        if (e[0] !== tail.id) return false;
        const targetNode = nodeFor(e[1]);
        return targetNode && OUTPUT_NODE_TYPES.has(targetNode.type);
      });
      if (existingOutEdge) {
        outputToRewire = existingOutEdge[1];
      }
    }

    // Position: place to the right of the tail node, or in a grid if no tail
    let nx = 140 + (state.workflow.nodes.length % 4) * 260;
    let ny = 90 + Math.floor(state.workflow.nodes.length / 4) * 140;
    if (type === 'export_code') { nx = 360; ny = 80; }
    if (tail) {
      nx = tail.x + 240;
      ny = tail.y;
      // If there's already a node at roughly that position, push it down slightly
      const collision = state.workflow.nodes.some(n => Math.abs(n.x - nx) < 80 && Math.abs(n.y - ny) < 60);
      if (collision) ny += 120;
    }

    // If rewiring to an output node that sits at or near nx, shift output node to the right
    if (outputToRewire) {
      const outNode = nodeFor(outputToRewire);
      if (outNode && outNode.x <= nx) {
        outNode.x = nx + 240;
      }
    }

    const node = {
      id,
      type,
      title: bp.title,
      subtitle: bp.subtitle,
      x: nx,
      y: ny,
      enabled: true,
      status: 'idle',
      config: clone(bp.config || {})
    };

    state.workflow.nodes.push(node);

    // Auto-connect if enabled: add an edge from tail -> new node (avoid duplicates)
    if (state.autoConnect && tail) {
      const edgeExists = state.workflow.edges.some(e => e[0] === tail.id && e[1] === id);
      if (!edgeExists) {
        state.workflow.edges.push([tail.id, id]);
      }
    }

    // Rewire into existing output node if applicable
    if (state.autoConnect && outputToRewire) {
      // Remove old tail -> output edge
      state.workflow.edges = state.workflow.edges.filter(e => !(e[0] === tail.id && e[1] === outputToRewire));
      // Connect new node -> output
      if (!state.workflow.edges.some(e => e[0] === id && e[1] === outputToRewire)) {
        state.workflow.edges.push([id, outputToRewire]);
      }
    }

    markDirty();
    renderCanvas();
    selectNode(id);
    updatePreviewSelect();
    toast(type === 'export_code' ? 'Export Code ditambahkan tanpa koneksi' : state.autoConnect ? `${bp.title} ditambahkan & terhubung` : `${bp.title} ditambahkan (Manual)`);
  }

  function deleteSelectedNode() {
    cancelActiveZoneEditor();
    if (!state.selected) return;
    const deletedId = state.selected;
    const deletedNode = nodeFor(deletedId);
    if (!deletedNode) return;
    const title = deletedNode.title || deletedId;

    // Candidates to bridge: [ [fromId, toId], ... ]
    let bridged = [];

    // Only compute bridge if state.autoConnect is active
    if (state.autoConnect) {
      // 1. Identify direct incoming and outgoing nodes
      const incomingIds = state.workflow.edges
        .filter(e => e[1] === deletedId)
        .map(e => e[0]);
      const outgoingIds = state.workflow.edges
        .filter(e => e[0] === deletedId)
        .map(e => e[1]);

      if (incomingIds.length > 0 && outgoingIds.length > 0) {
        // Standard chain: bridge all upstream nodes directly to all downstream nodes
        for (const inId of incomingIds) {
          for (const outId of outgoingIds) {
            if (inId !== outId) {
              bridged.push([inId, outId]);
            }
          }
        }
      } else if (incomingIds.length > 0 && outgoingIds.length === 0) {
        // Node only had incoming connections; check if there is an unattached downstream node
        // in visual sequence (ordered by x coordinate to the right)
        const otherNodes = state.workflow.nodes
          .filter(n => n.id !== deletedId && n.x > (deletedNode.x || 0))
          .sort((a, b) => (a.x || 0) - (b.x || 0));

        const currentInTargets = new Set(
          state.workflow.edges
            .filter(e => e[0] !== deletedId && e[1] !== deletedId)
            .map(e => e[1])
        );
        const downstream = otherNodes.find(n => !currentInTargets.has(n.id) || OUTPUT_NODE_TYPES.has(n.type));
        if (downstream) {
          for (const inId of incomingIds) {
            if (inId !== downstream.id) {
              bridged.push([inId, downstream.id]);
            }
          }
        }
      } else if (incomingIds.length === 0 && outgoingIds.length > 0) {
        // Node only had outgoing connections; check if there is an upstream node
        // in visual sequence (ordered by x coordinate to the left, descending)
        const otherNodes = state.workflow.nodes
          .filter(n => n.id !== deletedId && n.x < (deletedNode.x || 0))
          .sort((a, b) => (b.x || 0) - (a.x || 0));

        const currentOutSources = new Set(
          state.workflow.edges
            .filter(e => e[0] !== deletedId && e[1] !== deletedId)
            .map(e => e[0])
        );
        const upstream = otherNodes.find(n => !currentOutSources.has(n.id) && !OUTPUT_NODE_TYPES.has(n.type));
        if (upstream) {
          for (const outId of outgoingIds) {
            if (upstream.id !== outId) {
              bridged.push([upstream.id, outId]);
            }
          }
        }
      } else {
        // Neither incoming nor outgoing were connected; bridge unattached left and right neighbors in sequence
        const leftNodes = state.workflow.nodes
          .filter(n => n.id !== deletedId && n.x < (deletedNode.x || 0))
          .sort((a, b) => (b.x || 0) - (a.x || 0));
        const rightNodes = state.workflow.nodes
          .filter(n => n.id !== deletedId && n.x > (deletedNode.x || 0))
          .sort((a, b) => (a.x || 0) - (b.x || 0));

        const currentOutSources = new Set(
          state.workflow.edges
            .filter(e => e[0] !== deletedId && e[1] !== deletedId)
            .map(e => e[0])
        );
        const currentInTargets = new Set(
          state.workflow.edges
            .filter(e => e[0] !== deletedId && e[1] !== deletedId)
            .map(e => e[1])
        );

        const upstream = leftNodes.find(n => !currentOutSources.has(n.id) && !OUTPUT_NODE_TYPES.has(n.type));
        const downstream = rightNodes.find(n => !currentInTargets.has(n.id));
        if (upstream && downstream && upstream.id !== downstream.id) {
          bridged.push([upstream.id, downstream.id]);
        }
      }
    }

    // 2. Remove deleted node and its associated edges
    state.workflow.nodes = state.workflow.nodes.filter(item => item.id !== deletedId);
    state.workflow.edges = state.workflow.edges.filter(e => e[0] !== deletedId && e[1] !== deletedId);

    // 3. Apply newly bridged edges (guard against duplicates and self-loops)
    const newlyAdded = [];
    for (const [src, dst] of bridged) {
      if (src && dst && src !== dst) {
        const exists = state.workflow.edges.some(e => e[0] === src && e[1] === dst);
        if (!exists) {
          state.workflow.edges.push([src, dst]);
          newlyAdded.push([src, dst]);
        }
      }
    }

    state.selected = null;
    markDirty();
    renderCanvas();
    renderInspector();
    updatePreviewSelect();

    if (newlyAdded.length > 0) {
      const summary = newlyAdded
        .map(([s, d]) => `${nodeFor(s)?.title || s} → ${nodeFor(d)?.title || d}`)
        .join(', ');
      toast(`${title} dihapus & otomatis disambungkan (${summary})`);
    } else {
      toast(`${title} dihapus`);
    }
  }

  // --- Inspector / Tabbed & Conditional Settings ---
  function updateFrameSamplerStatus(nodeId, status = state.status) {
    const card = document.getElementById(`frame-sampler-stats-${nodeId}`);
    if (!card) return;
    const stats = status?.frameSamplers?.[nodeId];
    const value = (key, suffix = '') => {
      const raw = stats?.[key];
      if (raw === undefined || raw === null || !Number.isFinite(Number(raw))) return '—';
      return `${Number(raw).toFixed(key.toLowerCase().includes('fps') ? 1 : 0)}${suffix}`;
    };
    card.querySelector('[data-stat="inputFps"]').textContent = value('inputFps', ' FPS');
    card.querySelector('[data-stat="outputFps"]').textContent = value('outputFps', ' FPS');
    card.querySelector('[data-stat="inputFrames"]').textContent = value('inputFrames');
    card.querySelector('[data-stat="outputFrames"]').textContent = value('outputFrames');
    card.querySelector('[data-stat="droppedFrames"]').textContent = value('droppedFrames');
    card.querySelector('[data-stat="waiting"]').hidden = !!stats;
  }

  function updatePythonScriptStatus(nodeId, status = state.status) {
    const card = document.getElementById(`python-script-status-${nodeId}`);
    if (!card) return;
    const stats = status?.pythonScripts?.[nodeId] || {};
    const stateName = String(stats.state || 'idle').toUpperCase();
    card.querySelector('[data-stat="status"]').textContent = stateName;
    card.querySelector('[data-stat="metrics"]').textContent = `Frames: ${stats.processedFrames ?? '—'} · Errors: ${stats.errorCount ?? '—'} · Last: ${stats.lastDurationMs ?? '—'} ms · ${stats.lastRunAt || 'Belum ada run'}`;
    const details = [stats.error, ...(Array.isArray(stats.logs) ? stats.logs : [])].filter(Boolean).map(String).slice(-30);
    card.querySelector('[data-stat="logs"]').textContent = details.join('\n');
  }

  function renderNodeStatusBarContent(el, node, telem) {
    if (!el) return;
    if (node.enabled === false) {
      el.innerHTML = '<span class="status-dot bypassed"></span><span class="status-text bypassed">BYPASSED</span>';
      return;
    }
    if (!telem || telem.status === 'idle') {
      el.innerHTML = '<span class="status-dot idle"></span><span class="status-text idle">IDLE</span>';
      return;
    }
    if (telem.status === 'bypassed') {
      el.innerHTML = '<span class="status-dot bypassed"></span><span class="status-text bypassed">BYPASSED</span>';
      return;
    }
    if (telem.status === 'error') {
      el.innerHTML = '<span class="status-dot error"></span><span class="status-text error">✖ ERROR</span>';
      return;
    }
    const ms = telem.latencyMs !== undefined ? `${telem.latencyMs}ms` : '0ms';
    const items = telem.itemCount !== undefined ? `(${telem.itemCount})` : '';
    el.innerHTML = `<span class="status-dot success"></span><span class="status-latency">⚡ ${ms}</span> <span class="status-count">${items}</span>`;
  }

  function updateAllNodeTelemetryUI(telemetryData = {}) {
    state.workflow.nodes.forEach(node => {
      const bar = document.querySelector(`.node-status-bar[data-node-id="${node.id}"]`);
      if (bar) {
        renderNodeStatusBarContent(bar, node, telemetryData[node.id]);
      }
    });
    if (state.selected && state.inspectorTab === 'logs') {
      const selNode = nodeFor(state.selected);
      if (selNode) {
        updateInspectorLogsLive(selNode, telemetryData[selNode.id]);
      }
    }
  }

  function renderInspectorTelemetryLogs(node, container) {
    const telem = (state.status?.nodeTelemetry || {})[node.id] || {};
    const isNodeEnabled = node.enabled !== false;
    const isBypassed = !isNodeEnabled || telem.status === 'bypassed';
    const statusText = !isNodeEnabled ? 'BYPASSED (OFF)' : (telem.status ? telem.status.toUpperCase() : 'IDLE');
    const statusColor = isBypassed ? '#92400e' : (telem.status === 'success' ? '#065f46' : (telem.status === 'error' ? '#991b1b' : '#334155'));
    const statusBg = isBypassed ? '#fef3c7' : (telem.status === 'success' ? '#d1fae5' : (telem.status === 'error' ? '#fee2e2' : '#f1f5f9'));
    const statusBorder = isBypassed ? '#fcd34d' : (telem.status === 'success' ? '#6ee7b7' : (telem.status === 'error' ? '#fca5a5' : '#cbd5e1'));

    const hud = document.createElement('div');
    hud.className = 'telemetry-hud';
    hud.id = `telemetry-hud-${node.id}`;
    hud.innerHTML = `
      <div class="hud-stat-card">
        <span class="hud-stat-label">Execution Status</span>
        <span class="hud-stat-value" data-stat="status">
          <span class="status-pill-badge" style="background:${statusBg}; color:${statusColor}; border:1px solid ${statusBorder};">
            <span class="status-dot ${isBypassed ? 'bypassed' : (telem.status || 'idle')}"></span>
            ${statusText}
          </span>
        </span>
      </div>
      <div class="hud-stat-card">
        <span class="hud-stat-label">Latency (Per-Frame)</span>
        <span class="hud-stat-value" data-stat="latency" style="color:#0284c7; font-weight:800;">
          ${isBypassed ? '0.00 ms (Skip)' : (telem.latencyMs !== undefined ? `${telem.latencyMs} ms` : '—')}
        </span>
      </div>
      <div class="hud-stat-card">
        <span class="hud-stat-label">Items / Detections</span>
        <span class="hud-stat-value" data-stat="items" style="color:#7c3aed; font-weight:800;">
          ${telem.itemCount !== undefined ? `${telem.itemCount} items` : '—'}
        </span>
      </div>
      <div class="hud-stat-card">
        <span class="hud-stat-label">Last Timestamp</span>
        <span class="hud-stat-value" data-stat="time" style="font-size:11px; color:#0f172a; font-weight:700;">
          ${telem.timestamp ? new Date(telem.timestamp * 1000).toLocaleTimeString() : 'Belum jalan'}
        </span>
      </div>
    `;
    container.append(hud);

    // Action bar (Copy JSON, Refresh)
    const actRow = document.createElement('div');
    actRow.className = 'telemetry-action-row';

    const copyBtn = document.createElement('button');
    copyBtn.type = 'button';
    copyBtn.className = 'telemetry-btn-copy';
    copyBtn.innerHTML = '📋 Copy Full JSON Payload';
    copyBtn.onclick = () => {
      const fullPayload = {
        nodeId: node.id,
        type: node.type,
        enabled: isNodeEnabled,
        telemetry: telem,
      };
      navigator.clipboard.writeText(JSON.stringify(fullPayload, null, 2));
      toast('Payload telemetry berhasil disalin ke clipboard!');
    };

    const refreshBtn = document.createElement('button');
    refreshBtn.type = 'button';
    refreshBtn.className = 'telemetry-btn-refresh';
    refreshBtn.innerHTML = '🔄 Refresh';
    refreshBtn.onclick = async () => {
      await pollStatus();
      toast('Telemetry refreshed');
    };

    actRow.append(copyBtn, refreshBtn);
    container.append(actRow);

    // Error box if present
    const errBox = document.createElement('div');
    errBox.id = `telemetry-err-${node.id}`;
    errBox.className = 'telemetry-err-box';
    errBox.style.display = telem.error ? 'block' : 'none';
    errBox.style.background = 'rgba(239, 68, 68, 0.15)';
    errBox.style.border = '1px solid rgba(239, 68, 68, 0.4)';
    errBox.style.borderRadius = '6px';
    errBox.style.padding = '8px';
    errBox.style.marginBottom = '12px';
    errBox.style.fontSize = '11px';
    errBox.style.color = '#b91c1c';
    errBox.innerHTML = `<strong>Error Log:</strong> <span class="err-msg">${escapeHtml(telem.error || '')}</span>`;
    container.append(errBox);

    // Input Payload Box
    const inBox = document.createElement('div');
    inBox.className = 'payload-box';
    inBox.innerHTML = `
      <div class="payload-header" onclick="this.nextElementSibling.classList.toggle('collapsed')">
        <span>📥 Input Payload / Metadata</span>
        <span style="font-size:10px;opacity:0.7">▼ Collapse</span>
      </div>
      <pre class="payload-json" id="telemetry-input-${node.id}">${escapeHtml(JSON.stringify(telem.lastInput || {}, null, 2))}</pre>
    `;
    container.append(inBox);

    // Output Payload Box
    const outBox = document.createElement('div');
    outBox.className = 'payload-box';
    outBox.innerHTML = `
      <div class="payload-header" onclick="this.nextElementSibling.classList.toggle('collapsed')">
        <span>📤 Output Payload / Results</span>
        <span style="font-size:10px;opacity:0.7">▼ Collapse</span>
      </div>
      <pre class="payload-json" id="telemetry-output-${node.id}">${escapeHtml(JSON.stringify(telem.lastOutput || {}, null, 2))}</pre>
    `;
    container.append(outBox);
  }

  function updateInspectorLogsLive(node, telem = {}) {
    const hud = document.getElementById(`telemetry-hud-${node.id}`);
    if (!hud) return;
    const isNodeEnabled = node.enabled !== false;
    const isBypassed = !isNodeEnabled || telem.status === 'bypassed';
    const statusText = !isNodeEnabled ? 'BYPASSED (OFF)' : (telem.status ? telem.status.toUpperCase() : 'IDLE');
    const statusColor = !isNodeEnabled ? '#fbbf24' : (telem.status === 'success' ? '#10b981' : (telem.status === 'error' ? '#ef4444' : '#94a3b8'));

    const statusEl = hud.querySelector('[data-stat="status"]');
    if (statusEl) {
      statusEl.style.color = statusColor;
      statusEl.innerHTML = `<span class="status-dot ${isBypassed ? 'bypassed' : (telem.status || 'idle')}" style="display:inline-block;margin-right:4px;"></span> ${statusText}`;
    }

    const latEl = hud.querySelector('[data-stat="latency"]');
    if (latEl) {
      latEl.textContent = isBypassed ? '0.00 ms (Skip)' : (telem.latencyMs !== undefined ? `${telem.latencyMs} ms` : '—');
    }

    const itemEl = hud.querySelector('[data-stat="items"]');
    if (itemEl) {
      itemEl.textContent = telem.itemCount !== undefined ? `${telem.itemCount} items` : '—';
    }

    const timeEl = hud.querySelector('[data-stat="time"]');
    if (timeEl && telem.timestamp) {
      timeEl.textContent = new Date(telem.timestamp * 1000).toLocaleTimeString();
    }

    const inPre = document.getElementById(`telemetry-input-${node.id}`);
    if (inPre && !inPre.classList.contains('collapsed')) {
      inPre.textContent = JSON.stringify(telem.lastInput || {}, null, 2);
    }

    const outPre = document.getElementById(`telemetry-output-${node.id}`);
    if (outPre && !outPre.classList.contains('collapsed')) {
      outPre.textContent = JSON.stringify(telem.lastOutput || {}, null, 2);
    }

    const errBox = document.getElementById(`telemetry-err-${node.id}`);
    if (errBox) {
      errBox.style.display = telem.error ? 'block' : 'none';
      const errMsg = errBox.querySelector('.err-msg');
      if (errMsg) errMsg.textContent = telem.error || '';
    }
  }

  const _expandedOverlayLayerIds = new Set();

  const OVERLAY_LAYER_DEFAULTS_JS = {
    bounding_boxes: {
      type: 'bounding_boxes',
      enabled: true,
      color: '#2563eb',
      thickness: 2,
      fillOpacity: 0.0,
      classes: '',
    },
    labels: {
      type: 'labels',
      enabled: true,
      color: '#22c55e',
      template: '{detection.class}',
      fontScale: 0.55,
      position: 'top',
      classes: '',
    },
    confidence: {
      type: 'confidence',
      enabled: true,
      color: '#7c3aed',
      template: '{detection.confidence}',
      fontScale: 0.55,
      position: 'below_label',
      classes: '',
    },
    result_icons: {
      type: 'result_icons',
      enabled: true,
      passClasses: 'ok, pass, good',
      passText: 'OK',
      failText: 'X',
      passColor: '#22c55e',
      failColor: '#ef4444',
      size: 0.65,
      position: 'top_right',
      classes: '',
    },
    custom_text: {
      type: 'custom_text',
      enabled: true,
      template: '{classification.class}  {classification.confidence}',
      x: 24,
      y: 48,
      fontScale: 1.0,
      thickness: 2,
      color: '#ffffff',
      background: true,
      backgroundColor: '#111827',
      position: 'bottom_right',
      classes: '',
    },
    heatmap: {
      type: 'heatmap',
      enabled: true,
      opacity: 0.40,
      decay: 0.98,
      colormap: 'jet',
      classes: '',
    },
    vector_arrow: {
      type: 'vector_arrow',
      enabled: true,
      color: '#38bdf8',
      thickness: 2,
      scale: 1.5,
      classes: '',
    },
  };

  const OVERLAY_LAYER_NAMES_JS = {
    bounding_boxes: 'Bounding box',
    labels: 'Label',
    confidence: 'Confidence',
    result_icons: 'Status badge',
    custom_text: 'Custom text',
    heatmap: 'Traffic Heatmap',
    vector_arrow: 'Direction Arrow Vector',
  };

  function createOverlayLayerObject(type, count = 0) {
    const def = OVERLAY_LAYER_DEFAULTS_JS[type] || OVERLAY_LAYER_DEFAULTS_JS.custom_text;
    return { ...clone(def), id: `${type}-${Date.now()}-${count + 1}` };
  }

  function renderOverlayAnnotateInspector(node, body) {
    if (!node.config) node.config = {};
    if (!Array.isArray(node.config.layers)) {
      node.config.layers = [];
    }

    // Header matching user screenshot: "Node settings" with badge "Overlay / Annotate"
    const titleRow = document.createElement('div');
    titleRow.className = 'inspector-header-row';
    titleRow.innerHTML = `
      <span class="inspector-title-text">Node settings</span>
      <span class="inspector-node-badge">Overlay / Annotate</span>
    `;
    const titleEl = $('#inspectorTitle');
    if (titleEl) titleEl.replaceChildren(titleRow);

    // Subtitle
    const subtitle = document.createElement('p');
    subtitle.className = 'inspector-subtitle';
    subtitle.textContent = 'Configure the selected workflow step.';
    body.append(subtitle);

    // Guide button
    const guideBtn = document.createElement('button');
    guideBtn.type = 'button';
    guideBtn.className = 'inspector-guide-btn';
    guideBtn.innerHTML = `
      <svg class="icon-svg icon-sm" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><path d="M12 16v-4"/><path d="M12 8h.01"/></svg>
      <span>📘 Panduan &amp; Cara Penggunaan Node</span>
    `;
    guideBtn.onclick = () => showNodeGuideModal(node);
    body.append(guideBtn);

    // SETTINGS section
    const settingsLabel = document.createElement('div');
    settingsLabel.className = 'inspector-section-label';
    settingsLabel.textContent = 'SETTINGS';
    body.append(settingsLabel);

    const settingRow = document.createElement('div');
    settingRow.className = 'inspector-setting-row';
    const enabledText = document.createElement('span');
    enabledText.className = 'setting-name';
    enabledText.textContent = 'Enabled';

    const toggleLabel = document.createElement('label');
    toggleLabel.className = 'toggle-switch-blue';
    const toggleInput = document.createElement('input');
    toggleInput.type = 'checkbox';
    toggleInput.checked = node.enabled !== false;
    toggleInput.onchange = async () => {
      node.enabled = toggleInput.checked;
      markDirty();
      renderCanvas();
      await liveUpdateWorkflow();
    };
    const toggleSlider = document.createElement('span');
    toggleSlider.className = 'slider-blue';
    toggleLabel.append(toggleInput, toggleSlider);
    settingRow.append(enabledText, toggleLabel);
    body.append(settingRow);

    // DRAWING LAYERS section
    const drawingLabel = document.createElement('div');
    drawingLabel.className = 'inspector-section-label';
    drawingLabel.textContent = 'DRAWING LAYERS';
    body.append(drawingLabel);

    const addLayerContainer = document.createElement('div');
    addLayerContainer.className = 'add-layer-container';

    const addBtn = document.createElement('button');
    addBtn.type = 'button';
    addBtn.className = 'btn-add-layer';
    addBtn.id = 'btnAddOverlayLayer';
    addBtn.innerHTML = `
      <svg class="icon-svg icon-sm" viewBox="0 0 24 24"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
      <span>+ Add layer</span>
    `;

    const dropdown = document.createElement('div');
    dropdown.className = 'add-layer-dropdown';
    dropdown.id = 'addLayerDropdown';
    dropdown.hidden = true;

    const layerOptions = [
      { type: 'bounding_boxes', name: 'Bounding box', icon: '▢' },
      { type: 'labels', name: 'Label', icon: '🏷' },
      { type: 'confidence', name: 'Confidence', icon: '%' },
      { type: 'result_icons', name: 'Status badge', icon: '✔' },
      { type: 'custom_text', name: 'Custom text', icon: 'T' },
      { type: 'heatmap', name: 'Traffic Heatmap', icon: '🔥' },
      { type: 'vector_arrow', name: 'Direction Arrow Vector', icon: '➔' },
    ];

    layerOptions.forEach(opt => {
      const itemBtn = document.createElement('button');
      itemBtn.type = 'button';
      itemBtn.className = 'add-layer-item';
      itemBtn.setAttribute('data-layer-type', opt.type);
      itemBtn.innerHTML = `<span class="item-icon">${opt.icon}</span> <span>${opt.name}</span>`;
      itemBtn.onclick = async (e) => {
        e.stopPropagation();
        dropdown.hidden = true;
        const newLayer = createOverlayLayerObject(opt.type, node.config.layers.length);
        node.config.layers.push(newLayer);
        _expandedOverlayLayerIds.add(newLayer.id);
        markDirty();
        await liveUpdateWorkflow();
        renderLayerCards();
      };
      dropdown.append(itemBtn);
    });

    addBtn.onclick = (e) => {
      e.stopPropagation();
      dropdown.hidden = !dropdown.hidden;
    };

    const onDocClick = (e) => {
      if (!addLayerContainer.contains(e.target)) {
        dropdown.hidden = true;
      }
    };
    document.addEventListener('click', onDocClick);

    addLayerContainer.append(addBtn, dropdown);
    body.append(addLayerContainer);

    const layersList = document.createElement('div');
    layersList.className = 'overlay-layers-list';
    body.append(layersList);

    function renderLayerCards() {
      layersList.replaceChildren();

      if (!node.config.layers || node.config.layers.length === 0) {
        const emptyHint = document.createElement('div');
        emptyHint.className = 'overlay-empty-hint';
        emptyHint.innerHTML = 'Belum ada layer anotasi.<br>Klik tombol <b>"+ Add layer"</b> di atas untuk menambahkan Bounding box, Label, Confidence, dll.';
        layersList.append(emptyHint);
        return;
      }

      node.config.layers.forEach((layer, idx) => {
        const card = document.createElement('div');
        card.className = 'overlay-layer-card';
        if (_expandedOverlayLayerIds.has(layer.id) || node.config.layers.length === 1) {
          card.classList.add('is-expanded');
        }

        // Head
        const head = document.createElement('div');
        head.className = 'overlay-layer-head';

        const titleWrap = document.createElement('div');
        titleWrap.className = 'overlay-layer-title-wrap';

        const dragHandle = document.createElement('span');
        dragHandle.className = 'overlay-layer-drag';
        dragHandle.textContent = '⋮⋮';

        const colorDot = document.createElement('span');
        colorDot.className = 'overlay-layer-color-dot';
        colorDot.style.background = layer.color || layer.passColor || '#2563eb';

        const nameSpan = document.createElement('span');
        nameSpan.className = 'overlay-layer-name';
        nameSpan.textContent = OVERLAY_LAYER_NAMES_JS[layer.type] || layer.type;

        titleWrap.append(dragHandle, colorDot, nameSpan);

        const actions = document.createElement('div');
        actions.className = 'overlay-layer-actions';

        // Layer enabled toggle
        const toggleWrap = document.createElement('label');
        toggleWrap.className = 'toggle-switch-layer';
        toggleWrap.title = 'Aktifkan/Nonaktifkan layer ini';
        toggleWrap.style.marginRight = '4px';
        const layerChk = document.createElement('input');
        layerChk.type = 'checkbox';
        layerChk.checked = layer.enabled !== false;
        layerChk.onchange = async (e) => {
          e.stopPropagation();
          layer.enabled = layerChk.checked;
          markDirty();
          await liveUpdateWorkflow();
        };
        toggleWrap.append(layerChk);

        // Move up
        const upBtn = document.createElement('button');
        upBtn.type = 'button';
        upBtn.className = 'layer-action-btn';
        upBtn.title = 'Pindah ke atas';
        upBtn.innerHTML = '▲';
        upBtn.disabled = idx === 0;
        upBtn.onclick = async (e) => {
          e.stopPropagation();
          const prev = node.config.layers[idx - 1];
          node.config.layers[idx - 1] = layer;
          node.config.layers[idx] = prev;
          markDirty();
          await liveUpdateWorkflow();
          renderLayerCards();
        };

        // Move down
        const downBtn = document.createElement('button');
        downBtn.type = 'button';
        downBtn.className = 'layer-action-btn';
        downBtn.title = 'Pindah ke bawah';
        downBtn.innerHTML = '▼';
        downBtn.disabled = idx === node.config.layers.length - 1;
        downBtn.onclick = async (e) => {
          e.stopPropagation();
          const next = node.config.layers[idx + 1];
          node.config.layers[idx + 1] = layer;
          node.config.layers[idx] = next;
          markDirty();
          await liveUpdateWorkflow();
          renderLayerCards();
        };

        // Delete
        const delBtn = document.createElement('button');
        delBtn.type = 'button';
        delBtn.className = 'layer-action-btn btn-delete';
        delBtn.title = 'Hapus layer ini';
        delBtn.innerHTML = '🗑';
        delBtn.onclick = async (e) => {
          e.stopPropagation();
          node.config.layers.splice(idx, 1);
          _expandedOverlayLayerIds.delete(layer.id);
          markDirty();
          await liveUpdateWorkflow();
          renderLayerCards();
        };

        // Expand/collapse chevron
        const expandBtn = document.createElement('button');
        expandBtn.type = 'button';
        expandBtn.className = 'layer-action-btn';
        expandBtn.title = 'Buka/Tutup pengaturan';
        expandBtn.innerHTML = card.classList.contains('is-expanded') ? '▴' : '▾';

        head.onclick = () => {
          const isExp = card.classList.toggle('is-expanded');
          expandBtn.innerHTML = isExp ? '▴' : '▾';
          if (isExp) _expandedOverlayLayerIds.add(layer.id);
          else _expandedOverlayLayerIds.delete(layer.id);
        };

        actions.append(toggleWrap, upBtn, downBtn, delBtn, expandBtn);
        head.append(titleWrap, actions);
        card.append(head);

        // Body
        const cardBody = document.createElement('div');
        cardBody.className = 'overlay-layer-body';

        // Helper row builders
        const addColorRow = (label, propName, fallbackColor = '#2563eb') => {
          const row = document.createElement('div');
          row.className = 'overlay-field-row';
          const lbl = document.createElement('span');
          lbl.className = 'overlay-field-label';
          lbl.textContent = label;

          const grp = document.createElement('div');
          grp.className = 'overlay-field-input-group';
          const colorInp = document.createElement('input');
          colorInp.type = 'color';
          colorInp.value = layer[propName] || fallbackColor;

          const textInp = document.createElement('input');
          textInp.type = 'text';
          textInp.value = layer[propName] || fallbackColor;
          textInp.style.width = '75px';
          textInp.style.fontFamily = 'monospace';

          const sync = async (val) => {
            layer[propName] = val;
            colorDot.style.background = val;
            markDirty();
            await liveUpdateWorkflow();
          };

          colorInp.oninput = () => { textInp.value = colorInp.value; sync(colorInp.value); };
          textInp.onchange = () => { colorInp.value = textInp.value; sync(textInp.value); };

          grp.append(colorInp, textInp);
          row.append(lbl, grp);
          cardBody.append(row);
        };

        const addSliderRow = (label, propName, min, max, step, defVal, unit = '') => {
          const row = document.createElement('div');
          row.className = 'overlay-field-row';
          const lbl = document.createElement('span');
          lbl.className = 'overlay-field-label';
          const curVal = layer[propName] !== undefined ? layer[propName] : defVal;
          lbl.textContent = `${label} (${curVal}${unit})`;

          const grp = document.createElement('div');
          grp.className = 'overlay-field-input-group';
          const rangeInp = document.createElement('input');
          rangeInp.type = 'range';
          rangeInp.min = String(min);
          rangeInp.max = String(max);
          rangeInp.step = String(step);
          rangeInp.value = String(curVal);

          rangeInp.oninput = async () => {
            const val = Number(rangeInp.value);
            layer[propName] = val;
            lbl.textContent = `${label} (${val}${unit})`;
            markDirty();
            await liveUpdateWorkflow();
          };

          grp.append(rangeInp);
          row.append(lbl, grp);
          cardBody.append(row);
        };

        const addTextRow = (label, propName, placeholder = '') => {
          const row = document.createElement('div');
          row.className = 'overlay-field-row';
          const lbl = document.createElement('span');
          lbl.className = 'overlay-field-label';
          lbl.textContent = label;

          const grp = document.createElement('div');
          grp.className = 'overlay-field-input-group';
          const inp = document.createElement('input');
          inp.type = 'text';
          inp.placeholder = placeholder;
          inp.value = layer[propName] ?? '';
          inp.onchange = async () => {
            layer[propName] = inp.value;
            markDirty();
            await liveUpdateWorkflow();
          };

          grp.append(inp);
          row.append(lbl, grp);
          cardBody.append(row);
        };

        const addSelectRow = (label, propName, options, defVal) => {
          const row = document.createElement('div');
          row.className = 'overlay-field-row';
          const lbl = document.createElement('span');
          lbl.className = 'overlay-field-label';
          lbl.textContent = label;

          const grp = document.createElement('div');
          grp.className = 'overlay-field-input-group';
          const sel = document.createElement('select');
          options.forEach(([v, l]) => {
            const opt = document.createElement('option');
            opt.value = v;
            opt.textContent = l;
            sel.append(opt);
          });
          sel.value = layer[propName] || defVal;
          sel.onchange = async () => {
            layer[propName] = sel.value;
            markDirty();
            await liveUpdateWorkflow();
          };

          grp.append(sel);
          row.append(lbl, grp);
          cardBody.append(row);
        };

        // Specific fields per layer type
        if (layer.type === 'bounding_boxes') {
          addColorRow('Box Color', 'color', '#2563eb');
          addSliderRow('Thickness', 'thickness', 1, 10, 1, 2, 'px');
          addSliderRow('Fill Opacity', 'fillOpacity', 0.0, 0.8, 0.05, 0.0);
          addTextRow('Filter Classes', 'classes', 'person, car (empty = all)');
        } else if (layer.type === 'labels') {
          addColorRow('Label Color', 'color', '#22c55e');
          addTextRow('Template', 'template', '{detection.class}');
          addSliderRow('Font Scale', 'fontScale', 0.25, 2.0, 0.05, 0.55);
          addSelectRow('Position', 'position', [
            ['top', 'Top of Box'],
            ['bottom', 'Bottom of Box'],
            ['center', 'Center of Box']
          ], 'top');
          addTextRow('Filter Classes', 'classes', 'person, car (empty = all)');
        } else if (layer.type === 'confidence') {
          addColorRow('Text Color', 'color', '#7c3aed');
          addTextRow('Template', 'template', '{detection.confidence}');
          addSliderRow('Font Scale', 'fontScale', 0.25, 2.0, 0.05, 0.55);
          addSelectRow('Position', 'position', [
            ['below_label', 'Below Label'],
            ['top', 'Top of Box'],
            ['bottom', 'Bottom of Box']
          ], 'below_label');
          addTextRow('Filter Classes', 'classes', 'person, car (empty = all)');
        } else if (layer.type === 'result_icons') {
          addTextRow('Pass Classes', 'passClasses', 'ok, pass, good');
          addTextRow('Pass Text', 'passText', 'OK');
          addTextRow('Fail Text', 'failText', 'X');
          addColorRow('Pass Color', 'passColor', '#22c55e');
          addColorRow('Fail Color', 'failColor', '#ef4444');
          addSliderRow('Badge Size', 'size', 0.25, 2.0, 0.05, 0.65);
          addSelectRow('Position', 'position', [
            ['top_right', 'Top Right'],
            ['top_left', 'Top Left'],
            ['bottom_right', 'Bottom Right'],
            ['bottom_left', 'Bottom Left'],
            ['center', 'Center']
          ], 'top_right');
          addTextRow('Filter Classes', 'classes', 'person, car (empty = all)');
        } else if (layer.type === 'custom_text') {
          addTextRow('Template', 'template', '{classification.class}  {classification.confidence}');
          addSelectRow('Position', 'position', [
            ['bottom_right', 'Bottom Right'],
            ['bottom_left', 'Bottom Left'],
            ['top_left', 'Top Left'],
            ['top_right', 'Top Right'],
            ['center', 'Center'],
            ['custom', 'Custom Coordinates (X, Y)']
          ], 'bottom_right');
          if (layer.position === 'custom') {
            addSliderRow('Coordinate X', 'x', 0, 1920, 1, 24, 'px');
            addSliderRow('Coordinate Y', 'y', 0, 1080, 1, 48, 'px');
          }
          addSliderRow('Font Scale', 'fontScale', 0.25, 3.0, 0.1, 1.0);
          addSliderRow('Thickness', 'thickness', 1, 8, 1, 2, 'px');
          addColorRow('Text Color', 'color', '#ffffff');
          addColorRow('Background Color', 'backgroundColor', '#111827');
          addTextRow('Filter Classes', 'classes', 'person, car (empty = all)');
        } else if (layer.type === 'heatmap') {
          addSliderRow('Opacity', 'opacity', 0.05, 0.95, 0.05, 0.40);
          addSliderRow('Decay Rate', 'decay', 0.80, 0.999, 0.01, 0.98);
          addSelectRow('Colormap', 'colormap', [
            ['jet', 'Jet (Rainbow / Traffic)'],
            ['hot', 'Hot (Red / Yellow)'],
            ['turbo', 'Turbo (Vibrant Spectrum)']
          ], 'jet');
          addTextRow('Filter Classes', 'classes', 'person, car (empty = all)');
        } else if (layer.type === 'vector_arrow') {
          addColorRow('Arrow Color', 'color', '#38bdf8');
          addSliderRow('Thickness', 'thickness', 1, 10, 1, 2, 'px');
          addSliderRow('Scale', 'scale', 0.5, 5.0, 0.1, 1.5);
          addTextRow('Filter Classes', 'classes', 'person, car (empty = all)');
        }

        card.append(cardBody);
        layersList.append(card);
      });
    }

    renderLayerCards();

    // Delete node button at bottom
    const delBtn = document.createElement('button');
    delBtn.className = 'danger-button';
    delBtn.style.marginTop = '24px';
    delBtn.innerHTML = '<svg class="icon-svg icon-sm" viewBox="0 0 24 24"><path d="M3 6h18"/><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"/><path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"/></svg> Delete This Node';
    delBtn.onclick = deleteSelectedNode;
    body.append(delBtn);
  }

  function renderMultiZoneOccupancyInspector(node, body) {
    if (!node.config) node.config = {};
    let rawZones = node.config.zones;
    if (typeof rawZones === 'string') {
      try { rawZones = JSON.parse(rawZones); } catch { rawZones = null; }
    }
    if (!Array.isArray(rawZones) || rawZones.length === 0) {
      rawZones = [
        { id: 'zone_1', name: 'Zona A', capacity: 4, points: '0.15,0.20; 0.45,0.20; 0.45,0.80; 0.15,0.80' },
        { id: 'zone_2', name: 'Zona B', capacity: 2, points: '0.55,0.20; 0.85,0.20; 0.85,0.80; 0.55,0.80' }
      ];
      node.config.zones = rawZones;
    }

    // Title Row
    const titleRow = document.createElement('div');
    titleRow.className = 'inspector-header-row';
    titleRow.innerHTML = `
      <span class="inspector-title-text">Node settings</span>
      <span class="inspector-node-badge" style="background:rgba(56,189,248,0.15); color:#38bdf8;">Multi-Zone Occupancy</span>
    `;
    const titleEl = $('#inspectorTitle');
    if (titleEl) titleEl.replaceChildren(titleRow);

    const subtitle = document.createElement('p');
    subtitle.className = 'inspector-subtitle';
    subtitle.textContent = 'Pemantauan okupansi, kapasitas, dan durasi multi-area real-time.';
    body.append(subtitle);

    // Guide button
    const guideBtn = document.createElement('button');
    guideBtn.type = 'button';
    guideBtn.className = 'inspector-guide-btn';
    guideBtn.innerHTML = `
      <svg class="icon-svg icon-sm" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><path d="M12 16v-4"/><path d="M12 8h.01"/></svg>
      <span>📖 Panduan &amp; Cara Penggunaan Node</span>
    `;
    guideBtn.onclick = () => showNodeGuideModal(node.type);
    body.append(guideBtn);

    // Node Enabled Toggle
    const toggleWrap = document.createElement('div');
    toggleWrap.className = 'inspector-field-row';
    toggleWrap.innerHTML = `
      <span class="inspector-field-label">Enabled</span>
      <label class="switch">
        <input type="checkbox" ${node.enabled !== false ? 'checked' : ''} id="multiZoneEnabledToggle">
        <span class="slider round"></span>
      </label>
    `;
    toggleWrap.querySelector('#multiZoneEnabledToggle').onchange = (e) => {
      node.enabled = e.target.checked;
      markDirty();
      renderCanvas();
    };
    body.append(toggleWrap);

    // Multi-Zone Visual Draw Button
    const drawCard = document.createElement('div');
    drawCard.className = 'multi-zone-inspector-card';
    drawCard.innerHTML = `
      <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
        <span style="font-weight:600; color:var(--text); font-size:13px;">Daftar Area / Zona (${rawZones.length})</span>
      </div>
      <button type="button" class="button primary" id="openMultiZoneEditorBtn" style="width:100%; display:flex; align-items:center; justify-content:center; gap:8px; margin-bottom:12px;">
        <svg class="icon-svg icon-sm" viewBox="0 0 24 24"><polygon points="3 3 21 3 21 21 3 21"/></svg>
        📐 Gambar Poligon Zona di Preview
      </button>
      <div class="multi-zone-list-preview" id="multiZoneListPreview"></div>
    `;
    drawCard.querySelector('#openMultiZoneEditorBtn').onclick = () => startMultiZoneDrawing(node);

    const listContainer = drawCard.querySelector('#multiZoneListPreview');
    rawZones.forEach((z, idx) => {
      const zItem = document.createElement('div');
      zItem.className = 'multi-zone-item-chip';
      zItem.innerHTML = `
        <span class="multi-zone-chip-name">${idx + 1}. ${escapeHtml(z.name || ('Zona ' + (idx + 1)))}</span>
        <span class="multi-zone-chip-cap">Kapasitas: ${z.capacity || 4}</span>
      `;
      listContainer.append(zItem);
    });
    body.append(drawCard);

    // General Parameters
    const paramsCard = document.createElement('div');
    paramsCard.className = 'multi-zone-params-card';
    paramsCard.innerHTML = `
      <div style="font-weight:600; color:var(--text); font-size:13px; margin-bottom:10px;">Pengaturan Umum</div>

      <div class="inspector-field-group">
        <label>Target Kelas Objek (Target Classes)</label>
        <input type="text" class="input" id="mzTargetClasses" value="${escapeHtml(node.config.targetClasses || 'person')}" placeholder="person, car, dll">
      </div>

      <div style="display:grid; grid-template-columns:1fr 1fr; gap:8px; margin-top:8px;">
        <div class="inspector-field-group">
          <label>Konfirmasi Terisi (s)</label>
          <input type="number" class="input" id="mzConfirmSec" value="${node.config.confirmationSeconds ?? 3.0}" min="0" step="0.5">
        </div>
        <div class="inspector-field-group">
          <label>Toleransi Kosong (s)</label>
          <input type="number" class="input" id="mzGraceSec" value="${node.config.graceSeconds ?? 10.0}" min="0" step="1">
        </div>
      </div>

      <div class="inspector-field-group" style="margin-top:8px;">
        <label>Batas Waktu Maksimal / Overstay (menit, 0 = nonaktif)</label>
        <input type="number" class="input" id="mzMaxDwell" value="${node.config.maxDwellMinutes ?? 0.0}" min="0" step="5">
      </div>

      <div style="display:grid; grid-template-columns:1fr 1fr; gap:8px; margin-top:8px;">
        <div class="inspector-field-group">
          <label>Posisi Label &amp; Timer</label>
          <select class="input select" id="mzLabelPosition">
            <option value="center" ${(node.config.labelPosition || 'center') === 'center' ? 'selected' : ''}>🎯 Tengah Area (Center)</option>
            <option value="top" ${node.config.labelPosition === 'top' ? 'selected' : ''}>⬆️ Atas Poligon (Top)</option>
          </select>
        </div>
        <div class="inspector-field-group">
          <label>Gaya &amp; Ukuran Teks</label>
          <select class="input select" id="mzCompactLabel">
            <option value="true" ${node.config.compactLabel !== false ? 'selected' : ''}>✨ Ringkas &amp; Minimalis</option>
            <option value="false" ${node.config.compactLabel === false ? 'selected' : ''}>📋 Detail &amp; Lengkap</option>
          </select>
        </div>
      </div>

      <div style="margin-top:12px; display:flex; flex-direction:column; gap:8px;">
        <label style="display:flex; align-items:center; gap:8px; font-size:12px; color:var(--text);">
          <input type="checkbox" id="mzShowHud" ${node.config.showHudOverlay !== false ? 'checked' : ''}>
          Tampilkan Kartu HUD Meja/Zona di Preview
        </label>
        <label style="display:flex; align-items:center; gap:8px; font-size:12px; color:var(--text);">
          <input type="checkbox" id="mzShowSummary" ${node.config.showSummaryCard !== false ? 'checked' : ''}>
          Tampilkan Kotak Ringkasan Total di Pojok Preview
        </label>
      </div>
    `;

    paramsCard.querySelector('#mzTargetClasses').onchange = (e) => { node.config.targetClasses = e.target.value.trim() || 'person'; markDirty(); };
    paramsCard.querySelector('#mzConfirmSec').onchange = (e) => { node.config.confirmationSeconds = parseFloat(e.target.value) || 0; markDirty(); };
    paramsCard.querySelector('#mzGraceSec').onchange = (e) => { node.config.graceSeconds = parseFloat(e.target.value) || 0; markDirty(); };
    paramsCard.querySelector('#mzMaxDwell').onchange = (e) => { node.config.maxDwellMinutes = parseFloat(e.target.value) || 0; markDirty(); };
    paramsCard.querySelector('#mzLabelPosition').onchange = (e) => { node.config.labelPosition = e.target.value; markDirty(); };
    paramsCard.querySelector('#mzCompactLabel').onchange = (e) => { node.config.compactLabel = e.target.value === 'true'; markDirty(); };
    paramsCard.querySelector('#mzShowHud').onchange = (e) => { node.config.showHudOverlay = e.target.checked; markDirty(); };
    paramsCard.querySelector('#mzShowSummary').onchange = (e) => { node.config.showSummaryCard = e.target.checked; markDirty(); };

    body.append(paramsCard);

    // Delete node button at bottom
    const delBtn = document.createElement('button');
    delBtn.className = 'danger-button';
    delBtn.style.marginTop = '24px';
    delBtn.innerHTML = '<svg class="icon-svg icon-sm" viewBox="0 0 24 24"><path d="M3 6h18"/><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"/><path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"/></svg> Delete This Node';
    delBtn.onclick = deleteSelectedNode;
    body.append(delBtn);
  }

  function renderExportCodeInspector(node, body) {
    $('#inspectorTitle').textContent = 'Export Code';
    const info = document.createElement('p');
    info.className = 'node-description';
    info.textContent = 'Paket menjalankan seluruh workflow aktif secara terpisah. Node ini tidak memproses frame dan tidak memerlukan kabel.';
    body.append(info);
    const guide = document.createElement('button');
    guide.type = 'button';
    guide.className = 'inspector-guide-btn';
    guide.textContent = 'Panduan Export Code';
    guide.onclick = () => showNodeGuideModal(node);
    body.append(guide);
    const config = node.config ||= {};
    for (const [key, label, fallback] of [['packageName', 'Nama paket', state.project?.name || 'workflow'], ['version', 'Versi paket', '1.0.0']]) {
      const row = document.createElement('label');
      row.className = 'field';
      row.textContent = label;
      const input = document.createElement('input');
      input.value = config[key] || (key === 'packageName' ? '' : fallback);
      input.placeholder = fallback;
      input.oninput = () => { config[key] = input.value; markDirty(); };
      row.append(input);
      body.append(row);
    }
    const models = document.createElement('label');
    models.className = 'field-check';
    const include = document.createElement('input');
    include.type = 'checkbox';
    include.checked = config.includeModels === true;
    include.onchange = () => { config.includeModels = include.checked; markDirty(); };
    models.append(include, document.createTextNode(' Sertakan model lokal (pastikan hak distribusi)'));
    body.append(models);
    const result = document.createElement('div');
    result.id = 'exportCodeResult';
    result.className = 'field-help';
    result.textContent = 'Simpan workflow, lalu periksa paket sebelum mengunduh.';
    body.append(result);
    const check = document.createElement('button');
    check.type = 'button';
    check.className = 'button secondary';
    check.textContent = 'Periksa Paket';
    check.onclick = async () => {
      if (state.dirty && !(await save())) return;
      try {
        const data = await api(`/api/projects/${encodeURIComponent(state.project.id)}/export-code/check`, { method: 'POST' });
        const env = data.manifest.environment.map(item => item.name).join(', ') || 'tidak ada';
        result.textContent = `Siap dibangun. ${data.manifest.models.length} referensi model; environment: ${env}. ${data.manifest.warnings.join(' ')}`;
        toast('Paket siap dibangun');
      } catch (error) {
        result.textContent = `Perlu tindakan: ${error.message}`;
        toast(error.message, true);
      }
    };
    body.append(check);
    const build = document.createElement('button');
    build.type = 'button';
    build.className = 'button primary';
    build.style.marginLeft = '8px';
    build.textContent = 'Build & Download ZIP';
    build.onclick = async () => {
      if (state.dirty && !(await save())) return;
      build.disabled = true;
      result.textContent = 'Membangun paket…';
      try {
        const response = await fetch(`/api/projects/${encodeURIComponent(state.project.id)}/export-code`, { method: 'POST' });
        if (!response.ok) {
          const error = await response.json();
          throw new Error(error.detail || `Build gagal (${response.status})`);
        }
        const blob = await response.blob();
        const filename = response.headers.get('content-disposition')?.match(/filename="?([^";]+)"?/)?.[1] || 'workflow.zip';
        const link = document.createElement('a');
        link.href = URL.createObjectURL(blob);
        link.download = filename;
        link.click();
        setTimeout(() => URL.revokeObjectURL(link.href), 1000);
        result.textContent = `ZIP berhasil diunduh: ${filename}`;
        toast('Paket Python berhasil diunduh');
      } catch (error) {
        result.textContent = `Build gagal: ${error.message}`;
        toast(error.message, true);
      } finally {
        build.disabled = false;
      }
    };
    body.append(build);
    const remove = document.createElement('button');
    remove.type = 'button';
    remove.className = 'danger-button';
    remove.textContent = 'Delete This Node';
    remove.onclick = deleteSelectedNode;
    body.append(remove);
  }

  function renderInspector() {
    const n = nodeFor(state.selected);
    const body = $('#inspectorBody');
    if (!body) return;
    body.replaceChildren();
    if (n?.type !== 'draw_text') _drawTextEditNodeId = null;

    if (!n) {
      $('#inspectorTitle').textContent = 'Nothing selected';
      const empty = document.createElement('div');
      empty.className = 'inspector-empty';
      empty.innerHTML = `
        <svg class="icon-svg icon-lg" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><path d="m4.9 4.9 14.2 14.2"/></svg>
        <p>Select a node on the canvas to edit its configuration.</p>
      `;
      body.append(empty);
      syncDrawTextPreviewEditor();
      return;
    }

    if (n.type === 'export_code') {
      renderExportCodeInspector(n, body);
      return;
    }

    if (n.type === 'overlay_annotate') {
      renderOverlayAnnotateInspector(n, body);
      return;
    }

    if (n.type === 'multi_zone_occupancy') {
      renderMultiZoneOccupancyInspector(n, body);
      return;
    }

    const cat = categoryFor(n.type);
    $('#inspectorTitle').innerHTML = `
      <span style="display:inline-flex;align-items:center;gap:8px">
        ${getIcon(n.type, 'icon-md')} ${n.title || titleFor(n.type)}
      </span>
    `;

    const desc = document.createElement('p');
    desc.className = 'node-description';
    desc.textContent = state.catalog[n.type]?.subtitle || n.type;
    body.append(desc);

    const guideBtn = document.createElement('button');
    guideBtn.type = 'button';
    guideBtn.className = 'button secondary';
    guideBtn.style.width = '100%';
    guideBtn.style.display = 'flex';
    guideBtn.className = 'inspector-guide-btn';
    guideBtn.innerHTML = `
      <svg class="icon-svg icon-sm" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><path d="M12 16v-4"/><path d="M12 8h.01"/></svg>
      <span>📘 Panduan &amp; Cara Penggunaan Node</span>
    `;
    guideBtn.onclick = () => showNodeGuideModal(n);
    body.append(guideBtn);

    const isNodeEnabled = n.enabled !== false;
    const activeRow = document.createElement('div');
    activeRow.className = `inspector-active-row ${isNodeEnabled ? 'is-active' : 'is-bypassed'}`;
    activeRow.innerHTML = `
      <div class="active-row-label">
        <strong style="color: ${isNodeEnabled ? '#065f46' : '#b45309'}; font-weight:800; font-size:13.5px;">${isNodeEnabled ? '🟢 Node Aktif' : '🟠 Node Bypassed'}</strong>
        <small style="color: ${isNodeEnabled ? '#047857' : '#92400e'}; font-weight:600; font-size:11px;">${isNodeEnabled ? 'Aktif memproses data' : 'Bypass / Pass-Through (Data diteruskan)'}</small>
      </div>
    `;
    const activeSwitch = document.createElement('label');
    activeSwitch.className = 'node-toggle-switch';
    const activeCheck = document.createElement('input');
    activeCheck.type = 'checkbox';
    activeCheck.checked = isNodeEnabled;
    activeCheck.onchange = (e) => {
      n.enabled = e.target.checked;
      markDirty();
      renderCanvas();
      renderInspector();
      liveUpdateWorkflow();
    };
    const activeSlider = document.createElement('span');
    activeSlider.className = 'toggle-slider';
    activeSwitch.append(activeCheck, activeSlider);
    activeRow.append(activeSwitch);
    body.append(activeRow);

    // Tab buttons header
    const tabNav = document.createElement('div');
    tabNav.className = 'inspector-tabs';

    const basicTabBtn = document.createElement('button');
    basicTabBtn.className = `inspector-tab-btn ${state.inspectorTab === 'basic' ? 'active' : ''}`;
    basicTabBtn.innerHTML = '<svg class="icon-svg icon-sm" viewBox="0 0 24 24"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg> Basic Settings';
    basicTabBtn.onclick = () => {
      state.inspectorTab = 'basic';
      renderInspector();
    };

    const advTabBtn = document.createElement('button');
    advTabBtn.className = `inspector-tab-btn ${state.inspectorTab === 'advanced' ? 'active' : ''}`;
    advTabBtn.innerHTML = '<svg class="icon-svg icon-sm" viewBox="0 0 24 24"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg> Advanced & GPU';
    advTabBtn.onclick = () => {
      state.inspectorTab = 'advanced';
      renderInspector();
    };

    const logsTabBtn = document.createElement('button');
    logsTabBtn.className = `inspector-tab-btn ${state.inspectorTab === 'logs' ? 'active' : ''}`;
    logsTabBtn.innerHTML = '<svg class="icon-svg icon-sm" viewBox="0 0 24 24"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/></svg> Data &amp; Logs';
    logsTabBtn.onclick = () => {
      state.inspectorTab = 'logs';
      renderInspector();
    };

    tabNav.append(basicTabBtn, advTabBtn, logsTabBtn);
    body.append(tabNav);

    // Section container
    const section = document.createElement('div');
    section.className = 'settings-section';

    // Ensure customModelPath and customClasses exist if custom engine is selected
    if (['detector', 'segmenter', 'classifier'].includes(n.type)) {
      if (!n.config) n.config = {};
      const eng = n.config.engine || (n.type === 'classifier' ? 'convnext' : 'rfdetr');
      if (['ultralytics_yolo', 'yolo_world', 'roboflow_universe', 'onnx_custom', 'tflite', 'tensorflow_keras', 'custom_auto'].includes(eng)) {
        if (n.config.modelPath === undefined) n.config.modelPath = n.config.customModelPath || (eng === 'onnx_custom' ? n.config.rfdetrOnnxModel : n.config.rfdetrCheckpoint) || n.config.convnextCheckpoint || '';
        if (n.config.customModelPath === undefined) n.config.customModelPath = '';
        if (n.config.customClasses === undefined) n.config.customClasses = '';
        if (eng === 'roboflow_universe' && n.config.roboflowApiKey === undefined) n.config.roboflowApiKey = '';
      }
    }

    if (state.inspectorTab === 'basic') {
      // Title
      section.append(field('Node Label', n.title || titleFor(n.type), 'text', value => {
        n.title = value;
        markDirty();
        renderCanvas();
      }));

      // Enabled checkbox
      const enabledWrap = document.createElement('label');
      enabledWrap.className = 'field-check';
      const toggle = document.createElement('input');
      toggle.type = 'checkbox';
      toggle.checked = n.enabled !== false;
      toggle.onchange = () => {
        n.enabled = toggle.checked;
        markDirty();
        renderCanvas();
        renderInspector();
        liveUpdateWorkflow();
      };
      enabledWrap.append(toggle, document.createTextNode('Enable this node in execution graph'));
      section.append(enabledWrap);

      if (n.type === 'face_tracker') {
        const shortcutBox = document.createElement('div');
        shortcutBox.className = 'face-registry-shortcut-card';
        shortcutBox.style.cssText = 'background: linear-gradient(135deg, rgba(5,150,105,0.08), rgba(6,182,212,0.08)); border: 1px solid rgba(5,150,105,0.3); border-radius: 8px; padding: 12px; margin: 0 0 14px 0;';
        shortcutBox.innerHTML = `
          <div style="font-weight: 700; font-size: 12px; color: #047857; margin-bottom: 4px; display: flex; align-items: center; gap: 6px;">
            <svg class="icon-svg icon-sm" viewBox="0 0 24 24"><circle cx="12" cy="7" r="4"/><path d="M5.5 21a8.38 8.38 0 0 1 13 0"/></svg>
            <span>Database Wajah Terdaftar (Known Faces)</span>
          </div>
          <p style="font-size: 11px; color: #475569; margin: 0 0 10px 0; line-height: 1.4;">
            Node ini mencocokkan wajah yang terdeteksi dengan profil wajah di Galeri Wajah. Anda dapat mendaftarkan foto & nama karyawan/tamu.
          </p>
          <button type="button" class="button primary" id="openFaceRegistryFromNode" style="width: 100%; height: 32px; font-size: 11.5px; font-weight: 600; background: #059669; justify-content: center; display: flex; align-items: center; gap: 6px; border: none; cursor: pointer; border-radius: 6px; color: #fff;">
            <span>👥 Kelola Database Wajah Terdaftar →</span>
          </button>
        `;
        shortcutBox.querySelector('#openFaceRegistryFromNode').onclick = () => {
          switchProjectRailTab('faces');
        };
        section.append(shortcutBox);
      }

      // Primary / Basic config fields (filtered conditionally)
      Object.entries(n.config || {}).forEach(([key, value]) => {
        if (!ADVANCED_KEYS.has(key) && shouldShowField(n, key)) {
          section.append(createSmartConfigField(n, key, value));
        }
      });
    } else if (state.inspectorTab === 'logs') {
      renderInspectorTelemetryLogs(n, section);
    } else {
      // Advanced / Performance tab
      const advEntries = Object.entries(n.config || {}).filter(([key]) => ADVANCED_KEYS.has(key));
      if (!advEntries.length) {
        const noAdv = document.createElement('p');
        noAdv.className = 'field-help';
        noAdv.textContent = 'This node uses standard pipeline execution and does not have specialized hardware runtime overrides.';
        section.append(noAdv);
      } else {
        advEntries.forEach(([key, value]) => {
          if (shouldShowField(n, key)) {
            section.append(createSmartConfigField(n, key, value));
          }
        });
      }
    }

    body.append(section);

    if (n.type === 'draw_text') {
      const editHelp = document.createElement('p');
      editHelp.className = 'field-help';
      editHelp.textContent = 'Contoh variabel: {detection.count}, {detection.class}, {detection.confidence}, {track.id}. Untuk dua teks bersyarat, gunakan kondisi yang sama pada dua node If / Else (contoh Jumlah Objek > 1), lalu atur Pass When menjadi true pada cabang IF dan false pada cabang ELSE.';
      body.append(editHelp);
      const editBtn = document.createElement('button');
      editBtn.type = 'button';
      editBtn.className = 'button secondary draw-text-edit-btn';
      editBtn.textContent = _drawTextEditNodeId === n.id ? 'Selesai Atur di Preview' : 'Atur Posisi & Ukuran di Preview';
      editBtn.onclick = () => {
        if (_drawTextEditNodeId === n.id) {
          _drawTextEditNodeId = null;
        } else if (!$('#previewImage')?.naturalWidth) {
          toast('Jalankan workflow sampai preview menampilkan frame terlebih dahulu.', true);
          return;
        } else {
          _drawTextEditNodeId = n.id;
          toast('Geser teks untuk mengatur posisi; tarik titik di sudut untuk mengubah ukuran.');
        }
        renderInspector();
      };
      body.append(editBtn);
    }

    if (n.type === 'if_else') {
      const branchHelp = document.createElement('p');
      branchHelp.className = 'field-help';
      branchHelp.textContent = 'Untuk pasangan IF / ELSE yang menuju Draw Text berbeda, samakan Metrik, Operator, dan Nilainya pada kedua node. Bedakan hanya Pass When: true untuk IF, false untuk ELSE. Contoh: Jumlah Objek > 1.';
      body.append(branchHelp);
    }

    if (n.type === 'frame_sampler') {
      const statsCard = document.createElement('div');
      statsCard.id = `frame-sampler-stats-${n.id}`;
      statsCard.style.cssText = 'margin-top:12px;padding:12px;border:1px solid var(--border,#334155);border-radius:8px;background:var(--bg-card,#1e293b);font-size:11px;';
      statsCard.innerHTML = `
        <div style="font-weight:600;font-size:12px;margin-bottom:8px;">Runtime status</div>
        <div data-stat="waiting" style="color:var(--text-muted,#94a3b8);margin-bottom:8px;">Menunggu runtime...</div>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:6px;color:var(--text-muted,#94a3b8);">
          <span>Input FPS <b data-stat="inputFps" style="color:var(--text,#f1f5f9)">—</b></span>
          <span>Output FPS <b data-stat="outputFps" style="color:var(--text,#f1f5f9)">—</b></span>
          <span>Input frames <b data-stat="inputFrames" style="color:var(--text,#f1f5f9)">—</b></span>
          <span>Passed frames <b data-stat="outputFrames" style="color:var(--text,#f1f5f9)">—</b></span>
          <span>Dropped frames <b data-stat="droppedFrames" style="color:var(--text,#f1f5f9)">—</b></span>
        </div>`;
      body.append(statsCard);
      updateFrameSamplerStatus(n.id);
    }

    if (n.type === 'python_script') {
      const card = document.createElement('div');
      card.id = `python-script-status-${n.id}`;
      card.style.cssText = 'margin-top:12px;padding:12px;border:1px solid var(--border,#334155);border-radius:8px;background:var(--bg-card,#1e293b);font-size:11px;';
      card.innerHTML = '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px"><strong>Python Script Runtime</strong><span data-stat="status" style="font-weight:700;color:var(--text-muted,#94a3b8)">IDLE</span></div><div data-stat="metrics" style="color:var(--text-muted,#94a3b8)"></div><pre data-stat="logs" style="white-space:pre-wrap;max-height:100px;overflow:auto;margin:8px 0 0;color:var(--text-muted,#94a3b8)"></pre>';
      body.append(card);
      updatePythonScriptStatus(n.id);
    }

    // Node Specific Action Buttons
    if (n.type === 'if_else' || n.type === 'compare_value') {
      const isElse = String(n.config.passWhen).toLowerCase() === 'false';
      const branchCard = document.createElement('div');
      branchCard.style.background = 'var(--bg-card, #1e293b)';
      branchCard.style.border = '1px solid var(--border, #334155)';
      branchCard.style.borderRadius = '8px';
      branchCard.style.padding = '12px';
      branchCard.style.marginBottom = '14px';

      const statusRow = document.createElement('div');
      statusRow.style.display = 'flex';
      statusRow.style.justifyContent = 'space-between';
      statusRow.style.alignItems = 'center';
      statusRow.style.marginBottom = '8px';

      const statusTitle = document.createElement('span');
      statusTitle.style.fontWeight = '600';
      statusTitle.style.fontSize = '12px';
      statusTitle.textContent = 'Jalur Percabangan';

      const branchBadge = document.createElement('span');
      branchBadge.style.fontWeight = '700';
      branchBadge.style.fontSize = '11px';
      branchBadge.style.padding = '3px 8px';
      branchBadge.style.borderRadius = '12px';
      branchBadge.style.backgroundColor = isElse ? 'rgba(239, 68, 68, 0.2)' : 'rgba(34, 197, 94, 0.2)';
      branchBadge.style.color = isElse ? '#ef4444' : '#22c55e';
      branchBadge.style.border = `1px solid ${isElse ? '#ef4444' : '#22c55e'}`;
      branchBadge.textContent = isElse ? '🔴 CABANG ELSE (Salah)' : '🟢 CABANG IF (Benar)';

      statusRow.append(statusTitle, branchBadge);

      const desc = document.createElement('div');
      desc.style.fontSize = '11px';
      desc.style.color = 'var(--text-muted, #94a3b8)';
      desc.style.lineHeight = '1.4';
      desc.innerHTML = `Data akan diteruskan ke node selanjutnya <b>hanya jika kondisi bernilai ${isElse ? 'SALAH (False)' : 'BENAR (True)'}</b>.`;

      branchCard.append(statusRow, desc);

      const guideBtn = document.createElement('button');
      guideBtn.type = 'button';
      guideBtn.className = 'button secondary';
      guideBtn.style.width = '100%';
      guideBtn.style.marginTop = '10px';
      guideBtn.style.display = 'flex';
      guideBtn.style.alignItems = 'center';
      guideBtn.style.justifyContent = 'center';
      guideBtn.style.gap = '6px';
      guideBtn.style.fontSize = '12px';
      guideBtn.innerHTML = '📘 Panduan & Contoh Penerapan Percabangan';
      guideBtn.onclick = () => showIfElseGuideModal(n);
      branchCard.append(guideBtn);

      body.append(branchCard);
    } else if (n.type === 'crop' || n.type === 'roi_filter') {
      const roiBtn = document.createElement('button');
      roiBtn.className = 'button ghost';
      roiBtn.style.width = '100%';
      roiBtn.style.marginBottom = '8px';
      roiBtn.innerHTML = '<svg class="icon-svg icon-sm" viewBox="0 0 24 24"><rect width="18" height="18" x="3" y="3" rx="2" stroke-dasharray="4"/></svg> 📐 Draw ROI on Preview';
      roiBtn.onclick = () => startRoiDrawing(n);
      body.append(roiBtn);
    } else if (n.type === 'line_counter') {
      const lines = getOrCreateNodeLines(n);
      const container = document.createElement('div');
      container.style.display = 'flex';
      container.style.flexDirection = 'column';
      container.style.gap = '10px';
      container.style.marginBottom = '14px';

      // Header row with Add Line button
      const headRow = document.createElement('div');
      headRow.style.display = 'flex';
      headRow.style.alignItems = 'center';
      headRow.style.justifyContent = 'space-between';
      headRow.innerHTML = `<span style="font-weight:600; font-size:12px; color:var(--text, #f1f5f9);">Daftar Garis (${lines.length})</span>`;

      const addBtn = document.createElement('button');
      addBtn.type = 'button';
      addBtn.className = 'button secondary';
      addBtn.style.padding = '4px 8px';
      addBtn.style.fontSize = '11px';
      addBtn.innerHTML = '➕ Tambah Garis';
      addBtn.onclick = () => addNewLine(n);
      headRow.appendChild(addBtn);
      container.appendChild(headRow);

      // Global actions bar
      const globRow = document.createElement('div');
      globRow.style.display = 'flex';
      globRow.style.gap = '6px';

      const resetAllBtn = document.createElement('button');
      resetAllBtn.type = 'button';
      resetAllBtn.className = 'button ghost';
      resetAllBtn.style.flex = '1';
      resetAllBtn.style.padding = '4px 6px';
      resetAllBtn.style.fontSize = '11px';
      resetAllBtn.innerHTML = '0️⃣ Reset Semua';
      resetAllBtn.title = 'Reset hitungan semua garis ke 0';
      resetAllBtn.onclick = () => resetLineCounts(n);

      const clearAllBtn = document.createElement('button');
      clearAllBtn.type = 'button';
      clearAllBtn.className = 'button ghost';
      clearAllBtn.style.flex = '1';
      clearAllBtn.style.padding = '4px 6px';
      clearAllBtn.style.fontSize = '11px';
      clearAllBtn.style.color = '#ef4444';
      clearAllBtn.innerHTML = '🗑️ Hapus Semua';
      clearAllBtn.title = 'Hapus / kosongkan semua gambar garis';
      clearAllBtn.onclick = () => clearAllLinesDrawing(n);

      globRow.append(resetAllBtn, clearAllBtn);
      container.appendChild(globRow);

      // Render each line card
      lines.forEach((line, idx) => {
        const card = document.createElement('div');
        card.style.background = 'rgba(255, 255, 255, 0.03)';
        card.style.border = '1px solid rgba(255, 255, 255, 0.08)';
        card.style.borderLeft = `4px solid ${line.lineColor || '#22c55e'}`;
        card.style.borderRadius = '6px';
        card.style.padding = '8px';
        card.style.display = 'flex';
        card.style.flexDirection = 'column';
        card.style.gap = '6px';

        // Card header: name input + color picker + delete line button
        const cardHead = document.createElement('div');
        cardHead.style.display = 'flex';
        cardHead.style.alignItems = 'center';
        cardHead.style.gap = '6px';

        const nameInput = document.createElement('input');
        nameInput.type = 'text';
        nameInput.value = line.name || `Line ${idx + 1}`;
        nameInput.style.flex = '1';
        nameInput.style.padding = '3px 6px';
        nameInput.style.fontSize = '12px';
        nameInput.style.fontWeight = '600';
        nameInput.style.borderRadius = '4px';
        nameInput.style.border = '1px solid rgba(255,255,255,0.12)';
        nameInput.style.background = 'rgba(0,0,0,0.2)';
        nameInput.style.color = '#fff';
        nameInput.onchange = async () => {
          line.name = nameInput.value.trim() || `Line ${idx + 1}`;
          markDirty();
          await save();
          await liveUpdateWorkflow();
        };

        const colorInput = document.createElement('input');
        colorInput.type = 'color';
        colorInput.value = line.lineColor || '#22c55e';
        colorInput.style.width = '24px';
        colorInput.style.height = '24px';
        colorInput.style.padding = '0';
        colorInput.style.border = 'none';
        colorInput.style.background = 'transparent';
        colorInput.style.cursor = 'pointer';
        colorInput.title = 'Ubah warna garis';
        colorInput.onchange = async () => {
          line.lineColor = colorInput.value;
          card.style.borderLeftColor = line.lineColor;
          markDirty();
          await save();
          await liveUpdateWorkflow();
        };

        cardHead.append(nameInput, colorInput);

        if (lines.length > 1) {
          const delBtn = document.createElement('button');
          delBtn.type = 'button';
          delBtn.className = 'button ghost';
          delBtn.style.padding = '2px 6px';
          delBtn.style.color = '#ef4444';
          delBtn.title = 'Hapus garis ini dari daftar';
          delBtn.innerHTML = '❌';
          delBtn.onclick = () => removeLine(n, idx);
          cardHead.appendChild(delBtn);
        }
        card.appendChild(cardHead);

        // Status row
        const statusRow = document.createElement('div');
        statusRow.style.fontSize = '11px';
        statusRow.style.display = 'flex';
        statusRow.style.justifyContent = 'space-between';
        statusRow.style.alignItems = 'center';

        const hasCoords = line.startPoint && line.endPoint && line.startPoint !== '0,0';
        if (hasCoords) {
          statusRow.innerHTML = `<span style="color:#22c55e;">🟢 Terpasang (${line.startPoint} ➔ ${line.endPoint})</span>`;
        } else {
          statusRow.innerHTML = `<span style="color:#94a3b8;">⚪ Kosong (Belum Digambar)</span>`;
        }

        const dirBadge = document.createElement('span');
        dirBadge.style.fontSize = '10px';
        dirBadge.style.padding = '1px 5px';
        dirBadge.style.borderRadius = '3px';
        dirBadge.style.background = line.invertDirection ? 'rgba(239, 68, 68, 0.2)' : 'rgba(34, 197, 94, 0.2)';
        dirBadge.style.color = line.invertDirection ? '#f87171' : '#4ade80';
        dirBadge.textContent = line.invertDirection ? 'Tukar: OUT ➔ IN' : 'Normal: IN ➔ OUT';
        statusRow.appendChild(dirBadge);
        card.appendChild(statusRow);

        // Action button row 1: Draw / Redraw
        const drawBtn = document.createElement('button');
        drawBtn.type = 'button';
        drawBtn.className = 'button ghost';
        drawBtn.style.width = '100%';
        drawBtn.style.fontSize = '11px';
        drawBtn.style.padding = '5px 8px';
        drawBtn.innerHTML = `<svg class="icon-svg icon-sm" viewBox="0 0 24 24"><line x1="2" y1="12" x2="22" y2="12"/><polyline points="8 8 12 4 16 8"/><polyline points="8 16 12 20 16 16"/></svg> ✏️ ${hasCoords ? 'Gambar Ulang / Revisi Garis' : 'Gambar Garis di Preview'}`;
        drawBtn.onclick = () => startLineDrawing(n, idx);
        card.appendChild(drawBtn);

        // Action button row 2: Swap direction + Reset + Clear line
        const btnRow = document.createElement('div');
        btnRow.style.display = 'flex';
        btnRow.style.gap = '4px';

        const swapBtn = document.createElement('button');
        swapBtn.type = 'button';
        swapBtn.className = 'button ghost';
        swapBtn.style.flex = '1';
        swapBtn.style.fontSize = '11px';
        swapBtn.style.padding = '4px 6px';
        swapBtn.title = 'Tukar arah IN ↔ OUT untuk garis ini';
        swapBtn.innerHTML = '🔄 Tukar Arah';
        swapBtn.onclick = () => swapLineDirection(n, idx);

        const rstBtn = document.createElement('button');
        rstBtn.type = 'button';
        rstBtn.className = 'button ghost';
        rstBtn.style.flex = '1';
        rstBtn.style.fontSize = '11px';
        rstBtn.style.padding = '4px 6px';
        rstBtn.title = 'Reset hitungan garis ini ke 0';
        rstBtn.innerHTML = '0️⃣ Reset';
        rstBtn.onclick = () => resetLineCounts(n, line.id);

        const clrBtn = document.createElement('button');
        clrBtn.type = 'button';
        clrBtn.className = 'button ghost';
        clrBtn.style.flex = '1';
        clrBtn.style.fontSize = '11px';
        clrBtn.style.padding = '4px 6px';
        clrBtn.style.color = '#ef4444';
        clrBtn.title = 'Hapus gambar garis ini (kosongkan)';
        clrBtn.innerHTML = '🗑️ Hapus';
        clrBtn.onclick = () => clearLineDrawing(n, idx);

        btnRow.append(swapBtn, rstBtn, clrBtn);
        card.appendChild(btnRow);

        container.appendChild(card);
      });

      body.append(container);
    } else if (['dwell_time', 'zone_activity_timer', 'zone_exit_event'].includes(n.type)) {
      const zoneBtn = document.createElement('button');
      zoneBtn.className = 'button ghost';
      zoneBtn.style.width = '100%';
      zoneBtn.style.marginBottom = '8px';
      zoneBtn.innerHTML = '<svg class="icon-svg icon-sm" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg> ✏️ Draw Zone on Preview';
      zoneBtn.onclick = () => startPolygonZoneDrawing(n);
      body.append(zoneBtn);
    } else if (n.type === 'database_output') {
      const dbActions = document.createElement('div');
      dbActions.style.display = 'flex';
      dbActions.style.gap = '8px';
      dbActions.style.marginBottom = '8px';

      const exportBtn = document.createElement('button');
      exportBtn.className = 'button ghost';
      exportBtn.style.flex = '1';
      exportBtn.innerHTML = '<svg class="icon-svg icon-sm" viewBox="0 0 24 24"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg> Export CSV';
      exportBtn.onclick = () => window.open('/api/database/export?table=detections');

      const viewBtn = document.createElement('button');
      viewBtn.className = 'button ghost';
      viewBtn.style.flex = '1';
      viewBtn.innerHTML = '<svg class="icon-svg icon-sm" viewBox="0 0 24 24"><ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/></svg> View Logs';
      viewBtn.onclick = showDatabaseLogsModal;

      dbActions.append(exportBtn, viewBtn);
      body.append(dbActions);
    }

    // Delete node button
    const delBtn = document.createElement('button');
    delBtn.className = 'danger-button';
    delBtn.innerHTML = '<svg class="icon-svg icon-sm" viewBox="0 0 24 24"><path d="M3 6h18"/><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"/><path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"/></svg> Delete This Node';
    delBtn.onclick = deleteSelectedNode;
    body.append(delBtn);
    syncDrawTextPreviewEditor();
  }

  // Determine conditional visibility for clean forms
  function shouldShowField(node, key) {
    const cfg = node.config || {};
    // Input node conditional visibility
    if (node.type === 'input') {
      const src = cfg.sourceType || 'camera';
      if (src === 'youtube') {
        return ['sourceType', 'youtubeUrl', 'youtubeQuality', 'loop', 'autoReconnect', 'frameQueueSize', 'dropFrames', 'asyncPreview'].includes(key);
      }
      if (src === 'camera') {
        return !['filePath', 'loop', 'youtubeUrl', 'youtubeQuality', 'autoReconnect', 'dahengIdentifier', 'dahengExposureUs', 'dahengGain', 'dahengTimeoutMs', 'dahengFrameRate', 'dahengOpenMode'].includes(key);
      }
      if (src === 'image') {
        return !['source', 'loop', 'youtubeUrl', 'youtubeQuality', 'autoReconnect', 'dahengIdentifier', 'dahengExposureUs', 'dahengGain', 'dahengTimeoutMs', 'dahengFrameRate', 'dahengOpenMode'].includes(key);
      }
      if (src === 'video' || src === 'file') {
        return !['source', 'youtubeUrl', 'youtubeQuality', 'dahengIdentifier', 'dahengExposureUs', 'dahengGain', 'dahengTimeoutMs', 'dahengFrameRate', 'dahengOpenMode'].includes(key);
      }
      if (src === 'daheng') {
        return !['source', 'filePath', 'loop', 'youtubeUrl', 'youtubeQuality', 'autoReconnect'].includes(key);
      }
    }

    // Line Counter field visibility (internal fields handled in multi-line UI)
    if (node.type === 'line_counter') {
      return !['lines', 'startPoint', 'endPoint', 'lineColor', 'lineWidth', 'inLabel', 'outLabel', 'invertDirection', 'countMode'].includes(key);
    }

    // If/Else & Compare Value visibility (hide classes unless metric is class_count)
    if (node.type === 'if_else' || node.type === 'compare_value') {
      if (key === 'classes' && cfg.metric !== 'class_count') {
        return false;
      }
    }

    // Detector / Segmenter / Classifier engine visibility
    if (['detector', 'segmenter', 'classifier'].includes(node.type)) {
      const eng = cfg.engine || (node.type === 'classifier' ? 'convnext' : 'rfdetr');
      if (eng === 'rfdetr') {
        return !['rfdetrOnnxModel', 'rfdetrOnnxClasses', 'rfdetrTensorRTEngine', 'rfdetrTensorRTClasses', 'rfdetrTensorRTCudaGraph', 'rfdetrTensorRTProcess', 'customModelPath', 'modelPath', 'customClasses', 'samCheckpoint', 'concepts', 'convnextModel', 'convnextCheckpoint', 'convnextClasses', 'convnextImageSize', 'convnextHalfPrecision', 'topK'].includes(key);
      }
      if (eng === 'rfdetr_onnx') {
        return !['rfdetrModel', 'rfdetrCheckpoint', 'rfdetrHalfPrecision', 'rfdetrTensorRTEngine', 'rfdetrTensorRTClasses', 'rfdetrTensorRTCudaGraph', 'rfdetrTensorRTProcess', 'customModelPath', 'modelPath', 'customClasses', 'samCheckpoint', 'concepts', 'convnextModel', 'convnextCheckpoint', 'convnextClasses', 'convnextImageSize', 'convnextHalfPrecision', 'topK'].includes(key);
      }
      if (eng === 'rfdetr_tensorrt') {
        return !['rfdetrModel', 'rfdetrCheckpoint', 'rfdetrOnnxModel', 'rfdetrOnnxClasses', 'customModelPath', 'modelPath', 'customClasses', 'samCheckpoint', 'concepts', 'convnextModel', 'convnextCheckpoint', 'convnextClasses', 'convnextImageSize', 'convnextHalfPrecision', 'topK'].includes(key);
      }
      if (eng === 'sam3') {
        return !['rfdetrModel', 'rfdetrCheckpoint', 'rfdetrHalfPrecision', 'rfdetrOnnxModel', 'rfdetrOnnxClasses', 'rfdetrTensorRTEngine', 'rfdetrTensorRTClasses', 'rfdetrTensorRTCudaGraph', 'rfdetrTensorRTProcess', 'customModelPath', 'modelPath', 'customClasses', 'convnextModel', 'convnextCheckpoint', 'convnextClasses', 'convnextImageSize', 'convnextHalfPrecision', 'topK'].includes(key);
      }
      if (eng === 'convnext') {
        return !['rfdetrModel', 'rfdetrCheckpoint', 'rfdetrHalfPrecision', 'rfdetrOnnxModel', 'rfdetrOnnxClasses', 'rfdetrTensorRTEngine', 'rfdetrTensorRTClasses', 'rfdetrTensorRTCudaGraph', 'rfdetrTensorRTProcess', 'customModelPath', 'modelPath', 'customClasses', 'samCheckpoint', 'concepts'].includes(key);
      }
      if (eng === 'yolo_world') {
        return ['engine', 'customClasses', 'threshold', 'iouThreshold', 'device', 'modelPath', 'detectEveryNFrames', 'batchSize'].includes(key);
      }
      if (eng === 'roboflow_universe') {
        return ['engine', 'modelPath', 'roboflowApiKey', 'classes', 'threshold', 'iouThreshold', 'detectEveryNFrames', 'batchSize'].includes(key);
      }
      if (['ultralytics_yolo', 'onnx_custom', 'tflite', 'tensorflow_keras', 'custom_auto'].includes(eng)) {
        return !['rfdetrModel', 'rfdetrCheckpoint', 'rfdetrHalfPrecision', 'rfdetrOnnxModel', 'rfdetrOnnxClasses', 'rfdetrTensorRTEngine', 'rfdetrTensorRTClasses', 'rfdetrTensorRTCudaGraph', 'rfdetrTensorRTProcess', 'convnextModel', 'convnextCheckpoint', 'convnextClasses', 'convnextImageSize', 'convnextHalfPrecision', 'samCheckpoint', 'concepts', 'customModelPath', 'roboflowApiKey'].includes(key);
      }
    }

    // Tracker algorithm visibility
    if (node.type === 'tracker') {
      const algo = cfg.algorithm || 'bytetrack';
      if (key === 'trackerConfigVersion') return false;
      if (algo === 'bytetrack') {
        if (key.startsWith('botSort') || key.startsWith('ocSort')) return false;
      } else if (algo === 'botsort' || algo === 'cbiou') {
        if (key.startsWith('ocSort')) return false;
        if (key === 'matchThreshold') return false;
        if (algo === 'cbiou' && ['botSortGmc', 'botSortCmcMethod', 'botSortCmcDownscale'].includes(key)) return false;
      } else if (algo === 'ocsort') {
        if (key.startsWith('botSort')) return false;
      }
    }

    // Brightness / Contrast CLAHE visibility
    if (node.type === 'brightness_contrast') {
      if (!cfg.useClahe && ['autoLowLight', 'lowLightThreshold', 'clipLimit', 'tileGridSize'].includes(key)) {
        return false;
      }
      if (!cfg.autoLowLight && key === 'lowLightThreshold') {
        return false;
      }
    }

    // Detection Crop square padColor visibility
    if (node.type === 'detection_crop') {
      if (!cfg.square && key === 'padColor') return false;
    }

    // IP Camera watchdog visibility
    if (node.type === 'ip_camera') {
      if (!cfg.detectFreeze && key === 'freezeThresholdSeconds') return false;
      if (!cfg.detectTamper && ['tamperDarkThreshold', 'tamperBrightThreshold'].includes(key)) return false;
    }

    return true;
  }

  function field(label, value, type, change) {
    const wrap = document.createElement('div');
    wrap.className = 'field';
    const l = document.createElement('label');
    l.textContent = label;
    const input = document.createElement('input');
    input.type = type;
    input.value = value ?? '';
    input.onchange = () => change(input.value);
    wrap.append(l, input);
    return wrap;
  }

  async function inspectAndApplyModel(node, modelPath) {
    if (!node || !modelPath || !['detector', 'segmenter', 'classifier'].includes(node.type)) return;
    if (node.config && (node.config.engine === 'roboflow_universe' || node.config.engine === 'yolo_world')) return;
    if (typeof modelPath === 'string' && modelPath.includes('/') && !modelPath.includes('\\') && !modelPath.endsWith('.pt') && !modelPath.endsWith('.onnx')) return;
    try {
      const data = await api(`/api/models/inspect?path=${encodeURIComponent(modelPath)}`);
      if (data && data.engine) {
        node.config.engine = data.engine;
        node.config.customModelPath = data.path;
        node.config.modelPath = data.path;
        node.config.customClasses = (data.classes || []).join(', ');
        node.config.classes = '';
        markDirty();
        renderInspector();
        toast(`Configured ${data.name}: ${data.engine} (${data.classesCount || 0} classes)${data.classesCount ? '' : '. Label tidak tersimpan di model; isi Custom Classes.'}`);
      }
    } catch (err) {
      toast('Model tidak dapat dimuat: ' + err.message, true);
    }
  }

  const FIELD_BOUNDS = {
    // 0.0 - 1.0 Normalized threshold & ratios
    threshold: { min: 0.0, max: 1.0, step: 0.01, isSlider: true, unit: '' },
    confidence: { min: 0.0, max: 1.0, step: 0.01, isSlider: true, unit: '' },
    minConfidence: { min: 0.0, max: 1.0, step: 0.01, isSlider: true, unit: '' },
    minimumConfidence: { min: 0.0, max: 1.0, step: 0.01, isSlider: true, unit: '' },
    iouThreshold: { min: 0.0, max: 1.0, step: 0.01, isSlider: true, unit: '' },
    nmsThreshold: { min: 0.0, max: 1.0, step: 0.01, isSlider: true, unit: '' },
    scoreThreshold: { min: 0.0, max: 1.0, step: 0.01, isSlider: true, unit: '' },
    trackHighThreshold: { min: 0.0, max: 1.0, step: 0.01, isSlider: true, unit: '' },
    trackLowThreshold: { min: 0.0, max: 1.0, step: 0.01, isSlider: true, unit: '' },
    newTrackThreshold: { min: 0.0, max: 1.0, step: 0.01, isSlider: true, unit: '' },
    matchThreshold: { min: 0.0, max: 1.0, step: 0.01, isSlider: true, unit: '' },
    botSortFirstIouThreshold: { min: 0.0, max: 1.0, step: 0.01, isSlider: true, unit: '' },
    botSortSecondIouThreshold: { min: 0.0, max: 1.0, step: 0.01, isSlider: true, unit: '' },
    botSortUnconfirmedIouThreshold: { min: 0.0, max: 1.0, step: 0.01, isSlider: true, unit: '' },
    ocSortDetectionThreshold: { min: 0.0, max: 1.0, step: 0.01, isSlider: true, unit: '' },
    ocSortIouThreshold: { min: 0.0, max: 1.0, step: 0.01, isSlider: true, unit: '' },
    ocSortInertia: { min: 0.0, max: 1.0, step: 0.01, isSlider: true, unit: '' },
    anomalyThreshold: { min: 0.0, max: 1.0, step: 0.01, isSlider: true, unit: '' },
    heatmapOpacity: { min: 0.0, max: 1.0, step: 0.01, isSlider: true, unit: '' },
    maskOpacity: { min: 0.0, max: 1.0, step: 0.01, isSlider: true, unit: '' },
    fillOpacity: { min: 0.0, max: 1.0, step: 0.01, isSlider: true, unit: '' },
    opacity: { min: 0.0, max: 1.0, step: 0.01, isSlider: true, unit: '' },
    overlapRatio: { min: 0.0, max: 0.8, step: 0.01, isSlider: true, unit: '' },
    contextPaddingPercent: { min: 0.0, max: 1.0, step: 0.01, isSlider: true, unit: '' },
    paddingPercent: { min: 0.0, max: 1.0, step: 0.01, isSlider: true, unit: '' },
    alpha: { min: 0.0, max: 1.0, step: 0.05, isSlider: true, unit: '' },

    // Visual & Processing parameters
    contrast: { min: 0.1, max: 3.0, step: 0.1, isSlider: true, unit: 'x' },
    brightness: { min: -100, max: 100, step: 1, isSlider: true, unit: '' },
    strength: { min: 0.1, max: 5.0, step: 0.1, isSlider: true, unit: 'x' },
    clipLimit: { min: 0.1, max: 10.0, step: 0.1, isSlider: true, unit: '' },
    tileGridSize: { min: 2, max: 32, step: 1, isSlider: true, unit: 'px' },
    kernel: { min: 1, max: 51, step: 2, isSlider: true, unit: 'px', oddOnly: true },
    kernelSize: { min: 3, max: 99, step: 2, isSlider: true, unit: 'px', oddOnly: true },
    pixelateBlock: { min: 2, max: 64, step: 1, isSlider: true, unit: 'px' },
    lowLightThreshold: { min: 10.0, max: 200.0, step: 1.0, isSlider: true, unit: '' },
    fontScale: { min: 0.2, max: 4.0, step: 0.05, isSlider: true, unit: 'x' },
    thickness: { min: 1, max: 12, step: 1, isSlider: true, unit: 'px' },
    lineWidth: { min: 1, max: 12, step: 1, isSlider: true, unit: 'px' },
    size: { min: 0.2, max: 3.0, step: 0.05, isSlider: true, unit: 'x' },

    // Time & Delays
    seconds: { min: 0.1, max: 60.0, step: 0.1, isSlider: true, unit: 'dtk' },
    thresholdSeconds: { min: 0.5, max: 120.0, step: 0.5, isSlider: true, unit: 'dtk' },
    requiredCount: { min: 1, max: 1000, step: 1 },
    triggerCount: { min: 1, max: 1000, step: 1 },
    confirmationSeconds: { min: 0.0, max: 300.0, step: 0.1, isSlider: true, unit: 'dtk' },
    personGraceSeconds: { min: 0.0, max: 120.0, step: 0.1, isSlider: true, unit: 'dtk' },
    requiredGraceSeconds: { min: 0.0, max: 300.0, step: 0.1, isSlider: true, unit: 'dtk' },
    absenceGraceSeconds: { min: 0.0, max: 120.0, step: 0.1, isSlider: true, unit: 'dtk' },
    maxObservationGapSeconds: { min: 0.1, max: 120.0, step: 0.1, isSlider: true, unit: 'dtk' },
    maxSessionDurationSeconds: { min: 0.0, max: 86400.0, step: 1.0, isSlider: true, unit: 'dtk' },
    cooldownSeconds: { min: 0.1, max: 60.0, step: 0.5, isSlider: true, unit: 'dtk' },
    queryIntervalSeconds: { min: 0.1, max: 10.0, step: 0.1, isSlider: true, unit: 'dtk' },
    historySeconds: { min: 1.0, max: 30.0, step: 0.5, isSlider: true, unit: 'dtk' },
    timeoutSeconds: { min: 0.5, max: 30.0, step: 0.5, isSlider: true, unit: 'dtk' },
    timeoutMs: { min: 1, max: 60000, step: 1, isSlider: false, unit: 'ms' },
    clipDurationSeconds: { min: 1, max: 60, step: 1, isSlider: true, unit: 'dtk' },
    freezeThresholdSeconds: { min: 1.0, max: 60.0, step: 1.0, isSlider: true, unit: 'dtk' },
    periodicIntervalSeconds: { min: 1.0, max: 300.0, step: 1.0, isSlider: true, unit: 'dtk' },
    temperature: { min: 0.0, max: 2.0, step: 0.05, isSlider: true, unit: '' },
    maxTokens: { min: 50, max: 4000, step: 50, isSlider: false, unit: 'tokens' },
    imageMaxDimension: { min: 320, max: 1920, step: 80, isSlider: false, unit: 'px' },

    // Rates, Buffer & Quality
    jpegQuality: { min: 10, max: 100, step: 1, isSlider: true, unit: '%' },
    imageQuality: { min: 10, max: 100, step: 1, isSlider: true, unit: '%' },
    trackBuffer: { min: 1, max: 180, step: 1, isSlider: true, unit: 'frame' },
    minimumConsecutiveFrames: { min: 1, max: 10, step: 1, isSlider: true, unit: 'frame' },
    trackerFrameRate: { min: 1, max: 60, step: 1, isSlider: true, unit: 'fps' },
    classLockWindow: { min: 2, max: 30, step: 1, isSlider: true, unit: 'frame' },
    smoothingAlpha: { min: 0.05, max: 1.0, step: 0.05, isSlider: true, unit: '' },
    paddingPercent: { min: 0, max: 100, step: 5, isSlider: true, unit: '%' },
    defaultConfidence: { min: 0.0, max: 1.0, step: 0.05, isSlider: true, unit: '' },
    topK: { min: 1, max: 10, step: 1, isSlider: true, unit: '' },
    detectEveryNFrames: { min: 1, max: 30, step: 1, isSlider: true, unit: 'frame' },
    requiredVotes: { min: 1, max: 8, step: 1, isSlider: true, unit: 'model' },
    batchSize: { min: 1, max: 32, step: 1, isSlider: true, unit: '' },
    retryCount: { min: 0, max: 5, step: 1, isSlider: true, unit: 'x' },

    // Dimensions
    width: { min: 16, max: 3840, step: 1 },
    height: { min: 16, max: 2160, step: 1 },
    x: { min: 0, max: 3840, step: 1 },
    y: { min: 0, max: 2160, step: 1 },
    sliceWidth: { min: 128, max: 2048, step: 32, isSlider: true, unit: 'px' },
    sliceHeight: { min: 128, max: 2048, step: 32, isSlider: true, unit: 'px' },
    minCropWidth: { min: 8, max: 512, step: 8, isSlider: true, unit: 'px' },
    minCropHeight: { min: 8, max: 512, step: 8, isSlider: true, unit: 'px' },
    maxCrops: { min: 1, max: 64, step: 1, isSlider: true, unit: '' },
    maxCapacity: { min: 0, max: 10000, step: 1 },
    count: { min: 0, max: 10000, step: 1 }
  };

  let _drawTextEditNodeId = null;

  function createSmartConfigField(node, key, value) {
    const wrap = document.createElement('div');
    wrap.className = 'field';
    wrap.dataset.fieldKey = key;
    const label = document.createElement('label');
    
    const labelText = document.createElement('span');
    labelText.className = 'field-label-text';
    let resolvedLabel = INDO_FIELD_LABELS[key] || key.replace(/([A-Z])/g, ' $1').replaceAll('_', ' ').replace(/\b\w/g, c => c.toUpperCase());
    if (key === 'modelPath' || key === 'customModelPath') {
      if (node.config && node.config.engine === 'roboflow_universe') {
        resolvedLabel = 'Roboflow Universe Model ID';
      } else if (node.config && node.config.engine === 'yolo_world') {
        resolvedLabel = 'Checkpoint YOLO-World (Opsional)';
      }
    }
    labelText.textContent = resolvedLabel;
    label.append(labelText);

    const helpInfo = node.type === 'zone_exit_event' && key === 'classes'
      ? { text: 'Kelas objek yang dipantau keluar zona; wajib sesuai label pada model.', guide: 'Contoh truck,tire. Isi setidaknya satu kelas. Kelas tire memerlukan model yang mengenali ban.' }
      : FIELD_HELP[key];
    if (helpInfo) {
      const tip = typeof helpInfo === 'object' ? `${helpInfo.text}\n\n💡 Panduan: ${helpInfo.guide}` : helpInfo;
      const tooltipIcon = document.createElement('span');
      tooltipIcon.className = 'field-tooltip-icon';
      tooltipIcon.textContent = '?';
      tooltipIcon.title = tip;
      tooltipIcon.setAttribute('data-tooltip', tip);
      label.append(tooltipIcon);
    }
    wrap.append(label);

    if ((node.type === 'telegram_notification' && (key === 'messageCaption' || key === 'messageTemplate')) || (node.type === 'draw_text' && key === 'textTemplate')) {
      const input = document.createElement('textarea');
      input.value = value ?? '';
      input.rows = node.type === 'telegram_notification' ? 4 : 3;
      input.placeholder = node.type === 'telegram_notification'
        ? '🚨 Peringatan: {event.type} pada {event.zoneName}!\\nWaktu: {timestamp}'
        : 'Contoh: Jumlah orang: {detection.count}';
      input.oninput = () => {
        node.config[key] = input.value;
        markDirty();
      };
      wrap.append(input);
      const hint = document.createElement('small');
      hint.className = 'field-help';
      hint.textContent = node.type === 'telegram_notification'
        ? 'Placeholder dinamis: {event.type}, {event.zoneName}, {timestamp}, {event.message}, {track_id}, {class}, {confidence}'
        : 'Variabel tersedia: {detection.count}, {detection.class}, {detection.confidence}, {track.id}, {image.width}, {image.height}.';
      wrap.append(hint);
      return wrap;
    }

    if (node.type === 'screenshot_capture' && key === 'captureMode') {
      const select = document.createElement('select');
      const modes = [
        ['full_annotated', '🖼️ Full Frame Beranotasi (Bbox + Labels)'],
        ['raw_frame', '📷 Raw Frame Asli (Kamera Polos)'],
        ['crop_object', '✂️ Potongan Objek Pemicu (Crop Only)']
      ];
      modes.forEach(([val, lbl]) => {
        const opt = document.createElement('option');
        opt.value = val;
        opt.textContent = lbl;
        if (String(value) === val) opt.selected = true;
        select.append(opt);
      });
      select.onchange = () => {
        node.config[key] = select.value;
        markDirty();
        liveUpdateWorkflow();
      };
      wrap.append(select);
      return wrap;
    }

    if (key === 'parseMode') {
      const select = document.createElement('select');
      const pModes = [
        ['HTML', 'HTML (<b>tebal</b>, <i>miring</i>)'],
        ['Markdown', 'Markdown (*tebal*, _miring_)'],
        ['None', 'Teks Polos (Plain Text)']
      ];
      pModes.forEach(([val, lbl]) => {
        const opt = document.createElement('option');
        opt.value = val;
        opt.textContent = lbl;
        if (String(value) === val) opt.selected = true;
        select.append(opt);
      });
      select.onchange = () => {
        node.config[key] = select.value;
        markDirty();
        liveUpdateWorkflow();
      };
      wrap.append(select);
      return wrap;
    }


    if (key === 'targetFps') {
      const input = document.createElement('input');
      input.type = 'number';
      input.min = '0';
      input.step = 'any';
      input.required = true;
      input.value = value ?? 10;
      input.onchange = () => {
        if (!input.reportValidity()) return;
        node.config[key] = input.valueAsNumber;
        markDirty();
      };
      wrap.append(input);
      appendHelp(wrap, key);
      return wrap;
    }

    // Dropdown mappings
    const OPTION_MAPS = {
      timerFormat: [
        ['mm:ss', 'Menit : Detik (00:15)'],
        ['seconds', 'Detik Desimal (15.2s)'],
        ['hh:mm:ss', 'Jam : Menit : Detik (00:01:25)']
      ],
      badgePosition: [
        ['top', 'Di Atas Kotak (Top / Above Box)'],
        ['bottom', 'Di Bawah Kotak (Bottom / Below Box)'],
        ['inside', 'Di Dalam Kotak (Inside Box)']
      ],
      algorithm: [
        ['bytetrack', 'ByteTrack (Fastest, High/Low Match)'],
        ['botsort', 'BoT-SORT (Camera Motion Compensation)'],
        ['ocsort', 'OC-SORT (Observation-Centric, Occlusion Robust)'],
        ['cbiou', 'C-BIoU (Buffered Motion / Sampled Frames)']
      ],
      provider: (node.type === 'ai_agent') ? [
        ['openai', 'OpenAI (Official api.openai.com)'],
        ['openrouter', 'OpenRouter (Multi-model: Gemini, Claude, Llama, Qwen)'],
        ['custom', 'Custom / Local (Ollama, vLLM, LM Studio)']
      ] : [
        ['openrouter', 'OpenRouter (Gemini Flash, Qwen2-VL, dll)'],
        ['typesafe', 'TypeSafe Jev System One']
      ],
      triggerMode: [
        ['on_event', 'On Upstream Event (Hemat Token / Saat Ada Kejadian)'],
        ['periodic', 'Periodic Interval (Audit Rutin per N Detik)'],
        ['always', 'Every Frame (Sesuai Cooldown)']
      ],
      taskMode: [
        ['decision', 'Decision Gate (Filter True/False dengan Alasan)'],
        ['analysis', 'Incident Analysis & Summary Report'],
        ['structured_json', 'Structured JSON Extraction'],
        ['raw_text', 'Raw Text / Conversational Reasoning']
      ],
      passDownstreamOn: [
        ['decision_true', 'Hanya Jika Decision = True (Smart Gate)'],
        ['always', 'Teruskan Semua Hasil ke Hilir']
      ],
      sourceType: [
        ['camera', 'Camera (USB/Built-in OpenCV)'],
        ['youtube', 'YouTube Video / Live Stream'],
        ['daheng', 'Daheng Industrial Camera'],
        ['image', 'Static Image File'],
        ['video', 'Video File'],
        ['file', 'Generic File Source']
      ],
      youtubeQuality: [
        ['auto', 'Auto (Maks 720p - Rekomendasi)'],
        ['360p', '360p (Hemat Bandwidth)'],
        ['480p', '480p (Standar)'],
        ['720p', '720p (HD Tajam)'],
        ['1080p', '1080p (Full HD)']
      ],
      engine: [
        ['rfdetr', 'RF-DETR (PyTorch Engine)'],
        ['rfdetr_onnx', 'RF-DETR ONNX Runtime'],
        ['rfdetr_tensorrt', 'RF-DETR TensorRT (CUDA Accelerated)'],
        ['ultralytics_yolo', 'Ultralytics YOLO (best.pt / yolov8)'],
        ['yolo_world', 'YOLO-World (Zero-Shot Text Prompt)'],
        ['roboflow_universe', 'Roboflow Universe (Model ID)'],
        ['onnx_custom', 'Custom ONNX Runtime (.onnx)'],
        ['tflite', 'TensorFlow Lite (.tflite)'],
        ['tensorflow_keras', 'TensorFlow / Keras (.keras / .h5)'],
        ['sam3', 'Segment Anything 3 (SAM 3)'],
        ['convnext', 'ConvNeXt Classifier'],
        ['efficientad', 'EfficientAD Visual Inspection']
      ],
      rfdetrModel: [
        ['rfdetr-nano', 'RF-DETR Nano (Fast CPU/GPU)'],
        ['rfdetr-small', 'RF-DETR Small'],
        ['rfdetr-medium', 'RF-DETR Medium'],
        ['rfdetr-large', 'RF-DETR Large (High Accuracy)']
      ],
      device: [
        ['auto', 'Auto (CUDA GPU if available, else CPU)'],
        ['cpu', 'CPU Only'],
        ['cuda', 'CUDA GPU']
      ],
      mode: (node.type === 'blur_anonymizer') ? [
        ['gaussian', 'Gaussian Blur (Sensor Halus)'],
        ['pixelate', 'Pixelate (Sensor Kotak-kotak)']
      ] : (node.type === 'color_convert') ? [
        ['gray', 'Grayscale (Hitam Putih)'],
        ['hsv', 'HSV Color Space'],
        ['lab', 'CIELAB Color Space'],
        ['rgb', 'RGB Color Space'],
        ['bgr', 'BGR Color Space'],
        ['ycrcb', 'YCrCb Color Space']
      ] : (node.type === 'object_counter') ? [
        ['occupancy', 'Occupancy (Jumlah Objek Saat Ini)'],
        ['cumulative', 'Cumulative (Akumulasi Total Objek Unik)'],
        ['crossing', 'Crossing (Penghitungan Melintas)']
      ] : (node.type === 'roi_filter') ? [
        ['inside', 'Hanya Deteksi DI DALAM Area (Inside)'],
        ['outside', 'Hanya Deteksi DI LUAR Area (Outside)']
      ] : [
        ['gray', 'Grayscale'],
        ['hsv', 'HSV Color Space'],
        ['lab', 'CIELAB Color Space']
      ],
      shape: [
        ['rectangle', 'Persegi Panjang (Rectangle)'],
        ['polygon', 'Poligon Bebas (Multi-Point Polygon)']
      ],
      crossingDirection: [
        ['enter', 'Masuk Area Saja (Enter Zone)'],
        ['exit', 'Keluar Area Saja (Exit Zone)'],
        ['both', 'Masuk & Keluar (Both Directions)']
      ],
      captureMode: [
        ['crop_only', 'Hanya Potongan Objek (Crop Only)'],
        ['full_frame', 'Frame Utuh (Full Frame)'],
        ['both', 'Keduanya (Crop + Full Frame)']
      ],
      format: [
        ['jpg', 'JPEG (.jpg) — Cepat & Ukuran Ringkas'],
        ['png', 'PNG (.png) — Lossless Tanpa Kompresi'],
        ['webp', 'WebP (.webp) — Efisien untuk Web']
      ],
      direction: [
        ['both', 'Dua Arah (Masuk & Keluar)'],
        ['in', 'Arah Masuk Saja (IN)'],
        ['out', 'Arah Keluar Saja (OUT)']
      ],
      flip: [
        ['none', 'Tidak Dibalik (None)'],
        ['horizontal', 'Balik Horizontal (Kiri-Kanan)'],
        ['vertical', 'Balik Vertikal (Atas-Bawah)'],
        ['both', 'Balik Keduanya (Diagonal)']
      ],
      operation: [
        ['blur', 'Standard Box Blur'],
        ['sharpen', 'Edge Sharpening Filter'],
        ['gaussian_blur', 'Gaussian Blur'],
        ['median_blur', 'Median Blur (Salt & Pepper)'],
        ['bilateral', 'Bilateral Filter (Edge-Preserving)']
      ],
      rotation: [
        ['0', '0° (No rotation)'],
        ['90', '90° Clockwise'],
        ['180', '180° Inverted'],
        ['270', '270° Clockwise'],
        ['flip_h', 'Flip Horizontal'],
        ['flip_v', 'Flip Vertical'],
        ['flip_hv', 'Flip Both']
      ],
      method: [
        ['mog2', 'MOG2 Background Subtractor'],
        ['knn', 'KNN Background Subtractor']
      ],
      interpolation: [
        ['linear', 'Bilinear (Default)'],
        ['nearest', 'Nearest Neighbor (Fastest)'],
        ['cubic', 'Bicubic (Smooth)'],
        ['area', 'Area (Best for Downsampling)'],
        ['lanczos', 'Lanczos4 (Highest Quality)']
      ],
      operator: [
        ['gte', '>= (Lebih besar atau sama dengan)'],
        ['gt', '> (Lebih besar dari)'],
        ['lte', '<= (Lebih kecil atau sama dengan)'],
        ['lt', '< (Lebih kecil dari)'],
        ['eq', '== (Sama persis dengan)'],
        ['neq', '!= (Tidak sama dengan)']
      ],
      metric: [
        ['object_count', 'Jumlah Objek Terdeteksi (Live Detection Count)'],
        ['line_counter_in', 'Hitungan Masuk Line Counter (IN)'],
        ['line_counter_out', 'Hitungan Keluar Line Counter (OUT)'],
        ['line_counter_total', 'Total Hitungan Line Counter (IN + OUT)'],
        ['line_crossing', 'Ada Objek Melintasi Garis (Event Frame)'],
        ['class_count', 'Jumlah Objek Kelas Tertentu (Filter Class)'],
        ['max_confidence', 'Tingkat Akurasi / Confidence Tertinggi'],
        ['anomaly_score', 'Skor Anomali Cacat (EfficientAD)']
      ],
      passWhen: [
        ['true', '🟢 Cabang IF — Loloskan data jika kondisi BENAR (True)'],
        ['false', '🔴 Cabang ELSE — Loloskan data jika kondisi SALAH (False)']
      ],
      triggerAnchor: [
        ['bottom_center', 'Bottom Center (Ground Contact / Foot)'],
        ['center', 'Bounding Box Center'],
        ['top_center', 'Top Center (Head)'],
        ['overlap', 'Bounding Box Overlap'],
        ['contained', 'Fully Contained']
      ],
      match: [
        ['any', 'Setidaknya Salah Satu Memenuhi (Any)'],
        ['all', 'Semua Wajib Memenuhi (All)'],
        ['bottom_center', 'Bottom Center (Ground Contact)'],
        ['center', 'Bounding Box Center'],
        ['top_center', 'Top Center'],
        ['overlap', 'Bounding Box Overlap'],
        ['contained', 'Fully Contained']
      ],
      countMode: [
        ['both', 'IN & OUT (Bidirectional)'],
        ['in_only', 'IN Only (Masuk Saja)'],
        ['out_only', 'OUT Only (Keluar Saja)']
      ],
      onError: [
        ['stop', 'Stop workflow (berhenti jika error)'],
        ['pass', 'Pass-through (teruskan frame asli)']
      ]
    };

    if (node.type === 'python_script' && key === 'code') {
      const container = document.createElement('div');
      container.className = 'script-inspector-enhanced';

      // 1. Preset Templates definition
      const SCRIPT_PRESETS = [
        { label: '⚡ Pilih Template OpenCV...', code: '' },
        {
          label: '1. Watermark Teks & Timestamp Dinamis',
          code: `def process(frame, state):
    # Hitung frame dan catat waktu
    import time
    state['count'] = state.get('count', 0) + 1
    ts = time.strftime("%Y-%m-%d %H:%M:%S")

    # Render background watermark semi-transparan
    h, w = frame.shape[:2]
    overlay = frame.copy()
    cv2.rectangle(overlay, (15, 15), (320, 65), (0, 0, 0), -1)
    cv2.addWeighted(overlay, 0.6, frame, 0.4, 0, frame)

    # Teks watermark informatif
    cv2.putText(frame, "AFI VISION BUILDER", (25, 38), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1, cv2.LINE_AA)
    cv2.putText(frame, f"{ts} | Frame #{state['count']}", (25, 56), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (14, 165, 233), 1, cv2.LINE_AA)
    return frame`
        },
        {
          label: '2. Masking Warna HSV (Deteksi Target Warna)',
          code: `def process(frame, state):
    # Ubah ruang warna BGR ke HSV
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    # Rentang warna target (contoh: fluorescent / hijau)
    lower_bound = np.array([35, 60, 60], dtype=np.uint8)
    upper_bound = np.array([85, 255, 255], dtype=np.uint8)
    mask = cv2.inRange(hsv, lower_bound, upper_bound)

    # Temukan kontur area yang cocok
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    for c in contours:
        if cv2.contourArea(c) > 600:
            x, y, w, h = cv2.boundingRect(c)
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.putText(frame, "COLOR MATCH", (x, max(15, y - 6)), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 0), 1)

    return frame`
        },
        {
          label: '3. Adaptive Threshold & Canny Edge Overlay',
          code: `def process(frame, state):
    # Grayscale & Canny edge detection
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blurred, 50, 150)

    # Warnai edge dengan Cyan terang
    edge_bgr = np.zeros_like(frame)
    edge_bgr[edges > 0] = [255, 255, 0]

    # Padukan kembali ke frame
    frame = cv2.addWeighted(frame, 0.85, edge_bgr, 0.7, 0)
    return frame`
        },
        {
          label: '4. Dynamic Gamma Correction (Pencerah Area Gelap)',
          code: `def process(frame, state):
    # Koreksi kecerahan gamma dinamis (gamma < 1.0 mencerahkan)
    gamma = 0.75
    inv_gamma = 1.0 / gamma
    table = np.array([((i / 255.0) ** inv_gamma) * 255 for i in np.arange(0, 256)]).astype("uint8")
    return cv2.LUT(frame, table)`
        },
        {
          label: '5. Sharpening Kernel 3x3 (Penajaman Detail)',
          code: `def process(frame, state):
    # Kernel unsharp mask
    kernel = np.array([
        [0, -1, 0],
        [-1, 5, -1],
        [0, -1, 0]
    ], dtype=np.float32)
    return cv2.filter2D(frame, -1, kernel)`
        },
        {
          label: '6. Vignette & Cinematic Lens Effect',
          code: `def process(frame, state):
    h, w = frame.shape[:2]
    # Gaussian kernel untuk vignetting
    X_kernel = cv2.getGaussianKernel(w, w / 2)
    Y_kernel = cv2.getGaussianKernel(h, h / 2)
    kernel = Y_kernel * X_kernel.T
    mask = 255 * kernel / np.linalg.norm(kernel)
    mask = np.clip(mask * 1.5, 0, 1)

    out = np.copy(frame)
    for i in range(3):
        out[:, :, i] = out[:, :, i] * mask
    return out.astype(np.uint8)`
        }
      ];

      // 2. Toolbar baris atas: Preset Select + Tombol AI Prompt to Code
      const toolbar = document.createElement('div');
      toolbar.className = 'script-inspector-toolbar';

      const presetSelect = document.createElement('select');
      presetSelect.className = 'script-preset-select';
      SCRIPT_PRESETS.forEach((p, idx) => {
        const opt = document.createElement('option');
        opt.value = idx;
        opt.textContent = p.label;
        presetSelect.appendChild(opt);
      });

      const aiPromptBtn = document.createElement('button');
      aiPromptBtn.type = 'button';
      aiPromptBtn.className = 'script-ai-prompt-btn';
      aiPromptBtn.innerHTML = '<svg class="icon-svg icon-sm" viewBox="0 0 24 24"><path d="m12 3-1.9 5.8a2 2 0 0 1-1.3 1.3L3 12l5.8 1.9a2 2 0 0 1 1.3 1.3L12 21l1.9-5.8a2 2 0 0 1 1.3-1.3L21 12l-5.8-1.9a2 2 0 0 1-1.3-1.3L12 3z"/></svg><span>✨ AI Prompt</span>';

      toolbar.append(presetSelect, aiPromptBtn);
      container.append(toolbar);

      // 3. Inline AI Prompt Box (Hidden by default)
      const aiBox = document.createElement('div');
      aiBox.className = 'script-ai-box';
      aiBox.hidden = true;
      aiBox.innerHTML = `
        <div style="font-size:11.5px;font-weight:700;color:#0d9488;display:flex;align-items:center;gap:6px">
          <svg class="icon-svg icon-sm" viewBox="0 0 24 24"><path d="m12 3-1.9 5.8a2 2 0 0 1-1.3 1.3L3 12l5.8 1.9a2 2 0 0 1 1.3 1.3L12 21l1.9-5.8a2 2 0 0 1 1.3-1.3L21 12l-5.8-1.9a2 2 0 0 1-1.3-1.3L12 3z"/></svg>
          <span>AI Prompt-to-Code Python Script</span>
        </div>
        <textarea class="script-ai-prompt-input" rows="2" placeholder="Tulis instruksi OpenCV (misal: 'Beri grid garis hijau 4x4 dan tulis koordinat cell')..."></textarea>
        <div class="script-ai-box-actions">
          <button type="button" class="button secondary btn-sm cancel-ai-btn">Batal</button>
          <button type="button" class="button primary btn-sm generate-ai-btn" style="background:#0d9488!important;border:none!important">Generate Script</button>
        </div>
      `;
      container.append(aiBox);

      // 4. Code Editor Wrapper
      const editorWrap = document.createElement('div');
      editorWrap.className = 'script-editor-wrap';

      const textarea = document.createElement('textarea');
      textarea.className = 'script-code-editor';
      textarea.value = value ?? '';
      textarea.rows = 10;
      textarea.spellcheck = false;

      // Tab indentation support
      textarea.addEventListener('keydown', (e) => {
        if (e.key === 'Tab') {
          e.preventDefault();
          const start = textarea.selectionStart;
          const end = textarea.selectionEnd;
          textarea.value = textarea.value.substring(0, start) + '    ' + textarea.value.substring(end);
          textarea.selectionStart = textarea.selectionEnd = start + 4;
          node.config.code = textarea.value;
          markDirty();
          checkSyntaxLive();
        }
      });

      textarea.addEventListener('input', () => {
        node.config.code = textarea.value;
        markDirty();
        checkSyntaxLive();
      });

      // Status Footer & Syntax Badge
      const editorFooter = document.createElement('div');
      editorFooter.className = 'script-editor-footer';

      const syntaxBadge = document.createElement('span');
      syntaxBadge.className = 'script-syntax-badge valid';
      syntaxBadge.textContent = '✓ Valid Python AST';

      const charCounter = document.createElement('span');
      charCounter.style.color = '#94a3b8';
      charCounter.textContent = `${(textarea.value || '').length} chars`;

      editorFooter.append(syntaxBadge, charCounter);
      editorWrap.append(textarea, editorFooter);
      container.append(editorWrap);

      // Syntax checker logic
      let syntaxTimer = null;
      async function checkSyntaxLive() {
        charCounter.textContent = `${(textarea.value || '').length} chars`;
        clearTimeout(syntaxTimer);
        const code = textarea.value.trim();
        if (!code.includes('def process')) {
          syntaxBadge.className = 'script-syntax-badge invalid';
          syntaxBadge.textContent = '✕ Harus ada def process(frame, state)';
          return;
        }
        syntaxTimer = setTimeout(async () => {
          try {
            await api('/api/scripts/validate', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ code: textarea.value })
            });
            syntaxBadge.className = 'script-syntax-badge valid';
            syntaxBadge.textContent = '✓ Valid Python AST';
          } catch (e) {
            syntaxBadge.className = 'script-syntax-badge invalid';
            syntaxBadge.textContent = '✕ ' + (e.message || 'Syntax Error');
          }
        }, 300);
      }
      checkSyntaxLive();

      // Preset change handler
      presetSelect.addEventListener('change', () => {
        const idx = Number(presetSelect.value);
        if (idx > 0 && SCRIPT_PRESETS[idx]) {
          textarea.value = SCRIPT_PRESETS[idx].code;
          node.config.code = textarea.value;
          markDirty();
          checkSyntaxLive();
          toast(`Template "${SCRIPT_PRESETS[idx].label}" dimuat.`);
        }
      });

      // AI Prompt toggle & submit
      aiPromptBtn.addEventListener('click', () => {
        aiBox.hidden = !aiBox.hidden;
        if (!aiBox.hidden) {
          aiBox.querySelector('.script-ai-prompt-input')?.focus();
        }
      });

      aiBox.querySelector('.cancel-ai-btn')?.addEventListener('click', () => {
        aiBox.hidden = true;
      });

      aiBox.querySelector('.generate-ai-btn')?.addEventListener('click', async () => {
        const promptInput = aiBox.querySelector('.script-ai-prompt-input');
        const promptVal = promptInput?.value?.trim();
        if (!promptVal) {
          toast('Silakan masukkan instruksi script', true);
          return;
        }

        const genBtn = aiBox.querySelector('.generate-ai-btn');
        genBtn.disabled = true;
        genBtn.textContent = 'Generating...';

        try {
          const aiConfig = {
            provider: localStorage.getItem('visonode_setting_vlm_provider') || '9router',
            apiKey: localStorage.getItem('visonode_setting_api_key') || '',
            baseUrl: localStorage.getItem('visonode_setting_base_url') || '',
            model: localStorage.getItem('visonode_setting_ai_model') || 'cx/gpt-5.6-luna',
            ollamaUrl: localStorage.getItem('visonode_setting_ollama_url') || 'http://127.0.0.1:11434'
          };

          const res = await api('/api/ai/generate-script', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              prompt: promptVal,
              currentCode: textarea.value,
              aiConfig
            })
          });

          if (res.code) {
            textarea.value = res.code;
            node.config.code = textarea.value;
            markDirty();
            checkSyntaxLive();
            aiBox.hidden = true;
            toast('✨ Script Python berhasil dibuat oleh AI!');
          }
        } catch (err) {
          toast('AI Generation Error: ' + err.message, true);
        } finally {
          genBtn.disabled = false;
          genBtn.textContent = 'Generate Script';
        }
      });

      // 5. Test 1 Frame Sandbox Card (Realtime Visual Preview)
      const testCard = document.createElement('div');
      testCard.className = 'script-test-card';
      testCard.innerHTML = `
        <div style="display:flex;align-items:center;justify-content:space-between">
          <strong style="font-size:12px;color:#0f172a">Sandbox Visual Test</strong>
          <span class="script-test-status" style="font-size:11px;color:#64748b">Siap diuji</span>
        </div>
        <button type="button" class="script-test-btn" id="runScriptTestBtn">
          <svg class="icon-svg icon-sm" viewBox="0 0 24 24"><polygon points="5 3 19 12 5 21 5 3"/></svg>
          <span>▶️ Uji 1 Frame (Preview Visual)</span>
        </button>
        <div class="script-preview-grid" id="scriptTestPreviewGrid" style="display:none">
          <div class="script-preview-box">
            <span class="box-tag">Input Frame</span>
            <img id="scriptTestInputImg" alt="Input Frame">
          </div>
          <div class="script-preview-box">
            <span class="box-tag" style="background:#0d9488">Output Frame</span>
            <img id="scriptTestOutputImg" alt="Output Frame">
          </div>
        </div>
        <div class="script-test-meta" id="scriptTestMeta" style="display:none">
          <span id="scriptTestTime">Latency: 0 ms</span>
          <span id="scriptTestDims">Dimensi: 640x480</span>
        </div>
        <div class="script-logs-output" id="scriptTestLogs" style="display:none"></div>
      `;

      const testBtn = testCard.querySelector('#runScriptTestBtn');
      const testStatus = testCard.querySelector('.script-test-status');
      const testGrid = testCard.querySelector('#scriptTestPreviewGrid');
      const testInImg = testCard.querySelector('#scriptTestInputImg');
      const testOutImg = testCard.querySelector('#scriptTestOutputImg');
      const testMeta = testCard.querySelector('#scriptTestMeta');
      const testTime = testCard.querySelector('#scriptTestTime');
      const testDims = testCard.querySelector('#scriptTestDims');
      const testLogs = testCard.querySelector('#scriptTestLogs');

      testBtn.addEventListener('click', async () => {
        testBtn.disabled = true;
        testStatus.textContent = 'Menjalankan di sandbox worker...';
        try {
          const res = await api('/api/nodes/test-python-script', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ code: textarea.value })
          });

          if (res.success) {
            testGrid.style.display = 'grid';
            testMeta.style.display = 'flex';
            testInImg.src = res.inputImage;
            testOutImg.src = res.outputImage;
            testTime.textContent = `Latency: ${res.durationMs} ms`;
            testDims.textContent = `Dimensi: ${res.dimensions}`;
            testStatus.textContent = `Sukses (${res.durationMs} ms)`;
            testStatus.style.color = '#10b981';

            if (res.logs && res.logs.trim()) {
              testLogs.style.display = 'block';
              testLogs.textContent = 'Console Logs:\n' + res.logs;
            } else {
              testLogs.style.display = 'none';
            }
            toast(`Uji frame berhasil (${res.durationMs} ms)`);
          }
        } catch (err) {
          testStatus.textContent = 'Error eksekusi';
          testStatus.style.color = '#ef4444';
          toast('Uji script gagal: ' + err.message, true);
        } finally {
          testBtn.disabled = false;
        }
      });

      container.append(testCard);
      wrap.append(container);
      return wrap;
    }

    // 1. Dropdown select
    if (OPTION_MAPS[key]) {
      let options = OPTION_MAPS[key];
      if (key === 'engine') {
        if (node.type === 'detector') {
          options = [
            ['rfdetr', 'RF-DETR (PyTorch Engine)'],
            ['rfdetr_onnx', 'RF-DETR ONNX Runtime'],
            ['rfdetr_tensorrt', 'RF-DETR TensorRT (CUDA Accelerated)'],
            ['ultralytics_yolo', 'Ultralytics YOLO (best.pt / yolov8)'],
            ['yolo_world', 'YOLO-World (Zero-Shot Text Prompt)'],
            ['roboflow_universe', 'Roboflow Universe (Model ID)'],
            ['onnx_custom', 'Custom ONNX Runtime (.onnx)'],
            ['tflite', 'TensorFlow Lite (.tflite)'],
            ['tensorflow_keras', 'TensorFlow / Keras (.keras / .h5)']
          ];
        } else if (node.type === 'segmenter') {
          options = [
            ['sam3', 'Segment Anything 3 (SAM 3)'],
            ['rfdetr', 'RF-DETR Segmenter (PyTorch)'],
            ['rfdetr_onnx', 'RF-DETR Segmenter ONNX'],
            ['rfdetr_tensorrt', 'RF-DETR Segmenter TensorRT'],
            ['ultralytics_yolo', 'Ultralytics YOLO Segment (.pt)'],
            ['roboflow_universe', 'Roboflow Universe (Model ID)'],
            ['onnx_custom', 'Custom ONNX Segmenter (.onnx)'],
            ['tflite', 'TensorFlow Lite Segmenter (.tflite)']
          ];
        } else if (node.type === 'classifier') {
          options = [
            ['convnext', 'ConvNeXt Classifier (Default)'],
            ['ultralytics_yolo', 'Ultralytics YOLO Classify (.pt)'],
            ['roboflow_universe', 'Roboflow Universe (Model ID)'],
            ['onnx_custom', 'Custom ONNX Classifier (.onnx)'],
            ['tflite', 'TensorFlow Lite Classifier (.tflite)'],
            ['tensorflow_keras', 'TensorFlow / Keras (.keras / .h5)']
          ];
        }
      }

      const select = document.createElement('select');
      options.forEach(([optVal, optLabel]) => {
        const opt = document.createElement('option');
        opt.value = optVal;
        opt.textContent = optLabel;
        select.append(opt);
      });
      select.value = String(value);
      select.onchange = () => {
        node.config[key] = select.value;
        if (key === 'engine' && ['ultralytics_yolo', 'yolo_world', 'roboflow_universe', 'onnx_custom', 'tflite', 'tensorflow_keras', 'custom_auto'].includes(select.value)) {
          if (node.config.customModelPath === undefined) node.config.customModelPath = '';
          if (node.config.customClasses === undefined) node.config.customClasses = '';
          if (select.value === 'roboflow_universe' && node.config.roboflowApiKey === undefined) node.config.roboflowApiKey = '';
        }
        markDirty();
        renderInspector(); // Re-render for conditional visibility
      };
      wrap.append(select);
      appendHelp(wrap, key);
      return wrap;
    }

    // 1b. Camera Source selector for Input node
    if (key === 'source' && node.type === 'input') {
      const row = document.createElement('div');
      row.className = 'field-row';
      const select = document.createElement('select');
      select.style.flex = '1';

      const cameras = (state.cameras && state.cameras.length > 0)
        ? state.cameras
        : [
            { index: 0, label: 'Camera 0 (Default)' },
            { index: 1, label: 'Camera 1' },
            { index: 2, label: 'Camera 2' },
            { index: 3, label: 'Camera 3' }
          ];

      let matched = false;
      cameras.forEach(c => {
        const opt = document.createElement('option');
        opt.value = String(c.index);
        opt.textContent = c.label;
        if (String(value) === String(c.index)) {
          matched = true;
          opt.selected = true;
        }
        select.append(opt);
      });

      if (!matched && value !== undefined && value !== null && value !== '') {
        const customOpt = document.createElement('option');
        customOpt.value = String(value);
        customOpt.textContent = `Custom (${value})`;
        customOpt.selected = true;
        select.append(customOpt);
      }

      select.value = String(value ?? 0);
      select.onchange = () => {
        const val = select.value;
        node.config[key] = isNaN(Number(val)) ? val : Number(val);
        markDirty();
      };

      const scanBtn = document.createElement('button');
      scanBtn.type = 'button';
      scanBtn.className = 'button ghost';
      scanBtn.title = 'Rescan available webcams';
      scanBtn.innerHTML = '<svg class="icon-svg icon-sm" viewBox="0 0 24 24"><path d="M21.5 2v6h-6M21.34 15.57a10 10 0 1 1-.57-8.38l5.67-5.67"/></svg> Scan';
      scanBtn.onclick = async () => {
        scanBtn.disabled = true;
        toast('Scanning cameras...');
        await refreshCameras();
        scanBtn.disabled = false;
        renderInspector();
      };

      row.append(select, scanBtn);
      wrap.append(row);
      appendHelp(wrap, key);
      return wrap;
    }

    // 1b. IP Camera stream URL with "Discover IP Cameras / ONVIF" button
    if (key === 'streamUrl') {
      const row = document.createElement('div');
      row.className = 'field-row';
      const input = document.createElement('input');
      input.type = 'text';
      input.value = value ?? '';
      input.placeholder = 'rtsp://192.168.1.100:554/stream1 or http://...';
      input.onchange = () => {
        node.config[key] = input.value;
        markDirty();
      };

      const scanBtn = document.createElement('button');
      scanBtn.type = 'button';
      scanBtn.className = 'button ghost';
      scanBtn.title = 'Scan local network for ONVIF & RTSP cameras';
      scanBtn.innerHTML = '<svg class="icon-svg icon-sm" viewBox="0 0 24 24"><path d="M21.5 2v6h-6M21.34 15.57a10 10 0 1 1-.57-8.38l5.67-5.67"/></svg> Discover';
      scanBtn.onclick = async () => {
        scanBtn.disabled = true;
        toast('Discovering IP cameras & ONVIF devices...');
        try {
          const res = await api('/api/ip-cameras/discover');
          const cams = res.cameras || [];
          if (cams.length > 0) {
            state.discoveredCameras = cams;
            toast(`Found ${cams.length} IP camera stream(s)`);
            renderInspector();
          } else {
            toast('No IP cameras responded to multicast probe', true);
          }
        } catch (e) {
          toast('Discovery failed: ' + e.message, true);
        } finally {
          scanBtn.disabled = false;
        }
      };

      row.append(input, scanBtn);
      wrap.append(row);

      if (state.discoveredCameras && state.discoveredCameras.length > 0) {
        const picker = document.createElement('select');
        picker.style.marginTop = '4px';
        const emptyOpt = document.createElement('option');
        emptyOpt.value = '';
        emptyOpt.textContent = '-- Select detected camera / stream --';
        picker.append(emptyOpt);
        state.discoveredCameras.forEach(cam => {
          const opt = document.createElement('option');
          opt.value = cam.url;
          opt.textContent = `${cam.label} (${cam.url})`;
          if (cam.url === value) opt.selected = true;
          picker.append(opt);
        });
        picker.onchange = () => {
          if (picker.value) {
            node.config.streamUrl = picker.value;
            input.value = picker.value;
            markDirty();
          }
        };
        wrap.append(picker);
      }
      appendHelp(wrap, key);
      return wrap;
    }

    // 2. File path inputs with inline "Upload" button and uploaded media dropdown
    if (key === 'filePath') {
      const row = document.createElement('div');
      row.className = 'field-row';
      const input = document.createElement('input');
      input.type = 'text';
      input.value = value ?? '';
      input.placeholder = 'Path to image or video';
      input.onchange = () => {
        node.config[key] = input.value;
        markDirty();
      };

      const pickBtn = document.createElement('button');
      pickBtn.type = 'button';
      pickBtn.className = 'button ghost';
      pickBtn.innerHTML = '<svg class="icon-svg icon-sm" viewBox="0 0 24 24"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg> Upload';
      pickBtn.title = 'Upload image/video file';
      pickBtn.onclick = () => $('#fileInput').click();

      row.append(input, pickBtn);
      wrap.append(row);

      if (state.uploads && state.uploads.length > 0) {
        const picker = document.createElement('select');
        picker.style.marginTop = '4px';
        const emptyOpt = document.createElement('option');
        emptyOpt.value = '';
        emptyOpt.textContent = '-- Select uploaded media --';
        picker.append(emptyOpt);
        state.uploads.forEach(u => {
          const opt = document.createElement('option');
          opt.value = u.path;
          opt.textContent = `${u.name} (${u.kind}, ${(u.sizeBytes / 1024).toFixed(0)} KB)`;
          if (String(value) === u.path) opt.selected = true;
          picker.append(opt);
        });
        picker.onchange = () => {
          if (picker.value) {
            input.value = picker.value;
            node.config[key] = picker.value;
            const matched = state.uploads.find(u => u.path === picker.value);
            if (matched && node.type === 'input') {
              node.config.sourceType = matched.kind;
            }
            markDirty();
            renderInspector();
          }
        };
        wrap.append(picker);
      }

      appendHelp(wrap, key);
      return wrap;
    }

    // 3. Model checkpoint files with Model Picker & Upload
    if (['rfdetrCheckpoint', 'rfdetrOnnxModel', 'rfdetrTensorRTEngine', 'samCheckpoint', 'convnextCheckpoint', 'efficientadModel', 'customModelPath', 'modelPath'].includes(key)) {
      const isRoboflow = node.config && node.config.engine === 'roboflow_universe';
      const isYoloWorld = node.config && node.config.engine === 'yolo_world';

      const row = document.createElement('div');
      row.className = 'field-row';
      const input = document.createElement('input');
      input.type = 'text';
      input.value = value ?? '';
      input.placeholder = isRoboflow 
        ? 'Contoh: warehouse-safety/3 atau workspace/project/1'
        : (isYoloWorld ? 'Blank = yolov8s-worldv2.pt (default resmi otomatis unduh)' : 'Blank = default model, or custom file');
      input.onchange = async () => {
        node.config[key] = input.value;
        markDirty();
        if (input.value && !isRoboflow && !isYoloWorld) {
          await inspectAndApplyModel(node, input.value);
        }
      };

      if (!isRoboflow) {
        const modelBtn = document.createElement('button');
        modelBtn.type = 'button';
        modelBtn.className = 'button ghost';
        modelBtn.innerHTML = '<svg class="icon-svg icon-sm" viewBox="0 0 24 24"><rect width="16" height="16" x="4" y="4" rx="2"/><circle cx="12" cy="12" r="3"/></svg> Upload';
        modelBtn.onclick = () => $('#modelInput').click();
        row.append(input, modelBtn);
      } else {
        row.append(input);
      }
      wrap.append(row);

      if (isRoboflow) {
        const roboflowHelp = document.createElement('small');
        roboflowHelp.className = 'model-upload-help';
        roboflowHelp.textContent = 'Masukkan Model ID Roboflow Universe (format: project/version). Dieksekusi otomatis via Roboflow Hosted Inference API menggunakan API Key.';
        wrap.append(roboflowHelp);
      } else if (isYoloWorld) {
        const yoloWorldHelp = document.createElement('small');
        yoloWorldHelp.className = 'model-upload-help';
        yoloWorldHelp.textContent = 'YOLO-World adalah model zero-shot open-vocabulary. Kosongkan untuk mengunduh yolov8s-worldv2.pt resmi, atau arahkan ke checkpoint lokal.';
        wrap.append(yoloWorldHelp);
      } else if (['detector', 'segmenter'].includes(node.type) && ['customModelPath', 'modelPath', 'rfdetrCheckpoint', 'rfdetrOnnxModel', 'rfdetrTensorRTEngine', 'samCheckpoint'].includes(key)) {
        const uploadHelp = document.createElement('small');
        uploadHelp.className = 'model-upload-help';
        uploadHelp.textContent = 'Unggah model custom lewat tombol Upload di samping kolom ini atau Upload Model di toolbar atas. File masuk ke data/models dan diterapkan ke node ini. Untuk segmentasi, gunakan bobot model segmentasi yang sesuai dengan engine (.pt atau .onnx).';
        wrap.append(uploadHelp);
      }

      if (!isRoboflow && state.models && state.models.length > 0) {
        const picker = document.createElement('select');
        picker.style.marginTop = '6px';
        picker.style.fontWeight = '500';
        const emptyOpt = document.createElement('option');
        emptyOpt.value = '';
        emptyOpt.textContent = '-- Select model from Model Registry --';
        picker.append(emptyOpt);

        const groups = {};
        state.models.forEach(m => {
          const type = m.type || (m.isCustom ? 'Custom Models' : 'Foundation Models');
          if (!groups[type]) groups[type] = [];
          groups[type].push(m);
        });

        Object.keys(groups).forEach(grpName => {
          const optgroup = document.createElement('optgroup');
          optgroup.label = `── ${grpName} ──`;
          groups[grpName].forEach(m => {
            const opt = document.createElement('option');
            opt.value = m.name || m.path;
            const sizeLabel = m.sizeFormatted ? ` · ${m.sizeFormatted}` : '';
            opt.textContent = `${m.name} (${m.engine || m.format}${sizeLabel})`;
            if (String(value) === m.path || String(value) === m.name) {
              opt.selected = true;
            }
            optgroup.append(opt);
          });
          picker.append(optgroup);
        });

        picker.onchange = async () => {
          if (picker.value) {
            input.value = picker.value;
            node.config[key] = picker.value;
            markDirty();
            await inspectAndApplyModel(node, picker.value);
          }
        };
        wrap.append(picker);
      }
      appendHelp(wrap, key);
      return wrap;
    }

    // 3b. Classes filter and label import (.txt / .json)
    if (['classes', 'customClasses', 'rfdetrOnnxClasses', 'rfdetrTensorRTClasses', 'convnextClasses'].includes(key)) {
      const row = document.createElement('div');
      row.className = 'field-row';
      const input = document.createElement('input');
      input.type = 'text';
      input.value = value ?? '';
      input.placeholder = 'e.g. person, car, dog (or load labels.txt)';
      input.onchange = () => {
        node.config[key] = input.value;
        markDirty();
      };

      const loadLabelsBtn = document.createElement('button');
      loadLabelsBtn.type = 'button';
      loadLabelsBtn.className = 'button ghost';
      loadLabelsBtn.title = 'Import labels from labels.txt / classes.json';
      loadLabelsBtn.innerHTML = '<svg class="icon-svg icon-sm" viewBox="0 0 24 24"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg> Load .txt';

      const fileInput = document.createElement('input');
      fileInput.type = 'file';
      fileInput.accept = '.txt,.json,.yaml';
      fileInput.style.display = 'none';
      fileInput.onchange = (e) => {
        const file = e.target.files?.[0];
        if (!file) return;
        const reader = new FileReader();
        reader.onload = (evt) => {
          try {
            const text = evt.target.result;
            let classList = [];
            if (file.name.endsWith('.json')) {
              const parsed = JSON.parse(text);
              classList = Array.isArray(parsed) ? parsed : Object.values(parsed);
            } else {
              classList = text.split(/\r?\n/).map(l => l.trim()).filter(Boolean);
            }
            if (classList.length > 0) {
              const joined = classList.join(', ');
              input.value = joined;
              node.config[key] = joined;
              markDirty();
              toast(`Loaded ${classList.length} classes from ${file.name}`);
            }
          } catch (err) {
            toast('Failed to parse label file: ' + err.message, true);
          }
        };
        reader.readAsText(file);
      };

      loadLabelsBtn.onclick = () => fileInput.click();
      row.append(input, loadLabelsBtn, fileInput);
      wrap.append(row);
      appendHelp(wrap, key);
      return wrap;
    }

    // 4. Color inputs
    if (key.toLowerCase().includes('color') && typeof value === 'string' && (value.startsWith('#') || value.length === 7)) {
      const pickerWrap = document.createElement('div');
      pickerWrap.className = 'field-color-picker';
      const colorInput = document.createElement('input');
      colorInput.type = 'color';
      colorInput.value = value.startsWith('#') ? value : '#2563eb';
      const textInput = document.createElement('input');
      textInput.type = 'text';
      textInput.value = value;
      textInput.style.flex = '1';

      colorInput.oninput = () => {
        textInput.value = colorInput.value;
        node.config[key] = colorInput.value;
        markDirty();
      };
      textInput.onchange = () => {
        colorInput.value = textInput.value;
        node.config[key] = textInput.value;
        markDirty();
      };

      pickerWrap.append(colorInput, textInput);
      wrap.append(pickerWrap);
      appendHelp(wrap, key);
      return wrap;
    }

    // 5. Numeric and bounded fields with interactive dual controls
    let bounds = FIELD_BOUNDS[key];
    // Dynamic bounds for condition nodes (if_else, compare_value)
    if ((node.type === 'if_else' || node.type === 'compare_value') && key === 'value') {
      const metric = node.config?.metric || 'object_count';
      if (metric === 'max_confidence' || metric === 'anomaly_score') {
        bounds = { min: 0.0, max: 1.0, step: 0.01, isSlider: true, unit: '' };
      } else {
        bounds = { min: 0, max: 1000, step: 1, isSlider: true, unit: 'obj' };
      }
    }

    if (bounds || typeof value === 'number') {
      const b = bounds || { min: 0, max: 10000, step: 1, isSlider: false, unit: '' };
      const min = b.min !== undefined ? b.min : 0;
      const max = b.max !== undefined ? b.max : 10000;
      const step = b.step !== undefined ? b.step : (typeof value === 'number' && !Number.isInteger(value) ? 0.01 : 1);
      const isSlider = b.isSlider && max !== undefined && min !== undefined;

      const clampVal = (v) => {
        let n = Number(v);
        if (isNaN(n)) n = min;
        if (n < min) n = min;
        if (n > max) n = max;
        if (b.oddOnly && Math.round(n) % 2 === 0) {
          n = (n + 1 <= max) ? n + 1 : Math.max(min, n - 1);
        }
        return (step >= 1) ? Math.round(n) : Number(n.toFixed(3));
      };

      const initialVal = clampVal(value !== undefined && value !== null ? value : min);

      if (isSlider) {
        const group = document.createElement('div');
        group.className = 'field-slider-group';

        const row = document.createElement('div');
        row.className = 'field-slider-row';

        const range = document.createElement('input');
        range.type = 'range';
        range.min = String(min);
        range.max = String(max);
        range.step = String(step);
        range.value = String(initialVal);

        const numWrap = document.createElement('div');
        numWrap.className = 'field-num-wrap';

        const numInput = document.createElement('input');
        numInput.type = 'number';
        numInput.min = String(min);
        numInput.max = String(max);
        numInput.step = String(step);
        numInput.value = String(initialVal);

        range.oninput = () => {
          const clamped = clampVal(range.value);
          numInput.value = String(clamped);
          node.config[key] = clamped;
          markDirty();
        };

        const applyNumChange = () => {
          const clamped = clampVal(numInput.value);
          numInput.value = String(clamped);
          range.value = String(clamped);
          node.config[key] = clamped;
          markDirty();
        };

        numInput.oninput = () => {
          if (numInput.value !== '') {
            const raw = Number(numInput.value);
            if (raw > max) numInput.value = String(max);
            if (raw < min) numInput.value = String(min);
            const clamped = clampVal(numInput.value);
            range.value = String(clamped);
            node.config[key] = clamped;
            markDirty();
          }
        };
        numInput.onchange = applyNumChange;
        numInput.onblur = applyNumChange;

        numWrap.append(numInput);
        if (b.unit) {
          const unitSpan = document.createElement('span');
          unitSpan.className = 'field-unit-badge';
          unitSpan.textContent = b.unit;
          numWrap.append(unitSpan);
        }

        row.append(range, numWrap);
        group.append(row);

        const boundsHint = document.createElement('div');
        boundsHint.className = 'field-bounds-hint';
        boundsHint.innerHTML = `<span>Rentang Nilai:</span> <span class="bounds-range">${min} — ${max}${b.unit ? ' ' + b.unit : ''}</span>`;
        group.append(boundsHint);

        wrap.append(group);
      } else {
        const numInput = document.createElement('input');
        numInput.type = 'number';
        numInput.min = String(min);
        if (max !== undefined) numInput.max = String(max);
        numInput.step = String(step);
        numInput.value = String(initialVal);

        const applyVal = () => {
          const clamped = clampVal(numInput.value);
          numInput.value = String(clamped);
          node.config[key] = clamped;
          markDirty();
        };
        numInput.oninput = () => {
          if (numInput.value !== '') {
            const raw = Number(numInput.value);
            if (raw > max) numInput.value = String(max);
            if (raw < min) numInput.value = String(min);
            node.config[key] = clampVal(numInput.value);
            markDirty();
          }
        };
        numInput.onchange = applyVal;
        numInput.onblur = applyVal;

        wrap.append(numInput);
      }

      // Add interactive ROI helper button for crop & roi_filter
      if (['crop', 'roi_filter'].includes(node.type) && key === 'x') {
        const drawBtn = document.createElement('button');
        drawBtn.type = 'button';
        drawBtn.className = 'roi-draw-helper-btn';
        drawBtn.innerHTML = '<svg class="icon-svg icon-sm" viewBox="0 0 24 24"><path d="M3 3h7v7H3z"/><path d="M14 3h7v7h-7z"/><path d="M14 14h7v7h-7z"/><path d="M3 14h7v7H3z"/></svg> 📐 Gambar / Pilih Area Langsung di Preview';
        drawBtn.onclick = () => startRoiDrawing(node);
        wrap.append(drawBtn);
      }

      appendHelp(wrap, key);
      return wrap;
    }

    // 6. Boolean checkbox
    if (typeof value === 'boolean') {
      const line = document.createElement('label');
      line.className = 'field-check';
      const input = document.createElement('input');
      input.type = 'checkbox';
      input.checked = value;
      input.onchange = () => {
        node.config[key] = input.checked;
        markDirty();
      };
      line.append(input, document.createTextNode(labelText.textContent));
      wrap.replaceChildren(line);
      appendHelp(wrap, key);
      return wrap;
    }

    // 7. Arrays or Objects (JSON textarea)
    if (Array.isArray(value) || (value && typeof value === 'object')) {
      const textarea = document.createElement('textarea');
      textarea.value = JSON.stringify(value, null, 2);
      textarea.onchange = () => {
        try {
          node.config[key] = JSON.parse(textarea.value);
          markDirty();
        } catch {
          toast(`Invalid JSON for ${key}`, true);
        }
      };
      wrap.append(textarea);
      appendHelp(wrap, key);
      return wrap;
    }

    // 7b. Multiline prompt textareas for AI Agent
    if (['systemPrompt', 'userPrompt', 'jsonSchema'].includes(key)) {
      const textarea = document.createElement('textarea');
      textarea.rows = key === 'userPrompt' ? 4 : 3;
      textarea.value = value ?? '';
      if (key === 'userPrompt') {
        textarea.placeholder = 'Gunakan variabel {{detections}}, {{event}}, {{detection_count}}, {{timestamp}}';
      } else if (key === 'systemPrompt') {
        textarea.placeholder = 'Instruksi sistem / persona agen AI...';
      }
      textarea.onchange = () => {
        node.config[key] = textarea.value;
        markDirty();
      };
      wrap.append(textarea);
      appendHelp(wrap, key);
      return wrap;
    }

    // 8. General text input
    const input = document.createElement('input');
    input.name = key;
    input.dataset.fieldKey = key;
    if (key === 'apiKey') {
      input.type = 'password';
      input.placeholder = (node.type === 'ai_agent')
        ? 'Kosongkan untuk pakai .env (OPENAI_API_KEY / OPENROUTER_API_KEY)'
        : 'Kosongkan untuk pakai .env (OPENROUTER_API_KEY / TYPESAFE_API_KEY)';
    } else {
      input.type = 'text';
      if (key === 'objectPrompt') {
        input.placeholder = 'e.g. tire, worker, forklift';
      } else if (key === 'model') {
        input.placeholder = (node.type === 'ai_agent') ? 'e.g. gpt-4o-mini, gpt-4o, claude-3-5-sonnet' : 'e.g. google/gemini-2.0-flash-001';
      } else if (key === 'baseUrl') {
        input.placeholder = 'e.g. http://localhost:11434/v1';
      }
    }
    input.value = value ?? '';
    input.onchange = () => {
      node.config[key] = input.value;
      markDirty();
    };
    wrap.append(input);

    // ROI keeps its rectangle tool; polygon nodes use the preview editor.
    if (key === 'points' && ['roi_filter', 'dwell_time', 'zone_activity_timer', 'zone_exit_event'].includes(node.type)) {
      const drawBtn = document.createElement('button');
      drawBtn.type = 'button';
      drawBtn.className = 'roi-draw-helper-btn';
      const rectangleRoi = node.type === 'roi_filter';
      drawBtn.innerHTML = `<svg class="icon-svg icon-sm" viewBox="0 0 24 24"><polygon points="3 3 21 3 21 21 3 21"/></svg> 📐 ${rectangleRoi ? 'Gambar Persegi ROI' : 'Gambar Poligon Zona'} di Preview`;
      drawBtn.setAttribute('aria-label', rectangleRoi ? 'Gambar persegi ROI di preview' : 'Buka editor poligon zona di preview');
      drawBtn.onclick = () => ['roi_filter'].includes(node.type) ? startRoiDrawing(node) : startPolygonZoneDrawing(node);
      wrap.append(drawBtn);
    }
    return wrap;
  }

  function appendHelp(wrap, key) {
    // Keterangan di bawah field dinonaktifkan agar tidak kedouble dengan tooltip (?)
    return;
  }


  function startRoiDrawing(node) {
    const img = $('#previewImage');
    if (!img) return toast('Select a Preview node or start pipeline to draw ROI', true);
    toast('Click and drag on the preview image to select ROI region...');
    img.style.cursor = 'crosshair';
    let startX = 0, startY = 0, isDrawing = false;

    const onMouseDown = (e) => {
      const rect = img.getBoundingClientRect();
      startX = (e.clientX - rect.left) / rect.width;
      startY = (e.clientY - rect.top) / rect.height;
      isDrawing = true;
      e.preventDefault();
    };

    const onMouseUp = (e) => {
      if (!isDrawing) return;
      isDrawing = false;
      img.style.cursor = 'default';
      img.removeEventListener('mousedown', onMouseDown);
      window.removeEventListener('mouseup', onMouseUp);

      const rect = img.getBoundingClientRect();
      const endX = (e.clientX - rect.left) / rect.width;
      const endY = (e.clientY - rect.top) / rect.height;

      const w = img.naturalWidth || 1280;
      const h = img.naturalHeight || 720;

      const x1 = Math.max(0, Math.min(startX, endX));
      const y1 = Math.max(0, Math.min(startY, endY));
      const x2 = Math.min(1, Math.max(startX, endX));
      const y2 = Math.min(1, Math.max(startY, endY));

      const boxX = Math.round(x1 * w);
      const boxY = Math.round(y1 * h);
      const boxW = Math.max(10, Math.round((x2 - x1) * w));
      const boxH = Math.max(10, Math.round((y2 - y1) * h));

      node.config.x = boxX;
      node.config.y = boxY;
      node.config.width = boxW;
      node.config.height = boxH;
      markDirty();
      renderInspector();
      toast(`ROI region set: ${boxW}x${boxH} at (${boxX}, ${boxY})`);
    };

    img.addEventListener('mousedown', onMouseDown);
    window.addEventListener('mouseup', onMouseUp);
  }

  async function liveUpdateWorkflow() {
    if (!state.workflow) return;
    try {
      await api('/api/workflow/live-update', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ projectId: state.project?.id, workflow: state.workflow }),
      });
    } catch {
      // Ignore if server is not running or doesn't support live update
    }
  }

  const LINE_PALETTE = ['#22c55e', '#3b82f6', '#f59e0b', '#ec4899', '#8b5cf6', '#06b6d4', '#e11d48'];

  function getOrCreateNodeLines(node) {
    if (!node.config) node.config = {};
    if (!Array.isArray(node.config.lines) || node.config.lines.length === 0) {
      node.config.lines = [{
        id: 'line_1',
        name: 'Line 1',
        startPoint: node.config.startPoint || '',
        endPoint: node.config.endPoint || '',
        invertDirection: !!node.config.invertDirection,
        countMode: node.config.countMode || 'both',
        lineColor: node.config.lineColor || '#22c55e',
        inLabel: node.config.inLabel || 'IN',
        outLabel: node.config.outLabel || 'OUT',
        countIn: 0,
        countOut: 0,
      }];
    }
    return node.config.lines;
  }

  async function addNewLine(node) {
    const lines = getOrCreateNodeLines(node);
    const newIdx = lines.length + 1;
    const color = LINE_PALETTE[(newIdx - 1) % LINE_PALETTE.length];
    const newLine = {
      id: `line_${Date.now()}_${newIdx}`,
      name: `Line ${newIdx}`,
      startPoint: '',
      endPoint: '',
      invertDirection: false,
      countMode: 'both',
      lineColor: color,
      inLabel: 'IN',
      outLabel: 'OUT',
      countIn: 0,
      countOut: 0,
    };
    lines.push(newLine);
    markDirty();
    renderInspector();
    await save();
    await liveUpdateWorkflow();
    toast(`Garis baru "${newLine.name}" berhasil ditambahkan. Klik ✏️ Gambar untuk menggambar garis.`);
  }

  async function removeLine(node, lineIndex) {
    const lines = getOrCreateNodeLines(node);
    if (lines.length <= 1) {
      return clearLineDrawing(node, 0);
    }
    const removed = lines.splice(lineIndex, 1)[0];
    if (lineIndex === 0 && lines.length > 0) {
      node.config.startPoint = lines[0].startPoint;
      node.config.endPoint = lines[0].endPoint;
    }
    markDirty();
    renderInspector();
    await save();
    await liveUpdateWorkflow();
    await resetLineCounts(node, removed.id);
    toast(`Garis "${removed.name}" telah dihapus.`);
  }

  async function swapLineDirection(node, lineIndex = 0) {
    const lines = getOrCreateNodeLines(node);
    const line = lines[lineIndex];
    if (!line) return;
    line.invertDirection = !line.invertDirection;
    if (lineIndex === 0) {
      node.config.invertDirection = line.invertDirection;
    }
    markDirty();
    renderInspector();
    await save();
    await liveUpdateWorkflow();
    toast(`Arah "${line.name}" ditukar: ${line.invertDirection ? 'Inverted (OUT ➔ IN)' : 'Normal (IN ➔ OUT)'}`);
  }

  async function resetLineCounts(node, lineId = null) {
    const lines = getOrCreateNodeLines(node);
    if (lineId) {
      const line = lines.find((l) => l.id === lineId);
      if (line) {
        line.countIn = 0;
        line.countOut = 0;
      }
    } else {
      lines.forEach((l) => {
        l.countIn = 0;
        l.countOut = 0;
      });
    }
    renderInspector();

    try {
      await api('/api/counters/reset', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ nodeId: node.id, lineId: lineId }),
      });
    } catch {
      // Local count was already reset to 0 in UI; ignore API transport delay
    }

    if (lineId) {
      const line = lines.find((l) => l.id === lineId);
      toast(`Hitungan "${line ? line.name : 'Garis'}" direset ke 0`);
    } else {
      toast(`Semua hitungan ${node.title || 'Line Counter'} direset ke 0`);
    }
  }

  async function clearLineDrawing(node, lineIndex = 0) {
    const lines = getOrCreateNodeLines(node);
    const line = lines[lineIndex];
    if (!line) return;
    line.startPoint = '';
    line.endPoint = '';
    line.countIn = 0;
    line.countOut = 0;
    if (lineIndex === 0) {
      node.config.startPoint = '';
      node.config.endPoint = '';
    }
    markDirty();
    renderInspector();
    await save();
    await liveUpdateWorkflow();
    try {
      await resetLineCounts(node, line.id);
    } catch {}
    toast(`Garis "${line.name}" berhasil dihapus (kosong)`);
  }

  async function clearAllLinesDrawing(node) {
    const lines = getOrCreateNodeLines(node);
    lines.forEach((line) => {
      line.startPoint = '';
      line.endPoint = '';
      line.countIn = 0;
      line.countOut = 0;
    });
    node.config.startPoint = '';
    node.config.endPoint = '';
    markDirty();
    renderInspector();
    await save();
    await liveUpdateWorkflow();
    try {
      await resetLineCounts(node);
    } catch {}
    toast('Semua gambar garis berhasil dihapus (kosong)');
  }

  function startLineDrawing(node, lineIndex = 0) {
    const img = $('#previewImage');
    if (!img) return toast('Jalankan pipeline terlebih dahulu untuk menampilkan video & menggambar garis', true);

    const lines = getOrCreateNodeLines(node);
    const line = lines[lineIndex] || lines[0];
    const drawColor = line.lineColor || '#22c55e';

    toast(`Klik dan seret (drag) mouse di atas video preview untuk menggambar garis "${line.name}"...`);
    img.style.cursor = 'crosshair';

    $('#tempDrawOverlay')?.remove();

    const parent = img.parentElement;
    if (parent && getComputedStyle(parent).position === 'static') {
      parent.style.position = 'relative';
    }

    const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    svg.id = 'tempDrawOverlay';
    svg.style.position = 'absolute';
    svg.style.top = img.offsetTop + 'px';
    svg.style.left = img.offsetLeft + 'px';
    svg.style.width = img.clientWidth + 'px';
    svg.style.height = img.clientHeight + 'px';
    svg.style.pointerEvents = 'none';
    svg.style.zIndex = '50';
    if (parent) parent.appendChild(svg);

    let startX = 0, startY = 0, isDrawing = false;

    const onMouseDown = (e) => {
      const rect = img.getBoundingClientRect();
      startX = (e.clientX - rect.left) / rect.width;
      startY = (e.clientY - rect.top) / rect.height;
      isDrawing = true;
      e.preventDefault();
    };

    const onMouseMove = (e) => {
      if (!isDrawing) return;
      const rect = img.getBoundingClientRect();
      const curX = Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width));
      const curY = Math.max(0, Math.min(1, (e.clientY - rect.top) / rect.height));

      const w = img.clientWidth;
      const h = img.clientHeight;
      const x1 = startX * w, y1 = startY * h;
      const x2 = curX * w, y2 = curY * h;

      svg.innerHTML = `
        <line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" stroke="${drawColor}" stroke-width="3" stroke-linecap="round" />
        <circle cx="${x1}" cy="${y1}" r="6" fill="${drawColor}" stroke="#fff" stroke-width="2" />
        <circle cx="${x2}" cy="${y2}" r="6" fill="${drawColor}" stroke="#fff" stroke-width="2" />
      `;
    };

    const onMouseUp = async (e) => {
      if (!isDrawing) return;
      isDrawing = false;
      img.style.cursor = 'default';
      img.removeEventListener('mousedown', onMouseDown);
      window.removeEventListener('mousemove', onMouseMove);
      window.removeEventListener('mouseup', onMouseUp);
      svg.remove();

      const rect = img.getBoundingClientRect();
      const endX = Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width));
      const endY = Math.max(0, Math.min(1, (e.clientY - rect.top) / rect.height));

      const dist = Math.hypot(endX - startX, endY - startY);
      if (dist < 0.02) {
        return toast('Garis terlalu pendek, silakan seret lebih jauh melintasi area', true);
      }

      line.startPoint = `${startX.toFixed(3)},${startY.toFixed(3)}`;
      line.endPoint = `${endX.toFixed(3)},${endY.toFixed(3)}`;
      if (lineIndex === 0) {
        node.config.startPoint = line.startPoint;
        node.config.endPoint = line.endPoint;
      }
      markDirty();
      renderInspector();
      await save();
      await liveUpdateWorkflow();
      toast(`Garis "${line.name}" tersimpan: (${startX.toFixed(2)}, ${startY.toFixed(2)}) ➔ (${endX.toFixed(2)}, ${endY.toFixed(2)})`);
    };

    img.addEventListener('mousedown', onMouseDown);
    window.addEventListener('mousemove', onMouseMove);
    window.addEventListener('mouseup', onMouseUp);
  }

  function cancelActiveZoneEditor() {
    $('#previewImage')?._cancelZoneDrawing?.();
    $('#previewImage')?._cancelMultiZoneDrawing?.();
  }

  function startPolygonZoneDrawing(node) {
    const img = $('#previewImage');
    if (!img) return toast('Preview container tidak ditemukan', true);
    if (!img.naturalWidth || img.hidden) {
      const placeholderSvg = `<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="720" viewBox="0 0 1280 720">
        <rect width="100%" height="100%" fill="#090d16"/>
        <defs>
          <pattern id="camgrid" width="80" height="80" patternUnits="userSpaceOnUse">
            <path d="M 80 0 L 0 0 0 80" fill="none" stroke="rgba(255,255,255,0.06)" stroke-width="1"/>
          </pattern>
        </defs>
        <rect width="100%" height="100%" fill="url(#camgrid)" />
        <rect x="40" y="40" width="1200" height="640" fill="none" stroke="rgba(16,185,129,0.3)" stroke-width="1.5" stroke-dasharray="6 6"/>
        <text x="640" y="340" fill="#94a3b8" font-family="system-ui, sans-serif" font-size="24" text-anchor="middle" font-weight="600">📐 Frame Kalibrasi Area Kamera</text>
        <text x="640" y="380" fill="#64748b" font-family="system-ui, sans-serif" font-size="15" text-anchor="middle">Tentukan titik sudut poligon untuk menghitung durasi aktivitas kerja di zona ini</text>
      </svg>`;
      img.src = 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(placeholderSvg);
      img.hidden = false;
      $('#previewEmpty')?.setAttribute('hidden', 'true');
      img.onload = () => {
        startPolygonZoneDrawing(node);
      };
      return;
    }
    if (img._cancelZoneDrawing) img._cancelZoneDrawing();
    if (img._cancelMultiZoneDrawing) img._cancelMultiZoneDrawing();

    const parsePoints = (value) => String(value || '').split(';').map((part) => {
      const [x, y] = part.trim().split(',').map(Number);
      return Number.isFinite(x) && Number.isFinite(y) ? { x: Math.max(0, Math.min(1, x)), y: Math.max(0, Math.min(1, y)) } : null;
    }).filter(Boolean);
    const points = parsePoints(node.config.points);
    const original = node.config.points || '';
    const parent = img.parentElement;
    if (!parent) return;
    if (getComputedStyle(parent).position === 'static') parent.style.position = 'relative';

    const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    svg.classList.add('zone-preview-editor');
    svg.setAttribute('role', 'application');
    svg.setAttribute('aria-label', 'Editor poligon zona');
    const toolbar = document.createElement('div');
    toolbar.className = 'zone-preview-toolbar';
    const dragHandle = document.createElement('span');
    dragHandle.className = 'multi-zone-drag-handle';
    dragHandle.title = 'Zona';
    dragHandle.innerHTML = '<span style="font-size:11px;">📐</span>';

    const status = document.createElement('span');
    status.className = 'zone-preview-status';
    const removeBtn = document.createElement('button');
    removeBtn.type = 'button';
    removeBtn.className = 'button ghost';
    removeBtn.textContent = 'Hapus titik';
    removeBtn.disabled = true;

    const toggleBtn = document.createElement('button');
    toggleBtn.type = 'button';
    toggleBtn.className = 'button ghost';
    toggleBtn.title = 'Sembunyikan / Tampilkan detail';
    toggleBtn.innerHTML = '<span>👁️ Sembunyikan</span>';
    let zoneCollapsed = false;
    toggleBtn.onclick = (e) => {
      e.stopPropagation();
      zoneCollapsed = !zoneCollapsed;
      status.style.display = zoneCollapsed ? 'none' : '';
      removeBtn.style.display = zoneCollapsed ? 'none' : '';
      toggleBtn.innerHTML = zoneCollapsed ? '<span>👁️ Buka</span>' : '<span>👁️ Sembunyikan</span>';
    };

    const cancelBtn = document.createElement('button');
    cancelBtn.type = 'button';
    cancelBtn.className = 'button ghost';
    cancelBtn.textContent = 'Batal';
    const saveBtn = document.createElement('button');
    saveBtn.type = 'button';
    saveBtn.className = 'button primary';
    saveBtn.textContent = 'Simpan zona';
    toolbar.append(dragHandle, status, removeBtn, toggleBtn, cancelBtn, saveBtn);
    const oldZoneToolbar = parent.parentElement ? parent.parentElement.querySelector('.zone-preview-toolbar') : null;
    if (oldZoneToolbar) oldZoneToolbar.remove();
    if (parent.parentElement) {
      parent.parentElement.insertBefore(toolbar, parent);
    } else {
      parent.append(toolbar);
    }
    parent.append(svg);

    // Draggable
    let isDraggingZ = false, zStartX = 0, zStartY = 0, zInitL = 8, zInitT = 8;
    dragHandle.onmousedown = (e) => {
      e.preventDefault(); e.stopPropagation();
      isDraggingZ = true; zStartX = e.clientX; zStartY = e.clientY;
      const rect = toolbar.getBoundingClientRect();
      const parentRect = parent.getBoundingClientRect();
      zInitL = rect.left - parentRect.left;
      zInitT = rect.top - parentRect.top;
      const onMoveZ = (ev) => {
        if (!isDraggingZ) return;
        const pR = parent.getBoundingClientRect();
        const tR = toolbar.getBoundingClientRect();
        const nL = Math.max(2, Math.min(pR.width - tR.width - 4, zInitL + (ev.clientX - zStartX)));
        const nT = Math.max(2, Math.min(pR.height - tR.height - 4, zInitT + (ev.clientY - zStartY)));
        toolbar.style.left = `${nL}px`; toolbar.style.top = `${nT}px`;
      };
      const onUpZ = () => {
        isDraggingZ = false;
        document.removeEventListener('mousemove', onMoveZ);
        document.removeEventListener('mouseup', onUpZ);
      };
      document.addEventListener('mousemove', onMoveZ);
      document.addEventListener('mouseup', onUpZ);
    };

    let selected = -1;
    let suppressAddClick = false;
    let disposed = false;
    const editorProjectId = state.project?.id;
    let resizeObserver;
    const imageBox = () => {
      const frame = parent.getBoundingClientRect();
      const rect = img.getBoundingClientRect();
      const fit = Math.min(rect.width / img.naturalWidth, rect.height / img.naturalHeight);
      const width = img.naturalWidth * fit;
      const height = img.naturalHeight * fit;
      return { left: rect.left - frame.left + (rect.width - width) / 2, top: rect.top - frame.top + (rect.height - height) / 2, width, height };
    };
    const pointAt = (event) => {
      const box = imageBox();
      const frame = parent.getBoundingClientRect();
      const x = (event.clientX - frame.left - box.left) / box.width;
      const y = (event.clientY - frame.top - box.top) / box.height;
      return x >= 0 && x <= 1 && y >= 0 && y <= 1 ? { x, y } : null;
    };
    const cleanup = () => {
      if (disposed) return;
      disposed = true;
      resizeObserver?.disconnect();
      window.removeEventListener('keydown', onKey);
      img.removeEventListener('load', draw);
      img.style.cursor = 'default';
      svg.remove();
      toolbar.remove();
      delete img._cancelZoneDrawing;
    };
    const draw = () => {
      if (disposed) return;
      const box = imageBox();
      svg.style.left = `${box.left}px`; svg.style.top = `${box.top}px`;
      svg.setAttribute('width', String(box.width)); svg.setAttribute('height', String(box.height));
      svg.setAttribute('viewBox', `0 0 ${box.width} ${box.height}`);
      svg.replaceChildren();
      const valid = points.length >= 3;
      status.textContent = `${points.length} titik${valid ? '' : ' (minimal 3)'}. Klik gambar untuk menambah, seret titik untuk memindahkan.`;
      removeBtn.disabled = selected < 0 || points.length <= 3;
      if (points.length > 1) {
        const polygon = document.createElementNS('http://www.w3.org/2000/svg', 'polygon');
        polygon.setAttribute('points', points.map(p => `${p.x * box.width},${p.y * box.height}`).join(' '));
        polygon.setAttribute('class', 'zone-preview-polygon');
        svg.append(polygon);
      }
      points.forEach((point, index) => {
        const handle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
        handle.setAttribute('cx', String(point.x * box.width)); handle.setAttribute('cy', String(point.y * box.height));
        handle.setAttribute('r', index === selected ? '8' : '6'); handle.setAttribute('class', `zone-preview-vertex${index === selected ? ' selected' : ''}`);
        handle.setAttribute('tabindex', '0'); handle.setAttribute('aria-label', `Titik zona ${index + 1}`);
        handle.onpointerdown = (event) => {
          event.preventDefault(); event.stopPropagation(); suppressAddClick = true; selected = index; draw();
          const move = (moveEvent) => { const next = pointAt(moveEvent); if (next) { points[index] = next; draw(); } };
          const up = () => { window.removeEventListener('pointermove', move); window.removeEventListener('pointerup', up); setTimeout(() => { suppressAddClick = false; }, 0); };
          window.addEventListener('pointermove', move); window.addEventListener('pointerup', up, { once: true });
        };
        handle.onclick = (event) => { event.stopPropagation(); selected = index; draw(); };
        svg.append(handle);
      });
    };
    const onKey = (event) => {
      if (event.key === 'Escape') { event.preventDefault(); cleanup(); toast('Gambar zona dibatalkan'); return; }
      if (['INPUT', 'TEXTAREA', 'SELECT'].includes(event.target?.tagName) || event.target?.isContentEditable) return;
      if (event.key === 'Delete' || event.key === 'Backspace') {
        event.preventDefault();
        if (selected >= 0 && points.length > 3) { points.splice(selected, 1); selected = -1; draw(); }
      }
    };
    const onAdd = (event) => {
      if (event.target !== svg || suppressAddClick) return;
      const point = pointAt(event); if (!point) return;
      points.push(point); selected = points.length - 1; draw();
    };
    const commit = async () => {
      if (points.length < 3) return toast('Zona membutuhkan minimal 3 titik', true);
      if (state.project?.id !== editorProjectId || nodeFor(node.id) !== node) {
        cleanup();
        return toast('Project atau node sudah berubah; editor zona dibatalkan', true);
      }
      const value = points.map(p => `${p.x.toFixed(3)},${p.y.toFixed(3)}`).join('; ');
      node.config.points = value; markDirty();
      const saved = await save();
      if (!saved) { node.config.points = original; markDirty(); renderInspector(); return; }
      await liveUpdateWorkflow(); cleanup(); renderInspector(); toast(`${titleFor(node.type)} zone polygon tersimpan`);
    };
    removeBtn.onclick = () => { if (selected >= 0 && points.length > 3) { points.splice(selected, 1); selected = -1; draw(); } };
    cancelBtn.onclick = () => { cleanup(); toast('Gambar zona dibatalkan'); };
    saveBtn.onclick = commit;
    svg.addEventListener('click', onAdd);
    window.addEventListener('keydown', onKey);
    img.addEventListener('load', draw);
    img.style.cursor = 'crosshair';
    img._cancelZoneDrawing = cleanup;
    resizeObserver = new ResizeObserver(draw);
    resizeObserver.observe(parent);
    draw();
    toast('Editor zona aktif. Simpan hanya setelah bentuk zona selesai.');
  }

  function startMultiZoneDrawing(node) {
    const img = $('#previewImage');
    if (!img) return toast('Preview container tidak ditemukan', true);
    if (!img.naturalWidth || img.hidden) {
      const placeholderSvg = `<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="720" viewBox="0 0 1280 720">
        <rect width="100%" height="100%" fill="#090d16"/>
        <defs>
          <pattern id="camgrid2" width="80" height="80" patternUnits="userSpaceOnUse">
            <path d="M 80 0 L 0 0 0 80" fill="none" stroke="rgba(255,255,255,0.06)" stroke-width="1"/>
          </pattern>
        </defs>
        <rect width="100%" height="100%" fill="url(#camgrid2)" />
        <rect x="40" y="40" width="1200" height="640" fill="none" stroke="rgba(56,189,248,0.3)" stroke-width="1.5" stroke-dasharray="6 6"/>
        <text x="640" y="340" fill="#94a3b8" font-family="system-ui, sans-serif" font-size="24" text-anchor="middle" font-weight="600">📐 Frame Kalibrasi Multi-Zone / Area</text>
        <text x="640" y="380" fill="#64748b" font-family="system-ui, sans-serif" font-size="15" text-anchor="middle">Tentukan poligon setiap area (Meja/Bay/Zona) untuk memantau okupansi dan durasi</text>
      </svg>`;
      img.src = 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(placeholderSvg);
      img.hidden = false;
      $('#previewEmpty')?.setAttribute('hidden', 'true');
      img.onload = () => {
        startMultiZoneDrawing(node);
      };
      return;
    }

    if (img._cancelZoneDrawing) img._cancelZoneDrawing();
    if (img._cancelMultiZoneDrawing) img._cancelMultiZoneDrawing();

    if (!node.config) node.config = {};
    let rawZones = node.config.zones;
    if (typeof rawZones === 'string') {
      try { rawZones = JSON.parse(rawZones); } catch { rawZones = null; }
    }
    if (!Array.isArray(rawZones) || rawZones.length === 0) {
      rawZones = [
        { id: 'zone_1', name: 'Zona A', capacity: 4, points: '0.15,0.20; 0.45,0.20; 0.45,0.80; 0.15,0.80' },
        { id: 'zone_2', name: 'Zona B', capacity: 2, points: '0.55,0.20; 0.85,0.20; 0.85,0.80; 0.55,0.80' }
      ];
    }

    const parsePoints = (value) => String(value || '').split(';').map((part) => {
      const [x, y] = part.trim().split(',').map(Number);
      return Number.isFinite(x) && Number.isFinite(y) ? { x: Math.max(0, Math.min(1, x)), y: Math.max(0, Math.min(1, y)) } : null;
    }).filter(Boolean);

    const workingZones = rawZones.map((z, idx) => ({
      id: z.id || ('zone_' + (idx + 1)),
      name: z.name || ('Zona ' + (idx + 1)),
      capacity: parseInt(z.capacity, 10) || 4,
      points: parsePoints(z.points)
    }));

    let activeIndex = 0;
    let selectedVertex = -1;
    let suppressAddClick = false;
    let disposed = false;
    const editorProjectId = state.project?.id;
    let resizeObserver;

    const parent = img.parentElement;
    if (!parent) return;
    if (getComputedStyle(parent).position === 'static') parent.style.position = 'relative';

    const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    svg.classList.add('zone-preview-editor');
    svg.setAttribute('role', 'application');
    svg.setAttribute('aria-label', 'Editor Multi-Zone');

    const toolbar = document.createElement('div');
    toolbar.className = 'zone-preview-toolbar multi-zone-toolbar';

    // Header bar (always visible, draggable, compact status, hide/unhide toggle, Batal, Simpan)
    const headerBar = document.createElement('div');
    headerBar.className = 'multi-zone-toolbar-header';

    const dragHandle = document.createElement('div');
    dragHandle.className = 'multi-zone-drag-handle';
    dragHandle.title = 'Multi-Area Editor';
    dragHandle.innerHTML = '<span style="font-size:11px;">📐</span>';

    const activePill = document.createElement('span');
    activePill.className = 'multi-zone-active-pill';
    activePill.style.display = 'none';

    const zoneSelect = document.createElement('select');
    zoneSelect.className = 'multi-zone-select';
    zoneSelect.title = 'Pilih area aktif';

    const addZoneBtn = document.createElement('button');
    addZoneBtn.type = 'button';
    addZoneBtn.className = 'button ghost';
    addZoneBtn.textContent = '+ Area';
    addZoneBtn.title = 'Tambah area / zona baru';

    const delZoneBtn = document.createElement('button');
    delZoneBtn.type = 'button';
    delZoneBtn.className = 'button ghost';
    delZoneBtn.innerHTML = '🗑️';
    delZoneBtn.title = 'Hapus area aktif';

    const toggleBtn = document.createElement('button');
    toggleBtn.type = 'button';
    toggleBtn.className = 'button ghost multi-zone-toggle-btn';
    toggleBtn.title = 'Buka/Tutup pengaturan detail';
    toggleBtn.innerHTML = '<span class="toggle-icon">⚙️</span>';

    const cancelBtn = document.createElement('button');
    cancelBtn.type = 'button';
    cancelBtn.className = 'button ghost';
    cancelBtn.textContent = 'Batal';

    const saveBtn = document.createElement('button');
    saveBtn.type = 'button';
    saveBtn.className = 'button primary';
    saveBtn.textContent = 'Simpan Semua Area';

    headerBar.append(dragHandle, activePill, zoneSelect, addZoneBtn, delZoneBtn, toggleBtn, cancelBtn, saveBtn);

    // Body panel (contains compact name, capacity, point removal, status)
    const bodyPanel = document.createElement('div');
    bodyPanel.className = 'multi-zone-toolbar-body';

    const nameLabel = document.createElement('span');
    nameLabel.style.fontSize = '10px';
    nameLabel.style.color = '#64748b';
    nameLabel.textContent = 'Nama:';

    const nameInput = document.createElement('input');
    nameInput.type = 'text';
    nameInput.className = 'multi-zone-name-input';
    nameInput.placeholder = 'Nama Area';

    const capLabel = document.createElement('span');
    capLabel.style.fontSize = '10px';
    capLabel.style.color = '#64748b';
    capLabel.textContent = 'Maks:';

    const capInput = document.createElement('input');
    capInput.type = 'number';
    capInput.min = '1';
    capInput.max = '999';
    capInput.className = 'multi-zone-cap-input';
    capInput.title = 'Kapasitas maksimal';

    const removePointBtn = document.createElement('button');
    removePointBtn.type = 'button';
    removePointBtn.className = 'button ghost';
    removePointBtn.textContent = 'Hapus Titik';
    removePointBtn.disabled = true;

    const status = document.createElement('span');
    status.className = 'zone-preview-status';

    bodyPanel.append(nameLabel, nameInput, capLabel, capInput, removePointBtn, status);
    toolbar.append(headerBar, bodyPanel);
    const oldMultiToolbar = parent.parentElement ? parent.parentElement.querySelector('.zone-preview-toolbar') : null;
    if (oldMultiToolbar) oldMultiToolbar.remove();
    if (parent.parentElement) {
      parent.parentElement.insertBefore(toolbar, parent);
    } else {
      parent.append(toolbar);
    }
    parent.append(svg);

    // Toggle hide/unhide logic
    let isCollapsed = false;
    toggleBtn.onclick = (e) => {
      e.stopPropagation();
      isCollapsed = !isCollapsed;
      toolbar.classList.toggle('is-collapsed', isCollapsed);
      const iconSpan = toggleBtn.querySelector('.toggle-icon');
      const textSpan = toggleBtn.querySelector('.toggle-text');
      if (iconSpan) iconSpan.textContent = isCollapsed ? '⚙️' : '👁️';
      if (textSpan) textSpan.textContent = isCollapsed ? 'Buka Setting ▾' : 'Sembunyikan';
    };

    // Draggable logic
    let isDragging = false, dragStartX = 0, dragStartY = 0, initialLeft = 8, initialTop = 8;
    dragHandle.onmousedown = (e) => {
      e.preventDefault(); e.stopPropagation();
      isDragging = true; dragStartX = e.clientX; dragStartY = e.clientY;
      const rect = toolbar.getBoundingClientRect();
      const parentRect = parent.getBoundingClientRect();
      initialLeft = rect.left - parentRect.left;
      initialTop = rect.top - parentRect.top;
      const onMouseMove = (ev) => {
        if (!isDragging) return;
        const pR = parent.getBoundingClientRect();
        const tR = toolbar.getBoundingClientRect();
        const maxL = Math.max(0, pR.width - tR.width - 4);
        const maxT = Math.max(0, pR.height - tR.height - 4);
        const newL = Math.max(2, Math.min(maxL, initialLeft + (ev.clientX - dragStartX)));
        const newT = Math.max(2, Math.min(maxT, initialTop + (ev.clientY - dragStartY)));
        toolbar.style.left = `${newL}px`;
        toolbar.style.top = `${newT}px`;
      };
      const onMouseUp = () => {
        isDragging = false;
        document.removeEventListener('mousemove', onMouseMove);
        document.removeEventListener('mouseup', onMouseUp);
      };
      document.addEventListener('mousemove', onMouseMove);
      document.addEventListener('mouseup', onMouseUp);
    };

    const updateSelector = () => {
      zoneSelect.replaceChildren();
      workingZones.forEach((z, i) => {
        const opt = document.createElement('option');
        opt.value = String(i);
        opt.textContent = `${i + 1}. ${z.name || ('Zona ' + (i + 1))} (Cap: ${z.capacity})`;
        if (i === activeIndex) opt.selected = true;
        zoneSelect.append(opt);
      });
      const active = workingZones[activeIndex];
      if (active) {
        nameInput.value = active.name || '';
        capInput.value = active.capacity || 4;
        activePill.textContent = `${activeIndex + 1}. ${active.name || ('Zona ' + (activeIndex + 1))} (${active.capacity || 4})`;
      }
      delZoneBtn.disabled = workingZones.length <= 1;
    };

    zoneSelect.onchange = () => {
      activeIndex = parseInt(zoneSelect.value, 10) || 0;
      selectedVertex = -1;
      updateSelector();
      draw();
    };

    nameInput.oninput = () => {
      if (workingZones[activeIndex]) {
        workingZones[activeIndex].name = nameInput.value.trim() || `Zona ${activeIndex + 1}`;
        if (zoneSelect.options[activeIndex]) {
          zoneSelect.options[activeIndex].textContent = `${activeIndex + 1}. ${workingZones[activeIndex].name} (Cap: ${workingZones[activeIndex].capacity})`;
        }
      }
    };

    capInput.oninput = () => {
      if (workingZones[activeIndex]) {
        workingZones[activeIndex].capacity = Math.max(1, parseInt(capInput.value, 10) || 1);
        if (zoneSelect.options[activeIndex]) {
          zoneSelect.options[activeIndex].textContent = `${activeIndex + 1}. ${workingZones[activeIndex].name} (Cap: ${workingZones[activeIndex].capacity})`;
        }
      }
    };

    addZoneBtn.onclick = () => {
      const newIdx = workingZones.length + 1;
      const offsetX = Math.min(0.5, (newIdx * 0.08) % 0.5);
      const offsetY = Math.min(0.5, (newIdx * 0.08) % 0.5);
      workingZones.push({
        id: 'zone_' + Date.now(),
        name: 'Zona ' + newIdx,
        capacity: 4,
        points: [
          { x: 0.15 + offsetX, y: 0.20 + offsetY },
          { x: 0.35 + offsetX, y: 0.20 + offsetY },
          { x: 0.35 + offsetX, y: 0.50 + offsetY },
          { x: 0.15 + offsetX, y: 0.50 + offsetY }
        ]
      });
      activeIndex = workingZones.length - 1;
      selectedVertex = -1;
      updateSelector();
      draw();
      toast(`Area baru "Zona ${newIdx}" ditambahkan`);
    };

    delZoneBtn.onclick = () => {
      if (workingZones.length <= 1) return toast('Minimal harus memiliki 1 area', true);
      const removed = workingZones.splice(activeIndex, 1)[0];
      activeIndex = Math.max(0, activeIndex - 1);
      selectedVertex = -1;
      updateSelector();
      draw();
      toast(`Area "${removed.name}" dihapus`);
    };

    const imageBox = () => {
      const frame = parent.getBoundingClientRect();
      const rect = img.getBoundingClientRect();
      const fit = Math.min(rect.width / img.naturalWidth, rect.height / img.naturalHeight);
      const width = img.naturalWidth * fit;
      const height = img.naturalHeight * fit;
      return { left: rect.left - frame.left + (rect.width - width) / 2, top: rect.top - frame.top + (rect.height - height) / 2, width, height };
    };

    const pointAt = (event) => {
      const box = imageBox();
      const frame = parent.getBoundingClientRect();
      const x = (event.clientX - frame.left - box.left) / box.width;
      const y = (event.clientY - frame.top - box.top) / box.height;
      return x >= 0 && x <= 1 && y >= 0 && y <= 1 ? { x, y } : null;
    };

    const cleanup = () => {
      if (disposed) return;
      disposed = true;
      resizeObserver?.disconnect();
      window.removeEventListener('keydown', onKey);
      img.removeEventListener('load', draw);
      img.style.cursor = 'default';
      svg.remove();
      toolbar.remove();
      delete img._cancelMultiZoneDrawing;
    };

    const draw = () => {
      if (disposed) return;
      const box = imageBox();
      svg.style.left = `${box.left}px`;
      svg.style.top = `${box.top}px`;
      svg.setAttribute('width', String(box.width));
      svg.setAttribute('height', String(box.height));
      svg.setAttribute('viewBox', `0 0 ${box.width} ${box.height}`);
      svg.replaceChildren();

      const activeZone = workingZones[activeIndex];
      const activePts = activeZone ? activeZone.points : [];
      const valid = activePts.length >= 3;
      status.textContent = `[${activeZone?.name || 'Area'}] ${activePts.length} titik${valid ? '' : ' (min 3)'}. Klik area lain untuk berpindah.`;
      removePointBtn.disabled = selectedVertex < 0 || activePts.length <= 3;

      workingZones.forEach((z, zIdx) => {
        if (zIdx === activeIndex) return;
        if (z.points.length > 1) {
          const poly = document.createElementNS('http://www.w3.org/2000/svg', 'polygon');
          poly.setAttribute('points', z.points.map(p => `${p.x * box.width},${p.y * box.height}`).join(' '));
          poly.setAttribute('class', 'zone-preview-polygon passive-zone');
          poly.style.cursor = 'pointer';
          poly.onclick = (e) => {
            e.stopPropagation();
            activeIndex = zIdx;
            selectedVertex = -1;
            updateSelector();
            draw();
          };
          svg.append(poly);

          const avgX = z.points.reduce((sum, p) => sum + p.x, 0) / z.points.length;
          const avgY = z.points.reduce((sum, p) => sum + p.y, 0) / z.points.length;
          const label = document.createElementNS('http://www.w3.org/2000/svg', 'text');
          label.setAttribute('x', String(avgX * box.width));
          label.setAttribute('y', String(avgY * box.height));
          label.setAttribute('fill', '#94a3b8');
          label.setAttribute('font-size', '13');
          label.setAttribute('font-weight', '600');
          label.setAttribute('text-anchor', 'middle');
          label.setAttribute('dominant-baseline', 'middle');
          label.style.pointerEvents = 'none';
          label.textContent = z.name;
          svg.append(label);
        }
      });

      if (activeZone && activePts.length > 1) {
        const poly = document.createElementNS('http://www.w3.org/2000/svg', 'polygon');
        poly.setAttribute('points', activePts.map(p => `${p.x * box.width},${p.y * box.height}`).join(' '));
        poly.setAttribute('class', 'zone-preview-polygon active-zone');
        svg.append(poly);

        const avgX = activePts.reduce((sum, p) => sum + p.x, 0) / activePts.length;
        const avgY = activePts.reduce((sum, p) => sum + p.y, 0) / activePts.length;
        const label = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        label.setAttribute('x', String(avgX * box.width));
        label.setAttribute('y', String(avgY * box.height));
        label.setAttribute('fill', '#38bdf8');
        label.setAttribute('font-size', '14');
        label.setAttribute('font-weight', 'bold');
        label.setAttribute('text-anchor', 'middle');
        label.setAttribute('dominant-baseline', 'middle');
        label.style.pointerEvents = 'none';
        label.textContent = `${activeZone.name} (Maks ${activeZone.capacity})`;
        svg.append(label);
      }

      if (activeZone) {
        activePts.forEach((point, index) => {
          const handle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
          handle.setAttribute('cx', String(point.x * box.width));
          handle.setAttribute('cy', String(point.y * box.height));
          handle.setAttribute('r', index === selectedVertex ? '8' : '6');
          handle.setAttribute('class', `zone-preview-vertex${index === selectedVertex ? ' selected' : ''}`);
          handle.setAttribute('tabindex', '0');
          handle.setAttribute('aria-label', `Titik ${index + 1}`);

          handle.onpointerdown = (event) => {
            event.preventDefault();
            event.stopPropagation();
            suppressAddClick = true;
            selectedVertex = index;
            draw();
            const move = (moveEvent) => {
              const next = pointAt(moveEvent);
              if (next) {
                activePts[index] = next;
                draw();
              }
            };
            const up = () => {
              window.removeEventListener('pointermove', move);
              window.removeEventListener('pointerup', up);
              setTimeout(() => { suppressAddClick = false; }, 0);
            };
            window.addEventListener('pointermove', move);
            window.addEventListener('pointerup', up, { once: true });
          };

          handle.onclick = (event) => {
            event.stopPropagation();
            selectedVertex = index;
            draw();
          };

          svg.append(handle);
        });
      }
    };

    const onKey = (event) => {
      if (event.key === 'Escape') {
        event.preventDefault();
        cleanup();
        toast('Editor area dibatalkan');
        return;
      }
      if (['INPUT', 'TEXTAREA', 'SELECT'].includes(event.target?.tagName) || event.target?.isContentEditable) return;
      if (event.key === 'Delete' || event.key === 'Backspace') {
        event.preventDefault();
        const activePts = workingZones[activeIndex]?.points;
        if (selectedVertex >= 0 && activePts && activePts.length > 3) {
          activePts.splice(selectedVertex, 1);
          selectedVertex = -1;
          draw();
        }
      }
    };

    const onAdd = (event) => {
      if (event.target !== svg || suppressAddClick) return;
      const point = pointAt(event);
      if (!point) return;
      const activePts = workingZones[activeIndex]?.points;
      if (activePts) {
        activePts.push(point);
        selectedVertex = activePts.length - 1;
        draw();
      }
    };

    const commit = async () => {
      for (const z of workingZones) {
        if (!z.points || z.points.length < 3) {
          return toast(`Area "${z.name}" membutuhkan minimal 3 titik`, true);
        }
      }
      if (state.project?.id !== editorProjectId || nodeFor(node.id) !== node) {
        cleanup();
        return toast('Project atau node sudah berubah; editor dibatalkan', true);
      }

      const finalZones = workingZones.map(z => ({
        id: z.id,
        name: z.name,
        capacity: z.capacity,
        points: z.points.map(p => `${p.x.toFixed(3)},${p.y.toFixed(3)}`).join('; ')
      }));

      node.config.zones = finalZones;
      markDirty();
      const saved = await save();
      if (!saved) {
        renderInspector();
        return;
      }
      await liveUpdateWorkflow();
      cleanup();
      renderInspector();
      toast(`${workingZones.length} Area / Zona berhasil disimpan`);
    };

    removePointBtn.onclick = () => {
      const activePts = workingZones[activeIndex]?.points;
      if (selectedVertex >= 0 && activePts && activePts.length > 3) {
        activePts.splice(selectedVertex, 1);
        selectedVertex = -1;
        draw();
      }
    };

    cancelBtn.onclick = () => {
      cleanup();
      toast('Gambar area dibatalkan');
    };

    saveBtn.onclick = commit;

    svg.addEventListener('click', onAdd);
    window.addEventListener('keydown', onKey);
    img.addEventListener('load', draw);
    img.style.cursor = 'crosshair';
    img._cancelMultiZoneDrawing = cleanup;
    resizeObserver = new ResizeObserver(draw);
    resizeObserver.observe(parent);

    updateSelector();
    draw();
    toast('Editor Multi-Zone aktif. Klik gambar untuk menambah titik, atau pilih area lain.');
  }

  function applyBranchingPreset(presetName, targetNode) {
    if (!targetNode) return;
    if (presetName === 'overcrowding') {
      targetNode.config.metric = 'object_count';
      targetNode.config.operator = 'gte';
      targetNode.config.value = 5;
      targetNode.config.passWhen = 'true';
      toast('Preset Kapasitas Ruangan (Overcrowding >= 5) berhasil diterapkan!');
    } else if (presetName === 'line_quota') {
      targetNode.config.metric = 'line_counter_in';
      targetNode.config.operator = 'gte';
      targetNode.config.value = 10;
      targetNode.config.passWhen = 'true';
      toast('Preset Kuota Masuk Line Counter (IN >= 10) berhasil diterapkan!');
    } else if (presetName === 'quality_sort') {
      targetNode.config.metric = 'max_confidence';
      targetNode.config.operator = 'gte';
      targetNode.config.value = 0.85;
      targetNode.config.passWhen = 'false';
      toast('Preset Sortir Cacat / Reject (Confidence < 0.85) berhasil diterapkan!');
    }
    markDirty();
    renderCanvas();
    renderInspector();
  }

  function showIfElseGuideModal(node) {
    let modal = $('#ifElseGuideModal');
    if (!modal) {
      modal = document.createElement('dialog');
      modal.id = 'ifElseGuideModal';
      modal.className = 'template-modal';
      modal.style.maxWidth = '780px';
      modal.style.width = '92vw';
      modal.style.borderRadius = '12px';
      modal.style.border = '1px solid var(--border, #334155)';
      modal.style.backgroundColor = 'var(--bg-card, #0f172a)';
      modal.style.color = 'var(--text, #f1f5f9)';
      modal.style.boxShadow = '0 25px 50px -12px rgba(0, 0, 0, 0.7)';
      document.body.append(modal);
    }
    modal.replaceChildren();

    const head = document.createElement('div');
    head.className = 'modal-head';
    head.style.display = 'flex';
    head.style.alignItems = 'center';
    head.style.justifyContent = 'space-between';
    head.style.padding = '16px 20px';
    head.style.borderBottom = '1px solid var(--border, #334155)';
    head.innerHTML = `
      <div style="display:flex; align-items:center; gap:10px;">
        <span style="font-size:22px;">🔀</span>
        <div>
          <h3 style="margin:0; font-size:16px; font-weight:700; color:var(--text, #f8fafc);">Panduan Percabangan Alur (If / Else Logic)</h3>
          <small style="color:var(--text-muted, #94a3b8);">Cara kerja percabangan, parameter logika, dan 3 contoh kasus nyata</small>
        </div>
      </div>
    `;
    const closeBtn = document.createElement('button');
    closeBtn.className = 'button ghost';
    closeBtn.textContent = '✕';
    closeBtn.style.fontSize = '16px';
    closeBtn.onclick = () => modal.close();
    head.append(closeBtn);
    modal.append(head);

    const body = document.createElement('div');
    body.className = 'modal-body';
    body.style.padding = '20px';
    body.style.maxHeight = '72vh';
    body.style.overflowY = 'auto';
    body.style.display = 'flex';
    body.style.flexDirection = 'column';
    body.style.gap = '16px';

    body.innerHTML = `
      <!-- Section 1: Konsep Dasar -->
      <div style="background:rgba(30, 41, 59, 0.6); border:1px solid #334155; border-radius:8px; padding:14px;">
        <h4 style="margin:0 0 8px 0; font-size:13px; color:#38bdf8; display:flex; align-items:center; gap:6px;">
          <span>💡</span> 1. Bagaimana Sistem Percabangan Bekerja?
        </h4>
        <p style="margin:0 0 10px 0; font-size:12px; line-height:1.5; color:#cbd5e1;">
          Node <b>Percabangan (If / Else)</b> bertindak sebagai <i>gerbang seleksi cerdas</i>. Aliran deteksi frame akan <b>DILOLOSKAN</b> ke node downstream (tujuan) jika syarat terpenuhi, atau <b>DITAHAN</b> jika tidak memenuhi syarat.
        </p>
        <div style="display:grid; grid-template-columns: 1fr 1fr; gap:10px;">
          <div style="background:rgba(34, 197, 94, 0.1); border:1px solid rgba(34, 197, 94, 0.3); border-radius:6px; padding:10px;">
            <div style="font-weight:700; font-size:12px; color:#22c55e; margin-bottom:4px;">🟢 Cabang IF (True)</div>
            <div style="font-size:11px; color:#94a3b8; line-height:1.4;">
              Meneruskan data <b>hanya saat kondisi BENAR</b>.<br>
              <i>Contoh:</i> Jika jumlah orang &ge; 5 &rarr; Teruskan ke <b>Output Alert</b>.
            </div>
          </div>
          <div style="background:rgba(239, 68, 68, 0.1); border:1px solid rgba(239, 68, 68, 0.3); border-radius:6px; padding:10px;">
            <div style="font-weight:700; font-size:12px; color:#ef4444; margin-bottom:4px;">🔴 Cabang ELSE (False)</div>
            <div style="font-size:11px; color:#94a3b8; line-height:1.4;">
              Meneruskan data <b>hanya saat kondisi SALAH</b>.<br>
              <i>Contoh:</i> Jika akurasi produk tidak mencapai 85% &rarr; Teruskan ke <b>Reject Output</b>.
            </div>
          </div>
        </div>
      </div>

      <!-- Section 2: Diagram Skema Alur Percabangan -->
      <div style="background:rgba(15, 23, 42, 0.8); border:1px solid #334155; border-radius:8px; padding:14px;">
        <h4 style="margin:0 0 10px 0; font-size:13px; color:#38bdf8; display:flex; align-items:center; gap:6px;">
          <span>📐</span> 2. Skema Menghubungkan Dua Cabang di Canvas
        </h4>
        <pre style="margin:0; font-family:monospace; font-size:11px; background:#020617; padding:12px; border-radius:6px; border:1px solid #1e293b; color:#e2e8f0; line-height:1.5; overflow-x:auto;">
[ Kamera / Input ] ──&gt; [ Object Detection / Tracking ]
                                  │
                  ┌───────────────┴───────────────┐
                  ▼                               ▼
       [ If/Else: Cabang IF ]          [ If/Else: Cabang ELSE ]
       (Kondisi: Jumlah &ge; 5)           (Kondisi: Jumlah &lt; 5)
                  │                               │
                  ▼                               ▼
        [ Output Peringatan ]             [ Live Preview ]
         (Buzzer / Simpan Foto)            (Tampilan Normal)
        </pre>
        <p style="margin:8px 0 0 0; font-size:11px; color:#94a3b8;">
          <b>Tips Cara Pasang:</b> Tarik garis output dari node deteksi ke 2 node If/Else berbeda (satu diset <i>Cabang IF</i>, satu diset <i>Cabang ELSE</i>).
        </p>
      </div>

      <!-- Section 3: Tiga Contoh Nyata Kasus Industri -->
      <div>
        <h4 style="margin:0 0 10px 0; font-size:13px; color:#f8fafc; display:flex; align-items:center; gap:6px;">
          <span>🏭</span> 3. Contoh Penerapan Nyata (Pilih &amp; Pasang Otomatis)
        </h4>
        <div style="display:flex; flex-direction:column; gap:10px;">
          
          <!-- Contoh 1: Overcrowding -->
          <div style="background:rgba(30, 41, 59, 0.5); border:1px solid #334155; border-radius:8px; padding:12px;">
            <div style="display:flex; justify-content:space-between; align-items:flex-start;">
              <div>
                <div style="font-weight:700; font-size:12px; color:#f8fafc;">Kasus A: Peringatan Batas Kapasitas Ruangan (Overcrowding)</div>
                <div style="font-size:11px; color:#94a3b8; margin-top:2px;">
                  Picu alarm hanya saat jumlah orang di ruangan mencapai atau melebihi 5 orang.
                </div>
              </div>
              <button id="applyTplA" class="button secondary" style="font-size:11px; padding:4px 10px;">
                ⚡ Terapkan ke Node Ini
              </button>
            </div>
            <div style="margin-top:8px; font-size:11px; background:rgba(0,0,0,0.25); padding:6px 10px; border-radius:4px; font-family:monospace; color:#38bdf8;">
              Metrik: Jumlah Objek | Operator: &ge; | Nilai: 5 | Arah: Cabang IF (True)
            </div>
          </div>

          <!-- Contoh 2: Line Counter Quota -->
          <div style="background:rgba(30, 41, 59, 0.5); border:1px solid #334155; border-radius:8px; padding:12px;">
            <div style="display:flex; justify-content:space-between; align-items:flex-start;">
              <div>
                <div style="font-weight:700; font-size:12px; color:#f8fafc;">Kasus B: Peringatan Target Kuota Masuk (Line Counter)</div>
                <div style="font-size:11px; color:#94a3b8; margin-top:2px;">
                  Otomatis kirim notifikasi/simpan foto saat pengunjung yang masuk (IN) mencapai target 10 orang.
                </div>
              </div>
              <button id="applyTplB" class="button secondary" style="font-size:11px; padding:4px 10px;">
                ⚡ Terapkan ke Node Ini
              </button>
            </div>
            <div style="margin-top:8px; font-size:11px; background:rgba(0,0,0,0.25); padding:6px 10px; border-radius:4px; font-family:monospace; color:#38bdf8;">
              Metrik: Hitungan Masuk (IN) | Operator: &ge; | Nilai: 10 | Arah: Cabang IF (True)
            </div>
          </div>

          <!-- Contoh 3: Sortir Kualitas / Anomali -->
          <div style="background:rgba(30, 41, 59, 0.5); border:1px solid #334155; border-radius:8px; padding:12px;">
            <div style="display:flex; justify-content:space-between; align-items:flex-start;">
              <div>
                <div style="font-weight:700; font-size:12px; color:#f8fafc;">Kasus C: Sortir Produk Cacat / Reject (Cabang ELSE)</div>
                <div style="font-size:11px; color:#94a3b8; margin-top:2px;">
                  Arahkan produk yang tidak memenuhi akurasi standar (&lt; 85%) ke jalur Reject/Alarm.
                </div>
              </div>
              <button id="applyTplC" class="button secondary" style="font-size:11px; padding:4px 10px;">
                ⚡ Terapkan ke Node Ini
              </button>
            </div>
            <div style="margin-top:8px; font-size:11px; background:rgba(0,0,0,0.25); padding:6px 10px; border-radius:4px; font-family:monospace; color:#38bdf8;">
              Metrik: Akurasi Tertinggi | Operator: &ge; | Nilai: 0.85 | Arah: Cabang ELSE (False)
            </div>
          </div>

        </div>
      </div>
    `;

    modal.append(body);
    modal.showModal();

    $('#applyTplA').onclick = () => {
      if (node) {
        applyBranchingPreset('overcrowding', node);
        modal.close();
      } else {
        toast('Pilih node If / Else di canvas untuk menerapkan preset ini');
      }
    };
    $('#applyTplB').onclick = () => {
      if (node) {
        applyBranchingPreset('line_quota', node);
        modal.close();
      } else {
        toast('Pilih node If / Else di canvas untuk menerapkan preset ini');
      }
    };
    $('#applyTplC').onclick = () => {
      if (node) {
        applyBranchingPreset('quality_sort', node);
        modal.close();
      } else {
        toast('Pilih node If / Else di canvas untuk menerapkan preset ini');
      }
    };
  }

  const NODE_GUIDES_ID = {
  "export_code": {
    "concept": "Export Code membuat ZIP Python yang menjalankan snapshot seluruh workflow aktif di folder terpisah. Node ini tidak diproses per frame dan tidak memakai kabel.",
    "diagram": "[ Workflow tersimpan ] → [ Periksa Paket ] → [ ZIP ] → [ run.py ]",
    "steps": [
      "Simpan workflow, tambahkan satu node Export Code, dan biarkan tanpa koneksi.",
      "Pilih model disertakan hanya bila Anda memiliki hak distribusinya.",
      "Klik Periksa Paket, lalu Build & Download ZIP. Di komputer tujuan isi .env dan jalankan python run.py --check sebelum python run.py."
    ],
    "params": [
      { "key": "packageName", "label": "Nama paket", "desc": "Nama ZIP dan manifest; kosong berarti nama proyek." },
      { "key": "version", "label": "Versi paket", "desc": "Versi snapshot yang tercatat di manifest." },
      { "key": "includeModels", "label": "Sertakan model", "desc": "Jika nonaktif, model harus disediakan melalui environment dengan checksum yang sama." }
    ],
    "tips": "Alamat sumber, path file lokal, dan kredensial mungkin harus diisi ulang pada mesin tujuan. File .env tidak ikut ZIP."
  },
  "python_script": {
    "concept": "Custom Python Script memungkinkan pemrosesan frame langsung menggunakan OpenCV (cv2) dan NumPy (np) tingkat lanjut tanpa memblokir pipeline. Sangat fleksibel untuk manipulasi piksel, filter warna khusus, morfologi, atau running calculations.",
    "diagram": "[ Source / Preprocessing ] ──▶ [ Custom Python Script: process(frame, state) ] ──▶ [ Next Node ]",
    "steps": [
      "Tulis fungsi process(frame, state) yang menerima frame NumPy BGR uint8 dan dictionary persistensi state.",
      "Gunakan library cv2 atau np untuk pemrosesan piksel, misalnya thresholding, deteksi tepi, atau koreksi warna kustom.",
      "Kembalikan frame hasil modifikasi (return frame) dengan dimensi resolusi yang sama agar bounding box downstream tetap presisi.",
      "Klik tombol Check Script untuk memvalidasi sintaks dan runtime script secara instan."
    ],
    "params": [
      { "key": "code", "label": "Kode Script Python", "desc": "Wajib mendefinisikan def process(frame, state): ... dan mengembalikan frame." },
      { "key": "timeoutMs", "label": "Batas Waktu Eksekusi (ms)", "desc": "Batas maksimal waktu eksekusi script per frame (default 500ms) untuk mencegah freeze." },
      { "key": "onError", "label": "Perilaku Saat Error", "desc": "Pilih stop (hentikan workflow) atau pass (teruskan frame asli jika script gagal)." }
    ],
    "tips": "Gunakan state['my_var'] untuk menyimpan nilai antar frame seperti counter atau running average tanpa variabel global."
  },
  "zone_activity_timer": {
    "concept": "Zone Activity Timer mengukur aktivitas di dalam polygon berdasarkan jumlah kelas wajib dan kelas pemicu. Node ini bekerja berdasarkan observasi area dan tidak memerlukan ID track per objek.",
    "diagram": "[ Detector ] ──▶ [ Zone Activity Timer ] ──▶ [ Alert / Preview ]",
    "steps": [
      "Gambar polygon zona pada preview atau edit Points dalam format x,y; x,y dengan koordinat 0 sampai 1.",
      "Isi kelas wajib (contoh tire) dan kelas pemicu (contoh person), lalu atur jumlah minimum masing-masing.",
      "Atur durasi konfirmasi serta toleransi grace untuk menstabilkan observasi yang sesaat hilang."
    ],
    "params": [
      { "key": "points", "label": "Polygon Zona", "desc": "Koordinat polygon ternormalisasi; gunakan tombol Draw Zone on Preview." },
      { "key": "confirmationSeconds", "label": "Durasi Konfirmasi", "desc": "Waktu kondisi harus terpenuhi sebelum event aktivitas diteruskan." },
      { "key": "maxObservationGapSeconds", "label": "Maksimal Jeda Observasi", "desc": "Jeda maksimum antar observasi sebelum status dianggap tidak valid." }
      ,{ "key": "maxSessionDurationSeconds", "label": "Batas Durasi Sesi", "desc": "Jika lebih dari 0, sesi ditandai terlalu panjang setelah batas tercapai tanpa dipaksa selesai." }
    ],
    "tips": "Gunakan personGraceSeconds dan requiredGraceSeconds untuk menghindari event berkedip saat deteksi tertutup sesaat."
  },
  "zone_exit_event": {
    "concept": "Zone Exit Event mencatat objek terlacak yang pernah terlihat di dalam polygon lalu teramati berada di luar secara kontinu selama grace period.",
    "diagram": "[ Detector ] ──▶ [ Tracker ] ──▶ [ Zone Exit Event ] ──▶ [ Alert / Webhook ]",
    "steps": [
      "Hubungkan node dari detector dan tracker agar objek memiliki ID pelacakan.",
      "Gambar polygon zona pada preview dan isi classes dengan kelas yang perlu dipantau.",
      "Atur absenceGraceSeconds untuk menunggu observasi luar yang stabil; objek yang sekadar tidak terlihat tidak memicu exit."
    ],
    "params": [
      { "key": "points", "label": "Polygon Zona", "desc": "Koordinat polygon ternormalisasi; gunakan tombol Draw Zone on Preview." },
      { "key": "classes", "label": "Kelas yang Dilacak", "desc": "Kelas objek yang dapat menghasilkan event keluar." },
      { "key": "absenceGraceSeconds", "label": "Toleransi Keluar", "desc": "Durasi observasi di luar zona sebelum event exit diterbitkan." }
    ],
    "tips": "Kehilangan track atau objek yang tidak teramati tidak dianggap keluar sampai ada observasi di luar zona."
  },
  "object_timer": {
    "concept": "Object Timer menghitung durasi waktu kehadiran setiap orang atau objek yang terdeteksi secara real-time, menempelkan badge timer visual di atas objek pada layar, serta memicu event/alarm saat durasi melebihi batas yang ditentukan.",
    "diagram": "[ Detector / YOLO ] ──▶ [ Tracker ] ──▶ [ Object Timer ] ──▶ [ Live Preview / Alert ]",
    "steps": [
      "Hubungkan output dari model AI (Detector/YOLO) atau Tracker ke input Object Timer.",
      "Tentukan targetClasses (contoh: person untuk pekerja/tamu, forklift, atau * untuk semua objek).",
      "Atur alertThresholdSeconds untuk memicu peringatan jika orang/objek bertahan melebihi durasi tertentu (contoh: 10 detik).",
      "Pilih timerFormat ('mm:ss' atau 'seconds') dan posisi badge (top / bottom)."
    ],
    "params": [
      { "key": "targetClasses", "label": "Target Kelas Objek", "desc": "Kelas objek yang dihitung timernya (contoh: person, car, atau * untuk semua objek)." },
      { "key": "alertThresholdSeconds", "label": "Batas Alarm Durasi", "desc": "Durasi maksimal dalam detik sebelum status berubah menjadi peringatan OVERTIME (0 = nonaktif)." },
      { "key": "graceSeconds", "label": "Toleransi Hilang Sesaat", "desc": "Jeda toleransi detik jika objek tertutup sesaat sebelum timer di-reset." },
      { "key": "timerFormat", "label": "Format Tampilan", "desc": "Format teks timer: mm:ss (00:15), seconds (15.2s), atau hh:mm:ss." },
      { "key": "showOverlay", "label": "Tampilkan Badge Timer", "desc": "Tampilkan indikator stopwatch dan durasi secara langsung di frame video." }
    ],
    "tips": "Object Timer bekerja baik dengan Tracker (ByteTrack / BoT-SORT) maupun secara mandiri dengan deteksi langsung berkat algoritma pencocokan spasial IoU bawaan."
  },
  "multi_zone_occupancy": {
    "concept": "Multi-Zone Occupancy & Activity Tracker memantau banyak area/meja/slot/workstation sekaligus dalam satu frame kamera dengan kapasitas, durasi, status Vacant/Occupied, dan event ringkasan sesi.",
    "diagram": "[ Detector / YOLO ] ──▶ [ Tracker ] ──▶ [ Multi-Zone Occupancy ] ──▶ [ Live Preview / DB / Webhook ]",
    "steps": [
      "Buka 'Gambar Poligon Zona di Preview' untuk menambah banyak zona/meja dan mengatur titik poligon masing-masing.",
      "Tentukan targetClasses (contoh: person untuk meja/restoran, car untuk parkir, atau box/forklift untuk gudang).",
      "Atur kapasitas kursi/objek per zona, durasi konfirmasi terisi, serta toleransi kepergian sesaat (grace period)."
    ],
    "params": [
      { "key": "targetClasses", "label": "Target Kelas Objek", "desc": "Kelas objek yang dipantau (contoh: person, car, forklift)." },
      { "key": "confirmationSeconds", "label": "Konfirmasi Terisi (detik)", "desc": "Durasi objek harus bertahan di zona sebelum status berubah menjadi OCCUPIED." },
      { "key": "graceSeconds", "label": "Toleransi Kosong (detik)", "desc": "Jeda waktu saat objek tidak teramati sesaat sebelum sesi dianggap selesai." },
      { "key": "maxDwellMinutes", "label": "Batas Waktu Maksimal (menit)", "desc": "Batas waktu maksimal berada di zona sebelum alert OVERSTAY dipicu (0 = nonaktif)." }
    ],
    "tips": "Gunakan multi-polygon editor di preview frame untuk mengelola posisi dan kapasitas seluruh zona/meja secara visual."
  },
  "vlm_box_tracker": {
    "concept": "VLM Box Tracker mendeteksi dan melacak objek menggunakan Vision Language Model (OpenRouter / TypeSafe Jev) yang dipadukan dengan Lucas-Kanade Optical Flow dan Kalman Filter rewind-replay untuk pergerakan mulus 30+ FPS tanpa memblokir video.",
    "diagram": "[ Input ] ──▶ [ VLM Box Tracker ] ──▶ [ Overlay Annotate / Zone Timer / Alert ]",
    "steps": [
      "Hubungkan Input langsung ke VLM Box Tracker tanpa perlu melatih model YOLO lokal.",
      "Pilih provider (OpenRouter atau TypeSafe Jev) dan isi Object Prompt dengan kelas yang ingin dilacak (misal: tire, worker).",
      "Atur Query Interval (default 1.0s) agar hemat kuota/biaya API, sementara Optical Flow melacak objek di antara setiap query."
    ],
    "params": [
      { "key": "provider", "label": "Provider API", "desc": "Pilih OpenRouter (model vision fleksibel) atau TypeSafe Jev." },
      { "key": "objectPrompt", "label": "Target Objects", "desc": "Nama kelas objek dipisah koma (contoh: tire, worker, forklift)." },
      { "key": "queryIntervalSeconds", "label": "Jeda Query API", "desc": "Frekuensi pengiriman frame ke VLM untuk efisiensi biaya." },
      { "key": "minConfidence", "label": "Ambang Batas Akurasi", "desc": "Akurasi minimal deteksi sebelum dimasukkan ke dalam tracker." }
    ],
    "tips": "Biarkan API Key kosong di UI jika sudah mengatur OPENROUTER_API_KEY atau TYPESAFE_API_KEY di file .env server."
  },
  "ai_agent": {
    "concept": "AI Agent membawa penalaran kecerdasan buatan LLM/VLM (mirip n8n AI Agent) ke dalam video pipeline. Mampu menganalisis visual frame kamera langsung sekaligus data deteksi objek dan event insiden untuk evaluasi kepatuhan keselamatan atau verifikasi alarm.",
    "diagram": "[ Deteksi / Zone Timer ] ──▶ [ AI Agent Node ] ──▶ [ Alert / Webhook / DB ]",
    "steps": [
      "Pilih provider LLM: OpenAI (gpt-4o, gpt-4o-mini), OpenRouter, atau Custom/Local (Ollama, vLLM).",
      "Pilih triggerMode: 'On Upstream Event' (hemat biaya token, hanya saat ada event) atau 'Periodic' (audit berkala).",
      "Pilih taskMode: 'decision' (filter ya/tidak dengan alasan cerdas), 'analysis' (ringkasan insiden), atau 'structured_json'.",
      "Gunakan variabel {{detections}}, {{event}}, {{timestamp}} di dalam User Prompt."
    ],
    "params": [
      { "key": "provider", "label": "Provider LLM", "desc": "Pilihan: openai, openrouter, atau custom endpoint (Ollama/vLLM)." },
      { "key": "model", "label": "Model LLM/VLM", "desc": "Nama model, contoh: gpt-4o-mini, gpt-4o, google/gemini-2.0-flash-001." },
      { "key": "triggerMode", "label": "Mode Pemicu", "desc": "Kapan AI Agent dieksekusi: on_event, periodic, atau always." },
      { "key": "taskMode", "label": "Tugas Agen", "desc": "Format dan tujuan output agen: decision, analysis, structured_json, atau raw_text." },
      { "key": "includeImage", "label": "Sertakan Gambar Frame", "desc": "Kirim snapshot frame kamera ke model multimodal (VLM)." },
      { "key": "passDownstreamOn", "label": "Aturan Teruskan", "desc": "Hanya teruskan ke Alert/Webhook jika keputusan bernilai True (decision_true)." }
    ],
    "tips": "Biarkan kolom API Key kosong jika sudah menyetel OPENAI_API_KEY atau OPENROUTER_API_KEY di file .env."
  },
  "frame_sampler": {
    "concept": "Frame Sampler membatasi FPS frame yang diteruskan ke pemrosesan pada cabang ini. Sumber capture tetap berjalan pada FPS kamera.",
    "diagram": "[ Input ] ──▶ [ Preview asli ]\n[ Input ] ──▶ [ Frame Sampler ] ──▶ [ YOLO ] ──▶ [ Preview AI ]",
    "steps": [
      "Hubungkan Input ke Frame Sampler lalu sambungkan outputnya ke YOLO atau node pemrosesan lain.",
      "Isi Target FPS dengan angka 0 atau lebih; gunakan 0 untuk tanpa batas.",
      "Cabang Preview yang terhubung langsung dari Input tetap menerima frame tanpa sampler."
    ],
    "params": [
      {
        "key": "targetFps",
        "label": "Target FPS Pemrosesan",
        "desc": "Batas FPS downstream; 0 berarti unlimited dan tidak mengubah FPS capture sumber."
      }
    ],
    "tips": "Gunakan 10 FPS untuk mengurangi beban model berat. Status runtime menampilkan FPS input/output serta frame yang diteruskan dan dibuang."
  },
  "input": {
    "concept": "Node sumber input utama yang mengalirkan frame video dari webcam USB, kamera industri Daheng Imaging (Galaxy GXI), file gambar statis, atau file rekaman video lokal.",
    "diagram": "[ Input (Kamera / Video / Daheng) ] ──▶ [ Preprocessing / Detector ]",
    "steps": [
      "Pilih tipe sumber (sourceType): camera (webcam), daheng (kamera industri), atau file (video/gambar).",
      "Jika menggunakan webcam, pilih indeks kamera (0 untuk webcam internal, 1 untuk webcam USB eksternal).",
      "Jika menggunakan file video, masukkan path lengkap file pada kolom File Path dan centang Loop agar video berputar otomatis terus-menerus.",
      "Untuk kamera industri Daheng, atur identifier, exposure time (waktu eksposur), dan gain sensor sesuai pencahayaan pabrik."
    ],
    "params": [
      {
        "key": "sourceType",
        "label": "Tipe Sumber",
        "desc": "Pilihan input: camera (webcam), daheng (kamera industri), file (video/foto)."
      },
      {
        "key": "source",
        "label": "Indeks Kamera USB",
        "desc": "Nomor urut webcam perangkat komputer (0, 1, 2, ...)."
      },
      {
        "key": "filePath",
        "label": "Path File Video/Gambar",
        "desc": "Lokasi file rekaman video di hard drive untuk simulasi atau analisis."
      },
      {
        "key": "loop",
        "label": "Putar Berulang (Loop)",
        "desc": "Memutar ulang video secara terus-menerus dari awal setelah frame habis."
      },
      {
        "key": "dahengExposureUs",
        "label": "Waktu Eksposur Daheng (µs)",
        "desc": "Durasi rana sensor kamera industri dalam mikrodetik."
      },
      {
        "key": "dahengGain",
        "label": "Gain Sensor Daheng",
        "desc": "Penguat sinyal sensor kamera industri dalam satuan desibel (dB)."
      }
    ],
    "tips": "Untuk pengujian model AI tanpa kamera fisik, Anda bisa menggunakan file rekaman video (.mp4) dengan opsi Loop aktif."
  },
  "ip_camera": {
    "concept": "Node streaming jaringan IP untuk menghubungkan kamera CCTV keamanan, NVR/DVR, atau RTSP/HTTP stream dengan fitur pemulihan koneksi otomatis (auto-reconnect) dan pemantauan kesehatan kamera.",
    "diagram": "[ IP Camera / CCTV ] ──▶ [ Preprocessing / Object Detection ]",
    "steps": [
      "Masukkan URL RTSP lengkap pada kolom Stream URL (contoh: rtsp://admin:pass@192.168.1.100:554/stream1).",
      "Pilih protokol Transport: TCP (sangat direkomendasikan agar video stabil dan tidak pecah) atau UDP.",
      "Aktifkan Auto Reconnect agar sistem otomatis menyambung kembali saat koneksi jaringan CCTV terputus.",
      "Aktifkan Deteksi Freeze & Tamper untuk memicu peringatan jika kamera macet atau lensa ditutup secara sengaja."
    ],
    "params": [
      {
        "key": "streamUrl",
        "label": "URL Stream RTSP/HTTP",
        "desc": "Alamat URL stream kamera CCTV atau NVR (RTSP, RTMP, HTTP)."
      },
      {
        "key": "transport",
        "label": "Protokol Transport",
        "desc": "Pilih TCP untuk transmisi stabil bebas glitch atau UDP untuk latensi terendah."
      },
      {
        "key": "autoReconnect",
        "label": "Rekoneksi Otomatis",
        "desc": "Mencoba menyambung kembali secara otomatis saat sinyal jaringan terputus."
      },
      {
        "key": "detectFreeze",
        "label": "Deteksi Kamera Macet (Freeze)",
        "desc": "Mendeteksi jika frame video berhenti bergerak selama beberapa detik berturut-turut."
      },
      {
        "key": "detectTamper",
        "label": "Deteksi Sabotase Lensa (Tamper)",
        "desc": "Mendeteksi jika lensa kamera ditutup kain atau disorot cahaya sangat terang."
      }
    ],
    "tips": "Gunakan sub-stream (resolusi 720p atau VGA) dari NVR/CCTV untuk menghemat bandwidth jaringan dan mengoptimalkan FPS pengolahan AI."
  },
  "detector": {
    "concept": "Model AI Vision untuk mendeteksi lokasi dan klasifikasi kotak pembatas (bounding box) objek secara realtime dalam frame video.",
    "diagram": "[ Input Kamera ] ──▶ [ Object Detection ] ──▶ [ Object Tracking ]",
    "steps": [
      "Pilih arsitektur model pada Engine: RF-DETR (rekomendasi kecepatan & akurasi tinggi), Ultralytics YOLOv8, atau ONNX kustom.",
      "Atur Threshold akurasi keyakinan minimal: biasanya antara 0.40 hingga 0.60.",
      "Jika menggunakan model latih sendiri (.pt / .onnx), masukkan path file model pada kolom Custom Model Path.",
      "Hubungkan output node ini ke node Object Tracking untuk pelacakan objek yang stabil."
    ],
    "params": [
      {
        "key": "engine",
        "label": "Mesin Model AI",
        "desc": "Pilihan engine AI: rfdetr, ultralytics_yolo, yolo_world (zero-shot prompt), roboflow_universe, onnx_custom, tflite."
      },
      {
        "key": "threshold",
        "label": "Ambang Batas Akurasi (Confidence)",
        "desc": "Skor akurasi minimal (0.0 - 1.0) agar objek dianggap valid."
      },
      {
        "key": "iouThreshold",
        "label": "Ambang Batas NMS / IOU",
        "desc": "Ambang tumpang-tindih untuk menghapus deteksi ganda pada objek yang sama."
      },
      {
        "key": "rfdetrModel",
        "label": "Varian Model RF-DETR",
        "desc": "Pilihan ukuran model: rfdetr-nano, small, medium, large."
      },
      {
        "key": "customModelPath",
        "label": "Path Model Kustom",
        "desc": "Lokasi file bobot model (.pt atau .onnx) jika menggunakan model sendiri."
      }
    ],
    "tips": "Untuk mendeteksi objek berukuran sangat kecil pada resolusi tinggi, pasang node Small Object Slicer (SAHI) sebelum node ini."
  },
  "slicer": {
    "concept": "Node SAHI (Slicing Aided Hyper Inference) yang memotong gambar resolusi tinggi (1080p / 4K) menjadi petak-petak kecil bertingkat (tiles) sehingga objek kecil dapat terdeteksi tajam oleh model AI.",
    "diagram": "[ Input Kamera ] ──▶ [ Small Object Slicer ] ──▶ [ Object Detection ]",
    "steps": [
      "Pasang tepat sebelum node Object Detection jika objek target berukuran kecil (seperti sekrup, cacat mikro, atau orang dari CCTV jauh).",
      "Tentukan ukuran petak potong: Slice Width dan Slice Height (misal: 640x640 piksel).",
      "Tentukan Overlap Ratio (misal: 0.20 atau 20%) agar objek yang berada di perbatasan petak tetap terdeteksi utuh.",
      "Hasil potongan petak akan digabungkan kembali secara otomatis menggunakan algoritma NMS/IOU."
    ],
    "params": [
      {
        "key": "sliceWidth",
        "label": "Lebar Petak Potongan",
        "desc": "Lebar setiap potongan petak gambar dalam piksel (misal 640)."
      },
      {
        "key": "sliceHeight",
        "label": "Tinggi Petak Potongan",
        "desc": "Tinggi setiap potongan petak gambar dalam piksel (misal 640)."
      },
      {
        "key": "overlapRatio",
        "label": "Rasio Tumpang Tindih (Overlap)",
        "desc": "Persentase overlap antar petak bersebelahan (0.10 hingga 0.30)."
      },
      {
        "key": "iouThreshold",
        "label": "Ambang Batas NMS Penggabungan",
        "desc": "Ambang batas IOU saat menyatukan kembali deteksi dari semua petak."
      }
    ],
    "tips": "Gunakan SAHI saat kamera mengarah dari jarak jauh dengan sudut pandang lebar (wide angle)."
  },
  "segmenter": {
    "concept": "Model AI Instance Segmentation untuk menghasilkan kontur piksel dan masking presisi dari bentuk objek (bukan sekadar kotak persegi). Mendukung YOLOv8 Segmentation, RF-DETR Seg, dan Segment Anything (SAM 3).",
    "diagram": "[ Input Kamera ] ──▶ [ Object Segmentation ] ──▶ [ Live Preview / Measurement ]",
    "steps": [
      "Pilih engine segmentasi: Ultralytics YOLOv8 Seg, RF-DETR Seg, atau SAM 3 (Segment Anything).",
      "Atur Threshold akurasi minimal (default: 0.45).",
      "Jika menggunakan model sendiri, masukkan path file bobot (.pt) pada Custom Model Path.",
      "Hubungkan ke Live Preview untuk melihat lapisan warna kontur transparan di atas objek."
    ],
    "params": [
      {
        "key": "engine",
        "label": "Mesin Segmentasi AI",
        "desc": "Pilihan engine: ultralytics_yolo, rfdetr_seg, sam3."
      },
      {
        "key": "threshold",
        "label": "Ambang Batas Akurasi",
        "desc": "Skor akurasi minimal untuk menampilkan masking segmentasi."
      },
      {
        "key": "concepts",
        "label": "Konsep Teks (Prompt SAM 3)",
        "desc": "Kata kunci teks untuk segmentasi zero-shot SAM 3 (misal: 'person, car')."
      },
      {
        "key": "customModelPath",
        "label": "Path Model Kustom",
        "desc": "Lokasi file model segmentasi lokal (misal: data/models/yolov8n-seg.pt)."
      }
    ],
    "tips": "Segmentasi sangat ideal untuk inspeksi kualitas industri, mengukur luas permukaan cacat, atau memisahkan objek dari latar belakang."
  },
  "efficientad": {
    "concept": "Model AI Visual Inspection canggih berbasis EfficientAD untuk mendeteksi anomali cacat visual permukaan (sobekan, goresan, noda, keretakan) tanpa memerlukan contoh foto cacat saat pelatihan.",
    "diagram": "[ Input / Crop ] ──▶ [ Visual Inspection (EfficientAD) ] ──▶ [ Live Preview / Alert ]",
    "steps": [
      "Masukkan path model EfficientAD pada kolom EfficientAD Model.",
      "Atur Anomaly Threshold (ambang batas anomali cacat) sesuai toleransi inspeksi.",
      "Centang Show Heatmap dan atur Heatmap Opacity untuk melihat visualisasi sebaran lokasi cacat berwarna gradien merah.",
      "Hubungkan ke node If / Else atau Alert untuk memisahkan produk reject secara otomatis."
    ],
    "params": [
      {
        "key": "efficientadModel",
        "label": "Path Model EfficientAD",
        "desc": "Lokasi file model bobot EfficientAD (.pth / .onnx)."
      },
      {
        "key": "anomalyThreshold",
        "label": "Ambang Batas Anomali (Cacat)",
        "desc": "Skor ambang batas anomali; di atas nilai ini produk dianggap cacat/NG."
      },
      {
        "key": "showHeatmap",
        "label": "Tampilkan Peta Anomali (Heatmap)",
        "desc": "Menampilkan visualisasi gradien warna pada titik-titik cacat permukaan."
      },
      {
        "key": "heatmapOpacity",
        "label": "Transparansi Heatmap",
        "desc": "Tingkat transparansi lapisan warna cacat di atas video asli (0.1 - 1.0)."
      },
      {
        "key": "useModelThreshold",
        "label": "Gunakan Ambang Batas Bawaan",
        "desc": "Menggunakan nilai ambang batas otomatis dari file model yang dimuat."
      }
    ],
    "tips": "Cukup latih model dengan foto-foto produk bagus (OK). Setiap perbedaan sekecil apa pun akan otomatis terdeteksi sebagai anomali (NG)."
  },
  "classifier": {
    "concept": "Model AI Klasifikasi Citra untuk menentukan kategori atau status dari keseluruhan frame gambar atau potongan objek terdeteksi menggunakan arsitektur ConvNeXt ImageNet atau model kustom.",
    "diagram": "[ Input / Detection Crop ] ──▶ [ Image Classification ] ──▶ [ Logic / Alert ]",
    "steps": [
      "Hubungkan langsung dari Input untuk klasifikasi seluruh frame, atau dari Detection Crop untuk klasifikasi objek per objek.",
      "Pilih varian model ConvNeXt (Tiny, Small, Base) atau model kustom Anda.",
      "Atur Top-K untuk menentukan berapa banyak prediksi teratas yang ingin dicatat.",
      "Hubungkan output ke Draw Text atau Webhook untuk mengirimkan hasil klasifikasi."
    ],
    "params": [
      {
        "key": "engine",
        "label": "Mesin Klasifikasi",
        "desc": "Pilihan engine: convnext (ImageNet) atau model kustom."
      },
      {
        "key": "convnextModel",
        "label": "Varian Model ConvNeXt",
        "desc": "Pilihan ukuran: tiny, small, base, large."
      },
      {
        "key": "threshold",
        "label": "Ambang Batas Akurasi",
        "desc": "Skor akurasi minimal agar kelas dianggap valid."
      },
      {
        "key": "topK",
        "label": "Jumlah Prediksi Teratas (Top-K)",
        "desc": "Berapa banyak kelas kemungkinan tertinggi yang disimpan."
      },
      {
        "key": "customModelPath",
        "label": "Path Model Kustom",
        "desc": "Lokasi file bobot model klasifikasi kustom."
      }
    ],
    "tips": "Kombinasikan Detection Crop dengan Classifier untuk verifikasi bertingkat (misal: deteksi botol ➔ klasifikasi jenis isi botol teh/kopi/air)."
  },
  "detection_crop": {
    "concept": "Node pemotong yang otomatis memotong setiap bounding box objek hasil deteksi menjadi gambar terpisah, sangat ideal untuk diteruskan ke model klasifikasi kedua, OCR, atau barcode scanner.",
    "diagram": "[ Object Detection ] ──▶ [ Detection Crop ] ──▶ [ Classifier / Barcode ]",
    "steps": [
      "Hubungkan output dari node Object Detection ke input Detection Crop.",
      "Isi kolom Classes jika hanya ingin memotong kelas tertentu (misal: 'bottle' atau 'license_plate').",
      "Atur Context Padding Percent (misal 0.15 atau 15%) agar potongan tidak terpotong pas di tepi objek.",
      "Hubungkan output potongan ini ke node Classifier atau Barcode Reader."
    ],
    "params": [
      {
        "key": "classes",
        "label": "Filter Kelas Target",
        "desc": "Hanya potong objek dengan kelas yang tercantum (kosongkan untuk semua objek)."
      },
      {
        "key": "contextPaddingPercent",
        "label": "Margin Konteks Ekstra",
        "desc": "Persentase area luar kotak yang ikut disertakan (0.0 - 0.5)."
      },
      {
        "key": "square",
        "label": "Jadikan Persegi (Square)",
        "desc": "Membuat hasil potongan menjadi bentuk bujur sangkar dengan bantalan (padding)."
      },
      {
        "key": "minCropWidth",
        "label": "Lebar Minimal Potongan",
        "desc": "Abaikan potongan dengan ukuran lebar lebih kecil dari nilai ini."
      },
      {
        "key": "maxCrops",
        "label": "Batas Maksimal Potongan Per Frame",
        "desc": "Membatasi beban komputasi jika ada puluhan objek sekaligus dalam satu frame."
      }
    ],
    "tips": "Gunakan opsi Context Padding 15% untuk memberikan konteks visual yang lebih baik pada model klasifikasi downstream."
  },
  "barcode_reader": {
    "concept": "Pemindai kode batang (Barcode 1D: EAN, UPC, Code128) dan kode matriks 2D (QR Code) berkecepatan tinggi terintegrasi OpenCV.",
    "diagram": "[ Input / Detection Crop ] ──▶ [ Barcode & QR Reader ] ──▶ [ Database / Webhook ]",
    "steps": [
      "Hubungkan dari Input Kamera untuk membaca barcode di seluruh layar, atau dari Detection Crop untuk membaca barcode pada label produk terdeteksi.",
      "Centang Show Overlay untuk menampilkan kotak hijau penanda barcode di layar preview.",
      "Atur Cooldown Seconds (misal: 2.0 detik) agar barcode yang sama tidak terbaca berulang kali setiap frame.",
      "Teks hasil pemindaian otomatis tersimpan dalam variabel pipeline dan dapat dikirim via Webhook atau disimpan ke Database."
    ],
    "params": [
      {
        "key": "cropFromDetections",
        "label": "Pindai Dari Objek Terdeteksi",
        "desc": "Memindai barcode dari hasil kotak deteksi upstream."
      },
      {
        "key": "showOverlay",
        "label": "Tampilkan Kotak Penanda Barcode",
        "desc": "Menampilkan garis batas dan teks kode langsung di atas video."
      },
      {
        "key": "cooldownSeconds",
        "label": "Jeda Waktu Pembacaan Ulang (Cooldown)",
        "desc": "Mencegah pembacaan berulang kode yang sama dalam durasi detik tertentu."
      }
    ],
    "tips": "Untuk label barcode berukuran kecil pada kemasan produk, hubungkan melalui Detection Crop agar barcode terisolasi tajam."
  },
  "tracker": {
    "concept": "Node pelacak objek multi-objek (MOT) yang memberikan nomor ID unik permanen pada setiap objek yang bergerak antar-frame video agar tidak hilang atau dihitung berulang kali.",
    "diagram": "[ Object Detection ] ──▶ [ Object Tracking ] ──▶ [ Counting / Analysis ]",
    "steps": [
      "Wajib dihubungkan langsung dari output node Object Detection.",
      "Pilih ByteTrack untuk kamera statis, BoT-SORT untuk kamera bergerak, OC-SORT untuk arah gerak, atau C-BIoU untuk pergeseran besar antar-frame.",
      "Track Buffer default 90, ambang deteksi kuat 0.45, ambang track baru 0.5, dan konfirmasi 1 frame. Frame sampler tidak menghabiskan buffer.",
      "Hubungkan output Tracker ke Line Counter, Object Counter, atau Dwell Time."
    ],
    "params": [
      {
        "key": "algorithm",
        "label": "Algoritma Pelacakan",
        "desc": "Pilihan: bytetrack, botsort, ocsort, cbiou (pencocokan dengan area kotak diperluas)."
      },
      {
        "key": "trackHighThreshold",
        "label": "Ambang Deteksi Kuat",
        "desc": "Ambang deteksi kuat untuk pencocokan utama; pembuatan track baru memakai New Track Threshold."
      },
      {
        "key": "trackBuffer",
        "label": "Buffer Memori Frame",
        "desc": "Berapa frame ID dipertahankan saat objek hilang sementara sebelum dihapus."
      },
      {
        "key": "matchThreshold",
        "label": "Ambang Batas Pencocokan IOU",
        "desc": "Toleransi pergeseran kotak antar-frame saat menghubungkan track ID."
      }
    ],
    "tips": "Node ini adalah tulang punggung dari semua fitur analitik lanjutan (Line Counter, Object Counter, dan Dwell Time)."
  },
  "track_snapshot": {
    "concept": "Menangkap foto frame terbaik (Best Frame Snapshot) dari setiap objek unik yang terlacak tepat satu kali, mencegah spam inspeksi ganda pada objek yang sama.",
    "diagram": "[ Object Tracking ] ──▶ [ Once Per Track ] ──▶ [ Save Images / Webhook ]",
    "steps": [
      "Pasang langsung setelah node Object Tracking.",
      "Pilih Capture Mode: best_frame (frame dengan akurasi tertinggi) atau first_seen (saat objek pertama kali muncul).",
      "Tentukan Minimum Track Age Frames (misal: 3 frame) agar objek terkonfirmasi stabil sebelum difoto.",
      "Hubungkan output ke Save Images atau Webhook untuk mengirimkan foto bukti inspeksi."
    ],
    "params": [
      {
        "key": "captureMode",
        "label": "Mode Pengambilan Foto",
        "desc": "best_frame (foto terjelas saat confidence tertinggi) atau first_seen."
      },
      {
        "key": "minimumConfidence",
        "label": "Akurasi Minimal Snapshot",
        "desc": "Foto hanya diambil jika akurasi objek memenuhi ambang batas minimal ini."
      },
      {
        "key": "minimumTrackAgeFrames",
        "label": "Usia Minimal Track (Frame)",
        "desc": "Berapa frame objek harus terlacak sebelum snapshot diambil."
      },
      {
        "key": "retentionSeconds",
        "label": "Durasi Retensi ID",
        "desc": "Waktu memori mengingat ID objek agar tidak difoto ulang jika muncul kembali."
      }
    ],
    "tips": "Sangat cocok untuk gerbang parkir/tol otomatis atau conveyor pabrik agar setiap kendaraan/produk hanya difoto satu kali."
  },
  "object_counter": {
    "concept": "Node untuk memantau jumlah objek aktif di layar (Okupansi Langsung) atau menghitung total akumulasi objek unik yang pernah terdeteksi (Kumulatif).",
    "diagram": "[ Object Detection ] ──▶ [ Object Tracking ] ──▶ [ Object Counter ] ──▶ [ Alert / Database ]",
    "steps": [
      "Hubungkan setelah node Object Tracking agar setiap objek memiliki nomor ID unik.",
      "Pilih mode: Occupancy (jumlah objek saat ini di dalam kamera) atau Cumulative (total akumulasi objek unik yang pernah lewat).",
      "Jika ingin membatasi daya tampung ruangan, isi nilai Batas Kapasitas (Max Capacity).",
      "Centang Alarm Saat Melebihi Kapasitas untuk memicu peringatan otomatis jika ruangan penuh."
    ],
    "params": [
      {
        "key": "mode",
        "label": "Mode Perhitungan",
        "desc": "occupancy (okupansi langsung) atau cumulative (total akumulasi objek unik)."
      },
      {
        "key": "maxCapacity",
        "label": "Batas Kapasitas Maksimal",
        "desc": "Jumlah batas maksimal objek yang diizinkan (misal: 10 orang)."
      },
      {
        "key": "countOncePerTrack",
        "label": "Hitung Sekali Per ID",
        "desc": "Mencegah satu objek/orang yang sama dihitung berulang kali."
      },
      {
        "key": "classes",
        "label": "Filter Kelas",
        "desc": "Hanya hitung kelas tertentu (misal: person, vehicle)."
      },
      {
        "key": "alertOnCapacityExceeded",
        "label": "Alarm Saat Overcapacity",
        "desc": "Memicu sinyal alarm saat jumlah objek melampaui batas maksimal."
      }
    ],
    "tips": "Untuk membunyikan alarm saat ruangan penuh, sambungkan output node ini ke node If / Else dengan metrik object_count."
  },
  "line_counter": {
    "concept": "Node untuk menghitung objek yang memotong garis virtual dengan deteksi arah masuk (IN) dan keluar (OUT). Objek yang melintasi garis akan diidentifikasi secara otomatis berdasarkan arah pergerakan objek.",
    "diagram": "[ Object Detection ] ──▶ [ Object Tracking ] ──▶ [ Line Counter ] ──▶ [ Live Preview / Alert ]",
    "steps": [
      "Hubungkan output dari node Object Tracking ke input Line Counter agar tiap objek memiliki ID unik.",
      "Di panel pengaturan kanan (tab Line Counter), klik tombol '+ Tambah Garis Baru'.",
      "Tentukan titik koordinat awal dan akhir garis (atau klik langsung pada layar frame preview).",
      "Pilih Mode Hitung: Keduanya (IN & OUT), Hanya Masuk (IN Only), atau Hanya Keluar (OUT Only).",
      "Gunakan tombol 'Balik Arah (Invert)' jika tanda panah arah IN / OUT terbalik.",
      "Gunakan tombol 'Hapus Garis' pada kartu garis jika ingin menghapus garis tertentu tanpa mereset data.",
      "Hubungkan ke node If / Else atau Alert Output untuk memicu aksi saat target kuota tercapai."
    ],
    "params": [
      {
        "key": "lines",
        "label": "Daftar Garis (Multi-Line)",
        "desc": "Mendukung pembuatan multi-line (bisa membuat banyak garis dengan warna dan arah berbeda)."
      },
      {
        "key": "triggerAnchor",
        "label": "Titik Pemicu Objek",
        "desc": "center (titik tengah kotak) atau bottom_center (bagian kaki/bawah objek - sangat akurat untuk orang berjalan)."
      },
      {
        "key": "countMode",
        "label": "Mode Penghitungan",
        "desc": "Pilihan: both (IN & OUT), in_only (hanya masuk), out_only (hanya keluar)."
      },
      {
        "key": "invertDirection",
        "label": "Balik Arah Garis",
        "desc": "Membalik orientasi arah tanda panah IN dan OUT jika terpasang terbalik."
      },
      {
        "key": "classes",
        "label": "Filter Kelas Objek",
        "desc": "Batasi hanya menghitung kelas tertentu (misal: 'person' atau 'car'). Kosongkan untuk semua kelas."
      }
    ],
    "tips": "Saat objek menyeberangi garis, bounding box objek akan otomatis berubah warna (hijau/biru/oranye) dan counter IN/OUT akan bertambah secara instan di layar."
  },
  "dwell_time": {
    "concept": "Node ini mengukur durasi waktu (detik) suatu objek berdiam diri di dalam area zona tertentu (Loitering). Sangat efektif untuk mendeteksi orang mencurigakan atau antrean macet.",
    "diagram": "[ Object Tracking ] ──▶ [ Dwell Time / Loitering ] ──▶ [ Alert Output ]",
    "steps": [
      "Hubungkan setelah node Object Tracking.",
      "Atur titik poligon zona pemantauan pada kolom Points.",
      "Tentukan batas durasi waktu pada Threshold Seconds (misal: 10 detik).",
      "Aktifkan Alert on Exceed untuk memicu alarm jika objek berada di zona lebih lama dari batas waktu."
    ],
    "params": [
      {
        "key": "points",
        "label": "Titik Koordinat Zona",
        "desc": "Titik poligon yang membentuk zona pantau (format: x1,y1; x2,y2; ...)."
      },
      {
        "key": "thresholdSeconds",
        "label": "Ambang Batas Waktu (Detik)",
        "desc": "Durasi maksimal sebelum status peringatan aktif (misal 5.0 detik)."
      },
      {
        "key": "showTimer",
        "label": "Tampilkan Timer",
        "desc": "Menampilkan penghitung detik langsung di atas objek pada video."
      },
      {
        "key": "alertOnExceed",
        "label": "Picu Alarm Saat Lewat Batas",
        "desc": "Mengaktifkan status alarm saat waktu singgah melampaui batas."
      }
    ],
    "tips": "Pastikan node Tracker terhubung di upstream agar durasi waktu singgah tercatat akurat per nomor ID objek."
  },
  "filter": {
    "concept": "Node ini menyaring deteksi objek berdasarkan nama kelas, luas kotak piksel, rasio aspek, dan jarak margin tepi layar sebelum masuk ke tahap analisis berikutnya.",
    "diagram": "[ Object Detection ] ──▶ [ Detection & Geometry Filter ] ──▶ [ Tracker / Output ]",
    "steps": [
      "Pasang langsung setelah node Object Detection.",
      "Tuliskan nama kelas yang diizinkan pada kolom Classes (pisahkan dengan koma, misal: person, car).",
      "Gunakan Min Area dan Max Area untuk membuang deteksi noise yang terlalu kecil atau terlalu besar.",
      "Gunakan Exclude Border Margin untuk mengabaikan objek yang terpotong di tepi pinggir layar kamera."
    ],
    "params": [
      {
        "key": "classes",
        "label": "Daftar Kelas (Classes)",
        "desc": "Hanya teruskan objek dengan kelas yang tercantum di sini."
      },
      {
        "key": "minArea",
        "label": "Luas Area Minimal",
        "desc": "Abaikan bounding box dengan luas piksel lebih kecil dari nilai ini."
      },
      {
        "key": "maxArea",
        "label": "Luas Area Maksimal",
        "desc": "Abaikan bounding box dengan luas piksel lebih besar dari nilai ini."
      },
      {
        "key": "excludeBorderMargin",
        "label": "Margin Batas Tepi (Piksel)",
        "desc": "Abaikan objek yang menyentuh margin pinggir kamera."
      }
    ],
    "tips": "Gunakan filter ini untuk membersihkan deteksi palsu sebelum masuk ke tahap tracking dan counting."
  },
  "detections_consensus": {
    "concept": "Node ensemble multi-model yang menggabungkan hasil deteksi dari dua atau lebih model AI berbeda (misal YOLOv8 + RF-DETR) dengan sistem voting IoU untuk menghasilkan deteksi yang jauh lebih akurat dan bebas false positive.",
    "diagram": "[ Model A ] ──┐\n[ Model B ] ──┴──▶ [ Detections Consensus ] ──▶ [ Tracker / Filter ]",
    "steps": [
      "Hubungkan dua atau lebih node deteksi upstream ke node ini.",
      "Atur Required Votes (default 2): objek hanya diloloskan jika minimal 2 model mendeteksi objek yang sama.",
      "Atur IoU Threshold (default 0.5): ambang batas tumpang tindih kotak antar model.",
      "Pilih Confidence Aggregation (Average / Max / Min) dan Box Aggregation."
    ],
    "params": [
      {
        "key": "requiredVotes",
        "label": "Jumlah Suara Sepakat",
        "desc": "Minimal jumlah deteksi/model yang tumpang tindih untuk meloloskan objek."
      },
      {
        "key": "iouThreshold",
        "label": "Ambang Batas IoU",
        "desc": "Derajat tumpang tindih spasial (0.0 - 1.0) antar kotak deteksi model."
      },
      {
        "key": "classAware",
        "label": "Sensitif Terhadap Kelas",
        "desc": "Jika True, deteksi hanya dihitung sepakat jika memiliki label kelas yang sama."
      }
    ],
    "tips": "Sangat ideal untuk inspeksi keselamatan kritis di mana false alarm tidak boleh terjadi."
  },
  "distance_measurement": {
    "concept": "Node pengukuran jarak fisik 2D (sentimeter/meter) antara dua objek deteksi pada bidang datar. Otomatis memicu alarm event proximity_violation jika jarak kedua objek melanggar batas aman minimum.",
    "diagram": "[ Detections / Tracker ] ──▶ [ Distance Measurement ] ──▶ [ Alert / Webhook / Preview ]",
    "steps": [
      "Tentukan Kelas A (misal: person) dan Kelas B (misal: forklift).",
      "Kalibrasi faktor konversi rasio piksel ke sentimeter (Pixel Ratio).",
      "Atur Min Distance Threshold (misal 150 cm untuk batas zona bahaya).",
      "Pilih titik acuan (Bottom Center untuk kontak lantai, Centroid untuk pusat objek)."
    ],
    "params": [
      { "key": "objectAClass", "label": "Kelas Objek A", "desc": "Kelas objek pertama dalam pasangan pengukuran." },
      { "key": "objectBClass", "label": "Kelas Objek B", "desc": "Kelas objek kedua dalam pasangan pengukuran." },
      { "key": "pixelRatio", "label": "Rasio Piksel/cm", "desc": "Jumlah piksel pada gambar untuk merepresentasikan 1 cm fisik." },
      { "key": "minDistanceThreshold", "label": "Batas Jarak Bahaya (cm)", "desc": "Jarak minimum sebelum alarm bahaya dipicu." },
      { "key": "anchorMode", "label": "Titik Acuan Posisi", "desc": "Titik bottom_center atau centroid objek." }
    ],
    "tips": "Gunakan mode bottom_center untuk kamera CCTV dengan sudut miring dari atas agar jarak tapak kaki ke roda kendaraan terukur akurat."
  },
  "size_measurement": {
    "concept": "Node inspeksi dimensi fisik (lebar, tinggi, luas area) dari objek yang terdeteksi. Menyematkan metadata ukuran fisik dan mengevaluasi toleransi min/max untuk penyortiran QA/QC otomatis.",
    "diagram": "[ Detections / Segmentation ] ──▶ [ Size Measurement ] ──▶ [ Logic / Database / Preview ]",
    "steps": [
      "Pilih Target Kelas Inspeksi atau 'all' untuk seluruh objek.",
      "Tentukan faktor konversi Pixel Per Unit dan satuan (mm, cm, m, inch).",
      "Atur batas toleransi dimensi (Min/Max Width dan Min/Max Height).",
      "Aktifkan Trigger Alarm jika ingin menerima peringatan saat ukuran produk tidak standar."
    ],
    "params": [
      { "key": "targetClass", "label": "Target Kelas", "desc": "Nama kelas objek yang akan diukur dimensinya." },
      { "key": "pixelPerUnit", "label": "Piksel per Satuan", "desc": "Rasio kalibrasi piksel terhadap unit fisik." },
      { "key": "unitName", "label": "Satuan Ukuran", "desc": "Satuan fisik (mm, cm, m, inch)." },
      { "key": "minAllowedWidth", "label": "Batas Minimum Lebar", "desc": "Toleransi batas bawah lebar objek." },
      { "key": "maxAllowedWidth", "label": "Batas Maksimum Lebar", "desc": "Toleransi batas atas lebar objek." }
    ],
    "tips": "Kombinasikan dengan node Detection Crop atau Segmenter untuk inspeksi dimensi komponen presisi tinggi pada conveyor belt."
  },
  "camera_focus": {
    "concept": "Node pemantau kesehatan perangkat keras kamera yang menghitung skor ketajaman lensa (Laplacian Variance). Memicu peringatan otomatis bila lensa kamera buram, terkena debu tebal, uap, atau kabut.",
    "diagram": "[ Input / IP Camera ] ──▶ [ Camera Focus Health ] ──▶ [ Alert / Notifications ]",
    "steps": [
      "Letakkan node ini langsung setelah node sumber (Input / IP Camera).",
      "Tentukan Ambang Batas Blur (default: 100.0, semakin kecil semakin buram).",
      "Atur interval pengecekan (Check Interval Seconds) agar efisien.",
      "Opsional: Tentukan ROI poligon jika hanya ingin memeriksa area fokus tertentu."
    ],
    "params": [
      { "key": "blurThreshold", "label": "Ambang Batas Blur", "desc": "Skor Laplacian di bawah nilai ini dianggap buram." },
      { "key": "checkIntervalSeconds", "label": "Interval Pengecekan", "desc": "Jeda waktu antar evaluasi ketajaman lensa." },
      { "key": "enableAlarm", "label": "Picu Alarm", "desc": "Kirim event kamera buram saat skor di bawah ambang batas." },
      { "key": "roi", "label": "Poligon Area Fokus (ROI)", "desc": "Area spesifik untuk evaluasi ketajaman lensa." }
    ],
    "tips": "Gunakan pada kamera outdoor atau area workshop berdebu untuk mendeteksi dini kebutuhan maintenance pembersihan lensa CCTV."
  },
  "auto_rotate_edges": {
    "concept": "Node perataan gambar otomatis (Deskewing / Alignment) yang mendeteksi sudut kemiringan dominan dari tepi kontras tinggi menggunakan MinAreaRect dan merotasinya agar tegak lurus sempurna.",
    "diagram": "[ Input / Crop ] ──▶ [ Auto Rotate Edges ] ──▶ [ AI Detector / Barcode / Classifier ]",
    "steps": [
      "Letakkan sebelum node detektor atau OCR/Barcode yang memerlukan orientasi tegak.",
      "Tentukan Max Angle Limit (default: 45 derajat) untuk membatasi rentang rotasi.",
      "Pilih Border Mode (black_constant untuk latar hitam, replicate untuk duplikasi tepi)."
    ],
    "params": [
      { "key": "maxAngleLimit", "label": "Batas Maksimal Sudut", "desc": "Batas kemiringan ekstrem yang diizinkan untuk dirotasi." },
      { "key": "minAngleThreshold", "label": "Batas Sudut Minimum", "desc": "Ambang batas sudut terkecil sebelum koreksi rotasi dijalankan." },
      { "key": "borderMode", "label": "Mode Batas Tepi", "desc": "Perlakuan piksel pada area kosong hasil rotasi." }
    ],
    "tips": "Sangat ideal untuk conveyor belt paket/box atau pemindaian dokumen agar objek selalu berposisi tegak sebelum klasifikasi."
  },
  "overlap_analysis": {
    "concept": "Node analisis tumpang tindih spasial relasi parent-child untuk inspeksi kepatuhan APD (Alat Pelindung Diri) dan perakitan industri (misal: helm di atas kepala person, sabuk pengaman di tubuh supir).",
    "diagram": "[ Detector / Tracker ] ──▶ [ Overlap Analysis ] ──▶ [ Alert / Output ]",
    "steps": [
      "Tentukan Parent Class (misal: person) dan Child Class (misal: helmet).",
      "Pilih Parent Region (top_half untuk helm/kacamata, bottom_half untuk sepatu, full untuk rompi).",
      "Atur Min Overlap Ratio (default 0.5: minimal 50% area objek anak berada di dalam sub-region induk).",
      "Aktifkan Trigger Alarm jika ingin event otomatis dipicu saat pelanggaran terjadi."
    ],
    "params": [
      { "key": "parentClass", "label": "Kelas Induk", "desc": "Objek utama yang diperiksa kelengkapannya." },
      { "key": "childClass", "label": "Kelas Anak", "desc": "Objek pelengkap yang wajib hadir di sub-region induk." },
      { "key": "minOverlapRatio", "label": "Rasio Overlap Minimal", "desc": "Batas ambang rasio luas tumpang tindih." },
      { "key": "parentRegion", "label": "Sub-Area Induk", "desc": "Bagian tubuh/area induk (top_half, bottom_half, full)." }
    ],
    "tips": "Gunakan mode top_half untuk inspeksi helm keselamatan pekerja proyek agar akurasi tetap tinggi meskipun pekerja menunduk."
  },
  "velocity_calculator": {
    "concept": "Node kinematika video untuk mengestimasi kecepatan gerak objek nyata (km/jam atau m/s) dari perpindahan koordinat centroid per satuan waktu terukur (v = ds/dt).",
    "diagram": "[ Object Tracker ] ──▶ [ Velocity Calculator ] ──▶ [ Alert / Live Preview ]",
    "steps": [
      "Wajib diletakkan setelah node Object Tracker (ByteTrack / BoT-SORT / OC-SORT).",
      "Kalibrasi faktor Pixel Per Meter (jumlah piksel di frame untuk jarak 1 meter nyata).",
      "Tentukan Batas Kecepatan Maksimal (Speed Limit) di area kerja (misal 15 km/jam untuk forklift gudang).",
      "Pilih satuan kecepatan yang diinginkan (km/jam atau m/s)."
    ],
    "params": [
      { "key": "pixelPerMeter", "label": "Piksel per Meter", "desc": "Faktor konversi piksel kamera ke meter fisik." },
      { "key": "speedLimitKmh", "label": "Batas Kecepatan (km/jam)", "desc": "Batas kecepatan aman operasional." },
      { "key": "speedUnit", "label": "Satuan Kecepatan", "desc": "Satuan tampilan kecepatan (kmh / mps)." },
      { "key": "smoothingWindow", "label": "Jendela Peredam EMA", "desc": "Jumlah frame untuk meredam fluktuasi mikro." }
    ],
    "tips": "Untuk kamera yang menghadap miring, gunakan kalibrasi jarak pada bidang lantai untuk hasil kecepatan yang presisi."
  },
  "path_deviation": {
    "concept": "Node pemantau deviasi koridor rute (Virtual Corridor) untuk memastikan kendaraan logistik, forklift, atau AGV tetap berjalan di jalur lintasan yang telah ditetapkan.",
    "diagram": "[ Object Tracker ] ──▶ [ Path Deviation Monitor ] ──▶ [ Alert / Webhook ]",
    "steps": [
      "Tentukan koordinat garis rute baku (Guide Path Points) berupa rangkaian titik x,y.",
      "Tentukan Batas Maksimal Penyimpangan dalam meter (misal 1.5 meter).",
      "Kalibrasi faktor konversi Pixel Per Meter sesuai skala kamera.",
      "Tentukan Target Classes yang dipantau (misal: forklift, vehicle)."
    ],
    "params": [
      { "key": "guidePathPoints", "label": "Titik Rute Baku", "desc": "Rangkaian titik polyline koridor aman." },
      { "key": "maxAllowedDeviationMeters", "label": "Batas Toleransi Deviasi (m)", "desc": "Jarak tegak lurus maksimal dari koridor sebelum alarm." },
      { "key": "pixelPerMeter", "label": "Piksel per Meter", "desc": "Faktor konversi piksel kamera ke meter fisik." },
      { "key": "targetClasses", "label": "Target Kelas Objek", "desc": "Daftar kelas kendaraan yang dipantau." }
    ],
    "tips": "Gunakan pada lorong warehouse sempit untuk mencegah insiden tabrakan forklift dengan rak penyimpanan."
  },
  "delta_filter": {
    "concept": "Node penghemat komputasi AI (Compute & Motion Throttler) yang membandingkan perbedaan visual frame saat ini dengan background/frame sebelumnya. Jika pemandangan diam, inferensi model AI dilewati.",
    "diagram": "[ Input Source ] ──▶ [ Delta Motion Filter ] ──▶ [ AI Detector (Throttled) ]",
    "steps": [
      "Letakkan node ini langsung sebelum model deteksi AI (YOLO / RF-DETR).",
      "Atur Delta Threshold (default: 0.03 = 3% piksel berubah).",
      "Tentukan Heartbeat Interval (misal 15 detik) untuk menjamin frame tetap diproses secara berkala."
    ],
    "params": [
      { "key": "deltaThreshold", "label": "Ambang Batas Gerakan", "desc": "Persentase perubahan piksel untuk mengaktifkan pemrosesan." },
      { "key": "heartbeatIntervalSeconds", "label": "Interval Detak Jantung", "desc": "Jeda waktu maksimal untuk memaksa pemrosesan frame meskipun diam." },
      { "key": "minContourArea", "label": "Luas Kontur Minimum", "desc": "Ukuran kontur gerakan minimal dalam piksel." }
    ],
    "tips": "Menghemat hingga 70-85% penggunaan CPU/GPU pada kamera pengawas gudang yang sering berada dalam kondisi sepi."
  },
  "switch_case": {
    "concept": "Node pengarah alur logika multi-cabang (Multi-Branch Flow Router) yang mendistribusikan data packet atau deteksi ke port cabang keluaran spesifik berdasarkan nilai kelas atau atribut.",
    "diagram": "                    ┌──▶ Port 1 (Person)\n[ Switch Case Router ] ──┼──▶ Port 2 (Forklift)\n                    └──▶ Default Port",
    "steps": [
      "Tentukan bidang evaluasi (Evaluation Field, default: class).",
      "Tuliskan pemetaan kasus (Cases) dengan format nilai:port (misal: person:port_1, forklift:port_2).",
      "Hubungkan masing-masing cabang ke alur downstream yang sesuai."
    ],
    "params": [
      { "key": "evaluationField", "label": "Bidang Evaluasi", "desc": "Metadata yang dievaluasi (class, status, dll)." },
      { "key": "cases", "label": "Daftar Kasus Percabangan", "desc": "Pemetaan nilai ke nama port keluaran." },
      { "key": "defaultPort", "label": "Port Keluaran Default", "desc": "Port tujuan fallback jika tidak ada kasus yang cocok." }
    ],
    "tips": "Gunakan untuk memisahkan alur penanganan orang (masuk ke timer kerja) dan kendaraan (masuk ke logistik) dalam satu pipeline tunggal."
  },
  "model_comparison": {
    "concept": "Node perbandingan dua model AI (Side-by-side & Diff Overlay) untuk evaluasi QA, benchmarking akurasi, dan deteksi disparitas antar arsitektur model secara langsung.",
    "diagram": "[ Model A ] ──┐\n              ├──▶ [ Model Comparison Diff ] ──▶ [ Live Preview ]\n[ Model B ] ──┘",
    "steps": [
      "Sambungkan hasil deteksi dari Model A (misal: YOLOv8) dan Model B (misal: RF-DETR).",
      "Pilih Render Mode: 'side_by_side' untuk tampilan 2 layar berdampingan atau 'diff_overlay' untuk penumpukan satu layar berwarna.",
      "Tentukan ambang batas kesamaan (IoU Threshold) untuk mendefinisikan kesepakatan.",
      "Aktifkan Show Stats Header untuk melihat rasio persetujuan (Agreement Ratio)."
    ],
    "params": [
      { "key": "modelAName", "label": "Nama Model AI A", "desc": "Label identitas model pertama (Cyan)." },
      { "key": "modelBName", "label": "Nama Model AI B", "desc": "Label identitas model kedua (Magenta)." },
      { "key": "renderMode", "label": "Mode Visualisasi", "desc": "side_by_side atau diff_overlay." },
      { "key": "iouThreshold", "label": "Ambang Batas IoU", "desc": "Ambang minimal IoU untuk menganggap objek sama." }
    ],
    "tips": "Dalam mode diff_overlay, kotak hijau menandakan kedua model sepakat, sedangkan kotak cyan/magenta menandakan deteksi unik dari masing-masing model."
  },
  "detections_difference": {
    "concept": "Node perbandingan status deteksi sebelum vs sesudah (State Difference Comparator) untuk mendeteksi kemunculan objek baru atau hilangnya barang dari baseline acuan.",
    "diagram": "[ Object Detector ] ──▶ [ Detections Difference ] ──▶ [ Alarm / Log Event ]",
    "steps": [
      "Ambil snapshot acuan pertama kali (Baseline) saat area dalam kondisi normal.",
      "Tentukan batas ambang IoU pencocokan objek antar frame.",
      "Tentukan filter kelas jika hanya ingin memantau aset tertentu (misal: pallet, box).",
      "Aktifkan Alarm on Difference untuk memicu event darurat saat ada barang hilang/ditambahkan."
    ],
    "params": [
      { "key": "matchIoU", "label": "Ambang Pencocokan IoU", "desc": "Toleransi pergeseran objek agar tetap dianggap objek yang sama." },
      { "key": "filterClasses", "label": "Filter Kelas Objek", "desc": "Hanya bandingkan kelas tertentu (kosong = semua kelas)." },
      { "key": "triggerSnapshot", "label": "Perbarui Baseline", "desc": "Simpan kondisi frame saat ini sebagai acuan normal baru." },
      { "key": "alarmOnDifference", "label": "Picu Alarm", "desc": "Kirim event saat terdeteksi selisih objek." }
    ],
    "tips": "Sangat efektif untuk mendeteksi pencurian barang gudang atau mendeteksi barang tertinggal di area steril."
  },
  "preview": {
    "concept": "Node penampil streaming video langsung (Live Preview) untuk memantau jalankan pipeline secara visual realtime lengkap dengan anotasi, kotak, label, dan statistik.",
    "diagram": "[ Any Pipeline Node ] ──▶ [ Live Preview ]",
    "steps": [
      "Letakkan di akhir alur yang ingin Anda monitor.",
      "Centang elemen yang ingin ditampilkan: Bounding Boxes, Labels, Track IDs, Trails, Counts.",
      "Jika ingin merekam seluruh sesi video ke file, centang Save Video dan tentukan Output Path."
    ],
    "params": [
      {
        "key": "showBoxes",
        "label": "Tampilkan Kotak",
        "desc": "Menampilkan bounding box objek di jendela preview."
      },
      {
        "key": "showLabels",
        "label": "Tampilkan Label Kelas",
        "desc": "Menampilkan teks nama kelas dan skor keyakinan."
      },
      {
        "key": "showTrackIds",
        "label": "Tampilkan ID Pelacak",
        "desc": "Menampilkan nomor ID objek dari tracker."
      },
      {
        "key": "showCounts",
        "label": "Tampilkan Counter",
        "desc": "Menampilkan statistik jumlah objek langsung di atas video."
      },
      {
        "key": "saveVideo",
        "label": "Rekam Video Lengkap",
        "desc": "Menyimpan seluruh streaming video hasil pemrosesan ke file video lokal."
      }
    ],
    "tips": "Anda dapat menghubungkan beberapa node Preview ke berbagai tahapan pipeline untuk membandingkan hasil sebelum dan sesudah proses."
  },
  "alert": {
    "concept": "Node penanganan alarm yang mencatat riwayat event ke log, memberikan peringatan visual, dan merekam klip video bukti kejadian secara otomatis.",
    "diagram": "[ Logic Gate / Counter ] ──▶ [ Alert Output ]",
    "steps": [
      "Hubungkan dari node If / Else atau Line Counter.",
      "Tulis pesan peringatan pada Message.",
      "Centang Record Clip dan tentukan durasi rekaman (detik) jika ingin menyimpan bukti rekaman otomatis.",
      "Atur Cooldown Seconds untuk mencegah alarm berbunyi terus-menerus tanpa jeda."
    ],
    "params": [
      {
        "key": "message",
        "label": "Pesan Peringatan",
        "desc": "Teks keterangan yang dicatat saat event terpicu."
      },
      {
        "key": "recordClip",
        "label": "Rekam Klip Video Bukti",
        "desc": "Otomatis menyimpan rekaman video sebelum dan sesudah kejadian."
      },
      {
        "key": "clipDurationSeconds",
        "label": "Durasi Klip (Detik)",
        "desc": "Panjang video rekaman alarm yang disimpan (misal 5 detik)."
      },
      {
        "key": "cooldownSeconds",
        "label": "Jeda Waktu (Cooldown)",
        "desc": "Waktu jeda minimal sebelum alarm boleh terpicu kembali."
      }
    ],
    "tips": "Klip video alarm akan disimpan di folder data/alerts/ dan dapat ditinjau kembali kapan saja melalui tab Logs."
  },
  "image_output": {
    "concept": "Node penyimpan gambar inspeksi ke media penyimpanan lokal dengan fitur manajemen rotasi pembersihan otomatis (FIFO).",
    "diagram": "[ Pipeline Node ] ──▶ [ Save Images ]",
    "steps": [
      "Tentukan lokasi folder penyimpanan pada kolom Output Directory.",
      "Pilih format gambar (JPG / PNG) dan kualitas kompresi.",
      "Pilih Capture Mode: Full Frame (seluruh tampilan) atau Crop Only (hanya potongan objek terdeteksi).",
      "Tentukan batas maksimal file (FIFO) agar kapasitas hard disk tidak habis."
    ],
    "params": [
      {
        "key": "outputDirectory",
        "label": "Folder Penyimpanan",
        "desc": "Folder tempat menyimpan file gambar."
      },
      {
        "key": "captureMode",
        "label": "Mode Pengambilan",
        "desc": "crop_only (hanya gambar objek) atau full_frame (seluruh gambar)."
      },
      {
        "key": "maxFilesRetention",
        "label": "Batas Maksimal File (FIFO)",
        "desc": "Jumlah file maksimal yang disimpan sebelum file terlama otomatis dihapus."
      },
      {
        "key": "burnWatermark",
        "label": "Cetak Watermark Waktu",
        "desc": "Mencetak tanggal, jam, dan ID objek langsung ke pojok foto."
      }
    ],
    "tips": "Aktifkan 'Burn Watermark' untuk mencetak tanggal, waktu, dan ID objek langsung ke gambar sebagai bukti otentik."
  },
  "draw_text": {
    "concept": "Node untuk menggambar teks statis atau teks dinamis dari variabel pipeline (seperti nama kelas, skor akurasi, waktu, dan hitungan counter) langsung ke frame gambar.",
    "diagram": "[ Tracking / Logic ] ──▶ [ Draw Text ] ──▶ [ Live Preview ]",
    "steps": [
      "Tulis isi teks pada Template Teks. Variabel yang bisa dipakai antara lain {detection.count}, {detection.class}, {detection.confidence}, dan {track.id}.",
      "Klik Atur Posisi & Ukuran di Preview, lalu geser teks untuk memindahkan dan tarik titik sudut untuk mengubah ukurannya.",
      "Untuk pasangan IF / ELSE, samakan Metrik, Operator, dan Nilai pada kedua node; bedakan Pass When (true dan false), lalu hubungkan ke Draw Text berbeda.",
      "Untuk beberapa batas jumlah objek, sambungkan If / Else berikutnya dari cabang ELSE dan atur teks pada tiap cabang."
    ],
    "params": [
      {
        "key": "textTemplate",
        "label": "Template Teks Variabel",
        "desc": "Teks yang ditampilkan, mendukung placeholder variabel seperti {detection.class}."
      },
      {
        "key": "x",
        "label": "Posisi Horizontal X",
        "desc": "Koordinat piksel dari sisi kiri frame."
      },
      {
        "key": "y",
        "label": "Posisi Vertikal Y",
        "desc": "Koordinat piksel dari sisi atas frame."
      },
      {
        "key": "fontScale",
        "label": "Skala Ukuran Huruf",
        "desc": "Faktor pengali ukuran font (default 1.0)."
      },
      {
        "key": "color",
        "label": "Warna Teks (Hex)",
        "desc": "Kode warna hex teks (contoh: #ffffff untuk putih)."
      },
      {
        "key": "background",
        "label": "Gunakan Background Teks",
        "desc": "Menambahkan kotak latar belakang di belakang teks agar terbaca jelas."
      }
    ],
    "tips": "Gunakan {detection.count} untuk jumlah objek pada frame. Kondisi If / Else memilih Draw Text yang dijalankan, dan tiap cabang dapat memiliki isi teks sendiri."
  },
  "draw_boxes": {
    "concept": "Node penggambaran kotak pembatas (bounding box) deteksi dan label variabel pada frame gambar dengan kustomisasi warna dan gaya garis.",
    "diagram": "[ Object Detection ] ──▶ [ Draw Boxes ] ──▶ [ Live Preview ]",
    "steps": [
      "Hubungkan dari model deteksi atau tracking.",
      "Atur warna kotak (color) dan ketebalan garis (thickness).",
      "Centang Show Label jika ingin menampilkan nama kelas di atas kotak.",
      "Gunakan fillOpacity (misal 0.15) jika ingin memberi warna transparan lembut di dalam kotak."
    ],
    "params": [
      {
        "key": "color",
        "label": "Warna Kotak (Hex)",
        "desc": "Warna garis pembatas deteksi (misal: #22c55e)."
      },
      {
        "key": "thickness",
        "label": "Ketebalan Garis (Piksel)",
        "desc": "Ketebalan garis batas kotak (1 - 5 piksel)."
      },
      {
        "key": "showLabel",
        "label": "Tampilkan Label Teks",
        "desc": "Menampilkan nama kelas dan akurasi di atas kotak deteksi."
      },
      {
        "key": "fillOpacity",
        "label": "Transparansi Warna Isi",
        "desc": "Tingkat transparansi warna latar belakang di dalam kotak (0.0 = kosong)."
      }
    ],
    "tips": "Untuk proyek dengan banyak layer anotasi, disarankan menggunakan node 'Overlay / Annotate' yang menyatukan semua jenis visual."
  },
  "overlay_annotate": {
    "concept": "Node penggambaran visual serbaguna yang menyatukan seluruh anotasi visual (bounding box, label nama, skor akurasi, ikon OK/NG, jejak gerakan, heatmap) dalam satu node terintegrasi.",
    "diagram": "[ Tracking / Analysis ] ──▶ [ Overlay / Annotate ] ──▶ [ Live Preview ]",
    "steps": [
      "Hubungkan sebelum node Live Preview atau Save Images.",
      "Buka tab pengaturan Overlay untuk mengaktifkan atau menonaktifkan lapisan layer visual.",
      "Atur warna, ukuran font, dan posisi untuk setiap elemen visual sesuai standar inspeksi Anda."
    ],
    "params": [
      {
        "key": "bounding_boxes",
        "label": "Lapisan Kotak Deteksi",
        "desc": "Menggambar kotak pembatas objek dengan warna dan ketebalan kustom."
      },
      {
        "key": "labels",
        "label": "Lapisan Label Kelas",
        "desc": "Menampilkan nama kelas deteksi di atas objek."
      },
      {
        "key": "confidence",
        "label": "Lapisan Akurasi",
        "desc": "Menampilkan persentase skor keyakinan model AI."
      },
      {
        "key": "result_icons",
        "label": "Lapisan Ikon Hasil (OK/NG)",
        "desc": "Menampilkan badge centang hijau OK atau silang merah NG."
      },
      {
        "key": "vector_arrow",
        "label": "Lapisan Panah Vektor Arah",
        "desc": "Menampilkan garis panah arah pergerakan objek."
      }
    ],
    "tips": "Gunakan template '{detection.class} ({detection.confidence})' untuk menampilkan nama dan akurasi secara ringkas."
  },
  "database_output": {
    "concept": "Menyimpan seluruh data riwayat deteksi, kejadian event alarm, dan statistik pipeline secara permanen ke database lokal SQLite untuk pelaporan dan audit.",
    "diagram": "[ Any Pipeline Node ] ──▶ [ Database Output ]",
    "steps": [
      "Tentukan file database pada Database Path (atau kosongkan untuk memakai default di data/system.db).",
      "Centang data apa saja yang ingin disimpan: Save Detections, Save Events, atau Save Frames.",
      "Tentukan Retention Days (misal: 14 hari) agar data yang lebih tua dari batas tersebut otomatis dibersihkan.",
      "Buka tombol 'Database Records & Logs' pada panel inspector untuk meninjau data yang tersimpan."
    ],
    "params": [
      {
        "key": "databasePath",
        "label": "Lokasi File Database SQLite",
        "desc": "Path file database lokal tempat data disimpan."
      },
      {
        "key": "saveDetections",
        "label": "Simpan Riwayat Deteksi",
        "desc": "Mencatat setiap objek yang terdeteksi ke tabel database."
      },
      {
        "key": "saveEvents",
        "label": "Simpan Kejadian Event Alarm",
        "desc": "Mencatat trigger event penting (misal crossing garis, overcapacity)."
      },
      {
        "key": "retentionDays",
        "label": "Batas Retensi Hari (Auto-Cleanup)",
        "desc": "Jumlah hari data disimpan sebelum data lama otomatis dibersihkan."
      },
      {
        "key": "aggregateHourly",
        "label": "Agregasi Statistik Per Jam",
        "desc": "Mengelompokkan data ke statistik ringkasan per jam untuk grafik analitik."
      }
    ],
    "tips": "Aktifkan opsi Event Objects Only agar database hanya mencatat objek saat terjadi event penting, menghemat memori penyimpanan."
  },
  "webhook_output": {
    "concept": "Mengirimkan data payload event dan foto bukti kejadian secara realtime ke REST API endpoint eksternal, webhook Discord/Slack/Telegram, atau backend server pihak ketiga.",
    "diagram": "[ Alert / Logic ] ──▶ [ Webhook / HTTP Outbound ]",
    "steps": [
      "Masukkan URL webhook tujuan pada kolom URL (contoh: http://127.0.0.1:8000/webhook atau URL cloud API).",
      "Pilih metode HTTP: POST atau PUT.",
      "Atur Cooldown Seconds (misal: 2.0 detik) agar tidak membanjiri server tujuan.",
      "Aktifkan Send Image jika ingin menyertakan gambar bukti kejadian dalam format Base64/Multipart."
    ],
    "params": [
      {
        "key": "url",
        "label": "URL Endpoint Webhook",
        "desc": "Alamat URL REST API endpoint server penerima."
      },
      {
        "key": "method",
        "label": "Metode HTTP",
        "desc": "Metode permintaan HTTP (POST, PUT, GET)."
      },
      {
        "key": "cooldownSeconds",
        "label": "Jeda Cooldown Pengiriman",
        "desc": "Waktu jeda minimal antar pengiriman HTTP request agar tidak spam."
      },
      {
        "key": "sendImage",
        "label": "Sertakan Foto Kejadian",
        "desc": "Menyematkan frame foto bukti kejadian ke dalam payload request."
      },
      {
        "key": "imageQuality",
        "label": "Kualitas Kompresi Foto (JPEG)",
        "desc": "Kualitas gambar foto yang dikirim (10 - 100)."
      },
      {
        "key": "retryCount",
        "label": "Jumlah Percobaan Ulang (Retry)",
        "desc": "Berapa kali pengiriman diulang jika server tujuan gagal merespons."
      }
    ],
    "tips": "Sangat mudah dihubungkan ke bot Telegram, sistem absensi pabrik, atau integrasi SCADA IoT."
  },
  "resize": {
    "concept": "Node pengubah ukuran dimensi frame gambar (skala lebar dan tinggi) ke resolusi target tetap untuk mengoptimalkan kecepatan inferensi AI.",
    "diagram": "[ Input ] ──▶ [ Resize ] ──▶ [ AI Model ]",
    "steps": [
      "Pasang tepat setelah node Input Kamera sebelum masuk ke node model AI.",
      "Tentukan target Width dan Height dalam piksel (misal: 1280x720 atau 640x360).",
      "Pilih algoritma Interpolation: linear (seimbang), area (bagus untuk memperkecil), atau nearest (paling cepat)."
    ],
    "params": [
      {
        "key": "width",
        "label": "Lebar Target (Piksel)",
        "desc": "Lebar resolusi frame baru dalam satuan piksel."
      },
      {
        "key": "height",
        "label": "Tinggi Target (Piksel)",
        "desc": "Tinggi resolusi frame baru dalam satuan piksel."
      },
      {
        "key": "interpolation",
        "label": "Algoritma Interpolasi",
        "desc": "Metode penghitungan piksel: linear, nearest, area, cubic."
      }
    ],
    "tips": "Mengubah resolusi dari 4K/1080p ke 640x360 dapat meningkatkan kecepatan inferensi AI hingga 3x lipat dengan beban GPU yang jauh lebih ringan."
  },
  "crop": {
    "concept": "Node pangkas gambar yang memotong frame video ke koordinat persegi panjang tertentu untuk memfokuskan model AI hanya pada area penting dan menghemat komputasi.",
    "diagram": "[ Input Kamera ] ──▶ [ Crop / Region of Interest ] ──▶ [ AI Model ]",
    "steps": [
      "Pasang tepat setelah node Input Kamera.",
      "Masukkan koordinat X, Y, Width, dan Height area yang ingin dipotong (atau klik 'Draw ROI on Preview').",
      "Frame yang dikirim ke node downstream hanya berupa potongan area tersebut."
    ],
    "params": [
      {
        "key": "x",
        "label": "Titik Koordinat Awal X",
        "desc": "Jarak horizontal sudut kiri atas area potong dalam piksel."
      },
      {
        "key": "y",
        "label": "Titik Koordinat Awal Y",
        "desc": "Jarak vertikal sudut kiri atas area potong dalam piksel."
      },
      {
        "key": "width",
        "label": "Lebar Area Potong",
        "desc": "Lebar potongan gambar dalam satuan piksel."
      },
      {
        "key": "height",
        "label": "Tinggi Area Potong",
        "desc": "Tinggi potongan gambar dalam satuan piksel."
      }
    ],
    "tips": "Memotong area kamera ke bagian yang relevan (misal conveyor belt atau meja sortir) secara signifikan meningkatkan akurasi dan FPS."
  },
  "rotate_flip": {
    "concept": "Node untuk mengubah orientasi sudut frame video (rotasi 90°, 180°, 270°) atau membalikkan arah gambar secara horizontal (mirror) dan vertikal.",
    "diagram": "[ Input ] ──▶ [ Rotate / Flip ] ──▶ [ AI Model ]",
    "steps": [
      "Pasang setelah node Input Kamera.",
      "Pilih sudut rotasi pada Rotation: 0 (normal), 90 (searah jarum jam), 180 (terbalik), atau 270.",
      "Pilih opsi Flip jika ingin membalikkan orientasi: horizontal (mirroring), vertical, atau both."
    ],
    "params": [
      {
        "key": "rotation",
        "label": "Sudut Putaran (Derajat)",
        "desc": "Pilihan putaran sudut: 0, 90, 180, 270 derajat."
      },
      {
        "key": "flip",
        "label": "Pembalikan Arah (Flip)",
        "desc": "Pilihan mirror: none, horizontal, vertical, both."
      }
    ],
    "tips": "Gunakan rotasi 90° atau 270° jika kamera CCTV Anda dipasang secara vertikal (mode portrait) di koridor jalan."
  },
  "color_convert": {
    "concept": "Node konversi ruang warna untuk mengubah representasi warna frame (BGR ke Grayscale, HSV, atau RGB) guna menyederhanakan analisis citra tertentu.",
    "diagram": "[ Input ] ──▶ [ Color Conversion ] ──▶ [ Image Processing ]",
    "steps": [
      "Pilih mode konversi ruang warna yang diinginkan: gray (hitam putih), hsv (rona/kejenuhan), atau rgb.",
      "Sambungkan ke node pengolahan citra berikutnya (misal thresholding atau background subtraction)."
    ],
    "params": [
      {
        "key": "mode",
        "label": "Ruang Warna Target",
        "desc": "Pilihan konversi: gray (grayscale), hsv, rgb, lab."
      }
    ],
    "tips": "Konversi ke Grayscale memotong ukuran data gambar menjadi 1/3 dari ukuran aslinya, sangat mempercepat pemrosesan algoritma non-AI."
  },
  "brightness_contrast": {
    "concept": "Node pra-pemrosesan citra untuk memperbaiki pencahayaan video gelap atau silau, serta dilengkapi fitur Night Vision CLAHE untuk kondisi rekaman malam hari.",
    "diagram": "[ Input Kamera ] ──▶ [ Brightness / Contrast ] ──▶ [ AI Model ]",
    "steps": [
      "Pasang setelah node Input Kamera sebelum masuk ke node AI.",
      "Geser slider Brightness untuk menambah atau mengurangi cahaya.",
      "Centang Auto Low Light atau Use CLAHE untuk mengaktifkan peningkatan kontras adaptif rekaman malam hari (Night Vision)."
    ],
    "params": [
      {
        "key": "brightness",
        "label": "Tingkat Kecerahan",
        "desc": "Penambahan nilai intensitas kecerahan gambar (-100 hingga +100)."
      },
      {
        "key": "contrast",
        "label": "Faktor Kontras",
        "desc": "Pengali kontras citra (1.0 = normal)."
      },
      {
        "key": "useClahe",
        "label": "Night Vision CLAHE",
        "desc": "Peningkatan kontras adaptif lokal untuk area gelap."
      },
      {
        "key": "autoLowLight",
        "label": "Deteksi Otomatis Cahaya Rendah",
        "desc": "Mengaktifkan peningkatan kontras secara dinamis saat ruangan gelap."
      }
    ],
    "tips": "Fitur CLAHE sangat membantu model AI mendeteksi objek di ruangan remang-remang atau kamera CCTV malam hari."
  },
  "blur_sharpen": {
    "concept": "Node filter spasial untuk menghaluskan noise gambar (Blur Gaussian / Median) atau mempertajam detail tepian gambar (Sharpen) sebelum diproses AI.",
    "diagram": "[ Input ] ──▶ [ Blur / Sharpen ] ──▶ [ AI Model ]",
    "steps": [
      "Pilih operasi: blur (rata-rata), gaussian (halus), median (menghapus bintik noise salt-and-pepper), atau sharpen (mempertajam).",
      "Tentukan ukuran Kernel (bilangan ganjil: 3, 5, 7). Semakin besar kernel, semakin kuat efeknya.",
      "Atur kekuatan efek pada Strength (default: 1.0)."
    ],
    "params": [
      {
        "key": "operation",
        "label": "Tipe Operasi Spasial",
        "desc": "Pilihan filter: blur, gaussian, median, sharpen."
      },
      {
        "key": "kernel",
        "label": "Ukuran Kernel Matriks",
        "desc": "Ukuran jendela filter dalam piksel (harus ganjil: 3, 5, 7, 9)."
      },
      {
        "key": "strength",
        "label": "Kekuatan Efek (Strength)",
        "desc": "Faktor pengali intensitas efek penajaman/pengaburan."
      }
    ],
    "tips": "Gunakan filter Sharpen untuk memperjelas teks barcode atau nomor plat kendaraan yang sedikit buram sebelum dibaca model."
  },
  "perspective": {
    "concept": "Node koreksi perspektif (Four-point Bird's Eye View) untuk meluruskan area dengan sudut pandang miring menjadi tampilan tampak atas (Top-Down / Orthogonal).",
    "diagram": "[ Input Kamera ] ──▶ [ Perspective Correction ] ──▶ [ Tracker / Line Counter ]",
    "steps": [
      "Tentukan 4 titik koordinat sudut area miring pada kolom Points (Top-Left; Top-Right; Bottom-Right; Bottom-Left).",
      "Tentukan target lebar (Width) dan tinggi (Height) gambar lurus hasil koreksi.",
      "Frame hasil koreksi akan tampak tegak lurus seolah-olah kamera dipasang persis di atas objek."
    ],
    "params": [
      {
        "key": "points",
        "label": "Koordinat 4 Titik Sudut",
        "desc": "Titik sudut poligon miring (format: x1,y1; x2,y2; x3,y3; x4,y4)."
      },
      {
        "key": "width",
        "label": "Lebar Output Terkoreksi",
        "desc": "Lebar frame hasil transformasi perspektif dalam piksel."
      },
      {
        "key": "height",
        "label": "Tinggi Output Terkoreksi",
        "desc": "Tinggi frame hasil transformasi perspektif dalam piksel."
      }
    ],
    "tips": "Sangat ideal untuk conveyor belt atau pintu masuk parkir agar jarak dan ukuran objek dihitung konsisten di semua sisi."
  },
  "undistort": {
    "concept": "Node kalibrasi lensa kamera untuk menghilangkan efek distorsi cembung (Fisheye Barrel Distortion) menggunakan matriks parameter kalibrasi kamera.",
    "diagram": "[ Input Kamera ] ──▶ [ Camera Undistortion ] ──▶ [ AI Model ]",
    "steps": [
      "Masukkan path file hasil kalibrasi kamera (.yaml / .json) pada Calibration Path.",
      "Atur nilai Alpha (0.0 = potong area hitam di pinggir, 1.0 = pertahankan seluruh piksel sensor).",
      "Garis yang awalnya melengkung di tepi kamera wide-angle akan lurus sempurna."
    ],
    "params": [
      {
        "key": "calibrationPath",
        "label": "Path File Kalibrasi Lensa",
        "desc": "File parameter intrinsik kamera dari proses kalibrasi checkerboard."
      },
      {
        "key": "alpha",
        "label": "Faktor Skala Alpha Lensa",
        "desc": "Rentang 0.0 (tanpa border hitam) hingga 1.0 (semua piksel dipertahankan)."
      }
    ],
    "tips": "Kalibrasi lensa sangat penting dalam pengukuran dimensi fisik (metrologi) agar ukuran produk tidak terdistorsi lensa."
  },
  "background_subtract": {
    "concept": "Algoritma pemisah latar belakang (Background Subtraction MOG2) untuk mendeteksi dan mengekstrak objek bergerak dari latar belakang statis tanpa memerlukan model AI.",
    "diagram": "[ Input Kamera ] ──▶ [ Background Subtraction ] ──▶ [ Motion Trigger ]",
    "steps": [
      "Pilih metode pemisahan: mog2 (adaptif terhadap bayangan).",
      "Atur History (jumlah frame yang digunakan untuk mempelajari latar belakang).",
      "Atur Threshold sensitivitas gerak, dan centang Detect Shadows untuk memisahkan bayangan dari objek asli."
    ],
    "params": [
      {
        "key": "method",
        "label": "Algoritma Pemisahan",
        "desc": "Pilihan algoritma: mog2."
      },
      {
        "key": "history",
        "label": "Jumlah Frame Memori Latar",
        "desc": "Berapa banyak frame historis untuk memperbarui model background."
      },
      {
        "key": "threshold",
        "label": "Ambang Batas Sensitivitas Gerak",
        "desc": "Ambang batas jarak kuadrat Mahalanobis untuk mengelompokkan piksel bergerak."
      },
      {
        "key": "detectShadows",
        "label": "Deteksi & Pisahkan Bayangan",
        "desc": "Membedakan bayangan abu-abu dari objek fisik sebenarnya."
      }
    ],
    "tips": "Sangat hemat daya komputasi CPU sebagai pemicu awal (motion trigger) sebelum mengaktifkan model AI yang lebih berat."
  },
  "blur_anonymizer": {
    "concept": "Node sensor privasi otomatis yang menyamarkan wajah manusia atau plat nomor kendaraan dengan efek blur halus atau sensor piksel (Pixelate) guna mematuhi standar privasi data (GDPR / Privasi Publik).",
    "diagram": "[ Object Detection ] ──▶ [ Privacy Blur ] ──▶ [ Preview / Save Images ]",
    "steps": [
      "Hubungkan setelah node Object Detection.",
      "Tuliskan daftar kelas target yang ingin disensor pada Classes (misal: 'person, face, license_plate').",
      "Pilih mode penyensoran: gaussian (blur halus) atau pixelate (sensor kotak-kotak piksel).",
      "Atur Kernel Size atau Pixelate Block sesuai tingkat keburaman yang diinginkan."
    ],
    "params": [
      {
        "key": "classes",
        "label": "Kelas Yang Disensor",
        "desc": "Daftar nama kelas objek yang akan disensor privasinya."
      },
      {
        "key": "mode",
        "label": "Tipe Efek Sensor",
        "desc": "gaussian (blur halus) atau pixelate (sensor piksel mosaik)."
      },
      {
        "key": "kernelSize",
        "label": "Ukuran Blur Gaussian",
        "desc": "Tingkat keburaman sensor blur (harus bilangan ganjil)."
      },
      {
        "key": "pixelateBlock",
        "label": "Ukuran Kotak Mosaik Piksel",
        "desc": "Ukuran blok piksel sensor (semakin besar semakin tidak terbaca)."
      },
      {
        "key": "insideBbox",
        "label": "Sensor Hanya di Dalam Kotak",
        "desc": "Membatasi efek sensor tepat hanya di dalam bounding box objek."
      }
    ],
    "tips": "Wajib digunakan untuk publikasi rekaman video CCTV area publik atau siaran streaming online."
  },
  "if_else": {
    "concept": "Node percabangan alur logika cerdas (Branching Logic Gate). Aliran data akan DILOLOSKAN ke node downstream jika kondisi terpenuhi, atau DITAHAN jika tidak memenuhi syarat.",
    "diagram": "[ Source / Tracker ] ──▶ [ If / Else (IF or ELSE) ] ──▶ [ Alert / Preview ]",
    "steps": [
      "Pilih Metrik Kondisi yang ingin dievaluasi (jumlah objek, hitungan Line Counter IN/OUT, akurasi, dll).",
      "Pilih Operator logika: >=, >, <=, <, ==, !=.",
      "Tentukan Nilai Acuan (Threshold) yang menjadi target perbandingan.",
      "Pilih Arah Cabang Node Ini: Cabang IF (Benar) atau Cabang ELSE (Salah).",
      "Tarik garis sambungan ke node aksi downstream (seperti Alert Output atau Simpan Foto)."
    ],
    "params": [
      {
        "key": "metric",
        "label": "Metrik Kondisi Evaluasi",
        "desc": "Pilihan data yang diuji: object_count, line_counter_in, line_counter_out, max_confidence."
      },
      {
        "key": "operator",
        "label": "Operator Perbandingan Logika",
        "desc": "gte (>=), gt (>), lte (<=), lt (<), eq (==), neq (!=)."
      },
      {
        "key": "value",
        "label": "Nilai Batas Acuan (Threshold)",
        "desc": "Angka pembanding untuk pengujian logika."
      },
      {
        "key": "passWhen",
        "label": "Arah Cabang Node Ini",
        "desc": "true (lolos saat kondisi terpenuhi / IF) atau false (lolos saat kondisi TIDAK terpenuhi / ELSE)."
      },
      {
        "key": "classes",
        "label": "Target Kelas Objek",
        "desc": "Digunakan jika metrik dipilih class_count untuk menghitung kelas tertentu saja."
      }
    ],
    "tips": "Tarik 2 garis dari node deteksi ke 2 node If/Else berbeda untuk membuat cabang ganda (Cabang IF ➔ Alarm, Cabang ELSE ➔ Tampilan Normal)."
  },
  "compare_value": {
    "concept": "Node pembanding nilai metrik data pipeline dengan nilai ambang batas tertentu untuk filter kondisi alur.",
    "diagram": "[ Pipeline Node ] ──▶ [ Compare Value ] ──▶ [ Action Node ]",
    "steps": [
      "Pilih metrik data yang ingin dibandingkan (jumlah objek, hitungan garis, akurasi).",
      "Tentukan operator perbandingan dan nilai batas ambang acuan.",
      "Data hanya akan diteruskan ke node selanjutnya jika hasil perbandingan bernilai True."
    ],
    "params": [
      {
        "key": "metric",
        "label": "Metrik Yang Dibandingkan",
        "desc": "Pilihan data metrik pipeline yang diuji."
      },
      {
        "key": "operator",
        "label": "Operator Perbandingan",
        "desc": "gte, gt, lte, lt, eq, neq."
      },
      {
        "key": "value",
        "label": "Nilai Batas Acuan",
        "desc": "Angka pembanding untuk pengujian kondisi."
      }
    ],
    "tips": "Gunakan node ini sebagai filter selektif sebelum mengirimkan data ke sistem database eksternal."
  },
  "roi_filter": {
    "concept": "Node penyaring Region of Interest (ROI) untuk membatasi pemrosesan hanya pada objek yang berada di dalam atau di luar area zona tertentu.",
    "diagram": "[ Object Detection ] ──▶ [ ROI Filter ] ──▶ [ Action / Preview ]",
    "steps": [
      "Pasang setelah node deteksi objek.",
      "Tentukan bentuk area: Rectangle (persegi) atau Polygon.",
      "Pilih mode: Inside (hanya loloskan objek di dalam area) atau Outside (hanya loloskan objek di luar area).",
      "Tentukan trigger anchor (bagian tengah atau bawah kaki objek) yang diuji terhadap zona."
    ],
    "params": [
      {
        "key": "shape",
        "label": "Bentuk Area Pantau",
        "desc": "Pilihan bentuk: rectangle (persegi) atau polygon."
      },
      {
        "key": "mode",
        "label": "Mode Filter Area",
        "desc": "inside (hanya objek di dalam) atau outside (hanya objek di luar)."
      },
      {
        "key": "triggerAnchor",
        "label": "Titik Acuan Objek",
        "desc": "center (titik tengah kotak) atau bottom_center (bagian bawah/kaki objek)."
      },
      {
        "key": "showOverlay",
        "label": "Tampilkan Zona di Preview",
        "desc": "Menampilkan garis batas area pantau langsung pada video."
      }
    ],
    "tips": "Klik tombol 'Draw ROI on Preview' di panel pengaturan untuk menggambar area langsung pada frame video."
  },
  "object_count_condition": {
    "concept": "Node filter logika sederhana yang meloloskan frame data hanya jika jumlah objek di layar memenuhi kondisi ambang batas yang ditentukan.",
    "diagram": "[ Object Detection ] ──▶ [ Object Count Condition ] ──▶ [ Alert Output ]",
    "steps": [
      "Tentukan operator perbandingan: gte (>=), gt (>), lte (<=), lt (<), eq (==).",
      "Masukkan target jumlah objek pada count (misal: 5).",
      "Data hanya diteruskan jika jumlah objek saat ini memenuhi syarat tersebut."
    ],
    "params": [
      {
        "key": "operator",
        "label": "Operator Logika",
        "desc": "gte (>=), gt (>), lte (<=), lt (<), eq (==)."
      },
      {
        "key": "count",
        "label": "Target Jumlah Objek",
        "desc": "Batas angka jumlah objek yang diuji."
      }
    ],
    "tips": "Sangat praktis untuk membuat peringatan kerumunan orang (Overcrowding Alert) tanpa konfigurasi rumit."
  },
  "class_detected_condition": {
    "concept": "Node filter logika yang meloloskan frame data hanya jika terdapat deteksi dari kelas target tertentu dalam frame.",
    "diagram": "[ Object Detection ] ──▶ [ Class Detected Condition ] ──▶ [ Alert Output ]",
    "steps": [
      "Tuliskan nama kelas yang dicari pada Classes (misal: 'fire, smoke' atau 'person').",
      "Pilih mode pencocokan (Match): any (salah satu kelas ada) atau all (semua kelas harus ada).",
      "Jika terdeteksi, data langsung diteruskan ke node aksi downstream."
    ],
    "params": [
      {
        "key": "classes",
        "label": "Daftar Kelas Target",
        "desc": "Nama kelas objek yang memicu kondisi ini."
      },
      {
        "key": "match",
        "label": "Mode Pencocokan",
        "desc": "any (cukup salah satu kelas muncul) atau all (semua kelas harus ada)."
      }
    ],
    "tips": "Gunakan untuk memicu alarm bahaya saat terdeteksi kelas kritis seperti api, asap, atau hewan berbahaya."
  },
  "confidence_threshold": {
    "concept": "Node filter akurasi yang menyaring deteksi objek sehingga hanya deteksi dengan skor keyakinan model di atas ambang batas yang diloloskan.",
    "diagram": "[ Object Detection ] ──▶ [ Confidence Threshold ] ──▶ [ Quality Sort ]",
    "steps": [
      "Tentukan ambang batas akurasi pada Threshold (misal: 0.85 atau 85%).",
      "Pilih operator perbandingan (>= atau >).",
      "Deteksi dengan akurasi rendah akan otomatis dibuang agar tidak menimbulkan kesalahan inspeksi."
    ],
    "params": [
      {
        "key": "threshold",
        "label": "Ambang Batas Keyakinan Minimal",
        "desc": "Nilai minimal akurasi (0.0 - 1.0)."
      },
      {
        "key": "operator",
        "label": "Operator Logika",
        "desc": "gte (>=), gt (>), lte (<=), lt (<)."
      }
    ],
    "tips": "Efektif untuk inspeksi kontrol kualitas industri yang memerlukan standar kepastian akurasi sangat tinggi."
  },
  "timer_delay": {
    "concept": "Node penahan waktu (Timer Delay) yang menahan dan menstabilkan sinyal pemicu selama durasi detik tertentu sebelum diteruskan ke node berikutnya.",
    "diagram": "[ Trigger Event ] ──▶ [ Timer / Delay ] ──▶ [ Actuator / Alarm ]",
    "steps": [
      "Pasang di antara node pemicu event dan node aksi eksekusi.",
      "Tentukan durasi jeda waktu dalam detik pada kolom Seconds (misal: 2.5 detik).",
      "Sinyal akan ditahan selama durasi tersebut sebelum menyalakan aktuator atau alarm."
    ],
    "params": [
      {
        "key": "seconds",
        "label": "Durasi Jeda Waktu (Detik)",
        "desc": "Waktu penahanan sinyal dalam satuan detik."
      }
    ],
    "tips": "Berguna untuk sinkronisasi mekanis pabrik (misal memberi waktu lengan robot bergerak sebelum sensor kamera mengambil foto)."
  },
  "debounce": {
    "concept": "Node stabilisasi sinyal (Debounce) untuk mencegah pemicuan berulang-ulang dari deteksi objek yang berkedip-kedip (flickering) dalam rentang waktu singkat.",
    "diagram": "[ Logic / Trigger ] ──▶ [ Debounce ] ──▶ [ Webhook / Alert ]",
    "steps": [
      "Pasang tepat sebelum node output Alert atau Webhook.",
      "Tentukan durasi debounce pada Seconds (misal: 0.5 atau 1.0 detik).",
      "Jika sinyal deteksi berkedip-kedip hilang-timbul cepat, hanya 1 sinyal stabil yang akan diteruskan."
    ],
    "params": [
      {
        "key": "seconds",
        "label": "Durasi Stabilisasi Debounce (Detik)",
        "desc": "Waktu jeda toleransi kestabilan sinyal."
      }
    ],
    "tips": "Wajib digunakan jika kamera mendeteksi objek di area bergetar atau pencahayaan berfluktuasi agar tidak spam notifikasi."
  },
  "rate_limiter": {
    "concept": "Node pembatas frekuensi (Rate Limiter) yang membatasi pengiriman event agar aksi downstream hanya boleh terpicu maksimal satu kali dalam kurun waktu cooldown tertentu.",
    "diagram": "[ Alert Event ] ──▶ [ Rate Limiter ] ──▶ [ Webhook / Notifikasi ]",
    "steps": [
      "Pasang sebelum node pengiriman pesan atau webhook.",
      "Tentukan batas jeda waktu pada Seconds (misal: 30 detik atau 60 detik).",
      "Meskipun alarm terpicu puluhan kali, pesan hanya akan dikirim sekali setiap periode cooldown."
    ],
    "params": [
      {
        "key": "seconds",
        "label": "Jeda Waktu Cooldown (Detik)",
        "desc": "Jeda waktu minimal sebelum event berikutnya boleh dikirim."
      }
    ],
    "tips": "Mencegah kuota API webhook habis atau nomor WhatsApp diblokir akibat spam notifikasi bertubi-tubi."
  },
  "and_or_logic": {
    "concept": "Node gerbang logika kombinasi (Boolean AND / OR) untuk menggabungkan beberapa kondisi evaluasi menjadi satu keputusan akhir.",
    "diagram": "[ Kondisi A & B ] ──▶ [ AND / OR Logic ] ──▶ [ Final Action ]",
    "steps": [
      "Sambungkan beberapa node kondisi logika ke input node ini.",
      "Pilih operator logika: AND (semua kondisi harus bernilai True) atau OR (cukup salah satu kondisi bernilai True).",
      "Aksi downstream hanya akan dieksekusi jika hasil kombinasi logika terpenuhi."
    ],
    "params": [
      {
        "key": "operator",
        "label": "Tipe Gerbang Logika",
        "desc": "Pilihan: 'and' (semua syarat harus terpenuhi) atau 'or' (salah satu syarat terpenuhi)."
      },
      {
        "key": "enabledValue",
        "label": "Nilai Status Logika",
        "desc": "Nilai status boolean yang dicocokkan."
      }
    ],
    "tips": "Contoh: Peringatan hanya menyala jika (Jumlah Orang >= 5) AND (Di Luar Jam Kerja)."
  },
  "trigger_once": {
    "concept": "Node pengunci pemicu (Latch / Trigger Once) yang hanya meloloskan event tepat satu kali saat kondisi pertama kali tercapai, dan mengunci pemicu hingga kondisi kembali normal.",
    "diagram": "[ Kondisi Alarm ] ──▶ [ Trigger Once ] ──▶ [ Sirene / Notifikasi ]",
    "steps": [
      "Pasang tepat sebelum node Alert atau Simpan Foto.",
      "Centang Reset on Clear agar status pemicu otomatis kembali siap saat objek sudah keluar dari area pantau.",
      "Peringatan hanya dikirim 1 kali saat objek pertama kali masuk, tidak berulang setiap frame."
    ],
    "params": [
      {
        "key": "resetOnClear",
        "label": "Reset Otomatis Saat Kondisi Normal",
        "desc": "Membuka kembali kunci pemicu saat kondisi kembali normal (False)."
      }
    ],
    "tips": "Sangat efektif untuk sirene atau lampu indikator pabrik agar tidak terus berbunyi saat objek masih berada di zona pantau."
  },
  "data_aggregator": {
    "concept": "Node agregasi statistik bergulir (Sliding Window Rollup) yang menghitung akumulasi total event, durasi kerja, rata-rata durasi, dan puncak okupansi per jendela waktu operasional (misal per jam atau per shift).",
    "diagram": "[ Zone Activity / Counter / Alert ] ──▶ [ Data Aggregator ] ──▶ [ Dashboard / CSV Formatter / DB ]",
    "steps": [
      "Sambungkan output event dari Zone Activity Timer, Line Counter, atau Multi-Zone Occupancy.",
      "Tentukan rentang jendela waktu (Window Minutes), misalnya 60 menit untuk laporan per jam.",
      "Pilih metrik yang ingin dihitung: count, sum_duration, avg_duration, atau max_occupancy.",
      "Data agregasi siap dialirkan ke CSV Formatter atau dashboard pemantauan berkala."
    ],
    "params": [
      { "key": "windowMinutes", "label": "Jendela Waktu (Menit)", "desc": "Panjang rentang sliding window akumulasi data." },
      { "key": "metricTypes", "label": "Jenis Metrik Analisis", "desc": "Daftar kalkulasi statistik (count, sum_duration, avg_duration, max_occupancy)." }
    ],
    "tips": "Ideal untuk pembuatan rekap produktivitas operator workshop per shift kerja tanpa membebani database utama."
  },
  "csv_formatter": {
    "concept": "Node pemformat data tabular CSV yang mengubah riwayat event, tracking, dan okupansi menjadi baris-baris teks berstruktur CSV siap ekspor ke file atau spreadsheet Excel.",
    "diagram": "[ Event Stream / Aggregator ] ──▶ [ CSV Formatter ] ──▶ [ File / Webhook / ERP ]",
    "steps": [
      "Sambungkan data event masuk ke port input node CSV Formatter.",
      "Tentukan daftar kolom yang diinginkan (contoh: timestamp, zone_name, type, working_seconds, item_count).",
      "Pilih karakter delimiter (koma ',' atau titik koma ';').",
      "Tentukan path file output (misal: data/exports/shift_log.csv) untuk penyimpanan otomatis di server lokal."
    ],
    "params": [
      { "key": "columns", "label": "Kolom Data CSV", "desc": "Daftar nama kolom CSV yang dipisahkan tanda koma." },
      { "key": "delimiter", "label": "Karakter Pemisah", "desc": "Pemisah kolom (default koma ',')." },
      { "key": "outputFilePath", "label": "Lokasi File Simpan", "desc": "Path berkas CSV lokal untuk pencatatan otomatis." }
    ],
    "tips": "File CSV dapat langsung diimpor ke sistem ERP perusahaan atau divisualisasikan dengan Microsoft Excel / PowerBI."
  },
  "s3_sink": {
    "concept": "Node pengunggah penyimpanan objek awan (S3 Object Storage Sink) yang mengirimkan foto snapshot kejadian, frame resolusi penuh, atau crop bukti deteksi ke AWS S3, MinIO, atau Ceph secara aman.",
    "diagram": "[ Filter / Alarm / Crop ] ──▶ [ S3 Cloud Sink ] ──▶ [ Cloud URL / ERP Attachment ]",
    "steps": [
      "Masukkan URL endpoint penyimpanan (default AWS S3 atau MinIO on-premise).",
      "Isi nama bucket tujuan dan prefix direktori (misal: events/ atau cctv/2026/).",
      "Konfigurasikan environment variable credentials (AWS_ACCESS_KEY_ID & AWS_SECRET_ACCESS_KEY).",
      "Atur kualitas kompresi foto JPEG untuk mengoptimalkan kuota dan kecepatan upload."
    ],
    "params": [
      { "key": "endpointUrl", "label": "Endpoint URL", "desc": "Alamat URL API S3 kompatibel (AWS / MinIO / Ceph)." },
      { "key": "bucketName", "label": "Nama Bucket S3", "desc": "Nama wadah penyimpanan di cloud storage." },
      { "key": "objectPrefix", "label": "Prefix Folder", "desc": "Subfolder penyimpanan di dalam bucket." },
      { "key": "imageQuality", "label": "Kualitas Kompresi", "desc": "Kualitas kompresi foto JPEG (10-100, default 85)." }
    ],
    "tips": "Output node menghasilkan URL publik/presigned aman yang dapat langsung disematkan pada pesan notifikasi atau database ERP."
  },
  "notification_dispatcher": {
    "concept": "Node pengiriman notifikasi multi-kanal instan yang menyebarkan pesan peringatan dan foto bukti kejadian ke Telegram Bot, Slack Channel, WhatsApp Business API, atau Webhook dengan jeda pendingin (cooldown throttling).",
    "diagram": "[ Alarm / Security Event ] ──▶ [ Notification Dispatcher ] ──▶ [ Telegram / Slack / WA ]",
    "steps": [
      "Pilih saluran notifikasi utama (Telegram, Slack, WhatsApp, atau Webhook).",
      "Masukkan kredensial Bot Token dan ID Tujuan (Chat ID / Channel / Nomor WhatsApp).",
      "Sesuaikan template pesan dengan placeholder variabel dinamis seperti {event.type} atau {timestamp}.",
      "Aktifkan lampiran foto (Attach Image) agar penerima menerima gambar frame kejadian secara visual.",
      "Atur jeda cooldown untuk mencegah spamming saat kejadian berlangsung terus menerus."
    ],
    "params": [
      { "key": "channel", "label": "Saluran Notifikasi", "desc": "Media perpesanan instan (telegram, slack, whatsapp, webhook)." },
      { "key": "destinationId", "label": "ID Tujuan / Chat ID", "desc": "Target penerima pesan (Chat ID / Channel / Nomor HP)." },
      { "key": "botToken", "label": "Token Bot API", "desc": "Kunci otentikasi bot pengirim pesan." },
      { "key": "messageTemplate", "label": "Format Pesan", "desc": "Template teks pesan dengan tag dinamis." },
      { "key": "attachImage", "label": "Sertakan Foto", "desc": "Kirimkan tangkapan layar frame kejadian sebagai lampiran." },
      { "key": "cooldownSeconds", "label": "Jeda Cooldown (Detik)", "desc": "Durasi jeda antar notifikasi untuk mencegah banjir pesan." }
    ],
    "tips": "Gunakan template pesan yang ringkas dan jelas sehingga petugas patroli lapangan dapat langsung bertindak cepat saat alarm berbunyi."
  },
  "screenshot_capture": {
    "concept": "Node penangkap visual layar (Snapshot/Screenshot) yang merekam momen frame saat terjadi event kejadian atau deteksi dalam bentuk buffer in-memory tanpa membebani disk penyimpanan lokal.",
    "diagram": "[ Event / Detection ] ──▶ [ Screenshot Capture ] ──▶ [ Telegram Alert / Sink ]",
    "steps": [
      "Pilih Capture Mode sesuai kebutuhan (Full Frame Beranotasi, Raw Frame Kamera, atau Crop Objek Pemicu).",
      "Tentukan kualitas kompresi JPEG (default 85) untuk keseimbangan ketajaman dan ukuran file.",
      "Centang Sematkan Cap Waktu jika ingin menyertakan watermark tanggal jam di pojok gambar.",
      "Biarkan Simpan ke Disk tidak dicentang agar tangkapan layar langsung diteruskan via memori RAM ke Telegram."
    ],
    "params": [
      { "key": "captureMode", "label": "Mode Tangkapan", "desc": "Pilihan tangkapan frame utuh beranotasi, frame polos, atau crop objek." },
      { "key": "jpegQuality", "label": "Kualitas JPEG", "desc": "Tingkat kompresi foto visual dari 30 hingga 100." },
      { "key": "addTimestampWatermark", "label": "Watermark Waktu", "desc": "Mencetak tanggal dan jam UTC di bagian sudut bawah frame." },
      { "key": "saveToDisk", "label": "Simpan ke Disk", "desc": "Simpan salinan file fisik JPEG ke folder harddisk lokal." },
      { "key": "outputDirectory", "label": "Folder Arsip", "desc": "Direktori penyimpanan file tangkapan layar jika opsi simpan diaktifkan." }
    ],
    "tips": "Mode Full Frame Beranotasi sangat disukai manajemen karena menampilkan kotak deteksi hijau beserta nama kelas dan skor akurasi secara jelas."
  },
  "telegram_notification": {
    "concept": "Node pengiriman peringatan visual instan ke bot Telegram via API sendPhoto / sendMessage dengan dukungan caption dinamis, cooldown anti-spam, dan upload foto langsung dari RAM.",
    "diagram": "[ Screenshot / Alert Event ] ──▶ [ Telegram Alert ] ──▶ [ Telegram Chat / Grup / Channel ]",
    "steps": [
      "Masukkan Bot Token dari @BotFather dan Chat ID tujuan (grup, channel, atau akun pribadi).",
      "Kustomisasi format caption pesan dengan placeholder dinamis seperti {event.type}, {event.zoneName}, dan {timestamp}.",
      "Pilih mode format Markdown atau HTML sesuai gaya tampilan yang diinginkan.",
      "Atur Jeda Cooldown (detik) untuk membatasi frekuensi kirim agar grup tidak terbanjiri notifikasi berulang."
    ],
    "params": [
      { "key": "botToken", "label": "Token Bot API", "desc": "Kunci otentikasi bot Telegram (fallback ke TELEGRAM_BOT_TOKEN jika kosong)." },
      { "key": "chatId", "label": "ID Obrolan / Chat ID", "desc": "ID penerima pesan Telegram (fallback ke TELEGRAM_CHAT_ID jika kosong)." },
      { "key": "messageCaption", "label": "Format Keterangan (Caption)", "desc": "Template teks pesan notifikasi dengan tag variabel dinamis." },
      { "key": "parseMode", "label": "Format Styling Teks", "desc": "Penguraian tag styling (HTML, Markdown, atau Plain Text)." },
      { "key": "cooldownSeconds", "label": "Jeda Cooldown (Detik)", "desc": "Waktu jeda antar pesan untuk mencegah banjir notifikasi." },
      { "key": "disableNotification", "label": "Kirim Senyap", "desc": "Kirim pesan tanpa memicu nada dering/getar di ponsel penerima." }
    ],
    "tips": "Jika token bot dan chat ID dikosongkan, node akan secara otomatis membaca environment variable TELEGRAM_BOT_TOKEN dan TELEGRAM_CHAT_ID dari sistem."
  },
  "ptz_controller": {
    "concept": "Node pengendali motor kamera fisik PTZ (Pan-Tilt-Zoom) melalui protokol standar ONVIF Continuous Move untuk melacak objek bergerak (Auto-Following) dan menjaganya tetap berada di titik tengah frame inspeksi.",
    "diagram": "[ Object Tracker ] ──▶ [ PTZ Controller (ONVIF) ] ──▶ [ Hardware PTZ Camera ]",
    "steps": [
      "Hubungkan input dari node Object Tracker agar koordinat pergerakan objek terdeteksi stabil.",
      "Masukkan alamat IP kamera fisik PTZ serta nomor port protokol ONVIF.",
      "Tentukan targetClass yang ingin diikuti kamera secara otomatis (misal: person atau forklift).",
      "Atur Deadzone Percent sebagai batas toleransi agar motor kamera tidak bergetar saat target hampir di tengah.",
      "Sesuaikan kecepatan Pan (horizontal) dan Tilt (vertikal) sesuai kelincahan pergerakan objek di lapangan."
    ],
    "params": [
      { "key": "cameraIp", "label": "Alamat IP Kamera PTZ", "desc": "IP Address kamera pengawas di jaringan LAN." },
      { "key": "onvifPort", "label": "Port Layanan ONVIF", "desc": "Port ONVIF kamera (default 80)." },
      { "key": "targetClass", "label": "Target Kelas Objek", "desc": "Kelas objek yang akan diikuti arah geraknya." },
      { "key": "deadzonePercent", "label": "Toleransi Deadzone (%)", "desc": "Ambang batas toleransi tengah frame sebelum kamera berputar." },
      { "key": "panSpeed", "label": "Kecepatan Pan", "desc": "Faktor pengali kecepatan rotasi horizontal kamera (0.0 - 1.0)." },
      { "key": "tiltSpeed", "label": "Kecepatan Tilt", "desc": "Faktor pengali kecepatan kemiringan vertikal kamera (0.0 - 1.0)." }
    ],
    "tips": "Deadzone 15% (0.15) sangat ideal untuk menjaga kestabilan video rekaman tanpa hentakan motor kamera yang kasar."
  },
  "ocr_reader": {
    "concept": "Node OCR Text Reader memanfaatkan model ultra-ringan ONNX (PaddleOCR PP-OCR Mobile v3/v4) berukuran hanya ~2.4 MB (detection) dan ~7.8 MB (recognition) untuk membaca teks, nomor plat kendaraan, kode barcode/resi, dan label industri secara instan tanpa GPU.",
    "diagram": "[ Source / Detection Crop ] ──▶ [ OCR Text Reader (ONNX) ] ──▶ [ Alert / Webhook / Database ]",
    "steps": [
      "Letakkan node setelah Input atau Crop Region / Detector.",
      "Pilih mode: Full-frame (pemindaian seluruh area) atau Crop from Detections (hanya memindai di dalam kotak objek seperti plat nomor atau kemasan).",
      "Isi Character Whitelist jika ingin mengunci karakter tertentu (misal huruf kapital & angka: 0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ).",
      "Hasil teks dan skor keyakinan langsung diekspor sebagai bounding box berlabel dan event ocr_text_read."
    ],
    "params": [
      { "key": "recModelPath", "label": "Model Recognition ONNX", "desc": "Path model pengenal teks PP-OCR mobile (default ppocrv3_en_rec.onnx)." },
      { "key": "detModelPath", "label": "Model Detection ONNX", "desc": "Path model pendeteksi teks DBNet (default ppocrv3_det.onnx)." },
      { "key": "cropFromDetections", "label": "Ekstraksi dari Bounding Box", "desc": "Hanya baca teks di dalam kotak deteksi upstream untuk performa maksimal." },
      { "key": "characterWhitelist", "label": "Filter Karakter (Whitelist)", "desc": "Hanya loloskan karakter yang sesuai pola (misal nomor plat/serial)." },
      { "key": "minConfidence", "label": "Ambang Batas Akurasi", "desc": "Skor keyakinan minimum (0.0 - 1.0) agar teks dicatat." },
      { "key": "emitEvents", "label": "Kirim Event Teks", "desc": "Picu event ocr_text_read ke alert dan database." }
    ],
    "tips": "Model PP-OCR ONNX mobile bekerja sangat cepat (~10ms pada CPU standar) dan sangat ideal untuk ANPR (Automatic Number Plate Recognition) serta logistik pergudangan."
  }
};

  function showNodeGuideModal(nodeOrType) {
    const isObject = typeof nodeOrType === 'object' && nodeOrType !== null;
    const type = isObject ? nodeOrType.type : String(nodeOrType || '');
    const node = isObject ? nodeOrType : null;
    const bp = state.catalog[type] || {};

    if (type === 'if_else') {
      showIfElseGuideModal(node);
      return;
    }

    let modal = $('#nodeUniversalGuideModal');
    if (!modal) {
      modal = document.createElement('dialog');
      modal.id = 'nodeUniversalGuideModal';
      modal.className = 'template-modal';
      modal.style.maxWidth = '780px';
      modal.style.width = '92vw';
      modal.style.borderRadius = '12px';
      modal.style.border = '1px solid var(--border, #334155)';
      modal.style.backgroundColor = 'var(--bg-card, #0f172a)';
      modal.style.color = 'var(--text, #f1f5f9)';
      modal.style.boxShadow = '0 25px 50px -12px rgba(0, 0, 0, 0.7)';
      document.body.append(modal);
    }
    modal.replaceChildren();

    const titleText = (node && node.title) || bp.title || titleFor(type);
    const subText = bp.subtitle || 'Konfigurasi parameter dan panduan alur node';
    const catName = categoryFor(type);
    const guide = NODE_GUIDES_ID[type] || {
      concept: `Node <b>${titleText}</b> berfungsi untuk memproses data alur vision dalam kategori <b>${catName}</b>.`,
      diagram: `[ Upstream Node ] ──▶ [ ${titleText} ] ──▶ [ Downstream Node ]`,
      steps: [
        `Sambungkan input node ini dari node sumber atau node pemrosesan upstream yang sesuai.`,
        `Atur parameter konfigurasi pada panel pengaturan inspector di sebelah kanan.`,
        `Sambungkan output node ini ke node tujuan berikutnya (misalnya Live Preview atau Alert).`
      ],
      params: Object.keys(bp.config || {}).map(k => ({
        key: k,
        label: INDO_FIELD_LABELS[k] || k,
        desc: FIELD_HELP[k] || `Pengaturan untuk parameter ${k}.`
      })),
      tips: `Pastikan tipe data dan koneksi antar node sesuai agar alur pipeline berjalan lancar.`
    };

    const head = document.createElement('div');
    head.className = 'modal-head';
    head.style.display = 'flex';
    head.style.alignItems = 'center';
    head.style.justifyContent = 'space-between';
    head.style.padding = '16px 20px';
    head.style.borderBottom = '1px solid var(--border, #334155)';
    head.innerHTML = `
      <div style="display:flex; align-items:center; gap:12px;">
        <span style="display:inline-flex; align-items:center; justify-content:center; width:36px; height:36px; border-radius:8px; background:rgba(56, 189, 248, 0.15); border:1px solid rgba(56, 189, 248, 0.3);">
          ${getIcon(type, 'icon-md')}
        </span>
        <div>
          <div style="display:flex; align-items:center; gap:8px;">
            <h3 style="margin:0; font-size:16px; font-weight:700; color:var(--text, #f8fafc);">${titleText}</h3>
            <span style="font-size:10px; font-weight:600; padding:2px 8px; border-radius:10px; background:#1e293b; color:#94a3b8; border:1px solid #334155;">${catName}</span>
          </div>
          <small style="color:var(--text-muted, #94a3b8); display:block; margin-top:2px;">${subText}</small>
        </div>
      </div>
    `;

    const closeBtn = document.createElement('button');
    closeBtn.className = 'button ghost';
    closeBtn.textContent = '✕';
    closeBtn.style.fontSize = '16px';
    closeBtn.onclick = () => modal.close();
    head.append(closeBtn);
    modal.append(head);

    const body = document.createElement('div');
    body.className = 'modal-body';
    body.style.padding = '20px';
    body.style.maxHeight = '72vh';
    body.style.overflowY = 'auto';
    body.style.display = 'flex';
    body.style.flexDirection = 'column';
    body.style.gap = '16px';

    let stepsHtml = '';
    if (guide.steps && guide.steps.length) {
      stepsHtml = `
        <div style="background:rgba(30, 41, 59, 0.5); border:1px solid #334155; border-radius:8px; padding:14px;">
          <h4 style="margin:0 0 10px 0; font-size:13px; color:#38bdf8; display:flex; align-items:center; gap:6px;">
            <span>🛠️</span> 3. Langkah-Langkah Cara Penggunaan
          </h4>
          <ol style="margin:0; padding-left:18px; font-size:12px; line-height:1.6; color:#e2e8f0;">
            ${guide.steps.map(s => `<li style="margin-bottom:6px;">${s}</li>`).join('')}
          </ol>
        </div>
      `;
    }

    let paramsHtml = '';
    if (guide.params && guide.params.length) {
      paramsHtml = `
        <div style="background:rgba(30, 41, 59, 0.5); border:1px solid #334155; border-radius:8px; padding:14px;">
          <h4 style="margin:0 0 10px 0; font-size:13px; color:#38bdf8; display:flex; align-items:center; gap:6px;">
            <span>⚙️</span> 4. Penjelasan Parameter &amp; Pengaturan Kunci
          </h4>
          <div style="display:flex; flex-direction:column; gap:8px;">
            ${guide.params.map(p => `
              <div style="background:rgba(15, 23, 42, 0.6); padding:8px 12px; border-radius:6px; border:1px solid #1e293b;">
                <div style="font-weight:700; font-size:11px; color:#f1f5f9; display:flex; align-items:center; gap:6px;">
                  <span style="font-family:monospace; color:#38bdf8;">${p.key}</span>
                  <span style="color:#64748b;">·</span>
                  <span>${p.label}</span>
                </div>
                <div style="font-size:11px; color:#94a3b8; margin-top:2px; line-height:1.4;">${p.desc}</div>
              </div>
            `).join('')}
          </div>
        </div>
      `;
    }

    let tipsHtml = '';
    if (guide.tips) {
      tipsHtml = `
        <div style="background:rgba(56, 189, 248, 0.08); border:1px solid rgba(56, 189, 248, 0.25); border-radius:8px; padding:12px;">
          <div style="font-weight:700; font-size:12px; color:#38bdf8; margin-bottom:4px; display:flex; align-items:center; gap:6px;">
            <span>💡</span> Tips Praktis
          </div>
          <div style="font-size:12px; color:#cbd5e1; line-height:1.5;">${guide.tips}</div>
        </div>
      `;
    }

    body.innerHTML = `
      <!-- Section 1: Konsep Utama -->
      <div style="background:rgba(30, 41, 59, 0.6); border:1px solid #334155; border-radius:8px; padding:14px;">
        <h4 style="margin:0 0 8px 0; font-size:13px; color:#38bdf8; display:flex; align-items:center; gap:6px;">
          <span>💡</span> 1. Konsep &amp; Fungsi Utama
        </h4>
        <p style="margin:0; font-size:12px; line-height:1.5; color:#cbd5e1;">
          ${guide.concept}
        </p>
      </div>

      <!-- Section 2: Skema Alur -->
      <div style="background:rgba(15, 23, 42, 0.8); border:1px solid #334155; border-radius:8px; padding:14px;">
        <h4 style="margin:0 0 10px 0; font-size:13px; color:#38bdf8; display:flex; align-items:center; gap:6px;">
          <span>📐</span> 2. Skema Sambungan di Canvas
        </h4>
        <pre style="margin:0; font-family:monospace; font-size:11px; background:#020617; padding:12px; border-radius:6px; border:1px solid #1e293b; color:#e2e8f0; line-height:1.5; overflow-x:auto;">${guide.diagram}</pre>
      </div>

      <!-- Section 3: Langkah Penggunaan -->
      ${stepsHtml}

      <!-- Section 4: Parameter -->
      ${paramsHtml}

      <!-- Section 5: Tips -->
      ${tipsHtml}
    `;

    modal.append(body);
    modal.showModal();
  }

  async function showDatabaseLogsModal() {
    let modal = $('#dbLogsModal');
    if (!modal) {
      modal = document.createElement('dialog');
      modal.id = 'dbLogsModal';
      modal.className = 'template-modal';
      document.body.append(modal);
    }
    modal.replaceChildren();

    const head = document.createElement('div');
    head.className = 'modal-head';
    head.innerHTML = '<h3>Database Records & Logs</h3>';
    const closeBtn = document.createElement('button');
    closeBtn.className = 'button ghost';
    closeBtn.textContent = '✕';
    closeBtn.onclick = () => modal.close();
    head.append(closeBtn);
    modal.append(head);

    const body = document.createElement('div');
    body.className = 'modal-body';
    body.style.maxHeight = '450px';
    body.style.overflowY = 'auto';
    body.textContent = 'Loading records...';
    modal.append(body);
    modal.showModal();

    try {
      const data = await api('/api/database/records?limit=50');
      if (!data.records || !data.records.length) {
        body.textContent = 'No records saved in database yet.';
        return;
      }
      const table = document.createElement('table');
      table.style.width = '100%';
      table.style.fontSize = '12px';
      table.style.borderCollapse = 'collapse';
      table.innerHTML = '<thead><tr style="border-bottom:1px solid var(--border);text-align:left;"><th>ID</th><th>Time (ms)</th><th>Class</th><th>Conf</th><th>Box [x,y,w,h]</th></tr></thead>';
      const tbody = document.createElement('tbody');
      data.records.forEach(r => {
        const tr = document.createElement('tr');
        tr.style.borderBottom = '1px solid rgba(255,255,255,0.05)';
        const box = `${Math.round(r.x || 0)},${Math.round(r.y || 0)},${Math.round(r.width || 0)},${Math.round(r.height || 0)}`;
        tr.innerHTML = `<td>${r.id}</td><td>${r.timestamp_ms}</td><td><b>${r.class_name}</b></td><td>${(r.confidence || 0).toFixed(2)}</td><td>${box}</td>`;
        tbody.append(tr);
      });
      table.append(tbody);
      body.replaceChildren(table);
    } catch (e) {
      body.textContent = 'Failed to load logs: ' + e.message;
    }
  }

  // --- High-Performance Live Preview Frame Engine ---
  let _previewLoading = false;
  let _lastPreviewFetch = 0;
  let _previewLoopTimer = null;
  let _currentActiveTarget = '';
  let _previewGeneration = 0;

  function invalidatePreview() {
    _previewGeneration += 1;
    if (_previewLoopTimer) clearTimeout(_previewLoopTimer);
    _previewLoopTimer = null;
    _previewLoading = false;
    _currentActiveTarget = '';
    const modal = $('#previewModal');
    const modalImg = $('#modalPreviewImage');
    if (modal?.open) modal.close();
    if (modalImg) modalImg.src = '';
  }

  function previewOwnedByCurrentProject() {
    const status = state.status;
    if (!status) return true;
    if (!status.running) {
      if (!status.projectId && (status.previews || []).length) return false;
      return !status.projectId || status.projectId === state.project?.id;
    }
    return Boolean(status.projectId && status.projectId === state.project?.id);
  }

  function syncDrawTextPreviewEditor() {
    const container = $('#previewContainer');
    const img = $('#previewImage');
    let editor = $('#drawTextPreviewEditor');
    const node = nodeFor(_drawTextEditNodeId);
    if (!container || !img || !node || node.type !== 'draw_text' || !img.naturalWidth || img.hidden) {
      editor?.remove();
      return;
    }
    if (!editor) {
      editor = document.createElement('div');
      editor.id = 'drawTextPreviewEditor';
      editor.className = 'draw-text-preview-editor';
      container.append(editor);
    }
    const frame = container.getBoundingClientRect();
    const image = img.getBoundingClientRect();
    const fit = Math.min(image.width / img.naturalWidth, image.height / img.naturalHeight);
    const width = img.naturalWidth * fit;
    const height = img.naturalHeight * fit;
    const left = image.left - frame.left + (image.width - width) / 2;
    const top = image.top - frame.top + (image.height - height) / 2;
    const scale = Math.max(0.2, Number(node.config.fontScale) || 1);
    const fontSize = Math.max(8, 20 * scale * fit);
    editor.style.left = `${left}px`;
    editor.style.top = `${top}px`;
    editor.style.width = `${width}px`;
    editor.style.height = `${height}px`;
    editor.replaceChildren();

    const label = document.createElement('div');
    label.className = 'draw-text-preview-label';
    label.textContent = String(node.config.textTemplate || 'Text');
    label.style.left = `${Math.max(0, Number(node.config.x) || 0) * fit}px`;
    label.style.top = `${Math.max(0, Number(node.config.y) || 0) * fit - fontSize}px`;
    label.style.fontSize = `${fontSize}px`;
    label.style.color = node.config.color || '#ffffff';
    label.style.background = node.config.background === false ? 'transparent' : (node.config.backgroundColor || '#111827');
    label.style.cursor = 'move';
    label.title = 'Geser untuk mengatur posisi';

    const resize = document.createElement('span');
    resize.className = 'draw-text-preview-resize';
    resize.title = 'Tarik untuk mengatur ukuran';
    label.append(resize);
    editor.append(label);

    const startDrag = (event, resizing) => {
      event.preventDefault();
      event.stopPropagation();
      const startX = event.clientX;
      const startY = event.clientY;
      const baseX = Number(node.config.x) || 0;
      const baseY = Number(node.config.y) || 0;
      const baseScale = Number(node.config.fontScale) || 1;
      const onMove = (moveEvent) => {
        if (resizing) {
          node.config.fontScale = Math.min(4, Math.max(0.2, baseScale + (moveEvent.clientY - startY) / Math.max(1, 20 * fit)));
        } else {
          node.config.x = Math.round(Math.max(0, Math.min(img.naturalWidth, baseX + (moveEvent.clientX - startX) / fit)));
          node.config.y = Math.round(Math.max(1, Math.min(img.naturalHeight, baseY + (moveEvent.clientY - startY) / fit)));
        }
        markDirty();
        syncDrawTextPreviewEditor();
      };
      const onUp = () => {
        window.removeEventListener('pointermove', onMove);
        window.removeEventListener('pointerup', onUp);
        renderInspector();
        liveUpdateWorkflow();
      };
      window.addEventListener('pointermove', onMove);
      window.addEventListener('pointerup', onUp, { once: true });
    };
    label.onpointerdown = (event) => {
      if (event.target !== resize) startDrag(event, false);
    };
    resize.onpointerdown = (event) => startDrag(event, true);
  }

  function scheduleNextPreview(targetId) {
    const generation = _previewGeneration;
    const projectId = state.project?.id;
    if (_previewLoopTimer) clearTimeout(_previewLoopTimer);
    _previewLoopTimer = setTimeout(() => {
      if (generation === _previewGeneration && projectId === state.project?.id && state.status?.running && previewOwnedByCurrentProject()) {
        loadPreviewFrame(targetId, true);
      }
    }, 125); // ~8 FPS silky smooth
  }

  function loadPreviewFrame(targetId, isRunning) {
    const img = $('#previewImage');
    const modalImg = $('#modalPreviewImage');
    const emptyEl = $('#previewEmpty');
    if (!img || !targetId || !previewOwnedByCurrentProject()) {
      if (img && !state.status?.running) {
        img.hidden = true;
        img.src = '';
      }
      if (img && state.status?.running) img.hidden = true;
      if (emptyEl && !img?.src) emptyEl.hidden = false;
      return;
    }

    _currentActiveTarget = targetId;
    const generation = _previewGeneration;
    const projectId = state.project?.id;
    const now = Date.now();
    // Prevent overlapping network requests if one is still in-flight
    if (_previewLoading && (now - _lastPreviewFetch < 2000)) {
      return;
    }

    _previewLoading = true;
    _lastPreviewFetch = now;

    const frameUrl = `/api/preview/${encodeURIComponent(targetId)}?t=${now}`;
    const preloader = new Image();

    preloader.onload = () => {
      _previewLoading = false;
      if (generation !== _previewGeneration || projectId !== state.project?.id || !previewOwnedByCurrentProject() || _currentActiveTarget !== targetId) return;
      img.src = preloader.src;
      img.hidden = false;
      if (emptyEl) emptyEl.hidden = true;
      syncDrawTextPreviewEditor();

      if (modalImg && $('#previewModal')?.open) {
        modalImg.src = preloader.src;
      }

      if (isRunning && state.status?.running && _currentActiveTarget === targetId) {
        scheduleNextPreview(targetId);
      }
    };

    preloader.onerror = () => {
      _previewLoading = false;
      if (generation !== _previewGeneration || projectId !== state.project?.id || !previewOwnedByCurrentProject() || _currentActiveTarget !== targetId) return;
      if (!isRunning && !img.src) {
        img.hidden = true;
        if (emptyEl) emptyEl.hidden = false;
      } else if (isRunning && state.status?.running && _currentActiveTarget === targetId) {
        scheduleNextPreview(targetId);
      }
    };

    preloader.src = frameUrl;
  }

  // --- Preview Select Dropdown ---
  function updatePreviewSelect() {
    const select = $('#previewSelect');
    if (!select) return;
    const current = select.value;
    select.replaceChildren();

    const autoOpt = document.createElement('option');
    autoOpt.value = '';
    autoOpt.textContent = 'Auto Preview';
    select.append(autoOpt);

    const previewNodes = state.workflow.nodes.filter(n => n.type === 'preview');
    previewNodes.forEach(n => {
      const opt = document.createElement('option');
      opt.value = n.id;
      opt.textContent = n.title || n.id;
      select.append(opt);
    });

    // Also include any active preview IDs from the server if not already in the list
    (previewOwnedByCurrentProject() ? state.status?.previews || [] : []).forEach(pId => {
      if (pId !== 'auto_preview' && !previewNodes.some(n => n.id === pId)) {
        const opt = document.createElement('option');
        opt.value = pId;
        opt.textContent = nodeFor(pId)?.title || pId;
        select.append(opt);
      }
    });

    select.value = current;
    select.onchange = () => {
      invalidatePreview();
      state.previewNode = select.value;
      const target = state.previewNode || state.status?.previews?.[0];
      if (target) {
        loadPreviewFrame(target, !!state.status?.running);
      }
      pollStatus();
    };
  }

  // --- Snapshot Capture ---
  async function captureSnapshot() {
    const img = $('#previewImage');
    const target = state.previewNode || state.status?.previews?.[0];
    if (!previewOwnedByCurrentProject() || (!target && (!img || img.hidden || !img.src))) {
      toast('No active preview frame to capture', true);
      return;
    }
    try {
      if (target) {
        const resp = await fetch(`/api/preview/${encodeURIComponent(target)}?t=${Date.now()}`);
        if (resp.ok) {
          const blob = await resp.blob();
          if (!previewOwnedByCurrentProject()) return;
          const link = document.createElement('a');
          link.download = `afi-vision-builder-snapshot-${target}-${Date.now()}.jpg`;
          link.href = URL.createObjectURL(blob);
          link.click();
          setTimeout(() => URL.revokeObjectURL(link.href), 1000);
          toast('Snapshot downloaded (High-res JPG)');
          return;
        }
      }
      if (img && img.naturalWidth) {
        const canvas = document.createElement('canvas');
        canvas.width = img.naturalWidth;
        canvas.height = img.naturalHeight;
        const ctx = canvas.getContext('2d');
        ctx.drawImage(img, 0, 0);
        const link = document.createElement('a');
        link.download = `afi-vision-builder-snapshot-${Date.now()}.png`;
        link.href = canvas.toDataURL('image/png');
        link.click();
        toast('Snapshot downloaded');
      }
    } catch (e) {
      toast('Failed to capture snapshot: ' + e.message, true);
    }
  }

  // --- Fullscreen / Expanded Preview ---
  function toggleFullscreenPreview() {
    const modal = $('#previewModal');
    const modalImg = $('#modalPreviewImage');
    if (!modal || !modalImg) return;

    if (!modal.open) {
      if (!previewOwnedByCurrentProject()) {
        toast('Preview belongs to another project', true);
        return;
      }
      const target = state.previewNode || state.status?.previews?.[0];
      if (target) {
        modalImg.src = state.status?.running
          ? `/api/preview/${encodeURIComponent(target)}/stream`
          : `/api/preview/${encodeURIComponent(target)}?t=${Date.now()}`;
      } else {
        modalImg.src = $('#previewImage')?.src || '';
      }
      $('#modalPreviewTitle').textContent = $('#previewTitle')?.textContent || 'Live Preview';
      modal.showModal();
    } else {
      modalImg.src = '';
      modal.close();
    }
  }

  // --- Templates System ---
  async function loadTemplates() {
    try {
      const data = await api('/api/templates');
      state.templates = data.templates || [];
      renderTemplatesModal();
      renderProjectsHub();
    } catch (e) {
      console.warn('Templates endpoint:', e.message);
    }
  }

  function renderTemplatesModal() {
    const list = $('#templatesList');
    if (!list) return;
    list.replaceChildren();

    state.templates.forEach(t => {
      const card = document.createElement('div');
      card.className = 'template-card';

      const badgeText = t.badge || 'AI Vision';
      const purposeText = t.purpose || t.description || 'Alur kerja visi komputer siap pakai.';

      card.innerHTML = `
        <div style="display:flex; justify-content:space-between; align-items:flex-start; gap:8px;">
          <h3 style="margin:0; font-size:15px; font-weight:700; color:#0f172a;">${escapeHtml(t.name)}</h3>
          <span class="hub-tag-badge" style="background:#e0f2fe; color:#0369a1; flex-shrink:0;">${escapeHtml(badgeText)}</span>
        </div>
        <div class="hub-template-purpose-box" style="margin:8px 0; padding:8px 10px; background:#f8fafc; border-left:3px solid #10b981; border-radius:6px;">
          <div style="font-size:11px; font-weight:700; color:#065f46; display:flex; align-items:center; gap:4px;">
            <span>🎯 Fungsi Utama:</span>
          </div>
          <div style="font-size:12px; color:#334155; margin-top:2px; line-height:1.4;">${escapeHtml(purposeText)}</div>
        </div>
        <p style="margin:0 0 8px; font-size:12px; color:#64748b; line-height:1.4;">${escapeHtml(t.description || '')}</p>
        <div style="display:flex; justify-content:space-between; align-items:center; font-size:11px; color:#94a3b8; border-top:1px solid #f1f5f9; padding-top:8px;">
          <span>${escapeHtml(t.modelSize || 'Includes model')}</span>
          <span style="color:#0284c7; font-weight:600;">Gunakan Template &rarr;</span>
        </div>
      `;

      card.onclick = () => loadTemplate(t);
      list.append(card);
    });
  }

  async function loadTemplate(t) {
    if (state.dirty && !confirm('You have unsaved changes. Load template anyway?')) return;
    const modal = $('#templatesModal');
    if (modal) modal.close();

    const name = prompt('Name for this template project:', t.name);
    if (!name?.trim()) return;

    try {
      const created = await api('/api/projects', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: name.trim(), workflow: t.workflow })
      });
      await loadProjects();
      await switchProject(created.project.id, true);
      toast(`Template "${t.name}" loaded`);
    } catch (e) {
      toast('Failed to load template: ' + e.message, true);
    }
  }

  // --- Uploads (Media & Models) ---
  async function uploadMedia(file) {
    const form = new FormData();
    form.append('file', file);
    try {
      const data = await api('/api/upload', { method: 'POST', body: form });
      await refreshUploads();
      const inputNode = state.workflow.nodes.find(n => n.type === 'input');
      if (!inputNode) {
        return toast('Add an Input node to attach uploaded media', true);
      }
      const kind = data.kind || (file.type.startsWith('video/') ? 'video' : 'image');
      inputNode.config.sourceType = kind;
      inputNode.config.filePath = data.path || data.name || file.name;
      markDirty();
      selectNode(inputNode.id);
      renderInspector();
      toast(`${file.name} attached to Input node`);
    } catch (e) {
      toast(e.message, true);
    }
  }

  async function uploadModelFile(file) {
    const form = new FormData();
    form.append('file', file);
    try {
      const data = await api('/api/models/upload', { method: 'POST', body: form });
      await refreshModels();
      if (state.selected) {
        const n = nodeFor(state.selected);
        if (n && ['detector', 'segmenter', 'classifier'].includes(n.type)) {
          await inspectAndApplyModel(n, data.path);
        } else {
          toast(`Model ${file.name} uploaded. Pilih node AI untuk menggunakannya.`);
        }
      } else {
        toast(`Model ${file.name} uploaded successfully!`);
      }
    } catch (e) {
      toast('Model upload failed: ' + e.message, true);
    }
  }

  async function refreshModels() {
    try {
      const data = await api('/api/models?include_system=true');
      state.models = data.allModels || data.models || [];
      state.customModels = data.customModels || [];
      state.systemModels = data.systemModels || [];
      state.modelEngines = data.engines || [];
      state.modelOptions = data.options || {};
    } catch (e) {
      console.warn('Models error:', e.message);
    }
  }

  async function refreshCameras() {
    try {
      const data = await api('/api/cameras');
      state.cameras = data.cameras || [];
    } catch (e) {
      console.warn('Cameras error:', e.message);
      if (!state.cameras || state.cameras.length === 0) {
        state.cameras = [{ index: 0, label: 'Camera 0 (Default)' }];
      }
    }
  }

  async function refreshUploads() {
    try {
      const data = await api('/api/uploads');
      state.uploads = data.files || [];
    } catch (e) {
      console.warn('Uploads error:', e.message);
    }
  }

  // --- Import / Export ---
  function exportWorkflow() {
    const blob = new Blob([JSON.stringify(state.workflow, null, 2)], { type: 'application/json' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = `${(state.project?.name || 'workflow').replace(/[^a-z0-9]+/gi, '-').toLowerCase()}.json`;
    a.click();
    URL.revokeObjectURL(a.href);
  }

  async function importWorkflow(file) {
    if (state.dirty && !confirm('Discard unsaved changes and import workflow?')) return;
    try {
      const data = JSON.parse(await file.text());
      if (!Array.isArray(data.nodes) || !Array.isArray(data.edges)) {
        throw new Error('JSON file must contain nodes and edges arrays');
      }
      const name = prompt('Name imported project:', file.name.replace(/\.json$/i, ''));
      if (!name?.trim()) return;
      const created = await api('/api/projects', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: name.trim(), workflow: data })
      });
      await loadProjects();
      await switchProject(created.project.id, true);
      toast('Workflow imported');
    } catch (e) {
      toast('Import failed: ' + e.message, true);
    }
  }

  // --- Runtime Status Polling ---
  async function pollStatus() {
    if (state.pollBusy) return;
    state.pollBusy = true;
    try {
      const data = await api('/api/status');
      state.status = data;
      const sameProject = !data.running
        ? (!data.projectId || data.projectId === state.project?.id)
        : Boolean(data.projectId && data.projectId === state.project?.id);
      if (sameProject) {
        state.workflow.nodes.filter(node => node.type === 'frame_sampler').forEach(node => {
          updateFrameSamplerStatus(node.id, data);
        });
        state.workflow.nodes.filter(node => node.type === 'python_script').forEach(node => {
          updatePythonScriptStatus(node.id, data);
        });
        updateAllNodeTelemetryUI(data.nodeTelemetry || {});
      }

      // Status pill
      const pill = $('#runState');
      if (pill) {
        pill.textContent = sameProject ? (data.state ? data.state.toUpperCase() : 'IDLE') : 'OTHER PROJECT';
        pill.className = `status-pill ${sameProject && data.running ? 'running' : sameProject && data.error ? 'error' : ''}`;
      }
      const breadcrumbPill = $('#breadcrumbStatePill');
      if (breadcrumbPill) {
        if (sameProject && data.running) {
          breadcrumbPill.textContent = '• Running';
          breadcrumbPill.className = 'status-indicator-pill running';
        } else {
          breadcrumbPill.textContent = '• Stopped';
          breadcrumbPill.className = 'status-indicator-pill';
        }
      }

      // Buttons
      if ($('#runBtn')) $('#runBtn').disabled = !!data.running;
      if ($('#stopBtn')) $('#stopBtn').disabled = !data.running;

      // Realtime metrics
      const fps = sameProject ? (data.fps || data.previewFps || 0) : 0;
      const latency = sameProject ? (data.latencyMs || 0) : 0;
      const count = sameProject ? (data.objectCount || 0) : 0;
      const device = sameProject ? (data.device || 'CPU') : '—';

      if ($('#statFps')) $('#statFps').textContent = `${Number(fps).toFixed(1)} FPS`;
      if ($('#statLatency')) $('#statLatency').textContent = `${Math.round(latency)} ms`;
      if ($('#statCount')) $('#statCount').textContent = `${count} obj${count === 1 ? '' : 's'}`;
      if ($('#statDevice')) $('#statDevice').textContent = device;

      if (sameProject && data.error && data.error !== state.lastError) {
        toast(data.error, true);
      }
      state.lastError = sameProject ? data.error : null;

      // Logs & Notifications
      renderLogs(sameProject ? data.logs || [] : [], sameProject ? data.events || [] : []);

      if (sameProject && Array.isArray(data.events) && data.events.length) {
        data.events.slice(-3).forEach(ev => {
          const evTime = (ev.time || 0) * 1000;
          if (evTime > (state._lastEventNotifTime || 0)) {
            state._lastEventNotifTime = evTime;
            if (typeof getNotifications === 'function') {
              const notifs = getNotifications();
              const notifId = `ev-${ev.seq || evTime}`;
              if (!notifs.some(n => n.id === notifId)) {
                notifs.unshift({
                  id: notifId,
                  type: 'alert',
                  title: `Alert: ${ev.type || 'Event Terdeteksi'}`,
                  message: ev.message || `Insiden terdeteksi pada ${new Date(evTime).toLocaleTimeString()}`,
                  time: evTime || Date.now(),
                  read: false
                });
                if (notifs.length > 50) notifs.pop();
                if (typeof renderNotifications === 'function') renderNotifications();
              }
            }
          }
        });
      }

      // Preview frame
      const availablePreviews = data.previews || [];
      let targetPreviewId = state.previewNode;
      if (!targetPreviewId || !availablePreviews.includes(targetPreviewId)) {
        targetPreviewId = availablePreviews[0];
      }

      if (sameProject && targetPreviewId && availablePreviews.includes(targetPreviewId)) {
        loadPreviewFrame(targetPreviewId, !!data.running);
        const nodeTitle = targetPreviewId === 'auto_preview' ? 'Live Pipeline Preview' : (nodeFor(targetPreviewId)?.title || targetPreviewId);
        $('#previewTitle').textContent = nodeTitle;
      } else {
        const img = $('#previewImage');
        if (img) {
          img.hidden = true;
          const emptyEl = $('#previewEmpty');
          if (emptyEl) emptyEl.hidden = false;
        }
        $('#previewTitle').textContent = sameProject
          ? (data.running ? 'Processing input…' : 'Waiting for a run')
          : 'Another project is running';
      }
    } catch (e) {
      $('#runtimeText').textContent = 'Connection interrupted';
    } finally {
      state.pollBusy = false;
    }
  }

  function renderLogs(logs, events) {
    const list = $('#logList');
    if (!list) return;

    let unified = [];
    (logs || []).forEach(l => {
      const text = String(l.text || '');
      const isErr = text.toUpperCase().includes('ERROR') || text.toUpperCase().includes('FAILED');
      const isWarn = text.toUpperCase().includes('WARN');
      unified.push({
        seq: l.seq || 0,
        time: l.time,
        text: text,
        type: isErr ? 'error' : (isWarn ? 'warn' : 'log')
      });
    });

    (events || []).forEach(e => {
      unified.push({
        seq: (e.time || 0) * 1000,
        time: e.time,
        text: `${e.title || 'Event'}: ${e.detail || ''}`,
        type: 'event'
      });
    });

    unified.sort((a, b) => (a.time || 0) - (b.time || 0));

    if (state.clearedSeq) {
      unified = unified.filter(item => (item.seq || 0) > state.clearedSeq);
    }

    if (state.logFilter === 'errors') {
      unified = unified.filter(i => i.type === 'error');
    } else if (state.logFilter === 'events') {
      unified = unified.filter(i => i.type === 'event');
    }

    if (state.logSearchQuery) {
      const q = state.logSearchQuery.toLowerCase();
      unified = unified.filter(i => i.text.toLowerCase().includes(q));
    }

    const isAtBottom = list.scrollHeight - list.scrollTop - list.clientHeight < 60;

    const lastItemSeq = unified[unified.length - 1]?.seq;
    if (state._lastLogSeq === lastItemSeq && state._lastLogCount === unified.length && !state._forceLogRender) {
      return;
    }
    state._lastLogSeq = lastItemSeq;
    state._lastLogCount = unified.length;
    state._forceLogRender = false;

    list.replaceChildren();
    if (!unified.length) {
      const empty = document.createElement('div');
      empty.className = 'log-empty';
      empty.textContent = state.logSearchQuery ? 'No matching log entries found.' : 'No runtime events yet.';
      list.append(empty);
      return;
    }

    unified.slice(-150).forEach(item => {
      const row = document.createElement('div');
      const isErr = item.type === 'error';
      const isEvt = item.type === 'event';
      row.className = `log-line ${isErr ? 'error' : (isEvt ? 'event' : '')}`;

      const stamp = document.createElement('span');
      stamp.className = 'log-time';
      stamp.textContent = typeof item.time === 'number'
        ? new Date(item.time * 1000).toLocaleTimeString()
        : (item.time || '');

      const tag = document.createElement('span');
      tag.className = `log-tag ${isErr ? 'err' : (isEvt ? 'evt' : 'info')}`;
      tag.textContent = isErr ? 'ERR' : (isEvt ? 'EVT' : 'INFO');

      const text = document.createElement('span');
      text.style.flex = '1';
      text.textContent = item.text;

      row.append(stamp, tag, text);
      list.append(row);
    });

    if (isAtBottom) {
      list.scrollTop = list.scrollHeight;
    }
  }

  function copyLogs() {
    const list = $('#logList');
    if (!list) return;
    const lines = Array.from(list.querySelectorAll('.log-line')).map(r => r.innerText.replace(/\s+/g, ' ').trim());
    if (!lines.length) {
      toast('No logs to copy', true);
      return;
    }
    navigator.clipboard.writeText(lines.join('\n')).then(() => {
      toast(`Copied ${lines.length} log lines to clipboard`);
    }).catch(() => {
      toast('Failed to copy to clipboard', true);
    });
  }

  // --- Run & Stop ---
  async function run() {
    try {
      if (state.dirty && !(await save())) return;
      const data = await api('/api/run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ projectId: state.project?.id, workflow: state.workflow })
      });
      state.previewNode = state.workflow.nodes.find(n => n.type === 'preview')?.id || '';
      toast(data.message || 'Workflow pipeline running');
      pollStatus();
    } catch (e) {
      toast(e.message, true);
    }
  }

  async function stop() {
    try {
      await api('/api/stop', { method: 'POST' });
      toast('Workflow stopped');
      pollStatus();
    } catch (e) {
      toast(e.message, true);
    }
  }

  // --- Canvas Panning & Wire Tracking ---
  function setupCanvasPan() {
    const canvas = $('#canvas');
    if (!canvas) return;

    const canvasPoint = (e) => {
      const rect = canvas.getBoundingClientRect();
      return {
        x: (e.clientX - rect.left - canvas.clientLeft + canvas.scrollLeft) / state.zoom - state.panX,
        y: (e.clientY - rect.top - canvas.clientTop + canvas.scrollTop) / state.zoom - state.panY,
      };
    };

    const startPan = (e) => {
      state.isPanning = true;
      state.panStart = { x: e.clientX, y: e.clientY, panX: state.panX, panY: state.panY };
      canvas.classList.add('is-panning');
      canvas.setPointerCapture(e.pointerId);
    };

    // Space+drag and middle-button drag work anywhere, including over nodes.
    canvas.addEventListener('pointerdown', (e) => {
      if (e.button !== 1 && !(e.button === 0 && state.spacePan)) return;
      e.preventDefault();
      e.stopPropagation();
      startPan(e);
    }, true);

    document.addEventListener('keydown', (e) => {
      if (e.code !== 'Space' || e.repeat || /^(INPUT|TEXTAREA|SELECT)$/.test(e.target?.tagName)) return;
      if (!canvas.matches(':hover') && document.activeElement !== canvas) return;
      e.preventDefault();
      state.spacePan = true;
      canvas.classList.add('is-pan-ready');
    });
    document.addEventListener('keyup', (e) => {
      if (e.code !== 'Space') return;
      state.spacePan = false;
      canvas.classList.remove('is-pan-ready');
    });
    window.addEventListener('blur', () => {
      state.spacePan = false;
      state.isPanning = false;
      canvas.classList.remove('is-pan-ready', 'is-panning');
    });

    canvas.onpointerdown = (e) => {
      // The nodes layer covers the canvas, so detect empty space by excluding interactive items.
      const onEmptyCanvas = !e.target.closest('.node-card, .port, .edge-hit-area, button, input, select, textarea');
      if (!onEmptyCanvas) return;
      if (state.connecting) {
        state.connecting = null;
        $('#canvasHint').textContent = 'Penyambungan garis dibatalkan';
        renderCanvas();
        return;
      }
      state.selectedEdge = null;
      startPan(e);
    };

    canvas.onpointermove = (e) => {
      if (state.connecting) {
        const point = canvasPoint(e);
        state.connecting.mouseX = point.x;
        state.connecting.mouseY = point.y;
        const hoveredCard = document.elementFromPoint(e.clientX, e.clientY)?.closest('.node-card');
        state.connecting.targetHoverId = (hoveredCard && hoveredCard.dataset.id !== state.connecting.from)
          ? hoveredCard.dataset.id
          : null;
        drawEdges();
      }
      if (!state.isPanning) return;
      state.panX = state.panStart.panX + (e.clientX - state.panStart.x) / state.zoom;
      state.panY = state.panStart.panY + (e.clientY - state.panStart.y) / state.zoom;
      renderCanvas();
    };

    canvas.onpointerup = () => {
      state.isPanning = false;
      canvas.classList.remove('is-panning');
    };

    // Also track pointermove globally when connecting wire is active
    document.addEventListener('pointermove', (e) => {
      if (state.connecting) {
        const point = canvasPoint(e);
        state.connecting.mouseX = point.x;
        state.connecting.mouseY = point.y;
        const hoveredCard = document.elementFromPoint(e.clientX, e.clientY)?.closest('.node-card');
        state.connecting.targetHoverId = (hoveredCard && hoveredCard.dataset.id !== state.connecting.from)
          ? hoveredCard.dataset.id
          : null;
        drawEdges();
      }
    });

    canvas.onwheel = (e) => {
      e.preventDefault();
      const delta = e.deltaY < 0 ? 0.08 : -0.08;
      setZoom(state.zoom + delta);
    };
  }

  // --- Dashboard & Multi-Camera Operations (Fase D, E, F, G PRD) ---
  function switchMainView(viewName) {
    state.activeView = viewName;
    const views = {
      projectsHub: $('#viewProjectsHub'),
      studio: $('#viewStudio'),
      cameras: $('#viewLiveCameras'),
      sessions: $('#viewWorkshopSessions'),
      warehouse: $('#viewWarehouseEvents')
    };
    const tabs = {
      studio: $('#tabStudio'),
      cameras: $('#tabLiveCameras'),
      sessions: $('#tabSessions'),
      warehouse: $('#tabWarehouse')
    };

    Object.keys(views).forEach(key => {
      const el = views[key];
      if (el) {
        if (key === viewName) {
          el.removeAttribute('hidden');
        } else {
          el.setAttribute('hidden', '');
        }
      }
    });

    Object.keys(tabs).forEach(key => {
      const tab = tabs[key];
      if (tab) {
        tab.classList.toggle('active', key === viewName);
      }
    });

    // Topbar header mode: Hub vs Inside Project
    const isHub = (viewName === 'projectsHub');
    const hubActions = $('#hubHeaderActions');
    const projectBreadcrumb = $('#topbarProjectBreadcrumb');
    const projectActions = $('#topbarProjectActions');
    const projectSwitcherWrap = $('#projectSwitcherWrap');
    const projectSwitcherBtn = $('#projectSwitcherBtn');
    const topbarNavTabs = $('#topbarNavTabs');

    if (hubActions) hubActions.hidden = false;
    if (projectBreadcrumb) projectBreadcrumb.hidden = isHub;
    if (projectActions) projectActions.hidden = isHub;
    if (projectSwitcherWrap) projectSwitcherWrap.hidden = isHub;
    if (projectSwitcherBtn) projectSwitcherBtn.hidden = isHub;
    if (topbarNavTabs) topbarNavTabs.hidden = (viewName === 'studio');
    if (isHub) closeProjectSwitcherDropdown();

    if (viewName === 'projectsHub') {
      renderProjectsHub();
    } else if (viewName === 'studio') {
      switchProjectRailTab(state.activeRailTab || 'workflow');
    } else if (viewName === 'cameras') {
      loadDashboardCameras();
    } else if (viewName === 'sessions') {
      loadDashboardSessions();
    } else if (viewName === 'warehouse') {
      loadDashboardWarehouse();
    }
  }
  window.switchMainView = switchMainView;

  async function loadDashboardOverview() {
    try {
      const res = await api('/api/dashboard/overview');
      if (!res) return;
      const onlineBadge = $('#liveCamerasOnlineBadge');
      if (onlineBadge) onlineBadge.textContent = `${res.totalCameras || 8} Online`;
      const kpiTotal = $('#kpiTotalSessions');
      if (kpiTotal) kpiTotal.textContent = `${res.activeSessionsCount || 0} Sesi Aktif`;
      const kpiHours = $('#kpiTotalWorkHours');
      if (kpiHours) kpiHours.textContent = res.totalWorkHoursToday || '0j 0m';
      const kpiWh = $('#kpiWarehouseEvents');
      if (kpiWh) kpiWh.textContent = `${res.todayWarehouseEvents || 0} Event`;
      const kpiErp = $('#kpiErpDelivery');
      if (kpiErp) kpiErp.textContent = `${res.erpDeliveryRate || '—'}`;
    } catch (e) {
      console.warn('Dashboard overview fetch failed:', e);
    }
  }

  let currentCamFilter = 'all';

  function applyCamFilter(filter) {
    currentCamFilter = filter;
    $('#filterCamAll')?.classList.toggle('active', filter === 'all');
    $('#filterCamWS')?.classList.toggle('active', filter === 'workshop');
    $('#filterCamWH')?.classList.toggle('active', filter === 'warehouse');
    loadDashboardCameras(filter);
  }

  async function loadDashboardCameras(filterType = currentCamFilter) {
    try {
      const res = await api('/api/dashboard/cameras');
      const container = $('#cameraGridContainer');
      if (!container || !res?.cameras) return;

      let cameras = res.cameras;
      if (filterType !== 'all') {
        cameras = cameras.filter(c => c.type === filterType);
      }

      container.innerHTML = cameras.map(cam => {
        const isWorkshop = cam.type === 'workshop';
        const typeBadge = isWorkshop 
          ? '<span class="camera-type-badge workshop">Workshop Bay</span>' 
          : '<span class="camera-type-badge warehouse">Warehouse Gate</span>';
        const isOnline = (cam.status || '').toUpperCase() === 'ONLINE';
        const statusBadge = isOnline
          ? '<span class="badge-status-ok">● Online</span>'
          : '<span class="badge-status-failed">● Offline</span>';

        const fpsVal = typeof cam.fps === 'number' ? cam.fps.toFixed(1) : (cam.fps || '25.0');
        const activeSec = cam.activeDuration || 0;
        const durStr = activeSec > 0 ? `${Math.floor(activeSec / 60)}m ${Math.floor(activeSec % 60)}s` : '0m 0s';

        const workflowPill = cam.assignedProjectId
          ? `<button class="camera-workflow-pill active" data-open-proj="${cam.assignedProjectId}" title="Buka Workflow Studio Proyek Kamera Ini" type="button">
              <svg class="icon-svg icon-xs" viewBox="0 0 24 24"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/></svg>
              Workflow Aktif
             </button>`
          : `<button class="camera-workflow-pill" data-settings-cam="${cam.id}" title="Klik untuk hubungkan ke Workflow" type="button">
              + Setup Workflow
             </button>`;

        return `
          <div class="camera-card" data-camera-id="${cam.id}">
            <div class="camera-head">
              <span class="camera-title">
                <svg class="icon-svg icon-sm" viewBox="0 0 24 24"><path d="M23 7l-7 5 7 5V7z"/><rect x="1" y="5" width="15" height="14" rx="2" ry="2"/></svg>
                ${cam.name}
              </span>
              <div style="display:flex;align-items:center;gap:6px">
                ${typeBadge}
                ${statusBadge}
                <button class="camera-settings-btn" data-settings-cam="${cam.id}" title="Pengaturan Kamera & Workflow" type="button" aria-label="Pengaturan ${cam.name}">
                  <svg class="icon-svg icon-xs" viewBox="0 0 24 24"><path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z"/><circle cx="12" cy="12" r="3"/></svg>
                </button>
              </div>
            </div>
            <div class="camera-feed-box">
              <div class="camera-overlay">
                <div class="camera-overlay-top">
                  <span class="badge-live">LIVE</span>
                  <span class="badge-fps">${fpsVal} FPS</span>
                </div>
                <div class="camera-overlay-bot">
                  <span style="font-size:11px;font-family:ui-monospace,monospace;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;max-width:200px" title="${cam.streamUrl}">
                    ${cam.streamUrl}
                  </span>
                  <span style="font-size:10px;color:#9de87b;font-weight:700">${cam.resolution || 'HD 1080p'}</span>
                </div>
              </div>
              <svg viewBox="0 0 400 225" style="width:100%;height:100%;background:#0d1d1b" preserveAspectRatio="none">
                <defs>
                  <linearGradient id="camGrad_${cam.id}" x1="0" y1="0" x2="1" y2="1">
                    <stop offset="0%" stop-color="#122724" />
                    <stop offset="100%" stop-color="#0b1715" />
                  </linearGradient>
                </defs>
                <rect width="400" height="225" fill="url(#camGrad_${cam.id})"/>
                <polygon points="60,40 340,40 320,190 80,190" fill="rgba(34,197,94,0.12)" stroke="#22c55e" stroke-width="2" stroke-dasharray="4 2"/>
                <text x="70" y="60" fill="#a4f49c" font-size="12" font-family="Inter, sans-serif" font-weight="bold">ZONA PENGAWASAN AKTIF (${cam.zoneState || 'AKTIF'})</text>
                <circle cx="200" cy="115" r="16" fill="rgba(200,243,106,0.2)" stroke="#c8f36a" stroke-width="1.5"/>
                <text x="200" y="145" text-anchor="middle" fill="#8cb1a9" font-size="11" font-family="sans-serif">${cam.name}</text>
              </svg>
            </div>
            <div class="camera-meta">
              <span class="camera-zone-state">
                Status Zona: <strong>${cam.zoneState || 'IDLE'}</strong>
              </span>
              <div style="display:flex;align-items:center;gap:8px">
                ${workflowPill}
                <span>Observasi: ${durStr}</span>
              </div>
            </div>
          </div>
        `;
      }).join('');

      // Bind card interactions
      container.querySelectorAll('[data-settings-cam]').forEach(btn => {
        btn.addEventListener('click', (e) => {
          e.stopPropagation();
          const camId = btn.getAttribute('data-settings-cam');
          openCameraSettingsModal(camId);
        });
      });

      container.querySelectorAll('[data-open-proj]').forEach(btn => {
        btn.addEventListener('click', (e) => {
          e.stopPropagation();
          const projId = btn.getAttribute('data-open-proj');
          if (projId) {
            openProjectWorkflow(projId);
          }
        });
      });

    } catch (e) {
      console.warn('Dashboard cameras fetch failed:', e);
    }
  }

  let cachedProjectsList = [];
  let currentEditingCam = null;

  async function openCameraSettingsModal(camId) {
    const modal = $('#cameraSettingsModal');
    if (!modal) return;

    try {
      const [camsRes, projRes] = await Promise.all([
        api('/api/cctv-cameras'),
        api('/api/projects')
      ]);
      const cameras = camsRes?.cameras || [];
      cachedProjectsList = projRes?.projects || [];

      // Populate projects dropdown
      const projSelect = $('#camEditAssignedProject');
      if (projSelect) {
        projSelect.innerHTML = `
          <option value="">-- Belum Ada Workflow (Gunakan Mode Monitor Bawaan) --</option>
          ${cachedProjectsList.map(p => `<option value="${p.id}">${escapeHtml(p.name)}</option>`).join('')}
        `;
      }

      const cam = cameras.find(c => c.id === camId);
      currentEditingCam = cam || null;

      if (cam) {
        $('#cameraSettingsModalTitle').textContent = `Pengaturan Kamera (${cam.id})`;
        $('#cameraSettingsModalSubtitle').textContent = `Konfigurasi RTSP stream dan alur kerja (workflow) untuk ${cam.name}`;
        $('#camEditId').value = cam.id;
        $('#camEditName').value = cam.name || '';
        $('#camEditType').value = cam.type || 'workshop';
        $('#camEditStreamUrl').value = cam.streamUrl || '';
        $('#camEditResolution').value = cam.resolution || '1080p';
        $('#camEditFps').value = cam.fps || 25.0;
        $('#camEditZone').value = cam.zone || '';
        $('#camEditAssignedProject').value = cam.assignedProjectId || '';

        $('#camAutoGenerateWorkflowBtn').style.display = 'inline-block';
        if (cam.assignedProjectId) {
          $('#camOpenInStudioBtn').style.display = 'inline-flex';
          $('#camDrawPolygonBtn').style.display = 'inline-flex';
          const boundProj = cachedProjectsList.find(p => p.id === cam.assignedProjectId);
          $('#camWorkflowStatusHint').textContent = `✔ Terhubung ke workflow: ${boundProj?.name || cam.assignedProjectId}`;
          $('#camWorkflowStatusHint').classList.add('connected');
          $('#camWorkflowStatusHint').style.color = '#047857';
        } else {
          $('#camOpenInStudioBtn').style.display = 'none';
          $('#camDrawPolygonBtn').style.display = 'none';
          $('#camWorkflowStatusHint').textContent = 'Hubungkan kamera ini ke workflow visual untuk pemrosesan AI, deteksi objek, dan event log.';
          $('#camWorkflowStatusHint').classList.remove('connected');
          $('#camWorkflowStatusHint').style.color = '#64748b';
        }

        if (cam.isCustom) {
          $('#camDeleteBtn').style.display = 'inline-block';
        } else {
          $('#camDeleteBtn').style.display = 'none';
        }
      } else {
        // New camera
        $('#cameraSettingsModalTitle').textContent = 'Tambah Kamera CCTV Baru';
        $('#cameraSettingsModalSubtitle').textContent = 'Daftarkan kamera RTSP atau IP Camera baru ke sistem';
        $('#camEditId').value = '';
        $('#camEditName').value = '';
        $('#camEditType').value = 'workshop';
        $('#camEditStreamUrl').value = '';
        $('#camEditResolution').value = '1080p';
        $('#camEditFps').value = 25.0;
        $('#camEditZone').value = '';
        $('#camEditAssignedProject').value = '';
        $('#camAutoGenerateWorkflowBtn').style.display = 'none';
        $('#camOpenInStudioBtn').style.display = 'none';
        $('#camDrawPolygonBtn').style.display = 'none';
        $('#camDeleteBtn').style.display = 'none';
        $('#camWorkflowStatusHint').textContent = 'Pilih project workflow setelah kamera dibuat.';
        $('#camWorkflowStatusHint').style.color = 'var(--text-muted)';
      }

      modal.showModal();
    } catch (err) {
      console.error('Failed to open camera settings modal:', err);
      toast('Gagal memuat pengaturan kamera: ' + err.message, 'error');
    }
  }

  async function loadDashboardSessions() {
    try {
      const shift = $('#shiftFilterSelect')?.value || 'all';
      const search = $('#sessionsSearchInput')?.value?.toLowerCase().trim() || '';
      const res = await api(`/api/dashboard/sessions?shift=${encodeURIComponent(shift)}`);
      const tbody = $('#sessionsTableBody');
      if (!tbody || !res?.sessions) return;

      let rows = res.sessions;
      if (search) {
        rows = rows.filter(r => 
          (r.id && r.id.toLowerCase().includes(search)) || 
          (r.bayId && r.bayId.toLowerCase().includes(search)) || 
          (r.bayName && r.bayName.toLowerCase().includes(search)) || 
          (r.zoneName && r.zoneName.toLowerCase().includes(search))
        );
      }

      if (rows.length === 0) {
        tbody.innerHTML = `
          <tr>
            <td colspan="11" class="text-center py-6 text-muted" style="text-align:center;padding:32px;color:#94a3b8;">
              <div style="font-size:14px;font-weight:500;">Belum ada data sesi workshop yang tercatat</div>
              <div style="font-size:12px;margin-top:4px;color:#64748b;">Jalankan workflow dengan node <strong>Zone Activity Timer</strong> pada kamera workshop untuk mulai mencatat durasi & aktivitas perbaikan.</div>
            </td>
          </tr>
        `;
        return;
      }

      tbody.innerHTML = rows.map(r => {
        const isDone = (r.status || '').toUpperCase() === 'COMPLETED' || (r.status || '').toUpperCase() === 'SELESAI';
        const statusBadge = isDone
          ? '<span class="badge-status-ok">✔ Selesai</span>'
          : '<span class="badge-status-active">⚡ Aktif</span>';

        const startTimeStr = r.startTime ? (r.startTime.includes(' ') ? r.startTime.split(' ')[1] : r.startTime) : '—';
        const endTimeStr = r.endTime ? (r.endTime.includes(' ') ? r.endTime.split(' ')[1] : r.endTime) : '—';

        return `
          <tr>
            <td><strong>${r.id}</strong></td>
            <td>${r.bayName ? `${r.bayName} (${r.bayId})` : r.bayId}</td>
            <td>${r.zoneName || '—'}</td>
            <td>${startTimeStr}</td>
            <td>${endTimeStr}</td>
            <td><strong>${r.durationFormatted || '—'}</strong></td>
            <td>${r.tireCount || 0} Ban</td>
            <td>${r.mechanicCount || 0} Mekanik</td>
            <td><span class="camera-type-badge workshop">${r.shift || 'Pagi'}</span></td>
            <td>${statusBadge}</td>
            <td>
              <button class="button ghost icon-btn-sm" title="Lihat Sesi" onclick="window.toast && window.toast('Sesi ${r.id} tervalidasi observasi.')">
                <svg class="icon-svg icon-sm" viewBox="0 0 24 24"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
              </button>
            </td>
          </tr>
        `;
      }).join('');
    } catch (e) {
      console.warn('Dashboard sessions fetch failed:', e);
    }
  }

  async function loadDashboardWarehouse() {
    try {
      const gate = $('#gateFilterSelect')?.value || 'all';
      const search = $('#warehouseSearchInput')?.value?.toLowerCase().trim() || '';
      const res = await api(`/api/dashboard/warehouse-events?gate=${encodeURIComponent(gate)}`);
      const tbody = $('#warehouseTableBody');
      if (!tbody || !res?.events) return;

      let rows = res.events;
      if (search) {
        rows = rows.filter(r => 
          (r.id && r.id.toLowerCase().includes(search)) || 
          (r.gateId && r.gateId.toLowerCase().includes(search)) || 
          (r.gateName && r.gateName.toLowerCase().includes(search)) || 
          (r.objectClass && r.objectClass.toLowerCase().includes(search))
        );
      }

      if (rows.length === 0) {
        tbody.innerHTML = `
          <tr>
            <td colspan="9" class="text-center py-6 text-muted" style="text-align:center;padding:32px;color:#94a3b8;">
              <div style="font-size:14px;font-weight:500;">Belum ada log perlintasan keluar gerbang yang tercatat</div>
              <div style="font-size:12px;margin-top:4px;color:#64748b;">Jalankan workflow dengan node <strong>Zone Exit Event</strong> pada kamera gudang untuk mencatat log deteksi & pengiriman ERP.</div>
            </td>
          </tr>
        `;
        return;
      }

      tbody.innerHTML = rows.map(r => {
        const isDelivered = (r.erpStatus || '').toUpperCase() === 'DELIVERED';
        const statusBadge = isDelivered
          ? '<span class="badge-status-ok">✔ Delivered</span>'
          : '<span class="badge-status-active">⏳ Queued</span>';

        const timeStr = r.timestamp ? (r.timestamp.includes(' ') ? r.timestamp.split(' ')[1] : r.timestamp) : '—';

        return `
          <tr>
            <td><strong>${r.id}</strong></td>
            <td><span class="camera-type-badge warehouse">${r.gateId || r.gateName}</span></td>
            <td>${timeStr}</td>
            <td><strong>${(r.objectClass || '').toUpperCase()}</strong></td>
            <td>#${r.trackId || 0}</td>
            <td>
              <span style="display:inline-flex;align-items:center;gap:4px;color:#0e7490;font-weight:600">
                <svg class="icon-svg icon-sm" viewBox="0 0 24 24"><line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/></svg>
                ${r.direction || 'OUT'}
              </span>
            </td>
            <td>${statusBadge}</td>
            <td><code>${r.erpResponseCode || 200}</code></td>
            <td>
              <button class="button ghost icon-btn-sm" title="Lihat Snapshot" onclick="window.toast && window.toast('Snapshot ${r.snapshotUrl} tersimpan.')">
                <svg class="icon-svg icon-sm" viewBox="0 0 24 24"><rect width="18" height="18" x="3" y="3" rx="2" ry="2"/><circle cx="9" cy="9" r="2"/><path d="m21 15-3.086-3.086a2 2 0 0 0-2.828 0L6 21"/></svg>
              </button>
            </td>
          </tr>
        `;
      }).join('');
    } catch (e) {
      console.warn('Dashboard warehouse fetch failed:', e);
    }
  }

  // --- Event Wireup ---
  function wireEvents() {
    const shell = $('.app-shell');
    const clamp = (value, min, max) => Math.max(min, Math.min(max, Number(value) || min));
    const persistPanelLayout = () => {
      try { localStorage.setItem(PANEL_LAYOUT_KEY, JSON.stringify(state.panelLayout)); } catch {}
    };

    applyPanelLayout();
    $('#toggleSidebar')?.addEventListener('click', () => {
      state.panelLayout.sidebarHidden = !state.panelLayout.sidebarHidden;
      applyPanelLayout();
      persistPanelLayout();
    });
    $('#toggleBottom')?.addEventListener('click', () => {
      state.panelLayout.bottomHidden = !state.panelLayout.bottomHidden;
      applyPanelLayout();
      persistPanelLayout();
    });
    $('#toggleInspector')?.addEventListener('click', () => {
      state.panelLayout.inspectorHidden = !state.panelLayout.inspectorHidden;
      applyPanelLayout();
      persistPanelLayout();
    });

    for (const [id, size, min, max, direction] of [
      ['resizeSidebar', 'sidebarWidth', 180, 400, 'x'],
      ['resizeInspector', 'inspectorWidth', 220, 480, 'x'],
      ['resizeBottom', 'bottomHeight', 180, 600, 'y'],
    ]) {
      const separator = $(`#${id}`);
      if (!separator) continue;
      const setSize = value => {
        state.panelLayout[size] = clamp(value, min, max);
        separator.setAttribute('aria-valuenow', String(state.panelLayout[size]));
        if (shell) shell.style.setProperty(
          size === 'sidebarWidth' ? '--sidebar-width' : size === 'inspectorWidth' ? '--inspector-width' : '--bottom-height',
          `${state.panelLayout[size]}px`,
        );
      };
      setSize(state.panelLayout[size]);
      separator.addEventListener('pointerdown', event => {
        if (direction === 'x' && window.matchMedia('(max-width: 920px)').matches) return;
        event.preventDefault();
        separator.setPointerCapture(event.pointerId);
        const start = direction === 'x' ? event.clientX : event.clientY;
        const initial = state.panelLayout[size];
        document.body.style.cursor = direction === 'x' ? 'col-resize' : 'row-resize';
        document.body.style.userSelect = 'none';
        const move = moveEvent => {
          const delta = (direction === 'x' ? moveEvent.clientX : moveEvent.clientY) - start;
          setSize(initial + (id === 'resizeInspector' || direction === 'y' ? -delta : delta));
        };
        const end = () => {
          document.body.style.cursor = '';
          document.body.style.userSelect = '';
          persistPanelLayout();
          separator.removeEventListener('pointermove', move);
          separator.removeEventListener('pointerup', end);
          separator.removeEventListener('pointercancel', end);
        };
        separator.addEventListener('pointermove', move);
        separator.addEventListener('pointerup', end);
        separator.addEventListener('pointercancel', end);
      });
      separator.addEventListener('keydown', event => {
        if (!['ArrowLeft', 'ArrowRight', 'ArrowUp', 'ArrowDown'].includes(event.key)) return;
        event.preventDefault();
        const directionKey = direction === 'x'
          ? (id === 'resizeInspector' ? -1 : 1) * (event.key === 'ArrowRight' ? 1 : event.key === 'ArrowLeft' ? -1 : 0)
          : (event.key === 'ArrowDown' ? -1 : event.key === 'ArrowUp' ? 1 : 0);
        if (directionKey) {
          setSize(state.panelLayout[size] + directionKey * (event.shiftKey ? 40 : 12));
          persistPanelLayout();
        }
      });
    }

    // Topbar Main Navigation Tabs
    $('#tabStudio')?.addEventListener('click', () => switchMainView('studio'));
    $('#tabLiveCameras')?.addEventListener('click', () => switchMainView('cameras'));
    $('#tabSessions')?.addEventListener('click', () => switchMainView('sessions'));
    $('#tabWarehouse')?.addEventListener('click', () => switchMainView('warehouse'));

    // Camera Grid Switchers
    $('#gridFocusBtn')?.addEventListener('click', () => {
      $('#cameraGridContainer')?.setAttribute('class', 'camera-grid grid-focus-1');
      $('#gridFocusBtn')?.classList.add('active');
      $('#grid4Btn')?.classList.remove('active');
      $('#grid9Btn')?.classList.remove('active');
    });
    $('#grid4Btn')?.addEventListener('click', () => {
      $('#cameraGridContainer')?.setAttribute('class', 'camera-grid grid-quad-2x2');
      $('#grid4Btn')?.classList.add('active');
      $('#gridFocusBtn')?.classList.remove('active');
      $('#grid9Btn')?.classList.remove('active');
    });
    $('#grid9Btn')?.addEventListener('click', () => {
      $('#cameraGridContainer')?.setAttribute('class', 'camera-grid grid-matrix-3x3');
      $('#grid9Btn')?.classList.add('active');
      $('#gridFocusBtn')?.classList.remove('active');
      $('#grid4Btn')?.classList.remove('active');
    });

    // Camera Filters & Refresh
    $('#filterCamAll')?.addEventListener('click', () => applyCamFilter('all'));
    $('#filterCamWS')?.addEventListener('click', () => applyCamFilter('workshop'));
    $('#filterCamWH')?.addEventListener('click', () => applyCamFilter('warehouse'));
    $('#refreshCamerasBtn')?.addEventListener('click', () => {
      loadDashboardCameras(currentCamFilter);
      loadDashboardOverview();
      toast('Feed CCTV diperbarui');
    });

    // Camera Settings Modal Events
    $('#btnAddNewCamera')?.addEventListener('click', () => openCameraSettingsModal(null));
    $('#closeCameraSettingsModal')?.addEventListener('click', () => $('#cameraSettingsModal')?.close());
    $('#cancelCameraSettingsBtn')?.addEventListener('click', () => $('#cameraSettingsModal')?.close());

    $('#camEditAssignedProject')?.addEventListener('change', (e) => {
      const val = e.target.value;
      if (val) {
        $('#camOpenInStudioBtn').style.display = 'inline-flex';
        $('#camDrawPolygonBtn').style.display = 'inline-flex';
        const boundProj = cachedProjectsList.find(p => p.id === val);
        $('#camWorkflowStatusHint').textContent = `✔ Terhubung ke workflow: ${boundProj?.name || val}`;
        $('#camWorkflowStatusHint').classList.add('connected');
        $('#camWorkflowStatusHint').style.color = '#047857';
      } else {
        $('#camOpenInStudioBtn').style.display = 'none';
        $('#camDrawPolygonBtn').style.display = 'none';
        $('#camWorkflowStatusHint').textContent = 'Hubungkan kamera ini ke workflow visual untuk pemrosesan AI, deteksi objek, dan event log.';
        $('#camWorkflowStatusHint').classList.remove('connected');
        $('#camWorkflowStatusHint').style.color = '#64748b';
      }
    });

    $('#camOpenInStudioBtn')?.addEventListener('click', () => {
      const projId = $('#camEditAssignedProject')?.value;
      if (projId) {
        $('#cameraSettingsModal')?.close();
        openProjectWorkflow(projId);
      }
    });

    $('#camDrawPolygonBtn')?.addEventListener('click', async () => {
      const projId = $('#camEditAssignedProject')?.value;
      if (!projId) {
        toast('Pilih atau buat workflow terlebih dahulu', 'warn');
        return;
      }
      $('#cameraSettingsModal')?.close();
      await openProjectWorkflow(projId);

      const zoneNode = state.workflow?.nodes?.find(n => 
        ['zone_activity_timer', 'zone_exit_event', 'roi_filter'].includes(n.type)
      );

      if (zoneNode) {
        selectNode(zoneNode.id);
        setTimeout(() => {
          if (zoneNode.type === 'roi_filter') {
            startRoiDrawing(zoneNode);
          } else {
            startPolygonZoneDrawing(zoneNode);
          }
          toast('📐 Mode gambar zona aktif: Klik preview untuk menentukan titik sudut area kerja, lalu klik Simpan Zona.', 'info');
        }, 350);
      } else {
        toast('Workflow terbuka di Studio. Tambahkan node Zone Activity Timer untuk memantau area.', 'info');
      }
    });

    $('#camAutoGenerateWorkflowBtn')?.addEventListener('click', async () => {
      const camId = $('#camEditId')?.value;
      if (!camId) return;
      try {
        toast('Membuat workflow otomatis dari template…');
        const res = await api(`/api/cctv-cameras/${camId}/create-workflow`, { method: 'POST' });
        if (res?.project) {
          toast(`Workflow "${res.project.name}" berhasil dibuat!`, 'success');
          await openCameraSettingsModal(camId);
          loadDashboardCameras(currentCamFilter);
        }
      } catch (err) {
        toast('Gagal membuat workflow: ' + err.message, 'error');
      }
    });

    $('#saveCameraSettingsBtn')?.addEventListener('click', async () => {
      const camId = $('#camEditId')?.value;
      const name = $('#camEditName')?.value.trim();
      const type = $('#camEditType')?.value;
      const streamUrl = $('#camEditStreamUrl')?.value.trim();
      const resolution = $('#camEditResolution')?.value;
      const fps = parseFloat($('#camEditFps')?.value) || 25.0;
      const zone = $('#camEditZone')?.value.trim();
      const assignedProjectId = $('#camEditAssignedProject')?.value;

      if (!name) {
        toast('Nama kamera wajib diisi', 'error');
        return;
      }

      const payload = { name, type, streamUrl, resolution, fps, zone, assignedProjectId };
      try {
        if (camId) {
          await api(`/api/cctv-cameras/${camId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
          });
          toast(`Pengaturan kamera ${camId} berhasil disimpan!`, 'success');
        } else {
          const res = await api('/api/cctv-cameras', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
          });
          toast(`Kamera ${res?.camera?.id || name} berhasil ditambahkan!`, 'success');
        }
        $('#cameraSettingsModal')?.close();
        loadDashboardCameras(currentCamFilter);
        loadDashboardOverview();
      } catch (err) {
        toast('Gagal menyimpan kamera: ' + err.message, 'error');
      }
    });

    $('#camDeleteBtn')?.addEventListener('click', async () => {
      const camId = $('#camEditId')?.value;
      if (!camId) return;
      if (!confirm(`Hapus kamera ${camId}?`)) return;
      try {
        await api(`/api/cctv-cameras/${camId}`, { method: 'DELETE' });
        toast(`Kamera ${camId} berhasil dihapus`, 'success');
        $('#cameraSettingsModal')?.close();
        loadDashboardCameras(currentCamFilter);
        loadDashboardOverview();
      } catch (err) {
        toast('Gagal menghapus kamera: ' + err.message, 'error');
      }
    });

    // Sessions Filter, Search & Export
    $('#shiftFilterSelect')?.addEventListener('change', () => loadDashboardSessions());
    $('#sessionsSearchInput')?.addEventListener('input', () => loadDashboardSessions());
    $('#exportSessionsBtn')?.addEventListener('click', () => {
      window.open('/api/dashboard/export-sessions', '_blank');
      toast('Mengunduh rekap sesi workshop (CSV)…');
    });

    // Warehouse Filter, Search & Export
    $('#gateFilterSelect')?.addEventListener('change', () => loadDashboardWarehouse());
    $('#warehouseSearchInput')?.addEventListener('input', () => loadDashboardWarehouse());
    $('#exportWarehouseBtn')?.addEventListener('click', () => {
      window.open('/api/dashboard/export-warehouse', '_blank');
      toast('Mengunduh log keluar gerbang warehouse (CSV)…');
    });

    $('#nodeSearch')?.addEventListener('input', renderLibrary);
    $('#saveBtn')?.addEventListener('click', save);
    $('#runBtn')?.addEventListener('click', run);
    $('#stopBtn')?.addEventListener('click', stop);
    $('#newProject')?.addEventListener('click', newProject);
    $('#renameProject')?.addEventListener('click', renameProject);

    $('#uploadBtn')?.addEventListener('click', () => $('#fileInput').click());
    $('#fileInput')?.addEventListener('change', e => e.target.files[0] && uploadMedia(e.target.files[0]));

    $('#uploadModelBtn')?.addEventListener('click', () => $('#modelInput').click());
    $('#modelInput')?.addEventListener('change', e => {
      const file = e.target.files[0];
      e.target.value = '';
      if (file) uploadModelFile(file);
    });

    $('#templatesBtn')?.addEventListener('click', () => {
      const modal = $('#templatesModal');
      if (modal) modal.showModal();
    });
    $('#closeTemplatesModal')?.addEventListener('click', () => $('#templatesModal')?.close());

    $('#exportBtn')?.addEventListener('click', exportWorkflow);
    $('#importBtn')?.addEventListener('click', () => $('#importInput').click());
    $('#importInput')?.addEventListener('change', e => e.target.files[0] && importWorkflow(e.target.files[0]));

    $('#closeInspector')?.addEventListener('click', () => {
      state.selected = null;
      renderCanvas();
      renderInspector();
    });

    $('#deleteBtn')?.addEventListener('click', deleteSelectedNode);

    // Auto-Connect Toggle & Auto-Assemble button
    const autoToggle = $('#autoConnectToggle');
    if (autoToggle) {
      autoToggle.checked = state.autoConnect !== false;
      autoToggle.addEventListener('change', e => {
        state.autoConnect = !!e.target.checked;
        toast(state.autoConnect ? '⚡ Mode Auto-Connect aktif' : '🛠️ Mode Manual aktif (koneksi manual)');
      });
    }

    $('#autoAssembleBtn')?.addEventListener('click', autoAssembleWorkflow);

    // Dismiss edge context menu on click outside
    document.addEventListener('click', e => {
      if (!e.target.closest('#edgeContextMenu') && !e.target.closest('.edge-hit-area')) {
        hideEdgeContextMenu();
      }
    });

    // Zoom Controls
    $('#zoomInBtn')?.addEventListener('click', () => setZoom(state.zoom + 0.15));
    $('#zoomOutBtn')?.addEventListener('click', () => setZoom(state.zoom - 0.15));
    $('#zoomResetBtn')?.addEventListener('click', () => {
      state.panX = 0;
      state.panY = 0;
      setZoom(1.0);
    });

    $('#fitBtn')?.addEventListener('click', () => {
      const canvas = $('#canvas');
      if (!state.workflow.nodes.length) {
        state.panX = 0;
        state.panY = 0;
        setZoom(1.0);
        return;
      }
      const maxX = Math.max(...state.workflow.nodes.map(n => (n.x || 0) + 240));
      const maxY = Math.max(...state.workflow.nodes.map(n => (n.y || 0) + 160));
      state.panX = 20;
      state.panY = 20;
      const fitZoom = Math.min(1.0, Math.max(0.4, Math.min(
        (canvas.clientWidth - 40) / maxX,
        (canvas.clientHeight - 40) / maxY
      )));
      setZoom(fitZoom);
    });

    // Preview actions
    $('#snapshotBtn')?.addEventListener('click', captureSnapshot);
    $('#fullscreenBtn')?.addEventListener('click', toggleFullscreenPreview);
    $('#closePreviewModal')?.addEventListener('click', () => $('#previewModal')?.close());

    // Logs actions
    $('#clearLogs')?.addEventListener('click', () => {
      const allLogs = state.status?.logs || [];
      const allEvents = state.status?.events || [];
      const maxLogSeq = Math.max(0, ...allLogs.map(l => l.seq || 0));
      const maxEventSeq = Math.max(0, ...allEvents.map(e => (e.time || 0) * 1000));
      state.clearedSeq = Math.max(maxLogSeq, maxEventSeq);
      state._forceLogRender = true;
      renderLogs([], []);
      toast('Console logs cleared');
    });

    $('#copyLogsBtn')?.addEventListener('click', copyLogs);

    $('#filterLogsBtn')?.addEventListener('click', () => {
      if (state.logFilter === 'all') {
        state.logFilter = 'events';
        $('#filterLogsBtn').textContent = 'Events';
        $('#filterLogsBtn').classList.add('active-filter');
      } else if (state.logFilter === 'events') {
        state.logFilter = 'errors';
        $('#filterLogsBtn').textContent = 'Errors';
        $('#filterLogsBtn').classList.add('active-filter');
      } else {
        state.logFilter = 'all';
        $('#filterLogsBtn').textContent = 'All';
        $('#filterLogsBtn').classList.remove('active-filter');
      }
      state._forceLogRender = true;
      renderLogs(state.status?.logs || [], state.status?.events || []);
    });

    $('#logSearchInput')?.addEventListener('input', e => {
      state.logSearchQuery = e.target.value.trim();
      state._forceLogRender = true;
      renderLogs(state.status?.logs || [], state.status?.events || []);
    });

    // Keyboard shortcuts
    document.addEventListener('keydown', e => {
      if (document.querySelector('.zone-preview-editor') && ['Delete', 'Backspace', 'Escape'].includes(e.key)) return;
      if ((e.key === 'Delete' || e.key === 'Backspace') && !['INPUT', 'TEXTAREA', 'SELECT'].includes(document.activeElement.tagName)) {
        if (state.selectedEdge !== null && state.selectedEdge !== undefined && state.workflow.edges[state.selectedEdge]) {
          const edge = state.workflow.edges[state.selectedEdge];
          const a = nodeFor(edge[0]);
          const b = nodeFor(edge[1]);
          state.workflow.edges.splice(state.selectedEdge, 1);
          state.selectedEdge = null;
          markDirty();
          renderCanvas();
          toast(`Koneksi ${a?.title || edge[0]} → ${b?.title || edge[1]} berhasil dihapus`);
          return;
        }
        deleteSelectedNode();
      }
      if (e.key === 'Escape') {
        hideEdgeContextMenu();
        if (state.reconnectingEdge) {
          state.reconnectingEdge = null;
          $('#canvasHint').textContent = 'Select a node to inspect · drag to arrange · click port to connect';
          renderCanvas();
        }
        if (state.connecting) {
          state.connecting = null;
          $('#canvasHint').textContent = 'Select a node to inspect · drag to arrange · click port to connect';
          renderCanvas();
        }
        $('#templatesModal')?.close();
        $('#previewModal')?.close();
      }
    });

    window.addEventListener('beforeunload', e => {
      if (state.dirty) {
        e.preventDefault();
        e.returnValue = '';
      }
    });

  // ==========================================
  // FACE REGISTRY (UNIFACE GALLERY) LOGIC
  // ==========================================
  let selectedEnrollPhotoBase64 = null;

  async function renderFaceRegistry() {
    const cardsGrid = $('#faceCardsGrid');
    const statsBadge = $('#faceStatsBadge');
    if (!cardsGrid) return;

    try {
      const res = await fetch('/api/faces');
      if (!res.ok) throw new Error('HTTP ' + res.status);
      const data = await res.json();
      state.registeredFaces = data.faces || [];
    } catch (err) {
      console.warn('Could not fetch face registry:', err);
      state.registeredFaces = state.registeredFaces || [];
    }

    const faces = state.registeredFaces;
    if (statsBadge) {
      statsBadge.textContent = `${faces.length} Wajah Terdaftar`;
    }

    filterFaceGallery($('#faceSearchInput')?.value || '');
  }

  function filterFaceGallery(query) {
    const cardsGrid = $('#faceCardsGrid');
    if (!cardsGrid) return;
    cardsGrid.replaceChildren();

    const q = (query || '').trim().toLowerCase();
    const allFaces = state.registeredFaces || [];
    const filtered = q ? allFaces.filter(f => (f.name || '').toLowerCase().includes(q) || (f.role || '').toLowerCase().includes(q) || (f.notes || '').toLowerCase().includes(q)) : allFaces;

    if (!filtered.length) {
      const emptyDiv = document.createElement('div');
      emptyDiv.className = 'face-empty-state';
      emptyDiv.style.cssText = 'grid-column: 1 / -1; text-align: center; padding: 48px 16px; color: #64748b; background: #fff; border: 1px dashed #cbd5e1; border-radius: 12px;';
      emptyDiv.innerHTML = `
        <div style="font-size: 36px; margin-bottom: 8px;">👤</div>
        <strong style="font-size: 14px; color: #334155;">${q ? 'Tidak ada profil wajah yang sesuai pencarian' : 'Belum ada wajah terdaftar'}</strong>
        <p style="font-size: 12px; margin-top: 4px; color: #94a3b8;">${q ? 'Coba gunakan kata kunci pencarian yang lain.' : 'Klik tombol <b>"+ Daftarkan Wajah Baru"</b> untuk menambahkan profil wajah pertama Anda.'}</p>
      `;
      cardsGrid.append(emptyDiv);
      return;
    }

    filtered.forEach(face => {
      const card = document.createElement('div');
      card.className = 'face-card';
      card.style.cssText = 'background: #ffffff; border: 1px solid #e2e8f0; border-radius: 10px; padding: 14px; box-shadow: 0 1px 3px rgba(0,0,0,0.05); display: flex; flex-direction: column; gap: 10px; transition: transform .15s, box-shadow .15s;';

      const avatarSrc = face.avatar_url || (face.image_path ? ('/' + face.image_path) : '');
      const avatarHtml = avatarSrc
        ? `<img src="${avatarSrc}" alt="${face.name}" style="width: 60px; height: 60px; border-radius: 50%; object-fit: cover; border: 2px solid #10b981; background: #f1f5f9;">`
        : `<div style="width: 60px; height: 60px; border-radius: 50%; background: #e0f2fe; color: #0284c7; display: flex; align-items: center; justify-content: center; font-size: 24px; font-weight: 700; border: 2px solid #bae6fd;">${(face.name || 'W').charAt(0).toUpperCase()}</div>`;

      card.innerHTML = `
        <div style="display: flex; align-items: center; gap: 12px;">
          ${avatarHtml}
          <div style="flex: 1; min-width: 0;">
            <div style="display: flex; align-items: center; gap: 6px;">
              <h4 style="margin: 0; font-size: 14px; font-weight: 700; color: #1e293b; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">${face.name}</h4>
              <span style="font-size: 10px; background: #ecfdf5; color: #047857; border: 1px solid #a7f3d0; border-radius: 4px; padding: 1px 6px; font-weight: 600;">ArcFace</span>
            </div>
            <div style="font-size: 11.5px; color: #64748b; margin-top: 2px;">
              <span style="font-weight: 600; color: #0284c7;">${face.role || 'Karyawan'}</span>
            </div>
            <div style="font-size: 10px; color: #94a3b8; margin-top: 2px;">
              ID: ${face.id} · Terdaftar: ${face.created_at ? new Date(face.created_at).toLocaleDateString() : '-'}
            </div>
          </div>
        </div>
        ${face.notes ? `<div style="font-size: 11px; color: #475569; background: #f8fafc; padding: 6px 8px; border-radius: 6px; border-left: 3px solid #3b82f6;">${face.notes}</div>` : ''}
        <div style="margin-top: auto; padding-top: 8px; border-top: 1px solid #f1f5f9; display: flex; justify-content: flex-end; gap: 6px;">
          <button type="button" class="button ghost delete-face-btn" style="height: 26px; padding: 0 8px; font-size: 11px; color: #ef4444;" title="Hapus profil wajah ini">
            <svg class="icon-svg icon-sm" viewBox="0 0 24 24" style="width: 13px; height: 13px;"><path d="M3 6h18"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>
            <span>Hapus</span>
          </button>
        </div>
      `;

      card.querySelector('.delete-face-btn').onclick = async () => {
        if (!confirm(`Hapus profil wajah "${face.name}" dari sistem?`)) return;
        try {
          const delRes = await fetch(`/api/faces/${face.id}`, { method: 'DELETE' });
          if (!delRes.ok) throw new Error('Gagal menghapus');
          toast(`Profil wajah "${face.name}" berhasil dihapus.`);
          await renderFaceRegistry();
        } catch (e) {
          toast('Error menghapus profil: ' + e.message, true);
        }
      };

      cardsGrid.append(card);
    });
  }

  let faceWebcamStream = null;
  let faceCameraFacing = 'user';
  let facePhotoMode = 'upload';

  function switchFacePhotoMode(mode) {
    facePhotoMode = mode;
    const tabUpload = $('#faceTabUpload');
    const tabCamera = $('#faceTabCamera');
    const dropArea = $('#facePhotoDropArea');
    const cameraArea = $('#faceCameraArea');
    const previewContainer = $('#facePhotoPreviewContainer');

    if (tabUpload) {
      tabUpload.style.background = mode === 'upload' ? '#fff' : 'transparent';
      tabUpload.style.color = mode === 'upload' ? '#0f172a' : '#64748b';
      tabUpload.style.boxShadow = mode === 'upload' ? '0 1px 2px rgba(0,0,0,0.06)' : 'none';
    }
    if (tabCamera) {
      tabCamera.style.background = mode === 'camera' ? '#fff' : 'transparent';
      tabCamera.style.color = mode === 'camera' ? '#0f172a' : '#64748b';
      tabCamera.style.boxShadow = mode === 'camera' ? '0 1px 2px rgba(0,0,0,0.06)' : 'none';
    }

    if (selectedEnrollPhotoBase64) {
      if (previewContainer) previewContainer.style.display = 'block';
      if (dropArea) dropArea.style.display = 'none';
      if (cameraArea) cameraArea.style.display = 'none';
      stopFaceWebcam();
      return;
    }

    if (mode === 'camera') {
      if (dropArea) dropArea.style.display = 'none';
      if (cameraArea) cameraArea.style.display = 'block';
      startFaceWebcam();
    } else {
      stopFaceWebcam();
      if (cameraArea) cameraArea.style.display = 'none';
      if (dropArea) dropArea.style.display = 'block';
    }
  }

  async function startFaceWebcam() {
    const video = $('#faceWebcamVideo');
    const statusMsg = $('#cameraStatusMsg');
    if (!video) return;

    stopFaceWebcam();
    if (statusMsg) {
      statusMsg.textContent = 'Menghubungkan ke kamera...';
      statusMsg.style.color = '#94a3b8';
    }

    try {
      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        throw new Error('Browser tidak mendukung akses kamera (getUserMedia).');
      }

      const constraints = {
        video: {
          facingMode: faceCameraFacing,
          width: { ideal: 640 },
          height: { ideal: 480 }
        },
        audio: false
      };

      faceWebcamStream = await navigator.mediaDevices.getUserMedia(constraints);
      video.srcObject = faceWebcamStream;
      await video.play();

      if (statusMsg) {
        statusMsg.textContent = 'Kamera aktif · Arahkan wajah ke oval panduan';
        statusMsg.style.color = '#10b981';
      }
    } catch (err) {
      console.warn('Webcam capture error:', err);
      if (statusMsg) {
        statusMsg.textContent = 'Gagal mengakses kamera: ' + (err.message || 'Izin ditolak');
        statusMsg.style.color = '#ef4444';
      }
      toast('Kamera tidak dapat diakses. Gunakan tab Unggah Berkas.', true);
    }
  }

  function stopFaceWebcam() {
    if (faceWebcamStream) {
      try {
        faceWebcamStream.getTracks().forEach(t => t.stop());
      } catch (e) {}
      faceWebcamStream = null;
    }
    const video = $('#faceWebcamVideo');
    if (video) video.srcObject = null;
  }

  function captureFaceWebcamSnapshot() {
    const video = $('#faceWebcamVideo');
    const canvas = $('#faceWebcamCanvas');
    const previewImg = $('#facePhotoPreviewImg');
    const previewContainer = $('#facePhotoPreviewContainer');
    const cameraArea = $('#faceCameraArea');

    if (!video || !canvas) return;

    const vw = video.videoWidth || 640;
    const vh = video.videoHeight || 480;
    canvas.width = vw;
    canvas.height = vh;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Flip horizontal for natural selfie perspective if user-facing
    ctx.save();
    if (faceCameraFacing === 'user') {
      ctx.translate(vw, 0);
      ctx.scale(-1, 1);
    }
    ctx.drawImage(video, 0, 0, vw, vh);
    ctx.restore();

    selectedEnrollPhotoBase64 = canvas.toDataURL('image/jpeg', 0.95);
    if (previewImg) previewImg.src = selectedEnrollPhotoBase64;

    stopFaceWebcam();
    if (cameraArea) cameraArea.style.display = 'none';
    if (previewContainer) previewContainer.style.display = 'block';
    toast('Foto berhasil diambil dari kamera!');
  }

  function resetEnrollPhoto() {
    selectedEnrollPhotoBase64 = null;
    const previewContainer = $('#facePhotoPreviewContainer');
    const previewImg = $('#facePhotoPreviewImg');
    if (previewContainer) previewContainer.style.display = 'none';
    if (previewImg) previewImg.src = '';

    switchFacePhotoMode(facePhotoMode);
  }

  function openEnrollFaceModal() {
    selectedEnrollPhotoBase64 = null;
    const modal = $('#enrollFaceModal');
    const form = $('#enrollFaceForm');
    if (form) form.reset();
    if ($('#enrollRoleInput')) $('#enrollRoleInput').value = 'Karyawan';

    if ($('#facePhotoPlaceholder')) $('#facePhotoPlaceholder').style.display = 'block';
    if ($('#facePhotoPreviewContainer')) $('#facePhotoPreviewContainer').style.display = 'none';
    if ($('#facePhotoPreviewImg')) $('#facePhotoPreviewImg').src = '';

    switchFacePhotoMode('upload');

    if (modal) {
      modal.removeAttribute('hidden');
      modal.style.display = 'flex';
    }
  }

  function closeEnrollFaceModal() {
    stopFaceWebcam();
    const modal = $('#enrollFaceModal');
    if (modal) {
      modal.setAttribute('hidden', '');
      modal.style.display = 'none';
    }
  }

  async function handleEnrollFaceSubmit() {
    const name = ($('#enrollNameInput')?.value || '').trim();
    const role = ($('#enrollRoleInput')?.value || '').trim() || 'Karyawan';
    const notes = ($('#enrollNotesInput')?.value || '').trim();

    if (!name) {
      toast('Nama lengkap wajib diisi!', true);
      $('#enrollNameInput')?.focus();
      return;
    }

    if (!selectedEnrollPhotoBase64) {
      toast('Silakan pilih foto wajah terlebih dahulu!', true);
      return;
    }

    const submitBtn = $('#submitEnrollBtn');
    const origText = submitBtn ? submitBtn.textContent : '';
    if (submitBtn) {
      submitBtn.disabled = true;
      submitBtn.textContent = 'Mengekstrak Fitur ArcFace...';
    }

    try {
      const res = await fetch('/api/faces/enroll', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: name,
          role: role,
          notes: notes,
          image_base64: selectedEnrollPhotoBase64
        })
      });

      const result = await res.json();
      if (!res.ok) {
        throw new Error(result.detail || 'Gagal mendaftarkan wajah');
      }

      toast(`✅ Wajah "${name}" berhasil didaftarkan ke Database!`);
      closeEnrollFaceModal();
      await renderFaceRegistry();
    } catch (err) {
      toast('Gagal: ' + err.message, true);
    } finally {
      if (submitBtn) {
        submitBtn.disabled = false;
        submitBtn.textContent = origText;
      }
    }
  }

  function setupFacePhotoUploadHandlers() {
    const dropArea = $('#facePhotoDropArea');
    const fileInput = $('#faceFileInput');
    const placeholder = $('#facePhotoPlaceholder');
    const previewContainer = $('#facePhotoPreviewContainer');
    const previewImg = $('#facePhotoPreviewImg');
    const changeBtn = $('#changePhotoBtn');

    // Tab buttons
    $('#faceTabUpload')?.addEventListener('click', () => switchFacePhotoMode('upload'));
    $('#faceTabCamera')?.addEventListener('click', () => switchFacePhotoMode('camera'));

    // Camera action buttons
    $('#captureWebcamBtn')?.addEventListener('click', captureFaceWebcamSnapshot);
    $('#switchCameraFacingBtn')?.addEventListener('click', () => {
      faceCameraFacing = faceCameraFacing === 'user' ? 'environment' : 'user';
      startFaceWebcam();
    });
    if (changeBtn) changeBtn.onclick = resetEnrollPhoto;

    if (!dropArea || !fileInput) return;

    dropArea.onclick = (e) => {
      if (e.target !== changeBtn) fileInput.click();
    };

    fileInput.onchange = (e) => {
      const file = e.target.files?.[0];
      if (!file) return;
      handleSelectedPhotoFile(file);
    };

    dropArea.ondragover = (e) => {
      e.preventDefault();
      dropArea.style.borderColor = '#059669';
      dropArea.style.background = '#ecfdf5';
    };

    dropArea.ondragleave = (e) => {
      e.preventDefault();
      dropArea.style.borderColor = '#cbd5e1';
      dropArea.style.background = '#f8fafc';
    };

    dropArea.ondrop = (e) => {
      e.preventDefault();
      dropArea.style.borderColor = '#cbd5e1';
      dropArea.style.background = '#f8fafc';
      const file = e.dataTransfer?.files?.[0];
      if (file) handleSelectedPhotoFile(file);
    };

    function handleSelectedPhotoFile(file) {
      if (!file.type.startsWith('image/')) {
        toast('Pilih file gambar (JPG, PNG, WebP)!', true);
        return;
      }
      const reader = new FileReader();
      reader.onload = (ev) => {
        selectedEnrollPhotoBase64 = ev.target.result;
        if (previewImg) previewImg.src = selectedEnrollPhotoBase64;
        if (dropArea) dropArea.style.display = 'none';
        if (previewContainer) previewContainer.style.display = 'block';
      };
      reader.readAsDataURL(file);
    }
  }

    // Hub and Left Rail Navigation
    $('#brandLogoHome')?.addEventListener('click', () => switchMainView('projectsHub'));
    initProjectSwitcher();
    initHubEvents();
    $('#hubNewProjectBtn')?.addEventListener('click', newProject);
    $('#hubImportBtn')?.addEventListener('click', () => $('#importInput')?.click());
    $('#hubViewAllTemplatesBtn')?.addEventListener('click', () => {
      $('#templatesModal')?.showModal();
    });
    $('#hubViewAllProjectsBtn')?.addEventListener('click', () => {
      const prjSection = $('#hubRecentProjectsGrid');
      if (prjSection) prjSection.scrollIntoView({ behavior: 'smooth' });
    });

    // Left Rail Tabs
    $('#railTabWorkflow')?.addEventListener('click', () => switchProjectRailTab('workflow'));
    $('#railTabModels')?.addEventListener('click', () => switchProjectRailTab('models'));
    $('#railTabFaces')?.addEventListener('click', () => switchProjectRailTab('faces'));
    $('#faceRegistrySyncBtn')?.addEventListener('click', () => renderFaceRegistry());
    $('#faceEnrollBtn')?.addEventListener('click', () => openEnrollFaceModal());
    $('#closeEnrollModalBtn')?.addEventListener('click', () => closeEnrollFaceModal());
    $('#cancelEnrollBtn')?.addEventListener('click', () => closeEnrollFaceModal());
    $('#submitEnrollBtn')?.addEventListener('click', () => handleEnrollFaceSubmit());
    $('#faceSearchInput')?.addEventListener('input', (e) => filterFaceGallery(e.target.value));
    setupFacePhotoUploadHandlers();

    // Models Manager
    $('#modelsAddBtn')?.addEventListener('click', () => {
      const modal = $('#addModelModal');
      if (modal) modal.showModal();
    });
    $('#closeAddModelModal')?.addEventListener('click', () => $('#addModelModal')?.close());
    $('#cancelAddModelBtn')?.addEventListener('click', () => $('#addModelModal')?.close());

    const dropZone = $('#modelDropZone');
    const modelFileInput = $('#modalModelFileInput');
    const selectedLabel = $('#selectedModelFilename');
    const submitAddBtn = $('#submitAddModelBtn');

    if (dropZone && modelFileInput) {
      dropZone.addEventListener('click', () => modelFileInput.click());
      dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.classList.add('dragover');
      });
      dropZone.addEventListener('dragleave', () => dropZone.classList.remove('dragover'));
      dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.classList.remove('dragover');
        if (e.dataTransfer.files && e.dataTransfer.files[0]) {
          modelFileInput.files = e.dataTransfer.files;
          updateSelectedFile();
        }
      });
      modelFileInput.addEventListener('change', () => updateSelectedFile());

      function updateSelectedFile() {
        if (modelFileInput.files && modelFileInput.files[0]) {
          const f = modelFileInput.files[0];
          if (selectedLabel) {
            selectedLabel.textContent = `Selected: ${f.name} (${(f.size / (1024 * 1024)).toFixed(2)} MB)`;
            selectedLabel.hidden = false;
          }
          if (submitAddBtn) submitAddBtn.disabled = false;
        } else {
          if (selectedLabel) selectedLabel.hidden = true;
          if (submitAddBtn) submitAddBtn.disabled = true;
        }
      }

      $('#addModelForm')?.addEventListener('submit', async (e) => {
        e.preventDefault();
        if (!modelFileInput.files || !modelFileInput.files[0]) return;
        const file = modelFileInput.files[0];
        const formData = new FormData();
        formData.append('file', file);
        if (submitAddBtn) {
          submitAddBtn.disabled = true;
          submitAddBtn.textContent = 'Uploading...';
        }
        try {
          const res = await api('/api/models/upload', {
            method: 'POST',
            body: formData
          });
          toast(`Model "${res.name}" registered successfully!`);
          $('#addModelModal')?.close();
          modelFileInput.value = '';
          if (selectedLabel) selectedLabel.hidden = true;
          await refreshModels();
          renderModelsManager();
          renderInspector();
        } catch (err) {
          toast('Upload failed: ' + err.message, true);
        } finally {
          if (submitAddBtn) {
            submitAddBtn.disabled = false;
            submitAddBtn.textContent = 'Upload and Register';
          }
        }
      });
    }

    // Quantize & Optimize Model Manager
    let _latestQuantizeResult = null;

    $('#modelsQuantizeBtn')?.addEventListener('click', () => {
      openQuantizeModal();
    });
    $('#closeQuantizeModelModal')?.addEventListener('click', () => $('#quantizeModelModal')?.close());
    $('#cancelQuantizeBtn')?.addEventListener('click', () => $('#quantizeModelModal')?.close());

    window.openQuantizeModal = function openQuantizeModal() {
      const modal = $('#quantizeModelModal');
      const select = $('#quantizeSourceSelect');
      if (!modal || !select) return;

      select.innerHTML = '<option value="">-- Pilih model dari Model Registry --</option>';
      const eligibleModels = (state.models || []).filter(m => {
        const ext = (m.path || m.name || '').toLowerCase();
        return ext.endsWith('.pt') || ext.endsWith('.pth') || ext.endsWith('.onnx') || ext.endsWith('.keras') || ext.endsWith('.h5');
      });

      const listToRender = eligibleModels.length > 0 ? eligibleModels : (state.models || []);
      listToRender.forEach(m => {
        const opt = document.createElement('option');
        opt.value = m.name || m.path;
        opt.textContent = `${m.name} (${m.engine || m.format} · ${m.sizeFormatted || ''})`;
        select.append(opt);
      });

      const loading = $('#quantizeLoadingState');
      const resultCard = $('#quantizeResultCard');
      const startBtn = $('#startQuantizeBtn');
      if (loading) loading.style.display = 'none';
      if (resultCard) resultCard.style.display = 'none';
      if (startBtn) startBtn.disabled = false;
      modal.showModal();
    }

    $('#quantizeModelForm')?.addEventListener('submit', async (e) => {
      e.preventDefault();
      const modelPath = $('#quantizeSourceSelect')?.value;
      if (!modelPath) {
        toast('Pilih model sumber terlebih dahulu.', true);
        return;
      }
      const targetFormatRadio = document.querySelector('input[name="quantizeTargetFormat"]:checked');
      const targetFormat = targetFormatRadio ? targetFormatRadio.value : 'tflite_int8';
      const imageSize = parseInt($('#quantizeImageSize')?.value || '640', 10);

      const loading = $('#quantizeLoadingState');
      const resultCard = $('#quantizeResultCard');
      const startBtn = $('#startQuantizeBtn');

      if (loading) loading.style.display = 'block';
      if (resultCard) resultCard.style.display = 'none';
      if (startBtn) startBtn.disabled = true;

      try {
        const res = await api('/api/models/quantize', {
          method: 'POST',
          body: JSON.stringify({ modelPath, targetFormat, imageSize })
        });
        _latestQuantizeResult = res;

        if (loading) loading.style.display = 'none';
        if (resultCard) {
          resultCard.style.display = 'block';
          $('#quantizeSavedBadge').textContent = `-${res.savedPercent}% Ukuran`;
          $('#quantizeResultDetails').innerHTML = `
            <div><strong>Model Hasil:</strong> ${res.targetName}</div>
            <div><strong>Format & Presisi:</strong> ${res.targetFormat.toUpperCase()}</div>
            <div><strong>Ukuran:</strong> ${res.originalSizeFormatted} ➔ <span style="color:#059669; font-weight:700;">${res.quantizedSizeFormatted}</span> (${res.compressionRatio} lebih ringan)</div>
          `;
        }

        toast(`Model ${res.targetName} berhasil dikuantisasi! Hemat ${res.savedPercent}%`);
        await refreshModels();
        renderModelsManager();
        renderInspector();
      } catch (err) {
        if (loading) loading.style.display = 'none';
        toast('Gagal kuantisasi: ' + err.message, true);
      } finally {
        if (startBtn) startBtn.disabled = false;
      }
    });

    $('#applyQuantizedModelBtn')?.addEventListener('click', () => {
      if (!_latestQuantizeResult) return;
      const targetPath = _latestQuantizeResult.targetName || _latestQuantizeResult.targetPath;
      const targetEngine = _latestQuantizeResult.engine || 'tflite';

      let targetNode = null;
      if (state.selected) {
        const n = nodeFor(state.selected);
        if (n && ['detector', 'segmenter', 'classifier'].includes(n.type)) targetNode = n;
      }
      if (!targetNode) {
        targetNode = (state.workflow.nodes || []).find(n => ['detector', 'segmenter', 'classifier'].includes(n.type));
      }

      if (targetNode) {
        targetNode.config.engine = targetEngine;
        targetNode.config.modelPath = targetPath;
        targetNode.config.customModelPath = targetPath;
        markDirty();
        renderInspector();
        toast(`Model ${targetPath} diterapkan ke node ${targetNode.title || targetNode.id}!`);
        $('#quantizeModelModal')?.close();
      } else {
        toast(`Model ${targetPath} disimpan di registry. Tambahkan node Deteksi untuk menggunakannya.`);
      }
    });

    $('#downloadQuantizedModelBtn')?.addEventListener('click', () => {
      if (!_latestQuantizeResult) return;
      const path = _latestQuantizeResult.targetPath || _latestQuantizeResult.targetName;
      window.open(`/api/models/download?path=${encodeURIComponent(path)}`, '_blank');
    });

    setupCanvasPan();
  }

  function initSystemSettings() {
    const modal = $('#systemSettingsModal');
    if (!modal) return;

    // Load initial settings
    const device = localStorage.getItem('visonode_setting_device') || 'auto';
    const maxFps = localStorage.getItem('visonode_setting_max_fps') || '30';
    const autoSave = localStorage.getItem('visonode_setting_auto_save') !== 'false';
    const vlmProvider = localStorage.getItem('visonode_setting_vlm_provider') || '9router';
    const apiKey = localStorage.getItem('visonode_setting_api_key') || '';
    const baseUrl = localStorage.getItem('visonode_setting_base_url') || '';
    const aiModel = localStorage.getItem('visonode_setting_ai_model') || 'cx/gpt-5.6-luna';
    const ollamaUrl = localStorage.getItem('visonode_setting_ollama_url') || 'http://127.0.0.1:11434';
    const erpWebhook = localStorage.getItem('visonode_setting_erp_webhook') || '';

    if ($('#settingDevice')) $('#settingDevice').value = device;
    if ($('#settingMaxFps')) $('#settingMaxFps').value = maxFps;
    if ($('#settingAutoSave')) $('#settingAutoSave').checked = autoSave;
    if ($('#settingVlmProvider')) $('#settingVlmProvider').value = vlmProvider;
    if ($('#settingApiKey')) $('#settingApiKey').value = apiKey;
    if ($('#settingBaseUrl')) $('#settingBaseUrl').value = baseUrl;
    if ($('#settingAiModel')) $('#settingAiModel').value = aiModel;
    if ($('#settingOllamaUrl')) $('#settingOllamaUrl').value = ollamaUrl;
    if ($('#settingErpWebhook')) $('#settingErpWebhook').value = erpWebhook;

    // Wire up all settings buttons
    document.querySelectorAll('#hubSettingsBtn, .header-settings-btn').forEach(btn => {
      btn.onclick = () => modal.showModal();
    });

    $('#closeSystemSettingsModal')?.addEventListener('click', () => modal.close());
    $('#cancelSystemSettingsBtn')?.addEventListener('click', () => modal.close());

    // Settings tabs
    modal.querySelectorAll('.settings-nav-tab').forEach(tabBtn => {
      tabBtn.onclick = () => {
        modal.querySelectorAll('.settings-nav-tab').forEach(t => t.classList.remove('active'));
        tabBtn.classList.add('active');
        const tab = tabBtn.dataset.tab;
        if ($('#settingsPanelGeneral')) $('#settingsPanelGeneral').hidden = (tab !== 'general');
        if ($('#settingsPanelVlm')) $('#settingsPanelVlm').hidden = (tab !== 'vlm');
        if ($('#settingsPanelStorage')) $('#settingsPanelStorage').hidden = (tab !== 'storage');
      };
    });

    // Save button
    $('#saveSystemSettingsBtn')?.addEventListener('click', () => {
      localStorage.setItem('visonode_setting_device', $('#settingDevice')?.value || 'auto');
      localStorage.setItem('visonode_setting_max_fps', $('#settingMaxFps')?.value || '30');
      localStorage.setItem('visonode_setting_auto_save', $('#settingAutoSave')?.checked ? 'true' : 'false');
      localStorage.setItem('visonode_setting_vlm_provider', $('#settingVlmProvider')?.value || '9router');
      localStorage.setItem('visonode_setting_api_key', $('#settingApiKey')?.value || '');
      localStorage.setItem('visonode_setting_base_url', $('#settingBaseUrl')?.value || '');
      localStorage.setItem('visonode_setting_ai_model', $('#settingAiModel')?.value?.trim() || 'cx/gpt-5.6-luna');
      localStorage.setItem('visonode_setting_ollama_url', $('#settingOllamaUrl')?.value || 'http://127.0.0.1:11434');
      localStorage.setItem('visonode_setting_erp_webhook', $('#settingErpWebhook')?.value || '');

      const copilotBadge = $('#copilotActiveModel');
      if (copilotBadge) copilotBadge.textContent = localStorage.getItem('visonode_setting_ai_model') || 'cx/gpt-5.6-luna';

      modal.close();
      toast('Studio & Pipeline Settings saved successfully');
    });

    // Project rename form
    $('#closeProjectRenameModal')?.addEventListener('click', closeProjectRenameModal);
    $('#cancelProjectRenameBtn')?.addEventListener('click', closeProjectRenameModal);
    $('#projectRenameForm')?.addEventListener('submit', async (e) => {
      e.preventDefault();
      const pId = $('#renameProjectId')?.value;
      const newName = $('#renameProjectInput')?.value?.trim();
      if (!pId || !newName) return;
      try {
        await api(`/api/projects/${encodeURIComponent(pId)}`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ name: newName })
        });
        closeProjectRenameModal();
        if (state.project?.id === pId) {
          state.project.name = newName;
          $('#projectName').textContent = newName;
        }
        await loadProjects();
        toast('Project renamed successfully');
      } catch (err) {
        toast(err.message, true);
      }
    });

    // Project delete modal
    $('#closeProjectDeleteModal')?.addEventListener('click', closeProjectDeleteModal);
    $('#cancelProjectDeleteBtn')?.addEventListener('click', closeProjectDeleteModal);
    $('#confirmProjectDeleteBtn')?.addEventListener('click', async () => {
      const pId = $('#deleteProjectIdTarget')?.value;
      if (!pId) return;
      try {
        await api(`/api/projects/${encodeURIComponent(pId)}`, { method: 'DELETE' });
        closeProjectDeleteModal();
        if (state.project?.id === pId) {
          state.project = null;
          state.workflow = { nodes: [], edges: [] };
        }
        await loadProjects();
        toast('Project deleted');
      } catch (err) {
        toast(err.message, true);
      }
    });
  }

  // --- AI Studio Copilot Engine ---
  function initAiStudioCopilot() {
    const toggleBtn = $('#toggleAiCopilotBtn');
    const drawer = $('#studioAiCopilotDrawer');
    if (!toggleBtn || !drawer) return;

    const closeBtn = $('#copilotCloseDrawerBtn');
    const clearBtn = $('#copilotClearChatBtn');
    const chatForm = $('#copilotChatForm');
    const promptInput = $('#copilotPromptInput');
    const sendBtn = $('#copilotSendBtn');
    const messagesList = $('#copilotMessagesList');
    const chipsContainer = $('#copilotQuickChips');
    const modelBadge = $('#copilotActiveModel');

    if (modelBadge) {
      modelBadge.textContent = localStorage.getItem('visonode_setting_ai_model') || 'cx/gpt-5.6-luna';
    }

    let chatHistory = [];

    function toggleDrawer(open) {
      const willOpen = (open !== undefined) ? open : drawer.hidden;
      drawer.hidden = !willOpen;
      toggleBtn.classList.toggle('active', willOpen);
      if (willOpen) {
        promptInput?.focus();
      }
    }

    toggleBtn.addEventListener('click', () => toggleDrawer());
    closeBtn?.addEventListener('click', () => toggleDrawer(false));

    clearBtn?.addEventListener('click', () => {
      chatHistory = [];
      messagesList.innerHTML = `
        <div class="copilot-msg assistant">
          <div class="msg-bubble">
            Percakapan telah dibersihkan. Tuliskan instruksi alur baru atau pilih saran di bawah ini.
          </div>
        </div>
      `;
      toast('Riwayat Copilot dibersihkan.');
    });

    function appendMessage(role, htmlContent) {
      const msgDiv = document.createElement('div');
      msgDiv.className = `copilot-msg ${role}`;
      msgDiv.innerHTML = `<div class="msg-bubble">${htmlContent}</div>`;
      messagesList.appendChild(msgDiv);
      messagesList.scrollTop = messagesList.scrollHeight;
      return msgDiv;
    }

    async function handleSendPrompt(userText) {
      const text = (userText || promptInput?.value || '').trim();
      if (!text) return;

      appendMessage('user', escapeHtml(text));
      chatHistory.push({ role: 'user', content: text });
      if (promptInput) promptInput.value = '';

      if (sendBtn) sendBtn.disabled = true;
      const thinkingMsg = appendMessage('assistant', '<div style="display:flex;align-items:center;gap:6px"><em>Studio Copilot sedang merancang alur...</em></div>');

      try {
        const aiConfig = {
          provider: localStorage.getItem('visonode_setting_vlm_provider') || '9router',
          apiKey: localStorage.getItem('visonode_setting_api_key') || '',
          baseUrl: localStorage.getItem('visonode_setting_base_url') || '',
          model: localStorage.getItem('visonode_setting_ai_model') || 'cx/gpt-5.6-luna',
          ollamaUrl: localStorage.getItem('visonode_setting_ollama_url') || 'http://127.0.0.1:11434'
        };

        const currentWf = {
          nodes: (state.workflow?.nodes || []).map(n => ({
            id: n.id,
            type: n.type,
            title: n.title,
            x: n.x,
            y: n.y,
            config: n.config
          })),
          edges: (state.workflow?.edges || []).map(e => ({
            id: e.id,
            source: e.source,
            target: e.target
          }))
        };

        const historyPayload = chatHistory.slice(-8);
        chatHistory.push({ role: 'user', content: text });

        const res = await api('/api/ai/generate-workflow', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            userInstruction: text,
            currentWorkflow: currentWf,
            history: historyPayload,
            aiConfig
          })
        });

        thinkingMsg.remove();

        const explanation = res.explanation || 'Alur alur kerja telah dirancang.';
        const modifications = Array.isArray(res.modifications) ? res.modifications : [];
        const isUpdate = res.action === 'update';

        // Keep multi-turn assistant context with modification details
        let assistantSummary = explanation;
        if (modifications.length > 0) {
          assistantSummary += '\nPerubahan Parameter:\n' + modifications.map(m => '- ' + m).join('\n');
        }
        chatHistory.push({ role: 'assistant', content: assistantSummary });

        let modificationsHtml = '';
        if (modifications.length > 0) {
          modificationsHtml = `
            <div style="margin: 8px 0 6px 0; padding: 6px 10px; background: rgba(14, 165, 233, 0.08); border-left: 3px solid #0284c7; border-radius: 4px; font-size: 11px;">
              <strong style="color: #0369a1; display: block; margin-bottom: 4px;">Perubahan Parameter (Diff):</strong>
              <ul style="margin: 0; padding-left: 14px; color: #334155;">
                ${modifications.map(m => `<li>${escapeHtml(m)}</li>`).join('')}
              </ul>
            </div>
          `;
        }

        if (res.workflow && Array.isArray(res.workflow.nodes) && res.workflow.nodes.length > 0) {
          const actionTitle = isUpdate
            ? `Pembaruan Alur AI (${res.workflow.nodes.length} node terdampak)`
            : `Rancangan Alur AI (${res.workflow.nodes.length} node, ${res.workflow.edges ? res.workflow.edges.length : 0} edge)`;
          const buttonLabel = isUpdate
            ? `Terapkan Pembaruan ke Kanvas`
            : `Terapkan ke Kanvas (Apply to Canvas)`;

          const actionCardHtml = `
            <div>${explanation}</div>
            ${modificationsHtml}
            <div class="copilot-action-card">
              <div class="card-head">
                <span>${actionTitle}</span>
                <span style="font-size:10px;color:${isUpdate ? '#0284c7' : '#0d9488'};font-weight:700">${isUpdate ? 'REVISI SIAP' : 'SIAP DITERAPKAN'}</span>
              </div>
              <ul style="margin:4px 0 8px 16px;padding:0;font-size:11px;color:#475569">
                ${res.workflow.nodes.map(n => `<li><strong>${escapeHtml(n.title || n.type)}</strong> <code>(${n.type})</code></li>`).join('')}
              </ul>
              <button type="button" class="copilot-apply-btn">
                <svg class="icon-svg icon-sm" viewBox="0 0 24 24"><polyline points="20 6 9 17 4 12"/></svg>
                <span>${buttonLabel}</span>
              </button>
            </div>
          `;
          const bubble = appendMessage('assistant', actionCardHtml);
          const applyBtn = bubble.querySelector('.copilot-apply-btn');
          applyBtn?.addEventListener('click', () => {
            applyWorkflowToCanvas(res.workflow, res.action || 'create');
            applyBtn.disabled = true;
            applyBtn.innerHTML = '<svg class="icon-svg icon-sm" viewBox="0 0 24 24"><polyline points="20 6 9 17 4 12"/></svg><span>✓ Telah Diterapkan</span>';
            applyBtn.style.background = '#64748b';
          });
        } else {
          appendMessage('assistant', `<div>${explanation}</div>${modificationsHtml}`);
        }
      } catch (err) {
        thinkingMsg.remove();
        appendMessage('assistant', `<span style="color:#ef4444">Gagal memproses alur: ${escapeHtml(err.message)}</span>`);
      } finally {
        if (sendBtn) sendBtn.disabled = false;
      }
    }

    function applyWorkflowToCanvas(wf, action) {
      if (!wf || !wf.nodes) return;

      const actionType = action || 'create';
      const existingNodes = state.workflow?.nodes || [];

      if (actionType === 'update' && existingNodes.length > 0) {
        let updatedCount = 0;
        let addedCount = 0;
        const matchedExistingIds = new Set();

        wf.nodes.forEach(n => {
          let existing = existingNodes.find(en => en.id === n.id);
          if (!existing) {
            existing = existingNodes.find(en => en.type === n.type && !matchedExistingIds.has(en.id));
          }

          if (existing) {
            matchedExistingIds.add(existing.id);
            if (n.title) existing.title = n.title;
            if (n.config) {
              existing.config = Object.assign({}, existing.config || {}, n.config);
            }
            if (n.x !== undefined && Number.isFinite(Number(n.x))) existing.x = Number(n.x);
            if (n.y !== undefined && Number.isFinite(Number(n.y))) existing.y = Number(n.y);
            updatedCount++;
          } else {
            const nodeTypeSpec = (state.catalog && state.catalog[n.type]) || {};
            const baseConfig = JSON.parse(JSON.stringify(nodeTypeSpec.defaults || {}));
            existingNodes.push({
              id: n.id || ('node_' + Math.random().toString(36).substring(2, 9)),
              type: n.type,
              title: n.title || titleFor(n.type),
              x: Number(n.x) || 100,
              y: Number(n.y) || 200,
              enabled: n.enabled !== false,
              config: Object.assign(baseConfig, n.config || {})
            });
            addedCount++;
          }
        });

        if (Array.isArray(wf.edges) && wf.edges.length > 0) {
          state.workflow.edges = wf.edges.map((e, idx) => ({
            id: e.id || `edge_${idx}_${Date.now()}`,
            source: e.source,
            target: e.target
          }));
        }

        renderCanvas();
        markDirty();
        if (state.selected) {
          renderInspector();
        }
        toast(`✨ Pembaruan alur diterapkan: ${updatedCount} node diperbarui, ${addedCount} node baru.`);
        return;
      }

      const resolvedNodes = wf.nodes.map(n => {
        const nodeTypeSpec = (state.catalog && state.catalog[n.type]) || {};
        const baseConfig = JSON.parse(JSON.stringify(nodeTypeSpec.defaults || {}));
        return {
          id: n.id || ('node_' + Math.random().toString(36).substring(2, 9)),
          type: n.type,
          title: n.title || titleFor(n.type),
          x: Number(n.x) || 100,
          y: Number(n.y) || 200,
          enabled: n.enabled !== false,
          config: Object.assign(baseConfig, n.config || {})
        };
      });

      const resolvedEdges = (wf.edges || []).map((e, idx) => ({
        id: e.id || `edge_${idx}_${Date.now()}`,
        source: e.source,
        target: e.target
      }));

      state.workflow = {
        nodes: resolvedNodes,
        edges: resolvedEdges
      };

      renderCanvas();
      markDirty();
      if (state.selected) {
        renderInspector();
      }
      toast(`✨ ${resolvedNodes.length} node berhasil diterapkan ke kanvas!`);
    }

    chatForm?.addEventListener('submit', (e) => {
      e.preventDefault();
      handleSendPrompt();
    });

    promptInput?.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
        e.preventDefault();
        handleSendPrompt();
      }
    });

    chipsContainer?.querySelectorAll('.copilot-chip').forEach(chip => {
      chip.addEventListener('click', () => {
        const p = chip.dataset.prompt;
        if (p) handleSendPrompt(p);
      });
    });
  }

  // --- Notifications & Header Actions System ---
  let activeBellFilter = 'all';

  function getNotifications() {
    if (!state.notifications) {
      state.notifications = [
        {
          id: 'sys-quantizer',
          type: 'system',
          title: 'Model Quantizer Siap',
          message: 'Alat kuantisasi TFLite INT8/FP16 & ONNX Dynamic INT8 siap digunakan di Model Registry.',
          time: Date.now() - 1000 * 60 * 3,
          read: false
        },
        {
          id: 'sys-runtime',
          type: 'system',
          title: 'Runtime Engine Terhubung',
          message: 'FastAPI backend aktif di http://127.0.0.1:8765 dengan engine PyTorch & ONNX Runtime.',
          time: Date.now() - 1000 * 60 * 10,
          read: false
        },
        {
          id: 'sys-project',
          type: 'alert',
          title: 'Proyek Aktif',
          message: `Workspace aktif: ${state.project?.name || 'Smart Traffic Flow & Vehicle Counter'}`,
          time: Date.now() - 1000 * 60 * 15,
          read: false
        }
      ];
    }
    return state.notifications;
  }

  function formatTimeAgo(timestamp) {
    const diff = Math.floor((Date.now() - timestamp) / 1000);
    if (diff < 60) return 'Baru saja';
    if (diff < 3600) return `${Math.floor(diff / 60)}m lalu`;
    if (diff < 86400) return `${Math.floor(diff / 3600)}j lalu`;
    return `${Math.floor(diff / 86400)}h lalu`;
  }

  function renderNotifications() {
    const listEl = $('#hubBellList');
    if (!listEl) return;
    const notifs = getNotifications();
    const unreadCount = notifs.filter(n => !n.read).length;

    // Badge indicator
    const badgeEl = $('#hubBellBadge');
    if (badgeEl) {
      badgeEl.classList.toggle('active', unreadCount > 0);
    }
    const countBadgeEl = $('#hubBellCountBadge');
    if (countBadgeEl) {
      countBadgeEl.textContent = unreadCount > 0 ? `${unreadCount} Baru` : 'Semua Dibaca';
    }

    const filtered = notifs.filter(n => {
      if (activeBellFilter === 'alert') return n.type === 'alert';
      if (activeBellFilter === 'system') return n.type === 'system';
      return true;
    });

    if (!filtered.length) {
      listEl.innerHTML = `
        <div style="padding: 28px 16px; text-align: center; color: #94a3b8; font-size: 12px;">
          <div style="font-size: 26px; margin-bottom: 6px;">✨</div>
          <div style="font-weight: 600; color: #64748b;">Tidak Ada Notifikasi</div>
          <div style="font-size: 11px; margin-top: 2px;">Semua peristiwa dan alert telah ditinjau</div>
        </div>
      `;
      return;
    }

    listEl.innerHTML = filtered.map(item => `
      <div class="bell-notification-item ${item.read ? '' : 'unread'}" data-id="${item.id}">
        <div class="bell-item-icon ${item.type === 'alert' ? 'alert' : 'system'}">
          ${item.type === 'alert' ? '⚠️' : '⚡'}
        </div>
        <div class="bell-item-body">
          <div class="bell-item-title-row">
            <span class="bell-item-title">${escapeHtml(item.title)}</span>
            <span class="bell-item-time">${formatTimeAgo(item.time)}</span>
          </div>
          <div class="bell-item-msg">${escapeHtml(item.message)}</div>
        </div>
      </div>
    `).join('');
  }

  function closeAllHeaderDropdowns() {
    if ($('#topbarMoreDropdown')) $('#topbarMoreDropdown').hidden = true;
    if ($('#hubBellDropdown')) $('#hubBellDropdown').hidden = true;
    if ($('#hubUserDropdown')) $('#hubUserDropdown').hidden = true;
    if (typeof closeProjectSwitcherDropdown === 'function') closeProjectSwitcherDropdown();
  }

  function initHeaderActions() {
    // 1. More dropdown (...)
    const moreBtn = $('#topbarMoreBtn');
    const moreDropdown = $('#topbarMoreDropdown');
    if (moreBtn && moreDropdown) {
      moreBtn.onclick = (e) => {
        e.stopPropagation();
        const willOpen = moreDropdown.hidden;
        closeAllHeaderDropdowns();
        if (willOpen) {
          moreDropdown.hidden = false;
        }
      };

      $('#importBtn')?.addEventListener('click', () => {
        if (moreDropdown) moreDropdown.hidden = true;
      });
      $('#exportBtn')?.addEventListener('click', () => {
        if (moreDropdown) moreDropdown.hidden = true;
      });
    }

    $('#copyWorkflowJsonBtn')?.addEventListener('click', () => {
      if (moreDropdown) moreDropdown.hidden = true;
      try {
        const jsonStr = JSON.stringify(state.workflow || { nodes: [], edges: [] }, null, 2);
        if (navigator.clipboard && navigator.clipboard.writeText) {
          navigator.clipboard.writeText(jsonStr).then(() => {
            toast('Workflow JSON berhasil disalin ke clipboard!');
          }).catch(() => fallbackCopy(jsonStr));
        } else {
          fallbackCopy(jsonStr);
        }
      } catch (err) {
        toast('Gagal menyalin JSON: ' + err.message, true);
      }
    });

    function fallbackCopy(text) {
      const ta = document.createElement('textarea');
      ta.value = text;
      document.body.appendChild(ta);
      ta.select();
      document.execCommand('copy');
      document.body.removeChild(ta);
      toast('Workflow JSON berhasil disalin ke clipboard!');
    }

    $('#fitCanvasMoreBtn')?.addEventListener('click', () => {
      if (moreDropdown) moreDropdown.hidden = true;
      $('#fitBtn')?.click();
      toast('Tampilan kanvas dipusatkan');
    });

    const clearCanvasModal = $('#clearCanvasModal');
    function doClearCanvas() {
      state.workflow.nodes = [];
      state.workflow.edges = [];
      state.selected = null;
      state.selectedEdge = null;
      state.dirty = true;
      if ($('#dirty')) $('#dirty').hidden = false;
      renderCanvas();
      renderInspector();
      toast('Kanvas alur kerja berhasil dikosongkan');
    }

    $('#clearCanvasMoreBtn')?.addEventListener('click', () => {
      if (moreDropdown) moreDropdown.hidden = true;
      if (clearCanvasModal) {
        clearCanvasModal.showModal();
      } else {
        doClearCanvas();
      }
    });

    $('#closeClearCanvasModal')?.addEventListener('click', () => clearCanvasModal?.close());
    $('#cancelClearCanvasBtn')?.addEventListener('click', () => clearCanvasModal?.close());
    $('#confirmClearCanvasBtn')?.addEventListener('click', () => {
      clearCanvasModal?.close();
      doClearCanvas();
    });

    $('#docsSwaggerMoreBtn')?.addEventListener('click', () => {
      if (moreDropdown) moreDropdown.hidden = true;
      window.open('/docs', '_blank');
    });

    // 2. Notification Bell (🔔)
    const bellBtn = $('#hubBellBtn');
    const bellDropdown = $('#hubBellDropdown');
    if (bellBtn && bellDropdown) {
      bellBtn.onclick = (e) => {
        e.stopPropagation();
        const willOpen = bellDropdown.hidden;
        closeAllHeaderDropdowns();
        if (willOpen) {
          renderNotifications();
          bellDropdown.hidden = false;
        }
      };

      $('#hubBellMarkReadBtn')?.addEventListener('click', (e) => {
        e.stopPropagation();
        const notifs = getNotifications();
        notifs.forEach(n => { n.read = true; });
        renderNotifications();
        toast('Semua notifikasi ditandai telah dibaca');
      });

      $('#hubBellClearBtn')?.addEventListener('click', (e) => {
        e.stopPropagation();
        state.notifications = [];
        renderNotifications();
        toast('Riwayat notifikasi dibersihkan');
      });

      bellDropdown.querySelectorAll('.bell-filter-pill').forEach(btn => {
        btn.onclick = (e) => {
          e.stopPropagation();
          bellDropdown.querySelectorAll('.bell-filter-pill').forEach(b => b.classList.remove('active'));
          btn.classList.add('active');
          activeBellFilter = btn.dataset.filter || 'all';
          renderNotifications();
        };
      });

      $('#hubBellOpenLogsBtn')?.addEventListener('click', () => {
        bellDropdown.hidden = true;
        if (state.activeView !== 'studio') {
          switchMainView('studio');
        }
        switchProjectRailTab('telemetry');
        toast('Membuka console log & telemetri');
      });
    }

    // 3. System Help Modal (Help)
    const helpBtn = $('#hubHelpBtn');
    const helpModal = $('#systemHelpModal');
    if (helpBtn && helpModal) {
      helpBtn.onclick = () => {
        closeAllHeaderDropdowns();
        helpModal.showModal();
      };

      $('#closeSystemHelpModal')?.addEventListener('click', () => helpModal.close());
      $('#closeHelpFooterBtn')?.addEventListener('click', () => helpModal.close());

      // Help tabs
      helpModal.querySelectorAll('.help-nav-tab').forEach(tabBtn => {
        tabBtn.onclick = () => {
          helpModal.querySelectorAll('.help-nav-tab').forEach(t => t.classList.remove('active'));
          tabBtn.classList.add('active');
          const tab = tabBtn.dataset.tab;
          if ($('#helpPanelShortcuts')) $('#helpPanelShortcuts').hidden = (tab !== 'shortcuts');
          if ($('#helpPanelQuickstart')) $('#helpPanelQuickstart').hidden = (tab !== 'quickstart');
          if ($('#helpPanelCatalog')) $('#helpPanelCatalog').hidden = (tab !== 'catalog');
          if ($('#helpPanelAbout')) $('#helpPanelAbout').hidden = (tab !== 'about');
        };
      });

      helpModal.addEventListener('click', (e) => {
        const rect = helpModal.getBoundingClientRect();
        if (e.clientX < rect.left || e.clientX > rect.right || e.clientY < rect.top || e.clientY > rect.bottom) {
          helpModal.close();
        }
      });
    }

    // 4. User Avatar (AN)
    const userBtn = $('#hubUserAvatarBtn');
    const userDropdown = $('#hubUserDropdown');
    if (userBtn && userDropdown) {
      userBtn.onclick = (e) => {
        e.stopPropagation();
        const willOpen = userDropdown.hidden;
        closeAllHeaderDropdowns();
        if (willOpen) {
          userDropdown.hidden = false;
        }
      };

      $('#userMenuSettingsBtn')?.addEventListener('click', () => {
        userDropdown.hidden = true;
        $('#systemSettingsModal')?.showModal();
      });

      $('#userMenuQuantizeBtn')?.addEventListener('click', () => {
        userDropdown.hidden = true;
        if (typeof window.openQuantizeModal === 'function') {
          window.openQuantizeModal();
        } else {
          $('#quantizeModelModal')?.showModal();
        }
      });

      $('#userMenuHelpBtn')?.addEventListener('click', () => {
        userDropdown.hidden = true;
        helpModal?.showModal();
      });

      $('#userMenuDocsBtn')?.addEventListener('click', () => {
        userDropdown.hidden = true;
        window.open('/docs', '_blank');
      });

      $('#userMenuSyncBtn')?.addEventListener('click', async () => {
        userDropdown.hidden = true;
        try {
          await Promise.all([
            loadProjects(false),
            loadDashboardOverview(),
            pollStatus()
          ]);
          toast('Status sistem & proyek berhasil disinkronkan');
        } catch (err) {
          toast('Sinkronisasi selesai');
        }
      });

      $('#userMenuLockBtn')?.addEventListener('click', () => {
        userDropdown.hidden = true;
        toast('Sesi aman tersimpan (Single-Tenant On-Premise)');
      });
    }

    // Global document click listener for header dropdowns
    document.addEventListener('click', (e) => {
      const moreWrap = $('.header-more-wrap');
      const bellWrap = $('#hubBellWrap');
      const userWrap = $('#hubUserWrap');

      if (moreWrap && !moreWrap.contains(e.target)) {
        if (moreDropdown) moreDropdown.hidden = true;
      }
      if (bellWrap && !bellWrap.contains(e.target)) {
        if (bellDropdown) bellDropdown.hidden = true;
      }
      if (userWrap && !userWrap.contains(e.target)) {
        if (userDropdown) userDropdown.hidden = true;
      }
    });

    // Render initial notifications
    renderNotifications();
  }

  // --- Bootstrap ---
  (async () => {
    try {
      wireEvents();
      initSystemSettings();
      initHeaderActions();
      initAiStudioCopilot();
      switchMainView('projectsHub');

      const catalog = await api('/api/catalog');
      state.catalog = catalog.catalog || {};
      state.defaults = catalog.defaults;
      $('#runtimeText').textContent = catalog.runtime?.python ? `Python ${catalog.runtime.python}` : 'Ready';

      renderLibrary();
      await Promise.all([
        refreshModels(),
        refreshCameras(),
        refreshUploads(),
        loadTemplates(),
        loadProjects(false),
        loadDashboardOverview(),
      ]);
      if (!state.activeView || state.activeView === 'projectsHub') {
        renderProjectsHub();
      }
      await pollStatus();
      state.poll = setInterval(pollStatus, 800);
    } catch (e) {
      toast('Initialization error: ' + e.message, true);
      $('#runtimeText').textContent = 'API unavailable';
    }
  })();
})();

