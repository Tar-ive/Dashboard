// CADS Research Visualization Application
console.log('🎯 CADS Research Visualization - Initializing...');

// Application state
const app = {
    data: null,
    filteredData: null,
    searchIndex: null,
    clusterThemes: null,
    clusterCenters: null,
    deckgl: null,
    isLoading: true,
    currentZoom: 8,

    // UI elements
    elements: {
        loading: document.getElementById('loading'),
        loadingProgress: document.getElementById('loading-progress'),
        errorMessage: document.getElementById('error-message'),
        errorDetails: document.getElementById('error-details'),
        mapContainer: document.getElementById('map-container'),
        uiPanel: document.getElementById('ui-panel'),
        panelToggle: document.getElementById('panel-toggle'),
        searchInput: document.getElementById('search-input'),
        researcherFilter: document.getElementById('researcher-filter'),
        yearFilter: document.getElementById('year-filter'),
        yearDisplay: document.getElementById('year-display'),
        clusterFilter: document.getElementById('cluster-filter'),
        tooltip: document.getElementById('tooltip'),
        tooltipTitle: document.getElementById('tooltip-title'),
        tooltipDetails: document.getElementById('tooltip-details'),
        tooltipMeta: document.getElementById('tooltip-meta'),
        visiblePapers: document.getElementById('visible-papers'),
        totalPapers: document.getElementById('total-papers'),
        totalResearchers: document.getElementById('total-researchers'),
        totalClusters: document.getElementById('total-clusters')
    }
};

// Initialize the application
function init() {
    console.log('🚀 Starting CADS Research Visualization...');

    // Set up UI event listeners
    setupUIEventListeners();

    // Update loading progress
    updateLoadingProgress('Setting up interface...');

    // Load the visualization data and initialize
    loadVisualization();
}

// Set up UI event listeners
function setupUIEventListeners() {
    // Panel toggle
    app.elements.panelToggle.addEventListener('click', togglePanel);

    // Year filter
    app.elements.yearFilter.addEventListener('input', (e) => {
        app.elements.yearDisplay.textContent = e.target.value;
        applyFilters();
    });

    // Search input
    app.elements.searchInput.addEventListener('input', debounce((e) => {
        performSearch(e.target.value);
    }, 300));

    // Filter dropdowns
    app.elements.researcherFilter.addEventListener('change', (e) => {
        applyFilters();
    });

    app.elements.clusterFilter.addEventListener('change', (e) => {
        applyFilters();
    });

    // Keyboard shortcuts
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            hideTooltip();
        }
        if (e.key === '/' && !e.target.matches('input')) {
            e.preventDefault();
            app.elements.searchInput.focus();
        }
    });
}

// Toggle UI panel
function togglePanel() {
    const panel = app.elements.uiPanel;
    const button = app.elements.panelToggle;

    panel.classList.toggle('collapsed');
    button.textContent = panel.classList.contains('collapsed') ? '+' : '−';
    button.title = panel.classList.contains('collapsed') ? 'Show panel' : 'Hide panel';
}

// Update loading progress
function updateLoadingProgress(message) {
    app.elements.loadingProgress.textContent = message;
}

// Show error message
function showError(title, details) {
    app.elements.errorMessage.querySelector('.error-title').textContent = title;
    app.elements.errorDetails.textContent = details;
    app.elements.errorMessage.style.display = 'block';

    // Auto-hide after 10 seconds
    setTimeout(() => {
        app.elements.errorMessage.style.display = 'none';
    }, 10000);
}

// Hide loading screen
function hideLoading() {
    app.elements.loading.classList.add('hidden');
    app.isLoading = false;

    // Remove loading element after transition
    setTimeout(() => {
        app.elements.loading.style.display = 'none';
    }, 300);
}

// Show tooltip
function showTooltip(x, y, title, details, meta) {
    app.elements.tooltipTitle.textContent = title;
    app.elements.tooltipDetails.textContent = details;
    app.elements.tooltipMeta.textContent = meta;

    const tooltip = app.elements.tooltip;
    tooltip.style.display = 'block';

    // Position tooltip near cursor with small offset
    const offsetX = 15;
    const offsetY = 15;
    let tooltipX = x + offsetX;
    let tooltipY = y + offsetY;

    tooltip.style.left = tooltipX + 'px';
    tooltip.style.top = tooltipY + 'px';

    // Adjust position if tooltip goes off screen
    const rect = tooltip.getBoundingClientRect();
    if (rect.right > window.innerWidth) {
        tooltipX = x - rect.width - offsetX;
        tooltip.style.left = tooltipX + 'px';
    }
    if (rect.bottom > window.innerHeight) {
        tooltipY = y - rect.height - offsetY;
        tooltip.style.top = tooltipY + 'px';
    }

    // Ensure tooltip doesn't go off the left or top edge
    if (tooltipX < 0) {
        tooltip.style.left = '10px';
    }
    if (tooltipY < 0) {
        tooltip.style.top = '10px';
    }
}

