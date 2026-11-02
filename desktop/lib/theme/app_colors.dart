import 'package:flutter/material.dart';

/// Unslop Graphite Palette & Design Tokens for MediaCrush.
/// Focuses on quiet chrome, deep tinted graphite surfaces,
/// subtle hairlines, and single intentional accents.
abstract final class AppColors {
  // Backgrounds & Surfaces (Graphite Ramp)
  static const Color background = Color(0xFF0F1012);
  static const Color surface = Color(0xFF16181B);
  static const Color surfaceElevated = Color(0xFF1E2024);
  static const Color surfaceHover = Color(0xFF25282E);

  // Hairlines & Dividers
  static final Color border = Colors.white.withValues(alpha: 0.08);
  static final Color borderSubtle = Colors.white.withValues(alpha: 0.04);
  static final Color borderActive = const Color(0xFF38BDF8).withValues(alpha: 0.35);

  // Text Roles (Primary, Secondary, Muted)
  static const Color textPrimary = Color(0xFFF1F3F5);
  static const Color textSecondary = Color(0xFF8C939D);
  static const Color textMuted = Color(0xFF545963);

  // Accent (Sky Blue for Primary Actions & Silicon HUD)
  static const Color accent = Color(0xFF38BDF8);
  static const Color accentDark = Color(0xFF0284C7);
  static final Color accentGlow = const Color(0xFF38BDF8).withValues(alpha: 0.12);

  // Semantics (Measured & Muted)
  static const Color success = Color(0xFF34D399);
  static final Color successMuted = const Color(0xFF34D399).withValues(alpha: 0.15);
  static const Color warning = Color(0xFFFBBF24);
  static const Color error = Color(0xFFF87171);
  static final Color errorMuted = const Color(0xFFF87171).withValues(alpha: 0.15);
}
