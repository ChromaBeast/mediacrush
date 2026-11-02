import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../state/app_state.dart';
import '../../theme/app_colors.dart';
import '../../theme/app_typography.dart';
import 'media_row_item.dart';

/// Virtualized data table displaying media candidates and their compression progress.
class MediaTable extends StatelessWidget {
  const MediaTable({super.key});

  @override
  Widget build(BuildContext context) {
    final state = context.watch<AppState>();

    return Expanded(
      child: Container(
        margin: const EdgeInsets.symmetric(horizontal: 20.0),
        decoration: BoxDecoration(
          color: AppColors.surface,
          borderRadius: BorderRadius.circular(8.0),
          border: Border.all(color: AppColors.border),
        ),
        child: Column(
          children: [
            _buildTableHeader(),
            Expanded(
              child: _buildBody(state),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildTableHeader() {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16.0, vertical: 10.0),
      decoration: BoxDecoration(
        color: AppColors.surfaceElevated,
        borderRadius: const BorderRadius.vertical(top: Radius.circular(8.0)),
        border: Border(bottom: BorderSide(color: AppColors.border)),
      ),
      child: Row(
        children: [
          Expanded(flex: 4, child: Text('FILE NAME', style: AppTypography.label)),
          const SizedBox(width: 8.0),
          SizedBox(width: 70, child: Text('CODEC', style: AppTypography.label)),
          SizedBox(width: 60, child: Text('RES', style: AppTypography.label)),
          SizedBox(width: 90, child: Text('ORIGINAL', style: AppTypography.label)),
          SizedBox(width: 90, child: Text('EST. NEW', style: AppTypography.label)),
          SizedBox(width: 65, child: Text('SAVED', style: AppTypography.label)),
          SizedBox(width: 100, child: Text('STATUS', style: AppTypography.label)),
        ],
      ),
    );
  }

  Widget _buildBody(AppState state) {
    if (state.isScanning) {
      return Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const SizedBox(
              width: 20,
              height: 20,
              child: CircularProgressIndicator(strokeWidth: 2.0, color: AppColors.accent),
            ),
            const SizedBox(height: 12.0),
            Text('Scanning directory tree for media files...', style: AppTypography.bodySecondary),
          ],
        ),
      );
    }

    if (state.items.isEmpty) {
      return Center(
        child: Text(
          'Select a movie or TV show folder above to scan and calculate savings.',
          style: AppTypography.bodySecondary.copyWith(color: AppColors.textMuted),
        ),
      );
    }

    return ListView.builder(
      itemCount: state.items.length,
      itemBuilder: (context, index) {
        return MediaRowItem(
          item: state.items[index],
          isEven: index.isEven,
        );
      },
    );
  }
}
