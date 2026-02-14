"""
AI CRIME PATTERN PREDICTION FOR POLICE
CRITICAL FIX APPLIED: Resolved ERR_FILE_NOT_FOUND by loading the Folium map directly as an HTML string (in-memory) instead of relying on QUrl.fromLocalFile().
Data Loading Fix: Now programmatically creates the ZRP_Crime_Data_Sample_500.csv with provided data and enriches the missing 'Modus Operandi' column.
Key Updates:
1. Completed the data set to 500 records.
2. Implemented the Modus Operandi enrichment logic.
3. Implemented functional AI/ML training and prediction using RandomForest and KMeans.
4. Integrated all components into the PyQt6 GUI.
5. Enhanced login interface with modern design.
"""
import sys
import os
import sqlite3
import pandas as pd
import folium
import re
import random 
from collections import Counter
from io import StringIO 
import numpy as np
import hashlib
from datetime import datetime, timedelta
import time

# --- Library Imports ---
try:
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.cluster import KMeans
    from sklearn.preprocessing import LabelEncoder
    from fpdf import FPDF
    from html2image import Html2Image
except ImportError:
    print("Warning: Missing scikit-learn, fpdf2, or html2image. Please ensure all libraries are installed (pip install scikit-learn fpdf2 html2image).")
    Html2Image = None

from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QMainWindow,
    QMessageBox, QDateEdit, QTextEdit, QGridLayout, QComboBox, QDateTimeEdit,
    QDialog, QFormLayout, QProgressBar, QFrame
)
from PyQt6.QtCore import QDate, QUrl, Qt, QDateTime, QTimer
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWidgets import QGraphicsDropShadowEffect

# =====================================================================
# 1. DATABASE AND CORE AI MODEL (NATIONWIDE SCOPE)
# =====================================================================

DATABASE_NAME = 'ZRP_CrimeData.db'
CSV_FILENAME = 'ZRP_Crime_Data_Sample_500.csv'
N_CLUSTERS = 4
HOTSPOT_NAMES = {0: 'High-Risk Cluster', 1: 'Moderate-Risk Cluster', 2: 'Low-Risk Cluster', 3: 'General Cluster'}



# ZRP Police Stations (Sample locations across Zimbabwe)
ZRP_STATIONS = {
    "HARARE": [
        {"name": "Harare Central Police Station", "lat": -17.8252, "lon": 31.0531},
        {"name": "Avondale Police Station", "lat": -17.795, "lon": 31.035},
        {"name": "Mbare Police Station", "lat": -17.855, "lon": 31.045}
    ],
    "BULAWAYO": [
        {"name": "Bulawayo Central Police Station", "lat": -20.1508, "lon": 28.5795},
        {"name": "Nkulumane Police Station", "lat": -20.18, "lon": 28.55},
        {"name": "Entumbane Police Station", "lat": -20.13, "lon": 28.58}
    ],
    "CHITUNGWIZA": [
        {"name": "Chitungwiza Police Station", "lat": -18.0017, "lon": 31.0369},
        {"name": "Zengeza Police Post", "lat": -18.02, "lon": 31.04}
    ],
    "GWERU": [
        {"name": "Gweru Central Police Station", "lat": -19.4476, "lon": 29.8196},
        {"name": "Mkoba Police Station", "lat": -19.43, "lon": 29.82}
    ],
    "MASVINGO": [
        {"name": "Masvingo Central Police Station", "lat": -20.0660, "lon": 30.8328},
        {"name": "Mucheke Police Station", "lat": -20.08, "lon": 30.83}
    ],
    "MUTARE": [
        {"name": "Mutare Central Police Station", "lat": -18.9707, "lon": 32.6709},
        {"name": "Sakubva Police Station", "lat": -18.98, "lon": 32.68}
    ],
    "BEITBRIDGE": [
        {"name": "Beitbridge Police Station", "lat": -22.2140, "lon": 30.0036},
        {"name": "Dite Police Post", "lat": -22.22, "lon": 30.01}
    ],
    "CHINHOYI": [
        {"name": "Chinhoyi Police Station", "lat": -17.3667, "lon": 30.2},
        {"name": "Banket Police Post", "lat": -17.38, "lon": 30.22}
    ],
    "MARONDERA": [
        {"name": "Marondera Police Station", "lat": -18.1853, "lon": 31.5514},
        {"name": "Dombotombo Police Post", "lat": -18.17, "lon": 31.55}
    ],
    "KWEKWE": [
        {"name": "Kwekwe Central Police Station", "lat": -18.9167, "lon": 29.8167},
        {"name": "Redcliff Police Station", "lat": -18.92, "lon": 29.81}
    ],
    "ZVISHA": [
        {"name": "Zvishavane Police Station", "lat": -20.3333, "lon": 30.0667}
    ],
    "KADOMA": [
        {"name": "Kadoma Police Station", "lat": -18.3333, "lon": 29.9167},
        {"name": "Chegutu Police Station", "lat": -18.13, "lon": 30.14}
    ],
    "VIC FALLS": [
        {"name": "Victoria Falls Police Station", "lat": -17.9333, "lon": 25.8333}
    ],
    "HWANGE": [
        {"name": "Hwange Police Station", "lat": -18.3667, "lon": 26.5},
        {"name": "Dete Police Post", "lat": -18.62, "lon": 26.47}
    ],
    "BINDURA": [
        {"name": "Bindura Police Station", "lat": -17.3019, "lon": 31.3306}
    ],
    "DEFAULT": [
        {"name": "Nearest Police Station", "lat": -19.0154, "lon": 29.1549}
    ]
}

# Representative location centers across Zimbabwe (sample coordinates)
LOCATION_CENTERS = {
    "HARARE": {"lat": -17.8252, "lon": 31.0531, "risk": "High"},
    "BULAWAYO": {"lat": -20.1508, "lon": 28.5795, "risk": "High"},
    "CHITUNGWIZA": {"lat": -18.0017, "lon": 31.0369, "risk": "Moderate"},
    "GWERU": {"lat": -19.4476, "lon": 29.8196, "risk": "Moderate"},
    "MASVINGO": {"lat": -20.0660, "lon": 30.8328, "risk": "Moderate"},
    "MUTARE": {"lat": -18.9707, "lon": 32.6709, "risk": "Moderate"},
    "BEITBRIDGE": {"lat": -22.2140, "lon": 30.0036, "risk": "Critical"},
    "CHINHOYI": {"lat": -17.3667, "lon": 30.2, "risk": "Moderate"},
    "MARONDERA": {"lat": -18.1853, "lon": 31.5514, "risk": "Moderate"},
    "KWEKWE": {"lat": -18.9167, "lon": 29.8167, "risk": "Moderate"},
    "ZVISHA": {"lat": -20.3333, "lon": 30.0667, "risk": "Moderate"}, # Zvishavane
    "KADOMA": {"lat": -18.3333, "lon": 29.9167, "risk": "Moderate"},
    "VIC FALLS": {"lat": -17.9333, "lon": 25.8333, "risk": "Moderate"}, # Victoria Falls
    "HWANGE": {"lat": -18.3667, "lon": 26.5, "risk": "Moderate"},
    "BINDURA": {"lat": -17.3019, "lon": 31.3306, "risk": "Moderate"},
    "DEFAULT": {"lat": -19.0154, "lon": 29.1549, "risk": "General"}
}

# Location-Specific Learned Patterns (Simulated from CSV Analysis)
LOCATION_CRIME_PATTERNS = {
    "HARARE": {"Night_Crime": "Robbery", "Day_Crime": "Fraud", "General_Crime": "Cybercrime"},
    "BULAWAYO": {"Night_Crime": "Robbery", "Day_Crime": "Bribery", "General_Crime": "Assault"},
    "BEITBRIDGE": {"Night_Crime": "Stock Theft", "Day_Crime": "Smuggling", "General_Crime": "Rape"},
    "GWERU": {"Night_Crime": "Arson", "Day_Crime": "Drug Possession", "General_Crime": "Murder"},
    "CHITUNGWIZA": {"Night_Crime": "Robbery", "Day_Crime": "Fraud", "General_Crime": "Housebreaking"},
    "CHINHOYI": {"Night_Crime": "Murder", "Day_Crime": "Corruption", "General_Crime": "Theft"},
    "MARONDERA": {"Night_Crime": "Murder", "Day_Crime": "Bribery", "General_Crime": "Assault"},
    "KWEKWE": {"Night_Crime": "Arson", "Day_Crime": "Fraud", "General_Crime": "Kidnapping"},
    "ZVISHA": {"Night_Crime": "Robbery", "Day_Crime": "Stock Theft", "General_Crime": "Assault"},
    "KADOMA": {"Night_Crime": "Robbery", "Day_Crime": "Theft", "General_Crime": "Vandalism"},
    "VIC FALLS": {"Night_Crime": "Housebreaking", "Day_Crime": "Smuggling", "General_Crime": "Rape"},
    "HWANGE": {"Night_Crime": "Rape", "Day_Crime": "Kidnapping", "General_Crime": "Assault"},
    "MUTARE": {"Night_Crime": "Robbery", "Day_Crime": "Arson", "General_Crime": "Fraud"},
    "MASVINGO": {"Night_Crime": "Robbery", "Day_Crime": "Theft", "General_Crime": "Kidnapping"},
    "BINDURA": {"Night_Crime": "Murder", "Day_Crime": "Kidnapping", "General_Crime": "Rape"},
    "DEFAULT": {"Night_Crime": "Robbery", "Day_Crime": "Theft", "General_Crime": "Assault"}
}

def get_nearby_stations(location_key, user_lat=None, user_lon=None, max_distance=50):
    """Retrieves nearby ZRP stations for a given location key, optionally filtering by distance."""
    stations = ZRP_STATIONS.get(location_key.upper(), ZRP_STATIONS.get('DEFAULT', []))
    
    if user_lat is not None and user_lon is not None:
        # Calculate distance and filter (simple Euclidean for demo)
        nearby = []
        for station in stations:
            dist = ((station['lat'] - user_lat)**2 + (station['lon'] - user_lon)**2)**0.5 * 111  # Rough km
            if dist <= max_distance:
                nearby.append(station)
        return nearby
    return stations

# --- Modus Operandi Logic ---
def assign_modus_operandi(row):
    """Assigns a specific Modus Operandi based on the Crime Type and a simplified Location check."""
    offence = row['Crime Type']
    location = row['Location'].upper()
    
    if 'HARARE' in location or 'BULAWAYO' in location or 'CHITUNGWIZA' in location:
        area_type = 'City'
    elif 'BRIDGE' in location or 'FALLS' in location or 'HWANGE' in location:
        area_type = 'Transit'
    else:
        area_type = 'Town'

    if offence == 'Robbery':
        if area_type == 'City':
            return 'Armed, Targeting Cash Transit'
        return 'Machete Attack / Panga Robbery'
        
    elif offence == 'Housebreaking':
        if 'CBD' in location:
            return 'Smash-and-Grab Commercial'
        return 'Night-time Forced Entry (Residential)'

    elif offence == 'Theft':
        if area_type == 'Transit':
            return 'Pickpocketing in Crowded Area'
        return 'Theft of Auto Spares / Copper'
        
    elif offence == 'Murder':
        return 'Domestic Dispute Escalation' if random.random() < 0.5 else 'Ritualistic Crime'
        
    elif offence == 'Rape':
        return 'Acquaintance Rape' if random.random() < 0.6 else 'Stranger Assault / Predatory'
        
    elif offence == 'Stock Theft':
        return 'Cross-Border Smuggling' if area_type == 'Transit' else 'Night-time Farm Raid'
        
    elif offence == 'Smuggling':
        return 'Border Post Bypass (Official Corruption)'
        
    elif offence == 'Fraud' or offence == 'Cybercrime':
        return 'Internet Phishing/Mobile Money Scam'
        
    elif offence == 'Bribery' or offence == 'Corruption':
        return 'Police/Municipal Official Extortion'
        
    elif offence == 'Assault':
        return 'Bar Fight / Alcohol Induced'
        
    elif offence == 'Vandalism':
        return 'Political Graffiti / Public Property Damage'
        
    elif offence == 'Arson':
        return 'Business Dispute / Insurance Fraud'

    return 'Method Unspecified' # Default

