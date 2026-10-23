import 'package:flutter/material.dart';

class AppTheme {
  const AppTheme._();

  static ThemeData dark() {
    return ThemeData(
      brightness: Brightness.dark,
      useMaterial3: true,
    );
  }
}
