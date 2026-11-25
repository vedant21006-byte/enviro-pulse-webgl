"""
EnviroPulse 3D - All-India Multi-Tier Environmental Intelligence Platform
FastAPI + asyncio WebSockets for 60 FPS GPU-Accelerated Dashboard
Supports 3-Tier Hierarchical Drill-Down (State -> City -> Area) across ALL major Indian States.
"""

import os
import sys
import time
import math
import random
import asyncio
import logging
from typing import Dict, List, Optional, Set
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] EnviroPulseCore: %(message)s")
logger = logging.getLogger("EnviroPulseCore")

# -----------------------------------------------------------------------------
# Pydantic Schemas
# -----------------------------------------------------------------------------

class NaturalResources(BaseModel):
    forest_cover_pct: float
    forest_area_sqkm: float
    water_bodies_count: int
    tree_count_millions: float
    groundwater_depth_m: float
    monitoring_stations_count: int

class EntityTelemetry(BaseModel):
    id: str
    name: str
    tier: str  # 'state' | 'city' | 'area'
    parent_id: Optional[str] = None
    type: str
    lat: float
    lng: float
    camera_zoom: float
    camera_pitch: float
    camera_bearing: float
    neighbors: List[str] = []
    
    # Water Parameters
    bod: float
    cod: float
    do: float
    ph: float
    water_flow_mld: float
    water_temp_c: float
    
    # Air Parameters
    aqi: int
    pm25: float
    pm10: float
    no2: float
    so2: float
    air_temp_c: float
    
    # Natural Resources
    resources: NaturalResources
    status: str  # 'CRITICAL' | 'ELEVATED' | 'NORMAL'

class AlertEvent(BaseModel):
    id: str
    timestamp: float
    region_id: str
    region_name: str
    parameter: str
    value: float
    threshold: float
    severity: str
    message: str

class BroadcastPayload(BaseModel):
    timestamp: float
    sequence: int
    states: Dict[str, EntityTelemetry]
    cities: Dict[str, EntityTelemetry]
    areas: Dict[str, EntityTelemetry]
    active_alerts: List[AlertEvent]
    global_stats: Dict[str, float]

# -----------------------------------------------------------------------------
# Data Store with Complete All-India States, Cities, and Micro-Areas
# -----------------------------------------------------------------------------

