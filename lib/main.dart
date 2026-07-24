import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'theme/app_theme.dart';
import 'screens/main_shell.dart';

void main() {
  runApp(const AlRayesApp());
}

/// Root widget for the آل ناصر (Al Nasser) family app.
class AlRayesApp extends StatelessWidget {
  const AlRayesApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'آل ناصر',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.light(),
      // The app is Arabic-first and laid out right-to-left.
      locale: const Locale('ar'),
      supportedLocales: const [Locale('ar'), Locale('en')],
      localizationsDelegates: const [
        GlobalMaterialLocalizations.delegate,
        GlobalWidgetsLocalizations.delegate,
        GlobalCupertinoLocalizations.delegate,
      ],
      builder: (context, child) => Directionality(
        textDirection: TextDirection.rtl,
        child: child ?? const SizedBox.shrink(),
      ),
      home: const MainShell(),
    );
  }
}
