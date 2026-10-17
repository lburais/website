/**
 * Génère et affiche le contenu HTML d'une carte utilisateur.
 * @param {string} targetId - L'identifiant de l'élément HTML cible.
 * @param {Object} data - Les données à afficher (nom, lat, lon).
 */
function render_country(targetId, points) {

    const map = L.map(targetId).setView([48.8566, 2.3522], 5);
    // Deliberately do not add a background tile layer; only points and country outlines are shown.

    let pointMarkers = [];
    let countryLayers = [];
    let countriesPromise = null;

    function status(text) {
        const statusEl = document.getElementById('status');
        statusEl.textContent = text;
        return;
    }

    function escapeHtml(value) {
      return String(value).replace(/[&<>"']/g, char => ({
        '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
      }[char]));
    }

    async function fetchJson(url) {
      const response = await fetch(url);
      if (!response.ok) throw new Error(`HTTP ${response.status} from ${new URL(url).hostname}`);
      return response.json();
    }

    async function loadCountries() {
      if (!countriesPromise) {
        countriesPromise = (async () => {
          const urls = [
            'https://cdn.jsdelivr.net/gh/datasets/geo-countries@master/data/countries.geojson',
            'https://raw.githubusercontent.com/datasets/geo-countries/master/data/countries.geojson'
          ];
          let lastError;
          for (const url of urls) {
            try {
              const data = await fetchJson(url);
              if (data && Array.isArray(data.features) && data.features.length) return data;
              throw new Error('The boundary service returned invalid GeoJSON');
            } catch (error) { lastError = error; }
          }
          throw new Error(`Both boundary sources failed. ${lastError ? lastError.message : ''} Check your internet connection.`);
        })().catch(error => { countriesPromise = null; throw error; });
      }
      return countriesPromise;
    }

    function getCountryName(feature) {
      const props = feature.properties || {};
      return props.ADMIN || props.name || props.NAME || props.name_en || 'Country';
    }

    function findCountry(world, lat, lon) {
      const point = L.latLng(lat, lon);
      const candidates = world.features.filter(feature => {
        const bounds = L.geoJSON(feature).getBounds();
        return bounds.isValid() && bounds.contains(point);
      });
      return candidates.find(feature => geometryContainsPoint(feature.geometry, lat, lon)) || null;
    }

    function clearMapLayers() {
      pointMarkers.forEach(marker => map.removeLayer(marker));
      countryLayers.forEach(layer => map.removeLayer(layer));
      pointMarkers = [];
      countryLayers = [];
    }

    async function drawPointsAndCountries(points) {
      if (!points.length) {
        status('Select at least one city, or enter a custom point and press “Show point and country”.');
        return;
      }
      clearMapLayers();
      const groupBounds = L.latLngBounds([]);
      points.forEach(({ name, lat, lon }) => {
        const marker = L.marker([lat, lon], {
          icon: L.divIcon({
            className: '',
            html: '<div class="fp-map-marker"></div>',
            iconSize: [52, 52],
            iconAnchor: [26, 26]
          })
        }).addTo(map);
        marker.bindPopup(`<strong>${escapeHtml(name)}</strong><br>${lat.toFixed(6)}, ${lon.toFixed(6)}<br>Loading country boundary…`);
        pointMarkers.push(marker);
        groupBounds.extend([lat, lon]);
      });
      map.fitBounds(groupBounds, { padding: [35, 35], maxZoom: points.length === 1 ? 6 : 5 });
      status(`Displayed ${points.length} point${points.length === 1 ? '' : 's'}. Loading country boundaries…`);

      try {
        const world = await loadCountries();
        const drawnCountries = new Set();
        for (let i = 0; i < points.length; i++) {
          const { name, lat, lon } = points[i];
          const marker = pointMarkers[i];
          let matched = findCountry(world, lat, lon);
          if (!matched) {
            marker.setPopupContent(`<strong>${escapeHtml(name)}</strong><br>${lat.toFixed(6)}, ${lon.toFixed(6)}<br>Country boundary not found`);
            continue;
          }
          let countryName = getCountryName(matched);
          // distant overseas territories are omitted.
          const displayFeature = regionalCountryFeature(matched, lat, lon);
          if (!displayFeature) {
            marker.setPopupContent(`<strong>${escapeHtml(name)}</strong><br>${lat.toFixed(6)}, ${lon.toFixed(6)}<br>Country boundary not found in this region`);
            continue;
          }
          const key = countryName;
          marker.setPopupContent(`<strong>${escapeHtml(name)}</strong><br>${lat.toFixed(6)}, ${lon.toFixed(6)}<br>Country: ${escapeHtml(countryName)}`);

          if (!drawnCountries.has(key)) {
            const layer = L.geoJSON(displayFeature, {
              style: {
                color: '#55585c',
                weight: 1,
                opacity: 0.95,
                fillColor: '#d9d9d9',
                fillOpacity: 0.8
              }
            }).addTo(map);
            countryLayers.push(layer);
            const bounds = layer.getBounds();
            if (bounds.isValid()) groupBounds.extend(bounds);
            drawnCountries.add(key);
          }
        }
        map.fitBounds(groupBounds, { padding: [28, 28], maxZoom: points.length === 1 ? 8 : 5 });
        status(`Displayed ${points.length} point${points.length === 1 ? '' : 's'} across ${drawnCountries.size} countr${drawnCountries.size === 1 ? 'y' : 'ies'}.`);
      } catch (error) {
        status(`Points are displayed, but country boundaries could not be loaded. ${error.message}`);
      } finally {
      }
    }

    async function drawPointAndCountry(name, lat, lon) {
      await drawPointsAndCountries([{ name, lat, lon }]);
    }

    // Keep only country polygon parts in the same geographic region as the point,
    // preventing distant overseas territories from appearing in the outline.
    // A generous 1,200 km threshold preserves nearby islands that belong to the region.
    function regionalCountryFeature(feature, lat, lon) {
      const geometry = feature.geometry;
      if (!geometry) return null;
      const polygons = geometry.type === 'Polygon'
        ? [geometry.coordinates]
        : geometry.type === 'MultiPolygon' ? geometry.coordinates : [];
      const kept = polygons.filter(polygon => {
        const outer = polygon[0] || [];
        if (!outer.length) return false;
        const centerLon = outer.reduce((sum, p) => sum + p[0], 0) / outer.length;
        const centerLat = outer.reduce((sum, p) => sum + p[1], 0) / outer.length;
        const dLat = (centerLat - lat) * 111.32;
        const dLon = (centerLon - lon) * 111.32 * Math.cos(lat * Math.PI / 180);
        return Math.hypot(dLat, dLon) <= 1200 || geometryContainsPoint(feature.geometry, lat, lon) && polygonContainsPoint(polygon, lat, lon);
      });
      if (!kept.length) return feature;
      return {
        type: 'Feature',
        properties: { ...(feature.properties || {}) },
        geometry: kept.length === 1
          ? { type: 'Polygon', coordinates: kept[0] }
          : { type: 'MultiPolygon', coordinates: kept }
      };
    }

    // Ray-casting point-in-polygon test for Polygon and MultiPolygon GeoJSON geometry.
    function ringContainsPoint(ring, lat, lon) {
      let inside = false;
      for (let i = 0, j = ring.length - 1; i < ring.length; j = i++) {
        const xi = ring[i][0], yi = ring[i][1];
        const xj = ring[j][0], yj = ring[j][1];
        const intersects = ((yi > lat) !== (yj > lat)) &&
          (lon < (xj - xi) * (lat - yi) / ((yj - yi) || Number.EPSILON) + xi);
        if (intersects) inside = !inside;
      }
      return inside;
    }

    function polygonContainsPoint(polygon, lat, lon) {
      if (!polygon.length || !ringContainsPoint(polygon[0], lat, lon)) return false;
      for (let i = 1; i < polygon.length; i++) {
        if (ringContainsPoint(polygon[i], lat, lon)) return false; // hole
      }
      return true;
    }

    function geometryContainsPoint(geometry, lat, lon) {
      if (!geometry) return false;
      if (geometry.type === 'Polygon') return polygonContainsPoint(geometry.coordinates, lat, lon);
      if (geometry.type === 'MultiPolygon') {
        return geometry.coordinates.some(poly => polygonContainsPoint(poly, lat, lon));
      }
      return false;
    }

    drawPointsAndCountries(points);
}