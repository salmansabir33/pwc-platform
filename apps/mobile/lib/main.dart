import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'app/app.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  // Framework/zone handlers must never print request bodies or secret values.
  FlutterError.onError = (details) {
    /* Fail visually through Flutter, no telemetry. */
  };
  runApp(const ProviderScope(child: PwcApp()));
}
