import 'dart:io';

import 'package:flutter_test/flutter_test.dart';
import 'package:path/path.dart' as p;
import 'package:desktop/models/hardware_engine.dart';
import 'package:desktop/state/app_state.dart';

void main() {
  late Directory tmp;
  late AppState state;
  int notifications = 0;

  setUp(() {
    tmp = Directory.systemTemp.createTempSync('mc_state_');
    state = AppState();
    notifications = 0;
    state.addListener(() => notifications++);
  });

  tearDown(() {
    state.dispose();
    if (tmp.existsSync()) tmp.deleteSync(recursive: true);
  });

  File make(String name, int bytes) {
    final f = File(p.join(tmp.path, name))..createSync(recursive: true);
    f.writeAsBytesSync(List.filled(bytes, 0));
    return f;
  }

  group('initial state', () {
    test('is empty and idle', () {
      expect(state.items, isEmpty);
      expect(state.isScanning, isFalse);
      expect(state.isCompressing, isFalse);
      expect(state.job, isNull);
      expect(state.preset, 'anime');
      expect(state.outputFolder, isNull);
      expect(state.totalCandidates, 0);
      expect(state.savingsPercentage, 0.0);
      expect(state.hardware.name, 'libx265');
    });
  });

  group('setters notify listeners', () {
    test('preset', () {
      state.setPreset('saver');
      expect(state.preset, 'saver');
      expect(notifications, 1);
    });

    test('output folder', () {
      state.setOutputFolder('/out');
      expect(state.outputFolder, '/out');
      expect(notifications, 1);
    });

    test('hardware', () {
      state.setHardware(HardwareEngine.fromCliName('nvenc'));
      expect(state.hardware.vendor, 'NVIDIA');
      expect(notifications, 1);
    });
  });

  group('addFiles', () {
    test('adds existing files with estimate and default output folder', () {
      final f = make('a.mkv', 1000);
      state.addFiles([f.path]);
      expect(state.items, hasLength(1));
      expect(state.items.first.fileName, 'a.mkv');
      expect(state.items.first.originalBytes, 1000);
      expect(state.items.first.estimatedBytes, 450);
      expect(state.outputFolder, p.join(tmp.path, 'crushed'));
      expect(notifications, 1);
    });

    test('ignores missing files and duplicates', () {
      final f = make('a.mkv', 100);
      state.addFiles([f.path, f.path, p.join(tmp.path, 'ghost.mkv')]);
      expect(state.items, hasLength(1));
    });

    test('empty list is a no-op and does not notify', () {
      state.addFiles([]);
      expect(notifications, 0);
    });

    test('keeps an explicitly chosen output folder', () {
      state.setOutputFolder('/custom');
      state.addFiles([make('a.mkv', 10).path]);
      expect(state.outputFolder, '/custom');
    });

    test('aggregates totals and savings', () {
      state.addFiles([make('a.mkv', 1000).path, make('b.mkv', 3000).path]);
      expect(state.totalCandidates, 2);
      expect(state.totalOriginalBytes, 4000);
      expect(state.totalEstimatedBytes, 1800);
      expect(state.totalSavedBytes, 2200);
      expect(state.savingsPercentage, closeTo(55.0, 1e-9));
    });
  });

  group('scanFolder', () {
    test('finds only video files recursively and sets folders', () async {
      make('a.mkv', 10);
      make('sub/b.MP4', 10);
      make('notes.txt', 10);
      await state.scanFolder(tmp.path);
      expect(state.items.map((i) => i.fileName).toSet(), {'a.mkv', 'b.MP4'});
      expect(state.selectedFolder, tmp.path);
      expect(state.outputFolder, p.join(tmp.path, 'crushed'));
      expect(state.isScanning, isFalse);
      expect(notifications, greaterThanOrEqualTo(2)); // scanning on, scanning off
    });

    test('missing folder yields no items', () async {
      await state.scanFolder(p.join(tmp.path, 'nope'));
      expect(state.items, isEmpty);
      expect(state.isScanning, isFalse);
    });

    test('rescan replaces previous items', () async {
      make('a.mkv', 10);
      await state.scanFolder(tmp.path);
      File(p.join(tmp.path, 'a.mkv')).deleteSync();
      await state.scanFolder(tmp.path);
      expect(state.items, isEmpty);
    });
  });

  group('clearItems', () {
    test('empties list and selection', () async {
      make('a.mkv', 10);
      await state.scanFolder(tmp.path);
      state.clearItems();
      expect(state.items, isEmpty);
      expect(state.selectedFolder, isNull);
    });
  });

  group('compression control', () {
    test('startCompression with nothing queued does nothing', () async {
      await state.startCompression();
      expect(state.job, isNull);
      expect(state.isCompressing, isFalse);
    });

    test('pauseCompression is safe when idle and notifies', () {
      state.pauseCompression();
      expect(state.isCompressing, isFalse);
      expect(notifications, 1);
    });

    test('a bogus input fails the item without crashing and finishes the job', () async {
      // Input exists on disk but is not a real video, so ffmpeg (or its absence) must fail cleanly.
      final f = make('fake.mkv', 2048);
      state.addFiles([f.path]);
      state.setOutputFolder(p.join(tmp.path, 'out'));
      await state.startCompression();
      expect(state.isCompressing, isFalse);
      expect(state.job!.isRunning, isFalse);
      expect(state.job!.completedFiles, 0);
      expect(state.items.first.status.name, 'failed');
    }, timeout: const Timeout(Duration(seconds: 60)));
  });
}
