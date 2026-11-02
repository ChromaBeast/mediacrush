import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../models/media_item.dart';
import '../../state/app_state.dart';
import '../../theme/app_colors.dart';
import '../common/metric_tile.dart';

/// Grid of 4 summary telemetry metric tiles.
class SummaryStatsGrid extends StatelessWidget {
  const SummaryStatsGrid({super.key});

  @override
  Widget build(BuildContext context) {
    final state = context.watch<AppState>();

    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 20.0, vertical: 12.0),
      child: Row(
        children: [
          Expanded(
            child: MetricTile(
              title: 'CANDIDATES',
              value: '${state.totalCandidates}',
            ),
          ),
          const SizedBox(width: 12.0),
          Expanded(
            child: MetricTile(
              title: 'ORIGINAL SIZE',
              value: MediaItem.formatBytes(state.totalOriginalBytes),
            ),
          ),
          const SizedBox(width: 12.0),
          Expanded(
            child: MetricTile(
              title: 'ESTIMATED SIZE',
              value: MediaItem.formatBytes(state.totalEstimatedBytes),
            ),
          ),
          const SizedBox(width: 12.0),
          Expanded(
            child: MetricTile(
              title: 'PROJECTED SAVINGS',
              value: MediaItem.formatBytes(state.totalSavedBytes),
              comparison: state.savingsPercentage > 0
                  ? '-${state.savingsPercentage.toStringAsFixed(1)}%'
                  : null,
              valueColor: AppColors.success,
              isHighlighted: true,
            ),
          ),
        ],
      ),
    );
  }
}
