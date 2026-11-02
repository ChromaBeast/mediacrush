// ignore_for_file: deprecated_member_use

import 'dart:io';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:window_manager/legacy.dart';
import 'app.dart';
import 'state/app_state.dart';

void main(List<String> args) async {
  // Safety guard: If invoked with CLI arguments or by a child process, do NOT spawn GUI
  if (args.isNotEmpty) {
    if (args.contains('detect')) {
      stdout.writeln('CPU x265 (Safe Fallback)');
      exit(0);
    }
    stdout.writeln('MediaCrush GUI runner received unexpected arguments: ${args.join(" ")}');
    exit(0);
  }

  WidgetsFlutterBinding.ensureInitialized();

  if (Platform.isWindows || Platform.isMacOS || Platform.isLinux) {
    await windowManager.ensureInitialized();
    final windowOptions = WindowOptions(
      size: const Size(1100, 720),
      minimumSize: const Size(840, 540),
      center: true,
      backgroundColor: Colors.transparent,
      title: 'MediaCrush',
    );
    await windowManager.waitUntilReadyToShow(windowOptions, () async {
      await windowManager.show();
      await windowManager.focus();
    });
  }

  final appState = AppState();
  await appState.initialize();

  runApp(
    ChangeNotifierProvider.value(
      value: appState,
      child: const MediaCrushApp(),
    ),
  );
}
