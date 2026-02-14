#!/usr/bin/env python3
"""
Test script for track.py core functionalities.
Tests data loading, model training, predictions, and error handling.
"""
import sys
import os
import pandas as pd
from io import StringIO
import numpy as np
from sklearn.metrics import accuracy_score, classification_report

# Import functions from track.py (assuming it's in the same directory)
sys.path.append(os.path.dirname(__file__))
import track
from track import (
    PROVIDED_CSV_DATA, generate_remaining_data, prepare_data,
    initialize_database, load_data, train_ai_model, predict_crime_pattern,
    generate_hotspot_map, get_nearby_stations
)

def test_data_loading():
    """Test data loading and preparation."""
    print("Testing data loading...")
    df_temp = pd.read_csv(StringIO(PROVIDED_CSV_DATA))
    df, le_crime, le_location, le_mo = prepare_data(df_temp)

    assert len(df) == 500, f"Expected 500 records, got {len(df)}"
    assert 'Modus Operandi' in df.columns, "Modus Operandi column missing"
    assert 'Crime_Code' in df.columns, "Crime_Code column missing"
    print("PASS: Data loading and preparation passed")

    return df, le_crime, le_location, le_mo

def test_database_operations(df):
    """Test database initialization and loading."""
    print("Testing database operations...")
    success = initialize_database(df)
    assert success, "Database initialization failed"

    df_loaded = load_data()
    assert not df_loaded.empty, "Loaded data is empty"
    assert len(df_loaded) == len(df), "Loaded data length mismatch"
    print("PASS: Database operations passed")

def test_model_training(df):
    """Test ML model training."""
    print("Testing model training...")
    rf_model, kmeans_model = train_ai_model(df)

    assert rf_model is not None, "RandomForest model not trained"
    assert kmeans_model is not None, "KMeans model not trained"
    assert hasattr(df, 'Cluster_ID'), "Cluster_ID not added to DataFrame"
    print("PASS: Model training passed")

    return rf_model, kmeans_model

def test_predictions(rf_model, le_crime, le_location, df):
    """Test crime predictions."""
    print("Testing predictions...")
    from PyQt6.QtCore import QDateTime, QDate, QTime

    # Test with HARARE
    target_datetime = QDateTime(QDate(2024, 10, 1), QTime(14, 0))
    predicted_crimes, predicted_mo = predict_crime_pattern(rf_model, le_crime, le_location, df, "HARARE", target_datetime)

    assert len(predicted_crimes) == 3, f"Expected 3 predictions, got {len(predicted_crimes)}"
    assert isinstance(predicted_mo, str), "Predicted MO is not a string"
    print(f"PASS: Predictions passed: Top crime - {predicted_crimes[0]}, MO - {predicted_mo}")

def test_map_generation(df, kmeans_model):
    """Test map HTML generation."""
    print("Testing map generation...")
    map_html = generate_hotspot_map(df, kmeans_model)

    assert isinstance(map_html, str), "Map HTML is not a string"
    assert "folium" in map_html.lower() or "leaflet" in map_html.lower(), "Map HTML seems invalid"
    print("PASS: Map generation passed")

    return map_html

def test_nearby_stations():
    """Test nearby stations retrieval."""
    print("Testing nearby stations...")
    stations = get_nearby_stations("HARARE")

    assert isinstance(stations, list), "Stations is not a list"
    assert len(stations) > 0, "No stations found for HARARE"
    assert "name" in stations[0], "Station missing name"
    print(f"PASS: Nearby stations passed: Found {len(stations)} stations")

def test_error_handling():
    """Test error handling for invalid inputs."""
    print("Testing error handling...")
    df_temp = pd.read_csv(StringIO(PROVIDED_CSV_DATA))
    df, le_crime, le_location, le_mo = prepare_data(df_temp)
    rf_model, kmeans_model = train_ai_model(df)

    # Test with invalid location
    from PyQt6.QtCore import QDateTime, QDate, QTime
    target_datetime = QDateTime(QDate(2024, 10, 1), QTime(14, 0))

    try:
        predicted_crimes, predicted_mo = predict_crime_pattern(rf_model, le_crime, le_location, df, "INVALID_LOCATION", target_datetime)
        # Should not crash, should default
        assert len(predicted_crimes) == 3, "Prediction failed for invalid location"
        print("PASS: Error handling passed: Invalid location handled gracefully")
    except Exception as e:
        print(f"✗ Error handling failed: {e}")
        raise

def test_model_accuracy(df, rf_model):
    """Test model accuracy on training data (for demo purposes)."""
    print("Testing model accuracy...")
    features_clf = ['Location_Code', 'DayOfWeek', 'Month', 'Hour']
    target_clf = 'Crime_Code'
    X = df[features_clf]
    y = df[target_clf]

    predictions = rf_model.predict(X)
    accuracy = accuracy_score(y, predictions)
    print(".2f")

    # Basic check: accuracy should be reasonable (>0.5 for demo)
    assert accuracy > 0.5, f"Accuracy too low: {accuracy}"
    print("PASS: Model accuracy passed")

def run_all_tests():
    """Run all tests."""
    print("Starting thorough testing of track.py...\n")

    try:
        df, le_crime, le_location, le_mo = test_data_loading()
        test_database_operations(df)
        rf_model, kmeans_model = test_model_training(df)
        test_predictions(rf_model, le_crime, le_location, df)
        map_html = test_map_generation(df, kmeans_model)
        test_nearby_stations()
        test_error_handling()
        test_model_accuracy(df, rf_model)

        print("\nSUCCESS: All tests passed! Core functionalities are working correctly.")
        return True, map_html

    except Exception as e:
        print(f"\nFAIL: Test failed: {e}")
        return False, None

if __name__ == "__main__":
    success, map_html = run_all_tests()
    if success:
        # Save map HTML for browser testing
        with open("test_map.html", "w") as f:
            f.write(map_html)
        print("Map HTML saved to test_map.html for further testing.")
