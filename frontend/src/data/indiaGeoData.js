/**
 * GeoJSON Boundaries & Centroids for Indian States
 * Featuring natural resource metrics and topological neighbor links.
 */

export const INDIA_STATES_GEOJSON = {
  type: "FeatureCollection",
  features: [
    {
      type: "Feature",
      id: "IN-MH",
      properties: {
        id: "IN-MH",
        name: "Maharashtra",
        code: "MH",
        capital: "Mumbai",
        tier: "state",
        center: [75.7139, 19.7515],
        area_sq_km: 307713,
        neighbors: ["IN-GJ", "IN-MP", "IN-TG", "IN-KA"],
        forest_cover_pct: 20.13,
        forest_area_sqkm: 61952.0,
        water_bodies_count: 14200,
        tree_count_millions: 420.5,
        groundwater_depth_m: 8.4,
        monitoring_stations_count: 92
      },
      geometry: {
        type: "Polygon",
        coordinates: [
          [
            [72.65, 18.90], [72.82, 19.98], [73.50, 20.90], [74.20, 21.80],
            [75.80, 21.60], [77.50, 21.70], [79.20, 21.50], [80.90, 21.30],
            [80.50, 19.50], [80.10, 18.80], [78.90, 18.80], [77.60, 18.00],
            [76.50, 17.50], [75.80, 17.20], [74.50, 16.00], [73.80, 15.80],
            [73.30, 16.50], [73.00, 17.80], [72.75, 18.50], [72.65, 18.90]
          ]
        ]
      }
    },
    {
      type: "Feature",
      id: "IN-GJ",
      properties: {
        id: "IN-GJ",
        name: "Gujarat",
        code: "GJ",
        capital: "Gandhinagar",
        tier: "state",
        center: [71.1924, 22.2587],
        area_sq_km: 196024,
        neighbors: ["IN-MH", "IN-RJ", "IN-MP"],
        forest_cover_pct: 11.03,
        forest_area_sqkm: 21644.0,
        water_bodies_count: 11500,
        tree_count_millions: 260.0,
        groundwater_depth_m: 14.2,
        monitoring_stations_count: 64
      },
      geometry: {
        type: "Polygon",
        coordinates: [
          [
            [68.50, 23.50], [70.50, 24.50], [72.50, 24.50], [73.80, 23.00],
            [73.50, 21.00], [72.70, 20.40], [72.00, 21.00], [69.50, 22.00],
            [68.50, 23.50]
          ]
        ]
      }
    },
    {
      type: "Feature",
      id: "IN-KA",
      properties: {
        id: "IN-KA",
        name: "Karnataka",
        code: "KA",
        capital: "Bengaluru",
        tier: "state",
        center: [75.7139, 15.3173],
        area_sq_km: 191791,
        neighbors: ["IN-MH", "IN-TG", "IN-TN", "IN-KL"],
        forest_cover_pct: 20.11,
        forest_area_sqkm: 38575.0,
        water_bodies_count: 16800,
        tree_count_millions: 380.0,
        groundwater_depth_m: 7.8,
        monitoring_stations_count: 58
      },
      geometry: {
        type: "Polygon",
        coordinates: [
          [
            [74.05, 14.80], [75.00, 17.50], [77.50, 18.00], [77.60, 14.00],
            [77.00, 12.00], [75.50, 12.00], [74.50, 13.50], [74.05, 14.80]
          ]
        ]
      }
    },
    {
      type: "Feature",
      id: "IN-DL",
      properties: {
        id: "IN-DL",
        name: "Delhi (NCT)",
        code: "DL",
        capital: "New Delhi",
        tier: "state",
        center: [77.1025, 28.7041],
        area_sq_km: 1484,
        neighbors: ["IN-UP", "IN-RJ"],
        forest_cover_pct: 13.15,
        forest_area_sqkm: 195.0,
        water_bodies_count: 620,
        tree_count_millions: 18.5,
        groundwater_depth_m: 18.5,
        monitoring_stations_count: 42
      },
      geometry: {
        type: "Polygon",
        coordinates: [
          [
            [76.85, 28.45], [77.35, 28.45], [77.35, 28.88], [76.85, 28.88], [76.85, 28.45]
          ]
        ]
      }
    },
    {
      type: "Feature",
      id: "IN-MP",
      properties: {
        id: "IN-MP",
        name: "Madhya Pradesh",
        code: "MP",
        capital: "Bhopal",
        tier: "state",
        center: [78.6569, 22.9734],
        area_sq_km: 308252,
        neighbors: ["IN-MH", "IN-GJ", "IN-RJ", "IN-UP"],
        forest_cover_pct: 25.14,
        forest_area_sqkm: 77493.0,
        water_bodies_count: 19400,
        tree_count_millions: 610.0,
        groundwater_depth_m: 6.5,
        monitoring_stations_count: 52
      },
      geometry: {
        type: "Polygon",
        coordinates: [
          [
            [74.50, 22.00], [78.00, 26.50], [82.50, 24.00], [80.50, 21.50],
            [75.00, 21.50], [74.50, 22.00]
          ]
        ]
      }
    },
    {
      type: "Feature",
      id: "IN-TN",
      properties: {
        id: "IN-TN",
        name: "Tamil Nadu",
        code: "TN",
        capital: "Chennai",
        tier: "state",
        center: [78.6569, 11.1271],
        area_sq_km: 130058,
        neighbors: ["IN-KA", "IN-KL"],
        forest_cover_pct: 20.31,
        forest_area_sqkm: 26419.0,
        water_bodies_count: 18200,
        tree_count_millions: 340.0,
        groundwater_depth_m: 8.9,
        monitoring_stations_count: 60
      },
      geometry: {
        type: "Polygon",
        coordinates: [
          [
            [77.20, 8.10], [78.00, 9.00], [79.80, 10.30], [80.30, 13.40],
            [79.20, 13.00], [77.50, 12.00], [76.50, 11.50], [77.20, 8.10]
          ]
        ]
      }
    },
    {
      type: "Feature",
      id: "IN-WB",
      properties: {
        id: "IN-WB",
        name: "West Bengal",
        code: "WB",
        capital: "Kolkata",
        tier: "state",
        center: [87.8550, 22.9868],
        area_sq_km: 88752,
        neighbors: ["IN-OD", "IN-JH", "IN-BR"],
        forest_cover_pct: 18.96,
        forest_area_sqkm: 16828.0,
        water_bodies_count: 28400,
        tree_count_millions: 410.0,
        groundwater_depth_m: 5.2,
        monitoring_stations_count: 48
      },
      geometry: {
        type: "Polygon",
        coordinates: [
          [
            [86.00, 22.00], [88.50, 21.50], [89.00, 23.50], [88.20, 26.50],
            [87.00, 24.50], [86.00, 22.00]
          ]
        ]
      }
    }
  ]
};
