package com.hoverstone.ballroomcompanion;

import android.graphics.Color;
import android.os.Bundle;
import android.view.View;
import android.view.Window;
import android.view.WindowManager;
import androidx.core.view.WindowCompat;
import androidx.core.view.WindowInsetsControllerCompat;
import com.getcapacitor.BridgeActivity;

public class MainActivity extends BridgeActivity {
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        registerPlugin(DWTSLiveTrackingPlugin.class);
        super.onCreate(savedInstanceState);
        Window window = getWindow();
        window.addFlags(WindowManager.LayoutParams.FLAG_DRAWS_SYSTEM_BAR_BACKGROUNDS);
        window.setStatusBarColor(Color.parseColor("#111416"));
        window.setNavigationBarColor(Color.parseColor("#111416"));

        View decorView = window.getDecorView();
        decorView.setBackgroundColor(Color.parseColor("#111416"));

        WindowInsetsControllerCompat insetsController = WindowCompat.getInsetsController(window, decorView);
        if (insetsController != null) {
            insetsController.setAppearanceLightStatusBars(false); // Light (white) text/icons for dark status bar
            insetsController.setAppearanceLightNavigationBars(false); // Light navigation bar icons
        }
    }
}