class MultiTierDataManager:
    def __init__(self):
        self.sequence = 0
        self.active_connections: Set[WebSocket] = set()
        self.alerts: List[AlertEvent] = []
        
        # 1. TIER 1: All Major Indian States
        self.states_data = {
            "IN-MH": {
                "name": "Maharashtra", "tier": "state", "type": "Western Peninsular State",
                "lat": 19.7515, "lng": 75.7139, "zoom": 6.8, "pitch": 32, "bearing": -10,
                "neighbors": ["IN-GJ", "IN-MP", "IN-TG", "IN-KA"],
                "bod": 8.4, "cod": 42.0, "do": 5.8, "ph": 7.4, "water_flow": 320.0, "water_temp": 27.5,
                "aqi": 165, "pm25": 72.0, "pm10": 138.0, "no2": 38.0, "so2": 18.5, "air_temp": 30.2,
                "forest_cover_pct": 20.13, "forest_area_sqkm": 61952.0, "water_bodies": 14200, "trees_m": 420.5, "gw_depth": 8.4, "stations": 92
            },
            "IN-GJ": {
                "name": "Gujarat", "tier": "state", "type": "Western Coastal State",
                "lat": 22.2587, "lng": 71.1924, "zoom": 6.8, "pitch": 30, "bearing": 0,
                "neighbors": ["IN-MH", "IN-RJ", "IN-MP"],
                "bod": 9.2, "cod": 48.0, "do": 5.4, "ph": 7.6, "water_flow": 280.0, "water_temp": 28.0,
                "aqi": 148, "pm25": 65.0, "pm10": 125.0, "no2": 34.0, "so2": 22.0, "air_temp": 33.0,
                "forest_cover_pct": 11.03, "forest_area_sqkm": 21644.0, "water_bodies": 11500, "trees_m": 260.0, "gw_depth": 14.2, "stations": 64
            },
            "IN-KA": {
                "name": "Karnataka", "tier": "state", "type": "Southern Plateau State",
                "lat": 15.3173, "lng": 75.7139, "zoom": 6.8, "pitch": 25, "bearing": 0,
                "neighbors": ["IN-MH", "IN-TG", "IN-TN", "IN-KL"],
                "bod": 6.1, "cod": 32.0, "do": 6.5, "ph": 7.3, "water_flow": 240.0, "water_temp": 25.8,
                "aqi": 95, "pm25": 38.0, "pm10": 78.0, "no2": 22.0, "so2": 12.0, "air_temp": 27.4,
                "forest_cover_pct": 20.11, "forest_area_sqkm": 38575.0, "water_bodies": 16800, "trees_m": 380.0, "gw_depth": 7.8, "stations": 58
            },
            "IN-DL": {
                "name": "Delhi (NCT)", "tier": "state", "type": "National Capital Region",
                "lat": 28.7041, "lng": 77.1025, "zoom": 10.2, "pitch": 40, "bearing": 0,
                "neighbors": ["IN-UP", "IN-RJ"],
                "bod": 14.8, "cod": 78.5, "do": 3.1, "ph": 7.9, "water_flow": 180.0, "water_temp": 26.0,
                "aqi": 285, "pm25": 142.0, "pm10": 265.0, "no2": 62.0, "so2": 28.0, "air_temp": 32.5,
                "forest_cover_pct": 13.15, "forest_area_sqkm": 195.0, "water_bodies": 620, "trees_m": 18.5, "gw_depth": 18.5, "stations": 42
            },
            "IN-TN": {
                "name": "Tamil Nadu", "tier": "state", "type": "Southern Coastal State",
                "lat": 11.1271, "lng": 78.6569, "zoom": 6.8, "pitch": 28, "bearing": 0,
                "neighbors": ["IN-KA", "IN-KL", "IN-TG"],
                "bod": 7.8, "cod": 39.0, "do": 6.0, "ph": 7.5, "water_flow": 260.0, "water_temp": 28.5,
                "aqi": 115, "pm25": 48.0, "pm10": 94.0, "no2": 26.0, "so2": 15.0, "air_temp": 31.0,
                "forest_cover_pct": 20.31, "forest_area_sqkm": 26419.0, "water_bodies": 18900, "trees_m": 340.0, "gw_depth": 9.2, "stations": 60
            },
            "IN-TG": {
                "name": "Telangana", "tier": "state", "type": "Deccan Plateau State",
                "lat": 18.1124, "lng": 79.0193, "zoom": 6.8, "pitch": 30, "bearing": 0,
                "neighbors": ["IN-MH", "IN-KA", "IN-TN"],
                "bod": 8.0, "cod": 41.0, "do": 5.7, "ph": 7.5, "water_flow": 220.0, "water_temp": 28.0,
                "aqi": 128, "pm25": 54.0, "pm10": 108.0, "no2": 30.0, "so2": 16.0, "air_temp": 32.0,
                "forest_cover_pct": 24.00, "forest_area_sqkm": 26969.0, "water_bodies": 15200, "trees_m": 290.0, "gw_depth": 10.1, "stations": 48
            },
            "IN-WB": {
                "name": "West Bengal", "tier": "state", "type": "Eastern Coastal State",
                "lat": 22.9868, "lng": 87.8550, "zoom": 6.8, "pitch": 25, "bearing": 0,
                "neighbors": ["IN-UP", "IN-MP"],
                "bod": 10.4, "cod": 54.0, "do": 4.9, "ph": 7.7, "water_flow": 380.0, "water_temp": 27.0,
                "aqi": 178, "pm25": 82.0, "pm10": 156.0, "no2": 44.0, "so2": 24.0, "air_temp": 29.8,
                "forest_cover_pct": 19.04, "forest_area_sqkm": 16902.0, "water_bodies": 28400, "trees_m": 210.0, "gw_depth": 5.4, "stations": 52
            },
            "IN-UP": {
                "name": "Uttar Pradesh", "tier": "state", "type": "Northern Gangetic Plain",
                "lat": 26.8467, "lng": 80.9462, "zoom": 6.8, "pitch": 25, "bearing": 0,
                "neighbors": ["IN-DL", "IN-MP", "IN-RJ", "IN-WB"],
                "bod": 12.5, "cod": 64.0, "do": 4.2, "ph": 7.8, "water_flow": 410.0, "water_temp": 26.5,
                "aqi": 242, "pm25": 118.0, "pm10": 228.0, "no2": 52.0, "so2": 26.0, "air_temp": 32.0,
                "forest_cover_pct": 6.15, "forest_area_sqkm": 14818.0, "water_bodies": 24500, "trees_m": 310.0, "gw_depth": 11.8, "stations": 78
            },
            "IN-MP": {
                "name": "Madhya Pradesh", "tier": "state", "type": "Central Forest Heartland",
                "lat": 22.9734, "lng": 78.6569, "zoom": 6.8, "pitch": 25, "bearing": 0,
                "neighbors": ["IN-MH", "IN-UP", "IN-GJ", "IN-RJ"],
                "bod": 5.9, "cod": 29.0, "do": 6.8, "ph": 7.3, "water_flow": 310.0, "water_temp": 26.0,
                "aqi": 102, "pm25": 44.0, "pm10": 86.0, "no2": 24.0, "so2": 11.5, "air_temp": 30.5,
                "forest_cover_pct": 25.14, "forest_area_sqkm": 77493.0, "water_bodies": 21000, "trees_m": 540.0, "gw_depth": 8.9, "stations": 55
            },
            "IN-RJ": {
                "name": "Rajasthan", "tier": "state", "type": "Northwestern Desert State",
                "lat": 27.0238, "lng": 74.2179, "zoom": 6.8, "pitch": 25, "bearing": 0,
                "neighbors": ["IN-GJ", "IN-MP", "IN-UP", "IN-DL"],
                "bod": 6.8, "cod": 35.0, "do": 6.2, "ph": 7.6, "water_flow": 160.0, "water_temp": 27.8,
                "aqi": 155, "pm25": 68.0, "pm10": 152.0, "no2": 32.0, "so2": 18.0, "air_temp": 35.2,
                "forest_cover_pct": 4.87, "forest_area_sqkm": 16655.0, "water_bodies": 8900, "trees_m": 140.0, "gw_depth": 24.5, "stations": 46
            },
            "IN-KL": {
                "name": "Kerala", "tier": "state", "type": "Southwestern Coastal Tropical",
                "lat": 10.8505, "lng": 76.2711, "zoom": 7.2, "pitch": 30, "bearing": 0,
                "neighbors": ["IN-TN", "IN-KA"],
                "bod": 3.9, "cod": 19.5, "do": 7.8, "ph": 7.1, "water_flow": 290.0, "water_temp": 26.5,
                "aqi": 62, "pm25": 22.0, "pm10": 48.0, "no2": 14.0, "so2": 8.0, "air_temp": 28.0,
                "forest_cover_pct": 54.70, "forest_area_sqkm": 21253.0, "water_bodies": 12800, "trees_m": 390.0, "gw_depth": 4.2, "stations": 38
            }
        }

        # 2. TIER 2: Major Cities Across All 11 States
        self.cities_data = {
            # Maharashtra
            "MH-NM": {
                "name": "Navi Mumbai", "tier": "city", "parent_id": "IN-MH", "type": "Planned Industrial & Metro Port",
                "lat": 19.0330, "lng": 73.0297, "zoom": 12.2, "pitch": 50, "bearing": 25,
                "neighbors": ["MH-MUM", "MH-TH", "MH-PU"],
                "bod": 10.8, "cod": 56.0, "do": 4.9, "ph": 7.6, "water_flow": 280.0, "water_temp": 28.2,
                "aqi": 172, "pm25": 78.0, "pm10": 152.0, "no2": 44.0, "so2": 22.0, "air_temp": 31.0,
                "forest_cover_pct": 28.5, "forest_area_sqkm": 98.0, "water_bodies": 48, "trees_m": 12.4, "gw_depth": 5.8, "stations": 14
            },
            "MH-MUM": {
                "name": "Mumbai City", "tier": "city", "parent_id": "IN-MH", "type": "Island City Financial Capital",
                "lat": 18.9220, "lng": 72.8347, "zoom": 12.0, "pitch": 45, "bearing": 0,
                "neighbors": ["MH-NM", "MH-TH"],
                "bod": 11.5, "cod": 62.0, "do": 4.5, "ph": 7.7, "water_flow": 410.0, "water_temp": 28.0,
                "aqi": 185, "pm25": 84.0, "pm10": 160.0, "no2": 48.0, "so2": 24.0, "air_temp": 30.5,
                "forest_cover_pct": 14.2, "forest_area_sqkm": 42.0, "water_bodies": 24, "trees_m": 8.5, "gw_depth": 3.8, "stations": 22
            },
            "MH-TH": {
                "name": "Thane", "tier": "city", "parent_id": "IN-MH", "type": "Industrial & Lake District",
                "lat": 19.2183, "lng": 72.9781, "zoom": 12.0, "pitch": 40, "bearing": 0,
                "neighbors": ["MH-NM", "MH-MUM", "MH-PU"],
                "bod": 9.4, "cod": 48.0, "do": 5.2, "ph": 7.5, "water_flow": 230.0, "water_temp": 27.8,
                "aqi": 158, "pm25": 68.0, "pm10": 134.0, "no2": 36.0, "so2": 19.0, "air_temp": 30.0,
                "forest_cover_pct": 34.0, "forest_area_sqkm": 840.0, "water_bodies": 65, "trees_m": 24.0, "gw_depth": 6.2, "stations": 12
            },
            "MH-PU": {
                "name": "Pune", "tier": "city", "parent_id": "IN-MH", "type": "Automotive & IT Hub",
                "lat": 18.5204, "lng": 73.8567, "zoom": 12.0, "pitch": 42, "bearing": 10,
                "neighbors": ["MH-NM", "MH-TH"],
                "bod": 7.9, "cod": 41.0, "do": 6.2, "ph": 7.3, "water_flow": 290.0, "water_temp": 25.5,
                "aqi": 132, "pm25": 56.0, "pm10": 112.0, "no2": 32.0, "so2": 14.5, "air_temp": 28.5,
                "forest_cover_pct": 12.8, "forest_area_sqkm": 2004.0, "water_bodies": 84, "trees_m": 48.0, "gw_depth": 7.1, "stations": 20
            },
            # Delhi NCT
            "DL-ND": {
                "name": "New Delhi", "tier": "city", "parent_id": "IN-DL", "type": "Government Core & Green Buffer",
                "lat": 28.6139, "lng": 77.2090, "zoom": 12.2, "pitch": 45, "bearing": 0,
                "neighbors": ["DL-SO", "DL-NO"],
                "bod": 12.8, "cod": 68.0, "do": 3.8, "ph": 7.8, "water_flow": 120.0, "water_temp": 26.5,
                "aqi": 245, "pm25": 128.0, "pm10": 235.0, "no2": 54.0, "so2": 22.0, "air_temp": 31.8,
                "forest_cover_pct": 18.2, "forest_area_sqkm": 35.0, "water_bodies": 120, "trees_m": 4.2, "gw_depth": 16.5, "stations": 12
            },
            "DL-SO": {
                "name": "South Delhi", "tier": "city", "parent_id": "IN-DL", "type": "Mixed Tech & Commercial District",
                "lat": 28.4817, "lng": 77.1873, "zoom": 12.0, "pitch": 45, "bearing": 0,
                "neighbors": ["DL-ND", "DL-NO"],
                "bod": 13.9, "cod": 74.0, "do": 3.2, "ph": 7.9, "water_flow": 145.0, "water_temp": 26.2,
                "aqi": 272, "pm25": 138.0, "pm10": 255.0, "no2": 58.0, "so2": 26.0, "air_temp": 32.2,
                "forest_cover_pct": 16.5, "forest_area_sqkm": 42.0, "water_bodies": 140, "trees_m": 4.8, "gw_depth": 19.8, "stations": 14
            },
            "DL-NO": {
                "name": "North Delhi", "tier": "city", "parent_id": "IN-DL", "type": "Yamuna River Basin & Transport",
                "lat": 28.7200, "lng": 77.1600, "zoom": 12.0, "pitch": 40, "bearing": 0,
                "neighbors": ["DL-ND", "DL-SO"],
                "bod": 16.2, "cod": 84.0, "do": 2.4, "ph": 8.1, "water_flow": 190.0, "water_temp": 26.0,
                "aqi": 298, "pm25": 156.0, "pm10": 280.0, "no2": 66.0, "so2": 31.0, "air_temp": 32.5,
                "forest_cover_pct": 9.4, "forest_area_sqkm": 24.0, "water_bodies": 85, "trees_m": 3.1, "gw_depth": 21.0, "stations": 11
            },
            # Gujarat
            "GJ-AHM": {
                "name": "Ahmedabad", "tier": "city", "parent_id": "IN-GJ", "type": "Commercial & Textile Metro",
                "lat": 23.0225, "lng": 72.5714, "zoom": 11.8, "pitch": 40, "bearing": 0,
                "neighbors": ["GJ-SUR", "GJ-BRD"],
                "bod": 10.8, "cod": 58.0, "do": 4.8, "ph": 7.7, "water_flow": 260.0, "water_temp": 28.5,
                "aqi": 168, "pm25": 78.0, "pm10": 154.0, "no2": 39.0, "so2": 24.0, "air_temp": 34.0,
                "forest_cover_pct": 8.4, "forest_area_sqkm": 68.0, "water_bodies": 38, "trees_m": 7.5, "gw_depth": 15.2, "stations": 16
            },
            "GJ-SUR": {
                "name": "Surat", "tier": "city", "parent_id": "IN-GJ", "type": "Textile & Diamond Port City",
                "lat": 21.1702, "lng": 72.8311, "zoom": 11.8, "pitch": 38, "bearing": 0,
                "neighbors": ["GJ-AHM", "GJ-BRD"],
                "bod": 9.4, "cod": 49.0, "do": 5.5, "ph": 7.5, "water_flow": 240.0, "water_temp": 28.2,
                "aqi": 142, "pm25": 62.0, "pm10": 120.0, "no2": 32.0, "so2": 20.0, "air_temp": 32.8,
                "forest_cover_pct": 12.2, "forest_area_sqkm": 110.0, "water_bodies": 46, "trees_m": 9.8, "gw_depth": 11.4, "stations": 12
            },
            "GJ-BRD": {
                "name": "Vadodara", "tier": "city", "parent_id": "IN-GJ", "type": "Chemical & Petrochemical Hub",
                "lat": 22.3072, "lng": 73.1812, "zoom": 11.8, "pitch": 38, "bearing": 0,
                "neighbors": ["GJ-AHM", "GJ-SUR"],
                "bod": 10.2, "cod": 55.0, "do": 5.0, "ph": 7.6, "water_flow": 210.0, "water_temp": 28.0,
                "aqi": 152, "pm25": 66.0, "pm10": 130.0, "no2": 35.0, "so2": 23.0, "air_temp": 33.5,
                "forest_cover_pct": 13.5, "forest_area_sqkm": 145.0, "water_bodies": 40, "trees_m": 8.2, "gw_depth": 13.0, "stations": 10
            },
            # Karnataka
            "KA-BLR": {
                "name": "Bengaluru Urban", "tier": "city", "parent_id": "IN-KA", "type": "Silicon Valley IT Metro",
                "lat": 12.9716, "lng": 77.5946, "zoom": 12.0, "pitch": 48, "bearing": 15,
                "neighbors": ["KA-MYS"],
                "bod": 8.8, "cod": 44.0, "do": 5.9, "ph": 7.4, "water_flow": 310.0, "water_temp": 24.8,
                "aqi": 105, "pm25": 44.0, "pm10": 88.0, "no2": 28.0, "so2": 11.0, "air_temp": 26.5,
                "forest_cover_pct": 14.8, "forest_area_sqkm": 324.0, "water_bodies": 182, "trees_m": 18.4, "gw_depth": 12.1, "stations": 24
            },
            "KA-MYS": {
                "name": "Mysuru", "tier": "city", "parent_id": "IN-KA", "type": "Heritage Clean City",
                "lat": 12.2958, "lng": 76.6394, "zoom": 11.5, "pitch": 30, "bearing": 0,
                "neighbors": ["KA-BLR"],
                "bod": 4.5, "cod": 22.0, "do": 7.2, "ph": 7.2, "water_flow": 140.0, "water_temp": 24.2,
                "aqi": 72, "pm25": 28.0, "pm10": 58.0, "no2": 18.0, "so2": 8.0, "air_temp": 25.8,
                "forest_cover_pct": 24.5, "forest_area_sqkm": 1560.0, "water_bodies": 94, "trees_m": 26.0, "gw_depth": 6.8, "stations": 8
            },
            # Tamil Nadu
            "TN-CHN": {
                "name": "Chennai", "tier": "city", "parent_id": "IN-TN", "type": "Automotive & Port Metro",
                "lat": 13.0827, "lng": 80.2707, "zoom": 11.8, "pitch": 42, "bearing": 0,
                "neighbors": ["TN-CBE"],
                "bod": 9.2, "cod": 46.0, "do": 5.6, "ph": 7.6, "water_flow": 280.0, "water_temp": 29.5,
                "aqi": 118, "pm25": 52.0, "pm10": 98.0, "no2": 29.0, "so2": 17.0, "air_temp": 32.5,
                "forest_cover_pct": 15.2, "forest_area_sqkm": 64.0, "water_bodies": 68, "trees_m": 8.9, "gw_depth": 7.4, "stations": 18
            },
            "TN-CBE": {
                "name": "Coimbatore", "tier": "city", "parent_id": "IN-TN", "type": "Textile & Pump Engineering Core",
                "lat": 11.0168, "lng": 76.9558, "zoom": 11.5, "pitch": 32, "bearing": 0,
                "neighbors": ["TN-CHN"],
                "bod": 6.8, "cod": 34.0, "do": 6.4, "ph": 7.4, "water_flow": 180.0, "water_temp": 26.8,
                "aqi": 88, "pm25": 36.0, "pm10": 74.0, "no2": 21.0, "so2": 10.0, "air_temp": 28.0,
                "forest_cover_pct": 22.0, "forest_area_sqkm": 1100.0, "water_bodies": 54, "trees_m": 15.2, "gw_depth": 8.1, "stations": 10
            },
            # Telangana
            "TG-HYD": {
                "name": "Hyderabad", "tier": "city", "parent_id": "IN-TG", "type": "IT & Bulk Drug Pharma Metro",
                "lat": 17.3850, "lng": 78.4867, "zoom": 11.8, "pitch": 45, "bearing": 10,
                "neighbors": ["TG-WRG"],
                "bod": 8.9, "cod": 45.0, "do": 5.4, "ph": 7.5, "water_flow": 270.0, "water_temp": 28.0,
                "aqi": 138, "pm25": 58.0, "pm10": 118.0, "no2": 32.0, "so2": 16.0, "air_temp": 32.0,
                "forest_cover_pct": 12.6, "forest_area_sqkm": 82.0, "water_bodies": 74, "trees_m": 14.5, "gw_depth": 8.8, "stations": 20
            },
            "TG-WRG": {
                "name": "Warangal", "tier": "city", "parent_id": "IN-TG", "type": "Historical Agro-Industrial City",
                "lat": 17.9689, "lng": 79.5941, "zoom": 11.5, "pitch": 30, "bearing": 0,
                "neighbors": ["TG-HYD"],
                "bod": 5.9, "cod": 30.0, "do": 6.5, "ph": 7.3, "water_flow": 120.0, "water_temp": 27.5,
                "aqi": 92, "pm25": 38.0, "pm10": 80.0, "no2": 22.0, "so2": 11.0, "air_temp": 31.5,
                "forest_cover_pct": 28.5, "forest_area_sqkm": 860.0, "water_bodies": 88, "trees_m": 18.0, "gw_depth": 7.6, "stations": 8
            },
            # West Bengal
            "WB-KOL": {
                "name": "Kolkata", "tier": "city", "parent_id": "IN-WB", "type": "Riverine Cultural Metro",
                "lat": 22.5726, "lng": 88.3639, "zoom": 11.8, "pitch": 40, "bearing": 0,
                "neighbors": ["WB-HWH"],
                "bod": 11.8, "cod": 61.0, "do": 4.2, "ph": 7.7, "water_flow": 360.0, "water_temp": 27.5,
                "aqi": 198, "pm25": 92.0, "pm10": 172.0, "no2": 48.0, "so2": 26.0, "air_temp": 30.2,
                "forest_cover_pct": 10.4, "forest_area_sqkm": 21.0, "water_bodies": 160, "trees_m": 5.4, "gw_depth": 4.5, "stations": 16
            },
            "WB-HWH": {
                "name": "Howrah", "tier": "city", "parent_id": "IN-WB", "type": "Industrial Foundries & Port Gateway",
                "lat": 22.5958, "lng": 88.2636, "zoom": 11.8, "pitch": 38, "bearing": 0,
                "neighbors": ["WB-KOL"],
                "bod": 12.4, "cod": 66.0, "do": 3.9, "ph": 7.8, "water_flow": 240.0, "water_temp": 27.8,
                "aqi": 215, "pm25": 105.0, "pm10": 195.0, "no2": 52.0, "so2": 28.0, "air_temp": 30.5,
                "forest_cover_pct": 8.2, "forest_area_sqkm": 18.0, "water_bodies": 95, "trees_m": 4.1, "gw_depth": 4.8, "stations": 10
            },
            # Uttar Pradesh
            "UP-NOI": {
                "name": "Noida", "tier": "city", "parent_id": "IN-UP", "type": "Industrial & Tech NCR Node",
                "lat": 28.5355, "lng": 77.3910, "zoom": 12.0, "pitch": 46, "bearing": 15,
                "neighbors": ["UP-KNP", "UP-LKO", "DL-ND"],
                "bod": 14.2, "cod": 74.0, "do": 3.4, "ph": 7.9, "water_flow": 160.0, "water_temp": 26.5,
                "aqi": 268, "pm25": 134.0, "pm10": 248.0, "no2": 56.0, "so2": 27.0, "air_temp": 32.5,
                "forest_cover_pct": 9.8, "forest_area_sqkm": 38.0, "water_bodies": 42, "trees_m": 3.8, "gw_depth": 14.8, "stations": 12
            },
            "UP-KNP": {
                "name": "Kanpur", "tier": "city", "parent_id": "IN-UP", "type": "Leather Tannery & Ganga Basin Core",
                "lat": 26.4499, "lng": 80.3319, "zoom": 11.8, "pitch": 40, "bearing": 0,
                "neighbors": ["UP-NOI", "UP-LKO"],
                "bod": 16.5, "cod": 85.0, "do": 3.1, "ph": 8.2, "water_flow": 280.0, "water_temp": 26.2,
                "aqi": 280, "pm25": 145.0, "pm10": 270.0, "no2": 62.0, "so2": 32.0, "air_temp": 32.0,
                "forest_cover_pct": 5.4, "forest_area_sqkm": 48.0, "water_bodies": 52, "trees_m": 4.9, "gw_depth": 12.5, "stations": 14
            },
            "UP-LKO": {
                "name": "Lucknow", "tier": "city", "parent_id": "IN-UP", "type": "State Administrative Capital",
                "lat": 26.8467, "lng": 80.9462, "zoom": 11.8, "pitch": 35, "bearing": 0,
                "neighbors": ["UP-NOI", "UP-KNP"],
                "bod": 11.0, "cod": 56.0, "do": 4.6, "ph": 7.6, "water_flow": 220.0, "water_temp": 26.0,
                "aqi": 220, "pm25": 110.0, "pm10": 205.0, "no2": 48.0, "so2": 22.0, "air_temp": 31.8,
                "forest_cover_pct": 8.6, "forest_area_sqkm": 72.0, "water_bodies": 68, "trees_m": 6.8, "gw_depth": 10.2, "stations": 12
            },
            # Madhya Pradesh
            "MP-IND": {
                "name": "Indore", "tier": "city", "parent_id": "IN-MP", "type": "Cleanest City & Commercial Hub",
                "lat": 22.7196, "lng": 75.8577, "zoom": 11.8, "pitch": 35, "bearing": 0,
                "neighbors": ["MP-BHP"],
                "bod": 5.8, "cod": 29.0, "do": 6.8, "ph": 7.4, "water_flow": 210.0, "water_temp": 26.0,
                "aqi": 98, "pm25": 42.0, "pm10": 84.0, "no2": 24.0, "so2": 11.0, "air_temp": 29.5,
                "forest_cover_pct": 16.2, "forest_area_sqkm": 148.0, "water_bodies": 56, "trees_m": 12.0, "gw_depth": 8.2, "stations": 14
            },
            "MP-BHP": {
                "name": "Bhopal", "tier": "city", "parent_id": "IN-MP", "type": "City of Lakes & Green Capital",
                "lat": 23.2599, "lng": 77.4126, "zoom": 11.8, "pitch": 35, "bearing": 0,
                "neighbors": ["MP-IND"],
                "bod": 5.2, "cod": 26.0, "do": 7.1, "ph": 7.3, "water_flow": 190.0, "water_temp": 25.5,
                "aqi": 90, "pm25": 38.0, "pm10": 78.0, "no2": 21.0, "so2": 9.5, "air_temp": 29.0,
                "forest_cover_pct": 28.5, "forest_area_sqkm": 420.0, "water_bodies": 72, "trees_m": 19.5, "gw_depth": 6.5, "stations": 12
            },
            # Rajasthan
            "RJ-JPR": {
                "name": "Jaipur", "tier": "city", "parent_id": "IN-RJ", "type": "Pink City & Tourism Metro",
                "lat": 26.9124, "lng": 75.7873, "zoom": 11.8, "pitch": 35, "bearing": 0,
                "neighbors": ["RJ-JDH"],
                "bod": 7.2, "cod": 38.0, "do": 6.1, "ph": 7.6, "water_flow": 180.0, "water_temp": 27.2,
                "aqi": 162, "pm25": 72.0, "pm10": 165.0, "no2": 32.0, "so2": 18.0, "air_temp": 34.5,
                "forest_cover_pct": 8.9, "forest_area_sqkm": 94.0, "water_bodies": 28, "trees_m": 6.4, "gw_depth": 22.4, "stations": 14
            },
            "RJ-JDH": {
                "name": "Jodhpur", "tier": "city", "parent_id": "IN-RJ", "type": "Sun City & Arid Industrial Node",
                "lat": 26.2389, "lng": 73.0243, "zoom": 11.5, "pitch": 30, "bearing": 0,
                "neighbors": ["RJ-JPR"],
                "bod": 8.0, "cod": 42.0, "do": 5.8, "ph": 7.7, "water_flow": 130.0, "water_temp": 28.5,
                "aqi": 175, "pm25": 79.0, "pm10": 178.0, "no2": 34.0, "so2": 19.5, "air_temp": 36.0,
                "forest_cover_pct": 3.8, "forest_area_sqkm": 45.0, "water_bodies": 19, "trees_m": 3.2, "gw_depth": 31.0, "stations": 8
            },
            # Kerala
            "KL-COK": {
                "name": "Kochi", "tier": "city", "parent_id": "IN-KL", "type": "Port & Coastal Commercial Metro",
                "lat": 9.9312, "lng": 76.2673, "zoom": 12.0, "pitch": 40, "bearing": 0,
                "neighbors": ["KL-TVM"],
                "bod": 4.1, "cod": 21.0, "do": 7.6, "ph": 7.2, "water_flow": 220.0, "water_temp": 27.0,
                "aqi": 68, "pm25": 25.0, "pm10": 52.0, "no2": 16.0, "so2": 9.0, "air_temp": 28.5,
                "forest_cover_pct": 42.5, "forest_area_sqkm": 420.0, "water_bodies": 142, "trees_m": 24.5, "gw_depth": 3.8, "stations": 10
            },
            "KL-TVM": {
                "name": "Thiruvananthapuram", "tier": "city", "parent_id": "IN-KL", "type": "Coastal Green Capital",
                "lat": 8.5241, "lng": 76.9366, "zoom": 11.8, "pitch": 35, "bearing": 0,
                "neighbors": ["KL-COK"],
                "bod": 3.6, "cod": 18.0, "do": 8.0, "ph": 7.1, "water_flow": 180.0, "water_temp": 26.5,
                "aqi": 56, "pm25": 19.0, "pm10": 42.0, "no2": 12.0, "so2": 7.0, "air_temp": 27.8,
                "forest_cover_pct": 51.0, "forest_area_sqkm": 580.0, "water_bodies": 98, "trees_m": 28.0, "gw_depth": 4.1, "stations": 8
            }
        }

        # 3. TIER 3: Micro Areas across All States & Cities
        self.areas_data = {
            # Navi Mumbai Wards
            "NM-MAHAPE": {
                "name": "Mahape (MIDC Industrial)", "tier": "area", "parent_id": "MH-NM", "type": "Heavy Chemical & Manufacturing MIDC",
                "lat": 19.1120, "lng": 73.0230, "zoom": 14.5, "pitch": 62, "bearing": 45,
                "neighbors": ["NM-VASHI", "NM-AIROLI", "NM-TALOJA"],
                "bod": 15.8, "cod": 84.0, "do": 3.2, "ph": 8.1, "water_flow": 142.0, "water_temp": 29.1,
                "aqi": 224, "pm25": 108.0, "pm10": 210.0, "no2": 58.0, "so2": 32.0, "air_temp": 32.2,
                "forest_cover_pct": 8.5, "forest_area_sqkm": 1.4, "water_bodies": 3, "trees_m": 0.28, "gw_depth": 6.8, "stations": 3
            },
            "NM-VASHI": {
                "name": "Vashi (Sector 17 / Creek)", "tier": "area", "parent_id": "MH-NM", "type": "Commercial & Estuary Outflow",
                "lat": 19.0771, "lng": 72.9986, "zoom": 14.2, "pitch": 58, "bearing": 30,
                "neighbors": ["NM-MAHAPE", "NM-NERUL", "NM-BELAPUR"],
                "bod": 11.2, "cod": 58.0, "do": 4.5, "ph": 7.6, "water_flow": 115.0, "water_temp": 28.0,
                "aqi": 175, "pm25": 78.0, "pm10": 148.0, "no2": 45.0, "so2": 20.0, "air_temp": 30.6,
                "forest_cover_pct": 14.5, "forest_area_sqkm": 2.8, "water_bodies": 4, "trees_m": 0.45, "gw_depth": 3.9, "stations": 3
            },
            "NM-BELAPUR": {
                "name": "CBD Belapur (Marina Core)", "tier": "area", "parent_id": "MH-NM", "type": "Administrative Marine Core",
                "lat": 19.0178, "lng": 73.0400, "zoom": 14.5, "pitch": 60, "bearing": 40,
                "neighbors": ["NM-NERUL", "NM-KHARGHAR", "NM-VASHI"],
                "bod": 7.4, "cod": 36.0, "do": 6.4, "ph": 7.4, "water_flow": 98.0, "water_temp": 27.4,
                "aqi": 138, "pm25": 58.0, "pm10": 114.0, "no2": 32.0, "so2": 14.0, "air_temp": 30.2,
                "forest_cover_pct": 32.0, "forest_area_sqkm": 5.4, "water_bodies": 6, "trees_m": 0.95, "gw_depth": 4.5, "stations": 3
            },
            "NM-NERUL": {
                "name": "Nerul (Palm Beach Lake)", "tier": "area", "parent_id": "MH-NM", "type": "Residential Wetland Corridor",
                "lat": 19.0330, "lng": 73.0150, "zoom": 14.3, "pitch": 55, "bearing": 20,
                "neighbors": ["NM-VASHI", "NM-BELAPUR", "NM-KHARGHAR"],
                "bod": 6.8, "cod": 32.5, "do": 6.9, "ph": 7.3, "water_flow": 82.0, "water_temp": 27.2,
                "aqi": 128, "pm25": 52.0, "pm10": 104.0, "no2": 28.0, "so2": 12.0, "air_temp": 30.0,
                "forest_cover_pct": 35.8, "forest_area_sqkm": 6.1, "water_bodies": 8, "trees_m": 1.20, "gw_depth": 4.1, "stations": 2
            },
            "NM-KHARGHAR": {
                "name": "Kharghar (Valley Buffer)", "tier": "area", "parent_id": "MH-NM", "type": "Valley Buffer & Green Lungs",
                "lat": 19.0473, "lng": 73.0699, "zoom": 14.0, "pitch": 52, "bearing": -15,
                "neighbors": ["NM-BELAPUR", "NM-NERUL", "NM-TALOJA"],
                "bod": 5.6, "cod": 28.0, "do": 7.2, "ph": 7.2, "water_flow": 74.0, "water_temp": 26.8,
                "aqi": 118, "pm25": 46.0, "pm10": 92.0, "no2": 24.0, "so2": 10.5, "air_temp": 29.5,
                "forest_cover_pct": 48.2, "forest_area_sqkm": 14.2, "water_bodies": 9, "trees_m": 2.40, "gw_depth": 5.1, "stations": 2
            },
            "NM-AIROLI": {
                "name": "Airoli (TTC Tech corridor)", "tier": "area", "parent_id": "MH-NM", "type": "Tech Nexus & Bridge",
                "lat": 19.1550, "lng": 72.9980, "zoom": 14.2, "pitch": 56, "bearing": 10,
                "neighbors": ["NM-MAHAPE", "NM-VASHI"],
                "bod": 10.5, "cod": 54.0, "do": 4.8, "ph": 7.5, "water_flow": 128.0, "water_temp": 28.2,
                "aqi": 182, "pm25": 82.0, "pm10": 156.0, "no2": 48.0, "so2": 22.0, "air_temp": 31.0,
                "forest_cover_pct": 18.0, "forest_area_sqkm": 3.2, "water_bodies": 5, "trees_m": 0.65, "gw_depth": 4.8, "stations": 2
            },
            "NM-TALOJA": {
                "name": "Taloja (Chemical Belt)", "tier": "area", "parent_id": "MH-NM", "type": "Special Chemical CETP Outflow",
                "lat": 19.0550, "lng": 73.1250, "zoom": 14.3, "pitch": 60, "bearing": -35,
                "neighbors": ["NM-MAHAPE", "NM-KHARGHAR"],
                "bod": 18.2, "cod": 96.0, "do": 2.4, "ph": 8.4, "water_flow": 165.0, "water_temp": 29.8,
                "aqi": 258, "pm25": 126.0, "pm10": 245.0, "no2": 66.0, "so2": 38.0, "air_temp": 33.0,
                "forest_cover_pct": 11.0, "forest_area_sqkm": 2.6, "water_bodies": 4, "trees_m": 0.32, "gw_depth": 7.2, "stations": 3
            },
            # Mumbai City
            "MUM-BKC": {
                "name": "BKC (Mithi River Basin)", "tier": "area", "parent_id": "MH-MUM", "type": "Financial Core & Estuary",
                "lat": 19.0650, "lng": 72.8680, "zoom": 14.2, "pitch": 55, "bearing": 15,
                "neighbors": ["MUM-CHEM", "MUM-NP"],
                "bod": 16.5, "cod": 82.0, "do": 2.8, "ph": 7.9, "water_flow": 180.0, "water_temp": 28.5,
                "aqi": 198, "pm25": 92.0, "pm10": 174.0, "no2": 52.0, "so2": 26.0, "air_temp": 31.0,
                "forest_cover_pct": 6.8, "forest_area_sqkm": 1.1, "water_bodies": 3, "trees_m": 0.35, "gw_depth": 3.2, "stations": 3
            },
            "MUM-CHEM": {
                "name": "Chembur Industrial Zone", "tier": "area", "parent_id": "MH-MUM", "type": "Refinery & Petrochemical Core",
                "lat": 19.0520, "lng": 72.8980, "zoom": 14.2, "pitch": 55, "bearing": 20,
                "neighbors": ["MUM-BKC", "NM-VASHI"],
                "bod": 14.8, "cod": 78.0, "do": 3.4, "ph": 8.0, "water_flow": 165.0, "water_temp": 29.0,
                "aqi": 220, "pm25": 105.0, "pm10": 198.0, "no2": 56.0, "so2": 32.0, "air_temp": 32.0,
                "forest_cover_pct": 9.2, "forest_area_sqkm": 1.6, "water_bodies": 2, "trees_m": 0.42, "gw_depth": 4.1, "stations": 3
            },
            "MUM-NP": {
                "name": "Nariman Point Coast", "tier": "area", "parent_id": "MH-MUM", "type": "Coastal Marine Front",
                "lat": 18.9260, "lng": 72.8220, "zoom": 14.4, "pitch": 50, "bearing": 0,
                "neighbors": ["MUM-BKC"],
                "bod": 6.5, "cod": 32.0, "do": 6.8, "ph": 7.5, "water_flow": 120.0, "water_temp": 27.5,
                "aqi": 125, "pm25": 54.0, "pm10": 108.0, "no2": 31.0, "so2": 15.0, "air_temp": 29.8,
                "forest_cover_pct": 11.5, "forest_area_sqkm": 0.8, "water_bodies": 2, "trees_m": 0.25, "gw_depth": 2.8, "stations": 2
            },
            # Pune Wards
            "PU-HINJ": {
                "name": "Hinjewadi Tech Park", "tier": "area", "parent_id": "MH-PU", "type": "High-Tech IT SEZ",
                "lat": 18.5913, "lng": 73.7389, "zoom": 14.2, "pitch": 52, "bearing": 10,
                "neighbors": ["PU-BHOS"],
                "bod": 6.8, "cod": 34.0, "do": 6.6, "ph": 7.3, "water_flow": 110.0, "water_temp": 25.0,
                "aqi": 110, "pm25": 46.0, "pm10": 94.0, "no2": 26.0, "so2": 12.0, "air_temp": 27.5,
                "forest_cover_pct": 21.0, "forest_area_sqkm": 5.8, "water_bodies": 6, "trees_m": 1.10, "gw_depth": 8.2, "stations": 3
            },
            "PU-BHOS": {
                "name": "Bhosari MIDC", "tier": "area", "parent_id": "MH-PU", "type": "Automotive Engineering Cluster",
                "lat": 18.6250, "lng": 73.8450, "zoom": 14.2, "pitch": 58, "bearing": 25,
                "neighbors": ["PU-HINJ"],
                "bod": 13.5, "cod": 68.0, "do": 4.1, "ph": 7.8, "water_flow": 155.0, "water_temp": 26.5,
                "aqi": 185, "pm25": 86.0, "pm10": 168.0, "no2": 46.0, "so2": 24.0, "air_temp": 29.5,
                "forest_cover_pct": 7.5, "forest_area_sqkm": 1.8, "water_bodies": 3, "trees_m": 0.38, "gw_depth": 6.8, "stations": 3
            },
            # Gujarat (Ahmedabad & Surat)
            "AHM-NARODA": {
                "name": "Naroda Industrial GIDC", "tier": "area", "parent_id": "GJ-AHM", "type": "Chemical & Dyes Cluster",
                "lat": 23.0720, "lng": 72.6580, "zoom": 14.4, "pitch": 60, "bearing": 30,
                "neighbors": ["AHM-SGHI", "AHM-VATVA"],
                "bod": 16.2, "cod": 86.0, "do": 3.0, "ph": 8.2, "water_flow": 138.0, "water_temp": 29.4,
                "aqi": 218, "pm25": 102.0, "pm10": 204.0, "no2": 54.0, "so2": 31.0, "air_temp": 34.5,
                "forest_cover_pct": 4.5, "forest_area_sqkm": 0.8, "water_bodies": 2, "trees_m": 0.16, "gw_depth": 18.4, "stations": 3
            },
            "AHM-SGHI": {
                "name": "SG Highway Tech Corridor", "tier": "area", "parent_id": "GJ-AHM", "type": "Commercial IT Corridor",
                "lat": 23.0450, "lng": 72.5100, "zoom": 14.2, "pitch": 52, "bearing": 15,
                "neighbors": ["AHM-NARODA", "AHM-VATVA"],
                "bod": 7.9, "cod": 41.0, "do": 6.0, "ph": 7.4, "water_flow": 86.0, "water_temp": 27.8,
                "aqi": 138, "pm25": 58.0, "pm10": 118.0, "no2": 32.0, "so2": 16.0, "air_temp": 33.2,
                "forest_cover_pct": 16.2, "forest_area_sqkm": 2.9, "water_bodies": 4, "trees_m": 0.62, "gw_depth": 12.8, "stations": 2
            },
            "AHM-VATVA": {
                "name": "Vatva GIDC Chemical Zone", "tier": "area", "parent_id": "GJ-AHM", "type": "Heavy Chemical CETP Zone",
                "lat": 22.9600, "lng": 72.6300, "zoom": 14.2, "pitch": 58, "bearing": 20,
                "neighbors": ["AHM-NARODA", "AHM-SGHI"],
                "bod": 17.5, "cod": 92.0, "do": 2.6, "ph": 8.3, "water_flow": 160.0, "water_temp": 29.8,
                "aqi": 235, "pm25": 115.0, "pm10": 225.0, "no2": 60.0, "so2": 35.0, "air_temp": 35.0,
                "forest_cover_pct": 3.8, "forest_area_sqkm": 0.7, "water_bodies": 2, "trees_m": 0.12, "gw_depth": 19.5, "stations": 3
            },
            "SUR-SACH": {
                "name": "Sachin GIDC Textile Belt", "tier": "area", "parent_id": "GJ-SUR", "type": "Textile Dyeing & CETP Zone",
                "lat": 21.0800, "lng": 72.8800, "zoom": 14.2, "pitch": 55, "bearing": 20,
                "neighbors": ["SUR-ADAJ"],
                "bod": 14.5, "cod": 76.0, "do": 3.5, "ph": 8.0, "water_flow": 145.0, "water_temp": 29.0,
                "aqi": 182, "pm25": 84.0, "pm10": 165.0, "no2": 42.0, "so2": 25.0, "air_temp": 33.5,
                "forest_cover_pct": 6.8, "forest_area_sqkm": 1.2, "water_bodies": 3, "trees_m": 0.28, "gw_depth": 12.0, "stations": 2
            },
            "SUR-ADAJ": {
                "name": "Adajan Tapi Riverfront", "tier": "area", "parent_id": "GJ-SUR", "type": "Riverine Eco Buffer",
                "lat": 21.2000, "lng": 72.7950, "zoom": 14.2, "pitch": 45, "bearing": 0,
                "neighbors": ["SUR-SACH"],
                "bod": 6.2, "cod": 31.0, "do": 6.8, "ph": 7.4, "water_flow": 195.0, "water_temp": 27.5,
                "aqi": 115, "pm25": 48.0, "pm10": 96.0, "no2": 26.0, "so2": 14.0, "air_temp": 32.0,
                "forest_cover_pct": 21.0, "forest_area_sqkm": 3.5, "water_bodies": 5, "trees_m": 0.85, "gw_depth": 9.5, "stations": 2
            },
            # Bengaluru Wards
            "BLR-WHT": {
                "name": "Whitefield (Tech Hub)", "tier": "area", "parent_id": "KA-BLR", "type": "High-Tech IT Corridor",
                "lat": 12.9698, "lng": 77.7500, "zoom": 14.2, "pitch": 55, "bearing": 20,
                "neighbors": ["BLR-KORAM", "BLR-ECITY"],
                "bod": 7.8, "cod": 38.0, "do": 6.2, "ph": 7.4, "water_flow": 95.0, "water_temp": 25.0,
                "aqi": 112, "pm25": 48.0, "pm10": 94.0, "no2": 31.0, "so2": 12.0, "air_temp": 27.2,
                "forest_cover_pct": 22.5, "forest_area_sqkm": 4.8, "water_bodies": 6, "trees_m": 0.82, "gw_depth": 14.5, "stations": 3
            },
            "BLR-PEENYA": {
                "name": "Peenya (Industrial Estate)", "tier": "area", "parent_id": "KA-BLR", "type": "Major Manufacturing Cluster",
                "lat": 13.0285, "lng": 77.5197, "zoom": 14.4, "pitch": 60, "bearing": 35,
                "neighbors": ["BLR-WHT", "BLR-KORAM"],
                "bod": 14.2, "cod": 76.0, "do": 3.6, "ph": 8.0, "water_flow": 135.0, "water_temp": 26.2,
                "aqi": 188, "pm25": 84.0, "pm10": 172.0, "no2": 46.0, "so2": 25.0, "air_temp": 28.5,
                "forest_cover_pct": 6.4, "forest_area_sqkm": 1.2, "water_bodies": 2, "trees_m": 0.22, "gw_depth": 11.2, "stations": 3
            },
            "BLR-KORAM": {
                "name": "Koramangala (Urban Core)", "tier": "area", "parent_id": "KA-BLR", "type": "Commercial & Residential Core",
                "lat": 12.9352, "lng": 77.6245, "zoom": 14.2, "pitch": 50, "bearing": 0,
                "neighbors": ["BLR-WHT", "BLR-PEENYA", "BLR-ECITY"],
                "bod": 6.5, "cod": 32.0, "do": 6.8, "ph": 7.3, "water_flow": 72.0, "water_temp": 24.5,
                "aqi": 92, "pm25": 36.0, "pm10": 74.0, "no2": 24.0, "so2": 9.5, "air_temp": 26.0,
                "forest_cover_pct": 28.4, "forest_area_sqkm": 3.6, "water_bodies": 5, "trees_m": 0.95, "gw_depth": 9.4, "stations": 2
            },
            "BLR-ECITY": {
                "name": "Electronic City Phase 1", "tier": "area", "parent_id": "KA-BLR", "type": "IT SEZ & Industrial Buffer",
                "lat": 12.8450, "lng": 77.6650, "zoom": 14.2, "pitch": 52, "bearing": 15,
                "neighbors": ["BLR-WHT", "BLR-KORAM"],
                "bod": 7.2, "cod": 35.0, "do": 6.4, "ph": 7.4, "water_flow": 88.0, "water_temp": 24.8,
                "aqi": 104, "pm25": 42.0, "pm10": 85.0, "no2": 27.0, "so2": 11.0, "air_temp": 26.5,
                "forest_cover_pct": 19.5, "forest_area_sqkm": 3.2, "water_bodies": 4, "trees_m": 0.74, "gw_depth": 13.0, "stations": 2
            },
            # Delhi Wards
            "DEL-OKHLA": {
                "name": "Okhla Industrial Area", "tier": "area", "parent_id": "DL-SO", "type": "Manufacturing & CETP Zone",
                "lat": 28.5300, "lng": 77.2700, "zoom": 14.5, "pitch": 60, "bearing": 40,
                "neighbors": ["DEL-CP", "DEL-DWARKA"],
                "bod": 17.5, "cod": 92.0, "do": 2.1, "ph": 8.2, "water_flow": 158.0, "water_temp": 27.2,
                "aqi": 295, "pm25": 152.0, "pm10": 285.0, "no2": 68.0, "so2": 34.0, "air_temp": 33.2,
                "forest_cover_pct": 5.2, "forest_area_sqkm": 0.9, "water_bodies": 2, "trees_m": 0.18, "gw_depth": 22.5, "stations": 3
            },
            "DEL-CP": {
                "name": "Connaught Place (Central)", "tier": "area", "parent_id": "DL-ND", "type": "High-Density Commercial Nexus",
                "lat": 28.6315, "lng": 77.2167, "zoom": 14.3, "pitch": 55, "bearing": 10,
                "neighbors": ["DEL-OKHLA", "DEL-AV"],
                "bod": 11.2, "cod": 58.0, "do": 4.4, "ph": 7.7, "water_flow": 98.0, "water_temp": 26.0,
                "aqi": 235, "pm25": 118.0, "pm10": 220.0, "no2": 52.0, "so2": 22.0, "air_temp": 31.5,
                "forest_cover_pct": 14.8, "forest_area_sqkm": 2.2, "water_bodies": 3, "trees_m": 0.45, "gw_depth": 15.8, "stations": 2
            },
            "DEL-DWARKA": {
                "name": "Dwarka Sub-City", "tier": "area", "parent_id": "DL-SO", "type": "Planned Residential Sub-City",
                "lat": 28.5921, "lng": 77.0460, "zoom": 14.0, "pitch": 50, "bearing": 0,
                "neighbors": ["DEL-CP", "DEL-OKHLA"],
                "bod": 9.4, "cod": 48.0, "do": 5.2, "ph": 7.5, "water_flow": 112.0, "water_temp": 25.8,
                "aqi": 210, "pm25": 104.0, "pm10": 195.0, "no2": 44.0, "so2": 19.0, "air_temp": 31.0,
                "forest_cover_pct": 21.0, "forest_area_sqkm": 5.1, "water_bodies": 6, "trees_m": 0.88, "gw_depth": 17.2, "stations": 2
            },
            "DEL-AV": {
                "name": "Anand Vihar ISBT Basin", "tier": "area", "parent_id": "DL-NO", "type": "Transport & Industrial Air Basin",
                "lat": 28.6470, "lng": 77.3150, "zoom": 14.2, "pitch": 55, "bearing": 15,
                "neighbors": ["DEL-CP", "DEL-OKHLA"],
                "bod": 18.0, "cod": 95.0, "do": 2.0, "ph": 8.3, "water_flow": 170.0, "water_temp": 27.5,
                "aqi": 320, "pm25": 168.0, "pm10": 310.0, "no2": 72.0, "so2": 38.0, "air_temp": 33.8,
                "forest_cover_pct": 4.1, "forest_area_sqkm": 0.6, "water_bodies": 1, "trees_m": 0.14, "gw_depth": 24.0, "stations": 3
            },
            # Tamil Nadu (Chennai)
            "CHN-MANALI": {
                "name": "Manali Petrochem Zone", "tier": "area", "parent_id": "TN-CHN", "type": "Petrochemical & Fertilizer Hub",
                "lat": 13.1650, "lng": 80.2600, "zoom": 14.2, "pitch": 58, "bearing": 20,
                "neighbors": ["CHN-GUINDY", "CHN-OMR"],
                "bod": 16.8, "cod": 88.0, "do": 2.8, "ph": 8.2, "water_flow": 165.0, "water_temp": 30.5,
                "aqi": 195, "pm25": 94.0, "pm10": 178.0, "no2": 48.0, "so2": 29.0, "air_temp": 34.0,
                "forest_cover_pct": 5.8, "forest_area_sqkm": 0.9, "water_bodies": 2, "trees_m": 0.18, "gw_depth": 6.8, "stations": 3
            },
            "CHN-GUINDY": {
                "name": "Guindy Industrial Estate", "tier": "area", "parent_id": "TN-CHN", "type": "Mixed Industrial & National Park Buffer",
                "lat": 13.0100, "lng": 80.2150, "zoom": 14.2, "pitch": 50, "bearing": 10,
                "neighbors": ["CHN-MANALI", "CHN-OMR"],
                "bod": 9.8, "cod": 48.0, "do": 5.4, "ph": 7.6, "water_flow": 120.0, "water_temp": 29.0,
                "aqi": 132, "pm25": 58.0, "pm10": 112.0, "no2": 32.0, "so2": 18.0, "air_temp": 32.0,
                "forest_cover_pct": 26.5, "forest_area_sqkm": 4.2, "water_bodies": 4, "trees_m": 0.92, "gw_depth": 5.5, "stations": 2
            },
            "CHN-OMR": {
                "name": "OMR IT Expressway", "tier": "area", "parent_id": "TN-CHN", "type": "High-Tech IT Corridor",
                "lat": 12.9200, "lng": 80.2300, "zoom": 14.2, "pitch": 52, "bearing": 15,
                "neighbors": ["CHN-GUINDY"],
                "bod": 7.2, "cod": 36.0, "do": 6.2, "ph": 7.4, "water_flow": 95.0, "water_temp": 28.5,
                "aqi": 108, "pm25": 46.0, "pm10": 88.0, "no2": 26.0, "so2": 13.0, "air_temp": 31.5,
                "forest_cover_pct": 18.0, "forest_area_sqkm": 3.1, "water_bodies": 5, "trees_m": 0.68, "gw_depth": 6.2, "stations": 2
            },
            # Telangana (Hyderabad)
            "HYD-HITEC": {
                "name": "HITEC City Cyberabad", "tier": "area", "parent_id": "TG-HYD", "type": "Global Tech Hub",
                "lat": 17.4474, "lng": 78.3762, "zoom": 14.2, "pitch": 55, "bearing": 20,
                "neighbors": ["HYD-JEED", "HYD-SANATH"],
                "bod": 7.4, "cod": 37.0, "do": 6.2, "ph": 7.4, "water_flow": 110.0, "water_temp": 27.5,
                "aqi": 118, "pm25": 52.0, "pm10": 102.0, "no2": 28.0, "so2": 13.5, "air_temp": 31.0,
                "forest_cover_pct": 18.5, "forest_area_sqkm": 3.6, "water_bodies": 5, "trees_m": 0.85, "gw_depth": 9.5, "stations": 3
            },
            "HYD-JEED": {
                "name": "Jeedimetla CETP Industrial", "tier": "area", "parent_id": "TG-HYD", "type": "Pharma & Chemical CETP Zone",
                "lat": 17.5150, "lng": 78.4480, "zoom": 14.4, "pitch": 60, "bearing": 30,
                "neighbors": ["HYD-HITEC", "HYD-SANATH"],
                "bod": 17.2, "cod": 94.0, "do": 2.5, "ph": 8.3, "water_flow": 145.0, "water_temp": 29.5,
                "aqi": 242, "pm25": 118.0, "pm10": 230.0, "no2": 62.0, "so2": 35.0, "air_temp": 33.5,
                "forest_cover_pct": 4.8, "forest_area_sqkm": 0.8, "water_bodies": 2, "trees_m": 0.16, "gw_depth": 11.2, "stations": 3
            },
            "HYD-SANATH": {
                "name": "Sanath Nagar Industrial", "tier": "area", "parent_id": "TG-HYD", "type": "Manufacturing Cluster",
                "lat": 17.4580, "lng": 78.4420, "zoom": 14.2, "pitch": 55, "bearing": 15,
                "neighbors": ["HYD-HITEC", "HYD-JEED"],
                "bod": 12.8, "cod": 64.0, "do": 4.2, "ph": 7.7, "water_flow": 125.0, "water_temp": 28.5,
                "aqi": 178, "pm25": 82.0, "pm10": 158.0, "no2": 44.0, "so2": 22.0, "air_temp": 32.2,
                "forest_cover_pct": 8.2, "forest_area_sqkm": 1.4, "water_bodies": 3, "trees_m": 0.32, "gw_depth": 8.5, "stations": 2
            },
            # West Bengal (Kolkata)
            "KOL-SL": {
                "name": "Salt Lake Sector V", "tier": "area", "parent_id": "WB-KOL", "type": "IT & Electronics Core",
                "lat": 22.5780, "lng": 88.4320, "zoom": 14.2, "pitch": 52, "bearing": 15,
                "neighbors": ["KOL-TARA", "KOL-VM"],
                "bod": 8.5, "cod": 42.0, "do": 5.8, "ph": 7.5, "water_flow": 115.0, "water_temp": 27.2,
                "aqi": 165, "pm25": 78.0, "pm10": 145.0, "no2": 42.0, "so2": 21.0, "air_temp": 29.8,
                "forest_cover_pct": 16.5, "forest_area_sqkm": 2.8, "water_bodies": 8, "trees_m": 0.65, "gw_depth": 4.2, "stations": 2
            },
            "KOL-TARA": {
                "name": "Taratala Industrial Area", "tier": "area", "parent_id": "WB-KOL", "type": "Port Warehousing & Heavy Engineering",
                "lat": 22.5120, "lng": 88.3150, "zoom": 14.2, "pitch": 56, "bearing": 20,
                "neighbors": ["KOL-SL", "KOL-VM"],
                "bod": 15.2, "cod": 79.0, "do": 3.2, "ph": 7.9, "water_flow": 150.0, "water_temp": 28.0,
                "aqi": 235, "pm25": 112.0, "pm10": 210.0, "no2": 58.0, "so2": 32.0, "air_temp": 31.0,
                "forest_cover_pct": 5.2, "forest_area_sqkm": 0.9, "water_bodies": 4, "trees_m": 0.22, "gw_depth": 3.9, "stations": 3
            },
            "KOL-VM": {
                "name": "Victoria Memorial Green Buffer", "tier": "area", "parent_id": "WB-KOL", "type": "Protected Heritage Eco-Zone",
                "lat": 22.5448, "lng": 88.3426, "zoom": 14.2, "pitch": 45, "bearing": 0,
                "neighbors": ["KOL-SL", "KOL-TARA"],
                "bod": 6.8, "cod": 32.0, "do": 6.5, "ph": 7.4, "water_flow": 80.0, "water_temp": 26.5,
                "aqi": 138, "pm25": 62.0, "pm10": 118.0, "no2": 34.0, "so2": 16.0, "air_temp": 29.0,
                "forest_cover_pct": 34.0, "forest_area_sqkm": 3.2, "water_bodies": 6, "trees_m": 0.92, "gw_depth": 4.8, "stations": 2
            },
            # Uttar Pradesh (Noida & Kanpur)
            "NOI-SEC62": {
                "name": "Sector 62 Tech Core", "tier": "area", "parent_id": "UP-NOI", "type": "IT & Institutional Cluster",
                "lat": 28.6250, "lng": 77.3650, "zoom": 14.2, "pitch": 52, "bearing": 15,
                "neighbors": ["NOI-SEC11", "DEL-CP"],
                "bod": 9.5, "cod": 49.0, "do": 5.1, "ph": 7.6, "water_flow": 92.0, "water_temp": 26.0,
                "aqi": 230, "pm25": 112.0, "pm10": 210.0, "no2": 51.0, "so2": 24.0, "air_temp": 32.0,
                "forest_cover_pct": 14.0, "forest_area_sqkm": 2.1, "water_bodies": 3, "trees_m": 0.48, "gw_depth": 14.2, "stations": 2
            },
            "NOI-SEC11": {
                "name": "Sector 11 Industrial Cluster", "tier": "area", "parent_id": "UP-NOI", "type": "Light Engineering & Electronics MIDC",
                "lat": 28.5950, "lng": 77.3300, "zoom": 14.2, "pitch": 56, "bearing": 20,
                "neighbors": ["NOI-SEC62", "DEL-OKHLA"],
                "bod": 15.8, "cod": 82.0, "do": 3.0, "ph": 8.1, "water_flow": 140.0, "water_temp": 27.2,
                "aqi": 285, "pm25": 144.0, "pm10": 268.0, "no2": 64.0, "so2": 32.0, "air_temp": 33.2,
                "forest_cover_pct": 6.2, "forest_area_sqkm": 0.9, "water_bodies": 2, "trees_m": 0.20, "gw_depth": 15.5, "stations": 3
            },
            "KNP-JAJMAU": {
                "name": "Jajmau Tannery Ganga Basin", "tier": "area", "parent_id": "UP-KNP", "type": "Leather Processing & Heavy Chromium Outflow",
                "lat": 26.4350, "lng": 80.4050, "zoom": 14.4, "pitch": 62, "bearing": 35,
                "neighbors": ["KNP-PANKI"],
                "bod": 22.5, "cod": 118.0, "do": 1.8, "ph": 8.6, "water_flow": 185.0, "water_temp": 28.5,
                "aqi": 310, "pm25": 162.0, "pm10": 305.0, "no2": 72.0, "so2": 42.0, "air_temp": 33.5,
                "forest_cover_pct": 3.2, "forest_area_sqkm": 0.6, "water_bodies": 2, "trees_m": 0.12, "gw_depth": 11.5, "stations": 3
            },
            "KNP-PANKI": {
                "name": "Panki Industrial Area", "tier": "area", "parent_id": "UP-KNP", "type": "Thermal & Heavy Machinery MIDC",
                "lat": 26.4750, "lng": 80.2450, "zoom": 14.2, "pitch": 55, "bearing": 20,
                "neighbors": ["KNP-JAJMAU"],
                "bod": 14.8, "cod": 74.0, "do": 3.6, "ph": 7.9, "water_flow": 135.0, "water_temp": 27.0,
                "aqi": 265, "pm25": 132.0, "pm10": 248.0, "no2": 58.0, "so2": 29.0, "air_temp": 32.2,
                "forest_cover_pct": 7.4, "forest_area_sqkm": 1.4, "water_bodies": 3, "trees_m": 0.28, "gw_depth": 13.2, "stations": 2
            },
            # Madhya Pradesh (Indore & Bhopal)
            "IND-PITH": {
                "name": "Pithampur Industrial Belt", "tier": "area", "parent_id": "MP-IND", "type": "Automotive & Heavy Eng Hub",
                "lat": 22.6100, "lng": 75.6800, "zoom": 14.2, "pitch": 55, "bearing": 20,
                "neighbors": ["IND-VIJAY"],
                "bod": 12.5, "cod": 64.0, "do": 4.5, "ph": 7.7, "water_flow": 145.0, "water_temp": 27.0,
                "aqi": 145, "pm25": 66.0, "pm10": 132.0, "no2": 36.0, "so2": 18.0, "air_temp": 31.0,
                "forest_cover_pct": 11.2, "forest_area_sqkm": 2.2, "water_bodies": 3, "trees_m": 0.44, "gw_depth": 9.4, "stations": 3
            },
            "IND-VIJAY": {
                "name": "Vijay Nagar Tech Core", "tier": "area", "parent_id": "MP-IND", "type": "Commercial & Tech Buffer",
                "lat": 22.7520, "lng": 75.8940, "zoom": 14.2, "pitch": 48, "bearing": 10,
                "neighbors": ["IND-PITH"],
                "bod": 5.2, "cod": 26.0, "do": 7.2, "ph": 7.3, "water_flow": 85.0, "water_temp": 25.5,
                "aqi": 88, "pm25": 36.0, "pm10": 72.0, "no2": 21.0, "so2": 9.0, "air_temp": 28.5,
                "forest_cover_pct": 24.5, "forest_area_sqkm": 4.5, "water_bodies": 6, "trees_m": 0.95, "gw_depth": 7.8, "stations": 2
            },
            "BHP-LAKE": {
                "name": "Upper Lake Wetland Buffer", "tier": "area", "parent_id": "MP-BHP", "type": "Ramsar Wetland Eco-Zone",
                "lat": 23.2450, "lng": 77.3450, "zoom": 14.0, "pitch": 45, "bearing": 0,
                "neighbors": ["IND-VIJAY"],
                "bod": 4.2, "cod": 21.0, "do": 7.8, "ph": 7.2, "water_flow": 120.0, "water_temp": 24.5,
                "aqi": 74, "pm25": 30.0, "pm10": 62.0, "no2": 16.0, "so2": 7.5, "air_temp": 27.5,
                "forest_cover_pct": 46.0, "forest_area_sqkm": 18.0, "water_bodies": 12, "trees_m": 3.80, "gw_depth": 5.2, "stations": 3
            },
            # Rajasthan (Jaipur)
            "JPR-SITA": {
                "name": "Sitapura Industrial Area", "tier": "area", "parent_id": "RJ-JPR", "type": "Jewellery, Garment & IT SEZ",
                "lat": 26.7800, "lng": 75.8300, "zoom": 14.2, "pitch": 55, "bearing": 20,
                "neighbors": ["JPR-MANS"],
                "bod": 11.8, "cod": 58.0, "do": 4.8, "ph": 7.8, "water_flow": 110.0, "water_temp": 28.5,
                "aqi": 185, "pm25": 84.0, "pm10": 185.0, "no2": 38.0, "so2": 22.0, "air_temp": 35.5,
                "forest_cover_pct": 6.8, "forest_area_sqkm": 1.2, "water_bodies": 2, "trees_m": 0.22, "gw_depth": 25.0, "stations": 2
            },
            "JPR-MANS": {
                "name": "Mansarovar Basin", "tier": "area", "parent_id": "RJ-JPR", "type": "Residential Eco & Commercial Sector",
                "lat": 26.8600, "lng": 75.7600, "zoom": 14.2, "pitch": 48, "bearing": 10,
                "neighbors": ["JPR-SITA"],
                "bod": 6.4, "cod": 32.0, "do": 6.5, "ph": 7.5, "water_flow": 85.0, "water_temp": 26.8,
                "aqi": 142, "pm25": 62.0, "pm10": 145.0, "no2": 28.0, "so2": 15.0, "air_temp": 33.5,
                "forest_cover_pct": 14.5, "forest_area_sqkm": 2.8, "water_bodies": 4, "trees_m": 0.58, "gw_depth": 21.0, "stations": 2
            },
            # Kerala (Kochi)
            "COK-ELOOR": {
                "name": "Eloor Chemical Belt (Periyar)", "tier": "area", "parent_id": "KL-COK", "type": "Riverine Chemical Industrial Island",
                "lat": 10.0800, "lng": 76.2950, "zoom": 14.4, "pitch": 60, "bearing": 30,
                "neighbors": ["COK-MD", "COK-INFO"],
                "bod": 14.2, "cod": 72.0, "do": 3.8, "ph": 7.9, "water_flow": 160.0, "water_temp": 28.2,
                "aqi": 115, "pm25": 48.0, "pm10": 92.0, "no2": 28.0, "so2": 16.0, "air_temp": 29.5,
                "forest_cover_pct": 24.0, "forest_area_sqkm": 2.5, "water_bodies": 6, "trees_m": 0.82, "gw_depth": 2.8, "stations": 3
            },
            "COK-MD": {
                "name": "Marine Drive Coastal Bay", "tier": "area", "parent_id": "KL-COK", "type": "Backwater Coastal Promenade",
                "lat": 9.9800, "lng": 76.2750, "zoom": 14.2, "pitch": 45, "bearing": 0,
                "neighbors": ["COK-ELOOR", "COK-INFO"],
                "bod": 4.5, "cod": 22.0, "do": 7.4, "ph": 7.2, "water_flow": 140.0, "water_temp": 26.8,
                "aqi": 62, "pm25": 22.0, "pm10": 46.0, "no2": 14.0, "so2": 8.0, "air_temp": 28.0,
                "forest_cover_pct": 38.0, "forest_area_sqkm": 4.1, "water_bodies": 12, "trees_m": 1.45, "gw_depth": 3.2, "stations": 2
            },
            "COK-INFO": {
                "name": "Infopark Kakkanad", "tier": "area", "parent_id": "KL-COK", "type": "High-Tech IT SEZ Corridor",
                "lat": 10.0100, "lng": 76.3650, "zoom": 14.2, "pitch": 50, "bearing": 15,
                "neighbors": ["COK-ELOOR", "COK-MD"],
                "bod": 3.8, "cod": 19.0, "do": 7.8, "ph": 7.1, "water_flow": 88.0, "water_temp": 26.2,
                "aqi": 55, "pm25": 18.0, "pm10": 40.0, "no2": 12.0, "so2": 6.5, "air_temp": 27.5,
                "forest_cover_pct": 44.0, "forest_area_sqkm": 5.2, "water_bodies": 9, "trees_m": 1.80, "gw_depth": 4.5, "stations": 2
            }
        }

    def _fluctuate(self, val: float, base: float, delta: float, vmin: float, vmax: float) -> float:
        noise = (random.random() - 0.5) * delta
        return max(vmin, min(vmax, round(val + noise, 2)))

    def _compute_status(self, bod: float, cod: float, aqi: int) -> str:
        if bod > 15.0 or cod > 80.0 or aqi > 250:
            return "CRITICAL"
        elif bod > 9.0 or cod > 50.0 or aqi > 150:
            return "ELEVATED"
        return "NORMAL"

    def step_simulation(self):
        self.sequence += 1
        curr_time = time.time()
        self.alerts.clear()

        # Step States
        for key, item in self.states_data.items():
            item["bod"] = self._fluctuate(item["bod"], item["bod"], 0.20, 2.0, 30.0)
            item["cod"] = self._fluctuate(item["cod"], item["cod"], 0.80, 8.0, 140.0)
            item["do"] = self._fluctuate(item["do"], item["do"], 0.12, 1.5, 9.5)
            item["ph"] = self._fluctuate(item["ph"], item["ph"], 0.03, 6.2, 9.0)
            item["aqi"] = int(self._fluctuate(float(item["aqi"]), float(item["aqi"]), 3.0, 30.0, 450.0))
            item["pm25"] = self._fluctuate(item["pm25"], item["pm25"], 1.5, 10.0, 280.0)
            item["pm10"] = self._fluctuate(item["pm10"], item["pm10"], 2.2, 20.0, 480.0)
            item["no2"] = self._fluctuate(item["no2"], item["no2"], 0.6, 5.0, 110.0)
            item["so2"] = self._fluctuate(item["so2"], item["so2"], 0.4, 2.0, 60.0)
            item["water_flow"] = self._fluctuate(item["water_flow"], item["water_flow"], 3.0, 50.0, 600.0)

        # Step Cities
        for key, item in self.cities_data.items():
            item["bod"] = self._fluctuate(item["bod"], item["bod"], 0.25, 2.0, 35.0)
            item["cod"] = self._fluctuate(item["cod"], item["cod"], 1.00, 10.0, 150.0)
            item["do"] = self._fluctuate(item["do"], item["do"], 0.15, 1.2, 9.0)
            item["ph"] = self._fluctuate(item["ph"], item["ph"], 0.04, 6.4, 8.9)
            item["aqi"] = int(self._fluctuate(float(item["aqi"]), float(item["aqi"]), 3.5, 40.0, 420.0))
            item["pm25"] = self._fluctuate(item["pm25"], item["pm25"], 1.8, 15.0, 260.0)
            item["pm10"] = self._fluctuate(item["pm10"], item["pm10"], 2.8, 30.0, 400.0)
            item["no2"] = self._fluctuate(item["no2"], item["no2"], 0.8, 8.0, 100.0)
            item["so2"] = self._fluctuate(item["so2"], item["so2"], 0.5, 3.0, 55.0)
            item["water_flow"] = self._fluctuate(item["water_flow"], item["water_flow"], 3.0, 60.0, 550.0)

        # Step Areas
        for key, item in self.areas_data.items():
            is_ind = "Industrial" in item["type"] or "CETP" in item["type"] or "Chemical" in item["type"]
            vol_mult = 1.5 if is_ind else 1.0

            item["bod"] = self._fluctuate(item["bod"], item["bod"], 0.30 * vol_mult, 3.0, 40.0)
            item["cod"] = self._fluctuate(item["cod"], item["cod"], 1.20 * vol_mult, 15.0, 180.0)
            item["do"] = self._fluctuate(item["do"], item["do"], 0.18, 1.0, 9.2)
            item["ph"] = self._fluctuate(item["ph"], item["ph"], 0.05, 6.5, 9.2)
            item["aqi"] = int(self._fluctuate(float(item["aqi"]), float(item["aqi"]), 4.0 * vol_mult, 45.0, 450.0))
            item["pm25"] = self._fluctuate(item["pm25"], item["pm25"], 2.0 * vol_mult, 20.0, 300.0)
            item["pm10"] = self._fluctuate(item["pm10"], item["pm10"], 3.5 * vol_mult, 35.0, 450.0)
            item["no2"] = self._fluctuate(item["no2"], item["no2"], 1.0, 10.0, 120.0)
            item["so2"] = self._fluctuate(item["so2"], item["so2"], 0.7, 4.0, 70.0)
            item["water_flow"] = self._fluctuate(item["water_flow"], item["water_flow"], 2.2, 30.0, 250.0)

            if item["cod"] > 80.0:
                self.alerts.append(
                    AlertEvent(
                        id=f"ALT-COD-{key}-{self.sequence}",
                        timestamp=curr_time,
                        region_id=key,
                        region_name=item["name"],
                        parameter="COD",
                        value=item["cod"],
                        threshold=80.0,
                        severity="CRITICAL",
                        message=f"High Chemical Oxygen Demand ({item['cod']} mg/L) detected at {item['name']} outlet."
                    )
                )

    def _convert_to_telemetry(self, raw_dict: Dict[str, dict], tier: str) -> Dict[str, EntityTelemetry]:
        result = {}
        for k, v in raw_dict.items():
            status = self._compute_status(v["bod"], v["cod"], v["aqi"])
            res = NaturalResources(
                forest_cover_pct=v.get("forest_cover_pct", 20.0),
                forest_area_sqkm=v.get("forest_area_sqkm", 100.0),
                water_bodies_count=v.get("water_bodies", 10),
                tree_count_millions=v.get("trees_m", 1.0),
                groundwater_depth_m=v.get("gw_depth", 6.0),
                monitoring_stations_count=v.get("stations", 2)
            )
            result[k] = EntityTelemetry(
                id=k,
                name=v["name"],
                tier=tier,
                parent_id=v.get("parent_id"),
                type=v["type"],
                lat=v["lat"],
                lng=v["lng"],
                camera_zoom=v.get("zoom", 12.0),
                camera_pitch=v.get("pitch", 45.0),
                camera_bearing=v.get("bearing", 0.0),
                neighbors=v.get("neighbors", []),
                bod=v["bod"],
                cod=v["cod"],
                do=v["do"],
                ph=v["ph"],
                water_flow_mld=v["water_flow"],
                water_temp_c=v.get("water_temp", 27.0),
                aqi=v["aqi"],
                pm25=v["pm25"],
                pm10=v["pm10"],
                no2=v["no2"],
                so2=v.get("so2", 15.0),
                air_temp_c=v.get("air_temp", 30.0),
                resources=res,
                status=status
            )
        return result

    def get_snapshot(self) -> BroadcastPayload:
        states = self._convert_to_telemetry(self.states_data, "state")
        cities = self._convert_to_telemetry(self.cities_data, "city")
        areas = self._convert_to_telemetry(self.areas_data, "area")

        # Compute Global / All-India Aggregates
        all_bod = [s.bod for s in states.values()]
        all_cod = [s.cod for s in states.values()]
        all_aqi = [s.aqi for s in states.values()]
        total_flow = sum(s.water_flow_mld for s in states.values())
        total_forest_sqkm = sum(s.resources.forest_area_sqkm for s in states.values())
        total_lakes = sum(s.resources.water_bodies_count for s in states.values())

        global_stats = {
            "all_india_avg_bod": round(sum(all_bod) / len(all_bod), 1),
            "all_india_avg_cod": round(sum(all_cod) / len(all_cod), 1),
            "all_india_avg_aqi": round(sum(all_aqi) / len(all_aqi)),
            "all_india_total_flow_mld": round(total_flow, 1),
            "all_india_total_forest_sqkm": round(total_forest_sqkm, 0),
            "all_india_total_lakes": total_lakes,
            "monitored_entities_count": len(states) + len(cities) + len(areas),
            "fps_target": 60.0
        }

        return BroadcastPayload(
            timestamp=time.time(),
            sequence=self.sequence,
            states=states,
            cities=cities,
            areas=areas,
            active_alerts=list(self.alerts),
            global_stats=global_stats
        )

    async def register(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)
        snapshot = self.get_snapshot()
        await websocket.send_text(snapshot.model_dump_json())

    def unregister(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast_loop(self):
        logger.info("Starting all-India multi-tier telemetry broadcast loop...")
        while True:
            try:
                await asyncio.sleep(2.0)
                self.step_simulation()
                if not self.active_connections:
                    continue

                snapshot = self.get_snapshot()
                payload_str = snapshot.model_dump_json()

                disconnected = []
                for ws in self.active_connections:
                    try:
                        await ws.send_text(payload_str)
                    except Exception:
                        disconnected.append(ws)

                for ws in disconnected:
                    self.unregister(ws)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in telemetry loop: {e}")

data_manager = MultiTierDataManager()


# -----------------------------------------------------------------------------
# Standalone High-Performance GPU WebGL Interface
# -----------------------------------------------------------------------------

STANDALONE_DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>EnviroPulse 3D | All-India State • City • Area Environmental Intelligence</title>
  
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&family=JetBrains+Mono:wght@400;600;700&display=swap" rel="stylesheet">
  
  <script src="https://cdn.tailwindcss.com"></script>
  
  <!-- MapLibre & Deck.gl -->
  <link href="https://unpkg.com/maplibre-gl@3.6.2/dist/maplibre-gl.css" rel="stylesheet" />
  <script src="https://unpkg.com/maplibre-gl@3.6.2/dist/maplibre-gl.js"></script>
  <script src="https://unpkg.com/deck.gl@8.9.34/dist.min.js"></script>
  
  <!-- Chart.js -->
  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>

  <script>
    tailwind.config = {
      theme: {
        extend: {
          colors: {
            cyber: { 900: '#070b13', 850: '#0b111e', 800: '#0f172a', 750: '#15203b', 700: '#1e293b', border: 'rgba(56, 189, 248, 0.18)' },
            neon: { cyan: '#00f0ff', emerald: '#10b981', amber: '#f59e0b', rose: '#f43f5e', purple: '#a855f7', teal: '#14b8a6' }
          },
          fontFamily: { mono: ['"JetBrains Mono"', 'monospace'], sans: ['"Inter"', 'sans-serif'] }
        }
      }
    }
  </script>

  <style>
    body { background-color: #070b13; color: #e2e8f0; margin: 0; overflow: hidden; font-family: 'Inter', sans-serif; }
    .glass-panel {
      background: rgba(11, 17, 30, 0.88);
      backdrop-filter: blur(16px);
      border: 1px solid rgba(56, 189, 248, 0.2);
      box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.45);
    }
    .glass-panel-glow {
      background: rgba(15, 23, 42, 0.94);
      backdrop-filter: blur(20px);
      border: 1px solid rgba(0, 240, 255, 0.4);
      box-shadow: 0 0 25px -5px rgba(0, 240, 255, 0.25);
    }
    #deck-canvas-container { width: 100vw; height: 100vh; position: absolute; top: 0; left: 0; }
    #deck-canvas-container .maplibregl-map {
      filter: brightness(0.65) invert(0.92) contrast(1.35) hue-rotate(190deg) saturate(0.35);
    }
    .hud-badge { padding: 2px 8px; border-radius: 9999px; font-size: 11px; font-family: 'JetBrains Mono', monospace; font-weight: 700; }
    .deck-tooltip {
      position: absolute; pointer-events: none; z-index: 1000;
      background: rgba(7, 11, 19, 0.95); backdrop-filter: blur(12px);
      border: 1px solid rgba(0, 240, 255, 0.4); border-radius: 8px;
      padding: 10px 14px; font-size: 12px; color: #e2e8f0;
      box-shadow: 0 10px 30px rgba(0,0,0,0.8), 0 0 20px rgba(0, 240, 255, 0.2);
    }
    ::-webkit-scrollbar { width: 4px; }
    ::-webkit-scrollbar-track { background: rgba(11, 17, 30, 0.5); }
    ::-webkit-scrollbar-thumb { background: rgba(56, 189, 248, 0.3); border-radius: 4px; }
    ::-webkit-scrollbar-thumb:hover { background: rgba(0, 240, 255, 0.6); }
  </style>
