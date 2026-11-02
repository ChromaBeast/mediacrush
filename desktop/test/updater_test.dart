import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:desktop/models/update_info.dart';
import 'package:desktop/services/update_service.dart';
import 'package:desktop/widgets/common/update_dialog.dart';

void main() {
  group('UpdateInfo Model', () {
    test('creates none update object correctly', () {
      final info = UpdateInfo.none('1.0.1');
      expect(info.isAvailable, isFalse);
      expect(info.latestVersion, equals('1.0.1'));
      expect(info.currentVersion, equals('1.0.1'));
      expect(info.downloadUrl, isNull);
    });

    test('creates available update object correctly', () {
      const info = UpdateInfo(
        latestVersion: '1.0.2',
        currentVersion: '1.0.1',
        releaseNotes: 'Fixed hardware acceleration',
        downloadUrl: 'https://example.com/setup.exe',
        assetName: 'setup.exe',
        isAvailable: true,
      );
      expect(info.isAvailable, isTrue);
      expect(info.latestVersion, equals('1.0.2'));
      expect(info.assetName, equals('setup.exe'));
    });
  });

  group('UpdateService semver checks', () {
    final service = UpdateService();

    test('correctly identifies newer semantic versions', () {
      // Accessing semver check via public update simulation
      expect(service.isVersionNewer('1.0.2', '1.0.1'), isTrue);
      expect(service.isVersionNewer('1.1.0', '1.0.1'), isTrue);
      expect(service.isVersionNewer('2.0.0', '1.0.1'), isTrue);
      expect(service.isVersionNewer('1.0.10', '1.0.2'), isTrue);
    });

    test('rejects older or identical versions', () {
      expect(service.isVersionNewer('1.0.1', '1.0.1'), isFalse);
      expect(service.isVersionNewer('1.0.0', '1.0.1'), isFalse);
      expect(service.isVersionNewer('0.9.9', '1.0.1'), isFalse);
    });
  });

  group('UpdateDialog Widget', () {
    testWidgets('renders version, release notes and action buttons', (tester) async {
      tester.view.physicalSize = const Size(1280, 800);
      tester.view.devicePixelRatio = 1.0;
      addTearDown(tester.view.resetPhysicalSize);

      const updateInfo = UpdateInfo(
        latestVersion: '1.0.2',
        currentVersion: '1.0.1',
        releaseNotes: 'Performance improvements and bug fixes.',
        downloadUrl: 'https://example.com/MediaCrush-Windows-Setup-x64.exe',
        assetName: 'MediaCrush-Windows-Setup-x64.exe',
        isAvailable: true,
      );

      final service = UpdateService();

      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: UpdateDialog(info: updateInfo, service: service),
          ),
        ),
      );

      expect(find.text('MediaCrush Update Available (v1.0.2)'), findsOneWidget);
      expect(find.textContaining('Current version is v1.0.1'), findsOneWidget);
      expect(find.text('Performance improvements and bug fixes.'), findsOneWidget);
      expect(find.text('Later'), findsOneWidget);
      expect(find.text('Update Now'), findsOneWidget);
    });
  });
}
