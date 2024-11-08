package com.dashboard;

public class SystemInfoJNI {
    // Load the native library
    static {
        System.loadLibrary("SystemInfoJNI");
    }

    // Declare a native method to get system CPU usage
    public native float getCpuUsage();

    // Declare a native method to get total memory in kilobytes
    public native long getTotalMemory();

    // Declare other native methods for memory, process list, etc.
}
