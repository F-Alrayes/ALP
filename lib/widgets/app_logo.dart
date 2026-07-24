import 'package:flutter/material.dart';
import '../theme/app_theme.dart';

/// The آل ناصر wordmark.
///
/// This is a typographic placeholder that mirrors the reference logo — a fort
/// crown motif above the family name "آل ناصر". Swap in the official artwork by
/// dropping an asset and using [AppLogo.image].
class AppLogo extends StatelessWidget {
  const AppLogo({super.key, this.size = 88, this.color = AppColors.primary});

  final double size;
  final Color color;

  @override
  Widget build(BuildContext context) {
    return Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        Icon(Icons.castle_rounded, size: size * 0.55, color: color),
        SizedBox(height: size * 0.06),
        Text(
          'آل ناصر',
          maxLines: 1,
          style: TextStyle(
            fontSize: size * 0.38,
            fontWeight: FontWeight.w900,
            color: color,
            height: 1.0,
          ),
        ),
      ],
    );
  }
}

/// A compact, horizontal version of the logo for app bars.
class AppLogoMark extends StatelessWidget {
  const AppLogoMark({super.key, this.color = AppColors.primary, this.size = 28});

  final Color color;
  final double size;

  @override
  Widget build(BuildContext context) {
    return Icon(Icons.castle_rounded, size: size, color: color);
  }
}
