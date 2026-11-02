import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../state/app_state.dart';
import '../../theme/app_colors.dart';
import '../../theme/app_typography.dart';

/// Bottom action bar featuring batch progress bar, encoding speed, and primary action.
class FooterControlBar extends StatelessWidget {
  const FooterControlBar({super.key});

  @override
  Widget build(BuildContext context) {
    final state = context.watch<AppState>();
    final job = state.job;

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 20.0, vertical: 14.0),
      decoration: BoxDecoration(
        color: AppColors.background,
        border: Border(top: BorderSide(color: AppColors.border)),
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Row(
            children: [
              Expanded(
                child: Text(
                  _buildStatusText(state),
                  style: AppTypography.bodySecondary,
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
              ),
              const SizedBox(width: 16.0),
              if (state.isCompressing)
                OutlinedButton(
                  onPressed: () => state.pauseCompression(),
                  style: OutlinedButton.styleFrom(
                    foregroundColor: AppColors.textPrimary,
                    side: BorderSide(color: AppColors.border),
                    padding: const EdgeInsets.symmetric(horizontal: 16.0, vertical: 10.0),
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(6.0)),
                  ),
                  child: Text('Pause', style: AppTypography.bodySecondary),
                )
              else
                FilledButton.icon(
                  onPressed: state.items.isEmpty ? null : () => state.startCompression(),
                  icon: const Icon(Icons.bolt, size: 16),
                  label: Text('Start Optimization', style: AppTypography.body),
                  style: FilledButton.styleFrom(
                    backgroundColor: AppColors.accent,
                    foregroundColor: const Color(0xFF0F1012),
                    disabledBackgroundColor: AppColors.surfaceElevated,
                    disabledForegroundColor: AppColors.textMuted,
                    padding: const EdgeInsets.symmetric(horizontal: 18.0, vertical: 10.0),
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(6.0)),
                  ),
                ),
            ],
          ),
          if (state.isCompressing && job != null) ...[
            const SizedBox(height: 10.0),
            ClipRRect(
              borderRadius: BorderRadius.circular(3.0),
              child: LinearProgressIndicator(
                value: job.overallProgress,
                backgroundColor: AppColors.surfaceElevated,
                valueColor: const AlwaysStoppedAnimation<Color>(AppColors.accent),
                minHeight: 4.0,
              ),
            ),
          ],
        ],
      ),
    );
  }

  String _buildStatusText(AppState state) {
    if (state.isScanning) {
      return 'Scanning directory tree for media files...';
    }
    if (state.isCompressing && state.job != null) {
      final job = state.job!;
      return 'Crushing: ${job.completedFiles} of ${job.totalFiles} files completed • ${state.hardware.typicalFps} FPS (${state.hardware.codec})';
    }
    if (state.items.isNotEmpty) {
      return 'Ready to compress ${state.items.length} files. Estimated savings: ${state.savingsPercentage.toStringAsFixed(1)}%';
    }
    return 'Select a folder to begin optimization';
  }
}