# Provided CSV data as a string (Completed to simulate a full file)
PROVIDED_CSV_DATA = """Date,Crime Type,Location,Latitude,Longitude,Status,Summary
2024-05-19,Arson,Bindura,-17.3019,31.3306,Closed,Arson reported in bindura.
2024-05-23,Assault,Marondera,-18.1853,31.5514,Open,Assault reported in marondera.
2024-01-17,Housebreaking,Chinhoyi,-17.3667,30.2,Open,Housebreaking reported in chinhoyi.
2024-07-26,Arson,Mutare,-18.975,32.67,Open,Arson reported in mutare.
2024-06-05,Bribery,Bulawayo CBD,-20.1508,28.5795,Open,Bribery reported in bulawayo cbd.
2024-09-01,Stock Theft,Zvishavane,-20.3333,30.0667,Open,Stock Theft reported in zvishavane.
2024-02-08,Smuggling,Bulawayo CBD,-20.1508,28.5795,Under Investigation,Smuggling reported in bulawayo cbd.
2024-06-29,Housebreaking,Chinhoyi,-17.3667,30.2,Under Investigation,Housebreaking reported in chinhoyi.
2024-05-16,Vandalism,Chinhoyi,-17.3667,30.2,Open,Vandalism reported in chinhoyi.
2024-03-13,Murder,Chinhoyi,-17.3667,30.2,Under Investigation,Murder reported in chinhoyi.
2024-09-13,Vandalism,Mutare,-18.975,32.67,Closed,Vandalism reported in mutare.
2024-01-08,Rape,Marondera,-18.1853,31.5514,Under Investigation,Rape reported in marondera.
2024-07-20,Theft,Zvishavane,-20.3333,30.0667,Open,Theft reported in zvishavane.
2024-03-07,Fraud,Masvingo,-20.0637,30.8277,Open,Fraud reported in masvingo.
2024-04-06,Theft,Masvingo,-20.0637,30.8277,Open,Theft reported in masvingo.
2024-03-20,Theft,Victoria Falls,-17.9333,25.8333,Under Investigation,Theft reported in victoria falls.
2024-01-16,Murder,Marondera,-18.1853,31.5514,Closed,Murder reported in marondera.
2024-04-11,Arson,Chinhoyi,-17.3667,30.2,Closed,Arson reported in chinhoyi.
2024-01-21,Murder,Kwekwe,-18.9167,29.8167,Open,Murder reported in kwekwe.
2024-05-15,Drug Possession,Gweru,-19.45,29.8167,Closed,Drug Possession reported in gweru.
2024-09-28,Cybercrime,Beitbridge,-22.2167,30.0,Under Investigation,Cybercrime reported in beitbridge.
2024-09-04,Stock Theft,Kwekwe,-18.9167,29.8167,Closed,Stock Theft reported in kwekwe.
2024-02-15,Housebreaking,Victoria Falls,-17.9333,25.8333,Closed,Housebreaking reported in victoria falls.
2024-03-22,Vandalism,Gweru,-19.45,29.8167,Open,Vandalism reported in gweru.
2024-09-17,Theft,Bindura,-17.3019,31.3306,Under Investigation,Theft reported in bindura.
2024-06-10,Corruption,Kadoma,-18.3333,29.9167,Under Investigation,Corruption reported in kadoma.
2024-07-27,Vandalism,Kadoma,-18.3333,29.9167,Closed,Vandalism reported in kadoma.
2024-06-03,Cybercrime,Gweru,-19.45,29.8167,Under Investigation,Cybercrime reported in gweru.
2024-03-03,Robbery,Chitungwiza,-18.0127,31.0756,Open,Robbery reported in chitungwiza.
2024-09-29,Drug Possession,Kadoma,-18.3333,29.9167,Open,Drug Possession reported in kadoma.
2024-06-26,Arson,Gweru,-19.45,29.8167,Under Investigation,Arson reported in gweru.
2024-05-24,Murder,Zvishavane,-20.3333,30.0667,Under Investigation,Murder reported in zvishavane.
2024-08-15,Stock Theft,Masvingo,-20.0637,30.8277,Closed,Stock Theft reported in masvingo.
2024-05-25,Housebreaking,Victoria Falls,-17.9333,25.8333,Open,Housebreaking reported in victoria falls.
2024-02-01,Smuggling,Beitbridge,-22.2167,30.0,Closed,Smuggling reported in beitbridge.
2024-10-13,Theft,Chinhoyi,-17.3667,30.2,Under Investigation,Theft reported in chinhoyi.
2024-02-13,Drug Possession,Bulawayo CBD,-20.1508,28.5795,Under Investigation,Drug Possession reported in bulawayo cbd.
2024-07-16,Drug Possession,Zvishavane,-20.3333,30.0667,Under Investigation,Drug Possession reported in zvishavane.
2024-04-13,Robbery,Zvishavane,-20.3333,30.0667,Under Investigation,Robbery reported in zvishavane.
2024-03-31,Bribery,Chinhoyi,-17.3667,30.2,Open,Bribery reported in chinhoyi.
2024-03-12,Corruption,Chinhoyi,-17.3667,30.2,Under Investigation,Corruption reported in chinhoyi.
2024-08-15,Corruption,Victoria Falls,-17.9333,25.8333,Open,Corruption reported in victoria falls.
2024-06-29,Fraud,Chitungwiza,-18.0127,31.0756,Under Investigation,Fraud reported in chitungwiza.
2024-08-27,Stock Theft,Beitbridge,-22.2167,30.0,Under Investigation,Stock Theft reported in beitbridge.
2024-06-10,Rape,Victoria Falls,-17.9333,25.8333,Open,Rape reported in victoria falls.
2024-09-09,Robbery,Chitungwiza,-18.0127,31.0756,Closed,Robbery reported in chitungwiza.
2024-05-11,Bribery,Marondera,-18.1853,31.5514,Closed,Bribery reported in marondera.
2024-01-03,Murder,Victoria Falls,-17.9333,25.8333,Closed,Murder reported in victoria falls.
2024-06-28,Cybercrime,Mutare,-18.975,32.67,Under Investigation,Cybercrime reported in mutare.
2024-07-26,Arson,Kwekwe,-18.9167,29.8167,Open,Arson reported in kwekwe.
2024-06-09,Theft,Chitungwiza,-18.0127,31.0756,Closed,Theft reported in chitungwiza.
2024-06-11,Corruption,Chinhoyi,-17.3667,30.2,Closed,Corruption reported in chinhoyi.
2024-03-26,Cybercrime,Zvishavane,-20.3333,30.0667,Under Investigation,Cybercrime reported in zvishavane.
2024-04-06,Assault,Harare Central,-17.825,31.053,Under Investigation,Assault reported in harare central.
2024-01-19,Arson,Kadoma,-18.3333,29.9167,Under Investigation,Arson reported in kadoma.
2024-01-25,Stock Theft,Chitungwiza,-18.0127,31.0756,Closed,Stock Theft reported in chitungwiza.
2024-04-26,Fraud,Bulawayo CBD,-20.1508,28.5795,Under Investigation,Fraud reported in bulawayo cbd.
2024-01-22,Smuggling,Kwekwe,-18.9167,29.8167,Under Investigation,Smuggling reported in kwekwe.
2024-09-26,Kidnapping,Victoria Falls,-17.9333,25.8333,Under Investigation,Kidnapping reported in victoria falls.
2024-05-11,Drug Possession,Gweru,-19.45,29.8167,Open,Drug Possession reported in gweru.
2024-02-25,Rape,Victoria Falls,-17.9333,25.8333,Closed,Rape reported in victoria falls.
2024-05-09,Arson,Chitungwiza,-18.0127,31.0756,Under Investigation,Arson reported in chitungwiza.
2024-09-08,Murder,Chinhoyi,-17.3667,30.2,Under Investigation,Murder reported in chinhoyi.
2024-10-17,Fraud,Marondera,-18.1853,31.5514,Closed,Fraud reported in marondera.
2024-05-18,Smuggling,Victoria Falls,-17.9333,25.8333,Open,Smuggling reported in victoria falls.
2024-06-17,Theft,Zvishavane,-20.3333,30.0667,Open,Theft reported in zvishavane.
2024-08-02,Rape,Beitbridge,-22.2167,30.0,Closed,Rape reported in beitbridge.
2024-04-05,Assault,Kwekwe,-18.9167,29.8167,Closed,Assault reported in kwekwe.
2024-02-28,Theft,Gweru,-19.45,29.8167,Under Investigation,Theft reported in gweru.
2024-06-24,Assault,Bulawayo CBD,-20.1508,28.5795,Open,Assault reported in bulawayo cbd.
2024-08-10,Cybercrime,Chinhoyi,-17.3667,30.2,Under Investigation,Cybercrime reported in chinhoyi.
2024-04-09,Bribery,Beitbridge,-22.2167,30.0,Under Investigation,Bribery reported in beitbridge.
2024-03-03,Drug Possession,Bulawayo CBD,-20.1508,28.5795,Closed,Drug Possession reported in bulawayo cbd.
2024-03-24,Murder,Mutare,-18.975,32.67,Under Investigation,Murder reported in mutare.
2024-10-08,Housebreaking,Gweru,-19.45,29.8167,Under Investigation,Housebreaking reported in gweru.
2024-07-30,Fraud,Masvingo,-20.0637,30.8277,Closed,Fraud reported in masvingo.
2024-09-13,Kidnapping,Bindura,-17.3019,31.3306,Closed,Kidnapping reported in bindura.
2024-07-25,Smuggling,Chitungwiza,-18.0127,31.0756,Closed,Smuggling reported in chitungwiza.
2024-02-14,Arson,Bulawayo CBD,-20.1508,28.5795,Under Investigation,Arson reported in bulawayo cbd.
2024-03-26,Murder,Gweru,-19.45,29.8167,Closed,Murder reported in gweru.
2024-09-22,Drug Possession,Gweru,-19.45,29.8167,Open,Drug Possession reported in gweru.
2024-08-08,Corruption,Masvingo,-20.0637,30.8277,Open,Corruption reported in masvingo.
2024-03-08,Smuggling,Masvingo,-20.0637,30.8277,Closed,Smuggling reported in masvingo.
2024-01-18,Kidnapping,Hwange,-18.3667,26.5,Open,Kidnapping reported in hwange.
2024-01-29,Assault,Mutare,-18.975,32.67,Closed,Assault reported in mutare.
2024-03-18,Bribery,Masvingo,-20.0637,30.8277,Open,Bribery reported in masvingo.
2024-08-17,Vandalism,Gweru,-19.45,29.8167,Under Investigation,Vandalism reported in gweru.
2024-02-02,Smuggling,Masvingo,-20.0637,30.8277,Open,Smuggling reported in masvingo.
2024-05-09,Kidnapping,Hwange,-18.3667,26.5,Open,Kidnapping reported in hwange.
2024-07-21,Corruption,Gweru,-19.45,29.8167,Closed,Corruption reported in gweru.
2024-03-31,Bribery,Chitungwiza,-18.0127,31.0756,Open,Bribery reported in chitungwiza.
2024-04-25,Vandalism,Gweru,-19.45,29.8167,Open,Vandalism reported in gweru.
2024-07-27,Kidnapping,Masvingo,-20.0637,30.8277,Under Investigation,Kidnapping reported in masvingo.
2024-09-28,Kidnapping,Kwekwe,-18.9167,29.8167,Under Investigation,Kidnapping reported in kwezwe.
2024-03-06,Vandalism,Harare Central,-17.825,31.053,Closed,Vandalism reported in harare central.
2024-04-21,Kidnapping,Hwange,-18.3667,26.5,Under Investigation,Kidnapping reported in hwange.
2024-08-11,Assault,Marondera,-18.1853,31.5514,Open,Assault reported in marondera.
2024-04-24,Bribery,Chinhoyi,-17.3667,30.2,Closed,Bribery reported in chinhoyi.
2024-04-27,Assault,Victoria Falls,-17.9333,25.8333,Under Investigation,Assault reported in victoria falls.
2024-05-08,Drug Possession,Hwange,-18.3667,26.5,Under Investigation,Drug Possession reported in hwange.
2024-07-25,Arson,Hwange,-18.3667,26.5,Open,Arson reported in hwange.
2024-09-19,Theft,Gweru,-19.45,29.8167,Open,Theft reported in gweru.
2024-04-23,Fraud,Kwekwe,-18.9167,29.8167,Closed,Fraud reported in kwekwe.
2024-01-01,Robbery,Mutare,-18.975,32.67,Closed,Robbery reported in mutare.
2024-10-10,Robbery,Chitungwiza,-18.0127,31.0756,Under Investigation,Robbery reported in chitungwiza.
2024-09-14,Cybercrime,Zvishavane,-20.3333,30.0667,Under Investigation,Cybercrime reported in zvishavane.
2024-07-22,Rape,Bulawayo CBD,-20.1508,28.5795,Open,Rape reported in bulawayo cbd.
2024-01-09,Stock Theft,Zvishavane,-20.3333,30.0667,Closed,Stock Theft reported in zvishavane.
2024-08-09,Assault,Chitungwiza,-18.0127,31.0756,Closed,Assault reported in chitungwiza.
2024-07-10,Corruption,Chitungwiza,-18.0127,31.0756,Open,Corruption reported in chitungwiza.
2024-02-29,Housebreaking,Marondera,-18.1853,31.5514,Open,Housebreaking reported in marondera.
2024-07-07,Bribery,Kwekwe,-18.9167,29.8167,Under Investigation,Bribery reported in kwezwe.
2024-09-13,Smuggling,Marondera,-18.1853,31.5514,Open,Smuggling reported in marondera.
2024-09-20,Assault,Victoria Falls,-17.9333,25.8333,Closed,Assault reported in victoria falls.
2024-05-03,Theft,Harare Central,-17.825,31.053,Under Investigation,Theft reported in harare central.
2024-06-24,Assault,Zvishavane,-20.3333,30.0667,Closed,Assault reported in zvishavane.
2024-10-03,Kidnapping,Kwekwe,-18.9167,29.8167,Open,Kidnapping reported in kwezwe.
2024-04-21,Assault,Beitbridge,-22.2167,30.0,Under Investigation,Assault reported in beitbridge.
2024-07-04,Cybercrime,Chinhoyi,-17.3667,30.2,Open,Cybercrime reported in chinhoyi.
2024-10-25,Smuggling,Hwange,-18.3667,26.5,Closed,Smuggling reported in hwange.
2024-06-24,Corruption,Kwekwe,-18.9167,29.8167,Closed,Corruption reported in kwezwe.
2024-08-23,Arson,Victoria Falls,-17.9333,25.8333,Open,Arson reported in victoria falls.
2024-09-10,Corruption,Beitbridge,-22.2167,30.0,Under Investigation,Corruption reported in beitbridge.
2024-06-18,Drug Possession,Beitbridge,-22.2167,30.0,Closed,Drug Possession reported in beitbridge.
2024-07-10,Smuggling,Kwekwe,-18.9167,29.8167,Under Investigation,Smuggling reported in kwezwe.
2024-02-15,Bribery,Beitbridge,-22.2167,30.0,Open,Bribery reported in beitbridge.
2024-04-10,Stock Theft,Kadoma,-18.3333,29.9167,Open,Stock Theft reported in kadoma.
2024-10-14,Robbery,Harare Central,-17.825,31.053,Under Investigation,Robbery reported in harare central.
2024-05-06,Theft,Masvingo,-20.0637,30.8277,Open,Theft reported in masvingo.
2024-10-20,Smuggling,Kadoma,-18.3333,29.9167,Under Investigation,Smuggling reported in kadoma.
2024-03-10,Kidnapping,Masvingo,-20.0637,30.8277,Closed,Kidnapping reported in masvingo.
2024-02-12,Murder,Mutare,-18.975,32.67,Closed,Murder reported in mutare.
2024-06-26,Theft,Harare Central,-17.825,31.053,Closed,Theft reported in harare central.
2024-07-03,Cybercrime,Kadoma,-18.3333,29.9167,Open,Cybercrime reported in kadoma.
2024-04-20,Arson,Chinhoyi,-17.3667,30.2,Under Investigation,Arson reported in chinhoyi.
2024-05-25,Bribery,Bulawayo CBD,-20.1508,28.5795,Closed,Bribery reported in bulawayo cbd.
2024-01-23,Assault,Zvishavane,-20.3333,30.0667,Closed,Assault reported in zvishavane.
2024-10-17,Theft,Victoria Falls,-17.9333,25.8333,Under Investigation,Theft reported in victoria falls.
2024-03-18,Smuggling,Bulawayo CBD,-20.1508,28.5795,Open,Smuggling reported in bulawayo cbd.
2024-06-22,Corruption,Victoria Falls,-17.9333,25.8333,Closed,Corruption reported in victoria falls.
2024-10-22,Assault,Bulawayo CBD,-20.1508,28.5795,Closed,Assault reported in bulawayo cbd.
2024-08-05,Kidnapping,Gweru,-19.45,29.8167,Open,Kidnapping reported in gweru.
2024-04-26,Robbery,Mutare,-18.975,32.67,Closed,Robbery reported in mutare.
2024-06-16,Bribery,Hwange,-18.3667,26.5,Closed,Bribery reported in hwange.
2024-10-07,Housebreaking,Chitungwiza,-18.0127,31.0756,Open,Housebreaking reported in chitungwiza.
2024-10-09,Arson,Beitbridge,-22.2167,30.0,Closed,Arson reported in beitbridge.
2024-02-21,Bribery,Beitbridge,-22.2167,30.0,Under Investigation,Bribery reported in beitbridge.
2024-02-13,Drug Possession,Marondera,-18.1853,31.5514,Open,Drug Possession reported in marondera.
2024-03-13,Kidnapping,Zvishavane,-20.3333,30.0667,Under Investigation,Kidnapping reported in zvishavane.
2024-10-26,Fraud,Gweru,-19.45,29.8167,Closed,Fraud reported in gweru.
2024-05-14,Housebreaking,Kadoma,-18.3333,29.9167,Closed,Housebreaking reported in kadoma.
2024-01-23,Stock Theft,Gweru,-19.45,29.8167,Under Investigation,Stock Theft reported in gweru.
2024-10-21,Bribery,Chitungwiza,-18.0127,31.0756,Closed,Bribery reported in chitungwiza.
2024-07-13,Arson,Gweru,-19.45,29.8167,Under Investigation,Arson reported in gweru.
2024-05-14,Rape,Victoria Falls,-17.9333,25.8333,Under Investigation,Rape reported in victoria falls.
2024-02-03,Arson,Kwekwe,-18.9167,29.8167,Open,Arson reported in kwezwe.
2024-01-15,Kidnapping,Gweru,-19.45,29.8167,Under Investigation,Kidnapping reported in gweru.
2024-07-22,Rape,Beitbridge,-22.2167,30.0,Closed,Rape reported in beitbridge.
2024-03-13,Cybercrime,Harare Central,-17.825,31.053,Open,Cybercrime reported in harare central.
2024-10-01,Housebreaking,Chinhoyi,-17.3667,30.2,Open,Housebreaking reported in chinhoyi.
2024-10-01,Kidnapping,Gweru,-19.45,29.8167,Closed,Kidnapping reported in gweru.
2024-04-29,Murder,Gweru,-19.45,29.8167,Closed,Murder reported in gweru.
2024-09-12,Murder,Gweru,-19.45,29.8167,Open,Murder reported in gweru.
2024-10-16,Robbery,Masvingo,-20.0637,30.8277,Closed,Robbery reported in masvingo.
2024-04-06,Rape,Kadoma,-18.3333,29.9167,Under Investigation,Rape reported in kadoma.
2024-07-23,Murder,Chinhoyi,-17.3667,30.2,Open,Murder reported in chinhoyi.
2024-10-09,Robbery,Hwange,-18.3667,26.5,Under Investigation,Robbery reported in hwange.
2024-10-02,Rape,Victoria Falls,-17.9333,25.8333,Closed,Rape reported in victoria falls.
2024-04-20,Corruption,Zvishavane,-20.3333,30.0667,Closed,Corruption reported in zvishavane.
2024-03-18,Murder,Hwange,-18.3667,26.5,Under Investigation,Murder reported in hwange.
2024-02-27,Bribery,Masvingo,-20.0637,30.8277,Closed,Bribery reported in masvingo.
2024-09-22,Kidnapping,Kwekwe,-18.9167,29.8167,Closed,Kidnapping reported in kwezwe.
2024-08-26,Drug Possession,Masvingo,-20.0637,30.8277,Under Investigation,Drug Possession reported in masvingo.
2024-04-05,Fraud,Harare Central,-17.825,31.053,Closed,Fraud reported in harare central.
2024-06-24,Fraud,Chitungwiza,-18.0127,31.0756,Closed,Fraud reported in chitungwiza.
2024-04-16,Drug Possession,Gweru,-19.45,29.8167,Under Investigation,Drug Possession reported in gweru.
2024-03-29,Corruption,Kwekwe,-18.9167,29.8167,Under Investigation,Corruption reported in kwezwe.
2024-09-26,Rape,Chinhoyi,-17.3667,30.2,Under Investigation,Rape reported in chinhoyi.
2024-06-28,Rape,Hwange,-18.3667,26.5,Closed,Rape reported in hwange.
2024-06-04,Fraud,Chinhoyi,-17.3667,30.2,Closed,Fraud reported in chinhoyi.
2024-07-22,Drug Possession,Hwange,-18.3667,26.5,Under Investigation,Drug Possession reported in hwange.
2024-05-04,Murder,Chinhoyi,-17.3667,30.2,Closed,Murder reported in chinhoyi.
2024-02-22,Smuggling,Hwange,-18.3667,26.5,Closed,Smuggling reported in hwange.
2024-01-11,Theft,Bindura,-17.3019,31.3306,Under Investigation,Theft reported in bindura.
2024-04-28,Murder,Zvishavane,-20.3333,30.0667,Closed,Murder reported in zvishavane.
2024-03-28,Stock Theft,Victoria Falls,-17.9333,25.8333,Open,Stock Theft reported in victoria falls.
2024-05-14,Murder,Harare Central,-17.825,31.053,Under Investigation,Murder reported in harare central.
2024-06-12,Drug Possession,Hwange,-18.3667,26.5,Open,Drug Possession reported in hwange.
2024-03-06,Corruption,Chitungwiza,-18.0127,31.0756,Closed,Corruption reported in chitungwiza.
2024-06-19,Theft,Mutare,-18.975,32.67,Open,Theft reported in mutare.
2024-07-25,Fraud,Harare Central,-17.825,31.053,Open,Fraud reported in harare central.
2024-07-08,Murder,Bindura,-17.3019,31.3306,Open,Murder reported in bindura.
2024-10-08,Smuggling,Chitungwiza,-18.0127,31.0756,Open,Smuggling reported in chitungwiza.
2024-06-30,Arson,Hwange,-18.3667,26.5,Open,Arson reported in hwange.
2024-01-10,Fraud,Harare Central,-17.825,31.053,Closed,Fraud reported in harare central.
2024-05-15,Housebreaking,Chinhoyi,-17.3667,30.2,Closed,Housebreaking reported in chinhoyi.
2024-09-28,Corruption,Zvishavane,-20.3333,30.0667,Under Investigation,Corruption reported in zvishavane.
2024-04-10,Fraud,Victoria Falls,-17.9333,25.8333,Under Investigation,Fraud reported in victoria falls.
2024-07-24,Drug Possession,Chinhoyi,-17.3667,30.2,Closed,Drug Possession reported in chinhoyi.
2024-10-16,Bribery,Marondera,-18.1853,31.5514,Closed,Bribery reported in marondera.
2024-04-17,Fraud,Victoria Falls,-17.9333,25.8333,Open,Fraud reported in victoria falls.
2024-06-25,Rape,Kadoma,-18.3333,29.9167,Closed,Rape reported in kadoma.
2024-07-31,Smuggling,Masvingo,-20.0637,30.8277,Open,Smuggling reported in masvingo.
2024-05-23,Vandalism,Masvingo,-20.0637,30.8277,Under Investigation,Vandalism reported in masvingo.
2024-07-05,Housebreaking,Marondera,-18.1853,31.5514,Under Investigation,Housebreaking reported in marondera.
2024-08-03,Bribery,Hwange,-18.3667,26.5,Closed,Bribery reported in hwange.
2024-02-18,Robbery,Gweru,-19.45,29.8167,Under Investigation,Robbery reported in gweru.
2024-01-09,Housebreaking,Mutare,-18.975,32.67,Under Investigation,Housebreaking reported in mutare.
2024-02-24,Kidnapping,Hwange,-18.3667,26.5,Open,Kidnapping reported in hwange.
2024-04-17,Kidnapping,Hwange,-18.3667,26.5,Open,Kidnapping reported in hwange.
2024-07-08,Rape,Gweru,-19.45,29.8167,Closed,Rape reported in gweru.
2024-01-20,Rape,Hwange,-18.3667,26.5,Open,Rape reported in hwange.
2024-01-28,Bribery,Beitbridge,-22.2167,30.0,Under Investigation,Bribery reported in beitbridge.
2024-05-04,Fraud,Marondera,-18.1853,31.5514,Closed,Fraud reported in marondera.
2024-07-29,Bribery,Mutare,-18.975,32.67,Closed,Bribery reported in mutare.
2024-01-22,Assault,Harare Central,-17.825,31.053,Closed,Assault reported in harare central.
2024-02-21,Fraud,Bulawayo CBD,-20.1508,28.5795,Under Investigation,Fraud reported in bulawayo cbd.
2024-02-05,Smuggling,Kadoma,-18.3333,29.9167,Open,Smuggling reported in kadoma.
2024-04-01,Smuggling,Marondera,-18.1853,31.5514,Open,Smuggling reported in marondera.
2024-10-04,Vandalism,Chinhoyi,-17.3667,30.2,Under Investigation,Vandalism reported in chinhoyi.
2024-05-27,Corruption,Zvishavane,-20.3333,30.0667,Closed,Corruption reported in zvishavane.
2024-07-10,Assault,Victoria Falls,-17.9333,25.8333,Under Investigation,Assault reported in victoria falls.
2024-05-28,Cybercrime,Bulawayo CBD,-20.1508,28.5795,Open,Cybercrime reported in bulawayo cbd.
2024-04-12,Stock Theft,Zvishavane,-20.3333,30.0667,Under Investigation,Stock Theft reported in zvishavane.
2024-08-21,Assault,Kwekwe,-18.9167,29.8167,Closed,Assault reported in kwezwe.
2024-06-19,Murder,Zvishavane,-20.3333,30.0667,Closed,Murder reported in zvishavane.
2024-03-31,Robbery,Kadoma,-18.3333,29.9167,Open,Robbery reported in kadoma.
2024-10-09,Corruption,Hwange,-18.3667,26.5,Open,Corruption reported in hwange.
2024-04-04,Smuggling,Gweru,-19.45,29.8167,Closed,Smuggling reported in gweru.
2024-03-10,Drug Possession,Chinhoyi,-17.3667,30.2,Under Investigation,Drug Possession reported in chinhoyi.
2024-08-23,Vandalism,Beitbridge,-22.2167,30.0,Open,Vandalism reported in beitbridge.
2024-04-01,Rape,Beitbridge,-22.2167,30.0,Open,Rape reported in beitbridge.
2024-08-01,Vandalism,Chitungwiza,-18.0127,31.0756,Under Investigation,Vandalism reported in chitungwiza.
2024-05-16,Arson,Kadoma,-18.3333,29.9167,Open,Arson reported in kadoma.
2024-04-12,Robbery,Beitbridge,-22.2167,30.0,Open,Robbery reported in beitbridge.
2024-05-02,Bribery,Chitungwiza,-18.0127,31.0756,Open,Bribery reported in chitungwiza.
2024-03-31,Stock Theft,Bulawayo CBD,-20.1508,28.5795,Under Investigation,Stock Theft reported in bulawayo cbd.
2024-01-06,Housebreaking,Victoria Falls,-17.9333,25.8333,Open,Housebreaking reported in victoria falls.
2024-01-07,Robbery,Bulawayo CBD,-20.1508,28.5795,Under Investigation,Robbery reported in bulawayo cbd.
2024-06-19,Drug Possession,Victoria Falls,-17.9333,25.8333,Open,Drug Possession reported in victoria falls.
2024-03-16,Drug Possession,Hwange,-18.3667,26.5,Open,Drug Possession reported in hwange.
2024-04-11,Murder,Chinhoyi,-17.3667,30.2,Closed,Murder reported in chinhoyi.
2024-04-15,Arson,Chitungwiza,-18.0127,31.0756,Open,Arson reported in chitungwiza.
2024-04-07,Cybercrime,Masvingo,-20.0637,30.8277,Under Investigation,Cybercrime reported in masvingo.
2024-04-26,Robbery,Gweru,-19.45,29.8167,Open,Robbery reported in gweru.
2024-10-13,Rape,Gweru,-19.45,29.8167,Open,Rape reported in gweru.
2024-05-23,Vandalism,Chinhoyi,-17.3667,30.2,Open,Vandalism reported in chinhoyi.
2024-03-05,Smuggling,Bulawayo CBD,-20.1508,28.5795,Under Investigation,Smuggling reported in bulawayo cbd.
2024-08-04,Vandalism,Bindura,-17.3019,31.3306,Under Investigation,Vandalism reported in bindura.
2024-05-05,Rape,Chitungwiza,-18.0127,31.0756,Under Investigation,Rape reported in chitungwiza.
2024-03-02,Robbery,Mutare,-18.975,32.67,Under Investigation,Robbery reported in mutare.
2024-01-18,Fraud,Mutare,-18.975,32.67,Under Investigation,Fraud reported in mutare.
2024-09-05,Robbery,Chinhoyi,-17.3667,30.2,Under Investigation,Robbery reported in chinhoyi.
2024-06-10,Cybercrime,Marondera,-18.1853,31.5514,Closed,Cybercrime reported in marondera.
2024-05-03,Rape,Gweru,-19.45,29.8167,Closed,Rape reported in gweru.
2024-10-05,Vandalism,Chitungwiza,-18.0127,31.0756,Under Investigation,Vandalism reported in chitungwiza.
2024-09-18,Smuggling,Chinhoyi,-17.3667,30.2,Open,Smuggling reported in chinhoyi.
2024-07-18,Housebreaking,Hwange,-18.3667,26.5,Under Investigation,Housebreaking reported in hwange.
2024-02-27,Smuggling,Gweru,-19.45,29.8167,Open,Smuggling reported in gweru.
2024-05-25,Murder,Chinhoyi,-17.3667,30.2,Closed,Murder reported in chinhoyi.
2024-04-15,Murder,Chinhoyi,-17.3667,30.2,Under Investigation,Murder reported in chinhoyi.
2024-05-25,Smuggling,Kadoma,-18.3333,29.9167,Closed,Smuggling reported in kadoma.
2024-03-24,Kidnapping,Mutare,-18.975,32.67,Under Investigation,Kidnapping reported in mutare.
2024-10-15,Fraud,Marondera,-18.1853,31.5514,Closed,Fraud reported in marondera.
2024-08-06,Assault,Kadoma,-18.3333,29.9167,Closed,Assault reported in kadoma.
2024-04-04,Bribery,Bindura,-17.3019,31.3306,Under Investigation,Bribery reported in bindura.
2024-10-23,Robbery,Harare Central,-17.825,31.053,Open,Robbery reported in harare central.
2024-09-12,Bribery,Harare Central,-17.825,31.053,Closed,Bribery reported in harare central.
2024-10-25,Bribery,Harare Central,-17.825,31.053,Open,Bribery reported in harare central.
2024-01-07,Cybercrime,Victoria Falls,-17.9333,25.8333,Under Investigation,Cybercrime reported in victoria falls.
2024-10-08,Murder,Kwekwe,-18.9167,29.8167,Closed,Murder reported in kwezwe.
2024-07-24,Cybercrime,Zvishavane,-20.3333,30.0667,Open,Cybercrime reported in zvishavane.
2024-02-25,Kidnapping,Masvingo,-20.0637,30.8277,Under Investigation,Kidnapping reported in masvingo.
2024-06-23,Rape,Harare Central,-17.825,31.053,Open,Rape reported in harare central.
2024-05-21,Fraud,Victoria Falls,-17.9333,25.8333,Open,Fraud reported in victoria falls.
2024-07-29,Housebreaking,Gweru,-19.45,29.8167,Open,Housebreaking reported in gweru.
2024-01-11,Fraud,Victoria Falls,-17.9333,25.8333,Open,Fraud reported in victoria falls.
2024-02-25,Assault,Chitungwiza,-18.0127,31.0756,Under Investigation,Assault reported in chitungwiza.
2024-02-01,Housebreaking,Bulawayo CBD,-20.1508,28.5795,Under Investigation,Housebreaking reported in bulawayo cbd.
2024-07-24,Fraud,Kwekwe,-18.9167,29.8167,Under Investigation,Fraud reported in kwezwe.
2024-01-11,Rape,Bindura,-17.3019,31.3306,Closed,Rape reported in bindura.
2024-07-17,Drug Possession,Kwekwe,-18.9167,29.8167,Under Investigation,Drug Possession reported in kwezwe.
2024-08-04,Fraud,Kwekwe,-18.9167,29.8167,Open,Fraud reported in kwezwe.
2024-10-07,Drug Possession,Gweru,-19.45,29.8167,Open,Drug Possession reported in gweru.
2024-02-08,Drug Possession,Beitbridge,-22.2167,30.0,Under Investigation,Drug Possession reported in beitbridge.
2024-10-03,Vandalism,Bulawayo CBD,-20.1508,28.5795,Under Investigation,Vandalism reported in bulawayo cbd.
2024-02-10,Corruption,Hwange,-18.3667,26.5,Open,Corruption reported in hwange.
2024-02-23,Rape,Marondera,-18.1853,31.5514,Under Investigation,Rape reported in marondera.
2024-09-15,Arson,Zvishavane,-20.3333,30.0667,Closed,Arson reported in zvishavane.
2024-10-01,Assault,Hwange,-18.3667,26.5,Open,Assault reported in hwange.
2024-08-21,Rape,Bindura,-17.3019,31.3306,Closed,Rape reported in bindura.
2024-05-06,Murder,Zvishavane,-20.3333,30.0667,Closed,Murder reported in zvishavane.
2024-08-15,Drug Possession,Beitbridge,-22.2167,30.0,Open,Drug Possession reported in beitbridge.
2024-05-24,Bribery,Marondera,-18.1853,31.5514,Open,Bribery reported in marondera.
2024-06-22,Fraud,Chinhoyi,-17.3667,30.2,Under Investigation,Fraud reported in chinhoyi.
2024-01-13,Assault,Victoria Falls,-17.9333,25.8333,Open,Assault reported in victoria falls.
2024-02-15,Assault,Chinhoyi,-17.3667,30.2,Under Investigation,Assault reported in chinhoyi.
2024-07-09,Vandalism,Bulawayo CBD,-20.1508,28.5795,Under Investigation,Vandalism reported in bulawayo cbd.
2024-04-28,Murder,Kadoma,-18.3333,29.9167,Closed,Murder reported in kadoma.
2024-08-02,Stock Theft,Zvishavane,-20.3333,30.0667,Closed,Stock Theft reported in zvishavane.
2024-01-31,Robbery,Gweru,-19.45,29.8167,Under Investigation,Robbery reported in gweru.
2024-02-05,Corruption,Zvishavane,-20.3333,30.0667,Closed,Corruption reported in zvishavane.
2024-01-06,Bribery,Bulawayo CBD,-20.1508,28.5795,Under Investigation,Bribery reported in bulawayo cbd.
2024-10-06,Rape,Hwange,-18.3667,26.5,Closed,Rape reported in hwange.
2024-08-26,Cybercrime,Beitbridge,-22.2167,30.0,Under Investigation,Cybercrime reported in beitbridge.
2024-09-24,Rape,Victoria Falls,-17.9333,25.8333,Under Investigation,Rape reported in victoria falls.
2024-09-23,Corruption,Zvishavane,-20.3333,30.0667,Under Investigation,Corruption reported in zvishavane.
2024-01-06,Arson,Gweru,-19.45,29.8167,Open,Arson reported in gweru.
2024-09-23,Bribery,Bulawayo CBD,-20.1508,28.5795,Open,Bribery reported in bulawayo cbd.
2024-06-09,Stock Theft,Chitungwiza,-18.0127,31.0756,Closed,Stock Theft reported in chitungwiza.
2024-01-13,Cybercrime,Mutare,-18.975,32.67,Under Investigation,Cybercrime reported in mutare."""

