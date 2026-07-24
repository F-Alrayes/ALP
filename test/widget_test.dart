import 'package:flutter_test/flutter_test.dart';

import 'package:alp/main.dart';

void main() {
  testWidgets('Home tab renders sections and bottom nav',
      (WidgetTester tester) async {
    await tester.pumpWidget(const AlRayesApp());
    await tester.pump();

    // Home tab cards (unique to the home screen).
    expect(find.text('المكتبة'), findsOneWidget);
    expect(find.text('النسب'), findsOneWidget);
    expect(find.text('دخول'), findsOneWidget);

    // Bottom navigation destinations.
    expect(find.text('الرئيسية'), findsOneWidget);
    expect(find.text('زواجات'), findsOneWidget);
    expect(find.text('المزيد'), findsOneWidget);
  });
}
