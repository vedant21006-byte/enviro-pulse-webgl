/**
 * High-Resolution GeoJSON for Navi Mumbai Wards & Industrial Hubs
 * Featuring micro-level natural resources, tree population estimates, and bordering ward topology.
 */

export const NAVI_MUMBAI_WARDS_GEOJSON = {
  type: "FeatureCollection",
  features: [
    {
      type: "Feature",
      id: "NM-VASHI",
      properties: {
        id: "NM-VASHI",
        name: "Vashi (Sector 17 / Creek)",
        tier: "area",
        type: "Commercial & Creek Estuary Zone",
        center: [72.9986, 19.0771],
        camera_zoom: 14.2,
        camera_pitch: 58,
        camera_bearing: 30,
        neighbors: ["NM-KOPARKH", "NM-NERUL", "NM-GHANSOLI"],
        forest_cover_pct: 14.5,
        forest_area_sqkm: 2.8,
        water_bodies_count: 4,
        tree_count_millions: 0.45,
        groundwater_depth_m: 3.9,
        monitoring_stations_count: 3,
        sensor_id: "SEN-NM-VSH-01",
        description: "Vashi Creek outflow and high-density commercial nexus. Monitored for creek organic load and vehicular NO2."
      },
      geometry: {
        type: "Polygon",
        coordinates: [
          [
            [72.980, 19.060], [73.015, 19.060], [73.020, 19.095], [72.985, 19.095], [72.980, 19.060]
          ]
        ]
      }
    },
    {
      type: "Feature",
      id: "NM-BELAPUR",
      properties: {
        id: "NM-BELAPUR",
        name: "CBD Belapur (Marina Core)",
        tier: "area",
        type: "Administrative & Marine Core",
        center: [73.0400, 19.0178],
        camera_zoom: 14.5,
        camera_pitch: 60,
        camera_bearing: 40,
        neighbors: ["NM-NERUL", "NM-KHARGHAR", "NM-PANVEL"],
        forest_cover_pct: 32.0,
        forest_area_sqkm: 5.4,
        water_bodies_count: 6,
        tree_count_millions: 0.95,
        groundwater_depth_m: 4.5,
        monitoring_stations_count: 3,
        sensor_id: "SEN-NM-BLP-02",
        description: "Government headquarters and Belapur Creek harbour. Baseline water quality anchor."
      },
      geometry: {
        type: "Polygon",
        coordinates: [
          [
            [73.025, 19.005], [73.055, 19.005], [73.060, 19.035], [73.030, 19.035], [73.025, 19.005]
          ]
        ]
      }
    },
    {
      type: "Feature",
      id: "NM-NERUL",
      properties: {
        id: "NM-NERUL",
        name: "Nerul (Palm Beach Lake)",
        tier: "area",
        type: "Residential & Ecological Reserve",
        center: [73.0150, 19.0330],
        camera_zoom: 14.3,
        camera_pitch: 55,
        camera_bearing: 20,
        neighbors: ["NM-VASHI", "NM-BELAPUR", "NM-KHARGHAR"],
        forest_cover_pct: 35.8,
        forest_area_sqkm: 6.1,
        water_bodies_count: 8,
        tree_count_millions: 1.20,
        groundwater_depth_m: 4.1,
        monitoring_stations_count: 2,
        sensor_id: "SEN-NM-NRL-03",
        description: "Jewel of Navi Mumbai lake wetland and Palm Beach residential corridor."
      },
      geometry: {
        type: "Polygon",
        coordinates: [
          [
            [73.000, 19.020], [73.030, 19.020], [73.035, 19.055], [73.005, 19.055], [73.000, 19.020]
          ]
        ]
      }
    },
    {
      type: "Feature",
      id: "NM-KHARGHAR",
      properties: {
        id: "NM-KHARGHAR",
        name: "Kharghar (Valley Buffer)",
        tier: "area",
        type: "Educational & Green Corridor",
        center: [73.0699, 19.0473],
        camera_zoom: 14.0,
        camera_pitch: 52,
        camera_bearing: -15,
        neighbors: ["NM-BELAPUR", "NM-NERUL", "NM-TALOJA", "NM-PANVEL"],
        forest_cover_pct: 48.2,
        forest_area_sqkm: 14.2,
        water_bodies_count: 9,
        tree_count_millions: 2.40,
        groundwater_depth_m: 5.1,
        monitoring_stations_count: 2,
        sensor_id: "SEN-NM-KHG-04",
        description: "Pandavkada hills valley buffer and Central Park green lungs. Lowest historical BOD."
      },
      geometry: {
        type: "Polygon",
        coordinates: [
          [
            [73.050, 19.035], [73.090, 19.035], [73.095, 19.075], [73.055, 19.075], [73.050, 19.035]
          ]
        ]
      }
    },
    {
      type: "Feature",
      id: "NM-AIROLI",
      properties: {
        id: "NM-AIROLI",
        name: "Airoli (TTC Tech corridor)",
        tier: "area",
        type: "Technology & Creek Bridge Nexus",
        center: [72.9980, 19.1550],
        camera_zoom: 14.2,
        camera_pitch: 56,
        camera_bearing: 10,
        neighbors: ["NM-MAHAPE", "NM-GHANSOLI"],
        forest_cover_pct: 18.0,
        forest_area_sqkm: 3.2,
        water_bodies_count: 5,
        tree_count_millions: 0.65,
        groundwater_depth_m: 4.8,
        monitoring_stations_count: 2,
        sensor_id: "SEN-NM-ARL-05",
        description: "Gateway bridge to Mulund and northern TTC tech parks. Monitored for ambient particulate loads."
      },
      geometry: {
        type: "Polygon",
        coordinates: [
          [
            [72.980, 19.140], [73.015, 19.140], [73.020, 19.180], [72.985, 19.180], [72.980, 19.140]
          ]
        ]
      }
    },
    {
      type: "Feature",
      id: "NM-MAHAPE",
      properties: {
        id: "NM-MAHAPE",
        name: "Mahape (MIDC Industrial)",
        tier: "area",
        type: "Heavy Industrial & Chemical Zone",
        center: [73.0230, 19.1120],
        camera_zoom: 14.5,
        camera_pitch: 62,
        camera_bearing: 45,
        neighbors: ["NM-AIROLI", "NM-KOPARKH", "NM-GHANSOLI", "NM-TALOJA"],
        forest_cover_pct: 8.5,
        forest_area_sqkm: 1.4,
        water_bodies_count: 3,
        tree_count_millions: 0.28,
        groundwater_depth_m: 6.8,
        monitoring_stations_count: 3,
        sensor_id: "SEN-NM-MHP-06",
        description: "High-density MIDC manufacturing and chemical processing cluster. Frequent COD/BOD alert triggers."
      },
      geometry: {
        type: "Polygon",
        coordinates: [
          [
            [73.010, 19.095], [73.045, 19.095], [73.050, 19.135], [73.015, 19.135], [73.010, 19.095]
          ]
        ]
      }
    },
    {
      type: "Feature",
      id: "NM-KOPARKH",
      properties: {
        id: "NM-KOPARKH",
        name: "Kopar Khairane (Ind/Res)",
        tier: "area",
        type: "Mixed Industrial & Residential",
        center: [73.0070, 19.0980],
        camera_zoom: 14.2,
        camera_pitch: 55,
        camera_bearing: 25,
        neighbors: ["NM-MAHAPE", "NM-VASHI", "NM-GHANSOLI"],
        forest_cover_pct: 12.2,
        forest_area_sqkm: 2.1,
        water_bodies_count: 4,
        tree_count_millions: 0.38,
        groundwater_depth_m: 5.4,
        monitoring_stations_count: 2,
        sensor_id: "SEN-NM-KPK-07",
        description: "Buffer zone between TTC industrial belt and high-density residential wards."
      },
      geometry: {
        type: "Polygon",
        coordinates: [
          [
            [72.990, 19.085], [73.025, 19.085], [73.030, 19.115], [72.995, 19.115], [72.990, 19.085]
          ]
        ]
      }
    },
    {
      type: "Feature",
      id: "NM-TALOJA",
      properties: {
        id: "NM-TALOJA",
        name: "Taloja (Chemical Belt)",
        tier: "area",
        type: "Special Chemical & Effluent MIDC",
        center: [73.1250, 19.0550],
        camera_zoom: 14.3,
        camera_pitch: 60,
        camera_bearing: -35,
        neighbors: ["NM-MAHAPE", "NM-KHARGHAR", "NM-PANVEL"],
        forest_cover_pct: 11.0,
        forest_area_sqkm: 2.6,
        water_bodies_count: 4,
        tree_count_millions: 0.32,
        groundwater_depth_m: 7.2,
        monitoring_stations_count: 3,
        sensor_id: "SEN-NM-TLJ-08",
        description: "Major industrial CETP effluent treatment site and heavy chemical manufacturing hub."
      },
      geometry: {
        type: "Polygon",
        coordinates: [
          [
            [73.100, 19.035], [73.155, 19.035], [73.160, 19.080], [73.105, 19.080], [73.100, 19.035]
          ]
        ]
      }
    },
    {
      type: "Feature",
      id: "NM-GHANSOLI",
      properties: {
        id: "NM-GHANSOLI",
        name: "Ghansoli (Creek Side)",
        tier: "area",
        type: "Residential & Tech Node",
        center: [73.0030, 19.1280],
        camera_zoom: 14.2,
        camera_pitch: 54,
        camera_bearing: 15,
        neighbors: ["NM-AIROLI", "NM-MAHAPE", "NM-KOPARKH"],
        forest_cover_pct: 22.4,
        forest_area_sqkm: 4.1,
        water_bodies_count: 6,
        tree_count_millions: 0.72,
        groundwater_depth_m: 4.2,
        monitoring_stations_count: 2,
        sensor_id: "SEN-NM-GNS-09",
        description: "Reliance corporate park & residential sectors along Thane Creek mangrove belt."
      },
      geometry: {
        type: "Polygon",
        coordinates: [
          [
            [72.985, 19.115], [73.020, 19.115], [73.025, 19.145], [72.990, 19.145], [72.985, 19.115]
          ]
        ]
      }
    },
    {
      type: "Feature",
      id: "NM-PANVEL",
      properties: {
        id: "NM-PANVEL",
        name: "Panvel (Sub-Urban Node)",
        tier: "area",
        type: "Suburban & Transit Node",
        center: [73.1175, 18.9894],
        camera_zoom: 13.8,
        camera_pitch: 48,
        camera_bearing: -20,
        neighbors: ["NM-BELAPUR", "NM-KHARGHAR", "NM-TALOJA"],
        forest_cover_pct: 31.5,
        forest_area_sqkm: 8.4,
        water_bodies_count: 10,
        tree_count_millions: 1.65,
        groundwater_depth_m: 5.0,
        monitoring_stations_count: 2,
        sensor_id: "SEN-NM-PNV-10",
        description: "Southern gateway to Konkan and new Navi Mumbai International Airport influence zone."
      },
      geometry: {
        type: "Polygon",
        coordinates: [
          [
            [73.090, 18.965], [73.145, 18.965], [73.150, 19.015], [73.095, 19.015], [73.090, 18.965]
          ]
        ]
      }
    }
  ]
};
