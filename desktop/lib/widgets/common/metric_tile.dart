import 'package:flutter/material.dart';
import '../../theme/app_colors.dart';
import '../../theme/app_typography.dart';
import 'unslop_card.dart';

/// Reusable metric tile displaying tabular figures with clear visual hierarchy.
class MetricTile extends StatelessWidget {
  final String title;
  final String value;
  final String? comparison;
  final Color? valueColor;
  final bool isHighlighted;

  const MetricTile({
    super.key,
    required this.title,
    required this.value,
    this.comparison,
    this.valueColor,
    this.isHighlighted = false,
  });

  @override
  Widget build(BuildContext context) {
    return UnslopCard(
      padding: const EdgeInsets.symmetric(horizontal: 16.0, vertical: 14.0),
      borderColor: isHighlighted ? AppColors.borderActive : AppColors.border,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Text(
            title,
            style: AppTypography.label,
          ),
          const SizedBox(height: 6.0),
          Row(
            crossAxisAlignment: CrossAxisAlignment.baseline,
            textBaseline: TextBaseline.alphabetic,
            children: [
              Text(
                value,
                style: AppTypography.metricValue.copyWith(
                  color: valueColor ?? AppColors.textPrimary,
                ),
              ),
              if (comparison != null) ...[
                const SizedBox(width: 8.0),
                Text(
                  comparison!,
                  style: AppTypography.monoBadge.copyWith(
                    color: AppColors.success,
                  ),
                ),
              ],
            ],
          ),
        ],
      ),
    );
  }
}
