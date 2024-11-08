package com.dashboard;

public class DataCollector {

    static {
        System.loadLibrary("SystemInfoJNI"); // Load the native library
    }

    // Native methods to fetch system information
    public native String getGlobalMemoryUsage();
    public native String getGlobalCPUUsage();

    public String getGlobalMemoryUsage() {
        return getGlobalMemoryUsage(); // Calls the native method for memory usage
    }

    public String getGlobalCPUUsage() {
        return getGlobalCPUUsage(); // Calls the native method for CPU usage
    }
}
