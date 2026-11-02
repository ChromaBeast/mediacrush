import 'package:flutter/material.dart';
import '../../theme/app_colors.dart';
import '../../theme/app_typography.dart';

/// Minimal quiet badge pill for metadata, codecs, and status.
class BadgePill extends StatelessWidget {
  final String label;
  final Color foreground;
  final Color? background;
  final bool isMonospace;

  const BadgePill({
    super.key,
    required this.label,
    required this.foreground,
    this.background,
    this.isMonospace = true,
  });

  factory BadgePill.codec(String codec) {
    final isHevc = codec.toUpperCase().contains('HEVC') || codec.toUpperCase().contains('265');
    final isAv1 = codec.toUpperCase().contains('AV1');
    final color = isHevc || isAv1 ? AppColors.accent : AppColors.textSecondary;
    return BadgePill(
      label: codec,
      foreground: color,
      background: color.withValues(alpha: 0.12),
    );
  }

  factory BadgePill.status({
    required String text,
    required Color color,
  }) {
    return BadgePill(
      label: text,
      foreground: color,
      background: color.withValues(alpha: 0.12),
      isMonospace: false,
    );
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 7.0, vertical: 3.0),
      decoration: BoxDecoration(
        color: background ?? AppColors.surfaceElevated,
        borderRadius: BorderRadius.circular(4.0),
        border: Border.all(
          color: foreground.withValues(alpha: 0.2),
          width: 0.75,
        ),
      ),
      child: Text(
        label,
        style: (isMonospace ? AppTypography.monoBadge : AppTypography.label).copyWith(
          color: foreground,
          height: 1.1,
        ),
      ),
    );
  }
}
