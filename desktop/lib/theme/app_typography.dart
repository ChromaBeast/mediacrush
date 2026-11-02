import 'package:flutter/material.dart';
import 'app_colors.dart';

/// Unslop Typography Scale with Tabular Figures for MediaCrush.
abstract final class AppTypography {
  static const String _fontFamily = 'Segoe UI';
  static const String _monoFont = 'Consolas';

  static TextStyle get title => const TextStyle(
        fontFamily: _fontFamily,
        fontSize: 15,
        fontWeight: FontWeight.w600,
        color: AppColors.textPrimary,
        letterSpacing: -0.2,
      );

  static TextStyle get body => const TextStyle(
        fontFamily: _fontFamily,
        fontSize: 13,
        fontWeight: FontWeight.w400,
        color: AppColors.textPrimary,
      );

  static TextStyle get bodySecondary => const TextStyle(
        fontFamily: _fontFamily,
        fontSize: 12,
        fontWeight: FontWeight.w400,
        color: AppColors.textSecondary,
      );

  static TextStyle get label => const TextStyle(
        fontFamily: _fontFamily,
        fontSize: 11,
        fontWeight: FontWeight.w500,
        color: AppColors.textMuted,
        letterSpacing: 0.1,
      );

  static TextStyle get metricValue => const TextStyle(
        fontFamily: _monoFont,
        fontSize: 20,
        fontWeight: FontWeight.w600,
        color: AppColors.textPrimary,
        fontFeatures: [FontFeature.tabularFigures()],
      );

  static TextStyle get monoCell => const TextStyle(
        fontFamily: _monoFont,
        fontSize: 12,
        fontWeight: FontWeight.w400,
        color: AppColors.textSecondary,
        fontFeatures: [FontFeature.tabularFigures()],
      );

  static TextStyle get monoBadge => const TextStyle(
        fontFamily: _monoFont,
        fontSize: 10,
        fontWeight: FontWeight.w500,
        fontFeatures: [FontFeature.tabularFigures()],
      );
}