# --- GENERATE REMAINING DATA TO REACH 500 RECORDS ---
def generate_remaining_data(existing_data, target_count=500):
    df_existing = pd.read_csv(StringIO(existing_data))
    current_count = len(df_existing)
    if current_count >= target_count:
        return existing_data
    
    locations = list(LOCATION_CRIME_PATTERNS.keys())
    locations.remove('DEFAULT')
    crime_types = list(set(df_existing['Crime Type']))
    
    new_records = []
    start_date = pd.to_datetime('2024-01-01')
    end_date = pd.to_datetime('2024-10-31')
    time_delta = (end_date - start_date).days

    for i in range(current_count, target_count):
        date = (start_date + pd.Timedelta(days=random.randint(0, time_delta))).strftime('%Y-%m-%d')
        crime = random.choice(crime_types)
        
        # Select a location and get its coordinates
        loc_key = random.choice(locations)
        loc_data = LOCATION_CENTERS.get(loc_key, LOCATION_CENTERS['DEFAULT'])
        
        # Add slight jitter to coordinates for distinct map markers
        lat = loc_data['lat'] + random.uniform(-0.05, 0.05)
        lon = loc_data['lon'] + random.uniform(-0.05, 0.05)
        
        status = random.choice(['Open', 'Closed', 'Under Investigation'])
        summary = f"{crime} reported in {loc_key.capitalize()} area. (Simulated)"
        
        new_records.append([date, crime, loc_key, lat, lon, status, summary])

    # Convert to DataFrame
    df_new = pd.DataFrame(new_records, columns=df_existing.columns)
    df_combined = pd.concat([df_existing, df_new], ignore_index=True)
    return df_combined.to_csv(index=False)

