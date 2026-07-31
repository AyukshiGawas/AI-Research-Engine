import React from 'react';
import { Outlet } from 'react-router-dom';
import { Navbar } from '../components/Navbar';
import { Sidebar } from '../components/Sidebar';

export const DashboardLayout = () => {
  return (
    <div className="dashboard-shell-container">
      <Navbar />
      <div className="dashboard-shell-body">
        <Sidebar />
        <main className="dashboard-main-content">
          <Outlet />
        </main>
      </div>
    </div>
  );
};
