/**
 * High-Resolution GeoJSON for Maharashtra Districts / Cities
 * Featuring natural resource parameters and precise neighbor adjacencies.
 */

export const MAHARASHTRA_DISTRICTS_GEOJSON = {
  type: "FeatureCollection",
  features: [
    {
      type: "Feature",
      id: "MH-NM",
      properties: {
        id: "MH-NM",
        name: "Navi Mumbai",
        tier: "city",
        type: "Planned Urban Metropolitan Area",
        center: [73.0297, 19.0330],
        camera_zoom: 12.5,
        camera_pitch: 52,
        camera_bearing: 25,
        neighbors: ["MH-TH", "MH-MUM", "MH-MSU", "MH-RAI", "MH-PU"],
        forest_cover_pct: 28.4,
        forest_area_sqkm: 98.5,
        water_bodies_count: 48,
        tree_count_millions: 12.4,
        groundwater_depth_m: 5.8,
        monitoring_stations_count: 14,
        description: "Special planned urban region with mangrove creek estuaries and MIDC industrial belts."
      },
      geometry: {
        type: "Polygon",
        coordinates: [
          [
            [72.965, 19.185], [73.045, 19.185], [73.075, 19.120], [73.135, 19.080],
            [73.165, 19.010], [73.140, 18.940], [73.040, 18.930], [72.990, 18.980],
            [72.980, 19.050], [72.965, 19.110], [72.965, 19.185]
          ]
        ]
      }
    },
    {
      type: "Feature",
      id: "MH-TH",
      properties: {
        id: "MH-TH",
        name: "Thane",
        tier: "city",
        type: "Metropolitan District",
        center: [72.9781, 19.2183],
        camera_zoom: 11.5,
        camera_pitch: 40,
        camera_bearing: 15,
        neighbors: ["MH-NM", "MH-MSU", "MH-PU"],
        forest_cover_pct: 36.2,
        forest_area_sqkm: 1540.0,
        water_bodies_count: 62,
        tree_count_millions: 34.0,
        groundwater_depth_m: 6.4,
        monitoring_stations_count: 16,
        description: "Immediate northern neighbor of Navi Mumbai along the Ulhas river basin."
      },
      geometry: {
        type: "Polygon",
        coordinates: [
          [
            [72.935, 19.175], [73.050, 19.200], [73.180, 19.280], [73.350, 19.450],
            [73.150, 19.650], [72.850, 19.650], [72.880, 19.260], [72.935, 19.175]
          ]
        ]
      }
    },
    {
      type: "Feature",
      id: "MH-MUM",
      properties: {
        id: "MH-MUM",
        name: "Mumbai City",
        tier: "city",
        type: "Island City District",
        center: [72.8347, 18.9220],
        camera_zoom: 12.0,
        camera_pitch: 45,
        camera_bearing: 0,
        neighbors: ["MH-MSU", "MH-NM", "MH-RAI"],
        forest_cover_pct: 5.8,
        forest_area_sqkm: 9.2,
        water_bodies_count: 12,
        tree_count_millions: 3.8,
        groundwater_depth_m: 9.2,
        monitoring_stations_count: 18,
        description: "South Mumbai coastal urban zone: Marine Drive, Colaba, Worli marine discharge points."
      },
      geometry: {
        type: "Polygon",
        coordinates: [
          [
            [72.805, 18.895], [72.845, 18.895], [72.865, 18.950], [72.860, 19.010],
            [72.825, 19.020], [72.810, 18.980], [72.800, 18.940], [72.805, 18.895]
          ]
        ]
      }
    },
    {
      type: "Feature",
      id: "MH-MSU",
      properties: {
        id: "MH-MSU",
        name: "Mumbai Suburban",
        tier: "city",
        type: "Suburban District",
        center: [72.8697, 19.1136],
        camera_zoom: 11.8,
        camera_pitch: 45,
        camera_bearing: 0,
        neighbors: ["MH-MUM", "MH-TH", "MH-NM"],
        forest_cover_pct: 24.1,
        forest_area_sqkm: 108.0,
        water_bodies_count: 24,
        tree_count_millions: 16.2,
        groundwater_depth_m: 7.5,
        monitoring_stations_count: 22,
        description: "Bandra to Dahisar & Kurla to Mulund suburban belt including Sanjay Gandhi National Park."
      },
      geometry: {
        type: "Polygon",
        coordinates: [
          [
            [72.810, 19.020], [72.865, 19.010], [72.935, 19.060], [72.955, 19.175],
            [72.880, 19.260], [72.830, 19.260], [72.815, 19.150], [72.810, 19.020]
          ]
        ]
      }
    },
    {
      type: "Feature",
      id: "MH-PU",
      properties: {
        id: "MH-PU",
        name: "Pune",
        tier: "city",
        type: "Metropolitan District",
        center: [73.8567, 18.5204],
        camera_zoom: 11.0,
        camera_pitch: 35,
        camera_bearing: 0,
        neighbors: ["MH-NM", "MH-RAI", "MH-TH"],
        forest_cover_pct: 12.8,
        forest_area_sqkm: 2004.0,
        water_bodies_count: 84,
        tree_count_millions: 48.0,
        groundwater_depth_m: 7.1,
        monitoring_stations_count: 20,
        description: "Mula-Mutha river basin, automotive and IT industrial corridor."
      },
      geometry: {
        type: "Polygon",
        coordinates: [
          [
            [73.35, 18.25], [74.20, 18.10], [74.85, 18.60], [74.40, 19.20],
            [73.65, 19.10], [73.35, 18.25]
          ]
        ]
      }
    },
    {
      type: "Feature",
      id: "MH-RAI",
      properties: {
        id: "MH-RAI",
        name: "Raigad",
        tier: "city",
        type: "Coastal & Industrial District",
        center: [73.1812, 18.5158],
        camera_zoom: 10.5,
        camera_pitch: 30,
        camera_bearing: 0,
        neighbors: ["MH-NM", "MH-PU", "MH-MUM"],
        forest_cover_pct: 39.5,
        forest_area_sqkm: 2824.0,
        water_bodies_count: 76,
        tree_count_millions: 58.0,
        groundwater_depth_m: 4.8,
        monitoring_stations_count: 12,
        description: "Immediate southern neighbor of Navi Mumbai: Patalganga river, JNPT port, and petrochemical hubs."
      },
      geometry: {
        type: "Polygon",
        coordinates: [
          [
            [72.85, 18.20], [73.25, 17.85], [73.60, 18.30], [73.30, 18.90],
            [73.00, 18.90], [72.85, 18.20]
          ]
        ]
      }
    }
  ]
};