# Update the global data string
PROVIDED_CSV_DATA = generate_remaining_data(PROVIDED_CSV_DATA, target_count=500)


# =====================================================================
# 2. CORE FUNCTIONS: DATA PREPARATION, MODEL TRAINING, AND PREDICTION
# =====================================================================

def prepare_data(df):
    """Prepares and cleans the DataFrame for ML and clustering."""
    
    # 1. Add Modus Operandi (The user's core request)
    df['Modus Operandi'] = df.apply(assign_modus_operandi, axis=1)
    
    # 2. Feature Engineering
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    df['DayOfWeek'] = df['Date'].dt.dayofweek # Monday=0, Sunday=6
    df['Month'] = df['Date'].dt.month
    df['Hour'] = pd.Series([random.randint(0, 23) for _ in range(len(df))]) # Simulate missing Hour data

    # 3. Label Encoding for Categorical Features
    le_crime = LabelEncoder()
    le_location = LabelEncoder()
    le_mo = LabelEncoder()

    df['Crime_Code'] = le_crime.fit_transform(df['Crime Type'])
    df['Location_Code'] = le_location.fit_transform(df['Location'])
    df['MO_Code'] = le_mo.fit_transform(df['Modus Operandi'])
    
    return df, le_crime, le_location, le_mo

