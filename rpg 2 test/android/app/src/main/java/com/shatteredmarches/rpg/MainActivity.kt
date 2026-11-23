package com.shatteredmarches.rpg

import android.annotation.SuppressLint
import android.os.Bundle
import android.webkit.WebView
import androidx.appcompat.app.AppCompatActivity
import com.chaquo.python.Python
import kotlin.concurrent.thread

class MainActivity : AppCompatActivity() {
    private lateinit var webView: WebView

    @SuppressLint("SetJavaScriptEnabled")
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        webView = WebView(this)
        setContentView(webView)

        webView.settings.javaScriptEnabled = true
        webView.settings.domStorageEnabled = true
        webView.settings.allowFileAccess = true
        webView.settings.mediaPlaybackRequiresUserGesture = false

        thread {
            try {
                val server = Python.getInstance().getModule("mobile_server")
                server.callAttr(
                    "start",
                    applicationContext.filesDir.absolutePath
                )
            } catch (_: Throwable) {
                // The WebView reports server startup failures in the status screen.
            }
        }

        webView.postDelayed({
            webView.loadUrl("http://127.0.0.1:8080/")
        }, 1200)
    }

    override fun onDestroy() {
        webView.stopLoading()
        webView.destroy()
        super.onDestroy()
    }

    @Deprecated("Deprecated in Java")
    override fun onBackPressed() {
        if (webView.canGoBack()) {
            webView.goBack()
        } else {
            super.onBackPressed()
        }
    }
}