// Hide tooltip
function hideTooltip() {
    app.elements.tooltip.style.display = 'none';
}

// Debounce utility function
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Load and initialize the visualization
async function loadVisualization() {
    try {
        updateLoadingProgress('Loading research data...');

        // Try to load data - start with uncompressed for local development
        let response;
        let dataUrl = '';
        let data;

        try {
            // Try uncompressed first for local development
            dataUrl = '/data/visualization-data.json';
            response = await fetch(dataUrl);
            if (response.ok) {
                console.log('✅ Loading uncompressed data from:', dataUrl);
                data = await response.json();
            } else {
                throw new Error('Uncompressed data not available');
            }
        } catch (e) {
            console.log('⚠️ Uncompressed data failed, trying compressed...');
            try {
                dataUrl = '/data/visualization-data.json.gz';
                response = await fetch(dataUrl);
                if (!response.ok) throw new Error('Compressed data not available');
                console.log('✅ Loading compressed data from:', dataUrl);
                data = await response.json();
            } catch (gzError) {
                throw new Error(`Failed to load data from both sources. Uncompressed: ${e.message}, Compressed: ${gzError.message}`);
            }
        }

        // Validate data structure
        if (!data.p || !Array.isArray(data.p)) {
            throw new Error('Invalid data format: missing publications array');
        }
        if (!data.r || !Array.isArray(data.r)) {
            throw new Error('Invalid data format: missing researchers array');
        }
        if (!data.c || !Array.isArray(data.c)) {
            throw new Error('Invalid data format: missing clusters array');
        }

        console.log(`📊 Loaded ${data.p.length} publications, ${data.r.length} researchers, ${data.c.length} clusters`);
        app.data = data;

        updateLoadingProgress('Loading cluster themes...');

        // Load cluster themes and centers
        await loadClusterData();

        updateLoadingProgress('Processing data...');

        // Update UI with metadata
        app.elements.totalPapers.textContent = data.meta.totalPapers.toLocaleString();
        app.elements.totalResearchers.textContent = data.meta.totalResearchers;
        app.elements.totalClusters.textContent = data.meta.totalClusters;

        // Populate filter dropdowns
        populateFilters(data);

        updateLoadingProgress('Initializing visualization...');

        // Initialize Deck.gl visualization
        initializeDeckGL(data);

        updateLoadingProgress('Ready!');

        setTimeout(() => {
            hideLoading();
            console.log('✅ CADS Research Visualization - Loaded successfully!');
            console.log(`📊 Displaying ${data.p.length} publications from ${data.r.length} researchers`);
        }, 300);

    } catch (error) {
        console.error('Failed to load visualization:', error);
        showError('Loading Failed', `Could not load visualization data: ${error.message}`);
        hideLoading();
    }
}

// Populate filter dropdowns with data
function populateFilters(data) {
    // Populate researcher filter
    const researcherSelect = app.elements.researcherFilter;
    data.r.forEach(researcher => {
        const option = document.createElement('option');
        option.value = researcher.i;
        option.textContent = researcher.n;
        researcherSelect.appendChild(option);
    });

    // Populate cluster filter
    const clusterSelect = app.elements.clusterFilter;
    data.c.forEach(cluster => {
        const option = document.createElement('option');
        option.value = cluster.i;
        option.textContent = cluster.n;
        clusterSelect.appendChild(option);
    });
}

