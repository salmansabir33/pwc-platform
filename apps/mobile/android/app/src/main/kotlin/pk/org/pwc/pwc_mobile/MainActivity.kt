package pk.org.pwc.pwc_mobile

import android.os.Bundle
import android.util.AtomicFile
import android.view.WindowManager
import io.flutter.embedding.android.FlutterActivity
import io.flutter.embedding.engine.FlutterEngine
import io.flutter.plugin.common.MethodChannel
import java.io.File
import java.util.UUID

class MainActivity : FlutterActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        window.addFlags(WindowManager.LayoutParams.FLAG_SECURE)
        super.onCreate(savedInstanceState)
    }
    override fun configureFlutterEngine(flutterEngine: FlutterEngine) {
        super.configureFlutterEngine(flutterEngine)
        MethodChannel(flutterEngine.dartExecutor.binaryMessenger, "pwc/privacy")
            .setMethodCallHandler { call, result ->
                if (call.method != "installation" && call.method != "invalidate") {
                    result.notImplemented()
                } else {
                    try {
                        val marker = File(noBackupFilesDir, "pwc-installation-v1")
                        if (!marker.exists() || call.method == "invalidate") {
                            val id = UUID.randomUUID().toString()
                            // Non-secret installation binding; never backed up.
                            val atomic = AtomicFile(marker)
                            val stream = atomic.startWrite()
                            try {
                                stream.write(id.toByteArray(Charsets.UTF_8))
                                stream.fd.sync()
                                atomic.finishWrite(stream)
                            } catch (failure: Exception) {
                                atomic.failWrite(stream)
                                throw failure
                            }
                        }
                        val id = AtomicFile(marker).openRead().bufferedReader().use { it.readText() }
                        require(id.matches(Regex("[a-fA-F0-9-]{36}")))
                        result.success(id)
                    } catch (_: Exception) {
                        result.error("STORAGE_UNAVAILABLE", "Installation binding unavailable", null)
                    }
                }
            }
    }
}