def initialize_database(df):
    """Initializes the SQLite database and populates it with prepared data."""
    try:
        conn = sqlite3.connect(DATABASE_NAME)
        # Save enriched DataFrame to CSV (for persistence) and DB
        df.to_csv(CSV_FILENAME, index=False)
        df.to_sql('crime_reports', conn, if_exists='replace', index=False)
        conn.close()
        return True
    except Exception as e:
        print(f"Error initializing database: {e}")
        return False

def load_data():
    """Loads data from the database into a DataFrame."""
    try:
        conn = sqlite3.connect(DATABASE_NAME)
        df = pd.read_sql_query("SELECT * FROM crime_reports", conn)
        conn.close()
        return df
    except Exception as e:
        print(f"Error loading data: {e}")
        return pd.DataFrame()

def train_ai_model(df):
    """Trains the Random Forest and K-Means models."""
    if df.empty:
        return None, None

    # A. Feature Selection for Random Forest (Crime Prediction)
    features_clf = ['Location_Code', 'DayOfWeek', 'Month', 'Hour']
    target_clf = 'Crime_Code'
    
    X_clf = df[features_clf]
    y_clf = df[target_clf]

    # Initialize and Train Random Forest Classifier
    rf_model = RandomForestClassifier(n_estimators=100, random_state=42, class_weight='balanced')
    rf_model.fit(X_clf, y_clf)
    
    # B. Feature Selection for K-Means (Hotspot Clustering)
    features_kmeans = ['Latitude', 'Longitude']
    X_k = df[features_kmeans]

    # Initialize and Train K-Means Clustering
    kmeans_model = KMeans(n_clusters=N_CLUSTERS, random_state=42, n_init=10)
    df['Cluster_ID'] = kmeans_model.fit_predict(X_k)

    return rf_model, kmeans_model

def predict_crime_pattern(rf_model, le_crime, le_location, df, location_name, target_date_time):
    """Predicts the most likely crime type for a given location and time, including anticipated date/times."""
    location_key = location_name.split('(')[0].strip().upper()

    if location_key not in LOCATION_CENTERS:
        location_key = "DEFAULT"

    # Use the Location_Code from the LabelEncoder fitted earlier
    try:
        # Create a temporary DataFrame to find the corresponding Location_Code
        temp_df = pd.DataFrame({'Location': le_location.classes_})
        loc_code = temp_df[temp_df['Location'].str.contains(location_key, case=False, na=False)].index[0]
    except:
        loc_code = 0 # Default if lookup fails

    # Extract features from input
    input_date = target_date_time.toPyDateTime()
    day_of_week = input_date.weekday() # Monday=0, Sunday=6
    month = input_date.month
    hour = input_date.hour

    # Create prediction array
    X_pred = pd.DataFrame([[loc_code, day_of_week, month, hour]],
                          columns=['Location_Code', 'DayOfWeek', 'Month', 'Hour'])

    # 1. Prediction using Random Forest (Probability of all crimes)
    pred_proba = rf_model.predict_proba(X_pred)[0]
    top_n = 3
    top_indices = np.argsort(pred_proba)[::-1][:top_n]

    # Get the names of the top predicted crimes
    predicted_crimes = [le_crime.inverse_transform([idx])[0] for idx in top_indices]

    # 2. Get the corresponding Modus Operandi for the top predicted crime
    df_loc = df[df['Location'].str.contains(location_key, case=False, na=False)]

    if not df_loc.empty:
        # Find the most frequent MO for the top predicted crime in that area
        relevant_df = df_loc[df_loc['Crime Type'] == predicted_crimes[0]]
        if not relevant_df.empty:
            mo_count = relevant_df['Modus Operandi'].mode()
            predicted_mo = mo_count[0] if not mo_count.empty else "MO Pattern Undetermined"
        else:
            predicted_mo = "General MO in Area"
    else:
        predicted_mo = "General MO in Area"

    # 3. Generate anticipated date/times for each predicted crime within 72-hour window
    start_datetime = input_date
    end_datetime = start_datetime + pd.Timedelta(hours=72)
    anticipated_crimes = []
    for i, crime in enumerate(predicted_crimes):
        # Simulate random time within the window
        random_hours = random.randint(0, 72)
        anticipated_dt = start_datetime + pd.Timedelta(hours=random_hours)
        # For top crime, use the predicted_mo; for others, a general MO or simulated
        mo = predicted_mo if i == 0 else f"Simulated MO for {crime}"
        anticipated_crimes.append((crime, anticipated_dt, mo))

    return predicted_crimes, predicted_mo, anticipated_crimes


# =====================================================================
# 3. MAPPING AND REPORTING
# =====================================================================

# Define colors for different crime types
CRIME_COLORS = {
    'Robbery': 'red',
    'Assault': 'orange',
    'Theft': 'yellow',
    'Murder': 'black',
    'Rape': 'purple',
    'Fraud': 'blue',
    'Housebreaking': 'green',
    'Arson': 'brown',
    'Bribery': 'pink',
    'Corruption': 'gray',
    'Cybercrime': 'cyan',
    'Drug Possession': 'lime',
    'Kidnapping': 'magenta',
    'Smuggling': 'navy',
    'Stock Theft': 'olive',
    'Vandalism': 'maroon'
}

def generate_hotspot_map(df, kmeans_model, user_location=None, nearby_stations=None, anticipated_crimes=None):
    """Generates a Folium map showing the crime hotspots (K-Means clusters), user location, nearby stations, and crime markers for the selected location."""
    if df.empty or kmeans_model is None:
        # Create a basic map centered on Zimbabwe if no data
        return folium.Map(location=[-19.0154, 29.1549], zoom_start=6)._repr_html_()

    # Center the map near the centroid of all reported crimes or user location if provided
    if user_location:
        map_center = [user_location['lat'], user_location['lon']]
        zoom_start = 10  # Zoom in for location-specific view
    else:
        map_center = [df['Latitude'].mean(), df['Longitude'].mean()]
        zoom_start = 6

    m = folium.Map(location=map_center, zoom_start=zoom_start, tiles='CartoDB positron')

    # Get the cluster centers from K-Means
    centers = kmeans_model.cluster_centers_

    # Calculate crime density for each cluster
    cluster_counts = df['Cluster_ID'].value_counts().to_dict()
    max_count = max(cluster_counts.values()) if cluster_counts else 1

    # Define colors for hotspots
    hotspot_colors = {0: 'red', 1: 'orange', 2: 'purple', 3: 'blue'}

    # Add cluster markers
    for i, (lat, lon) in enumerate(centers):
        cluster_id = i
        hotspot_name = f"Hotspot {cluster_id}"
        crime_count = cluster_counts.get(cluster_id, 0)

        # Determine the radius based on crime density (for visual impact)
        radius = 5000 + (crime_count / max_count) * 15000

        # Calculate the most frequent crime in the cluster
        cluster_data = df[df['Cluster_ID'] == cluster_id]
        top_crime = cluster_data['Crime Type'].mode().iloc[0] if not cluster_data.empty else "N/A"

        popup_html = f"""
            <b>Hotspot:</b> {hotspot_name}<br>
            <b>Total Cases:</b> {crime_count}<br>
            <b>Top Crime:</b> {top_crime}<br>
            <b>Coordinates:</b> ({lat:.4f}, {lon:.4f})
        """

        folium.Circle(
            location=[lat, lon],
            radius=radius,
            color=hotspot_colors.get(cluster_id, 'gray'),
            fill=True,
            fill_color=hotspot_colors.get(cluster_id, 'gray'),
            fill_opacity=0.6,
            popup=popup_html
        ).add_to(m)

    # Add crime markers for the selected location if provided
    if user_location:
        loc_key = user_location.get('name', '').upper()
        df_loc = df[df['Location'].str.contains(loc_key, case=False, na=False)]
        for _, row in df_loc.iterrows():
            crime = row['Crime Type']
            color = CRIME_COLORS.get(crime, 'gray')
            folium.CircleMarker(
                location=[row['Latitude'], row['Longitude']],
                radius=5,
                color=color,
                fill=True,
                fill_color=color,
                fill_opacity=0.7,
                popup=f"<b>Crime:</b> {crime}<br><b>Date:</b> {row['Date']}<br><b>Summary:</b> {row['Summary']}"
            ).add_to(m)

    # Add user location marker if provided
    if user_location:
        folium.Marker(
            location=[user_location['lat'], user_location['lon']],
            popup=f"<b>User Location:</b> {user_location.get('name', 'Entered Location')}",
            icon=folium.Icon(color='green', icon='user')
        ).add_to(m)

    # Add nearby stations markers if provided
    if nearby_stations:
        for station in nearby_stations:
            folium.Marker(
                location=[station['lat'], station['lon']],
                popup=f"<b>ZRP Station:</b> {station['name']}",
                icon=folium.Icon(color='blue', icon='shield')
            ).add_to(m)

    # Add anticipated crimes markers if provided
    if anticipated_crimes and user_location:
        for i, (crime, dt, mo) in enumerate(anticipated_crimes):
            color = CRIME_COLORS.get(crime, 'gray')
            # Slight offset to avoid overlap
            offset_lat = user_location['lat'] + (i * 0.001)
            offset_lon = user_location['lon'] + (i * 0.001)
            folium.Marker(
                location=[offset_lat, offset_lon],
                popup=f"<b>Anticipated Crime:</b> {crime}<br><b>Date/Time:</b> {dt.strftime('%Y-%m-%d %H:%M')}<br><b>M.O.:</b> {mo}",
                icon=folium.Icon(color=color, icon='exclamation-triangle')
            ).add_to(m)

    # Convert the Folium map to an HTML string
    return m._repr_html_()


# =====================================================================
# 4. USER MANAGEMENT AND AUTHENTICATION
# =====================================================================

def hash_password(password):
    """Hash a password using SHA-256."""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password, hashed):
    """Verify a password against its hash."""
    return hash_password(password) == hashed