// Load cluster data (themes and centers)
async function loadClusterData() {
    try {
        console.log('🎨 Loading cluster themes...');
        // Try uncompressed first for local development
        let themesResponse;
        let themesUrl = '';
        try {
            themesUrl = '/data/cluster_themes.json';
            themesResponse = await fetch(themesUrl);
            if (themesResponse.ok) {
                const themesData = await themesResponse.json();
                app.clusterThemes = themesData.themes || themesData;
                console.log(`✅ Loaded ${Object.keys(app.clusterThemes).length} cluster themes from ${themesUrl}`);
            } else {
                throw new Error('Uncompressed themes not available');
            }
        } catch (e) {
            console.log('⚠️ Uncompressed themes failed, trying compressed...');
            try {
                themesUrl = '/data/cluster_themes.json.gz';
                themesResponse = await fetch(themesUrl);
                if (themesResponse.ok) {
                    const themesData = await themesResponse.json();
                    app.clusterThemes = themesData.themes || themesData;
                    console.log(`✅ Loaded ${Object.keys(app.clusterThemes).length} cluster themes from ${themesUrl}`);
                } else {
                    throw new Error('Compressed themes not available');
                }
            } catch (gzError) {
                console.warn(`⚠️ Failed to load cluster themes from both sources:`, e.message, gzError.message);
            }
        }

        console.log('📍 Loading cluster centers...');
        // Try uncompressed first for local development
        let centersResponse;
        let centersUrl = '';
        try {
            centersUrl = '/data/clustering_results.json';
            centersResponse = await fetch(centersUrl);
            if (centersResponse.ok) {
                const centersData = await centersResponse.json();
                app.clusterCenters = centersData.cluster_info || centersData;
                console.log(`✅ Loaded ${Object.keys(app.clusterCenters).length} cluster centers from ${centersUrl}`);
            } else {
                throw new Error('Uncompressed centers not available');
            }
        } catch (e) {
            console.log('⚠️ Uncompressed centers failed, trying compressed...');
            try {
                centersUrl = '/data/clustering_results.json.gz';
                centersResponse = await fetch(centersUrl);
                if (centersResponse.ok) {
                    const centersData = await centersResponse.json();
                    app.clusterCenters = centersData.cluster_info || centersData;
                    console.log(`✅ Loaded ${Object.keys(app.clusterCenters).length} cluster centers from ${centersUrl}`);
                } else {
                    throw new Error('Compressed centers not available');
                }
            } catch (gzError) {
                console.warn(`⚠️ Failed to load cluster centers from both sources:`, e.message, gzError.message);
            }
        }
    } catch (error) {
        console.warn('⚠️ Could not load cluster data:', error);
        // Continue without cluster labels if data is not available
        app.clusterThemes = {};
        app.clusterCenters = {};
    }
}

// Initialize Deck.gl visualization
function initializeDeckGL(data) {
    // Store initial zoom level
    app.currentZoom = data.v.z;

    // Create the Deck.gl instance
    app.deckgl = new deck.DeckGL({
        container: 'map-container',
        initialViewState: {
            longitude: data.v.lng,
            latitude: data.v.lat,
            zoom: data.v.z,
            pitch: 0,
            bearing: 0
        },
        controller: true,
        layers: createAllLayers(data, data.p),
        onHover: handleHover,
        onClick: handleClick,
        onViewStateChange: handleViewStateChange,
        getCursor: () => 'crosshair'
    });

    // Update visible papers count
    app.elements.visiblePapers.textContent = data.p.length.toLocaleString();
}

// Handle view state changes (zoom, pan)
function handleViewStateChange({ viewState }) {
    app.currentZoom = viewState.zoom;
    // Update layers when zoom changes to show/hide labels appropriately
    if (app.deckgl && app.data) {
        const currentData = getCurrentFilteredData();
        app.deckgl.setProps({
            layers: createAllLayers(app.data, currentData)
        });
    }
}

// Get currently filtered data
function getCurrentFilteredData() {
    if (!app.data) return [];

    const researcherFilter = app.elements.researcherFilter.value;
    const clusterFilter = app.elements.clusterFilter.value;
    const yearFilter = parseInt(app.elements.yearFilter.value);

    let filteredData = app.data.p;

    if (researcherFilter) {
        filteredData = filteredData.filter(p => p.r === researcherFilter);
    }

    if (clusterFilter) {
        filteredData = filteredData.filter(p => p.c === parseInt(clusterFilter));
    }

    if (yearFilter) {
        filteredData = filteredData.filter(p => p.y >= yearFilter);
    }

    return filteredData;
}

// Create all layers (scatterplot + text labels)
function createAllLayers(fullData, publications) {
    const layers = [createScatterplotLayerWithData(fullData, publications)];

    // Add cluster theme labels if data is available and zoom level is appropriate
    if (app.clusterThemes && app.clusterCenters && shouldShowLabels()) {
        try {
            const labelLayer = createClusterLabelsLayer(fullData, publications);
            if (labelLayer) {
                layers.push(labelLayer);
            }
        } catch (error) {
            console.error('Error creating cluster labels layer:', error);
        }
    }

    return layers;
}

