@echo off
cd frontend
if not exist node_modules npm install
if not exist .env.local copy .env.local.example .env.local
npm run dev