def initialize_user_database():
    """Initialize user management tables in the database."""
    try:
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL,
                full_name TEXT,
                email TEXT,
                created_date TEXT NOT NULL,
                last_login TEXT,
                is_active INTEGER DEFAULT 1,
                daily_prediction_count INTEGER DEFAULT 0,
                last_prediction_date TEXT
            )
        ''')
        
        # User sessions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                login_time TEXT NOT NULL,
                logout_time TEXT,
                session_duration INTEGER,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        
        # Audit logs table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                username TEXT,
                action TEXT NOT NULL,
                details TEXT,
                timestamp TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        
        # System settings table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS system_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                setting_key TEXT UNIQUE NOT NULL,
                setting_value TEXT NOT NULL,
                description TEXT,
                updated_by TEXT,
                updated_date TEXT
            )
        ''')
        
        # Prediction history table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS prediction_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                username TEXT NOT NULL,
                location TEXT NOT NULL,
                prediction_date TEXT NOT NULL,
                predicted_crimes TEXT,
                timestamp TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        
        # Generated reports table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS generated_reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                username TEXT NOT NULL,
                report_type TEXT NOT NULL,
                location TEXT,
                file_path TEXT NOT NULL,
                generation_date TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        
        # Check if default admin exists
        cursor.execute("SELECT COUNT(*) FROM users WHERE username = 'admin'")
        if cursor.fetchone()[0] == 0:
            # Create default users
            default_users = [
                ('admin', hash_password('admin'), 'Admin', 'System Administrator', 'admin@zrp.gov.zw'),
                ('analyst', hash_password('analyst'), 'Data Analyst', 'Crime Data Analyst', 'analyst@zrp.gov.zw'),
                ('user', hash_password('user'), 'Standard User', 'Police Officer', 'user@zrp.gov.zw')
            ]
            
            for username, pwd_hash, role, full_name, email in default_users:
                cursor.execute('''
                    INSERT INTO users (username, password_hash, role, full_name, email, created_date, is_active)
                    VALUES (?, ?, ?, ?, ?, ?, 1)
                ''', (username, pwd_hash, role, full_name, email, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        
        # Initialize default system settings
        default_settings = [
            ('standard_user_daily_quota', '10', 'Daily prediction quota for Standard Users'),
            ('session_timeout_minutes', '60', 'Session timeout in minutes'),
            ('data_retention_days', '365', 'Number of days to retain audit logs'),
            ('enable_email_notifications', 'false', 'Enable email notifications')
        ]
        
        for key, value, desc in default_settings:
            cursor.execute('''
                INSERT OR IGNORE INTO system_settings (setting_key, setting_value, description, updated_date)
                VALUES (?, ?, ?, ?)
            ''', (key, value, desc, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error initializing user database: {e}")
        return False

def log_audit(user_id, username, action, details=""):
    """Log an action to the audit trail."""
    try:
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO audit_logs (user_id, username, action, details, timestamp)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, username, action, details, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error logging audit: {e}")

def authenticate_user(username, password):
    """Authenticate a user and return user data if successful."""
    try:
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, username, password_hash, role, full_name, email, is_active
            FROM users WHERE username = ?
        ''', (username,))
        user = cursor.fetchone()
        conn.close()
        
        if user and user[6] == 1:  # is_active
            if verify_password(password, user[2]):
                return {
                    'id': user[0],
                    'username': user[1],
                    'role': user[3],
                    'full_name': user[4],
                    'email': user[5]
                }
        return None
    except Exception as e:
        print(f"Error authenticating user: {e}")
        return None

def update_last_login(user_id):
    """Update the last login time for a user."""
    try:
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE users SET last_login = ? WHERE id = ?
        ''', (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), user_id))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error updating last login: {e}")

def create_session(user_id):
    """Create a new session for a user."""
    try:
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO user_sessions (user_id, login_time)
            VALUES (?, ?)
        ''', (user_id, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        session_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return session_id
    except Exception as e:
        print(f"Error creating session: {e}")
        return None

def close_session(session_id, user_id):
    """Close a user session."""
    try:
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        
        # Get login time
        cursor.execute('SELECT login_time FROM user_sessions WHERE id = ?', (session_id,))
        result = cursor.fetchone()
        if result:
            login_time = datetime.strptime(result[0], '%Y-%m-%d %H:%M:%S')
            logout_time = datetime.now()
            duration = int((logout_time - login_time).total_seconds() / 60)  # in minutes
            
            cursor.execute('''
                UPDATE user_sessions 
                SET logout_time = ?, session_duration = ?
                WHERE id = ?
            ''', (logout_time.strftime('%Y-%m-%d %H:%M:%S'), duration, session_id))
            conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error closing session: {e}")

def check_prediction_quota(user_id, role):
    """Check if user has remaining prediction quota."""
    if role in ['Admin', 'Data Analyst']:
        return True, -1  # Unlimited
    
    try:
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        
        # Get quota setting
        cursor.execute("SELECT setting_value FROM system_settings WHERE setting_key = 'standard_user_daily_quota'")
        quota = int(cursor.fetchone()[0])
        
        # Get user's prediction count
        cursor.execute('''
            SELECT daily_prediction_count, last_prediction_date FROM users WHERE id = ?
        ''', (user_id,))
        result = cursor.fetchone()
        
        if result:
            count, last_date = result
            today = datetime.now().strftime('%Y-%m-%d')
            
            # Reset count if it's a new day
            if last_date != today:
                count = 0
                cursor.execute('''
                    UPDATE users SET daily_prediction_count = 0, last_prediction_date = ?
                    WHERE id = ?
                ''', (today, user_id))
                conn.commit()
            
            conn.close()
            remaining = quota - count
            return remaining > 0, remaining
        
        conn.close()
        return True, quota
    except Exception as e:
        print(f"Error checking quota: {e}")
        return True, 0

def increment_prediction_count(user_id):
    """Increment the user's daily prediction count."""
    try:
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        today = datetime.now().strftime('%Y-%m-%d')
        cursor.execute('''
            UPDATE users 
            SET daily_prediction_count = daily_prediction_count + 1,
                last_prediction_date = ?
            WHERE id = ?
        ''', (today, user_id))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error incrementing prediction count: {e}")

def save_prediction_history(user_id, username, location, predicted_crimes):
    """Save prediction to history."""
    try:
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO prediction_history (user_id, username, location, prediction_date, predicted_crimes, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, username, location, datetime.now().strftime('%Y-%m-%d'),
              ', '.join(predicted_crimes), datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error saving prediction history: {e}")

def save_generated_report(user_id, username, report_type, location, file_path):
    """Save generated report information."""
    try:
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO generated_reports (user_id, username, report_type, location, file_path, generation_date)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, username, report_type, location, file_path, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error saving report: {e}")

# =====================================================================
# 5. SPLASH SCREEN (KEPT BUT BYPASSED IN DEPLOYED VERSION)
# =====================================================================

class SplashScreen(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ZRP System")
        self.setFixedSize(600, 400)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #0f2027, stop:1 #2c5364);
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Logo/Title
        title = QLabel("🏛️ ZIMBABWE REPUBLIC POLICE")
        title.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 28px;
                font-weight: bold;
                font-family: 'Arial Black', sans-serif;
            }
        """)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        subtitle = QLabel("AI Crime Pattern Prediction System")
        subtitle.setStyleSheet("""
            QLabel {
                color: rgba(255, 255, 255, 0.8);
                font-size: 18px;
                font-weight: 500;
                margin-top: 10px;
            }
        """)
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Loading indicator
        self.loading_label = QLabel("Initializing System Components...")
        self.loading_label.setStyleSheet("""
            QLabel {
                color: rgba(255, 255, 255, 0.7);
                font-size: 14px;
                margin-top: 30px;
            }
        """)
        self.loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Progress bar
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setTextVisible(False)
        self.progress.setFixedWidth(300)
        self.progress.setFixedHeight(8)
        self.progress.setStyleSheet("""
            QProgressBar {
                background-color: rgba(255, 255, 255, 0.1);
                border-radius: 4px;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
                border-radius: 4px;
            }
        """)
        
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addStretch()
        layout.addWidget(self.loading_label)
        layout.addWidget(self.progress)
        layout.addStretch()
        
        # Footer
        footer = QLabel("© 2026 ZRP Digital Transformation Initiative")
        footer.setStyleSheet("""
            QLabel {
                color: rgba(255, 255, 255, 0.5);
                font-size: 27x;
            }
        """)
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(footer)
        
        # Animate progress
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_progress)
        self.timer.start(50)
        self.progress_value = 0
        
    def update_progress(self):
        self.progress_value += 1
        self.progress.setValue(self.progress_value)
        
        if self.progress_value == 30:
            self.loading_label.setText("Loading Crime Database...")
        elif self.progress_value == 60:
            self.loading_label.setText("Training AI Models...")
        elif self.progress_value == 90:
            self.loading_label.setText("Starting Security Protocols...")
        elif self.progress_value >= 100:
            self.timer.stop()
            self.close()

# =====================================================================
# 6. ENHANCED LOGIN DIALOG
# =====================================================================

class LoginDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ZRP Crime Prediction System - Secure Login")
        self.setModal(True)
        self.setFixedSize(600, 700)
        self.user_data = None
        
        # Apply modern styling
        self.setStyleSheet("""
            QDialog {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #1a2980, stop:1 #26d0ce);
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QLabel {
                color: white;
                font-size: 14px;
                font-weight: 500;
            }
            QLineEdit {
                background-color: rgba(255, 255, 255, 0.9);
                border: 2px solid rgba(255, 255, 255, 0.3);
                border-radius: 8px;
                padding: 12px;
                font-size: 14px;
                color: #333;
                min-height: 25px;
            }
            QLineEdit:focus {
                border: 2px solid #4CAF50;
                background-color: white;
            }
            QPushButton {
                background-color: rgba(76, 175, 80, 0.9);
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 24px;
                font-size: 14px;
                font-weight: 600;
                min-height: 40px;
            }
            QPushButton:hover {
                background-color: rgba(76, 175, 80, 1);
            }
            QPushButton:pressed {
                background-color: rgba(56, 142, 60, 1);
            }
            QLabel#header {
                font-size: 24px;
                font-weight: bold;
                color: white;
                padding: 10px;
            }
            QLabel#subheader {
                font-size: 16px;
                color: rgba(255, 255, 255, 0.8);
                padding: 5px;
            }
            QFrame#formFrame {
                background-color: rgba(255, 255, 255, 0.1);
                border-radius: 12px;
                border: 1px solid rgba(255, 255, 255, 0.2);
            }
        """)

        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(30, 30, 30, 30)

        # Header section
        header_layout = QVBoxLayout()
        header_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Logo/Title
        header_label = QLabel("🔒 ZRP AI CRIME PREDICTION SYSTEM")
        header_label.setObjectName("header")
        header_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        subheader_label = QLabel("Secure Access Portal v2.0")
        subheader_label.setObjectName("subheader")
        subheader_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        header_layout.addWidget(header_label)
        header_layout.addWidget(subheader_label)
        main_layout.addLayout(header_layout)

        # Form frame with subtle background
        form_frame = QFrame()
        form_frame.setObjectName("formFrame")
        form_layout = QVBoxLayout(form_frame)
        form_layout.setSpacing(15)
        form_layout.setContentsMargins(25, 25, 25, 25)

        # Username field
        username_layout = QVBoxLayout()
        username_label = QLabel("USERNAME")
        username_label.setStyleSheet("font-weight: bold;")
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Enter your username")
        self.username_input.setMinimumHeight(40)
        username_layout.addWidget(username_label)
        username_layout.addWidget(self.username_input)

        # Password field
        password_layout = QVBoxLayout()
        password_label = QLabel("PASSWORD")
        password_label.setStyleSheet("font-weight: bold;")
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setPlaceholderText("Enter your password")
        self.password_input.setMinimumHeight(40)
        password_layout.addWidget(password_label)
        password_layout.addWidget(self.password_input)

        form_layout.addLayout(username_layout)
        form_layout.addLayout(password_layout)
        main_layout.addWidget(form_frame)

        # Button section
        button_layout = QVBoxLayout()
        button_layout.setSpacing(10)

        # Login button
        self.login_button = QPushButton("🚀 LOGIN TO SYSTEM")
        self.login_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.login_button.clicked.connect(self.login)
        self.login_button.setMinimumHeight(45)

        # Default credentials hint
        hint_label = QLabel("Default: admin, analyst, user")
        hint_label.setStyleSheet("color: rgba(255, 255, 255, 0.7); font-size: 12px; font-style: italic;")
        hint_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        button_layout.addWidget(self.login_button)
        button_layout.addWidget(hint_label)
        main_layout.addLayout(button_layout)

        # Footer
        footer_label = QLabel("© 2026 Zimbabwe Republic Police - AI Crime Prediction Division")
        footer_label.setStyleSheet("color: rgba(255, 255, 255, 0.6); font-size: 18px;")
        footer_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(footer_label)

        # Set Enter key to trigger login
        self.username_input.returnPressed.connect(self.login)
        self.password_input.returnPressed.connect(self.login)

        # Add shadow effect
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(25)
        shadow.setColor(Qt.GlobalColor.black)
        shadow.setOffset(0, 5)
        self.setGraphicsEffect(shadow)

    def login(self):
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()

        if not username or not password:
            self.show_error_message("Input Required", "Please enter both username and password.")
            return

        # Add loading animation
        self.login_button.setText("🔐 AUTHENTICATING...")
        self.login_button.setEnabled(False)
        QApplication.processEvents()

        # Authenticate using database
        user = authenticate_user(username, password)
        
        if user:
            self.user_data = user
            update_last_login(user['id'])
            log_audit(user['id'], user['username'], "Login", f"User logged in as {user['role']}")
            
            # Success animation
            self.login_button.setText("✅ LOGIN SUCCESSFUL!")
            self.login_button.setStyleSheet("""
                QPushButton {
                    background-color: #4CAF50;
                    color: white;
                    border: none;
                    border-radius: 8px;
                    padding: 12px 24px;
                    font-size: 14px;
                    font-weight: 600;
                }
            """)
            QTimer.singleShot(500, self.accept)
        else:
            self.login_button.setText("🚀 LOGIN TO SYSTEM")
            self.login_button.setEnabled(True)
            self.show_error_message("Login Failed", 
                "Invalid credentials or account inactive.\n\n"
                "Please check your username and password.")

    def show_error_message(self, title, message):
        """Show a styled error message"""
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.setIcon(QMessageBox.Icon.Warning)
        msg_box.setStyleSheet("""
            QMessageBox {
                background-color: #f8f9fa;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QMessageBox QLabel {
                color: #333;
                font-size: 14px;
            }
            QMessageBox QPushButton {
                background-color: #dc3545;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 20px;
                font-size: 13px;
                font-weight: 500;
            }
            QMessageBox QPushButton:hover {
                background-color: #c82333;
            }
        """)
        msg_box.exec()

    def keyPressEvent(self, event):
        """Handle Escape key to close dialog"""
        if event.key() == Qt.Key.Key_Escape:
            self.reject()
        else:
            super().keyPressEvent(event)

# =====================================================================
# 7. MAIN APPLICATION WINDOW
# =====================================================================

# Global variables for models and data
rf_model_global = None
kmeans_model_global = None
df_global = None
le_crime = None
le_location = None

class ZRPPredictionApp(QMainWindow):
    def __init__(self, user_data):
        super().__init__()
        self.user_data = user_data
        self.role = user_data['role']
        self.session_id = None
        
        # Create session for non-guest users
        if user_data['id'] is not None:
            self.session_id = create_session(user_data['id'])
        
        self.setWindowTitle(f"ZRP Proactive Crime Pattern Prediction System - {self.user_data['full_name']} ({self.role})")
        self.setGeometry(100, 100, 1200, 800)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.main_layout = QHBoxLayout(self.central_widget)

        # Left side: Controls and Prediction Output
        self.control_panel = QWidget()
        self.control_panel.setFixedWidth(400)
        self.control_layout = QVBoxLayout(self.control_panel)
        self.control_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.main_layout.addWidget(self.control_panel)

        # Right side: Map Visualization
        self.map_view = QWebEngineView()

        # Create right panel with vertical layout for map
        self.right_panel = QWidget()
        self.right_layout = QVBoxLayout(self.right_panel)
        self.right_layout.setContentsMargins(0, 0, 0, 0)
        self.right_panel.setContentsMargins(0, 0, 0, 0)
        self.right_layout.addWidget(self.map_view)

        self.main_layout.addWidget(self.right_panel, 1)

        self.initialize_ui()
        self.load_and_train_data()

    def initialize_ui(self):
        
        # --- Header ---
        header_label = QLabel("AI CRIME PATTERN PREDICTION FOR POLICE")
        header_label.setStyleSheet("font-size: 18pt; font-weight: bold; color: navy;")
        self.control_layout.addWidget(header_label)
        self.control_layout.addWidget(QLabel("---"))
        
        # --- Prediction Inputs (Grid Layout) ---
        input_group = QWidget()
        input_grid = QGridLayout(input_group)
        
        # Location Input
        input_grid.addWidget(QLabel("Target Location:"), 0, 0)
        self.location_input = QComboBox()
        locations = [loc for loc in LOCATION_CENTERS.keys() if loc != 'DEFAULT']
        self.location_input.addItems(locations)
        self.location_input.setCurrentText("HARARE")
        input_grid.addWidget(self.location_input, 0, 1)

        # Date/Time Input
        input_grid.addWidget(QLabel("Date & Time:"), 1, 0)
        self.datetime_input = QDateTimeEdit(QDateTime.currentDateTime())
        self.datetime_input.setCalendarPopup(True)
        self.datetime_input.setDisplayFormat("yyyy-MM-dd HH:mm")
        input_grid.addWidget(self.datetime_input, 1, 1)

        # Predict Button
        self.predict_button = QPushButton("Predict Crime Pattern")
        self.predict_button.setStyleSheet("background-color: darkgreen; color: white; font-weight: bold;")
        self.predict_button.clicked.connect(self.run_prediction)
        input_grid.addWidget(self.predict_button, 2, 0, 1, 2)

        # Plot Predicted Crimes Button
        self.plot_button = QPushButton("Plot Predicted Crimes on Map")
        self.plot_button.setStyleSheet("background-color: darkblue; color: white; font-weight: bold;")
        self.plot_button.clicked.connect(self.plot_predicted_crimes)
        input_grid.addWidget(self.plot_button, 3, 0, 1, 2)
        
        self.control_layout.addWidget(input_group)
        self.control_layout.addWidget(QLabel("---"))
        
        # --- Prediction Output (Text Area) ---
        output_label = QLabel("Tactical Intelligence Report:")
        output_label.setStyleSheet("font-weight: bold;")
        self.control_layout.addWidget(output_label)
        
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setFixedHeight(200)
        self.control_layout.addWidget(self.output_text)
        
        # --- Legend ---
        legend_label = QLabel("Crime Type Key:")
        legend_label.setStyleSheet("font-weight: bold;")
        self.control_layout.addWidget(legend_label)

        legend_text = ""
        for crime, color in CRIME_COLORS.items():
            legend_text += f'<span style="color:{color}; font-weight:bold;">■</span> {crime}<br>'
        self.legend_display = QLabel(legend_text)
        self.legend_display.setTextFormat(Qt.TextFormat.RichText)
        self.legend_display.setStyleSheet("font-size: 10pt; border: 1px solid gray; padding: 5px;")
        self.control_layout.addWidget(self.legend_display)

        # --- Map Status and Report Button ---
        self.map_status_label = QLabel("Map Status: Loading...")
        self.map_status_label.setStyleSheet("font-size: 10pt; color: orange;")
        self.control_layout.addWidget(self.map_status_label)

        self.report_button = QPushButton("Generate PDF Report")
        self.report_button.setStyleSheet("background-color: darkred; color: white;")
        self.report_button.clicked.connect(self.generate_report)
        self.control_layout.addWidget(self.report_button)

        self.anticipated_report_button = QPushButton("Generate Anticipated Crimes Report")
        self.anticipated_report_button.setStyleSheet("background-color: darkorange; color: white;")
        self.anticipated_report_button.clicked.connect(self.generate_anticipated_report)
        self.control_layout.addWidget(self.anticipated_report_button)

        # Bottom buttons layout (Refresh and Exit)
        bottom_buttons_layout = QHBoxLayout()
        bottom_buttons_layout.setAlignment(Qt.AlignmentFlag.AlignRight)

        self.refresh_button = QPushButton("Refresh Map")
        self.refresh_button.setStyleSheet("background-color: lightblue; color: black;")
        self.refresh_button.clicked.connect(self.refresh_map)
        bottom_buttons_layout.addWidget(self.refresh_button)

        self.exit_button = QPushButton("Exit")
        self.exit_button.setStyleSheet("background-color: red; color: white;")
        self.exit_button.clicked.connect(self.exit_app)
        bottom_buttons_layout.addWidget(self.exit_button)

        self.control_layout.addLayout(bottom_buttons_layout)

        # Role-based access control
        self.apply_role_permissions()

    def apply_role_permissions(self):
        """Applies role-based access control to UI elements."""
        if self.role == 'Guest':
            # Disable all buttons except Refresh and Exit
            self.predict_button.setEnabled(False)
            self.plot_button.setEnabled(False)
            self.report_button.setEnabled(False)
            self.anticipated_report_button.setEnabled(False)
            # Refresh and Exit are enabled by default
        else:
            # Admin, Data Analyst, Standard User: all enabled
            self.predict_button.setEnabled(True)
            self.plot_button.setEnabled(True)
            self.report_button.setEnabled(True)
            self.anticipated_report_button.setEnabled(True)

    def load_and_train_data(self):
        """Initial data setup and model training."""
        global df_global, rf_model_global, kmeans_model_global, le_crime, le_location

        # 1. Prepare and Save Data
        df_temp = pd.read_csv(StringIO(PROVIDED_CSV_DATA))
        df_global, le_crime, le_location, _ = prepare_data(df_temp)
        
        if initialize_database(df_global):
            self.map_status_label.setText("Data Status: Loaded (500 Records)")
            self.map_status_label.setStyleSheet("font-size: 10pt; color: green;")
        else:
            self.map_status_label.setText("Data Status: Error Loading Database!")
            self.map_status_label.setStyleSheet("font-size: 10pt; color: red;")
            return

        # 2. Train Models
        rf_model_global, kmeans_model_global = train_ai_model(df_global)
        
        # 3. Initial Map Load
        self.load_map()

    def load_map(self):
        """Generates and displays the hotspot map."""
        map_html = generate_hotspot_map(df_global, kmeans_model_global)
        # Load the HTML string directly into the QWebEngineView
        self.map_view.setHtml(map_html)
        self.map_status_label.setText("Map Status: Hotspot Visualization Ready.")
        self.map_status_label.setStyleSheet("font-size: 10pt; color: blue;")


    def run_prediction(self):
        """Handles the user request to predict the crime pattern."""
        if df_global is None:
            QMessageBox.critical(self, "Error", "Data not loaded. Check console for data loading errors.")
            return

        # Check prediction quota for non-guest users
        if self.user_data['id'] is not None:
            can_predict, remaining = check_prediction_quota(self.user_data['id'], self.role)
            if not can_predict:
                QMessageBox.warning(self, "Quota Exceeded", 
                    f"You have reached your daily prediction limit.\nStandard Users are limited to {remaining + 1} predictions per day.\nPlease try again tomorrow or contact an administrator.")
                return
            
            # Show remaining predictions for Standard Users
            if self.role == 'Standard User' and remaining >= 0:
                self.map_status_label.setText(f"Predictions Remaining Today: {remaining}")
                self.map_status_label.setStyleSheet("font-size: 10pt; color: orange;")

        location_name = self.location_input.currentText()
        target_datetime = self.datetime_input.dateTime()

        predicted_crimes, predicted_mo, anticipated_crimes = predict_crime_pattern(rf_model_global, le_crime, le_location, df_global, location_name, target_datetime)
        
        # Increment prediction count and save to history for non-guest users
        if self.user_data['id'] is not None:
            increment_prediction_count(self.user_data['id'])
            save_prediction_history(self.user_data['id'], self.user_data['username'], location_name, predicted_crimes)
            log_audit(self.user_data['id'], self.user_data['username'], "Prediction", 
                     f"Generated prediction for {location_name}")

        # Get Location Risk
        loc_key = location_name.upper()
        loc_risk = LOCATION_CENTERS.get(loc_key, LOCATION_CENTERS['DEFAULT'])['risk']

        # Get user location
        user_location = LOCATION_CENTERS.get(loc_key, LOCATION_CENTERS['DEFAULT'])
        user_location['name'] = location_name.upper()

        # Retrieve nearby stations
        nearby_stations = get_nearby_stations(loc_key, user_location['lat'], user_location['lon'])

        # Find Hotspot Cluster
        try:
            loc_data = df_global[df_global['Location'].str.contains(loc_key, case=False, na=False)].iloc[0]
            cluster_id = loc_data['Cluster_ID']
            hotspot = HOTSPOT_NAMES.get(cluster_id, "Unknown Hotspot")
        except:
            hotspot = "No local cluster found"

        # Build nearby stations section
        stations_text = " - ".join([station['name'] for station in nearby_stations])

        # Store variables for PDF generation
        self.location_name = location_name
        self.target_datetime = target_datetime
        self.loc_risk = loc_risk
        self.hotspot = hotspot
        self.predicted_crimes = predicted_crimes
        self.predicted_mo = predicted_mo
        self.stations_text = stations_text
        self.anticipated_crimes = anticipated_crimes

        # Format anticipated crimes for report
        anticipated_text = ""
        for i, (crime, dt, mo) in enumerate(anticipated_crimes, 1):
            anticipated_text += f"{i}. {crime} - Anticipated: {dt.strftime('%Y-%m-%d %H:%M')}, M.O.: {mo}\n"

        report = f"""
        --- TACTICAL CRIME PREDICTION ---

        TARGET AREA: {location_name.upper()}
        PREDICTION PERIOD: Next 72 Hours Starting {target_datetime.toString("yyyy-MM-dd hh:mm AP")}

        RISK ASSESSMENT: {loc_risk}
        HOTSPOT CLUSTER: {hotspot}

        --- PREDICTED THREATS ---

        1. TOP LIKELY CRIME: {predicted_crimes[0]}
           MODUS OPERANDI (M.O.): {predicted_mo}
           ANTICIPATED: {anticipated_crimes[0][1].strftime('%Y-%m-%d %H:%M')}

        2. SECONDARY THREAT: {predicted_crimes[1]}
           ANTICIPATED: {anticipated_crimes[1][1].strftime('%Y-%m-%d %H:%M')}

        3. TERTIARY THREAT: {predicted_crimes[2]}
           ANTICIPATED: {anticipated_crimes[2][1].strftime('%Y-%m-%d %H:%M')}

        --- NEARBY ZRP STATIONS ---
        {stations_text}

        --- ACTIONABLE INTELLIGENCE ---

        The primary threat in {location_name.upper()} is {predicted_crimes[0]}, with a risk assessment of {loc_risk}.
        This crime is likely to occur using the modus operandi of "{predicted_mo}", based on historical patterns.
        Patrols should prioritize interdiction in the {hotspot} hotspot cluster, focusing on high-density areas.
        Nearby ZRP stations are available for rapid response, including {stations_text}.
        Intelligence recommends increased surveillance during the next 72 hours starting {target_datetime.toString("yyyy-MM-dd hh:mm AP")}.
        Secondary threats include {predicted_crimes[1]} and {predicted_crimes[2]}, which should also be monitored.
        Overall, proactive measures in {location_name.upper()} can mitigate these risks effectively.

        --- ANTICIPATED CRIME TIMELINES ---
        {anticipated_text.strip()}
        """
        self.output_text.setPlainText(report.strip())

        # Regenerate map with user location and nearby stations
        map_html = generate_hotspot_map(df_global, kmeans_model_global, user_location, nearby_stations)
        self.map_view.setHtml(map_html)
        self.map_status_label.setText("Map Status: Updated with User Location and Nearby Stations.")
        self.map_status_label.setStyleSheet("font-size: 10pt; color: blue;")

    def plot_predicted_crimes(self):
        """Handles plotting the predicted crimes on the map."""
        if not hasattr(self, 'anticipated_crimes') or not self.anticipated_crimes:
            QMessageBox.warning(self, "Warning", "Please run a prediction first to plot crimes.")
            return

        # Get user location
        loc_key = self.location_name.upper()
        user_location = LOCATION_CENTERS.get(loc_key, LOCATION_CENTERS['DEFAULT']).copy()
        user_location['name'] = loc_key

        # Retrieve nearby stations
        nearby_stations = get_nearby_stations(loc_key, user_location['lat'], user_location['lon'])

        # Generate map with anticipated crimes
        map_html = generate_hotspot_map(df_global, kmeans_model_global, user_location, nearby_stations, self.anticipated_crimes)
        self.map_view.setHtml(map_html)
        self.map_status_label.setText("Map Status: Updated with Anticipated Crimes Plotted.")
        self.map_status_label.setStyleSheet("font-size: 10pt; color: green;")

    def generate_report(self):
        """Generates a PDF report of the current prediction and map."""
        if not hasattr(self, 'predicted_crimes'):
            QMessageBox.warning(self, "Warning", "Please run a prediction first to generate a report.")
            return

        # Use the specified format for the report
        report_text = f"""TACTICAL CRIME PREDICTION
TARGET AREA: {self.location_name.upper()}
PREDICTION PERIOD: Next 72 Hours Starting {self.target_datetime.toString("yyyy-MM-dd hh:mm AP")}
RISK ASSESSMENT: {self.loc_risk} HOTSPOT CLUSTER: {self.hotspot}
PREDICTED THREATS
1. TOP LIKELY CRIME: {self.predicted_crimes[0]} MODUS OPERANDI (M.O.): {self.predicted_mo}
2. SECONDARY THREAT: {self.predicted_crimes[1]}
3. TERTIARY THREAT: {self.predicted_crimes[2]}
 NEARBY ZRP STATIONS --- {self.stations_text}
ACTIONABLE INTELLIGENCE
The primary threat in {self.location_name.upper()} is {self.predicted_crimes[0]}, with a risk assessment of {self.loc_risk}. This crime is likely to occur using the modus operandi of "{self.predicted_mo}", based on historical patterns.
Patrols should prioritize interdiction in the {self.hotspot} hotspot cluster, focusing on high-density areas. Nearby ZRP stations are available for rapid response, including {self.stations_text}.
Intelligence recommends increased surveillance during the next 72 hours starting {self.target_datetime.toString("yyyy-MM-dd hh:mm AP")}. Secondary threats include {self.predicted_crimes[1]} and {self.predicted_crimes[2]}, which should also be monitored. Overall, proactive measures in {self.location_name.upper()} can mitigate these risks effectively."""

        # Add anticipated crimes section
        if hasattr(self, 'anticipated_crimes') and self.anticipated_crimes:
            anticipated_text = "\n\n--- ANTICIPATED CRIME TIMELINES ---\n"
            for i, (crime, dt, mo) in enumerate(self.anticipated_crimes, 1):
                anticipated_text += f"{i}. {crime} - Anticipated: {dt.strftime('%Y-%m-%d %H:%M')}, M.O.: {mo}\n"
            report_text += anticipated_text.strip()

        # Compute top 5 most common crimes for the entered location
        if df_global is not None and not df_global.empty:
            loc_key = self.location_name.upper()
            df_loc = df_global[df_global['Location'].str.contains(loc_key, case=False, na=False)]
            if not df_loc.empty:
                top_crimes = df_loc['Crime Type'].value_counts().head(5)
                top_crimes_str = "\n".join([f"{i+1}. {crime}: {count} cases" for i, (crime, count) in enumerate(top_crimes.items())])
                top_crimes_section = f"\n\n--- TOP 5 MOST COMMON CRIMES (in {loc_key}) ---\n{top_crimes_str}"
            else:
                top_crimes_section = f"\n\n--- TOP 5 MOST COMMON CRIMES (in {loc_key}) ---\nNo data available for this location."
            report_text += top_crimes_section
        else:
            report_text += "\n\n--- TOP 5 MOST COMMON CRIMES ---\nData not available."

        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Courier", "B", 16)
        pdf.cell(0, 10, "AI CRIME PATTERN PREDICTION FOR POLICE", 0, 1, "C")
        pdf.set_font("Courier", "", 12)
        pdf.multi_cell(0, 8, f"Report Generated: {QDateTime.currentDateTime().toString('yyyy-MM-dd hh:mm:ss')}", 0, "L")
        pdf.ln(5)

        pdf.ln(10)

        pdf.set_font("Courier", "", 10)
        # Add the prediction text
        pdf.multi_cell(0, 5, report_text)

        # Determine the save path with auto-increment
        downloads_dir = os.path.join(os.path.expanduser("~"), "Downloads")
        base_name = "ZRP_Tactical_Report.pdf"
        pdf_path = os.path.join(downloads_dir, base_name)
        counter = 1
        while os.path.exists(pdf_path):
            name, ext = os.path.splitext(base_name)
            pdf_path = os.path.join(downloads_dir, f"{name}_{counter}{ext}")
            counter += 1

        pdf.output(pdf_path)
        filename = os.path.basename(pdf_path)
        
        # Save report to database for non-guest users
        if self.user_data['id'] is not None:
            save_generated_report(self.user_data['id'], self.user_data['username'], 
                                 "Tactical Report", self.location_name, pdf_path)
            log_audit(self.user_data['id'], self.user_data['username'], "Report Generated", 
                     f"Generated tactical report for {self.location_name}")

        QMessageBox.information(self, "Report Generated", f"Tactical Report saved to Downloads folder as {filename}")

    def generate_anticipated_report(self):
        """Generates a separate PDF report focused on anticipated crimes."""
        if not hasattr(self, 'anticipated_crimes') or not self.anticipated_crimes:
            QMessageBox.warning(self, "Warning", "No anticipated crimes data available. Please run a prediction first.")
            return

        # Build the report text focused on anticipated crimes
        report_text = f"""ANTICIPATED CRIMES REPORT
TARGET AREA: {self.location_name.upper()}
PREDICTION PERIOD: Next 72 Hours Starting {self.target_datetime.toString("yyyy-MM-dd hh:mm AP")}
RISK ASSESSMENT: {self.loc_risk}
HOTSPOT CLUSTER: {self.hotspot}

--- ANTICIPATED CRIME TIMELINES ---
"""
        for i, (crime, dt, mo) in enumerate(self.anticipated_crimes, 1):
            report_text += f"{i}. Crime: {crime}\n   Anticipated Date/Time: {dt.strftime('%Y-%m-%d %H:%M')}\n   Modus Operandi: {mo}\n\n"

        report_text += f"""--- ACTIONABLE INTELLIGENCE ---
Based on AI predictions, the following crimes are anticipated in {self.location_name.upper()} within the next 72 hours.
Prioritize patrols and surveillance around the predicted times to prevent these incidents.
Nearby ZRP Stations: {self.stations_text}
"""

        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Courier", "B", 16)
        pdf.cell(0, 10, "AI CRIME PATTERN PREDICTION FOR POLICE - ANTICIPATED CRIMES", 0, 1, "C")
        pdf.set_font("Courier", "", 12)
        pdf.multi_cell(0, 8, f"Report Generated: {QDateTime.currentDateTime().toString('yyyy-MM-dd hh:mm:ss')}", 0, "L")
        pdf.ln(5)

        pdf.ln(10)

        pdf.set_font("Courier", "", 10)
        # Add the anticipated crimes text
        pdf.multi_cell(0, 5, report_text)

        # Determine the save path with auto-increment
        downloads_dir = os.path.join(os.path.expanduser("~"), "Downloads")
        base_name = "ZRP_Anticipated_Crimes_Report.pdf"
        pdf_path = os.path.join(downloads_dir, base_name)
        counter = 1
        while os.path.exists(pdf_path):
            name, ext = os.path.splitext(base_name)
            pdf_path = os.path.join(downloads_dir, f"{name}_{counter}{ext}")
            counter += 1

        pdf.output(pdf_path)
        filename = os.path.basename(pdf_path)
        
        # Save report to database for non-guest users
        if self.user_data['id'] is not None:
            save_generated_report(self.user_data['id'], self.user_data['username'], 
                                 "Anticipated Crimes Report", self.location_name, pdf_path)
            log_audit(self.user_data['id'], self.user_data['username'], "Report Generated", 
                     f"Generated anticipated crimes report for {self.location_name}")

        QMessageBox.information(self, "Anticipated Crimes Report Generated", f"Report saved to Downloads folder as {filename}")

    def refresh_map(self):
        """Refreshes the map to the initial hotspot visualization."""
        self.load_map()

    def exit_app(self):
        """Exits the application."""
        # Close session and log logout for non-guest users
        if self.user_data['id'] is not None and self.session_id is not None:
            close_session(self.session_id, self.user_data['id'])
            log_audit(self.user_data['id'], self.user_data['username'], "Logout", "User logged out")
        self.close()


# =====================================================================
# 8. MAIN EXECUTION
# =====================================================================

if __name__ == '__main__':
    # Initial data preparation and model training
    df_temp = pd.read_csv(StringIO(PROVIDED_CSV_DATA))
    df_global, le_crime, le_location, _ = prepare_data(df_temp)
    initialize_database(df_global)
    initialize_user_database()  # Initialize user management tables
    rf_model_global, kmeans_model_global = train_ai_model(df_global)

    # Start the QApplication
    app = QApplication(sys.argv)
    
    # --- SPLASH SCREEN SKIPPED IN DEPLOYED VERSION ---
    # The splash screen code is commented out so the login dialog appears immediately.
    # Uncomment the following lines if you want the splash screen back.
    #
    # splash = SplashScreen()
    # splash.show()
    # QApplication.processEvents()
    # time.sleep(2)
    # splash.close()
    
    # Show login dialog directly
    login_dialog = LoginDialog()
    if login_dialog.exec() == QDialog.DialogCode.Accepted:
        user_data = login_dialog.user_data
        window = ZRPPredictionApp(user_data)
        window.show()
        sys.exit(app.exec())
    else:
        # User canceled login
        sys.exit()