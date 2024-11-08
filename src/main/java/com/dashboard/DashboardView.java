package com.dashboard;

import javafx.application.Application;
import javafx.scene.Scene;
import javafx.scene.control.Label;
import javafx.scene.layout.VBox;
import javafx.stage.Stage;
import java.util.Timer;
import java.util.TimerTask;

public class DashboardView extends Application {

    private SystemInfoJNI systemInfo;  // Interface to the native code
    private Label cpuLabel;            // Label to display CPU usage
    private Label memoryLabel;         // Label to display memory usage

    public DashboardView() {
        systemInfo = new SystemInfoJNI();
    }

    @Override
    public void start(Stage primaryStage) {
        // Initialize the labels
        cpuLabel = new Label("CPU Usage: 0%");
        memoryLabel = new Label("Total Memory: 0 MB");

        // Create a layout and add labels
        VBox layout = new VBox(10);
        layout.getChildren().addAll(cpuLabel, memoryLabel);

        // Set up the scene and stage
        Scene scene = new Scene(layout, 300, 200);
        primaryStage.setTitle("System Dashboard");
        primaryStage.setScene(scene);
        primaryStage.show();

        // Start updating the dashboard with system data
        startUpdatingDashboard();
    }

    // Method to update the dashboard
    private void updateDashboard() {
        // Get the CPU usage and memory information from the native methods
        float cpuUsage = systemInfo.getCpuUsage();
        long totalMemory = systemInfo.getTotalMemory() / 1024;  // Convert to MB

        // Update the labels with the latest system info
        cpuLabel.setText("CPU Usage: " + String.format("%.2f", cpuUsage * 100) + "%");
        memoryLabel.setText("Total Memory: " + totalMemory + " MB");
    }

    // Method to start periodic updates
    private void startUpdatingDashboard() {
        Timer timer = new Timer();
        timer.scheduleAtFixedRate(new TimerTask() {
            @Override
            public void run() {
                updateDashboard();
            }
        }, 0, 1000);  // Update every second
    }

    public static void main(String[] args) {
        launch(args);  // Launch the JavaFX application
    }
}
