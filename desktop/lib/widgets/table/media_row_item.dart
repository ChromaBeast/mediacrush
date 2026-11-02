import 'package:flutter/material.dart';
import '../../models/media_item.dart';
import '../../theme/app_colors.dart';
import '../../theme/app_typography.dart';
import '../common/badge_pill.dart';

/// Single item row in the media queue table.
class MediaRowItem extends StatelessWidget {
  final MediaItem item;
  final bool isEven;

  const MediaRowItem({
    super.key,
    required this.item,
    required this.isEven,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16.0, vertical: 8.0),
      color: isEven ? AppColors.surface : AppColors.surfaceElevated.withValues(alpha: 0.4),
      child: Row(
        children: [
          Expanded(
            flex: 4,
            child: Text(
              item.fileName,
              style: AppTypography.body,
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
            ),
          ),
          const SizedBox(width: 8.0),
          SizedBox(
            width: 70,
            child: Align(
              alignment: Alignment.centerLeft,
              child: BadgePill.codec(item.codec),
            ),
          ),
          SizedBox(
            width: 60,
            child: Text(item.resolution, style: AppTypography.monoCell),
          ),
          SizedBox(
            width: 90,
            child: Text(
              MediaItem.formatBytes(item.originalBytes),
              style: AppTypography.monoCell,
            ),
          ),
          SizedBox(
            width: 90,
            child: Text(
              MediaItem.formatBytes(
                item.status == MediaStatus.completed ? item.finalBytes : item.estimatedBytes,
              ),
              style: AppTypography.monoCell.copyWith(color: AppColors.accent),
            ),
          ),
          SizedBox(
            width: 65,
            child: Text(
              '-${(item.savingsRatio * 100).toStringAsFixed(0)}%',
              style: AppTypography.monoCell.copyWith(color: AppColors.success),
            ),
          ),
          SizedBox(
            width: 100,
            child: _buildStatusWidget(),
          ),
        ],
      ),
    );
  }

  Widget _buildStatusWidget() {
    switch (item.status) {
      case MediaStatus.pending:
        return BadgePill.status(text: 'Queued', color: AppColors.textMuted);
      case MediaStatus.compressing:
        return Row(
          children: [
            SizedBox(
              width: 12,
              height: 12,
              child: CircularProgressIndicator(
                strokeWidth: 1.5,
                color: AppColors.accent,
                value: item.progress > 0 ? item.progress : null,
              ),
            ),
            const SizedBox(width: 6.0),
            Text('${(item.progress * 100).toInt()}%', style: AppTypography.monoBadge),
          ],
        );
      case MediaStatus.completed:
        return BadgePill.status(text: 'Crushed', color: AppColors.success);
      case MediaStatus.skipped:
        return BadgePill.status(text: 'Skipped', color: AppColors.warning);
      case MediaStatus.failed:
        return BadgePill.status(text: 'Failed', color: AppColors.error);
    }
  }
}
