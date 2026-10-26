import Flutter
import UIKit

@main
@objc class AppDelegate: FlutterAppDelegate {
  private var privacyCover: UIView?
  override func application(
    _ application: UIApplication,
    didFinishLaunchingWithOptions launchOptions: [UIApplication.LaunchOptionsKey: Any]?
  ) -> Bool {
    GeneratedPluginRegistrant.register(with: self)
    if let controller = window?.rootViewController as? FlutterViewController {
      FlutterMethodChannel(name: "pwc/privacy", binaryMessenger: controller.binaryMessenger)
        .setMethodCallHandler { call, result in
          guard call.method == "installation" || call.method == "invalidate" else { result(FlutterMethodNotImplemented); return }
          do {
            let directory = try FileManager.default.url(for: .applicationSupportDirectory, in: .userDomainMask, appropriateFor: nil, create: true)
            var marker = directory.appendingPathComponent("pwc-installation-v1")
            if !FileManager.default.fileExists(atPath: marker.path) || call.method == "invalidate" {
              try UUID().uuidString.data(using: .utf8)!.write(to: marker, options: [.atomic, .noFileProtection])
              let handle = try FileHandle(forWritingTo: marker)
              try handle.synchronize()
              try handle.close()
            }
            var values = URLResourceValues()
            values.isExcludedFromBackup = true
            try marker.setResourceValues(values)
            result(try String(contentsOf: marker, encoding: .utf8))
          } catch { result(FlutterError(code: "STORAGE_UNAVAILABLE", message: "Installation binding unavailable", details: nil)) }
        }
    }
    return super.application(application, didFinishLaunchingWithOptions: launchOptions)
  }
  override func applicationWillResignActive(_ application: UIApplication) {
    if let window = window, privacyCover == nil {
      let cover = UIView(frame: window.bounds)
      cover.backgroundColor = UIColor.systemBackground
      cover.autoresizingMask = [.flexibleWidth, .flexibleHeight]
      window.addSubview(cover)
      privacyCover = cover
    }
    super.applicationWillResignActive(application)
  }
  override func applicationDidBecomeActive(_ application: UIApplication) {
    privacyCover?.removeFromSuperview()
    privacyCover = nil
    super.applicationDidBecomeActive(application)
  }
}