</head>
<body class="bg-cyber-900 select-none">

  <!-- Main WebGL Viewport -->
  <div id="deck-canvas-container"></div>
  <div id="tooltip-container"></div>

  <!-- Top Navigation HUD -->
  <header class="fixed top-3 left-3 right-3 z-50 flex items-center justify-between pointer-events-none">
    <div class="flex items-center gap-3 pointer-events-auto">
      <div class="glass-panel-glow px-4 py-2 rounded-xl flex items-center gap-3">
        <div class="w-8 h-8 rounded-lg bg-cyan-500/20 border border-cyan-400/50 flex items-center justify-center text-cyan-400 font-bold">
          ⚡
        </div>
        <div>
          <div class="flex items-center gap-2">
            <span class="font-extrabold text-sm tracking-wider bg-gradient-to-r from-cyan-400 via-teal-300 to-indigo-400 bg-clip-text text-transparent">
              ENVIROPULSE 3D
            </span>
            <span class="px-1.5 py-0.2 bg-cyan-500/10 border border-cyan-500/30 text-[10px] font-mono text-cyan-300 rounded">
              All-India Grid
            </span>
          </div>
          <p class="text-[10px] text-slate-400 font-mono">Real-Time State • City • Area Environmental Intelligence</p>
        </div>
      </div>

      <!-- Quick 3-Tier Dropdown Navigator -->
      <div class="glass-panel px-3 py-1.5 rounded-xl flex items-center gap-2 text-xs font-mono">
        <span class="text-slate-400">Drill:</span>
        <select id="tier-selector" onchange="handleDropdownSelection(this.value)" class="bg-cyber-800 border border-cyan-500/40 text-cyan-300 rounded px-2.5 py-1 outline-none text-xs font-mono max-w-[280px]">
          <!-- Populated dynamically -->
        </select>
      </div>

      <!-- Breadcrumbs -->
      <div id="breadcrumb-bar" class="glass-panel px-3.5 py-1.5 rounded-xl flex items-center gap-1.5 text-xs font-mono text-slate-300">
        <!-- Dynamically updated -->
      </div>
    </div>

    <!-- Mode Selector & Live Status -->
    <div class="flex items-center gap-3 pointer-events-auto">
      <div class="glass-panel p-1 rounded-xl flex items-center gap-1 text-xs font-mono">
        <button onclick="setMetricMode('water')" id="mode-water" class="px-3 py-1.5 rounded-lg bg-cyan-950/80 border border-cyan-400 text-cyan-300 font-bold">
          💧 Water (BOD/COD)
        </button>
        <button onclick="setMetricMode('air')" id="mode-air" class="px-3 py-1.5 rounded-lg text-slate-400 hover:text-white">
          💨 Air (AQI/PM)
        </button>
        <button onclick="setMetricMode('resources')" id="mode-resources" class="px-3 py-1.5 rounded-lg text-slate-400 hover:text-white">
          🌿 Resources
        </button>
      </div>

      <div class="glass-panel px-3.5 py-2 rounded-xl flex items-center gap-3 text-xs font-mono">
        <span class="flex items-center gap-1.5 text-emerald-400 font-bold" id="ws-status">
          <span class="relative flex h-2 w-2">
            <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
            <span class="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
          </span>
          <span>LIVE 2s</span>
        </span>
        <span class="text-slate-600">|</span>
        <span class="text-slate-400" id="seq-counter">SEQ #0</span>
      </div>
    </div>
  </header>

  <!-- Left HUD Controls -->
  <div class="fixed top-20 left-3 z-40 flex flex-col gap-2 pointer-events-auto">
    <div class="glass-panel p-2.5 rounded-2xl flex flex-col gap-2 w-52 text-xs font-mono">
      <div class="text-[10px] text-slate-400 uppercase tracking-wider pb-1 border-b border-slate-800 flex justify-between items-center">
        <span>Hierarchy Tier</span>
        <span class="text-cyan-400 font-bold">60 FPS</span>
      </div>
      
      <!-- Tier Switcher Buttons -->
      <button onclick="switchTier('state')" id="tier-btn-state" class="px-2.5 py-1.5 rounded-lg text-left text-slate-300 hover:bg-slate-800 flex justify-between items-center">
        <span>Tier 1: States</span>
        <span class="text-[10px] bg-slate-800 px-1.5 py-0.5 rounded text-slate-400">11</span>
      </button>
      <button onclick="switchTier('city')" id="tier-btn-city" class="px-2.5 py-1.5 rounded-lg text-left text-slate-300 hover:bg-slate-800 flex justify-between items-center">
        <span>Tier 2: Cities</span>
        <span class="text-[10px] bg-slate-800 px-1.5 py-0.5 rounded text-slate-400">27</span>
      </button>
      <button onclick="switchTier('area')" id="tier-btn-area" class="px-2.5 py-1.5 rounded-lg text-left bg-cyan-950/80 border border-cyan-400 text-cyan-300 font-bold flex justify-between items-center">
        <span>Tier 3: Micro-Areas</span>
        <span class="text-[10px] bg-cyan-900/60 px-1.5 py-0.5 rounded text-cyan-300">46</span>
      </button>

      <div class="border-t border-slate-800 pt-2 flex flex-col gap-1.5">
        <div class="text-[10px] text-slate-400 uppercase tracking-wider">3D GPU Visuals</div>
        <button onclick="toggle3DColumns()" id="btn-3d" class="px-2.5 py-1.5 rounded-lg text-left bg-cyan-950/80 border border-cyan-400 text-cyan-300 flex justify-between items-center transition-all">
          <span>3D Extrusions</span>
          <span class="text-cyan-400 text-xs font-bold">ON</span>
        </button>
        <button onclick="togglePitch()" class="px-2.5 py-1.5 rounded-lg text-left text-slate-300 bg-slate-800/60 hover:bg-slate-800 flex justify-between items-center">
          <span>Toggle 3D Tilt</span>
          <span class="text-slate-400 text-xs">55°</span>
        </button>
      </div>
    </div>
  </div>

  <!-- Bottom Real-Time Telemetry Ticker -->
  <footer class="fixed bottom-3 left-3 right-3 z-40 flex items-center justify-between pointer-events-none">
    <div class="glass-panel px-4 py-2 rounded-2xl flex items-center gap-6 pointer-events-auto text-xs font-mono">
      <div class="flex items-center gap-2">
        <span class="text-slate-400 text-[10px] uppercase">Active Target:</span>
        <span class="text-cyan-400 font-bold" id="hud-active-name">Mahape MIDC</span>
      </div>
      <div class="h-4 w-px bg-slate-700"></div>
      <div class="flex items-center gap-4">
        <div><span class="text-slate-500 text-[10px]">BOD:</span> <span class="font-bold text-cyan-300" id="hud-bod">15.8</span> <span class="text-[10px] text-slate-500">mg/L</span></div>
        <div><span class="text-slate-500 text-[10px]">COD:</span> <span class="font-bold text-indigo-300" id="hud-cod">84.0</span> <span class="text-[10px] text-slate-500">mg/L</span></div>
        <div><span class="text-slate-500 text-[10px]">AQI:</span> <span class="font-bold text-rose-400" id="hud-aqi">224</span></div>
        <div><span class="text-slate-500 text-[10px]">Forest:</span> <span class="font-bold text-emerald-400" id="hud-forest">8.5%</span></div>
        <div><span class="text-slate-500 text-[10px]">Water Bodies:</span> <span class="font-bold text-sky-400" id="hud-waterbodies">3</span></div>
      </div>
    </div>

    <div class="glass-panel px-3 py-2 rounded-2xl flex items-center gap-3 pointer-events-auto text-xs font-mono text-slate-400">
      <span>CPCB Standards Validated</span>
      <span class="w-2 h-2 rounded-full bg-cyan-400"></span>
      <span class="text-cyan-300">GPU Accelerated</span>
    </div>
  </footer>

  <!-- Right Slide-Out Analytics Panel -->
  <aside id="analytics-panel" class="fixed top-20 right-3 bottom-14 w-96 glass-panel-glow rounded-3xl p-5 z-40 flex flex-col gap-4 overflow-y-auto pointer-events-auto transition-transform duration-500 ease-out shadow-2xl">
    <!-- Header -->
    <div class="flex justify-between items-start border-b border-slate-800/80 pb-3">
      <div>
        <div class="flex items-center gap-2 mb-1">
          <span id="panel-tier-badge" class="hud-badge bg-cyan-500/20 text-cyan-300 border border-cyan-500/30">AREA LEVEL</span>
          <span id="panel-status-badge" class="hud-badge bg-rose-500/20 text-rose-400 border border-rose-500/40">CRITICAL</span>
        </div>
        <h2 id="panel-entity-name" class="text-base font-extrabold text-white tracking-wide">Mahape (MIDC Industrial)</h2>
        <p id="panel-entity-type" class="text-xs text-slate-400 font-mono">Heavy Chemical & Manufacturing MIDC</p>
      </div>
      <button onclick="closePanel()" class="w-7 h-7 rounded-lg bg-slate-800/60 hover:bg-slate-700 text-slate-400 hover:text-white flex items-center justify-center transition-colors">
        ✕
      </button>
    </div>

    <!-- Quick Drill-Down Sub-Hierarchy Navigation -->
    <div id="drill-down-subpanel" class="p-3 rounded-2xl bg-cyber-800/70 border border-cyan-500/30 flex flex-col gap-2">
      <!-- Injected dynamically based on tier -->
    </div>

    <!-- Live Telemetry Grid -->
    <div class="grid grid-cols-2 gap-2.5 font-mono">
      <div class="p-3 rounded-xl bg-cyber-800/60 border border-slate-700/60">
        <div class="text-[10px] text-slate-400 uppercase">BOD (Organic)</div>
        <div class="text-xl font-bold text-cyan-300 mt-1 flex items-baseline gap-1">
          <span id="stat-bod">15.8</span>
          <span class="text-[10px] text-slate-400 font-normal">mg/L</span>
        </div>
        <div class="text-[9px] text-slate-500 mt-0.5">CPCB Limit: &lt;3 mg/L</div>
      </div>

      <div class="p-3 rounded-xl bg-cyber-800/60 border border-slate-700/60">
        <div class="text-[10px] text-slate-400 uppercase">COD (Chemical)</div>
        <div class="text-xl font-bold text-indigo-300 mt-1 flex items-baseline gap-1">
          <span id="stat-cod">84.0</span>
          <span class="text-[10px] text-slate-400 font-normal">mg/L</span>
        </div>
        <div class="text-[9px] text-slate-500 mt-0.5">CPCB Limit: &lt;50 mg/L</div>
      </div>

      <div class="p-3 rounded-xl bg-cyber-800/60 border border-slate-700/60">
        <div class="text-[10px] text-slate-400 uppercase">AQI Composite</div>
        <div class="text-xl font-bold text-rose-400 mt-1" id="stat-aqi">224</div>
        <div class="text-[9px] text-slate-500 mt-0.5">PM2.5: <span id="stat-pm25" class="text-slate-300">108</span> | PM10: <span id="stat-pm10" class="text-slate-300">210</span></div>
      </div>

      <div class="p-3 rounded-xl bg-cyber-800/60 border border-slate-700/60">
        <div class="text-[10px] text-slate-400 uppercase">Dissolved Oxygen</div>
        <div class="text-xl font-bold text-emerald-400 mt-1 flex items-baseline gap-1">
          <span id="stat-do">3.2</span>
          <span class="text-[10px] text-slate-400 font-normal">mg/L</span>
        </div>
        <div class="text-[9px] text-slate-500 mt-0.5">Flow: <span id="stat-flow" class="text-slate-300">142</span> MLD</div>
      </div>
    </div>

    <!-- Natural Resources Census -->
    <div class="p-3.5 rounded-2xl bg-cyber-800/60 border border-emerald-500/25 flex flex-col gap-2">
      <div class="flex justify-between items-center">
        <span class="text-xs font-bold text-emerald-300 flex items-center gap-1.5">
          <span>🌿 Natural Resources Inventory</span>
        </span>
        <span class="text-[10px] font-mono text-slate-400">MoEFCC Census</span>
      </div>
      
      <div class="grid grid-cols-2 gap-2 text-xs font-mono pt-1">
        <div class="flex flex-col bg-slate-900/70 p-2 rounded-lg border border-slate-800">
          <span class="text-[10px] text-slate-400">Forest Canopy</span>
          <span class="text-emerald-400 font-bold text-sm" id="stat-forest">8.5%</span>
          <span class="text-[9px] text-slate-500" id="stat-forest-area">1.4 km²</span>
        </div>
        <div class="flex flex-col bg-slate-900/70 p-2 rounded-lg border border-slate-800">
          <span class="text-[10px] text-slate-400">Water Bodies / Lakes</span>
          <span class="text-sky-400 font-bold text-sm" id="stat-lakes">3</span>
          <span class="text-[9px] text-slate-500">Wetland Basin</span>
        </div>
        <div class="flex flex-col bg-slate-900/70 p-2 rounded-lg border border-slate-800">
          <span class="text-[10px] text-slate-400">Tree Census</span>
          <span class="text-teal-400 font-bold text-sm" id="stat-trees">0.28 M</span>
          <span class="text-[9px] text-slate-500">Standing Canopy</span>
        </div>
        <div class="flex flex-col bg-slate-900/70 p-2 rounded-lg border border-slate-800">
          <span class="text-[10px] text-slate-400">Groundwater Depth</span>
          <span class="text-indigo-400 font-bold text-sm" id="stat-gw">6.8 m bgl</span>
          <span class="text-[9px] text-slate-500" id="stat-stations">3 Stations</span>
        </div>
      </div>
    </div>

    <!-- Dynamic Topological Neighbor Comparison Radar -->
    <div class="p-3.5 rounded-2xl bg-cyber-800/60 border border-slate-700/60">
      <div class="flex justify-between items-center mb-1">
        <h3 class="text-xs font-bold text-slate-200">Neighbor Footprint Radar</h3>
        <span class="text-[10px] font-mono text-cyan-400">6-Axis</span>
      </div>
      <div class="w-full h-52">
        <canvas id="radarChart"></canvas>
      </div>
    </div>

    <!-- Dynamic Neighbor Bar Chart -->
    <div class="p-3.5 rounded-2xl bg-cyber-800/60 border border-slate-700/60">
      <div class="flex justify-between items-center mb-1">
        <h3 class="text-xs font-bold text-slate-200" id="bar-title">Direct Pollutant Comparison</h3>
        <span class="text-[10px] font-mono text-slate-400">mg/L</span>
      </div>
      <div class="w-full h-44">
        <canvas id="barChart"></canvas>
      </div>
    </div>

  </aside>

  <!-- Application Logic & Deck.gl 60 FPS Controller -->
  <script>
    // -------------------------------------------------------------------------
    // Synchronous In-Memory Static Entity Catalogue (Guarantees Instant Selection)
    // -------------------------------------------------------------------------
    const ENTITY_CATALOGUE = {
  "IN-MH": {
    "name": "Maharashtra",
    "tier": "state",
    "type": "Western Peninsular State",
    "lat": 19.7515,
    "lng": 75.7139,
    "zoom": 6.8,
    "pitch": 32,
    "bearing": -10,
    "neighbors": [
      "IN-GJ",
      "IN-MP",
      "IN-TG",
      "IN-KA"
    ],
    "bod": 8.4,
    "cod": 42.0,
    "do": 5.8,
    "ph": 7.4,
    "water_flow": 320.0,
    "water_temp": 27.5,
    "aqi": 165,
    "pm25": 72.0,
    "pm10": 138.0,
    "no2": 38.0,
    "so2": 18.5,
    "air_temp": 30.2,
    "forest_cover_pct": 20.13,
    "forest_area_sqkm": 61952.0,
    "water_bodies": 14200,
    "trees_m": 420.5,
    "gw_depth": 8.4,
    "stations": 92,
    "id": "IN-MH"
  },
  "IN-GJ": {
    "name": "Gujarat",
    "tier": "state",
    "type": "Western Coastal State",
    "lat": 22.2587,
    "lng": 71.1924,
    "zoom": 6.8,
    "pitch": 30,
    "bearing": 0,
    "neighbors": [
      "IN-MH",
      "IN-RJ",
      "IN-MP"
    ],
    "bod": 9.2,
    "cod": 48.0,
    "do": 5.4,
    "ph": 7.6,
    "water_flow": 280.0,
    "water_temp": 28.0,
    "aqi": 148,
    "pm25": 65.0,
    "pm10": 125.0,
    "no2": 34.0,
    "so2": 22.0,
    "air_temp": 33.0,
    "forest_cover_pct": 11.03,
    "forest_area_sqkm": 21644.0,
    "water_bodies": 11500,
    "trees_m": 260.0,
    "gw_depth": 14.2,
    "stations": 64,
    "id": "IN-GJ"
  },
  "IN-KA": {
    "name": "Karnataka",
    "tier": "state",
    "type": "Southern Plateau State",
    "lat": 15.3173,
    "lng": 75.7139,
    "zoom": 6.8,
    "pitch": 25,
    "bearing": 0,
    "neighbors": [
      "IN-MH",
      "IN-TG",
      "IN-TN",
      "IN-KL"
    ],
    "bod": 6.1,
    "cod": 32.0,
    "do": 6.5,
    "ph": 7.3,
    "water_flow": 240.0,
    "water_temp": 25.8,
    "aqi": 95,
    "pm25": 38.0,
    "pm10": 78.0,
    "no2": 22.0,
    "so2": 12.0,
    "air_temp": 27.4,
    "forest_cover_pct": 20.11,
    "forest_area_sqkm": 38575.0,
    "water_bodies": 16800,
    "trees_m": 380.0,
    "gw_depth": 7.8,
    "stations": 58,
    "id": "IN-KA"
  },
  "IN-DL": {
    "name": "Delhi (NCT)",
    "tier": "state",
    "type": "National Capital Region",
    "lat": 28.7041,
    "lng": 77.1025,
    "zoom": 10.2,
    "pitch": 40,
    "bearing": 0,
    "neighbors": [
      "IN-UP",
      "IN-RJ"
    ],
    "bod": 14.8,
    "cod": 78.5,
    "do": 3.1,
    "ph": 7.9,
    "water_flow": 180.0,
    "water_temp": 26.0,
    "aqi": 285,
    "pm25": 142.0,
    "pm10": 265.0,
    "no2": 62.0,
    "so2": 28.0,
    "air_temp": 32.5,
    "forest_cover_pct": 13.15,
    "forest_area_sqkm": 195.0,
    "water_bodies": 620,
    "trees_m": 18.5,
    "gw_depth": 18.5,
    "stations": 42,
    "id": "IN-DL"
  },
  "IN-TN": {
    "name": "Tamil Nadu",
    "tier": "state",
    "type": "Southern Coastal State",
    "lat": 11.1271,
    "lng": 78.6569,
    "zoom": 6.8,
    "pitch": 28,
    "bearing": 0,
    "neighbors": [
      "IN-KA",
      "IN-KL",
      "IN-TG"
    ],
    "bod": 7.8,
    "cod": 39.0,
    "do": 6.0,
    "ph": 7.5,
    "water_flow": 260.0,
    "water_temp": 28.5,
    "aqi": 115,
    "pm25": 48.0,
    "pm10": 94.0,
    "no2": 26.0,
    "so2": 15.0,
    "air_temp": 31.0,
    "forest_cover_pct": 20.31,
    "forest_area_sqkm": 26419.0,
    "water_bodies": 18900,
    "trees_m": 340.0,
    "gw_depth": 9.2,
    "stations": 60,
    "id": "IN-TN"
  },
  "IN-TG": {
    "name": "Telangana",
    "tier": "state",
    "type": "Deccan Plateau State",
    "lat": 18.1124,
    "lng": 79.0193,
    "zoom": 6.8,
    "pitch": 30,
    "bearing": 0,
    "neighbors": [
      "IN-MH",
      "IN-KA",
      "IN-TN"
    ],
    "bod": 8.0,
    "cod": 41.0,
    "do": 5.7,
    "ph": 7.5,
    "water_flow": 220.0,
    "water_temp": 28.0,
    "aqi": 128,
    "pm25": 54.0,
    "pm10": 108.0,
    "no2": 30.0,
    "so2": 16.0,
    "air_temp": 32.0,
    "forest_cover_pct": 24.0,
    "forest_area_sqkm": 26969.0,
    "water_bodies": 15200,
    "trees_m": 290.0,
    "gw_depth": 10.1,
    "stations": 48,
    "id": "IN-TG"
  },
  "IN-WB": {
    "name": "West Bengal",
    "tier": "state",
    "type": "Eastern Coastal State",
    "lat": 22.9868,
    "lng": 87.855,
    "zoom": 6.8,
    "pitch": 25,
    "bearing": 0,
    "neighbors": [
      "IN-UP",
      "IN-MP"
    ],
    "bod": 10.4,
    "cod": 54.0,
    "do": 4.9,
    "ph": 7.7,
    "water_flow": 380.0,
    "water_temp": 27.0,
    "aqi": 178,
    "pm25": 82.0,
    "pm10": 156.0,
    "no2": 44.0,
    "so2": 24.0,
    "air_temp": 29.8,
    "forest_cover_pct": 19.04,
    "forest_area_sqkm": 16902.0,
    "water_bodies": 28400,
    "trees_m": 210.0,
    "gw_depth": 5.4,
    "stations": 52,
    "id": "IN-WB"
  },
  "IN-UP": {
    "name": "Uttar Pradesh",
    "tier": "state",
    "type": "Northern Gangetic Plain",
    "lat": 26.8467,
    "lng": 80.9462,
    "zoom": 6.8,
    "pitch": 25,
    "bearing": 0,
    "neighbors": [
      "IN-DL",
      "IN-MP",
      "IN-RJ",
      "IN-WB"
    ],
    "bod": 12.5,
    "cod": 64.0,
    "do": 4.2,
    "ph": 7.8,
    "water_flow": 410.0,
    "water_temp": 26.5,
    "aqi": 242,
    "pm25": 118.0,
    "pm10": 228.0,
    "no2": 52.0,
    "so2": 26.0,
    "air_temp": 32.0,
    "forest_cover_pct": 6.15,
    "forest_area_sqkm": 14818.0,
    "water_bodies": 24500,
    "trees_m": 310.0,
    "gw_depth": 11.8,
    "stations": 78,
    "id": "IN-UP"
  },
  "IN-MP": {
    "name": "Madhya Pradesh",
    "tier": "state",
    "type": "Central Forest Heartland",
    "lat": 22.9734,
    "lng": 78.6569,
    "zoom": 6.8,
    "pitch": 25,
    "bearing": 0,
    "neighbors": [
      "IN-MH",
      "IN-UP",
      "IN-GJ",
      "IN-RJ"
    ],
    "bod": 5.9,
    "cod": 29.0,
    "do": 6.8,
    "ph": 7.3,
    "water_flow": 310.0,
    "water_temp": 26.0,
    "aqi": 102,
    "pm25": 44.0,
    "pm10": 86.0,
    "no2": 24.0,
    "so2": 11.5,
    "air_temp": 30.5,
    "forest_cover_pct": 25.14,
    "forest_area_sqkm": 77493.0,
    "water_bodies": 21000,
    "trees_m": 540.0,
    "gw_depth": 8.9,
    "stations": 55,
    "id": "IN-MP"
  },
  "IN-RJ": {
    "name": "Rajasthan",
    "tier": "state",
    "type": "Northwestern Desert State",
    "lat": 27.0238,
    "lng": 74.2179,
    "zoom": 6.8,
    "pitch": 25,
    "bearing": 0,
    "neighbors": [
      "IN-GJ",
      "IN-MP",
      "IN-UP",
      "IN-DL"
    ],
    "bod": 6.8,
    "cod": 35.0,
    "do": 6.2,
    "ph": 7.6,
    "water_flow": 160.0,
    "water_temp": 27.8,
    "aqi": 155,
    "pm25": 68.0,
    "pm10": 152.0,
    "no2": 32.0,
    "so2": 18.0,
    "air_temp": 35.2,
    "forest_cover_pct": 4.87,
    "forest_area_sqkm": 16655.0,
    "water_bodies": 8900,
    "trees_m": 140.0,
    "gw_depth": 24.5,
    "stations": 46,
    "id": "IN-RJ"
  },
  "IN-KL": {
    "name": "Kerala",
    "tier": "state",
    "type": "Southwestern Coastal Tropical",
    "lat": 10.8505,
    "lng": 76.2711,
    "zoom": 7.2,
    "pitch": 30,
    "bearing": 0,
    "neighbors": [
      "IN-TN",
      "IN-KA"
    ],
    "bod": 3.9,
    "cod": 19.5,
    "do": 7.8,
    "ph": 7.1,
    "water_flow": 290.0,
    "water_temp": 26.5,
    "aqi": 62,
    "pm25": 22.0,
    "pm10": 48.0,
    "no2": 14.0,
    "so2": 8.0,
    "air_temp": 28.0,
    "forest_cover_pct": 54.7,
    "forest_area_sqkm": 21253.0,
    "water_bodies": 12800,
    "trees_m": 390.0,
    "gw_depth": 4.2,
    "stations": 38,
    "id": "IN-KL"
  },
  "MH-NM": {
    "name": "Navi Mumbai",
    "tier": "city",
    "parent_id": "IN-MH",
    "type": "Planned Industrial & Metro Port",
    "lat": 19.033,
    "lng": 73.0297,
    "zoom": 12.2,
    "pitch": 50,
    "bearing": 25,
    "neighbors": [
      "MH-MUM",
      "MH-TH",
      "MH-PU"
    ],
    "bod": 10.8,
    "cod": 56.0,
    "do": 4.9,
    "ph": 7.6,
    "water_flow": 280.0,
    "water_temp": 28.2,
    "aqi": 172,
    "pm25": 78.0,
    "pm10": 152.0,
    "no2": 44.0,
    "so2": 22.0,
    "air_temp": 31.0,
    "forest_cover_pct": 28.5,
    "forest_area_sqkm": 98.0,
    "water_bodies": 48,
    "trees_m": 12.4,
    "gw_depth": 5.8,
    "stations": 14,
    "id": "MH-NM"
  },
  "MH-MUM": {
    "name": "Mumbai City",
    "tier": "city",
    "parent_id": "IN-MH",
    "type": "Island City Financial Capital",
    "lat": 18.922,
    "lng": 72.8347,
    "zoom": 12.0,
    "pitch": 45,
    "bearing": 0,
    "neighbors": [
      "MH-NM",
      "MH-TH"
    ],
    "bod": 11.5,
    "cod": 62.0,
    "do": 4.5,
    "ph": 7.7,
    "water_flow": 410.0,
    "water_temp": 28.0,
    "aqi": 185,
    "pm25": 84.0,
    "pm10": 160.0,
    "no2": 48.0,
    "so2": 24.0,
    "air_temp": 30.5,
    "forest_cover_pct": 14.2,
    "forest_area_sqkm": 42.0,
    "water_bodies": 24,
    "trees_m": 8.5,
    "gw_depth": 3.8,
    "stations": 22,
    "id": "MH-MUM"
  },
  "MH-TH": {
    "name": "Thane",
    "tier": "city",
    "parent_id": "IN-MH",
    "type": "Industrial & Lake District",
    "lat": 19.2183,
    "lng": 72.9781,
    "zoom": 12.0,
    "pitch": 40,
    "bearing": 0,
    "neighbors": [
      "MH-NM",
      "MH-MUM",
      "MH-PU"
    ],
    "bod": 9.4,
    "cod": 48.0,
    "do": 5.2,
    "ph": 7.5,
    "water_flow": 230.0,
    "water_temp": 27.8,
    "aqi": 158,
    "pm25": 68.0,
    "pm10": 134.0,
    "no2": 36.0,
    "so2": 19.0,
    "air_temp": 30.0,
    "forest_cover_pct": 34.0,
    "forest_area_sqkm": 840.0,
    "water_bodies": 65,
    "trees_m": 24.0,
    "gw_depth": 6.2,
    "stations": 12,
    "id": "MH-TH"
  },
  "MH-PU": {
    "name": "Pune",
    "tier": "city",
    "parent_id": "IN-MH",
    "type": "Automotive & IT Hub",
    "lat": 18.5204,
    "lng": 73.8567,
    "zoom": 12.0,
    "pitch": 42,
    "bearing": 10,
    "neighbors": [
      "MH-NM",
      "MH-TH"
    ],
    "bod": 7.9,
    "cod": 41.0,
    "do": 6.2,
    "ph": 7.3,
    "water_flow": 290.0,
    "water_temp": 25.5,
    "aqi": 132,
    "pm25": 56.0,
    "pm10": 112.0,
    "no2": 32.0,
    "so2": 14.5,
    "air_temp": 28.5,
    "forest_cover_pct": 12.8,
    "forest_area_sqkm": 2004.0,
    "water_bodies": 84,
    "trees_m": 48.0,
    "gw_depth": 7.1,
    "stations": 20,
    "id": "MH-PU"
  },
  "DL-ND": {
    "name": "New Delhi",
    "tier": "city",
    "parent_id": "IN-DL",
    "type": "Government Core & Green Buffer",
    "lat": 28.6139,
    "lng": 77.209,
    "zoom": 12.2,
    "pitch": 45,
    "bearing": 0,
    "neighbors": [
      "DL-SO",
      "DL-NO"
    ],
    "bod": 12.8,
    "cod": 68.0,
    "do": 3.8,
    "ph": 7.8,
    "water_flow": 120.0,
    "water_temp": 26.5,
    "aqi": 245,
    "pm25": 128.0,
    "pm10": 235.0,
    "no2": 54.0,
    "so2": 22.0,
    "air_temp": 31.8,
    "forest_cover_pct": 18.2,
    "forest_area_sqkm": 35.0,
    "water_bodies": 120,
    "trees_m": 4.2,
    "gw_depth": 16.5,
    "stations": 12,
    "id": "DL-ND"
  },
  "DL-SO": {
    "name": "South Delhi",
    "tier": "city",
    "parent_id": "IN-DL",
    "type": "Mixed Tech & Commercial District",
    "lat": 28.4817,
    "lng": 77.1873,
    "zoom": 12.0,
    "pitch": 45,
    "bearing": 0,
    "neighbors": [
      "DL-ND",
      "DL-NO"
    ],
    "bod": 13.9,
    "cod": 74.0,
    "do": 3.2,
    "ph": 7.9,
    "water_flow": 145.0,
    "water_temp": 26.2,
    "aqi": 272,
    "pm25": 138.0,
    "pm10": 255.0,
    "no2": 58.0,
    "so2": 26.0,
    "air_temp": 32.2,
    "forest_cover_pct": 16.5,
    "forest_area_sqkm": 42.0,
    "water_bodies": 140,
    "trees_m": 4.8,
    "gw_depth": 19.8,
    "stations": 14,
    "id": "DL-SO"
  },
  "DL-NO": {
    "name": "North Delhi",
    "tier": "city",
    "parent_id": "IN-DL",
    "type": "Yamuna River Basin & Transport",
    "lat": 28.72,
    "lng": 77.16,
    "zoom": 12.0,
    "pitch": 40,
    "bearing": 0,
    "neighbors": [
      "DL-ND",
      "DL-SO"
    ],
    "bod": 16.2,
    "cod": 84.0,
    "do": 2.4,
    "ph": 8.1,
    "water_flow": 190.0,
    "water_temp": 26.0,
    "aqi": 298,
    "pm25": 156.0,
    "pm10": 280.0,
    "no2": 66.0,
    "so2": 31.0,
    "air_temp": 32.5,
    "forest_cover_pct": 9.4,
    "forest_area_sqkm": 24.0,
    "water_bodies": 85,
    "trees_m": 3.1,
    "gw_depth": 21.0,
    "stations": 11,
    "id": "DL-NO"
  },
  "GJ-AHM": {
    "name": "Ahmedabad",
    "tier": "city",
    "parent_id": "IN-GJ",
    "type": "Commercial & Textile Metro",
    "lat": 23.0225,
    "lng": 72.5714,
    "zoom": 11.8,
    "pitch": 40,
    "bearing": 0,
    "neighbors": [
      "GJ-SUR",
      "GJ-BRD"
    ],
    "bod": 10.8,
    "cod": 58.0,
    "do": 4.8,
    "ph": 7.7,
    "water_flow": 260.0,
    "water_temp": 28.5,
    "aqi": 168,
    "pm25": 78.0,
    "pm10": 154.0,
    "no2": 39.0,
    "so2": 24.0,
    "air_temp": 34.0,
    "forest_cover_pct": 8.4,
    "forest_area_sqkm": 68.0,
    "water_bodies": 38,
    "trees_m": 7.5,
    "gw_depth": 15.2,
    "stations": 16,
    "id": "GJ-AHM"
  },
  "GJ-SUR": {
    "name": "Surat",
    "tier": "city",
    "parent_id": "IN-GJ",
    "type": "Textile & Diamond Port City",
    "lat": 21.1702,
    "lng": 72.8311,
    "zoom": 11.8,
    "pitch": 38,
    "bearing": 0,
    "neighbors": [
      "GJ-AHM",
      "GJ-BRD"
    ],
    "bod": 9.4,
    "cod": 49.0,
    "do": 5.5,
    "ph": 7.5,
    "water_flow": 240.0,
    "water_temp": 28.2,
    "aqi": 142,
    "pm25": 62.0,
    "pm10": 120.0,
    "no2": 32.0,
    "so2": 20.0,
    "air_temp": 32.8,
    "forest_cover_pct": 12.2,
    "forest_area_sqkm": 110.0,
    "water_bodies": 46,
    "trees_m": 9.8,
    "gw_depth": 11.4,
    "stations": 12,
    "id": "GJ-SUR"
  },
  "GJ-BRD": {
    "name": "Vadodara",
    "tier": "city",
    "parent_id": "IN-GJ",
    "type": "Chemical & Petrochemical Hub",
    "lat": 22.3072,
    "lng": 73.1812,
    "zoom": 11.8,
    "pitch": 38,
    "bearing": 0,
    "neighbors": [
      "GJ-AHM",
      "GJ-SUR"
    ],
    "bod": 10.2,
    "cod": 55.0,
    "do": 5.0,
    "ph": 7.6,
    "water_flow": 210.0,
    "water_temp": 28.0,
    "aqi": 152,
    "pm25": 66.0,
    "pm10": 130.0,
    "no2": 35.0,
    "so2": 23.0,
    "air_temp": 33.5,
    "forest_cover_pct": 13.5,
    "forest_area_sqkm": 145.0,
    "water_bodies": 40,
    "trees_m": 8.2,
    "gw_depth": 13.0,
    "stations": 10,
    "id": "GJ-BRD"
  },
  "KA-BLR": {
    "name": "Bengaluru Urban",
    "tier": "city",
    "parent_id": "IN-KA",
    "type": "Silicon Valley IT Metro",
    "lat": 12.9716,
    "lng": 77.5946,
    "zoom": 12.0,
    "pitch": 48,
    "bearing": 15,
    "neighbors": [
      "KA-MYS"
    ],
    "bod": 8.8,
    "cod": 44.0,
    "do": 5.9,
    "ph": 7.4,
    "water_flow": 310.0,
    "water_temp": 24.8,
    "aqi": 105,
    "pm25": 44.0,
    "pm10": 88.0,
    "no2": 28.0,
    "so2": 11.0,
    "air_temp": 26.5,
    "forest_cover_pct": 14.8,
    "forest_area_sqkm": 324.0,
    "water_bodies": 182,
    "trees_m": 18.4,
    "gw_depth": 12.1,
    "stations": 24,
    "id": "KA-BLR"
  },
  "KA-MYS": {
    "name": "Mysuru",
    "tier": "city",
    "parent_id": "IN-KA",
    "type": "Heritage Clean City",
    "lat": 12.2958,
    "lng": 76.6394,
    "zoom": 11.5,
    "pitch": 30,
    "bearing": 0,
    "neighbors": [
      "KA-BLR"
    ],
    "bod": 4.5,
    "cod": 22.0,
    "do": 7.2,
    "ph": 7.2,
    "water_flow": 140.0,
    "water_temp": 24.2,
    "aqi": 72,
    "pm25": 28.0,
    "pm10": 58.0,
    "no2": 18.0,
    "so2": 8.0,
    "air_temp": 25.8,
    "forest_cover_pct": 24.5,
    "forest_area_sqkm": 1560.0,
    "water_bodies": 94,
    "trees_m": 26.0,
    "gw_depth": 6.8,
    "stations": 8,
    "id": "KA-MYS"
  },
  "TN-CHN": {
    "name": "Chennai",
    "tier": "city",
    "parent_id": "IN-TN",
    "type": "Automotive & Port Metro",
    "lat": 13.0827,
    "lng": 80.2707,
    "zoom": 11.8,
    "pitch": 42,
    "bearing": 0,
    "neighbors": [
      "TN-CBE"
    ],
    "bod": 9.2,
    "cod": 46.0,
    "do": 5.6,
    "ph": 7.6,
    "water_flow": 280.0,
    "water_temp": 29.5,
    "aqi": 118,
    "pm25": 52.0,
    "pm10": 98.0,
    "no2": 29.0,
    "so2": 17.0,
    "air_temp": 32.5,
    "forest_cover_pct": 15.2,
    "forest_area_sqkm": 64.0,
    "water_bodies": 68,
    "trees_m": 8.9,
    "gw_depth": 7.4,
    "stations": 18,
    "id": "TN-CHN"
  },
  "TN-CBE": {
    "name": "Coimbatore",
    "tier": "city",
    "parent_id": "IN-TN",
    "type": "Textile & Pump Engineering Core",
    "lat": 11.0168,
    "lng": 76.9558,
    "zoom": 11.5,
    "pitch": 32,
    "bearing": 0,
    "neighbors": [
      "TN-CHN"
    ],
    "bod": 6.8,
    "cod": 34.0,
    "do": 6.4,
    "ph": 7.4,
    "water_flow": 180.0,
    "water_temp": 26.8,
    "aqi": 88,
    "pm25": 36.0,
    "pm10": 74.0,
    "no2": 21.0,
    "so2": 10.0,
    "air_temp": 28.0,
    "forest_cover_pct": 22.0,
    "forest_area_sqkm": 1100.0,
    "water_bodies": 54,
    "trees_m": 15.2,
    "gw_depth": 8.1,
    "stations": 10,
    "id": "TN-CBE"
  },
  "TG-HYD": {
    "name": "Hyderabad",
    "tier": "city",
    "parent_id": "IN-TG",
    "type": "IT & Bulk Drug Pharma Metro",
    "lat": 17.385,
    "lng": 78.4867,
    "zoom": 11.8,
    "pitch": 45,
    "bearing": 10,
    "neighbors": [
      "TG-WRG"
    ],
    "bod": 8.9,
    "cod": 45.0,
    "do": 5.4,
    "ph": 7.5,
    "water_flow": 270.0,
    "water_temp": 28.0,
    "aqi": 138,
    "pm25": 58.0,
    "pm10": 118.0,
    "no2": 32.0,
    "so2": 16.0,
    "air_temp": 32.0,
    "forest_cover_pct": 12.6,
    "forest_area_sqkm": 82.0,
    "water_bodies": 74,
    "trees_m": 14.5,
    "gw_depth": 8.8,
    "stations": 20,
    "id": "TG-HYD"
  },
  "TG-WRG": {
    "name": "Warangal",
    "tier": "city",
    "parent_id": "IN-TG",
    "type": "Historical Agro-Industrial City",
    "lat": 17.9689,
    "lng": 79.5941,
    "zoom": 11.5,
    "pitch": 30,
    "bearing": 0,
    "neighbors": [
      "TG-HYD"
    ],
    "bod": 5.9,
    "cod": 30.0,
    "do": 6.5,
    "ph": 7.3,
    "water_flow": 120.0,
    "water_temp": 27.5,
    "aqi": 92,
    "pm25": 38.0,
    "pm10": 80.0,
    "no2": 22.0,
    "so2": 11.0,
    "air_temp": 31.5,
    "forest_cover_pct": 28.5,
    "forest_area_sqkm": 860.0,
    "water_bodies": 88,
    "trees_m": 18.0,
    "gw_depth": 7.6,
    "stations": 8,
    "id": "TG-WRG"
  },
  "WB-KOL": {
    "name": "Kolkata",
    "tier": "city",
    "parent_id": "IN-WB",
    "type": "Riverine Cultural Metro",
    "lat": 22.5726,
    "lng": 88.3639,
    "zoom": 11.8,
    "pitch": 40,
    "bearing": 0,
    "neighbors": [
      "WB-HWH"
    ],
    "bod": 11.8,
    "cod": 61.0,
    "do": 4.2,
    "ph": 7.7,
    "water_flow": 360.0,
    "water_temp": 27.5,
    "aqi": 198,
    "pm25": 92.0,
    "pm10": 172.0,
    "no2": 48.0,
    "so2": 26.0,
    "air_temp": 30.2,
    "forest_cover_pct": 10.4,
    "forest_area_sqkm": 21.0,
    "water_bodies": 160,
    "trees_m": 5.4,
    "gw_depth": 4.5,
    "stations": 16,
    "id": "WB-KOL"
  },
  "WB-HWH": {
    "name": "Howrah",
    "tier": "city",
    "parent_id": "IN-WB",
    "type": "Industrial Foundries & Port Gateway",
    "lat": 22.5958,
    "lng": 88.2636,
    "zoom": 11.8,
    "pitch": 38,
    "bearing": 0,
    "neighbors": [
      "WB-KOL"
    ],
    "bod": 12.4,
    "cod": 66.0,
    "do": 3.9,
    "ph": 7.8,
    "water_flow": 240.0,
    "water_temp": 27.8,
    "aqi": 215,
    "pm25": 105.0,
    "pm10": 195.0,
    "no2": 52.0,
    "so2": 28.0,
    "air_temp": 30.5,
    "forest_cover_pct": 8.2,
    "forest_area_sqkm": 18.0,
    "water_bodies": 95,
    "trees_m": 4.1,
    "gw_depth": 4.8,
    "stations": 10,
    "id": "WB-HWH"
  },
  "UP-NOI": {
    "name": "Noida",
    "tier": "city",
    "parent_id": "IN-UP",
    "type": "Industrial & Tech NCR Node",
    "lat": 28.5355,
    "lng": 77.391,
    "zoom": 12.0,
    "pitch": 46,
    "bearing": 15,
    "neighbors": [
      "UP-KNP",
      "UP-LKO",
      "DL-ND"
    ],
    "bod": 14.2,
    "cod": 74.0,
    "do": 3.4,
    "ph": 7.9,
    "water_flow": 160.0,
    "water_temp": 26.5,
    "aqi": 268,
    "pm25": 134.0,
    "pm10": 248.0,
    "no2": 56.0,
    "so2": 27.0,
    "air_temp": 32.5,
    "forest_cover_pct": 9.8,
    "forest_area_sqkm": 38.0,
    "water_bodies": 42,
    "trees_m": 3.8,
    "gw_depth": 14.8,
    "stations": 12,
    "id": "UP-NOI"
  },
  "UP-KNP": {
    "name": "Kanpur",
    "tier": "city",
    "parent_id": "IN-UP",
    "type": "Leather Tannery & Ganga Basin Core",
    "lat": 26.4499,
    "lng": 80.3319,
    "zoom": 11.8,
    "pitch": 40,
    "bearing": 0,
    "neighbors": [
      "UP-NOI",
      "UP-LKO"
    ],
    "bod": 16.5,
    "cod": 85.0,
    "do": 3.1,
    "ph": 8.2,
    "water_flow": 280.0,
    "water_temp": 26.2,
    "aqi": 280,
    "pm25": 145.0,
    "pm10": 270.0,
    "no2": 62.0,
    "so2": 32.0,
    "air_temp": 32.0,
    "forest_cover_pct": 5.4,
    "forest_area_sqkm": 48.0,
    "water_bodies": 52,
    "trees_m": 4.9,
    "gw_depth": 12.5,
    "stations": 14,
    "id": "UP-KNP"
  },
  "UP-LKO": {
    "name": "Lucknow",
    "tier": "city",
    "parent_id": "IN-UP",
    "type": "State Administrative Capital",
    "lat": 26.8467,
    "lng": 80.9462,
    "zoom": 11.8,
    "pitch": 35,
    "bearing": 0,
    "neighbors": [
      "UP-NOI",
      "UP-KNP"
    ],
    "bod": 11.0,
    "cod": 56.0,
    "do": 4.6,
    "ph": 7.6,
    "water_flow": 220.0,
    "water_temp": 26.0,
    "aqi": 220,
    "pm25": 110.0,
    "pm10": 205.0,
    "no2": 48.0,
    "so2": 22.0,
    "air_temp": 31.8,
    "forest_cover_pct": 8.6,
    "forest_area_sqkm": 72.0,
    "water_bodies": 68,
    "trees_m": 6.8,
    "gw_depth": 10.2,
    "stations": 12,
    "id": "UP-LKO"
  },
  "MP-IND": {
    "name": "Indore",
    "tier": "city",
    "parent_id": "IN-MP",
    "type": "Cleanest City & Commercial Hub",
    "lat": 22.7196,
    "lng": 75.8577,
    "zoom": 11.8,
    "pitch": 35,
    "bearing": 0,
    "neighbors": [
      "MP-BHP"
    ],
    "bod": 5.8,
    "cod": 29.0,
    "do": 6.8,
    "ph": 7.4,
    "water_flow": 210.0,
    "water_temp": 26.0,
    "aqi": 98,
    "pm25": 42.0,
    "pm10": 84.0,
    "no2": 24.0,
    "so2": 11.0,
    "air_temp": 29.5,
    "forest_cover_pct": 16.2,
    "forest_area_sqkm": 148.0,
    "water_bodies": 56,
    "trees_m": 12.0,
    "gw_depth": 8.2,
    "stations": 14,
    "id": "MP-IND"
  },
  "MP-BHP": {
    "name": "Bhopal",
    "tier": "city",
    "parent_id": "IN-MP",
    "type": "City of Lakes & Green Capital",
    "lat": 23.2599,
    "lng": 77.4126,
    "zoom": 11.8,
    "pitch": 35,
    "bearing": 0,
    "neighbors": [
      "MP-IND"
    ],
    "bod": 5.2,
    "cod": 26.0,
    "do": 7.1,
    "ph": 7.3,
    "water_flow": 190.0,
    "water_temp": 25.5,
    "aqi": 90,
    "pm25": 38.0,
    "pm10": 78.0,
    "no2": 21.0,
    "so2": 9.5,
    "air_temp": 29.0,
    "forest_cover_pct": 28.5,
    "forest_area_sqkm": 420.0,
    "water_bodies": 72,
    "trees_m": 19.5,
    "gw_depth": 6.5,
    "stations": 12,
    "id": "MP-BHP"
  },
  "RJ-JPR": {
    "name": "Jaipur",
    "tier": "city",
    "parent_id": "IN-RJ",
    "type": "Pink City & Tourism Metro",
    "lat": 26.9124,
    "lng": 75.7873,
    "zoom": 11.8,
    "pitch": 35,
    "bearing": 0,
    "neighbors": [
      "RJ-JDH"
    ],
    "bod": 7.2,
    "cod": 38.0,
    "do": 6.1,
    "ph": 7.6,
    "water_flow": 180.0,
    "water_temp": 27.2,
    "aqi": 162,
    "pm25": 72.0,
    "pm10": 165.0,
    "no2": 32.0,
    "so2": 18.0,
    "air_temp": 34.5,
    "forest_cover_pct": 8.9,
    "forest_area_sqkm": 94.0,
    "water_bodies": 28,
    "trees_m": 6.4,
    "gw_depth": 22.4,
    "stations": 14,
    "id": "RJ-JPR"
  },
  "RJ-JDH": {
    "name": "Jodhpur",
    "tier": "city",
    "parent_id": "IN-RJ",
    "type": "Sun City & Arid Industrial Node",
    "lat": 26.2389,
    "lng": 73.0243,
    "zoom": 11.5,
    "pitch": 30,
    "bearing": 0,
    "neighbors": [
      "RJ-JPR"
    ],
    "bod": 8.0,
    "cod": 42.0,
    "do": 5.8,
    "ph": 7.7,
    "water_flow": 130.0,
    "water_temp": 28.5,
    "aqi": 175,
    "pm25": 79.0,
    "pm10": 178.0,
    "no2": 34.0,
    "so2": 19.5,
    "air_temp": 36.0,
    "forest_cover_pct": 3.8,
    "forest_area_sqkm": 45.0,
    "water_bodies": 19,
    "trees_m": 3.2,
    "gw_depth": 31.0,
    "stations": 8,
    "id": "RJ-JDH"
  },
  "KL-COK": {
    "name": "Kochi",
    "tier": "city",
    "parent_id": "IN-KL",
    "type": "Port & Coastal Commercial Metro",
    "lat": 9.9312,
    "lng": 76.2673,
    "zoom": 12.0,
    "pitch": 40,
    "bearing": 0,
    "neighbors": [
      "KL-TVM"
    ],
    "bod": 4.1,
    "cod": 21.0,
    "do": 7.6,
    "ph": 7.2,
    "water_flow": 220.0,
    "water_temp": 27.0,
    "aqi": 68,
    "pm25": 25.0,
    "pm10": 52.0,
    "no2": 16.0,
    "so2": 9.0,
    "air_temp": 28.5,
    "forest_cover_pct": 42.5,
    "forest_area_sqkm": 420.0,
    "water_bodies": 142,
    "trees_m": 24.5,
    "gw_depth": 3.8,
    "stations": 10,
    "id": "KL-COK"
  },
  "KL-TVM": {
    "name": "Thiruvananthapuram",
    "tier": "city",
    "parent_id": "IN-KL",
    "type": "Coastal Green Capital",
    "lat": 8.5241,
    "lng": 76.9366,
    "zoom": 11.8,
    "pitch": 35,
    "bearing": 0,
    "neighbors": [
      "KL-COK"
    ],
    "bod": 3.6,
    "cod": 18.0,
    "do": 8.0,
    "ph": 7.1,
    "water_flow": 180.0,
    "water_temp": 26.5,
    "aqi": 56,
    "pm25": 19.0,
    "pm10": 42.0,
    "no2": 12.0,
    "so2": 7.0,
    "air_temp": 27.8,
    "forest_cover_pct": 51.0,
    "forest_area_sqkm": 580.0,
    "water_bodies": 98,
    "trees_m": 28.0,
    "gw_depth": 4.1,
    "stations": 8,
    "id": "KL-TVM"
  },
  "NM-MAHAPE": {
    "name": "Mahape (MIDC Industrial)",
    "tier": "area",
    "parent_id": "MH-NM",
    "type": "Heavy Chemical & Manufacturing MIDC",
    "lat": 19.112,
    "lng": 73.023,
    "zoom": 14.5,
    "pitch": 62,
    "bearing": 45,
    "neighbors": [
      "NM-VASHI",
      "NM-AIROLI",
      "NM-TALOJA"
    ],
    "bod": 15.8,
    "cod": 84.0,
    "do": 3.2,
    "ph": 8.1,
    "water_flow": 142.0,
    "water_temp": 29.1,
    "aqi": 224,
    "pm25": 108.0,
    "pm10": 210.0,
    "no2": 58.0,
    "so2": 32.0,
    "air_temp": 32.2,
    "forest_cover_pct": 8.5,
    "forest_area_sqkm": 1.4,
    "water_bodies": 3,
    "trees_m": 0.28,
    "gw_depth": 6.8,
    "stations": 3,
    "id": "NM-MAHAPE"
  },
  "NM-VASHI": {
    "name": "Vashi (Sector 17 / Creek)",
    "tier": "area",
    "parent_id": "MH-NM",
    "type": "Commercial & Estuary Outflow",
    "lat": 19.0771,
    "lng": 72.9986,
    "zoom": 14.2,
    "pitch": 58,
    "bearing": 30,
    "neighbors": [
      "NM-MAHAPE",
      "NM-NERUL",
      "NM-BELAPUR"
    ],
    "bod": 11.2,
    "cod": 58.0,
    "do": 4.5,
    "ph": 7.6,
    "water_flow": 115.0,
    "water_temp": 28.0,
    "aqi": 175,
    "pm25": 78.0,
    "pm10": 148.0,
    "no2": 45.0,
    "so2": 20.0,
    "air_temp": 30.6,
    "forest_cover_pct": 14.5,
    "forest_area_sqkm": 2.8,
    "water_bodies": 4,
    "trees_m": 0.45,
    "gw_depth": 3.9,
    "stations": 3,
    "id": "NM-VASHI"
  },
  "NM-BELAPUR": {
    "name": "CBD Belapur (Marina Core)",
    "tier": "area",
    "parent_id": "MH-NM",
    "type": "Administrative Marine Core",
    "lat": 19.0178,
    "lng": 73.04,
    "zoom": 14.5,
    "pitch": 60,
    "bearing": 40,
    "neighbors": [
      "NM-NERUL",
      "NM-KHARGHAR",
      "NM-VASHI"
    ],
    "bod": 7.4,
    "cod": 36.0,
    "do": 6.4,
    "ph": 7.4,
    "water_flow": 98.0,
    "water_temp": 27.4,
    "aqi": 138,
    "pm25": 58.0,
    "pm10": 114.0,
    "no2": 32.0,
    "so2": 14.0,
    "air_temp": 30.2,
    "forest_cover_pct": 32.0,
    "forest_area_sqkm": 5.4,
    "water_bodies": 6,
    "trees_m": 0.95,
    "gw_depth": 4.5,
    "stations": 3,
    "id": "NM-BELAPUR"
  },
  "NM-NERUL": {
    "name": "Nerul (Palm Beach Lake)",
    "tier": "area",
    "parent_id": "MH-NM",
    "type": "Residential Wetland Corridor",
    "lat": 19.033,
    "lng": 73.015,
    "zoom": 14.3,
    "pitch": 55,
    "bearing": 20,
    "neighbors": [
      "NM-VASHI",
      "NM-BELAPUR",
      "NM-KHARGHAR"
    ],
    "bod": 6.8,
    "cod": 32.5,
    "do": 6.9,
    "ph": 7.3,
    "water_flow": 82.0,
    "water_temp": 27.2,
    "aqi": 128,
    "pm25": 52.0,
    "pm10": 104.0,
    "no2": 28.0,
    "so2": 12.0,
    "air_temp": 30.0,
    "forest_cover_pct": 35.8,
    "forest_area_sqkm": 6.1,
    "water_bodies": 8,
    "trees_m": 1.2,
    "gw_depth": 4.1,
    "stations": 2,
    "id": "NM-NERUL"
  },
  "NM-KHARGHAR": {
    "name": "Kharghar (Valley Buffer)",
    "tier": "area",
    "parent_id": "MH-NM",
    "type": "Valley Buffer & Green Lungs",
    "lat": 19.0473,
    "lng": 73.0699,
    "zoom": 14.0,
    "pitch": 52,
    "bearing": -15,
    "neighbors": [
      "NM-BELAPUR",
      "NM-NERUL",
      "NM-TALOJA"
    ],
    "bod": 5.6,
    "cod": 28.0,
    "do": 7.2,
    "ph": 7.2,
    "water_flow": 74.0,
    "water_temp": 26.8,
    "aqi": 118,
    "pm25": 46.0,
    "pm10": 92.0,
    "no2": 24.0,
    "so2": 10.5,
    "air_temp": 29.5,
    "forest_cover_pct": 48.2,
    "forest_area_sqkm": 14.2,
    "water_bodies": 9,
    "trees_m": 2.4,
    "gw_depth": 5.1,
    "stations": 2,
    "id": "NM-KHARGHAR"
  },
  "NM-AIROLI": {
    "name": "Airoli (TTC Tech corridor)",
    "tier": "area",
    "parent_id": "MH-NM",
    "type": "Tech Nexus & Bridge",
    "lat": 19.155,
    "lng": 72.998,
    "zoom": 14.2,
    "pitch": 56,
    "bearing": 10,
    "neighbors": [
      "NM-MAHAPE",
      "NM-VASHI"
    ],
    "bod": 10.5,
    "cod": 54.0,
    "do": 4.8,
    "ph": 7.5,
    "water_flow": 128.0,
    "water_temp": 28.2,
    "aqi": 182,
    "pm25": 82.0,
    "pm10": 156.0,
    "no2": 48.0,
    "so2": 22.0,
    "air_temp": 31.0,
    "forest_cover_pct": 18.0,
    "forest_area_sqkm": 3.2,
    "water_bodies": 5,
    "trees_m": 0.65,
    "gw_depth": 4.8,
    "stations": 2,
    "id": "NM-AIROLI"
  },
  "NM-TALOJA": {
    "name": "Taloja (Chemical Belt)",
    "tier": "area",
    "parent_id": "MH-NM",
    "type": "Special Chemical CETP Outflow",
    "lat": 19.055,
    "lng": 73.125,
    "zoom": 14.3,
    "pitch": 60,
    "bearing": -35,
    "neighbors": [
      "NM-MAHAPE",
      "NM-KHARGHAR"
    ],
    "bod": 18.2,
    "cod": 96.0,
    "do": 2.4,
    "ph": 8.4,
    "water_flow": 165.0,
    "water_temp": 29.8,
    "aqi": 258,
    "pm25": 126.0,
    "pm10": 245.0,
    "no2": 66.0,
    "so2": 38.0,
    "air_temp": 33.0,
    "forest_cover_pct": 11.0,
    "forest_area_sqkm": 2.6,
    "water_bodies": 4,
    "trees_m": 0.32,
    "gw_depth": 7.2,
    "stations": 3,
    "id": "NM-TALOJA"
  },
  "MUM-BKC": {
    "name": "BKC (Mithi River Basin)",
    "tier": "area",
    "parent_id": "MH-MUM",
    "type": "Financial Core & Estuary",
    "lat": 19.065,
    "lng": 72.868,
    "zoom": 14.2,
    "pitch": 55,
    "bearing": 15,
    "neighbors": [
      "MUM-CHEM",
      "MUM-NP"
    ],
    "bod": 16.5,
    "cod": 82.0,
    "do": 2.8,
    "ph": 7.9,
    "water_flow": 180.0,
    "water_temp": 28.5,
    "aqi": 198,
    "pm25": 92.0,
    "pm10": 174.0,
    "no2": 52.0,
    "so2": 26.0,
    "air_temp": 31.0,
    "forest_cover_pct": 6.8,
    "forest_area_sqkm": 1.1,
    "water_bodies": 3,
    "trees_m": 0.35,
    "gw_depth": 3.2,
    "stations": 3,
    "id": "MUM-BKC"
  },
  "MUM-CHEM": {
    "name": "Chembur Industrial Zone",
    "tier": "area",
    "parent_id": "MH-MUM",
    "type": "Refinery & Petrochemical Core",
    "lat": 19.052,
    "lng": 72.898,
    "zoom": 14.2,
    "pitch": 55,
    "bearing": 20,
    "neighbors": [
      "MUM-BKC",
      "NM-VASHI"
    ],
    "bod": 14.8,
    "cod": 78.0,
    "do": 3.4,
    "ph": 8.0,
    "water_flow": 165.0,
    "water_temp": 29.0,
    "aqi": 220,
    "pm25": 105.0,
    "pm10": 198.0,
    "no2": 56.0,
    "so2": 32.0,
    "air_temp": 32.0,
    "forest_cover_pct": 9.2,
    "forest_area_sqkm": 1.6,
    "water_bodies": 2,
    "trees_m": 0.42,
    "gw_depth": 4.1,
    "stations": 3,
    "id": "MUM-CHEM"
  },
  "MUM-NP": {
    "name": "Nariman Point Coast",
    "tier": "area",
    "parent_id": "MH-MUM",
    "type": "Coastal Marine Front",
    "lat": 18.926,
    "lng": 72.822,
    "zoom": 14.4,
    "pitch": 50,
    "bearing": 0,
    "neighbors": [
      "MUM-BKC"
    ],
    "bod": 6.5,
    "cod": 32.0,
    "do": 6.8,
    "ph": 7.5,
    "water_flow": 120.0,
    "water_temp": 27.5,
    "aqi": 125,
    "pm25": 54.0,
    "pm10": 108.0,
    "no2": 31.0,
    "so2": 15.0,
    "air_temp": 29.8,
    "forest_cover_pct": 11.5,
    "forest_area_sqkm": 0.8,
    "water_bodies": 2,
    "trees_m": 0.25,
    "gw_depth": 2.8,
    "stations": 2,
    "id": "MUM-NP"
  },
  "PU-HINJ": {
    "name": "Hinjewadi Tech Park",
    "tier": "area",
    "parent_id": "MH-PU",
    "type": "High-Tech IT SEZ",
    "lat": 18.5913,
    "lng": 73.7389,
    "zoom": 14.2,
    "pitch": 52,
    "bearing": 10,
    "neighbors": [
      "PU-BHOS"
    ],
    "bod": 6.8,
    "cod": 34.0,
    "do": 6.6,
    "ph": 7.3,
    "water_flow": 110.0,
    "water_temp": 25.0,
    "aqi": 110,
    "pm25": 46.0,
    "pm10": 94.0,
    "no2": 26.0,
    "so2": 12.0,
    "air_temp": 27.5,
    "forest_cover_pct": 21.0,
    "forest_area_sqkm": 5.8,
    "water_bodies": 6,
    "trees_m": 1.1,
    "gw_depth": 8.2,
    "stations": 3,
    "id": "PU-HINJ"
  },
  "PU-BHOS": {
    "name": "Bhosari MIDC",
    "tier": "area",
    "parent_id": "MH-PU",
    "type": "Automotive Engineering Cluster",
    "lat": 18.625,
    "lng": 73.845,
    "zoom": 14.2,
    "pitch": 58,
    "bearing": 25,
    "neighbors": [
      "PU-HINJ"
    ],
    "bod": 13.5,
    "cod": 68.0,
    "do": 4.1,
    "ph": 7.8,
    "water_flow": 155.0,
    "water_temp": 26.5,
    "aqi": 185,
    "pm25": 86.0,
    "pm10": 168.0,
    "no2": 46.0,
    "so2": 24.0,
    "air_temp": 29.5,
    "forest_cover_pct": 7.5,
    "forest_area_sqkm": 1.8,
    "water_bodies": 3,
    "trees_m": 0.38,
    "gw_depth": 6.8,
    "stations": 3,
    "id": "PU-BHOS"
  },
  "AHM-NARODA": {
    "name": "Naroda Industrial GIDC",
    "tier": "area",
    "parent_id": "GJ-AHM",
    "type": "Chemical & Dyes Cluster",
    "lat": 23.072,
    "lng": 72.658,
    "zoom": 14.4,
    "pitch": 60,
    "bearing": 30,
    "neighbors": [
      "AHM-SGHI",
      "AHM-VATVA"
    ],
    "bod": 16.2,
    "cod": 86.0,
    "do": 3.0,
    "ph": 8.2,
    "water_flow": 138.0,
    "water_temp": 29.4,
    "aqi": 218,
    "pm25": 102.0,
    "pm10": 204.0,
    "no2": 54.0,
    "so2": 31.0,
    "air_temp": 34.5,
    "forest_cover_pct": 4.5,
    "forest_area_sqkm": 0.8,
    "water_bodies": 2,
    "trees_m": 0.16,
    "gw_depth": 18.4,
    "stations": 3,
    "id": "AHM-NARODA"
  },
  "AHM-SGHI": {
    "name": "SG Highway Tech Corridor",
    "tier": "area",
    "parent_id": "GJ-AHM",
    "type": "Commercial IT Corridor",
    "lat": 23.045,
    "lng": 72.51,
    "zoom": 14.2,
    "pitch": 52,
    "bearing": 15,
    "neighbors": [
      "AHM-NARODA",
      "AHM-VATVA"
    ],
    "bod": 7.9,
    "cod": 41.0,
    "do": 6.0,
    "ph": 7.4,
    "water_flow": 86.0,
    "water_temp": 27.8,
    "aqi": 138,
    "pm25": 58.0,
    "pm10": 118.0,
    "no2": 32.0,
    "so2": 16.0,
    "air_temp": 33.2,
    "forest_cover_pct": 16.2,
    "forest_area_sqkm": 2.9,
    "water_bodies": 4,
    "trees_m": 0.62,
    "gw_depth": 12.8,
    "stations": 2,
    "id": "AHM-SGHI"
  },
  "AHM-VATVA": {
    "name": "Vatva GIDC Chemical Zone",
    "tier": "area",
    "parent_id": "GJ-AHM",
    "type": "Heavy Chemical CETP Zone",
    "lat": 22.96,
    "lng": 72.63,
    "zoom": 14.2,
    "pitch": 58,
    "bearing": 20,
    "neighbors": [
      "AHM-NARODA",
      "AHM-SGHI"
    ],
    "bod": 17.5,
    "cod": 92.0,
    "do": 2.6,
    "ph": 8.3,
    "water_flow": 160.0,
    "water_temp": 29.8,
    "aqi": 235,
    "pm25": 115.0,
    "pm10": 225.0,
    "no2": 60.0,
    "so2": 35.0,
    "air_temp": 35.0,
    "forest_cover_pct": 3.8,
    "forest_area_sqkm": 0.7,
    "water_bodies": 2,
    "trees_m": 0.12,
    "gw_depth": 19.5,
    "stations": 3,
    "id": "AHM-VATVA"
  },
  "SUR-SACH": {
    "name": "Sachin GIDC Textile Belt",
    "tier": "area",
    "parent_id": "GJ-SUR",
    "type": "Textile Dyeing & CETP Zone",
    "lat": 21.08,
    "lng": 72.88,
    "zoom": 14.2,
    "pitch": 55,
    "bearing": 20,
    "neighbors": [
      "SUR-ADAJ"
    ],
    "bod": 14.5,
    "cod": 76.0,
    "do": 3.5,
    "ph": 8.0,
    "water_flow": 145.0,
    "water_temp": 29.0,
    "aqi": 182,
    "pm25": 84.0,
    "pm10": 165.0,
    "no2": 42.0,
    "so2": 25.0,
    "air_temp": 33.5,
    "forest_cover_pct": 6.8,
    "forest_area_sqkm": 1.2,
    "water_bodies": 3,
    "trees_m": 0.28,
    "gw_depth": 12.0,
    "stations": 2,
    "id": "SUR-SACH"
  },
  "SUR-ADAJ": {
    "name": "Adajan Tapi Riverfront",
    "tier": "area",
    "parent_id": "GJ-SUR",
    "type": "Riverine Eco Buffer",
    "lat": 21.2,
    "lng": 72.795,
    "zoom": 14.2,
    "pitch": 45,
    "bearing": 0,
    "neighbors": [
      "SUR-SACH"
    ],
    "bod": 6.2,
    "cod": 31.0,
    "do": 6.8,
    "ph": 7.4,
    "water_flow": 195.0,
    "water_temp": 27.5,
    "aqi": 115,
    "pm25": 48.0,
    "pm10": 96.0,
    "no2": 26.0,
    "so2": 14.0,
    "air_temp": 32.0,
    "forest_cover_pct": 21.0,
    "forest_area_sqkm": 3.5,
    "water_bodies": 5,
    "trees_m": 0.85,
    "gw_depth": 9.5,
    "stations": 2,
    "id": "SUR-ADAJ"
  },
  "BLR-WHT": {
    "name": "Whitefield (Tech Hub)",
    "tier": "area",
    "parent_id": "KA-BLR",
    "type": "High-Tech IT Corridor",
    "lat": 12.9698,
    "lng": 77.75,
    "zoom": 14.2,
    "pitch": 55,
    "bearing": 20,
    "neighbors": [
      "BLR-KORAM",
      "BLR-ECITY"
    ],
    "bod": 7.8,
    "cod": 38.0,
    "do": 6.2,
    "ph": 7.4,
    "water_flow": 95.0,
    "water_temp": 25.0,
    "aqi": 112,
    "pm25": 48.0,
    "pm10": 94.0,
    "no2": 31.0,
    "so2": 12.0,
    "air_temp": 27.2,
    "forest_cover_pct": 22.5,
    "forest_area_sqkm": 4.8,
    "water_bodies": 6,
    "trees_m": 0.82,
    "gw_depth": 14.5,
    "stations": 3,
    "id": "BLR-WHT"
  },
  "BLR-PEENYA": {
    "name": "Peenya (Industrial Estate)",
    "tier": "area",
    "parent_id": "KA-BLR",
    "type": "Major Manufacturing Cluster",
    "lat": 13.0285,
    "lng": 77.5197,
    "zoom": 14.4,
    "pitch": 60,
    "bearing": 35,
    "neighbors": [
      "BLR-WHT",
      "BLR-KORAM"
    ],
    "bod": 14.2,
    "cod": 76.0,
    "do": 3.6,
    "ph": 8.0,
    "water_flow": 135.0,
    "water_temp": 26.2,
    "aqi": 188,
    "pm25": 84.0,
    "pm10": 172.0,
    "no2": 46.0,
    "so2": 25.0,
    "air_temp": 28.5,
    "forest_cover_pct": 6.4,
    "forest_area_sqkm": 1.2,
    "water_bodies": 2,
    "trees_m": 0.22,
    "gw_depth": 11.2,
    "stations": 3,
    "id": "BLR-PEENYA"
  },
  "BLR-KORAM": {
    "name": "Koramangala (Urban Core)",
    "tier": "area",
    "parent_id": "KA-BLR",
    "type": "Commercial & Residential Core",
    "lat": 12.9352,
    "lng": 77.6245,
    "zoom": 14.2,
    "pitch": 50,
    "bearing": 0,
    "neighbors": [
      "BLR-WHT",
      "BLR-PEENYA",
      "BLR-ECITY"
    ],
    "bod": 6.5,
    "cod": 32.0,
    "do": 6.8,
    "ph": 7.3,
    "water_flow": 72.0,
    "water_temp": 24.5,
    "aqi": 92,
    "pm25": 36.0,
    "pm10": 74.0,
    "no2": 24.0,
    "so2": 9.5,
    "air_temp": 26.0,
    "forest_cover_pct": 28.4,
    "forest_area_sqkm": 3.6,
    "water_bodies": 5,
    "trees_m": 0.95,
    "gw_depth": 9.4,
    "stations": 2,
    "id": "BLR-KORAM"
  },
  "BLR-ECITY": {
    "name": "Electronic City Phase 1",
    "tier": "area",
    "parent_id": "KA-BLR",
    "type": "IT SEZ & Industrial Buffer",
    "lat": 12.845,
    "lng": 77.665,
    "zoom": 14.2,
    "pitch": 52,
    "bearing": 15,
    "neighbors": [
      "BLR-WHT",
      "BLR-KORAM"
    ],
    "bod": 7.2,
    "cod": 35.0,
    "do": 6.4,
    "ph": 7.4,
    "water_flow": 88.0,
    "water_temp": 24.8,
    "aqi": 104,
    "pm25": 42.0,
    "pm10": 85.0,
    "no2": 27.0,
    "so2": 11.0,
    "air_temp": 26.5,
    "forest_cover_pct": 19.5,
    "forest_area_sqkm": 3.2,
    "water_bodies": 4,
    "trees_m": 0.74,
    "gw_depth": 13.0,
    "stations": 2,
    "id": "BLR-ECITY"
  },
  "DEL-OKHLA": {
    "name": "Okhla Industrial Area",
    "tier": "area",
    "parent_id": "DL-SO",
    "type": "Manufacturing & CETP Zone",
    "lat": 28.53,
    "lng": 77.27,
    "zoom": 14.5,
    "pitch": 60,
    "bearing": 40,
    "neighbors": [
      "DEL-CP",
      "DEL-DWARKA"
    ],
    "bod": 17.5,
    "cod": 92.0,
    "do": 2.1,
    "ph": 8.2,
    "water_flow": 158.0,
    "water_temp": 27.2,
    "aqi": 295,
    "pm25": 152.0,
    "pm10": 285.0,
    "no2": 68.0,
    "so2": 34.0,
    "air_temp": 33.2,
    "forest_cover_pct": 5.2,
    "forest_area_sqkm": 0.9,
    "water_bodies": 2,
    "trees_m": 0.18,
    "gw_depth": 22.5,
    "stations": 3,
    "id": "DEL-OKHLA"
  },
  "DEL-CP": {
    "name": "Connaught Place (Central)",
    "tier": "area",
    "parent_id": "DL-ND",
    "type": "High-Density Commercial Nexus",
    "lat": 28.6315,
    "lng": 77.2167,
    "zoom": 14.3,
    "pitch": 55,
    "bearing": 10,
    "neighbors": [
      "DEL-OKHLA",
      "DEL-AV"
    ],
    "bod": 11.2,
    "cod": 58.0,
    "do": 4.4,
    "ph": 7.7,
    "water_flow": 98.0,
    "water_temp": 26.0,
    "aqi": 235,
    "pm25": 118.0,
    "pm10": 220.0,
    "no2": 52.0,
    "so2": 22.0,
    "air_temp": 31.5,
    "forest_cover_pct": 14.8,
    "forest_area_sqkm": 2.2,
    "water_bodies": 3,
    "trees_m": 0.45,
    "gw_depth": 15.8,
    "stations": 2,
    "id": "DEL-CP"
  },
  "DEL-DWARKA": {
    "name": "Dwarka Sub-City",
    "tier": "area",
    "parent_id": "DL-SO",
    "type": "Planned Residential Sub-City",
    "lat": 28.5921,
    "lng": 77.046,
    "zoom": 14.0,
    "pitch": 50,
    "bearing": 0,
    "neighbors": [
      "DEL-CP",
      "DEL-OKHLA"
    ],
    "bod": 9.4,
    "cod": 48.0,
    "do": 5.2,
    "ph": 7.5,
    "water_flow": 112.0,
    "water_temp": 25.8,
    "aqi": 210,
    "pm25": 104.0,
    "pm10": 195.0,
    "no2": 44.0,
    "so2": 19.0,
    "air_temp": 31.0,
    "forest_cover_pct": 21.0,
    "forest_area_sqkm": 5.1,
    "water_bodies": 6,
    "trees_m": 0.88,
    "gw_depth": 17.2,
    "stations": 2,
    "id": "DEL-DWARKA"
  },
  "DEL-AV": {
    "name": "Anand Vihar ISBT Basin",
    "tier": "area",
    "parent_id": "DL-NO",
    "type": "Transport & Industrial Air Basin",
    "lat": 28.647,
    "lng": 77.315,
    "zoom": 14.2,
    "pitch": 55,
    "bearing": 15,
    "neighbors": [
      "DEL-CP",
      "DEL-OKHLA"
    ],
    "bod": 18.0,
    "cod": 95.0,
    "do": 2.0,
    "ph": 8.3,
    "water_flow": 170.0,
    "water_temp": 27.5,
    "aqi": 320,
    "pm25": 168.0,
    "pm10": 310.0,
    "no2": 72.0,
    "so2": 38.0,
    "air_temp": 33.8,
    "forest_cover_pct": 4.1,
    "forest_area_sqkm": 0.6,
    "water_bodies": 1,
    "trees_m": 0.14,
    "gw_depth": 24.0,
    "stations": 3,
    "id": "DEL-AV"
  },
  "CHN-MANALI": {
    "name": "Manali Petrochem Zone",
    "tier": "area",
    "parent_id": "TN-CHN",
    "type": "Petrochemical & Fertilizer Hub",
    "lat": 13.165,
    "lng": 80.26,
    "zoom": 14.2,
    "pitch": 58,
    "bearing": 20,
    "neighbors": [
      "CHN-GUINDY",
      "CHN-OMR"
    ],
    "bod": 16.8,
    "cod": 88.0,
    "do": 2.8,
    "ph": 8.2,
    "water_flow": 165.0,
    "water_temp": 30.5,
    "aqi": 195,
    "pm25": 94.0,
    "pm10": 178.0,
    "no2": 48.0,
    "so2": 29.0,
    "air_temp": 34.0,
    "forest_cover_pct": 5.8,
    "forest_area_sqkm": 0.9,
    "water_bodies": 2,
    "trees_m": 0.18,
    "gw_depth": 6.8,
    "stations": 3,
    "id": "CHN-MANALI"
  },
  "CHN-GUINDY": {
    "name": "Guindy Industrial Estate",
    "tier": "area",
    "parent_id": "TN-CHN",
    "type": "Mixed Industrial & National Park Buffer",
    "lat": 13.01,
    "lng": 80.215,
    "zoom": 14.2,
    "pitch": 50,
    "bearing": 10,
    "neighbors": [
      "CHN-MANALI",
      "CHN-OMR"
    ],
    "bod": 9.8,
    "cod": 48.0,
    "do": 5.4,
    "ph": 7.6,
    "water_flow": 120.0,
    "water_temp": 29.0,
    "aqi": 132,
    "pm25": 58.0,
    "pm10": 112.0,
    "no2": 32.0,
    "so2": 18.0,
    "air_temp": 32.0,
    "forest_cover_pct": 26.5,
    "forest_area_sqkm": 4.2,
    "water_bodies": 4,
    "trees_m": 0.92,
    "gw_depth": 5.5,
    "stations": 2,
    "id": "CHN-GUINDY"
  },
  "CHN-OMR": {
    "name": "OMR IT Expressway",
    "tier": "area",
    "parent_id": "TN-CHN",
    "type": "High-Tech IT Corridor",
    "lat": 12.92,
    "lng": 80.23,
    "zoom": 14.2,
    "pitch": 52,
    "bearing": 15,
    "neighbors": [
      "CHN-GUINDY"
    ],
    "bod": 7.2,
    "cod": 36.0,
    "do": 6.2,
    "ph": 7.4,
    "water_flow": 95.0,
    "water_temp": 28.5,
    "aqi": 108,
    "pm25": 46.0,
    "pm10": 88.0,
    "no2": 26.0,
    "so2": 13.0,
    "air_temp": 31.5,
    "forest_cover_pct": 18.0,
    "forest_area_sqkm": 3.1,
    "water_bodies": 5,
    "trees_m": 0.68,
    "gw_depth": 6.2,
    "stations": 2,
    "id": "CHN-OMR"
  },
  "HYD-HITEC": {
    "name": "HITEC City Cyberabad",
    "tier": "area",
    "parent_id": "TG-HYD",
    "type": "Global Tech Hub",
    "lat": 17.4474,
    "lng": 78.3762,
    "zoom": 14.2,
    "pitch": 55,
    "bearing": 20,
    "neighbors": [
      "HYD-JEED",
      "HYD-SANATH"
    ],
    "bod": 7.4,
    "cod": 37.0,
    "do": 6.2,
    "ph": 7.4,
    "water_flow": 110.0,
    "water_temp": 27.5,
    "aqi": 118,
    "pm25": 52.0,
    "pm10": 102.0,
    "no2": 28.0,
    "so2": 13.5,
    "air_temp": 31.0,
    "forest_cover_pct": 18.5,
    "forest_area_sqkm": 3.6,
    "water_bodies": 5,
    "trees_m": 0.85,
    "gw_depth": 9.5,
    "stations": 3,
    "id": "HYD-HITEC"
  },
  "HYD-JEED": {
    "name": "Jeedimetla CETP Industrial",
    "tier": "area",
    "parent_id": "TG-HYD",
    "type": "Pharma & Chemical CETP Zone",
    "lat": 17.515,
    "lng": 78.448,
    "zoom": 14.4,
    "pitch": 60,
    "bearing": 30,
    "neighbors": [
      "HYD-HITEC",
      "HYD-SANATH"
    ],
    "bod": 17.2,
    "cod": 94.0,
    "do": 2.5,
    "ph": 8.3,
    "water_flow": 145.0,
    "water_temp": 29.5,
    "aqi": 242,
    "pm25": 118.0,
    "pm10": 230.0,
    "no2": 62.0,
    "so2": 35.0,
    "air_temp": 33.5,
    "forest_cover_pct": 4.8,
    "forest_area_sqkm": 0.8,
    "water_bodies": 2,
    "trees_m": 0.16,
    "gw_depth": 11.2,
    "stations": 3,
    "id": "HYD-JEED"
  },
  "HYD-SANATH": {
    "name": "Sanath Nagar Industrial",
    "tier": "area",
    "parent_id": "TG-HYD",
    "type": "Manufacturing Cluster",
    "lat": 17.458,
    "lng": 78.442,
    "zoom": 14.2,
    "pitch": 55,
    "bearing": 15,
    "neighbors": [
      "HYD-HITEC",
      "HYD-JEED"
    ],
    "bod": 12.8,
    "cod": 64.0,
    "do": 4.2,
    "ph": 7.7,
    "water_flow": 125.0,
    "water_temp": 28.5,
    "aqi": 178,
    "pm25": 82.0,
    "pm10": 158.0,
    "no2": 44.0,
    "so2": 22.0,
    "air_temp": 32.2,
    "forest_cover_pct": 8.2,
    "forest_area_sqkm": 1.4,
    "water_bodies": 3,
    "trees_m": 0.32,
    "gw_depth": 8.5,
    "stations": 2,
    "id": "HYD-SANATH"
  },
  "KOL-SL": {
    "name": "Salt Lake Sector V",
    "tier": "area",
    "parent_id": "WB-KOL",
    "type": "IT & Electronics Core",
    "lat": 22.578,
    "lng": 88.432,
    "zoom": 14.2,
    "pitch": 52,
    "bearing": 15,
    "neighbors": [
      "KOL-TARA",
      "KOL-VM"
    ],
    "bod": 8.5,
    "cod": 42.0,
    "do": 5.8,
    "ph": 7.5,
    "water_flow": 115.0,
    "water_temp": 27.2,
    "aqi": 165,
    "pm25": 78.0,
    "pm10": 145.0,
    "no2": 42.0,
    "so2": 21.0,
    "air_temp": 29.8,
    "forest_cover_pct": 16.5,
    "forest_area_sqkm": 2.8,
    "water_bodies": 8,
    "trees_m": 0.65,
    "gw_depth": 4.2,
    "stations": 2,
    "id": "KOL-SL"
  },
  "KOL-TARA": {
    "name": "Taratala Industrial Area",
    "tier": "area",
    "parent_id": "WB-KOL",
    "type": "Port Warehousing & Heavy Engineering",
    "lat": 22.512,
    "lng": 88.315,
    "zoom": 14.2,
    "pitch": 56,
    "bearing": 20,
    "neighbors": [
      "KOL-SL",
      "KOL-VM"
    ],
    "bod": 15.2,
    "cod": 79.0,
    "do": 3.2,
    "ph": 7.9,
    "water_flow": 150.0,
    "water_temp": 28.0,
    "aqi": 235,
    "pm25": 112.0,
    "pm10": 210.0,
    "no2": 58.0,
    "so2": 32.0,
    "air_temp": 31.0,
    "forest_cover_pct": 5.2,
    "forest_area_sqkm": 0.9,
    "water_bodies": 4,
    "trees_m": 0.22,
    "gw_depth": 3.9,
    "stations": 3,
    "id": "KOL-TARA"
  },
  "KOL-VM": {
    "name": "Victoria Memorial Green Buffer",
    "tier": "area",
    "parent_id": "WB-KOL",
    "type": "Protected Heritage Eco-Zone",
    "lat": 22.5448,
    "lng": 88.3426,
    "zoom": 14.2,
    "pitch": 45,
    "bearing": 0,
    "neighbors": [
      "KOL-SL",
      "KOL-TARA"
    ],
    "bod": 6.8,
    "cod": 32.0,
    "do": 6.5,
    "ph": 7.4,
    "water_flow": 80.0,
    "water_temp": 26.5,
    "aqi": 138,
    "pm25": 62.0,
    "pm10": 118.0,
    "no2": 34.0,
    "so2": 16.0,
    "air_temp": 29.0,
    "forest_cover_pct": 34.0,
    "forest_area_sqkm": 3.2,
    "water_bodies": 6,
    "trees_m": 0.92,
    "gw_depth": 4.8,
    "stations": 2,
    "id": "KOL-VM"
  },
  "NOI-SEC62": {
    "name": "Sector 62 Tech Core",
    "tier": "area",
    "parent_id": "UP-NOI",
    "type": "IT & Institutional Cluster",
    "lat": 28.625,
    "lng": 77.365,
    "zoom": 14.2,
    "pitch": 52,
    "bearing": 15,
    "neighbors": [
      "NOI-SEC11",
      "DEL-CP"
    ],
    "bod": 9.5,
    "cod": 49.0,
    "do": 5.1,
    "ph": 7.6,
    "water_flow": 92.0,
    "water_temp": 26.0,
    "aqi": 230,
    "pm25": 112.0,
    "pm10": 210.0,
    "no2": 51.0,
    "so2": 24.0,
    "air_temp": 32.0,
    "forest_cover_pct": 14.0,
    "forest_area_sqkm": 2.1,
    "water_bodies": 3,
    "trees_m": 0.48,
    "gw_depth": 14.2,
    "stations": 2,
    "id": "NOI-SEC62"
  },
  "NOI-SEC11": {
    "name": "Sector 11 Industrial Cluster",
    "tier": "area",
    "parent_id": "UP-NOI",
    "type": "Light Engineering & Electronics MIDC",
    "lat": 28.595,
    "lng": 77.33,
    "zoom": 14.2,
    "pitch": 56,
    "bearing": 20,
    "neighbors": [
      "NOI-SEC62",
      "DEL-OKHLA"
    ],
    "bod": 15.8,
    "cod": 82.0,
    "do": 3.0,
    "ph": 8.1,
    "water_flow": 140.0,
    "water_temp": 27.2,
    "aqi": 285,
    "pm25": 144.0,
    "pm10": 268.0,
    "no2": 64.0,
    "so2": 32.0,
    "air_temp": 33.2,
    "forest_cover_pct": 6.2,
    "forest_area_sqkm": 0.9,
    "water_bodies": 2,
    "trees_m": 0.2,
    "gw_depth": 15.5,
    "stations": 3,
    "id": "NOI-SEC11"
  },
  "KNP-JAJMAU": {
    "name": "Jajmau Tannery Ganga Basin",
    "tier": "area",
    "parent_id": "UP-KNP",
    "type": "Leather Processing & Heavy Chromium Outflow",
    "lat": 26.435,
    "lng": 80.405,
    "zoom": 14.4,
    "pitch": 62,
    "bearing": 35,
    "neighbors": [
      "KNP-PANKI"
    ],
    "bod": 22.5,
    "cod": 118.0,
    "do": 1.8,
    "ph": 8.6,
    "water_flow": 185.0,
    "water_temp": 28.5,
    "aqi": 310,
    "pm25": 162.0,
    "pm10": 305.0,
    "no2": 72.0,
    "so2": 42.0,
    "air_temp": 33.5,
    "forest_cover_pct": 3.2,
    "forest_area_sqkm": 0.6,
    "water_bodies": 2,
    "trees_m": 0.12,
    "gw_depth": 11.5,
    "stations": 3,
    "id": "KNP-JAJMAU"
  },
  "KNP-PANKI": {
    "name": "Panki Industrial Area",
    "tier": "area",
    "parent_id": "UP-KNP",
    "type": "Thermal & Heavy Machinery MIDC",
    "lat": 26.475,
    "lng": 80.245,
    "zoom": 14.2,
    "pitch": 55,
    "bearing": 20,
    "neighbors": [
      "KNP-JAJMAU"
    ],
    "bod": 14.8,
    "cod": 74.0,
    "do": 3.6,
    "ph": 7.9,
    "water_flow": 135.0,
    "water_temp": 27.0,
    "aqi": 265,
    "pm25": 132.0,
    "pm10": 248.0,
    "no2": 58.0,
    "so2": 29.0,
    "air_temp": 32.2,
    "forest_cover_pct": 7.4,
    "forest_area_sqkm": 1.4,
    "water_bodies": 3,
    "trees_m": 0.28,
    "gw_depth": 13.2,
    "stations": 2,
    "id": "KNP-PANKI"
  },
  "IND-PITH": {
    "name": "Pithampur Industrial Belt",
    "tier": "area",
    "parent_id": "MP-IND",
    "type": "Automotive & Heavy Eng Hub",
    "lat": 22.61,
    "lng": 75.68,
    "zoom": 14.2,
    "pitch": 55,
    "bearing": 20,
    "neighbors": [
      "IND-VIJAY"
    ],
    "bod": 12.5,
    "cod": 64.0,
    "do": 4.5,
    "ph": 7.7,
    "water_flow": 145.0,
    "water_temp": 27.0,
    "aqi": 145,
    "pm25": 66.0,
    "pm10": 132.0,
    "no2": 36.0,
    "so2": 18.0,
    "air_temp": 31.0,
    "forest_cover_pct": 11.2,
    "forest_area_sqkm": 2.2,
    "water_bodies": 3,
    "trees_m": 0.44,
    "gw_depth": 9.4,
    "stations": 3,
    "id": "IND-PITH"
  },
  "IND-VIJAY": {
    "name": "Vijay Nagar Tech Core",
    "tier": "area",
    "parent_id": "MP-IND",
    "type": "Commercial & Tech Buffer",
    "lat": 22.752,
    "lng": 75.894,
    "zoom": 14.2,
    "pitch": 48,
    "bearing": 10,
    "neighbors": [
      "IND-PITH"
    ],
    "bod": 5.2,
    "cod": 26.0,
    "do": 7.2,
    "ph": 7.3,
    "water_flow": 85.0,
    "water_temp": 25.5,
    "aqi": 88,
    "pm25": 36.0,
    "pm10": 72.0,
    "no2": 21.0,
    "so2": 9.0,
    "air_temp": 28.5,
    "forest_cover_pct": 24.5,
    "forest_area_sqkm": 4.5,
    "water_bodies": 6,
    "trees_m": 0.95,
    "gw_depth": 7.8,
    "stations": 2,
    "id": "IND-VIJAY"
  },
  "BHP-LAKE": {
    "name": "Upper Lake Wetland Buffer",
    "tier": "area",
    "parent_id": "MP-BHP",
    "type": "Ramsar Wetland Eco-Zone",
    "lat": 23.245,
    "lng": 77.345,
    "zoom": 14.0,
    "pitch": 45,
    "bearing": 0,
    "neighbors": [
      "IND-VIJAY"
    ],
    "bod": 4.2,
    "cod": 21.0,
    "do": 7.8,
    "ph": 7.2,
    "water_flow": 120.0,
    "water_temp": 24.5,
    "aqi": 74,
    "pm25": 30.0,
    "pm10": 62.0,
    "no2": 16.0,
    "so2": 7.5,
    "air_temp": 27.5,
    "forest_cover_pct": 46.0,
    "forest_area_sqkm": 18.0,
    "water_bodies": 12,
    "trees_m": 3.8,
    "gw_depth": 5.2,
    "stations": 3,
    "id": "BHP-LAKE"
  },
  "JPR-SITA": {
    "name": "Sitapura Industrial Area",
    "tier": "area",
    "parent_id": "RJ-JPR",
    "type": "Jewellery, Garment & IT SEZ",
    "lat": 26.78,
    "lng": 75.83,
    "zoom": 14.2,
    "pitch": 55,
    "bearing": 20,
    "neighbors": [
      "JPR-MANS"
    ],
    "bod": 11.8,
    "cod": 58.0,
    "do": 4.8,
    "ph": 7.8,
    "water_flow": 110.0,
    "water_temp": 28.5,
    "aqi": 185,
    "pm25": 84.0,
    "pm10": 185.0,
    "no2": 38.0,
    "so2": 22.0,
    "air_temp": 35.5,
    "forest_cover_pct": 6.8,
    "forest_area_sqkm": 1.2,
    "water_bodies": 2,
    "trees_m": 0.22,
    "gw_depth": 25.0,
    "stations": 2,
    "id": "JPR-SITA"
  },
  "JPR-MANS": {
    "name": "Mansarovar Basin",
    "tier": "area",
    "parent_id": "RJ-JPR",
    "type": "Residential Eco & Commercial Sector",
    "lat": 26.86,
    "lng": 75.76,
    "zoom": 14.2,
    "pitch": 48,
    "bearing": 10,
    "neighbors": [
      "JPR-SITA"
    ],
    "bod": 6.4,
    "cod": 32.0,
    "do": 6.5,
    "ph": 7.5,
    "water_flow": 85.0,
    "water_temp": 26.8,
    "aqi": 142,
    "pm25": 62.0,
    "pm10": 145.0,
    "no2": 28.0,
    "so2": 15.0,
    "air_temp": 33.5,
    "forest_cover_pct": 14.5,
    "forest_area_sqkm": 2.8,
    "water_bodies": 4,
    "trees_m": 0.58,
    "gw_depth": 21.0,
    "stations": 2,
    "id": "JPR-MANS"
  },
  "COK-ELOOR": {
    "name": "Eloor Chemical Belt (Periyar)",
    "tier": "area",
    "parent_id": "KL-COK",
    "type": "Riverine Chemical Industrial Island",
    "lat": 10.08,
    "lng": 76.295,
    "zoom": 14.4,
    "pitch": 60,
    "bearing": 30,
    "neighbors": [
      "COK-MD",
      "COK-INFO"
    ],
    "bod": 14.2,
    "cod": 72.0,
    "do": 3.8,
    "ph": 7.9,
    "water_flow": 160.0,
    "water_temp": 28.2,
    "aqi": 115,
    "pm25": 48.0,
    "pm10": 92.0,
    "no2": 28.0,
    "so2": 16.0,
    "air_temp": 29.5,
    "forest_cover_pct": 24.0,
    "forest_area_sqkm": 2.5,
    "water_bodies": 6,
    "trees_m": 0.82,
    "gw_depth": 2.8,
    "stations": 3,
    "id": "COK-ELOOR"
  },
  "COK-MD": {
    "name": "Marine Drive Coastal Bay",
    "tier": "area",
    "parent_id": "KL-COK",
    "type": "Backwater Coastal Promenade",
    "lat": 9.98,
    "lng": 76.275,
    "zoom": 14.2,
    "pitch": 45,
    "bearing": 0,
    "neighbors": [
      "COK-ELOOR",
      "COK-INFO"
    ],
    "bod": 4.5,
    "cod": 22.0,
    "do": 7.4,
    "ph": 7.2,
    "water_flow": 140.0,
    "water_temp": 26.8,
    "aqi": 62,
    "pm25": 22.0,
    "pm10": 46.0,
    "no2": 14.0,
    "so2": 8.0,
    "air_temp": 28.0,
    "forest_cover_pct": 38.0,
    "forest_area_sqkm": 4.1,
    "water_bodies": 12,
    "trees_m": 1.45,
    "gw_depth": 3.2,
    "stations": 2,
    "id": "COK-MD"
  },
  "COK-INFO": {
    "name": "Infopark Kakkanad",
    "tier": "area",
    "parent_id": "KL-COK",
    "type": "High-Tech IT SEZ Corridor",
    "lat": 10.01,
    "lng": 76.365,
    "zoom": 14.2,
    "pitch": 50,
    "bearing": 15,
    "neighbors": [
      "COK-ELOOR",
      "COK-MD"
    ],
    "bod": 3.8,
    "cod": 19.0,
    "do": 7.8,
    "ph": 7.1,
    "water_flow": 88.0,
    "water_temp": 26.2,
    "aqi": 55,
    "pm25": 18.0,
    "pm10": 40.0,
    "no2": 12.0,
    "so2": 6.5,
    "air_temp": 27.5,
    "forest_cover_pct": 44.0,
    "forest_area_sqkm": 5.2,
    "water_bodies": 9,
    "trees_m": 1.8,
    "gw_depth": 4.5,
    "stations": 2,
    "id": "COK-INFO"
  }
};

    // GeoJSON Feature Collections
    const ALL_STATES_GEOJSON = {
      type: "FeatureCollection",
      features: Object.values(ENTITY_CATALOGUE).filter(e => e.tier === 'state').map(e => ({
        id: e.id,
        properties: { id: e.id, name: e.name, tier: "state", type: e.type, center: [e.lng, e.lat] },
        geometry: {
          type: "Polygon",
          coordinates: [
            [[e.lng - 1.6, e.lat - 1.2], [e.lng + 1.6, e.lat - 1.2], [e.lng + 1.8, e.lat + 1.2], [e.lng - 1.4, e.lat + 1.4], [e.lng - 1.6, e.lat - 1.2]]
          ]
        }
      }))
    };

    const ALL_CITIES_GEOJSON = {
      type: "FeatureCollection",
      features: Object.values(ENTITY_CATALOGUE).filter(e => e.tier === 'city').map(e => ({
        id: e.id,
        properties: { id: e.id, name: e.name, tier: "city", parent_id: e.parent_id, type: e.type, center: [e.lng, e.lat] },
        geometry: {
          type: "Polygon",
          coordinates: [
            [[e.lng - 0.22, e.lat - 0.16], [e.lng + 0.22, e.lat - 0.16], [e.lng + 0.24, e.lat + 0.16], [e.lng - 0.18, e.lat + 0.18], [e.lng - 0.22, e.lat - 0.16]]
          ]
        }
      }))
    };

    const ALL_AREAS_GEOJSON = {
      type: "FeatureCollection",
      features: Object.values(ENTITY_CATALOGUE).filter(e => e.tier === 'area').map(e => ({
        id: e.id,
        properties: { id: e.id, name: e.name, tier: "area", parent_id: e.parent_id, type: e.type, center: [e.lng, e.lat] },
        geometry: {
          type: "Polygon",
          coordinates: [
            [[e.lng - 0.024, e.lat - 0.018], [e.lng + 0.024, e.lat - 0.018], [e.lng + 0.028, e.lat + 0.018], [e.lng - 0.020, e.lat + 0.022], [e.lng - 0.024, e.lat - 0.018]]
          ]
        }
      }))
    };

    // State Variables
    let telemetryState = null;
    let selectedTier = "area";
    let selectedEntityId = "NM-MAHAPE";
    let metricMode = "water";
    let show3D = true;

    // View State
    let viewState = {
      longitude: 73.0230,
      latitude: 19.1120,
      zoom: 14.2,
      pitch: 55,
      bearing: 30,
      maxPitch: 85
    };

    // Set MapboxGL alias to MapLibre for standalone Deck.gl compatibility
    if (typeof window.maplibregl !== 'undefined') {
      window.mapboxgl = window.maplibregl;
    }

    // 100% Free OpenStreetMap Humanitarian basemap (ZERO API KEY REQUIRED, NO WATERMARKS)
    const BASEMAP_STYLE = {
      version: 8,
      sources: {
        'osm-hot': {
          type: 'raster',
          tiles: [
            'https://a.tile.openstreetmap.fr/hot/{z}/{x}/{y}.png',
            'https://b.tile.openstreetmap.fr/hot/{z}/{x}/{y}.png',
            'https://c.tile.openstreetmap.fr/hot/{z}/{x}/{y}.png'
          ],
          tileSize: 256,
          attribution: '&copy; OpenStreetMap contributors, Humanitarian OpenStreetMap Team'
        }
      },
      layers: [
        {
          id: 'background',
          type: 'background',
          paint: {
            'background-color': '#070b13'
          }
        },
        {
          id: 'osm-hot-tiles',
          type: 'raster',
          source: 'osm-hot',
          minzoom: 0,
          maxzoom: 20
        }
      ]
    };

    // Initialize MapLibre & Controlled DeckGL
    const deckgl = new deck.DeckGL({
      container: 'deck-canvas-container',
      mapLib: window.maplibregl || window.mapboxgl,
      mapStyle: BASEMAP_STYLE,
      initialViewState: viewState,
      viewState: viewState,
      controller: true,
      onViewStateChange: ({viewState: vs}) => {
        viewState = vs;
        deckgl.setProps({ viewState: vs });
      },
      getCursor: ({isHovering}) => isHovering ? 'pointer' : 'default',
      onError: (err) => console.warn('DeckGL note:', err)
    });

    function getColor(bod, cod, aqi, resources) {
      if (metricMode === 'water') {
        if (bod > 14 || cod > 75) return [244, 63, 94, 210];
        if (bod > 8 || cod > 45) return [245, 158, 11, 210];
        return [16, 185, 129, 210];
      } else if (metricMode === 'air') {
        if (aqi > 200) return [244, 63, 94, 210];
        if (aqi > 140) return [245, 158, 11, 210];
        return [16, 185, 129, 210];
      } else {
        const forest = resources ? (resources.forest_cover_pct || 20) : 20;
        if (forest > 30) return [16, 185, 129, 220];
        if (forest > 15) return [20, 184, 166, 190];
        return [245, 158, 11, 190];
      }
    }

    // 100% Reliable Entity Data Lookup
    function getEntityData(id) {
      if (!id) return null;
      if (telemetryState) {
        if (telemetryState.areas && telemetryState.areas[id]) return telemetryState.areas[id];
        if (telemetryState.cities && telemetryState.cities[id]) return telemetryState.cities[id];
        if (telemetryState.states && telemetryState.states[id]) return telemetryState.states[id];
      }
      return ENTITY_CATALOGUE[id] || null;
    }

    function getActiveDataset() {
      if (selectedTier === 'state') return ALL_STATES_GEOJSON;
      if (selectedTier === 'city') return ALL_CITIES_GEOJSON;
      return ALL_AREAS_GEOJSON;
    }

    function updateLayers() {
      const dataset = getActiveDataset();
      const layerList = [];

      // 1. Interactive Polygons Layer with optional 3D Polygon extrusion
      layerList.push(
        new deck.GeoJsonLayer({
          id: `geojson-layer-${selectedTier}`,
          data: dataset,
          pickable: true,
          stroked: true,
          filled: true,
          extruded: show3D,
          wireframe: show3D,
          lineWidthMinPixels: 2,
          getElevation: (f) => {
            if (!show3D) return 0;
            const fid = f.id || (f.properties && f.properties.id);
            const data = getEntityData(fid);
            const cod = data ? data.cod : 50;
            if (selectedTier === 'state') return cod * 1200;
            if (selectedTier === 'city') return cod * 250;
            return cod * 40;
          },
          getLineColor: (f) => {
            const fid = f.id || (f.properties && f.properties.id);
            return fid === selectedEntityId ? [0, 240, 255, 255] : [56, 189, 248, 130];
          },
          getFillColor: (f) => {
            const fid = f.id || (f.properties && f.properties.id);
            const data = getEntityData(fid);
            if (!data) return [30, 41, 59, 140];
            return getColor(data.bod, data.cod, data.aqi, data.resources);
          },
          transitions: {
            getElevation: 600,
            getFillColor: 400
          },
          updateTriggers: {
            getElevation: [show3D, telemetryState ? telemetryState.sequence : 0, selectedTier],
            getLineColor: [selectedEntityId],
            getFillColor: [telemetryState ? telemetryState.sequence : 0, metricMode, selectedEntityId]
          },
          onClick: (info) => {
            if (info && info.object) {
              const obj = info.object;
              const targetId = obj.id || (obj.properties && obj.properties.id);
              const targetTier = (obj.properties && obj.properties.tier) || obj.tier || selectedTier;
              if (targetId) {
                selectEntity(targetTier, targetId);
              }
            }
          }
        })
      );

      // 2. 3D Volumetric Extruded Columns (Available across ALL TIERS with resilient min-pixel scaling)
      if (show3D) {
        const isState = selectedTier === 'state';
        const isCity = selectedTier === 'city';
        const rad = isState ? 35000 : (isCity ? 5000 : 380);
        const radMin = isState ? 10 : (isCity ? 7 : 5);
        const radMax = isState ? 35 : (isCity ? 24 : 18);
        const elevMult = isState ? 3200 : (isCity ? 450 : 60);

        const columnData = dataset.features.map(f => {
          const fid = f.id || (f.properties && f.properties.id);
          const d = getEntityData(fid);
          const elev = d ? (d.cod * elevMult) : (50 * elevMult);
          return { id: fid, coordinates: f.properties.center, elevation: elev, data: d, properties: f.properties };
        });

        layerList.push(
          new deck.ColumnLayer({
            id: `3d-columns-${selectedTier}`,
            data: columnData,
            diskResolution: 24,
            radius: rad,
            radiusMinPixels: radMin,
            radiusMaxPixels: radMax,
            elevationScale: 1,
            extruded: true,
            pickable: true,
            getPosition: d => d.coordinates,
            getElevation: d => d.elevation,
            getFillColor: d => d.data ? getColor(d.data.bod, d.data.cod, d.data.aqi, d.data.resources) : [0, 240, 255, 200],
            getLineColor: [0, 240, 255, 255],
            lineWidthMinPixels: 1.5,
            transitions: {
              getElevation: 600,
              getFillColor: 400
            },
            updateTriggers: {
              getElevation: [telemetryState ? telemetryState.sequence : 0, selectedTier],
              getFillColor: [telemetryState ? telemetryState.sequence : 0, metricMode, selectedTier]
            },
            onClick: (info) => {
              if (info && info.object) {
                const targetId = info.object.id || (info.object.properties && info.object.properties.id);
                if (targetId) selectEntity(selectedTier, targetId);
              }
            }
          })
        );
      }

      // 3. Crisp GPU Location Labels Layer (Always 100% visible, zero watermark)
      const labelData = dataset.features.map(f => {
        const fid = f.id || (f.properties && f.properties.id);
        const name = (f.properties && f.properties.name) || fid;
        return {
          id: fid,
          name: name,
          coordinates: f.properties.center,
          isSelected: fid === selectedEntityId
        };
      });

      layerList.push(
        new deck.TextLayer({
          id: `location-labels-${selectedTier}`,
          data: labelData,
          pickable: true,
          getPosition: d => [d.coordinates[0], d.coordinates[1], show3D ? 120 : 10],
          getText: d => d.name,
          getSize: d => d.isSelected ? 13 : 11,
          sizeMinPixels: 10,
          sizeMaxPixels: 17,
          getColor: d => d.isSelected ? [0, 240, 255, 255] : [241, 245, 249, 230],
          getTextAnchor: 'middle',
          getAlignmentBaseline: 'center',
          backgroundColor: [11, 17, 30, 210],
          backgroundPadding: [6, 3],
          fontFamily: '"JetBrains Mono", monospace',
          fontWeight: 700,
          billboard: true,
          onClick: (info) => {
            if (info && info.object) {
              selectEntity(selectedTier, info.object.id);
            }
          }
        })
      );

      deckgl.setProps({ layers: layerList });
    }

    // Chart.js Instances
    let radarChartInstance = null;
    let barChartInstance = null;

    function initCharts() {
      const radarCtx = document.getElementById('radarChart').getContext('2d');
      radarChartInstance = new Chart(radarCtx, {
        type: 'radar',
        data: {
          labels: ['BOD', 'COD', 'AQI', 'PM2.5', 'Forest %', 'Water Bodies'],
          datasets: []
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          scales: { r: { grid: { color: '#334155' }, ticks: { display: false }, angleLines: { color: '#475569' } } },
          plugins: { legend: { labels: { color: '#94a3b8', font: { size: 10 } } } }
        }
      });

      const barCtx = document.getElementById('barChart').getContext('2d');
      barChartInstance = new Chart(barCtx, {
        type: 'bar',
        data: {
          labels: [],
          datasets: [
            { label: 'BOD (mg/L)', data: [], backgroundColor: '#00f0ff' },
            { label: 'COD (mg/L)', data: [], backgroundColor: '#818cf8' }
          ]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          scales: {
            x: { ticks: { color: '#94a3b8' }, grid: { color: '#1e293b' } },
            y: { ticks: { color: '#94a3b8' }, grid: { color: '#1e293b' } }
          },
          plugins: { legend: { labels: { color: '#94a3b8', font: { size: 10 } } } }
        }
      });
    }

    // Populate Tier Selector Dropdown
    function populateDropdown() {
      const selectElem = document.getElementById('tier-selector');
      if (!selectElem) return;
      selectElem.innerHTML = '';

      const grpStates = document.createElement('optgroup');
      grpStates.label = "STATES (Tier 1)";
      Object.values(ENTITY_CATALOGUE).filter(e => e.tier === 'state').forEach(e => {
        const opt = document.createElement('option');
        opt.value = `state:${e.id}`;
        opt.innerText = `State: ${e.name}`;
        grpStates.appendChild(opt);
      });
      selectElem.appendChild(grpStates);

      const grpCities = document.createElement('optgroup');
      grpCities.label = "CITIES (Tier 2)";
      Object.values(ENTITY_CATALOGUE).filter(e => e.tier === 'city').forEach(e => {
        const opt = document.createElement('option');
        opt.value = `city:${e.id}`;
        opt.innerText = `${e.name} (${e.parent_id.replace('IN-', '')})`;
        grpCities.appendChild(opt);
      });
      selectElem.appendChild(grpCities);

      const grpAreas = document.createElement('optgroup');
      grpAreas.label = "MICRO-AREAS (Tier 3)";
      Object.values(ENTITY_CATALOGUE).filter(e => e.tier === 'area').forEach(e => {
        const opt = document.createElement('option');
        opt.value = `area:${e.id}`;
        opt.innerText = `${e.name}`;
        grpAreas.appendChild(opt);
      });
      selectElem.appendChild(grpAreas);
    }

    // Master Entity Selector Function
    function selectEntity(tier, id) {
      if (!id) return;
      const entity = getEntityData(id);
      if (!entity) return;

      selectedTier = entity.tier || tier;
      selectedEntityId = id;

      // Update button styles on HUD
      ['state', 'city', 'area'].forEach(t => {
        const btn = document.getElementById(`tier-btn-${t}`);
        if (btn) {
          if (t === selectedTier) {
            btn.className = 'px-2.5 py-1.5 rounded-lg text-left bg-cyan-950/80 border border-cyan-400 text-cyan-300 font-bold flex justify-between items-center';
          } else {
            btn.className = 'px-2.5 py-1.5 rounded-lg text-left text-slate-300 hover:bg-slate-800 flex justify-between items-center';
          }
        }
      });

      // Update Camera with 60 FPS interpolation and persistent 3D perspective
      const targetZoom = entity.camera_zoom || (selectedTier === 'state' ? 6.8 : (selectedTier === 'city' ? 11.5 : 14.2));
      const targetPitch = show3D ? Math.max(entity.pitch || 50, 45) : (entity.pitch || 30);
      const targetBearing = show3D ? (entity.bearing || 25) : (entity.bearing || 0);

      viewState = {
        ...viewState,
        longitude: entity.lng,
        latitude: entity.lat,
        zoom: targetZoom,
        pitch: targetPitch,
        bearing: targetBearing,
        maxPitch: 85,
        transitionDuration: 1800,
        transitionInterpolator: new deck.FlyToInterpolator({ speed: 1.2, curve: 1.4 })
      };
      deckgl.setProps({ viewState: viewState });

      // Synchronize dropdown
      const selectElem = document.getElementById('tier-selector');
      if (selectElem) {
        const matchVal = `${selectedTier}:${id}`;
        for (let i = 0; i < selectElem.options.length; i++) {
          if (selectElem.options[i].value === matchVal) {
            selectElem.selectedIndex = i;
            break;
          }
        }
      }

      // Update Breadcrumbs
      updateBreadcrumbs(entity);

      // Update UI panels & charts
      updateLayers();
      updateSidebar();
      openPanel();
    }

    function updateBreadcrumbs(entity) {
      const bBar = document.getElementById('breadcrumb-bar');
      if (!bBar) return;
      
      let html = `<button onclick="switchTier('state')" class="hover:text-cyan-300 transition-colors">All India</button>`;
      
      if (entity.tier === 'state') {
        html += ` <span class="text-slate-600">/</span> <span class="text-cyan-400 font-bold">${entity.name}</span>`;
      } else if (entity.tier === 'city') {
        const stateObj = getEntityData(entity.parent_id);
        if (stateObj) {
          html += ` <span class="text-slate-600">/</span> <button onclick="selectEntity('state', '${stateObj.id}')" class="hover:text-cyan-300 transition-colors">${stateObj.name}</button>`;
        }
        html += ` <span class="text-slate-600">/</span> <span class="text-cyan-400 font-bold">${entity.name}</span>`;
      } else {
        const cityObj = getEntityData(entity.parent_id);
        if (cityObj) {
          const stateObj = getEntityData(cityObj.parent_id);
          if (stateObj) {
            html += ` <span class="text-slate-600">/</span> <button onclick="selectEntity('state', '${stateObj.id}')" class="hover:text-cyan-300 transition-colors">${stateObj.name}</button>`;
          }
          html += ` <span class="text-slate-600">/</span> <button onclick="selectEntity('city', '${cityObj.id}')" class="hover:text-cyan-300 transition-colors">${cityObj.name}</button>`;
        }
        html += ` <span class="text-slate-600">/</span> <span class="text-cyan-400 font-bold">${entity.name.split(' ')[0]}</span>`;
      }
      
      bBar.innerHTML = html;
    }

    function switchTier(tier) {
      selectedTier = tier;
      const active = getEntityData(selectedEntityId);

      // Smart tier switching preserving local context
      let targetId = "IN-MH";
      if (tier === 'state') {
        if (active && active.tier === 'city') targetId = active.parent_id;
        else if (active && active.tier === 'area') {
          const c = getEntityData(active.parent_id);
          targetId = c ? c.parent_id : "IN-MH";
        } else targetId = active ? active.id : "IN-MH";
      } else if (tier === 'city') {
        if (active && active.tier === 'state') {
          const firstCity = Object.values(ENTITY_CATALOGUE).find(e => e.tier === 'city' && e.parent_id === active.id);
          targetId = firstCity ? firstCity.id : "MH-NM";
        } else if (active && active.tier === 'area') {
          targetId = active.parent_id || "MH-NM";
        } else targetId = active ? active.id : "MH-NM";
      } else {
        if (active && active.tier === 'city') {
          const firstArea = Object.values(ENTITY_CATALOGUE).find(e => e.tier === 'area' && e.parent_id === active.id);
          targetId = firstArea ? firstArea.id : "NM-MAHAPE";
        } else if (active && active.tier === 'state') {
          const firstCity = Object.values(ENTITY_CATALOGUE).find(e => e.tier === 'city' && e.parent_id === active.id);
          const firstArea = firstCity ? Object.values(ENTITY_CATALOGUE).find(e => e.tier === 'area' && e.parent_id === firstCity.id) : null;
          targetId = firstArea ? firstArea.id : "NM-MAHAPE";
        } else targetId = active ? active.id : "NM-MAHAPE";
      }

      selectEntity(tier, targetId);
    }

    function handleDropdownSelection(val) {
      const parts = val.split(':');
      if (parts.length === 2) {
        selectEntity(parts[0], parts[1]);
      }
    }

    function updateSidebar() {
      const active = getEntityData(selectedEntityId);
      if (!active) return;

      document.getElementById('panel-tier-badge').innerText = `${active.tier.toUpperCase()} LEVEL: ${active.id}`;
      document.getElementById('panel-entity-name').innerText = active.name;
      document.getElementById('panel-entity-type').innerText = active.type;

      // Status badge
      const statusBadge = document.getElementById('panel-status-badge');
      statusBadge.innerText = `${active.status} LOAD`;
      statusBadge.className = active.status === 'CRITICAL' 
        ? 'hud-badge bg-rose-500/20 text-rose-400 border border-rose-500/40' 
        : (active.status === 'ELEVATED' 
          ? 'hud-badge bg-amber-500/20 text-amber-400 border border-amber-500/40' 
          : 'hud-badge bg-emerald-500/20 text-emerald-400 border border-emerald-500/40');

      // Update Sub-Hierarchy Navigation (Explore child cities or child areas)
      const subNav = document.getElementById('drill-down-subpanel');
      if (active.tier === 'state') {
        const childCities = Object.values(ENTITY_CATALOGUE).filter(e => e.tier === 'city' && e.parent_id === active.id);
        let subHtml = `<div class="text-[10px] text-cyan-300 font-bold uppercase tracking-wider">Explore Cities in ${active.name} (${childCities.length}):</div>`;
        subHtml += `<div class="flex flex-wrap gap-1.5 mt-1">`;
        childCities.forEach(c => {
          subHtml += `<button onclick="selectEntity('city', '${c.id}')" class="px-2 py-1 rounded bg-slate-900/80 border border-slate-700 hover:border-cyan-400 text-[11px] font-mono text-slate-200 hover:text-cyan-300 transition-colors">${c.name}</button>`;
        });
        subHtml += `</div>`;
        subNav.innerHTML = subHtml;
        subNav.classList.remove('hidden');
      } else if (active.tier === 'city') {
        const childAreas = Object.values(ENTITY_CATALOGUE).filter(e => e.tier === 'area' && e.parent_id === active.id);
        let subHtml = `<div class="text-[10px] text-cyan-300 font-bold uppercase tracking-wider">Explore Micro-Areas in ${active.name} (${childAreas.length}):</div>`;
        subHtml += `<div class="flex flex-wrap gap-1.5 mt-1">`;
        childAreas.forEach(a => {
          subHtml += `<button onclick="selectEntity('area', '${a.id}')" class="px-2 py-1 rounded bg-slate-900/80 border border-slate-700 hover:border-cyan-400 text-[11px] font-mono text-slate-200 hover:text-cyan-300 transition-colors">${a.name.split(' ')[0]}</button>`;
        });
        subHtml += `</div>`;
        subNav.innerHTML = subHtml;
        subNav.classList.remove('hidden');
      } else {
        const cityObj = getEntityData(active.parent_id);
        if (cityObj) {
          subNav.innerHTML = `<div class="flex items-center justify-between"><span class="text-[10px] text-slate-400">Belongs to ${cityObj.name}</span><button onclick="selectEntity('city', '${cityObj.id}')" class="px-2 py-1 bg-cyan-950/80 border border-cyan-400 text-cyan-300 rounded text-[10px] font-mono font-bold hover:bg-cyan-900">⬆ View City Overview</button></div>`;
          subNav.classList.remove('hidden');
        } else {
          subNav.classList.add('hidden');
        }
      }

      // Primary stats
      document.getElementById('stat-bod').innerText = active.bod.toFixed(1);
      document.getElementById('stat-cod').innerText = active.cod.toFixed(1);
      document.getElementById('stat-aqi').innerText = active.aqi;
      document.getElementById('stat-pm25').innerText = active.pm25.toFixed(1);
      document.getElementById('stat-pm10').innerText = active.pm10.toFixed(1);
      document.getElementById('stat-do').innerText = active.do.toFixed(1);
      document.getElementById('stat-flow').innerText = active.water_flow_mld ? active.water_flow_mld.toFixed(0) : (active.water_flow || 100);

      // Natural Resources
      const res = active.resources || {
        forest_cover_pct: active.forest_cover_pct || 20.0,
        forest_area_sqkm: active.forest_area_sqkm || 100.0,
        water_bodies_count: active.water_bodies || 10,
        tree_count_millions: active.trees_m || 1.0,
        groundwater_depth_m: active.gw_depth || 6.0,
        monitoring_stations_count: active.stations || 2
      };

      document.getElementById('stat-forest').innerText = `${res.forest_cover_pct.toFixed(1)}%`;
      document.getElementById('stat-forest-area').innerText = `${res.forest_area_sqkm.toFixed(0)} km²`;
      document.getElementById('stat-lakes').innerText = res.water_bodies_count;
      document.getElementById('stat-trees').innerText = `${res.tree_count_millions.toFixed(2)} M`;
      document.getElementById('stat-gw').innerText = `${res.groundwater_depth_m.toFixed(1)} m bgl`;
      document.getElementById('stat-stations').innerText = `${res.monitoring_stations_count} Stations`;

      // Bottom HUD
      document.getElementById('hud-active-name').innerText = active.name;
      document.getElementById('hud-bod').innerText = active.bod.toFixed(1);
      document.getElementById('hud-cod').innerText = active.cod.toFixed(1);
      document.getElementById('hud-aqi').innerText = active.aqi;
      document.getElementById('hud-forest').innerText = `${res.forest_cover_pct.toFixed(1)}%`;
      document.getElementById('hud-waterbodies').innerText = res.water_bodies_count;

      // Dynamic Neighbor Comparison Graph
      const neighbors = (active.neighbors || []).map(nid => getEntityData(nid)).filter(Boolean);
      
      const palette = ['#00f0ff', '#f59e0b', '#f43f5e', '#a855f7', '#10b981'];
      const bgPalette = ['rgba(0, 240, 255, 0.25)', 'rgba(245, 158, 11, 0.15)', 'rgba(244, 63, 94, 0.15)', 'rgba(168, 85, 247, 0.15)', 'rgba(16, 185, 129, 0.15)'];

      // Update Radar
      if (radarChartInstance) {
        const radarDatasets = [];
        
        radarDatasets.push({
          label: active.name.split(' ')[0],
          data: [
            Math.min((active.bod / 20) * 100, 100),
            Math.min((active.cod / 100) * 100, 100),
            Math.min((active.aqi / 300) * 100, 100),
            Math.min((active.pm25 / 150) * 100, 100),
            Math.min(res.forest_cover_pct * 2, 100),
            Math.min((res.water_bodies_count / 50) * 100, 100)
          ],
          borderColor: palette[0],
          backgroundColor: bgPalette[0]
        });

        neighbors.slice(0, 3).forEach((n, idx) => {
          const nRes = n.resources || { forest_cover_pct: n.forest_cover_pct || 20, water_bodies_count: n.water_bodies || 10 };
          radarDatasets.push({
            label: n.name.split(' ')[0],
            data: [
              Math.min((n.bod / 20) * 100, 100),
              Math.min((n.cod / 100) * 100, 100),
              Math.min((n.aqi / 300) * 100, 100),
              Math.min((n.pm25 / 150) * 100, 100),
              Math.min(nRes.forest_cover_pct * 2, 100),
              Math.min((nRes.water_bodies_count / 50) * 100, 100)
            ],
            borderColor: palette[idx + 1],
            backgroundColor: bgPalette[idx + 1]
          });
        });

        radarChartInstance.data.datasets = radarDatasets;
        radarChartInstance.update();
      }

      // Update Bar Chart
      if (barChartInstance) {
        const barLabels = [active.name.split(' ')[0], ...neighbors.slice(0, 3).map(n => n.name.split(' ')[0])];
        const bodValues = [active.bod, ...neighbors.slice(0, 3).map(n => n.bod)];
        const codValues = [active.cod, ...neighbors.slice(0, 3).map(n => n.cod)];

        barChartInstance.data.labels = barLabels;
        barChartInstance.data.datasets[0].data = bodValues;
        barChartInstance.data.datasets[1].data = codValues;
        barChartInstance.update();
      }
    }

    // WebSocket Pipeline (Resilient to dev proxies on port 5173 or direct port 8000)
    function connectWS() {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const wsPort = window.location.port === '5173' ? '8000' : (window.location.port || '8000');
      const wsUrl = `${protocol}//${window.location.hostname}:${wsPort}/ws/environmental-data`;

      console.log(`[WebSocket] Connecting to ${wsUrl}...`);
      const socket = new WebSocket(wsUrl);

      socket.onopen = () => {
        document.getElementById('ws-status').innerHTML = `
          <span class="relative flex h-2 w-2">
            <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
            <span class="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
          </span>
          <span>LIVE 2s</span>
        `;
      };

      socket.onmessage = (event) => {
        try {
          telemetryState = JSON.parse(event.data);
          document.getElementById('seq-counter').innerText = `SEQ #${telemetryState.sequence}`;
          updateLayers();
          updateSidebar();
        } catch(e) { console.error(e); }
      };

      socket.onclose = () => {
        document.getElementById('ws-status').innerHTML = `<span class="w-2 h-2 rounded-full bg-amber-400"></span><span>SYNC</span>`;
        setTimeout(connectWS, 3000);
      };

      socket.onerror = (e) => {
        console.warn("[WebSocket] Error, fallback to synchronous in-memory telemetry.", e);
      };
    }

    function toggle3DColumns() {
      show3D = !show3D;
      const btn = document.getElementById('btn-3d');
      if (show3D) {
        btn.className = 'px-2.5 py-1.5 rounded-lg text-left bg-cyan-950/80 border border-cyan-400 text-cyan-300 flex justify-between items-center transition-all';
        btn.querySelector('span:last-child').innerText = 'ON';
        btn.querySelector('span:last-child').className = 'text-cyan-400 text-xs font-bold';
        if (viewState.pitch < 30) {
          viewState = { ...viewState, pitch: 52, bearing: 20, transitionDuration: 1200, transitionInterpolator: new deck.FlyToInterpolator() };
          deckgl.setProps({ viewState: viewState });
        }
      } else {
        btn.className = 'px-2.5 py-1.5 rounded-lg text-left bg-slate-800/60 border border-transparent text-slate-400 flex justify-between items-center transition-all';
        btn.querySelector('span:last-child').innerText = 'OFF';
        btn.querySelector('span:last-child').className = 'text-slate-500 text-xs';
      }
      updateLayers();
    }

    function togglePitch() {
      const newPitch = viewState.pitch > 20 ? 0 : 55;
      const newBearing = newPitch > 20 ? 25 : 0;
      viewState = {
        ...viewState,
        pitch: newPitch,
        bearing: newBearing,
        transitionDuration: 1000,
        transitionInterpolator: new deck.FlyToInterpolator()
      };
      deckgl.setProps({ viewState: viewState });
    }

    function setMetricMode(mode) {
      metricMode = mode;
      document.getElementById('mode-water').className = mode === 'water' ? 'px-3 py-1.5 rounded-lg bg-cyan-950/80 border border-cyan-400 text-cyan-300 font-bold' : 'px-3 py-1.5 rounded-lg text-slate-400 hover:text-white';
      document.getElementById('mode-air').className = mode === 'air' ? 'px-3 py-1.5 rounded-lg bg-purple-950/80 border border-purple-400 text-purple-300 font-bold' : 'px-3 py-1.5 rounded-lg text-slate-400 hover:text-white';
      document.getElementById('mode-resources').className = mode === 'resources' ? 'px-3 py-1.5 rounded-lg bg-emerald-950/80 border border-emerald-400 text-emerald-300 font-bold' : 'px-3 py-1.5 rounded-lg text-slate-400 hover:text-white';
      updateLayers();
    }

    function closePanel() { document.getElementById('analytics-panel').classList.add('translate-x-full'); }
    function openPanel() { document.getElementById('analytics-panel').classList.remove('translate-x-full'); }

    function startApp() {
      populateDropdown();
      initCharts();
      selectEntity('area', 'NM-MAHAPE');
      connectWS();
      setTimeout(updateLayers, 400);
    }

    if (document.readyState === 'complete' || document.readyState === 'interactive') {
      setTimeout(startApp, 100);
    } else {
      window.addEventListener('DOMContentLoaded', startApp);
      window.addEventListener('load', startApp);
    }
  </script>
