import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';
import 'package:desktop/app.dart';
import 'package:desktop/state/app_state.dart';

void main() {
  testWidgets('MediaCrushApp renders header and candidate metrics', (WidgetTester tester) async {
    tester.view.physicalSize = const Size(1280, 800);
    tester.view.devicePixelRatio = 1.0;
    addTearDown(tester.view.resetPhysicalSize);

    final state = AppState();
    await tester.pumpWidget(
      ChangeNotifierProvider.value(
        value: state,
        child: const MediaCrushApp(),
      ),
    );

    expect(find.text('MediaCrush'), findsOneWidget);
    expect(find.text('CANDIDATES'), findsOneWidget);
    expect(find.text('PROJECTED SAVINGS'), findsOneWidget);
  });
}
