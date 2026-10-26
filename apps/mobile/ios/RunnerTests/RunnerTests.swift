import Flutter
import UIKit
import XCTest

class RunnerTests: XCTestCase {
  func testNativeDeviceAcceptanceRequiresDedicatedHarness() throws {
    throw XCTSkip("Run integration_test/credential_lifecycle_test.dart on a real iOS simulator/device; this host stub is not security acceptance.")
  }
}