</body>
</html>
"""

# -----------------------------------------------------------------------------
# FastAPI Lifecycle & Endpoints
# -----------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(data_manager.broadcast_loop())
    yield
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        logger.info("Broadcaster task cancelled.")

app = FastAPI(
    title="EnviroPulse 3D All-India Intelligence",
    description="High-Frequency Environmental & Natural Resource Telemetry Engine",
    version="2.5.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", response_class=HTMLResponse)
async def serve_dashboard():
    return HTMLResponse(content=STANDALONE_DASHBOARD_HTML)

@app.get("/api/hierarchy")
async def get_all_hierarchy():
    snapshot = data_manager.get_snapshot()
    return {
        "states": list(snapshot.states.keys()),
        "cities": list(snapshot.cities.keys()),
        "areas": list(snapshot.areas.keys()),
        "total_nodes": snapshot.global_stats.get("monitored_entities_count", 84),
        "timestamp": snapshot.timestamp
    }

@app.get("/api/entity/{tier}/{entity_id}")
async def get_entity_detail(tier: str, entity_id: str):
    snapshot = data_manager.get_snapshot()
    target_dict = {}
    if tier == "state": target_dict = snapshot.states
    elif tier == "city": target_dict = snapshot.cities
    elif tier == "area": target_dict = snapshot.areas
    else:
        target_dict = {**snapshot.states, **snapshot.cities, **snapshot.areas}

    if entity_id in target_dict:
        return target_dict[entity_id]
    return JSONResponse(status_code=404, content={"error": f"Entity '{entity_id}' not found in tier '{tier}'."})

@app.websocket("/ws/environmental-data")
async def websocket_telemetry_endpoint(websocket: WebSocket):
    await data_manager.register(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        data_manager.unregister(websocket)
    except Exception as e:
        logger.warning(f"WebSocket connection error: {e}")
        data_manager.unregister(websocket)
