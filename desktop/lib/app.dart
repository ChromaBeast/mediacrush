import 'package:flutter/material.dart';
import 'theme/app_colors.dart';
import 'widgets/footer/footer_control_bar.dart';
import 'widgets/header/header_bar.dart';
import 'widgets/stats/summary_stats_grid.dart';
import 'widgets/table/media_table.dart';

/// Main application shell and scaffold.
class MediaCrushApp extends StatelessWidget {
  const MediaCrushApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'MediaCrush',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        brightness: Brightness.dark,
        scaffoldBackgroundColor: AppColors.background,
        useMaterial3: true,
      ),
      home: const Scaffold(
        body: SafeArea(
          child: Column(
            children: [
              HeaderBar(),
              SummaryStatsGrid(),
              MediaTable(),
              FooterControlBar(),
            ],
          ),
        ),
      ),
    );
  }
}
