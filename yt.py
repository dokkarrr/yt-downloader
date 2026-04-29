name: YouTube Downloader CI/CD

on:
  push:
    branches: [ main, master ]
  pull_request:
    branches: [ main, master ]
  schedule:
    # Weekly test runs
    - cron: '0 0 * * 0'
  workflow_dispatch:
    # Manual trigger with inputs
    inputs:
      youtube_url:
        description: 'YouTube URL to download'
        required: false
        default: 'https://www.youtube.com/watch?v=dQw4w9WgXcQ'
      download_type:
        description: 'Type of download'
        required: true
        default: 'video'
        type: choice
        options:
          - video
          - audio
          - subs

jobs:
  test:
    strategy:
      matrix:
        os: [ubuntu-latest, macos-latest, windows-latest]
        python-version: ['3.8', '3.9', '3.10', '3.11']
    
    runs-on: ${{ matrix.os }}
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v4
    
    - name: Setup Python ${{ matrix.python-version }}
      uses: actions/setup-python@v5
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Cache pip packages
      uses: actions/cache@v3
      with:
        path: ~/.cache/pip
        key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements.txt') }}
        restore-keys: |
          ${{ runner.os }}-pip-
    
    - name: Install FFmpeg (Ubuntu)
      if: runner.os == 'Linux'
      run: sudo apt-get update && sudo apt-get install -y ffmpeg
    
    - name: Install FFmpeg (macOS)
      if: runner.os == 'macOS'
      run: brew install ffmpeg
    
    - name: Install FFmpeg (Windows)
      if: runner.os == 'Windows'
      run: |
        choco install ffmpeg -y
        echo "C:\ProgramData\chocolatey\bin" | Out-File -FilePath $env:GITHUB_PATH -Encoding utf8 -Append
    
    - name: Run tests
      run: python yt_downloader.py --test
      env:
        GITHUB_ACTIONS: true
    
    - name: Test download (Linux)
      if: runner.os == 'Linux' && github.event_name == 'workflow_dispatch'
      run: python yt_downloader.py --download "${{ github.event.inputs.youtube_url }}"
      env:
        GITHUB_ACTIONS: true
    
    - name: Upload artifacts
      if: always() && github.event_name == 'workflow_dispatch'
      uses: actions/upload-artifact@v4
      with:
        name: downloads-${{ runner.os }}
        path: /tmp/yt-downloads/**/*

  notify:
    needs: test
    if: always()
    runs-on: ubuntu-latest
    steps:
      - name: Send notification
        if: ${{ always() && github.event_name == 'schedule' }}
        run: |
          echo "✅ YouTube Downloader tests completed!"
          echo "Status: ${{ needs.test.result }}"
