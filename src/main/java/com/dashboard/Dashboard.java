package com.dashboard;

import java.util.Timer;
import java.util.TimerTask;

public class Dashboard {

    private SystemInfoJNI systemInfo;

    public Dashboard() {
        systemInfo = new SystemInfoJNI();
    }

    // Start updating the system information every second
    public void startUpdatingDashboard() {
        Timer timer = new Timer();
        timer.scheduleAtFixedRate(new TimerTask() {
            @Override
            public void run() {
                updateDashboard();
            }
        }, 0, 1000);  // Update every second
    }

    // Method to fetch and update dashboard data
    private void updateDashboard() {
        // Get the CPU usage and total memory
        float cpuUsage = systemInfo.getCpuUsage();
        long totalMemory = systemInfo.getTotalMemory() / 1024;  // Convert to MB

        // Here, you can print to the console for debugging or perform other actions
        System.out.println("CPU Usage: " + String.format("%.2f", cpuUsage * 100) + "%");
        System.out.println("Total Memory: " + totalMemory + " MB");
    }

    public static void main(String[] args) {
        Dashboard dashboard = new Dashboard();
        dashboard.startUpdatingDashboard();
    }
}
