import 'package:flutter/material.dart';

/// Reusable vector branding logo for MediaCrush matching the favicon SVG.
class AppLogo extends StatelessWidget {
  final double size;

  const AppLogo({super.key, this.size = 24.0});

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: size,
      height: size,
      child: CustomPaint(
        painter: _AppLogoPainter(),
      ),
    );
  }
}

class _AppLogoPainter extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    final double s = size.width / 512.0;

    Offset pt(double x, double y) => Offset(x * s, y * s);

    // Cyan Gradient for compression jaws
    final cyanPaint = Paint()
      ..shader = const LinearGradient(
        begin: Alignment.topLeft,
        end: Alignment.bottomRight,
        colors: [Color(0xFF38BDF8), Color(0xFF0EA5E9), Color(0xFF0284C7)],
      ).createShader(Rect.fromLTWH(0, 0, size.width, size.height))
      ..style = PaintingStyle.fill;

    // Core Gradient for center diamond
    final corePaint = Paint()
      ..shader = const LinearGradient(
        begin: Alignment.topLeft,
        end: Alignment.bottomRight,
        colors: [Color(0xFF1E222B), Color(0xFF0F1116)],
      ).createShader(Rect.fromLTWH(0, 0, size.width, size.height))
      ..style = PaintingStyle.fill;

    final borderPaint = Paint()
      ..color = const Color(0xFF38BDF8)
      ..strokeWidth = 8.0 * s
      ..style = PaintingStyle.stroke
      ..strokeJoin = StrokeJoin.round;

    final arrowPaint = Paint()
      ..color = Colors.white
      ..style = PaintingStyle.fill;

    // 1. Left Compression Jaw
    final leftJaw = Path()
      ..moveTo(pt(120, 110).dx, pt(120, 110).dy)
      ..lineTo(pt(230, 220).dx, pt(230, 220).dy)
      ..lineTo(pt(230, 292).dx, pt(230, 292).dy)
      ..lineTo(pt(120, 402).dx, pt(120, 402).dy)
      ..lineTo(pt(72, 364).dx, pt(72, 364).dy)
      ..lineTo(pt(162, 256).dx, pt(162, 256).dy)
      ..lineTo(pt(72, 148).dx, pt(72, 148).dy)
      ..close();
    canvas.drawPath(leftJaw, cyanPaint);

    // 2. Right Compression Jaw
    final rightJaw = Path()
      ..moveTo(pt(392, 110).dx, pt(392, 110).dy)
      ..lineTo(pt(282, 220).dx, pt(282, 220).dy)
      ..lineTo(pt(282, 292).dx, pt(282, 292).dy)
      ..lineTo(pt(392, 402).dx, pt(392, 402).dy)
      ..lineTo(pt(440, 364).dx, pt(440, 364).dy)
      ..lineTo(pt(350, 256).dx, pt(350, 256).dy)
      ..lineTo(pt(440, 148).dx, pt(440, 148).dy)
      ..close();
    canvas.drawPath(rightJaw, cyanPaint);

    // 3. Center Diamond Core
    final coreDiamond = Path()
      ..moveTo(pt(256, 168).dx, pt(256, 168).dy)
      ..lineTo(pt(328, 256).dx, pt(328, 256).dy)
      ..lineTo(pt(256, 344).dx, pt(256, 344).dy)
      ..lineTo(pt(184, 256).dx, pt(184, 256).dy)
      ..close();
    canvas.drawPath(coreDiamond, corePaint);
    canvas.drawPath(coreDiamond, borderPaint);

    // 4. Precision Play Core Arrow
    final arrow = Path()
      ..moveTo(pt(242, 222).dx, pt(242, 222).dy)
      ..lineTo(pt(284, 256).dx, pt(284, 256).dy)
      ..lineTo(pt(242, 290).dx, pt(242, 290).dy)
      ..close();
    canvas.drawPath(arrow, arrowPaint);
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}
