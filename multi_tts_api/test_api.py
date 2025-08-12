#!/usr/bin/env python3
"""
Test script for Multi-Backend TTS API

This script tests the API endpoints and various TTS backends.
"""

import requests
import json
import time
import sys
import os
import tempfile
import wave
import subprocess


def test_endpoint(url, method="GET", json_data=None, expected_status=200):
    """Test an API endpoint"""
    try:
        if method == "GET":
            response = requests.get(url, timeout=10)
        elif method == "POST":
            response = requests.post(url, json=json_data, timeout=30)
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        if response.status_code == expected_status:
            print(f"✓ {method} {url} - Status: {response.status_code}")
            return response
        else:
            print(f"✗ {method} {url} - Status: {response.status_code} (expected {expected_status})")
            print(f"  Response: {response.text[:200]}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"✗ {method} {url} - Error: {e}")
        return None


def verify_wav_file(wav_data):
    """Verify that the data is a valid WAV file"""
    try:
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
            tmp_file.write(wav_data)
            tmp_filename = tmp_file.name
        
        with wave.open(tmp_filename, 'rb') as wav_file:
            channels = wav_file.getnchannels()
            sample_width = wav_file.getsampwidth()
            framerate = wav_file.getframerate()
            n_frames = wav_file.getnframes()
            
            print(f"  WAV Info: {channels} channel(s), {framerate}Hz, {n_frames} frames")
            
            os.unlink(tmp_filename)
            return True
    except Exception as e:
        print(f"  Invalid WAV file: {e}")
        if 'tmp_filename' in locals():
            os.unlink(tmp_filename)
        return False


def main():
    # Check if server is running
    base_url = "http://localhost:8000"
    
    print("=" * 60)
    print("Multi-Backend TTS API Test Suite")
    print("=" * 60)
    print(f"Testing API at: {base_url}")
    print()
    
    # Test 1: Root endpoint
    print("1. Testing root endpoint...")
    response = test_endpoint(f"{base_url}/")
    if response:
        data = response.json()
        print(f"  API Title: {data.get('message', 'N/A')}")
    print()
    
    # Test 2: Health check
    print("2. Testing health check...")
    response = test_endpoint(f"{base_url}/health")
    if response:
        data = response.json()
        print(f"  Status: {data.get('status', 'N/A')}")
        print(f"  Available backends: {data.get('available_backends', 0)}")
    print()
    
    # Test 3: List backends
    print("3. Testing backend listing...")
    response = test_endpoint(f"{base_url}/backends")
    available_backends = []
    if response:
        data = response.json()
        available_backends = data.get('backends', [])
        print(f"  Found {len(available_backends)} backend(s): {', '.join(available_backends)}")
        
        for backend_id, info in data.get('details', {}).items():
            print(f"  - {backend_id}:")
            print(f"    Initialized: {info.get('initialized', False)}")
            print(f"    Available: {info.get('available', False)}")
            print(f"    Voices: {len(info.get('voices', []))}")
            print(f"    Languages: {', '.join(info.get('languages', []))[:50]}")
    print()
    
    # Test 4: Test synthesis with each available backend
    if available_backends:
        print("4. Testing speech synthesis with each backend...")
        test_text = "Hello, this is a test of the text to speech system."
        
        for backend_id in available_backends:
            print(f"\n  Testing {backend_id}...")
            
            # Get backend info
            response = test_endpoint(f"{base_url}/backends/{backend_id}")
            
            # Test synthesis
            tts_request = {
                "text": test_text,
                "backend": backend_id,
                "speed": 1.0,
                "pitch": 1.0,
                "format": "wav"
            }
            
            response = test_endpoint(
                f"{base_url}/synthesize",
                method="POST",
                json_data=tts_request
            )
            
            if response and response.status_code == 200:
                wav_data = response.content
                print(f"    Received {len(wav_data)} bytes")
                if verify_wav_file(wav_data):
                    print(f"    ✓ Valid WAV file generated")
                    
                    # Save sample file
                    sample_file = f"test_output_{backend_id}.wav"
                    with open(sample_file, 'wb') as f:
                        f.write(wav_data)
                    print(f"    Saved to: {sample_file}")
            
            # Test voices endpoint
            response = test_endpoint(f"{base_url}/voices/{backend_id}")
            if response:
                voices = response.json().get('voices', [])
                print(f"    Available voices: {len(voices)}")
                if voices and len(voices) > 0:
                    print(f"    Sample voice: {voices[0].get('id', 'N/A')}")
            
            # Test languages endpoint
            response = test_endpoint(f"{base_url}/languages/{backend_id}")
            if response:
                languages = response.json().get('languages', [])
                print(f"    Available languages: {len(languages)}")
                if languages:
                    print(f"    Sample languages: {', '.join(languages[:5])}")
    else:
        print("4. No backends available for synthesis testing")
        print("   Attempting to register eSpeak backend...")
        
        # Try to register eSpeak
        register_request = {
            "backend_id": "espeak",
            "config": {}
        }
        response = test_endpoint(
            f"{base_url}/backends/register",
            method="POST",
            json_data=register_request
        )
    
    print()
    
    # Test 5: Batch synthesis
    if available_backends:
        print("5. Testing batch synthesis...")
        backend = available_backends[0]
        batch_request = [
            {"text": "First text", "backend": backend, "format": "wav"},
            {"text": "Second text", "backend": backend, "format": "wav"}
        ]
        
        response = test_endpoint(
            f"{base_url}/synthesize/batch",
            method="POST",
            json_data=batch_request
        )
        
        if response:
            data = response.json()
            print(f"  Total: {data.get('total', 0)}")
            print(f"  Successful: {data.get('successful', 0)}")
            print(f"  Failed: {data.get('failed', 0)}")
    print()
    
    # Test 6: Stream synthesis
    if available_backends:
        print("6. Testing streaming synthesis...")
        backend = available_backends[0]
        stream_request = {
            "text": "Testing streaming audio output",
            "backend": backend,
            "format": "wav"
        }
        
        response = test_endpoint(
            f"{base_url}/synthesize/stream",
            method="POST",
            json_data=stream_request
        )
        
        if response and response.status_code == 200:
            print(f"  ✓ Streaming response received")
            print(f"  Content-Type: {response.headers.get('Content-Type', 'N/A')}")
    
    print()
    print("=" * 60)
    print("Test suite completed!")
    print("=" * 60)


if __name__ == "__main__":
    # Check if API server is running
    try:
        response = requests.get("http://localhost:8000/health", timeout=2)
    except requests.exceptions.RequestException:
        print("ERROR: API server is not running!")
        print("Please start the server first with:")
        print("  python run_server.py")
        sys.exit(1)
    
    main()