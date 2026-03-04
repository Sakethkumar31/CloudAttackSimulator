@echo off
setlocal

if "%NEO4J_URI%"=="" set "NEO4J_URI=neo4j://localhost:7687"
if "%NEO4J_USER%"=="" set "NEO4J_USER=neo4j"
if "%NEO4J_PASSWORD%"=="" set "NEO4J_PASSWORD=your_password"

py dashboard_web\app.py