// Determine if labels should be shown based on zoom level
function shouldShowLabels() {
    // Show labels when zoomed in enough to see cluster structure clearly
    return app.currentZoom >= 5;
}

// Create cluster theme labels layer
function createClusterLabelsLayer(fullData, publications) {
    // Get unique clusters from current publications
    const visibleClusters = new Set(publications.map(p => p.c).filter(c => c !== -1));

    // Create label data for visible clusters
    const labelData = [];
    visibleClusters.forEach(clusterId => {
        const clusterInfo = app.clusterCenters[clusterId.toString()];
        const themeName = app.clusterThemes[clusterId.toString()];

        if (clusterInfo && themeName && clusterInfo.size >= 15) { // Only show labels for significant clusters
            labelData.push({
                position: clusterInfo.center,
                text: themeName,
                clusterId: clusterId,
                size: clusterInfo.size
            });
        }
    });

    console.log(`Creating cluster labels layer with ${labelData.length} labels`);

    // Check if TextLayer is available
    if (!deck.TextLayer) {
        console.warn('TextLayer not available in this Deck.gl version');
        return null;
    }

    return new deck.TextLayer({
        id: 'cluster-labels-layer',
        data: labelData,

        // Position
        getPosition: d => [d.position[0], d.position[1], 1], // Slightly elevated

        // Text properties
        getText: d => d.text,
        getSize: d => Math.max(12, Math.min(18, 12 + Math.log(d.size))), // Size based on cluster size
        getColor: [255, 255, 255, 200], // White text with slight transparency

        // Font and styling
        fontFamily: 'Arial, sans-serif',
        fontWeight: 'bold',

        // Alignment
        getTextAnchor: 'middle',
        getAlignmentBaseline: 'center',

        // Interaction
        pickable: false,

        // Performance
        updateTriggers: {
            getPosition: publications,
            getText: app.clusterThemes
        }
    });
}

// Create scatterplot layer with optimized data
function createScatterplotLayerWithData(fullData, publications) {
    return new deck.ScatterplotLayer({
        id: 'publications-layer',
        data: publications,

        // Position from pre-computed UMAP coordinates
        getPosition: d => [d.p[0], d.p[1], 0],

        // Size and color
        getRadius: 3,
        getFillColor: d => {
            const researcher = fullData.r.find(r => r.i === d.r);
            return researcher ? researcher.col : [128, 128, 128];
        },

        // Interaction
        pickable: true,
        autoHighlight: true,

        // Performance optimizations
        radiusMinPixels: 1,
        radiusMaxPixels: 12,

        // Update triggers for efficient re-rendering
        updateTriggers: {
            getFillColor: publications,
            getPosition: publications
        }
    });
}

// Handle hover events
function handleHover(info) {
    if (info.object && info.x !== undefined && info.y !== undefined) {
        const publication = info.object;
        const researcher = app.data.r.find(r => r.i === publication.r);
        const cluster = app.data.c.find(c => c.i === publication.c);

        const title = publication.t || 'Untitled';
        const details = `${researcher ? researcher.n : 'Unknown Author'} • ${publication.y || 'Unknown Year'}`;
        const meta = `${publication.cit || 0} citations • ${cluster ? cluster.n : 'Uncategorized'}`;

        showTooltip(info.x, info.y, title, details, meta);
    } else {
        hideTooltip();
    }
}

// Handle click events
function handleClick(info) {
    if (info.object) {
        const publication = info.object;
        console.log('Clicked publication:', publication);

        // Could implement paper details modal here
        if (publication.d) {
            // Open DOI link if available
            window.open(`https://doi.org/${publication.d}`, '_blank');
        }
    }
}

// Apply filters to the visualization
function applyFilters() {
    if (!app.deckgl || !app.data) return;

    const filteredData = getCurrentFilteredData();

    // Update layers with filtered data
    app.deckgl.setProps({
        layers: createAllLayers(app.data, filteredData)
    });

    // Update visible papers count
    app.elements.visiblePapers.textContent = filteredData.length.toLocaleString();
}

// Perform search (placeholder - would need search index implementation)
function performSearch(query) {
    if (!query.trim()) {
        // Reset to show all data
        applyFilters();
        return;
    }

    console.log('Searching for:', query);
    // TODO: Implement search functionality with search index
    // For now, just apply current filters
    applyFilters();
}

// Initialize when DOM is loaded
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    init();
}

// Expose functions and app object globally for debugging and error handling
window.CADSVisualization = app;
window.showError = showError;