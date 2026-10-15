import { defineConfig } from '@playwright/test';
export default defineConfig({
 testDir:'./tests/browser',fullyParallel:false,workers:1,
 use:{baseURL:'http://127.0.0.1:4173',headless:true,viewport:{width:1440,height:1000},trace:'retain-on-failure'},
 webServer:[
  {command:'npx vite --host 127.0.0.1 --port 4173 --strictPort',url:'http://127.0.0.1:4173',reuseExistingServer:false},
  {command:'npx vite --host 127.0.0.1 --port 4174 --strictPort',url:'http://127.0.0.1:4174',reuseExistingServer:false,env:{VITE_DATA_MODE:'api',VITE_API_BASE_URL:'http://127.0.0.1:4174/api'}}
 ]
});
